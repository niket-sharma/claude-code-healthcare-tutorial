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
