"""Behavioral tests for the chat State (session 02 brief; responder mocked since session 03)."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


CANNED_REPLY = "- Newton's second law: $F = m a$"


@pytest.fixture(autouse=True)
def canned_responder(monkeypatch):
    """Never call OpenAI from these tests: the State sees a canned reply."""
    from phys_formula import state

    monkeypatch.setattr(state, "get_formulae", lambda problem: CANNED_REPLY)


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
        {"role": "user", "content": "What is F for m=2kg, a=3m/s^2?"},
        {"role": "assistant", "content": CANNED_REPLY},
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
    assert s.messages == [{"role": "user", "content": "Kinetic energy of 5 kg at 4 m/s?"}]
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
