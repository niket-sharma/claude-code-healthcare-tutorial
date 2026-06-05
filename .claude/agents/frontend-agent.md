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