#!/bin/bash
# Run a session's check_commands from session_queue.yaml.
# Usage: gate_check.sh <session-id>
set -e
SESSION_ID="$1"
QUEUE="/Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/CONDUCTOR/build_orchestrator/session_queue.yaml"

[ -z "$SESSION_ID" ] && echo "ERROR: session-id required" && exit 1

# Extract check_commands for this session
COMMANDS=$(python3 - << PYEOF
import yaml
with open('$QUEUE') as f:
    q = yaml.safe_load(f)
for s in q.get('sessions', []):
    if s.get('id') == '$SESSION_ID':
        for cmd in s.get('check_commands', []):
            print(cmd)
        break
PYEOF
)

if [ -z "$COMMANDS" ]; then
  echo "WARN: no check_commands for session $SESSION_ID"
  exit 0
fi

echo "=== GATE CHECK: $SESSION_ID ==="
PASS=0; FAIL=0
while IFS= read -r CMD; do
  [ -z "$CMD" ] && continue
  echo "Running: $CMD"
  if eval "$CMD"; then
    echo "PASS"
    PASS=$((PASS+1))
  else
    echo "FAIL"
    FAIL=$((FAIL+1))
  fi
done <<< "$COMMANDS"

echo "=== $PASS PASS, $FAIL FAIL ==="
[ "$FAIL" -gt 0 ] && exit 1 || exit 0
