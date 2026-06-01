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