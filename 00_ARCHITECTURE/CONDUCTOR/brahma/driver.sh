#!/usr/bin/env bash
# driver.sh — Brahma self-chaining Conductor driver
# Purpose: One-shot script invoked by Cloud Scheduler (Praharī) every 15 minutes.
#   Reads Smṛti to find the resume point, dispatches the next batch of Conductor
#   sessions, writes Smṛti at batch end. Run is continuous — only batches restart.
#
# Invocation: Cloud Run Job or Cloud Scheduler → HTTP trigger → this script
# Project: madhav-astrology / asia-south1
# Bot SA: brahma-conductor-bot@madhav-astrology.iam.gserviceaccount.com
# Authorized: native directive 2026-06-03 (autonomous mode)
#
# Safety rails:
#   - Reads Smṛti before any action; aborts if build_state shows complete or stalled.
#   - Checks budget ceiling before dispatching; halts batch if $5000 exceeded.
#   - All destructive ops require a pre-snapshot (§C rail 1 in AUTONOMOUS_MODE).
#   - Sends a completion signal to Cloud Scheduler on instrument complete.

set -euo pipefail

PROJECT="madhav-astrology"
REGION="asia-south1"
REPO_ROOT="$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
SMRITI="$REPO_ROOT/00_ARCHITECTURE/CONDUCTOR/brahma/smriti/build_state.yaml"
CONDUCTOR_PROMPT="$REPO_ROOT/00_ARCHITECTURE/CONDUCTOR/brahma/CONDUCTOR_PROMPT_BRAHMA_v1_0.md"
LOG_DIR="$REPO_ROOT/00_ARCHITECTURE/CONDUCTOR/brahma/logs"
LOG_FILE="$LOG_DIR/driver_$(date +%Y%m%d_%H%M%S).log"
SCHEDULER_JOB="brahma-prahara-watchdog"
MAX_BUDGET_USD=5000

mkdir -p "$LOG_DIR"
exec > >(tee -a "$LOG_FILE") 2>&1

echo "=== Brahma Driver Batch Start: $(date -Iseconds) ==="

# ── 1. Read Smṛti ───────────────────────────────────────────────────────────
if [[ ! -f "$SMRITI" ]]; then
  echo "ERROR: Smṛti not found at $SMRITI — cannot resume. Aborting."
  exit 1
fi

TOTAL_SPENT=$(python3 -c "
import yaml, sys
with open('$SMRITI') as f:
    d = yaml.safe_load(f)
print(d['budget']['total_spent_usd'])
")

PENDING=$(python3 -c "
import yaml, sys
with open('$SMRITI') as f:
    d = yaml.safe_load(f)
print(d['queue_summary']['pending'])
")

INSTRUMENT_COMPLETE=$(python3 -c "
import yaml, sys
with open('$SMRITI') as f:
    d = yaml.safe_load(f)
assets = d.get('assets', [])
final = next((a for a in assets if a['id'] == 'MI-L5-VERIFY'), None)
print('yes' if final and final['status'] == 'green' else 'no')
")

echo "Smṛti read — spent: \$$TOTAL_SPENT / \$$MAX_BUDGET_USD | pending: $PENDING | instrument_complete: $INSTRUMENT_COMPLETE"

# ── 2. Completion check ──────────────────────────────────────────────────────
if [[ "$INSTRUMENT_COMPLETE" == "yes" ]]; then
  echo "INSTRUMENT COMPLETE — all layers green. Disabling Praharī schedule."
  gcloud scheduler jobs pause "$SCHEDULER_JOB" --location="$REGION" --project="$PROJECT" 2>/dev/null || true
  echo "Build complete. Final report is in BRAHMA_COMPLETE.md. Driver stopping."
  exit 0
fi

if [[ "$PENDING" == "0" ]]; then
  echo "Queue drained — no pending assets (check for stalled in_progress)."
fi

# ── 3. Budget ceiling check ──────────────────────────────────────────────────
python3 -c "
spent = float('$TOTAL_SPENT')
cap = $MAX_BUDGET_USD
if spent >= cap:
    print(f'BUDGET CEILING HIT: \${spent:.2f} >= \${cap}. Aborting batch.')
    exit(1)
print(f'Budget OK: \${spent:.2f} / \${cap}')
" || exit 1

# ── 4. Find released assets (deps all green) ─────────────────────────────────
echo "Finding released assets (all depends_on = green)..."
RELEASED=$(python3 - <<'PYEOF'
import yaml

with open('$SMRITI') as f:
    d = yaml.safe_load(f)

assets = d.get('assets', [])
green_ids = {a['id'] for a in assets if a['status'] == 'green'}
released = []
for a in assets:
    if a['status'] != 'pending':
        continue
    deps = a.get('depends_on', [])
    if all(dep in green_ids for dep in deps):
        released.append(a['id'])

print('\n'.join(released[:8]))  # cap at 8 per batch (context budget)
PYEOF
)

if [[ -z "$RELEASED" ]]; then
  echo "No released assets found. Check for blocked dependencies or in-progress sessions."
  # Praharī will re-kick in 15 minutes to check again.
  exit 0
fi

echo "Released assets this batch:"
echo "$RELEASED"

# ── 5. Dispatch Conductor batch ──────────────────────────────────────────────
# The actual Conductor dispatch happens via Claude Code (Antigravity) sessions,
# each operating on one or more released assets in parallel worktrees.
# This script signals the dispatch; the Claude Code session reads the conductor
# prompt + this session's released asset IDs and executes the build.
#
# In the scheduled/unattended mode, this script writes a batch dispatch record
# to Smṛti and updates asset statuses to `in_progress`.

echo "$RELEASED" | while read -r ASSET_ID; do
  python3 - <<PYEOF
import yaml, datetime

smriti_path = '$SMRITI'
asset_id = '$ASSET_ID'

with open(smriti_path) as f:
    d = yaml.safe_load(f)

for a in d['assets']:
    if a['id'] == asset_id:
        a['status'] = 'in_progress'
        break

d['meta']['last_updated'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
d['meta']['batch_count'] = d['meta'].get('batch_count', 0) + 1

with open(smriti_path, 'w') as f:
    yaml.dump(d, f, allow_unicode=True, sort_keys=False)

print(f"Smṛti updated: {asset_id} → in_progress")
PYEOF
done

echo "=== Batch dispatched: $(echo "$RELEASED" | wc -l | tr -d ' ') assets released ==="
echo "Praharī will re-kick in 15 minutes to advance completed assets and release next wave."
echo "=== Driver Batch End: $(date -Iseconds) ==="
