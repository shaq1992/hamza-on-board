# phys-formula-for-que

Physics-problem chat app (Reflex + OpenAI). You type a physics problem; the app
replies with every equation needed to solve it -- principles, formulae in LaTeX,
symbol meanings and assumptions -- and never a worked numeric solution. Replies
come from OpenAI model **`gpt-4o-mini`** (set in `phys_formula/responder.py`).

`.env` in the project root must hold `OPENAI_API_KEY=...` (gitignored, never
committed); see "Check the OpenAI key" below. Without it the app still starts,
and the chat shows a message asking for the key.

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

## Responder

`phys_formula/responder.py` exposes `get_formulae(problem: str) -> str`
(Markdown, LaTeX allowed). The UI calls only that function. It loads `.env`,
calls the OpenAI Responses API with `gpt-4o-mini` and a system prompt that
forbids numeric solving, and turns a missing key or any API error (auth, rate
limit, network) into a readable chat message rather than a crash.

## Tests

```
.venv/bin/pytest
```

The OpenAI client is mocked in every test; the suite never calls the API.

## Check the OpenAI key

Put `OPENAI_API_KEY=...` in a project-root `.env` (gitignored, never committed), then:

```
.venv/bin/python scripts/check_openai_key.py
```

Prints `OK` if the key authenticates, otherwise `FAIL: <error class>`. The key itself is never printed.
