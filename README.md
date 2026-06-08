# CareTriage

> **NOT A MEDICAL DEVICE.**
> CareTriage is educational software built to demonstrate AI-assisted development
> workflows. It is **not approved for clinical use**, **not a substitute for
> professional medical advice**, and **must never be deployed to real patients.**
> Every response carries an explicit disclaimer to that effect.

---

## What is CareTriage?

CareTriage is a symptom-intake and triage-suggestion service. A patient describes
their symptoms; the service records a structured intake, runs a deterministic
red-flag screen, and (if no emergency is detected) calls an LLM to produce a
triage suggestion in one of four levels:

| Level | Meaning |
|---|---|
| `self_care` | Minor, self-limiting — manage at home |
| `see_clinician` | Warrants professional evaluation, not urgent |
| `urgent` | Same-day or next-day care needed |
| `seek_immediate_care` | Call 911 or go to an emergency room now |

Urgent and immediate-care encounters are automatically added to a clinician
review queue.

---

## Safety Design

### 1 — Red-flags run first, always

Before any LLM call, a deterministic keyword screen (`app/core/red_flags.py`)
checks for emergency indicators: chest pain, stroke signs, difficulty breathing,
severe bleeding, anaphylaxis, suicidal ideation, sudden severe headache, and loss
of consciousness. If any phrase matches, the response is `seek_immediate_care`
and the LLM is never contacted.

### 2 — Fail-safe fallbacks

If the LLM call fails or returns malformed output, the service falls back to
`see_clinician` with an instruction to consult a clinician — never to a silent
failure or an empty response.

### 3 — Disclaimer on every response

Every triage result — in the API JSON and in the UI — carries:

> *"This output is not a medical diagnosis. Always consult a qualified clinician
> for medical advice."*

### 4 — Synthetic data only

No route, test fixture, seed script, or log statement may accept, store, or emit
real patient health information. All sample data uses obviously fictional names,
dates, and symptoms.

### 5 — Secrets stay in the environment

The OpenAI API key is read from `.env` at runtime via `python-dotenv`. It never
appears in source files, test files, or CI config.

---

## Features

- **POST /triage** — submit age, sex, and symptoms; receive a triage level,
  rationale, and safety disclaimer
- **GET /encounters** — paginated list of all recorded encounters for the
  clinician dashboard
- **Automatic review queue** — `urgent` and `seek_immediate_care` encounters are
  enqueued atomically with the encounter write
- **Red-flag module** — 8 emergency categories, 60+ trigger phrases, zero network
  dependency
- **React dashboard** — clinician-facing encounter list (Vite + TypeScript)
- **Full test suite** — 92 tests covering triage logic, red-flag detection,
  review queue behaviour, and API endpoints

---

## Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- An OpenAI API key

### 1 — Clone and configure

```bash
git clone <repo-url>
cd claude-code-healthcare-tutorial

cp .env.example .env
# Edit .env and set:  OPENAI_API_KEY=<your-key>
```

### 2 — Backend

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt

uvicorn app.main:app --reload --port 8000
```

The API is now available at `http://localhost:8000`.  
Interactive docs: `http://localhost:8000/docs`

### 3 — Frontend

```bash
cd frontend
npm install
npm run dev
```

The dashboard is now available at `http://localhost:5173`.  
API calls are proxied to `localhost:8000` automatically.

---

## Development

```bash
# Run all backend tests
pytest

# Run tests with coverage
pytest --cov=app --cov-report=term-missing

# Lint and format (Python)
ruff check .
ruff format .

# Frontend tests and lint
cd frontend
npm test
npm run lint
```

---

## Project Structure

```
app/
  api/          # FastAPI routers
  core/         # config, DB engine, red-flag module
  models/       # SQLAlchemy / SQLModel ORM models
  services/     # business logic, OpenAI client
tests/          # pytest suite
frontend/       # React + Vite dashboard
docs/           # architecture notes
```

---

## License

Educational use only. See [CLAUDE.md](CLAUDE.md) for the full project constitution
and safety rules.
