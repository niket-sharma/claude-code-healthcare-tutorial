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
