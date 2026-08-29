# phys-formula-for-que

Physics-problem chat app (Reflex + OpenAI). You type a physics problem; the app
replies with the formulae you need. The reply currently comes from a stub
responder (no OpenAI call yet).

## Setup

A venv is needed on Debian/Ubuntu Python 3.12, which refuses system-wide
`pip install` per PEP 668.

```
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Run the chat app

```
.venv/bin/reflex db init      # first time only: creates reflex.db (SQLite)
.venv/bin/reflex run
```

Then open http://localhost:3000/ (Reflex picks the next free port and prints it
if 3000/8000 are busy). Chat history is one shared thread stored in `reflex.db`
(gitignored) and reloaded on page open. Replies render as Markdown with
`$...$` LaTeX via KaTeX.

## Swap in a real responder

`phys_formula/responder.py` exposes `get_formulae(problem: str) -> str`
(Markdown, LaTeX allowed). The UI calls only that function; replace its body
to wire a model.

## Tests

```
.venv/bin/pytest
```

## Check the OpenAI key

Put `OPENAI_API_KEY=...` in a project-root `.env` (gitignored, never committed), then:

```
.venv/bin/python scripts/check_openai_key.py
```

Prints `OK` if the key authenticates, otherwise `FAIL: <error class>`. The key itself is never printed.
