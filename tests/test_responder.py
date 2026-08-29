"""Behavioral tests for the OpenAI-backed responder (session 03 brief).

The OpenAI client is always mocked; nothing here touches the network.
"""

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

PROBLEM = "A ball is launched at 20 m/s at 30 degrees above horizontal. Find its range."


class FakeClient:
    """Records the kwargs of responses.create and returns a canned response."""

    def __init__(self, *, text="canned", error=None):
        self.calls = []
        self._text = text
        self._error = error
        self.responses = SimpleNamespace(create=self._create)

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        if self._error is not None:
            raise self._error
        return SimpleNamespace(output_text=self._text)


@pytest.fixture()
def with_key(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-not-real")


def install(monkeypatch, client):
    from phys_formula import responder

    monkeypatch.setattr(responder, "OpenAI", lambda: client)
    return responder


# 1 -- prevents the model being asked the wrong thing (problem dropped, or
#      "no worked solution" rule lost, or a model other than the pinned one)
def test_prompt_carries_problem_and_no_solution_rule(monkeypatch, with_key):
    client = FakeClient()
    responder = install(monkeypatch, client)

    responder.get_formulae(PROBLEM)

    assert len(client.calls) == 1
    call = client.calls[0]
    assert call["model"] == "gpt-4o-mini"
    assert PROBLEM in call["input"]
    instructions = call["instructions"].lower()
    assert "do not" in instructions and "solve" in instructions
    assert "final answer" in instructions


# 2 -- prevents reading the wrong field (e.g. returning the response object's repr)
def test_returns_mocked_content(monkeypatch, with_key):
    client = FakeClient(text=r"- Range: $R = \frac{v_0^2 \sin 2\theta}{g}$")
    responder = install(monkeypatch, client)

    assert responder.get_formulae(PROBLEM) == r"- Range: $R = \frac{v_0^2 \sin 2\theta}{g}$"


# 3 -- prevents a stack trace in the chat bubble / a crashed event handler
def test_api_error_yields_readable_message(monkeypatch, with_key):
    class RateLimitBoom(Exception):
        pass

    client = FakeClient(error=RateLimitBoom("429 slow down"))
    responder = install(monkeypatch, client)

    reply = responder.get_formulae(PROBLEM)

    assert isinstance(reply, str) and reply.strip()
    assert "RateLimitBoom" in reply
    assert "Traceback" not in reply


# 4 -- prevents `reflex run` without a .env crashing on the first question
def test_missing_key_yields_readable_message(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    from phys_formula import responder

    monkeypatch.setattr(responder, "load_dotenv", lambda *a, **k: False)
    constructed = []
    monkeypatch.setattr(responder, "OpenAI", lambda: constructed.append(1))

    reply = responder.get_formulae(PROBLEM)

    assert "OPENAI_API_KEY" in reply and ".env" in reply
    assert constructed == []


# ---- session 04: image input -------------------------------------------------

import base64  # noqa: E402

PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
)


# 5 -- prevents the image feature silently changing the text-only request shape
#      (e.g. wrapping input in a list), which is the call E019 verified
def test_text_only_call_unchanged(monkeypatch, with_key):
    client = FakeClient()
    responder = install(monkeypatch, client)

    responder.get_formulae(PROBLEM)

    assert client.calls == [
        {
            "model": "gpt-4o-mini",
            "instructions": responder.SYSTEM_PROMPT,
            "input": f"Physics problem:\n\n{PROBLEM}",
        }
    ]


# 6 -- prevents the image being dropped, or sent with the wrong mime/encoding
#      (model answers the text alone, or the API rejects the part)
def test_image_call_builds_image_part(monkeypatch, with_key):
    client = FakeClient()
    responder = install(monkeypatch, client)

    responder.get_formulae(PROBLEM, PNG_BYTES, "image/png")

    call = client.calls[0]
    assert call["model"] == "gpt-4o-mini"
    assert call["instructions"] == responder.SYSTEM_PROMPT
    assert isinstance(call["input"], list) and len(call["input"]) == 1
    msg = call["input"][0]
    assert msg["role"] == "user"
    parts = msg["content"]
    text_parts = [p for p in parts if p["type"] == "input_text"]
    image_parts = [p for p in parts if p["type"] == "input_image"]
    assert len(text_parts) == 1 and PROBLEM in text_parts[0]["text"]
    assert len(image_parts) == 1
    expected = "data:image/png;base64," + base64.b64encode(PNG_BYTES).decode()
    assert image_parts[0]["image_url"] == expected


# 7 -- prevents an image-only submit sending an empty prompt beside the image
def test_image_without_text_uses_default_instruction(monkeypatch, with_key):
    client = FakeClient()
    responder = install(monkeypatch, client)

    responder.get_formulae("   ", PNG_BYTES, "image/png")

    parts = client.calls[0]["input"][0]["content"]
    text = [p for p in parts if p["type"] == "input_text"][0]["text"]
    assert text.strip() == responder.DEFAULT_IMAGE_INSTRUCTION
