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