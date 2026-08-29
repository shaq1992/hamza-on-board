# phys-formula-for-que

Physics-problem chat app (Reflex + OpenAI) -- currently at the "does the key work" stage.

## Check the OpenAI key

Put `OPENAI_API_KEY=...` in a project-root `.env` (gitignored, never committed), then:

```
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/check_openai_key.py
```

(A venv is needed on Debian/Ubuntu Python 3.12, which refuses system-wide `pip install` per PEP 668.)

Prints `OK` if the key authenticates, otherwise `FAIL: <error class>`. The key itself is never printed.
