# CareTriage — Project Constitution

## Project Summary

**CareTriage** is an educational symptom-intake and triage-suggestion service.
A patient describes their symptoms; the service records a structured intake, calls
the OpenAI API to produce a triage suggestion (self-care / see a clinician / urgent
/ seek immediate care), persists the encounter in SQLite, and exposes a clinician
dashboard via a React frontend.

This is **educational software built to demonstrate Claude Code features** — it is
**not a medical device** and must never be deployed to real users.

---

## Stack

| Layer | Technology |
|---|---|
| API server | Python 3.11 · FastAPI · Uvicorn |
| Database | SQLite via SQLAlchemy (async) |
| AI triage | OpenAI API (`gpt-4o-mini` by default) |
| Frontend | React 18 · Vite · TypeScript |
| Testing | Pytest + pytest-asyncio (backend) · Vitest (frontend) |
| Linting | Ruff (Python) · ESLint + Prettier (JS/TS) |
| Env management | python-dotenv — key read from `.env`, never hardcoded |

Directory layout:

```
app/
  api/          # FastAPI routers
  core/         # config, DB engine, red-flag module
  models/       # SQLAlchemy ORM models
  services/     # business logic, OpenAI client
tests/          # pytest test suite
frontend/       # React / Vite app
docs/           # tutorial and architecture notes
```

---

## Commands

### Backend

```bash
# Create and activate virtual environment (first time only)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run dev server (hot-reload)
uvicorn app.main:app --reload --port 8000

# Run all tests
pytest

# Run tests with coverage
pytest --cov=app --cov-report=term-missing

# Lint + format check
ruff check .
ruff format --check .

# Auto-fix lint issues
ruff check --fix .
ruff format .
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start dev server (proxies /api → localhost:8000)
npm run dev

# Build for production
npm run build

# Run tests
npm test

# Lint
npm run lint
```

### Full stack (dev)

Run the backend and frontend dev servers in separate terminals.

---

## Conventions

### Python / FastAPI
- **One router per resource** in `app/api/` (e.g. `encounters.py`, `triage.py`).
- All database access goes through `app/core/database.py`; never open a raw
  `sqlite3` connection elsewhere.
- Use `async def` for all route handlers and service functions that touch the DB
  or the OpenAI API.
- Pydantic v2 schemas live alongside the route that uses them (or in a
  `schemas.py` sibling) — not in `app/models/`.
- HTTP status codes: `201` for created resources, `422` for validation errors
  (FastAPI default), `503` if the OpenAI call fails.
- All responses include a `disclaimer` field reminding users this is not a
  diagnosis.

### Red-flag module (`app/core/red_flags.py`)
- The red-flag check runs **before** any OpenAI call.
- It is a pure deterministic function — no AI, no network.
- If it fires, the triage result is `"seek_immediate_care"` and the OpenAI call
  is skipped entirely.
- Trigger terms (chest pain, stroke signs, difficulty breathing, severe bleeding,
  unconsciousness, etc.) are maintained in a hard-coded list — never loaded from
  a database or config file that could be modified at runtime.

### React / TypeScript
- Components in `frontend/src/components/`; pages in `frontend/src/pages/`.
- Fetch wrapper in `frontend/src/api/client.ts` — all API calls go through it.
- No patient data persisted in `localStorage` or `sessionStorage`.
- Every triage result rendered in the UI must display the safety disclaimer.

### Data
- All sample/seed data is **synthetic** — use obviously fictional names, dates,
  and symptoms.
- The SQLite file (`caretriage.db`) is git-ignored; never commit a database file.

### Environment
- Runtime config is read from `.env` (git-ignored) via `python-dotenv`.
- The only secrets are `OPENAI_API_KEY` and, optionally, `DATABASE_URL`.
- `.env.example` (no real values) is the only env file committed to git.

---

## CRITICAL SAFETY RULES

> These rules are non-negotiable. They exist because even educational health
> software shapes how engineers think about building the real thing.

1. **This is educational software, NOT a medical device. Never remove safety disclaimers.**
   Every triage response — in the API JSON and in the UI — must carry an explicit
   disclaimer that the output is not a diagnosis and the user should consult a
   qualified clinician.

2. **Synthetic data only. Never generate code that ingests or logs real PHI.**
   No route, service, migration, seed script, test fixture, or log statement may
   accept, store, or emit real patient health information (names tied to conditions,
   real DOBs, SSNs, insurance IDs, etc.).

3. **Red-flag symptoms must ALWAYS escalate to "seek immediate care" and must never
   depend solely on the LLM. Never weaken the red-flag module.**
   The deterministic red-flag check in `app/core/red_flags.py` is the last line of
   safety. Do not shorten its trigger list, gate it behind a feature flag, or make
   it conditional on AI output. Any PR that touches this file requires extra scrutiny.

4. **Never hardcode the OpenAI API key. It is read from the environment only.**
   The key must come from `os.environ` / `python-dotenv` at runtime. It must not
   appear in source files, test files, notebooks, Docker files, or CI config.

5. **Never print, log, or commit the contents of `.env`.**
   Do not `cat .env`, `print(os.environ)`, log the full settings object, or add
   `.env` to any commit. The pre-commit hook enforces this, but the rule applies
   even when the hook is bypassed.
