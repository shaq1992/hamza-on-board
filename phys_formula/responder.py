"""Pluggable responder: the only thing the UI State calls to get a reply.

``get_formulae`` asks OpenAI for every equation a physics problem needs --
formulae, symbol meanings, assumptions -- and never a worked numeric solution.
The API key is read from the project-root ``.env`` here, never in the UI.
"""

import base64
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

MODEL = "gpt-4o-mini"

SYSTEM_PROMPT = """You are a physics tutor who supplies the TOOLS to solve a problem, never the solution.

Given a physics problem, respond in Markdown with these sections:

1. **Principles** -- name every physical principle or law the problem needs (e.g. conservation of energy, Newton's second law, projectile kinematics).
2. **Equations** -- list EVERY equation required to solve the problem, one per bullet, written in LaTeX between single dollar signs (for example $v = v_0 + a t$). Include intermediate relations the solver will need, not only the final one.
3. **Symbols** -- define every symbol that appears in the equations, with its SI unit.
4. **Assumptions** -- state the simplifying assumptions the equations rely on (e.g. neglect air resistance, uniform gravitational field, point mass).

Strict rules:
- Do NOT solve the problem. Do NOT substitute the numbers from the problem into any equation.
- Do NOT compute or state a final answer, a numeric result, or a partial numeric result.
- Do not explain the solution steps in prose; only supply the principles, equations, symbol meanings and assumptions.
"""

MISSING_KEY_MESSAGE = (
    "OPENAI_API_KEY is not set. Add a line `OPENAI_API_KEY=...` to the project-root "
    "`.env` file and restart the app."
)

DEFAULT_IMAGE_INSTRUCTION = "Solve the problem shown in the image."

_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"


def _build_input(problem: str, image: bytes | None, mime: str | None):
    """Text-only calls keep the session-03 string input; an image adds a content-part list."""
    if image is None:
        return f"Physics problem:\n\n{problem}"
    text = f"Physics problem:\n\n{problem}" if problem.strip() else DEFAULT_IMAGE_INSTRUCTION
    data_url = f"data:{mime};base64,{base64.b64encode(image).decode('ascii')}"
    return [
        {
            "role": "user",
            "content": [
                {"type": "input_text", "text": text},
                {"type": "input_image", "image_url": data_url},
            ],
        }
    ]


def get_formulae(problem: str, image: bytes | None = None, mime: str | None = None) -> str:
    """Return the formulae relevant to ``problem`` as Markdown (LaTeX allowed).

    ``image`` (raw PNG/JPEG/WebP bytes) and its ``mime`` type are optional; when
    given, the screenshot is sent to the model alongside the text (or a default
    instruction if the text is blank). Never raises: a missing key or an API
    failure comes back as a readable message so the chat page shows it instead
    of crashing.
    """
    load_dotenv(_ENV_PATH)
    if not os.environ.get("OPENAI_API_KEY"):
        return MISSING_KEY_MESSAGE
    try:
        response = OpenAI().responses.create(
            model=MODEL,
            instructions=SYSTEM_PROMPT,
            input=_build_input(problem, image, mime),
        )
        return response.output_text
    except Exception as exc:  # noqa: BLE001 - every API failure becomes a chat message
        return (
            f"Sorry, the request to OpenAI failed ({type(exc).__name__}): {exc}\n\n"
            "Check the API key, your network connection, or try again in a moment."
        )
