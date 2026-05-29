#!/bin/bash
# Resume Conductor from last known position.
DIR="$(dirname "$0")/.."
REPO="/Users/Dev/Vibe-Coding/Apps/Madhav"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

echo "=== RESUME ($TIMESTAMP) ==="

# Clear pause flag
python3 "$DIR/scripts/update_tracker.py" \
  --workstream "running" \
  --activity "RESUME: Conductor resumed at $TIMESTAMP" 2>/dev/null || true

# Find last incomplete session from queue
LAST_SESSION=$(python3 - << 'PYEOF'
import yaml
with open('00_ARCHITECTURE/CONDUCTOR/build_orchestrator/session_queue.yaml') as f:
    q = yaml.safe_load(f)
for s in q.get('sessions', []):
    if s.get('status') in ('pending', 'in_progress', 'failed'):
        print(s['id'])
        break
PYEOF
)

echo "Resuming from session: ${LAST_SESSION:-'(all complete)'}"
cat >> "$DIR/CONDUCTOR_LOG.md" << EOF

## RESUME ($TIMESTAMP)
- Resumed from session: $LAST_SESSION

EOF

echo "Conductor state restored. Re-launch with the same prompt to continue."
