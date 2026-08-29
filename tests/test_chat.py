"""Behavioral tests for the chat State (session 02 brief; responder mocked since session 03;
image attachment cases added in session 04)."""

import base64
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


CANNED_REPLY = "- Newton's second law: $F = m a$"

PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
)


@pytest.fixture(autouse=True)
def canned_responder(monkeypatch):
    """Never call OpenAI from these tests: the State sees a canned reply. Records calls."""
    from phys_formula import state

    calls = []

    def fake(problem, image=None, mime=None):
        calls.append((problem, image, mime))
        return CANNED_REPLY

    monkeypatch.setattr(state, "get_formulae", fake)
    return calls


@pytest.fixture(autouse=True)
def upload_dir(tmp_path, monkeypatch):
    """Attachments land in a per-test temp dir, never in the project upload dir."""
    from phys_formula import state

    d = tmp_path / "uploads"
    monkeypatch.setattr(state, "get_upload_dir", lambda: d)
    return d


@pytest.fixture()
def db(tmp_path):
    """Point the store at a fresh temp SQLite file for each test."""
    from phys_formula import store

    store.configure(f"sqlite:///{tmp_path / 'test.db'}")
    yield
    store.configure(None)


def fresh_state():
    from phys_formula.state import ChatState

    return ChatState(_reflex_internal_init=True)


def drive(gen):
    """Run a submit generator to completion, returning the list of yield points."""
    return list(gen)


# 1 -- prevents an empty assistant bubble hiding broken wiring
def test_responder_returns_nonempty_string(db):
    s = fresh_state()
    s.question = "A ball is thrown upward at 10 m/s. How high does it go?"
    drive(s.submit())
    reply = s.messages[-1]["content"]
    assert isinstance(reply, str)
    assert reply.strip()


# 2 -- prevents the submit flow dropping the user turn or never calling the responder
def test_submit_appends_user_and_reply(db):
    s = fresh_state()
    s.question = "What is F for m=2kg, a=3m/s^2?"
    drive(s.submit())
    assert s.messages[-2:] == [
        {"role": "user", "content": "What is F for m=2kg, a=3m/s^2?", "image": ""},
        {"role": "assistant", "content": CANNED_REPLY, "image": ""},
    ]
    assert s.question == ""
    assert s.thinking is False


# 3 -- prevents a blank Enter press creating a blank bubble and a canned reply
def test_submit_ignores_blank(db):
    s = fresh_state()
    s.question = "   "
    drive(s.submit())
    assert s.messages == []
    assert s.thinking is False


# 4 -- prevents the thinking indicator never showing (no yield before the responder)
def test_thinking_flag_set_while_pending(db):
    s = fresh_state()
    s.question = "Kinetic energy of 5 kg at 4 m/s?"
    gen = s.submit()
    next(gen)  # first yield: user message shown, reply pending
    assert s.thinking is True
    assert s.messages == [{"role": "user", "content": "Kinetic energy of 5 kg at 4 m/s?", "image": ""}]
    drive(gen)
    assert s.thinking is False


# 5 -- prevents history that is saved but never reloaded (or never saved)
def test_history_persists_and_reloads(db):
    s = fresh_state()
    s.question = "Period of a 1 m pendulum?"
    drive(s.submit())

    s2 = fresh_state()
    assert s2.messages == []
    s2.load_history()
    assert s2.messages == s.messages
    assert len(s2.messages) == 2


# ---- session 04: image attachment ------------------------------------------


# 6 -- prevents the State attaching an image but calling the text-only path
def test_submit_with_image_calls_responder_with_bytes(db, canned_responder, upload_dir):
    s = fresh_state()
    s.attach_bytes(PNG_BYTES, "image/png")
    assert s.pending_image.endswith(".png") and s.error == ""
    assert (upload_dir / s.pending_image).read_bytes() == PNG_BYTES
    s.question = "Which formulae does this need?"
    drive(s.submit())

    assert canned_responder == [("Which formulae does this need?", PNG_BYTES, "image/png")]
    user_msg, reply = s.messages[-2:]
    assert user_msg["content"] == "Which formulae does this need?"
    assert user_msg["image"].endswith(".png")
    assert reply == {"role": "assistant", "content": CANNED_REPLY, "image": ""}
    assert s.pending_image == "" and s.pending_mime == ""


# 7 -- prevents the blank-text guard swallowing an image-only submit
def test_submit_image_only(db, canned_responder):
    s = fresh_state()
    s.attach_bytes(PNG_BYTES, "image/jpeg")
    s.question = ""
    drive(s.submit())

    assert len(canned_responder) == 1
    assert canned_responder[0][1] == PNG_BYTES and canned_responder[0][2] == "image/jpeg"
    assert s.messages[-2]["role"] == "user" and s.messages[-2]["image"].endswith(".jpg")
    assert s.messages[-1]["content"] == CANNED_REPLY


# 8 -- prevents an oversize file or a non-image reaching the API (cost, 400s)
def test_attach_rejects_oversize_and_wrong_type(db, canned_responder, upload_dir):
    s = fresh_state()
    s.attach_bytes(b"x" * (5 * 1024 * 1024 + 1), "image/png")
    assert s.pending_image == ""
    assert "5 MB" in s.error

    s.attach_bytes(b"GIF89a", "image/gif")
    assert s.pending_image == ""
    assert "PNG" in s.error and "JPEG" in s.error and "WebP" in s.error

    s.attach_bytes(b"%PDF-1.4", "application/pdf")
    assert s.pending_image == ""

    assert not upload_dir.exists() or list(upload_dir.iterdir()) == []
    s.question = "still works?"
    drive(s.submit())
    assert canned_responder == [("still works?", None, None)]


# 9 -- prevents history reloading without the thumbnail (image column not saved/loaded)
def test_image_filename_persists_and_reloads(db):
    s = fresh_state()
    s.attach_bytes(PNG_BYTES, "image/webp")
    s.question = "From the screenshot"
    drive(s.submit())
    name = s.messages[-2]["image"]
    assert name.endswith(".webp")

    s2 = fresh_state()
    s2.load_history()
    assert s2.messages == s.messages
    assert s2.messages[0]["image"] == name
