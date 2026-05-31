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