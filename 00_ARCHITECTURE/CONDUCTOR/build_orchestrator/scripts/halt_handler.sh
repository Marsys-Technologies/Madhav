#!/bin/bash
# Handle a stream halt: log to CONDUCTOR_HALT_LOG.md, update tracker to blocked.
# Usage: halt_handler.sh <session-id> <reason> <retry_count>
SESSION_ID="$1"
REASON="${2:-unknown}"
RETRY="${3:-3}"
DIR="$(dirname "$0")/.."
HALT_LOG="$DIR/CONDUCTOR_HALT_LOG.md"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

cat >> "$HALT_LOG" << EOF

## HALT: $SESSION_ID ($TIMESTAMP)
- **Session**: $SESSION_ID
- **Reason**: $REASON
- **Retries exhausted**: $RETRY/3
- **Status**: STREAM_HALTED (other streams continue)
- **Action required**: Review diagnostic, fix underlying issue, update session brief, re-queue

EOF

echo "HALT logged for $SESSION_ID"

# Update tracker
python3 "$DIR/scripts/update_tracker.py" \
  --session "$SESSION_ID" \
  --impl "blocked" \
  --activity "HALT: session $SESSION_ID blocked after $RETRY retries — $REASON" 2>/dev/null || true
