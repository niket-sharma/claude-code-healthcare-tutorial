# CareTriage Tutorial — Phase Audit Report

**Document audited:** `claude-code-healthcare-tutorial.md` (1,228 lines)
**Method:** One subagent per phase (0–13), each extracting code blocks, validating commands/paths, checking internal consistency, and flagging anachronistic feature references.
**Date:** 2026-06-09

---

## Summary

| Verdict | Count | Phases |
|---|---|---|
| ✅ Pass | 9 | 1, 2, 5, 6, 8, 9, 10, 11, 13 |
| ⚠️ Warn | 5 | 0, 3, 4, 7, 12 |
| ❌ Fail | 0 | — |

**Anachronism check: CLEAN.** Across all 14 phases, **zero** references to features that postdate the tutorial were found — no dynamic workflows, no `ultracode`, no Opus 4.8 / `claude-opus-4-8`. Model references throughout are era-appropriate plain aliases (`sonnet`, `opus`). The tutorial's coverage of sub-agents, agent teams, slash commands, skills, hooks, and MCP is legitimate and not flagged.

### Summary table

| Phase | Title | Verdict | Code blocks | Issues (fail/warn/info) |
|---|---|---|---|---|
| 0 | Project Setup & The Constitution | ⚠️ Warn | 9 | 1 / 2 / 2 |
| 1 | Permissions & Safety Guardrails | ✅ Pass | 4 | 0 / 0 / 0 |
| 2 | The Core Backend (Plan Mode) | ✅ Pass | 4 | 0 / 0 / 4 |
| 3 | Red-Flag Safety Module | ⚠️ Warn | 3 | 0 / 2 / 2 |
| 4 | The Triage Brain (OpenAI API) | ⚠️ Warn | 5 | 0 / 3 / 2 |
| 5 | Slash Commands | ✅ Pass | 4 | 0 / 0 / 1 |
| 6 | Skills + Hooks | ✅ Pass | 9 | 0 / 0 / 2 |
| 7 | MCP (GitHub + reference lookup) | ⚠️ Warn | 6 | 0 / 1 / 2 |
| 8 | Sub-Agents (research→plan→review) | ✅ Pass | 7 | 0 / 0 / 0 |
| 9 | Agent Teams (parallel frontend) | ✅ Pass | 9 | 0 / 0 / 2 |
| 10 | GSD-Style Spec-Driven Feature | ✅ Pass | 6 | 0 / 0 / 0 |
| 11 | Ralph Loop (sandboxed, optional) | ✅ Pass | 4 | 0 / 0 / 1 |
| 12 | A Tiny Gas Town (advanced, optional) | ⚠️ Warn | 2 | 0 / 1 / 1 |
| 13 | Final Review & Ship It | ✅ Pass | 3 | 0 / 0 / 0 |
| | **Total** | | **75** | **1 / 9 / 19** |

---

## Cross-cutting themes

These recurring issues drive most of the Warn verdicts. Fixing them at the source would clear several phases at once.

1. **`redflags.py` vs `red_flags.py` (naming drift)** — Phases 0, 3, 7, 11, 12.
   The tutorial body consistently uses `app/core/redflags.py` (no underscore), but `CLAUDE.md` establishes the canonical module as `app/core/red_flags.py` (with underscore). The tutorial is *internally* consistent with itself, but contradicts the project constitution and the actual repo file. **Recommendation:** global find/replace `redflags` → `red_flags` in the tutorial.

2. **Red-flag triage level: `"urgent"` vs `"seek_immediate_care"` (safety-relevant)** — Phases 3, 4.
   Prompts instruct the red-flag path to return `triage_level="urgent"`, but `CLAUDE.md` CRITICAL SAFETY RULE 3 mandates red-flag hits escalate to `"seek_immediate_care"` (a strictly higher level). Phase 4 even lists allowed levels as `self_care | see_clinician | urgent`, omitting `seek_immediate_care` entirely, while line 438 then asks to confirm the "seek-immediate-care message." This is the most consequential inconsistency because it touches the non-negotiable safety taxonomy. **Recommendation:** make every red-flag example return `seek_immediate_care` and include it in the enumerated level list.

3. **App entrypoint: `app.api.main:app` vs `app.main:app`** — Phases 0, 2, 4, 9.
   The tutorial serves from `app/api/main.py` (`uvicorn app.api.main:app`), but `CLAUDE.md`'s Commands section uses `uvicorn app.main:app`. The tutorial is self-consistent; the divergence is tutorial-vs-constitution. **Recommendation:** align `CLAUDE.md` and tutorial on one entrypoint.

4. **Virtualenv directory: `.venv` vs `venv`** — Phases 0, 2, 4, 9.
   Tutorial uses `.venv` (dot-prefixed); `CLAUDE.md` uses `venv`. Cosmetic but reader-confusing. **Recommendation:** pick one.

5. **Database module: `app/core/db.py` vs `app/core/database.py`** — Phase 2.
   Tutorial creates `db.py`; constitution names it `database.py`.

---

## Detailed findings per phase

### Phase 0 — Project Setup & The Constitution · ⚠️ Warn · 9 code blocks
- ❌ **fail · command · line 80** — Truncated/broken command `sour` instead of `source .venv/bin/activate`. As written it fails, the venv is never activated, and the subsequent `pip install` runs outside the venv. **This is the only hard breakage in the document.**
- ⚠️ **warn · consistency · line 163** — Example `CLAUDE.md` uses `uvicorn app.api.main:app`, implying `app/api/main.py`, vs the canonical `app.main:app`.
- ⚠️ **warn · consistency · line 178** — Example `CLAUDE.md` names the module `app/core/redflags.py` (no underscore) vs the conventional `red_flags.py`.
- ℹ️ info · line 157 — Illustrative `CLAUDE.md` lists `SQLModel (SQLite)` while the constitution specifies SQLAlchemy (async). Phrased as a rough example, low impact.
- ℹ️ info · line 87 — `mkdir -p app/{api,core,models,services} tests frontend docs .claude` correctly establishes the documented layout.

### Phase 1 — Permissions & Safety Guardrails · ✅ Pass · 4 code blocks
- No issues. JSON `settings.json`, bash, and prompt blocks all valid; permission syntax, modes, paths, and git commands consistent with the layout.

### Phase 2 — The Core Backend (Plan Mode) · ✅ Pass · 4 code blocks
- ℹ️ info · line 288 — `app/core/db.py` vs constitution's `app/core/database.py` (self-consistent within phase).
- ℹ️ info · lines 285,300 — Creates `app/api/main.py` + runs `uvicorn app.api.main:app`; internally consistent, diverges from `CLAUDE.md`'s `app.main:app`.
- ℹ️ info · line 289 — `requirements.txt` lists `sqlmodel`; constitution's stack table says SQLAlchemy (async). SQLModel is built on SQLAlchemy, so plausible.
- ℹ️ info · line 298 — `.venv` vs `venv`. Command itself valid.

### Phase 3 — Red-Flag Safety Module · ⚠️ Warn · 3 code blocks
- ⚠️ **warn · path · lines 333/346/355/363** — Uses `app/core/redflags.py` and `tests/test_redflags.py` (no underscore) vs canonical `red_flags.py`.
- ⚠️ **warn · consistency · lines 336/350** — Forces `triage_level="urgent"`; constitution mandates `"seek_immediate_care"` for red-flag hits. Free-text message says "seek immediate care" but the structured level is wrong.
- ℹ️ info · line 355 — `pytest -q tests/test_redflags.py` is valid.
- ℹ️ info · lines 363–364 — `git add`/`git commit` valid and reference the named files.

### Phase 4 — The Triage Brain (OpenAI API) · ⚠️ Warn · 5 code blocks
- ⚠️ **warn · path · line 423** — `uvicorn app.api.main:app` vs documented `app.main:app`; also POST `/triage` added to `app/api/main.py` rather than `app/api/triage.py` (one-router-per-resource convention).
- ⚠️ **warn · consistency · line 422** — `.venv` vs documented `venv`.
- ⚠️ **warn · consistency · line 383** — Plan instructs red-flag hits to `return "urgent"`; constitution requires `seek_immediate_care`. Line 438 confirms a "seek-immediate-care message", contradicting the level label.
- ℹ️ info · line 385 — Allowed levels listed as `self_care | see_clinician | urgent`, omitting `seek_immediate_care`.
- ℹ️ info · line 408 — Triage route in `app/api/main.py` rather than `app/api/triage.py`.

### Phase 5 — Slash Commands · ✅ Pass · 4 code blocks
- ℹ️ info · line 489 — Tutorial creates `.claude/commands/new-endpoint.md` (hyphen); actual repo file is `new_endpoint.md` (underscore). Self-consistent within the phase; repo-vs-tutorial divergence only.

### Phase 6 — Skills + Hooks · ✅ Pass · 9 code blocks
- ℹ️ info · lines 609–630 / 639–666 — `settings.json` hooks block shown twice (partial then complete); the two are consistent — intentional redundancy.
- ℹ️ info · lines 624,662 — PostToolUse `ruff check app/ --fix --quiet || true` valid; `app/` matches layout. The phi-audit skill, commit-guard PreToolUse hook, and auto-lint hook all check out.

### Phase 7 — MCP (GitHub + reference lookup) · ⚠️ Warn · 6 code blocks
- ⚠️ **warn · path · line 731** — References bare `redflags.py` — both misnamed (vs `red_flags.py`) and missing its `app/core/` directory. Note the same phase correctly uses `app/services/triage.py` (line 741).
- ℹ️ info · line 726 — Creates a top-level `reference/` folder outside the documented layout; intentional demo folder for the filesystem MCP server, so plausible.
- ℹ️ info · line 709 — `claude mcp add github npx @github/mcp-server` is plausible; the exact package name is illustrative and unverifiable from the text.

### Phase 8 — Sub-Agents (research→plan→review) · ✅ Pass · 7 code blocks
- No issues. Agent Markdown files, prompt blocks, and the commit block all valid; paths (`.claude/agents/`, `docs/research/`, `docs/plans/`) consistent; model aliases plain `sonnet`/`opus` — no Opus 4.8.

### Phase 9 — Agent Teams (parallel frontend) · ✅ Pass · 9 code blocks
- ℹ️ info · line 948 — `uvicorn app.api.main:app` is internally consistent with the rest of the tutorial (163, 300, 423) and matches the real `app/api/main.py`; diverges only from `CLAUDE.md`.
- ℹ️ info · line 948 — `.venv` matches tutorial's earlier usage (79, 298, 422). Git worktree, npm, uvicorn, pytest commands all valid.

### Phase 10 — GSD-Style Spec-Driven Feature · ✅ Pass · 6 code blocks
- No issues. Valid commands and layout-consistent paths (`docs/specs/`, `docs/plans/`, `app/`). "GSD spec-driven workflow" is a *methodology* reference, **not** the dynamic Workflow tool — correctly not flagged.

### Phase 11 — Ralph Loop (sandboxed, optional) · ✅ Pass · 4 code blocks
- ℹ️ info · lines 1040–1041 — Prompt references `app/core/redflags.py`; matches the tutorial's own (non-underscore) convention, so internally consistent. Commands include `--dangerously-skip-permissions`, `--model sonnet`, `git worktree`, `--allow-empty` — all valid, era-appropriate (`sonnet`, not Opus 4.8).

### Phase 12 — A Tiny Gas Town (advanced, optional) · ⚠️ Warn · 2 code blocks
- ⚠️ **warn · path · line 1121** — `app/core/redflags.py` vs project-standard `app/core/red_flags.py`.
- ℹ️ info · lines 1110–1112 — Worker loop `claude --dangerously-skip-permissions -p ... --model sonnet` plausible; prompt instructs not to modify safety modules, consistent with guardrails.

### Phase 13 — Final Review & Ship It · ✅ Pass · 3 code blocks
- No issues. Ship slash-command definition, README prompt, and `git add/commit/push` all valid; `pytest -q`, `ruff check .`, paths (`app/`, `.claude/commands/ship.md`, `README.md`) consistent; no anachronisms.

---

## Recommended fix priority

1. **Fix the broken command** (Phase 0, line 80: `sour` → `source .venv/bin/activate`) — only hard breakage.
2. **Reconcile the red-flag triage level** (Phases 3, 4) — safety taxonomy; use `seek_immediate_care` everywhere and add it to the enumerated level list.
3. **Normalize `redflags.py` → `red_flags.py`** (Phases 0, 3, 7, 11, 12) — and decide whether `CLAUDE.md` or the tutorial is source of truth.
4. **Pick one entrypoint** (`app.main` vs `app.api.main`) and **one venv name** (`venv` vs `.venv`) across tutorial and `CLAUDE.md`.

*Note: themes 3–4 are tutorial-vs-`CLAUDE.md` divergences. The tutorial is self-consistent; aligning the two documents is a documentation decision, not a tutorial bug per se.*
