#!/bin/bash
# Emergency halt: stop all Conductor sub-processes.
DIR="$(dirname "$0")/.."
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

echo "=== HALT ALL ($TIMESTAMP) ==="

# Kill any Claude Code sub-agent processes spawned by conductor
pkill -f "claude.*--dangerously-skip-permissions" 2>/dev/null && echo "Killed claude sub-agents" || echo "No claude sub-agents running"

# Mark tracker paused
python3 "$DIR/scripts/update_tracker.py" \
  --workstream "paused" \
  --activity "HALT_ALL: operator-triggered emergency halt at $TIMESTAMP" 2>/dev/null || true

cat >> "$DIR/CONDUCTOR_HALT_LOG.md" << EOF

## HALT_ALL ($TIMESTAMP)
- **Trigger**: Operator manual halt_all.sh
- **Effect**: All streams paused
- **Resume**: bash scripts/resume.sh

EOF

echo "=== HALTED. Resume: bash scripts/resume.sh ==="
