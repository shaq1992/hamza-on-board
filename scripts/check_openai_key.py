"""Verify OPENAI_API_KEY in the project-root .env authenticates.

Prints exactly one line: ``OK`` or ``FAIL: <error class>``. Never prints the key.
"""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv


def main() -> int:
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
    if not os.environ.get("OPENAI_API_KEY"):
        print("FAIL: MissingKey")
        return 1
    try:
        from openai import OpenAI

        OpenAI().models.list()  # cheap, model-agnostic auth probe
    except Exception as exc:  # noqa: BLE001 - report class only, never the message
        print(f"FAIL: {type(exc).__name__}")
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
