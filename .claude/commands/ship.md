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