# Building "CareTriage" with Claude Code — A Step-by-Step Project Tutorial

> **Repository:** [claude-code-healthcare-tutorial](https://github.com/niket-sharma/claude-code-healthcare-tutorial)  
> **File:** `docs/02-caretriage-project.md`  
> **Part 2 of 2** — hands-on project. For the full Claude Code feature reference, see `docs/01-claude-code-tutorial.md`.

> A hands-on project that exercises **every major Claude Code feature** while you build a real, runnable healthcare app on Windows WSL.
>
> You will build **CareTriage**: a symptom-intake and triage-suggestion service. A patient describes their symptoms, the service captures a structured intake, uses the OpenAI API to produce a *triage suggestion* (self-care / see a clinician / urgent), stores the encounter, and surfaces everything on a clinician dashboard.

---

## ⚠️ Read This First — Safety & Scope

This is an **educational project**, not a medical device. Build it with the same care you'd want from anyone writing health software:

1. **Synthetic data only.** You will never enter, store, or process real patient information (PHI). All sample patients are made up. This keeps you clear of HIPAA/GDPR obligations *and* makes the security parts of this tutorial concrete.
2. **The AI output is a suggestion, not a diagnosis.** Every triage response carries an explicit disclaimer and a recommendation to consult a real clinician.
3. **Hard-coded red-flag escalation.** Certain symptoms (e.g. chest pain, signs of stroke, difficulty breathing) bypass the AI entirely and always return "seek immediate care." We never let a probabilistic model be the only thing standing between a user and an emergency.
4. **Do not deploy this to real users.** It's a sandbox for learning Claude Code and full-stack patterns.

We'll wire these principles into the code itself — via permission deny-rules, a PHI-leak hook, and a red-flag module — so you learn *responsible* healthcare engineering, not just feature plumbing.

---

## What You'll Practice (feature → where it shows up)

| Claude Code feature | Where you'll use it in CareTriage |
|---|---|
| **CLAUDE.md** | Project constitution: stack, commands, the safety rules above |
| **Plan mode** | Before every multi-file change |
| **Permissions** | Deny reading `.env`/real DB; block destructive commands |
| **Slash commands** | `/triage-review`, `/new-endpoint`, `/ship` |
| **Checkpoints** | Rewind when a refactor goes sideways |
| **MCP** | GitHub (issues/PRs) + a reference-lookup server |
| **Skills** | A reusable "triage-rules reviewer" and "PHI-leak auditor" |
| **Hooks** | Block commits containing API keys / PHI patterns; auto-run tests |
| **Sub-agents** | Researcher + planner + reviewer for new features |
| **Agent teams** | Backend and frontend built in parallel worktrees |
| **Ralph loop** | Autonomously expand the triage test suite |
| **GSD** | Spec-driven build of "red-flag escalation" |
| **Gas Town** | (Optional) sprint through a backlog of symptom-taxonomy tasks |

You don't have to do the advanced phases (11–14) to have a working app — phases 0–10 give you a complete, runnable CareTriage. The autonomous phases are marked **optional** and **sandboxed**.

---

## Prerequisites

- Windows 10/11 with **WSL2 + Ubuntu** installed
- **Claude Code** installed in WSL (`claude --version` works) — see `docs/01-claude-code-tutorial.md` (§1) in [claude-code-healthcare-tutorial](https://github.com/niket-sharma/claude-code-healthcare-tutorial) if not
- **Python 3.11+** and **Node 18+** inside WSL
- An **OpenAI API key** (from platform.openai.com) — we'll store it safely, never in code
- **VS Code** with the Remote-WSL extension (`code .` from WSL opens it)
- Basic familiarity with the terminal

A note on cost: the OpenAI calls in this project are tiny (a few cents of usage for the whole tutorial if you use a small model like `gpt-4o-mini`). Claude Code usage draws from your Claude plan as normal.

---

## Phase 0 — Project Setup & The Constitution

**Goal:** an empty-but-correct project skeleton, a git repo, and a CLAUDE.md so every later Claude Code session already knows the rules.

### 0.1 — Create the project and open it

In your WSL terminal:

```bash
mkdir -p ~/projects/caretriage
cd ~/projects/caretriage
git init
code .            # opens VS Code via Remote-WSL
```

### 0.2 — Set up the Python environment

```bash
python3 -m venv .venv
sour
pip install --upgrade pip
```

We'll let Claude Code fill in dependencies shortly, but create the folder layout now so it has a target:

```bash
mkdir -p app/{api,core,models,services} tests frontend docs .claude
touch app/__init__.py
```

### 0.3 — Protect secrets *before* writing any code

Create `.env` (this holds your real key and must never be committed):

```bash
cat > .env << 'EOF'
OPENAI_API_KEY=sk-replace-with-your-real-key
OPENAI_MODEL=gpt-4o-mini
APP_ENV=development
EOF
```

Create `.gitignore`:

```bash
cat > .gitignore << 'EOF'
.venv/
__pycache__/
*.pyc
.env
.env.*
*.db
*.sqlite3
node_modules/
dist/
.claude/settings.local.json
EOF
```

> Notice we excluded `.env` and `*.db` *first*. The number-one way people leak secrets is committing them before the ignore rule exists. We'll add a hook later that catches it even if `.gitignore` fails.

### 0.4 — Write CLAUDE.md (the constitution)

This is the single most important file. Start Claude Code and let it help — but you own the safety section. Launch Claude:

```bash
claude
```

Then give it this prompt (paste it):

```
Create a CLAUDE.md for this project. It's "CareTriage", a FastAPI + SQLite
symptom-triage service using the OpenAI API, with a React dashboard.

Include these sections: Project summary, Stack, Commands (build/test/lint/run),
Conventions, and a CRITICAL SAFETY RULES section containing exactly these rules:
- This is educational software, NOT a medical device. Never remove safety disclaimers.
- Synthetic data only. Never generate code that ingests or logs real PHI.
- Red-flag symptoms must ALWAYS escalate to "seek immediate care" and must never
  depend solely on the LLM. Never weaken the red-flag module.
- Never hardcode the OpenAI API key. It is read from the environment only.
- Never print, log, or commit the contents of .env.

Keep it under 200 lines.
```

Review what Claude produces. If the safety rules aren't verbatim, fix them. A good CLAUDE.md ends up looking roughly like this — confirm yours matches the spirit:

```markdown
# CareTriage

Educational symptom-triage service. FastAPI + SQLite + OpenAI API, React dashboard.
NOT a medical device.

## Stack
- Python 3.11, FastAPI, SQLModel (SQLite), Pydantic v2
- OpenAI Python SDK (model from OPENAI_MODEL env var)
- Frontend: React + Vite + Recharts
- Tooling: pytest, ruff, httpx for tests

## Commands
- Run API:  `uvicorn app.api.main:app --reload`
- Test:     `pytest -q`
- Lint:     `ruff check . --fix`
- Frontend: `cd frontend && npm run dev`

## Conventions
- Type hints everywhere; Pydantic models for all request/response bodies
- Services layer holds business logic; API layer stays thin
- Commit format: feat/fix/chore(scope): description
- Tests live in tests/ and must pass before commit

## CRITICAL SAFETY RULES
- Educational software, NOT a medical device. Never remove safety disclaimers.
- Synthetic data only. Never write code that ingests or logs real PHI.
- Red-flag symptoms ALWAYS escalate to "seek immediate care" and never depend
  solely on the LLM. Never weaken app/core/redflags.py.
- Never hardcode the OpenAI API key — read from environment only.
- Never print, log, or commit the contents of .env.
```

### 0.5 — First commit

Exit Claude (`/exit`) or run git from a second terminal:

```bash
git add CLAUDE.md .gitignore
git commit -m "chore: project skeleton + CLAUDE.md constitution"
```

✅ **Checkpoint:** You have a repo, a protected `.env`, and a constitution. Every future `claude` session in this folder now starts already knowing the rules.

---

## Phase 1 — Permissions & Safety Guardrails

**Goal:** configure Claude Code so it can work smoothly *and* literally cannot read your secrets or nuke your data. In a healthcare project this isn't optional polish — it's the point.

### 1.1 — Create the project permissions file

Create `.claude/settings.json`:

```json
{
  "permissions": {
    "defaultMode": "acceptEdits",
    "allow": [
      "Bash(python:*)",
      "Bash(pytest:*)",
      "Bash(ruff:*)",
      "Bash(uvicorn:*)",
      "Bash(npm:*)",
      "Bash(git status)",
      "Bash(git diff:*)",
      "Bash(git add:*)",
      "Bash(git commit:*)",
      "Read(./**)"
    ],
    "ask": [
      "Bash(git push:*)"
    ],
    "deny": [
      "Read(./.env)",
      "Read(./.env.*)",
      "Edit(./.env)",
      "Edit(./.env.*)",
      "Bash(rm -rf:*)",
      "Bash(cat .env*)",
      "Bash(curl:*)",
      "Read(./*.db)",
      "Read(./*.sqlite3)"
    ]
  }
}
```

What this does, line by line:
- **`defaultMode: acceptEdits`** — Claude can freely read/write project files without nagging you on every edit, but shell commands still go through the rules.
- **`allow`** — the everyday commands (run, test, lint, basic git) never prompt.
- **`ask`** — `git push` always asks first. Pushing is a real-world action; you want a beat to confirm.
- **`deny`** — the safety net. Reading or editing `.env`, `cat`-ing it, touching the SQLite DB files, `rm -rf`, and raw `curl` are all blocked. **Deny wins over everything**, even if you later switch to a permissive mode.

> Evaluation order is deny → ask → allow, first match wins. So even if `Read(./**)` would allow reading everything, the explicit `Read(./.env)` deny blocks the secret. That's the whole design.

### 1.2 — Prove the guardrail works

Restart Claude (so it picks up the new settings) and try to make it read the secret:

```bash
claude
```

Ask it:

```
Show me the contents of the .env file.
```

Claude should refuse / be blocked by the deny rule rather than printing your key. **This is the test that matters in a healthcare app** — confirm it actually can't. If it somehow reads it, stop and fix your `settings.json` before continuing.

### 1.3 — Commit

```bash
git add .claude/settings.json
git commit -m "chore: permission guardrails (deny .env and db reads)"
```

✅ **Checkpoint:** Claude Code is now sandboxed against your most sensitive files. You'll layer a *hook* on top of this in Phase 6 for defense-in-depth.

---

## Phase 2 — The Core Backend (Plan Mode + first real feature)

**Goal:** a runnable FastAPI service with a real intake model and a health endpoint — built using **plan mode** so you review the design before any code lands.

### 2.1 — Use plan mode for the design

Start Claude and enter **plan mode** by pressing **Shift+Tab** until you see plan mode indicated (or type `/plan`). In plan mode Claude can read and propose but won't edit until you approve.

Prompt:

```
Plan the core backend for CareTriage. I want:
- app/api/main.py: FastAPI app with a GET /health endpoint
- app/models/encounter.py: SQLModel models for a triage Encounter
  (id, created_at, age, sex, symptoms_text, triage_level, rationale, disclaimer)
- app/core/db.py: SQLite engine + session helper, DB file caretriage.db
- requirements.txt with fastapi, uvicorn, sqlmodel, pydantic, openai, httpx, pytest, ruff
Do not implement triage logic yet — just the skeleton, models, DB, and /health.
Propose the plan first.
```

Read the plan. This is the habit that prevents runaway edits — you're the senior engineer signing off on scope. If it looks right, approve it (accept the plan). Claude will exit plan mode and implement.

### 2.2 — Install and run
```bash
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.api.main:app --reload
```

Visit `http://localhost:8000/health` — you should get a JSON OK response. Then `http://localhost:8000/docs` shows the auto-generated Swagger UI. Stop the server with `Ctrl+C`.

### 2.3 — Commit via a checkpoint mindset

Before committing, glance at what changed:

```bash
git status
git diff
```

If something looks off, remember: **every prompt you sent created an automatic checkpoint**. You can `/rewind` inside Claude to roll back code and/or conversation. When you're happy:

```bash
git add -A
git commit -m "feat: core backend skeleton (health, encounter model, sqlite)"
```

✅ **Checkpoint:** A running FastAPI app with a persistent model. Next we add the triage brain — and the red-flag safety layer that guards it.
---

## Phase 3 — Red-Flag Safety Module (the non-negotiable core)

**Goal:** build the deterministic safety layer *before* the AI layer, so the AI can never be the only thing deciding an emergency. This ordering is deliberate and is itself a lesson in healthcare software design.

### 3.1 — Build it test-first

Start Claude (normal mode is fine here). Prompt:

```
Create app/core/redflags.py with a function:
    check_red_flags(symptoms_text: str, age: int) -> RedFlagResult | None
It scans for emergency indicators and, if found, returns a result forcing
triage_level="urgent" with a clear "seek immediate care" message.

Cover at minimum: chest pain, pressure or tightness in chest; difficulty
breathing / shortness of breath; signs of stroke (face drooping, arm weakness,
slurred speech, sudden confusion); severe bleeding; suicidal ideation;
anaphylaxis signs; sudden severe headache ("worst headache of life").

Use simple, auditable keyword/phrase matching — NOT an LLM. This module must be
deterministic and easy for a clinician to review.

Also create tests/test_redflags.py with cases for each category (positive and
negative). Then run pytest.
```

Why keyword matching and not AI here? Because this layer must be **auditable and deterministic** — a reviewer can read exactly what triggers an escalation. An LLM that's right 99% of the time is unacceptable when the 1% is a missed stroke.

### 3.2 — Verify the tests pass

```bash
pytest -q tests/test_redflags.py
```

All green before you move on. If Claude's keyword list has gaps, tell it which symptom it missed and have it add a test + the rule.

### 3.3 — Commit

```bash
git add app/core/redflags.py tests/test_redflags.py
git commit -m "feat: deterministic red-flag escalation module (test-covered)"
```

✅ **Checkpoint:** The safety floor exists and is tested. Now the AI layer sits *on top* of it, never around it.

---

## Phase 4 — The Triage Brain (OpenAI API integration)

**Goal:** wire in the OpenAI API to produce a triage suggestion — but only *after* red-flags have had first say.

### 4.1 — Design the service in plan mode

Enter plan mode (Shift+Tab). Prompt:

```
Plan app/services/triage.py with a function:
    triage(age, sex, symptoms_text) -> TriageResult
Logic order (critical):
  1. FIRST call check_red_flags(). If it returns a hit, return "urgent" with the
     red-flag message immediately. Do NOT call OpenAI in that case.
  2. Otherwise call the OpenAI API (model from OPENAI_MODEL env var) with a
     system prompt that: states it is a triage assistant, NOT a diagnosis;
     must return one of self_care | see_clinician | urgent; must include a short
     plain-language rationale; must always append a disclaimer to see a real
     clinician.
  3. Parse the response into TriageResult(triage_level, rationale, disclaimer).
Use structured output (ask the model to return JSON) and parse it safely with a
fallback to "see_clinician" if parsing fails (fail safe, not fail open).
Read the API key from the environment via app/core/config.py (pydantic settings).
Propose the plan first.
```

Note the **fail-safe** instruction: if the model returns garbage, we escalate to "see a clinician," never downgrade to "self-care." That's a healthcare design principle — failures should err toward caution.

### 4.2 — Add the config loader (secret-safe)

If Claude didn't already create it, ensure `app/core/config.py` reads `OPENAI_API_KEY` from the environment (via pydantic-settings or `os.environ`) and **never** has a default key value. Approve the plan and let it implement.

### 4.3 — Wire the endpoint

Prompt (normal mode):

```
Add POST /triage to app/api/main.py. It accepts an intake body
(age, sex, symptoms_text), validates with a Pydantic model, calls the triage
service, saves the Encounter to the DB, and returns the TriageResult.
Add tests/test_triage_endpoint.py that mocks the OpenAI call (do not hit the
real API in tests) and asserts: a red-flag input returns urgent without calling
OpenAI; a normal input returns a parsed result; the disclaimer is always present.
Run pytest.
```

### 4.4 — Run it for real (one live call)

With your real key in `.env`:

```bash
source .venv/bin/activate
uvicorn app.api.main:app --reload
```

In another WSL terminal:

```bash
# Normal symptom
curl -s -X POST localhost:8000/triage -H "Content-Type: application/json" \
  -d '{"age": 30, "sex": "female", "symptoms_text": "mild sore throat for 2 days"}' | python3 -m json.tool

# Red-flag symptom (should be urgent, no OpenAI call)
curl -s -X POST localhost:8000/triage -H "Content-Type: application/json" \
  -d '{"age": 55, "sex": "male", "symptoms_text": "crushing chest pain and short of breath"}' | python3 -m json.tool
```

Confirm the chest-pain case returns **urgent** and includes the seek-immediate-care message. Confirm every response has a disclaimer.

### 4.5 — Commit

```bash
git add -A
git commit -m "feat: OpenAI triage service (red-flags first, fail-safe parsing)"
```

✅ **Checkpoint:** CareTriage now does its core job. The remaining phases make it robust, reviewable, and a showcase of Claude Code's workflow features.

---

## Phase 5 — Slash Commands (your repeatable workflows)

**Goal:** turn the things you'll do repeatedly into one-word commands.

### 5.1 — A triage-safety review command

Create `.claude/commands/triage-review.md`:

```markdown
---
description: Audit triage-related code for safety regressions
allowed-tools: Read, Grep, Glob
---

Review the files I name (or all of app/ if none given): $ARGUMENTS

Check specifically for these SAFETY regressions and report any you find:
1. Any path where the LLM result can override or skip check_red_flags()
2. Any place a parsing failure could downgrade severity (must fail to
   "see_clinician" or "urgent", never "self_care")
3. Missing disclaimer in any triage response
4. Any hardcoded API key or .env contents in code
5. Any logging of full symptom text alongside identifiers (PHI-shaped logging)

Output: a Markdown report with sections Pass / Concerns / Must-Fix, each with
file:line references. Do not modify any files — this is review only.
```

Use it:

```
/triage-review app/services/triage.py app/api/main.py
```

This is your safety net for every future change. Run it before you ship anything.

### 5.2 — A "new endpoint" scaffold command

Create `.claude/commands/new-endpoint.md`:

```markdown
---
description: Scaffold a new API endpoint with model, route, and test
allowed-tools: Read, Write, Edit, Bash
---

Create a new endpoint for: $ARGUMENTS

1. Add a Pydantic request/response model (or SQLModel if it persists)
2. Add the route to app/api/main.py, keeping the API layer thin (logic in services)
3. Add a test in tests/ that does not hit external APIs (mock them)
4. Run pytest -q and fix failures
5. Summarize what you added
```

### 5.3 — Commit

```bash
git add .claude/commands/
git commit -m "feat: slash commands (triage-review, new-endpoint)"
```

✅ **Checkpoint:** Repeatable workflows are now one command each. `/triage-review` in particular is the habit that keeps the safety invariants intact.

---

## Phase 6 — Skills + Hooks (reusable expertise + enforced guardrails)

**Goal:** package deeper review logic as a **Skill**, and make safety **mechanically enforced** with a **Hook** that blocks bad commits even if you (or Claude) forget.

### 6.1 — A PHI-leak auditor Skill

Skills load on demand (token-cheap) and can carry reference material. Create the folder and file:

```bash
mkdir -p .claude/skills/phi-audit
```

`.claude/skills/phi-audit/SKILL.md`:

```markdown
---
name: phi-audit
description: Audit code and logs for PHI-leak patterns and secret exposure. Use before shipping or when touching logging, storage, or API responses.
allowed-tools: Read, Grep, Glob
---

# PHI / Secret Leak Audit

When invoked, scan the named files (or all of app/) for:

1. Logging that combines identifiers with clinical detail
   (e.g. logging name/email/id together with symptoms_text)
2. Symptom or encounter data written to stdout/print in production paths
3. Any string that looks like an API key (sk-...) outside .env
4. Responses that echo back more PII than the caller sent
5. Stack traces or debug dumps that could include intake content

Read patterns.md for the detailed checklist before auditing.

Output: Pass / Concerns / Must-Fix with file:line references. Review only —
never modify files.
```

`.claude/skills/phi-audit/patterns.md`:

```markdown
# PHI-shaped patterns to flag

- `logger.*(.*symptoms_text.*` combined with any id/name/email field
- `print(.*encounter` or `print(.*intake`
- regex for keys: sk-[A-Za-z0-9]{20,}
- f-strings interpolating both a patient identifier and free-text symptoms
- exception handlers that `repr()` or `str()` a full request body into logs

# Safe alternatives to recommend
- Log an encounter_id only, never the content
- Redact free text before logging
- Keep secrets exclusively in environment/config
```

Invoke it any time with `/phi-audit` (skills become slash commands).

### 6.2 — A hook that BLOCKS dangerous commits

A skill *asks*; a hook *enforces*. Create a pre-commit-style guard via Claude Code's hook system. First the script:

```bash
mkdir -p .claude/hooks
cat > .claude/hooks/guard-commit.sh << 'EOF'
#!/bin/bash
# PreToolUse hook: inspect git commit commands and block secret/PHI leaks.
# Receives JSON on stdin; we read the command Claude is about to run.
input=$(cat)
command=$(echo "$input" | jq -r '.tool_input.command // ""')

# Only act on git commit / git add commands
if echo "$command" | grep -qE 'git (commit|add)'; then
  # Block if any staged file contains an OpenAI-style key
  if git diff --cached -U0 2>/dev/null | grep -qE 'sk-[A-Za-z0-9]{20,}'; then
    echo '{"message": "BLOCKED: an OpenAI-style API key is staged. Unstage it and move it to .env."}'
    exit 2
  fi
  # Block if .env itself is staged
  if git diff --cached --name-only 2>/dev/null | grep -qE '(^|/)\.env'; then
    echo '{"message": "BLOCKED: .env is staged. It must never be committed."}'
    exit 2
  fi
fi
exit 0
EOF
chmod +x .claude/hooks/guard-commit.sh
```

(Install `jq` if you haven't: `sudo apt-get install -y jq`.)

Now register the hook. Add this to `.claude/settings.json` (alongside your `permissions` block — keep both):

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          { "type": "command", "command": ".claude/hooks/guard-commit.sh" }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          { "type": "command", "command": "ruff check app/ --fix --quiet || true" }
        ]
      }
    ]
  }
}
```

- The **PreToolUse** hook inspects every Bash command; if Claude tries to commit a staged key or `.env`, it **exits 2 and blocks** the commit.
- The **PostToolUse** hook auto-lints after any file edit, so style never drifts.

> Exit code 2 is the enforcement lever — it stops the action. Exit 0 lets it proceed. This is defense-in-depth: even though `.gitignore` and permissions already protect `.env`, the hook catches a staged key that slipped through any other way.

**Don't overwrite your permissions block.** `settings.json` holds one JSON object with both `permissions` and `hooks` keys. Here's the complete file after this phase — safe to copy wholesale:

```json
{
  "permissions": {
    "defaultMode": "acceptEdits",
    "allow": [
      "Bash(python:*)", "Bash(pytest:*)", "Bash(ruff:*)", "Bash(uvicorn:*)",
      "Bash(npm:*)", "Bash(git status)", "Bash(git diff:*)",
      "Bash(git add:*)", "Bash(git commit:*)", "Read(./**)"
    ],
    "ask": ["Bash(git push:*)"],
    "deny": [
      "Read(./.env)", "Read(./.env.*)", "Edit(./.env)", "Edit(./.env.*)",
      "Bash(rm -rf:*)", "Bash(cat .env*)", "Bash(curl:*)",
      "Read(./*.db)", "Read(./*.sqlite3)"
    ]
  },
  "hooks": {
    "PreToolUse": [
      { "matcher": "Bash",
        "hooks": [ { "type": "command", "command": ".claude/hooks/guard-commit.sh" } ] }
    ],
    "PostToolUse": [
      { "matcher": "Edit|Write",
        "hooks": [ { "type": "command", "command": "ruff check app/ --fix --quiet || true" } ] }
    ]
  }
}
```

### 6.3 — Test the guard

Try to trick it (safely). Create a throwaway file with a fake key and attempt a commit *inside Claude*:

```bash
echo 'KEY = "sk-abcdef1234567890abcdef1234567890"' > scratch_leak.py
```

Then in Claude: `commit scratch_leak.py with message "test"`. The hook should block it. Clean up:

```bash
rm scratch_leak.py
```

### 6.4 — Commit your safety tooling

```bash
git add .claude/skills/ .claude/hooks/ .claude/settings.json
git commit -m "feat: phi-audit skill + commit-guard hook + auto-lint"
```

✅ **Checkpoint:** Safety is now enforced by machinery, not memory. You have a reusable PHI auditor and a hook that physically refuses to commit secrets.
---

## Phase 7 — MCP (connect Claude to GitHub + a reference lookup)

**Goal:** give Claude Code access to external systems so it can manage issues/PRs and look up clinical reference data — without you copy-pasting.

### 7.1 — Add the GitHub MCP server

First create a GitHub repo for CareTriage (separate from [claude-code-healthcare-tutorial](https://github.com/niket-sharma/claude-code-healthcare-tutorial) — this is your *app* repo) and a personal access token (classic, with `repo` scope). Put the token in `.env` (never in code):

```bash
echo 'GITHUB_TOKEN=ghp_your_token_here' >> .env
```

Add the server:

```bash
claude mcp add github npx @github/mcp-server
```

Now Claude can read/create issues and PRs. Try it:

```
List the open issues in my caretriage repo, and create a new issue titled
"Add encounter list endpoint for the dashboard" with a short body.
```

> Why this matters here: in a team healthcare project, traceability is real — every change tends to map to a ticket. MCP lets Claude keep that hygiene without you leaving the terminal.

### 7.2 — Add a reference-data MCP (optional but illustrative)

For clinical reference lookups you can wire a simple MCP server (e.g. a filesystem server pointed at a folder of guideline notes, or a public health-info API server if you have one). The simplest, safe demo is a local reference folder:

```bash
mkdir -p reference
cat > reference/triage-guidelines.md << 'EOF'
# Internal triage reference (synthetic, educational)
- Sore throat without red flags, <3 days: typically self-care; safety-net advice.
- Fever >3 days or >39.5C: consider clinician review.
- Any red-flag symptom: immediate care (handled by redflags.py).
EOF

claude mcp add --scope project refs npx @modelcontextprotocol/server-filesystem ./reference
```

Now Claude can consult `reference/` when reasoning about triage rules. Ask:

```
Using the refs server, summarize our internal guidance for sore throat and
check whether app/services/triage.py's prompt is consistent with it.
```

### 7.3 — Commit

```bash
git add .claude/  # mcp project config if created here
git commit -m "chore: MCP servers (github + local reference data)"
```

✅ **Checkpoint:** Claude can now reach beyond the repo — managing issues and consulting reference material as part of its reasoning.

---

## Phase 8 — Sub-Agents (research → plan → review pipeline)

**Goal:** delegate heavy work to isolated agents so the main session stays clean, and you get specialist behavior per task. We'll use them to add an **encounter-list endpoint** for the dashboard.

### 8.1 — Define three subagents

Recall: subagents are Markdown files in `.claude/agents/`. Required fields are `name` and `description`; `tools` and `model` are optional.

`.claude/agents/researcher.md`:

```markdown
---
name: researcher
description: Researches implementation approaches and existing-code context. Use before planning a new feature.
tools: Read, Grep, Glob, WebFetch
model: sonnet
---

You research, you do not edit code. Given a feature:
1. Read the relevant existing files to understand current patterns
2. If needed, fetch official docs for libraries involved
3. Write findings to docs/research/<feature>.md: current state, options,
   recommended approach, risks (especially any safety implications)
```

`.claude/agents/planner.md`:

```markdown
---
name: planner
description: MUST BE USED before implementing a feature. Turns research into an atomic task plan.
tools: Read, Write
model: opus
---

Given a feature and its research doc:
1. Read docs/research/<feature>.md
2. Produce docs/plans/<feature>.md: ordered atomic tasks, files affected,
   acceptance criteria, and an explicit "safety check" item for anything
   touching triage or logging
```

`.claude/agents/reviewer.md`:

```markdown
---
name: reviewer
description: Reviews a diff for correctness and CareTriage safety invariants. Use after implementation, before commit.
tools: Read, Grep, Bash
model: sonnet
---

Review recent changes (git diff). Report Bugs / Safety / Style with file:line.
Safety invariants to enforce:
- red-flags run before any LLM call and can't be bypassed
- parsing failures never downgrade severity
- no PHI-shaped logging, no secrets in code
- disclaimer present on every triage response
```

### 8.2 — Run the pipeline

In Claude:

```
Use the researcher subagent to research adding a GET /encounters endpoint that
returns recent encounters (paginated, newest first) for the clinician dashboard.
```

Then:

```
Use the planner subagent on the encounters feature.
```

Review `docs/plans/encounters.md`, then implement (you can do this directly or via `/new-endpoint "GET /encounters paginated list"`). Finally:

```
Use the reviewer subagent to check my changes before I commit.
```

> The payoff: each subagent runs in its **own context window**, so the noisy research and review work never clogs your main session. The main thread stays focused and high-quality even across many features.

### 8.3 — Commit

```bash
git add -A
git commit -m "feat: GET /encounters endpoint (research->plan->review pipeline)"
```

✅ **Checkpoint:** You have a reusable research→plan→review team and a new endpoint feeding the dashboard.

---

## Phase 9 — Agent Teams (build the frontend in parallel)

**Goal:** build the React dashboard *in parallel* with backend polish, using separate git worktrees so the agents don't collide. This is where agent teams shine: genuinely independent workstreams.

> Note: agent-team orchestration is evolving fast. Treat the commands below as a working pattern and check `/help` for your version's exact keybindings. The core technique — worktrees for isolation — is stable and is the part that matters.

### 9.1 — Create isolated worktrees

```bash
# from the repo root, on a clean tree
git worktree add ../caretriage-frontend -b feature/dashboard
git worktree add ../caretriage-backend  -b feature/backend-polish
```

Each worktree is a full checkout on its own branch. An agent working in one can't step on the other.

### 9.2 — Define the two worker agents

`.claude/agents/frontend-agent.md`:

```markdown
---
name: frontend-agent
description: Builds the React dashboard. Owns the frontend/ directory only.
tools: Read, Write, Edit, Bash
model: sonnet
---

Owns: frontend/ ONLY. Never edit app/ (backend-agent owns that).

Build a Vite + React dashboard that:
1. Has an intake form (age, sex, symptoms_text) posting to POST /triage
2. Shows the triage result with a colored severity badge and the disclaimer
   ALWAYS visible (never hide it)
3. Lists recent encounters from GET /encounters with a small Recharts bar chart
   of triage levels
Run `npm run build` and fix errors. Keep the disclaimer prominent — it's a
safety requirement.
```

`.claude/agents/backend-agent.md`:

```markdown
---
name: backend-agent
description: Backend polish — CORS, pagination, error handling. Owns app/ only.
tools: Read, Write, Edit, Bash
model: sonnet
---

Owns: app/ ONLY. Never edit frontend/.

Tasks: enable CORS for the Vite dev origin; ensure /encounters pagination works;
add consistent error responses; run pytest and keep it green. Do not weaken any
safety module.
```

### 9.3 — Run them

Open a Claude session in each worktree (two terminals), and in each, invoke the matching agent — or drive both from the root session by delegating:

```
Delegate the dashboard build to frontend-agent (in the frontend worktree) and
backend polish to backend-agent (in the backend worktree). They work in parallel.
Report when each finishes.
```

While they run, you can watch progress. Each commits to its own branch.

### 9.4 — Merge the workstreams

```bash
cd ~/projects/caretriage
git merge feature/backend-polish
git merge feature/dashboard
# resolve any conflicts (should be minimal since they owned different dirs)
git worktree remove ../caretriage-frontend
git worktree remove ../caretriage-backend
```

### 9.5 — Run the whole thing

```bash
# Terminal 1: backend
source .venv/bin/activate && uvicorn app.api.main:app --reload
# Terminal 2: frontend
cd frontend && npm install && npm run dev
```

Open the Vite URL (usually `http://localhost:5173`), submit a symptom, and watch the triage result + encounters chart. Try the chest-pain input and confirm the urgent badge + disclaimer.

```bash
git add -A && git commit -m "feat: React dashboard + backend polish (parallel agent teams)"
```

✅ **Checkpoint:** Full-stack CareTriage runs end to end, built by two agents working in parallel.

---

## Phase 10 — GSD-Style Spec-Driven Feature (red-flag escalation v2)

**Goal:** use a structured spec → plan → build → verify flow to add a meaningful feature: **escalation logging + a clinician "needs review" queue**. You can use the GSD framework if you've installed it, or replicate the discipline with your own subagents — the *method* is the lesson.

> Reminder from the feature tutorial: GSD's upstream project changed hands in 2026; if you install a framework, use the current community repo and audit it first. You don't need any external framework to follow this phase — the spec-driven *workflow* below works with the plain subagents you already built.

### 10.1 — Write the spec

In Claude:

```
Create docs/specs/review-queue.md. Spec only, no code. Feature: when a triage
result is "urgent" (including red-flag escalations), record it to a review_queue
table and expose GET /review-queue for clinicians, plus a way to mark an item
"reviewed". Include: data model, endpoints, acceptance criteria, and a safety
section (must not lose any urgent encounter; review status never alters the
original triage record).
```

### 10.2 — Plan it (planner subagent)

```
Use the planner subagent on docs/specs/review-queue.md to produce
docs/plans/review-queue.md with atomic, ordered tasks.
```

### 10.3 — Build phase by phase

Implement each task from the plan in order, committing after each green step. Because each task is atomic and tested, quality stays high — this is the context-engineering benefit GSD formalizes: small units, fresh focus, verify as you go.

```
Implement task 1 from docs/plans/review-queue.md. Add its test. Run pytest.
```

Repeat for each task. Use `/triage-review` and the `reviewer` subagent before the final commit.

### 10.4 — Verify and ship

```bash
pytest -q
```

Then a final review and commit:

```
Run /phi-audit on app/ and the reviewer subagent on the full diff. Summarize
any Must-Fix items.
```

```bash
git add -A && git commit -m "feat: clinician review queue for urgent encounters (spec-driven)"
```

✅ **Checkpoint:** You've shipped a real feature through a disciplined spec→plan→build→verify cycle — the workflow that keeps large features from degrading into spaghetti.
---

## Phase 11 — (Optional, Sandboxed) Ralph Loop: auto-expand the test suite

**Goal:** let Claude run autonomously to grow the triage test suite — a perfect mechanical task with a clear "done" signal. Because this runs with reduced prompting, we sandbox it.

> ⚠️ **Safety first.** Autonomous loops run with `--dangerously-skip-permissions`, which puts Claude in bypass mode (only your *deny* rules and hooks still protect you). For a healthcare project, run this in a **container or a dedicated worktree on a throwaway branch**, never on your main branch, and keep your `.env` deny-rules and commit-guard hook in place.

### 11.1 — Isolate

```bash
git worktree add ../caretriage-ralph -b experiment/test-expansion
cd ../caretriage-ralph
```

### 11.2 — Write the agent prompt with a hard stop condition

```bash
cat > AGENT_PROMPT.md << 'EOF'
Goal: expand tests/ to cover more triage scenarios WITHOUT touching app/core/redflags.py
or app/services/triage.py logic (tests only).

Each iteration:
1. Read existing tests to see what's covered.
2. Add 2-3 new test cases for uncovered, realistic synthetic scenarios
   (mock OpenAI; never call the real API in tests).
3. Run `pytest -q`. If failures are due to a real bug, note it in NOTES.md but
   DO NOT modify safety modules — only fix the test or report.
4. When pytest reports 25+ passing triage-related tests, append the exact line
   TASK_COMPLETE to AGENT_PROMPT.md and stop.

Constraints: synthetic data only; never log PHI; never weaken safety modules.
EOF
```

### 11.3 — The loop

```bash
cat > ralph.sh << 'EOF'
#!/bin/bash
for i in $(seq 1 15); do
  echo "=== Ralph iteration $i ==="
  claude --dangerously-skip-permissions -p "$(cat AGENT_PROMPT.md)" --model sonnet
  if grep -q "TASK_COMPLETE" AGENT_PROMPT.md; then
    echo "Done at iteration $i"; break
  fi
  pytest -q && git add -A && git commit -m "ralph: test expansion iter $i" --allow-empty
done
EOF
chmod +x ralph.sh
./ralph.sh
```

When it finishes, review the generated tests *yourself* — autonomy doesn't remove the review step, it relocates it to the end. Cherry-pick or merge what's good:

```bash
cd ~/projects/caretriage
git merge experiment/test-expansion   # or cherry-pick specific commits
git worktree remove ../caretriage-ralph
```

✅ **Checkpoint:** You've seen the fresh-context loop pattern do real mechanical work, safely fenced off from your main branch and safety code.

---

## Phase 12 — (Optional, Advanced) A Tiny Gas Town

**Goal:** glimpse the "agent assembly line" — an orchestrator handing tasks to worker loops. Keep this small; it's here to demystify the concept, not to run your repo overnight unsupervised.

Build a backlog of safe, mechanical tasks (docstring coverage, adding type hints, expanding the symptom synonym list used by red-flags' *tests*, etc.):

```bash
cat > backlog.md << 'EOF'
- [ ] Add docstrings to all functions in app/services/
- [ ] Add type hints where missing in app/api/
- [ ] Expand tests/fixtures with 10 more synthetic intake examples
- [ ] Add OpenAPI summaries/descriptions to each endpoint
EOF
```

Run **one** worker loop against the backlog (single worker first — never start at scale):

```bash
cat > worker.sh << 'EOF'
#!/bin/bash
for i in $(seq 1 10); do
  TASK=$(grep -m1 '^- \[ \]' backlog.md)
  [ -z "$TASK" ] && echo "Backlog empty" && break
  echo "=== Working: $TASK ==="
  claude --dangerously-skip-permissions \
    -p "Complete this backlog task, then mark it done by changing its '[ ]' to '[x]' in backlog.md: $TASK. Run pytest -q. Do not modify safety modules." \
    --model sonnet
  pytest -q && git add -A && git commit -m "gastown: $TASK" --allow-empty
done
EOF
chmod +x worker.sh
```

Run it in a sandbox worktree as in Phase 11. The lesson: an orchestrator (here, the backlog file + loop) feeds discrete tasks to a worker that commits each independently. Scaling to multiple parallel workers + a quality gate is the full Gas Town pattern — powerful, but only worth it once you trust your test gate and run it isolated.

> **Cost & safety reality check:** parallel autonomous agents multiply token spend and risk. For a healthcare codebase specifically, never let a loop modify `app/core/redflags.py` or `app/services/triage.py` unattended. Your deny-rules, hook, and a strong test gate are what make any of this safe.

✅ **Checkpoint:** You understand the assembly-line concept and, more importantly, the guardrails that make it responsible.

---

## Phase 13 — Final Review & "Ship It"

**Goal:** a clean, reviewed, documented project.

### 13.1 — A master ship command

Create `.claude/commands/ship.md`:

```markdown
---
description: Full pre-ship gate for CareTriage
allowed-tools: Read, Grep, Glob, Bash
---

Run the full ship gate and report a go/no-go:
1. /triage-review on app/
2. /phi-audit on app/
3. reviewer subagent on the full git diff vs main
4. pytest -q  (must be green)
5. ruff check . (must be clean)
6. Confirm: disclaimer present on triage responses; red-flags run before LLM;
   no secrets in tracked files.
Summarize Must-Fix items. If all pass, say SHIP READY.
```

Run `/ship`. Fix anything flagged.

### 13.2 — Write the README

```
Create README.md: what CareTriage is, the prominent NOT-A-MEDICAL-DEVICE
disclaimer and safety design (red-flags-first, fail-safe, synthetic data),
setup steps (env, install, run backend + frontend), and a feature list.
Do not include any real keys or PHI.
```

### 13.3 — Final commit and push

```bash
git add -A
git commit -m "docs: README + ship gate command"
git push   # Claude will ASK first — your permission rule in action
```

✅ **You built it.** A full-stack, AI-assisted healthcare triage app with deterministic safety, built end-to-end through every major Claude Code workflow.

---

## Phase 14 — What You Practiced (self-check)

Tick these off — if any feel shaky, revisit that phase:

- [ ] **CLAUDE.md** drove every session's behavior (Phase 0)
- [ ] **Permissions** blocked reading `.env` and the DB (Phase 1)
- [ ] **Plan mode** before multi-file changes (Phases 2, 4)
- [ ] **Checkpoints/rewind** understood as the in-session safety net (Phase 2)
- [ ] **Deterministic safety module** built before the AI (Phase 3)
- [ ] **OpenAI integration** with red-flags-first + fail-safe parsing (Phase 4)
- [ ] **Slash commands** for repeatable workflows (Phase 5)
- [ ] **Skill** (phi-audit) + **Hook** (commit guard) for enforced safety (Phase 6)
- [ ] **MCP** for GitHub + reference data (Phase 7)
- [ ] **Sub-agents** research→plan→review pipeline (Phase 8)
- [ ] **Agent teams** + worktrees for parallel full-stack work (Phase 9)
- [ ] **Spec-driven (GSD-style)** feature delivery (Phase 10)
- [ ] **Ralph loop**, sandboxed, for mechanical work (Phase 11, optional)
- [ ] **Gas Town** concept + its guardrails (Phase 12, optional)
- [ ] **Ship gate** combining commands, skills, and subagents (Phase 13)

---

## Troubleshooting (WSL-specific)

- **`claude` not found in scripts/loops:** non-interactive shells may miss your PATH. Add `export PATH="$HOME/.local/bin:$PATH"` to `~/.bashrc`, then `source ~/.bashrc`. Test with `claude -p "hello" --model sonnet`.
- **`jq: command not found`:** `sudo apt-get install -y jq` (needed by the commit-guard hook).
- **Cloudflare/network errors from Claude:** `echo "nameserver 8.8.8.8" | sudo tee /etc/resolv.conf`.
- **OpenAI auth errors:** confirm `OPENAI_API_KEY` is in `.env` and that your code reads it from the environment (your deny-rule means *you* must verify, since Claude can't read `.env`). `echo $OPENAI_API_KEY` after `set -a; source .env; set +a` in a throwaway shell to sanity-check (never commit that shell history).
- **Frontend can't reach the API (CORS):** ensure the backend enables CORS for the Vite origin (the backend-agent task in Phase 9).
- **The commit-guard hook blocks a legitimate commit:** it only triggers on staged `sk-...` strings or a staged `.env`. If you hit it, you almost certainly *do* have a key or `.env` staged — that's the hook doing its job.
- **A loop won't stop:** every loop here has a max iteration count and a `TASK_COMPLETE` check. If it spins, `Ctrl+C`, inspect `AGENT_PROMPT.md`/`backlog.md`, and lower the iteration cap.

---

## Resources

- **This repo:** [claude-code-healthcare-tutorial](https://github.com/niket-sharma/claude-code-healthcare-tutorial)
- **Feature reference (Part 1):** `docs/01-claude-code-tutorial.md` in the same repo
- Claude Code docs: https://docs.claude.com/en/docs/claude-code/overview
- OpenAI API: https://platform.openai.com/docs
- FastAPI: https://fastapi.tiangolo.com
- MCP spec: https://modelcontextprotocol.io

---

## Where to Take It Next

- Add authentication + role separation (patient vs clinician views)
- Add an MCP server for a real clinical-reference API (audit it first)
- Add structured audit logging (encounter_id only — never content)
- Containerize with Docker so the autonomous loops run fully isolated
- Add an evaluation harness that scores triage suggestions against a synthetic gold set (great Ralph-loop target)

Remember the throughline: **the AI is assistive, the safety layer is deterministic, the data is synthetic, and the guardrails are enforced by machinery — not by hoping the model behaves.** That mindset is what separates a demo from responsible healthcare software.