#!/usr/bin/env bash
# deploy.sh — Push data_progress.html + snapshot file location to GCS
# After this runs, visit https://storage.googleapis.com/marsys-tracker-public/data_progress.html
# The page fetches data_build_status.json (written by poll_daemon.py) every 5s.
#
# Usage:
#   bash 00_ARCHITECTURE/CONDUCTOR/build_orchestrator/data_progress/deploy.sh

set -euo pipefail

BUCKET="${BUCKET:-marsys-tracker-public}"
DIR="$(cd "$(dirname "$0")" && pwd)"

echo "==> Pushing data_progress.html to gs://$BUCKET/data_progress.html"
gcloud storage cp "$DIR/data_progress.html" "gs://$BUCKET/data_progress.html" \
  --cache-control="no-cache,max-age=0"

# Initial empty snapshot (so the page doesn't 404 before the daemon writes)
if [ ! -f "$DIR/data_build_status.json" ]; then
  cat > "$DIR/data_build_status.json" <<JSON
{"snapshot_at":"$(date -u +%Y-%m-%dT%H:%M:%SZ)","chart_id":"362f9f17-95a5-490b-a5a7-027d3e0efda0","build":null,"chart_facts":{"total_rows":0,"by_ayanamsha_asset":[],"by_ayanamsha_rollup":[],"verification":{}},"l25_tables":[],"migrations":[],"migrations_applied_count":0,"note":"Daemon not yet running."}
JSON
fi
gcloud storage cp "$DIR/data_build_status.json" "gs://$BUCKET/data_build_status.json" \
  --cache-control="no-cache,max-age=0"

echo ""
echo "============================================================"
echo "Data-build tracker live at:"
echo "  https://storage.googleapis.com/marsys-tracker-public/data_progress.html"
echo ""
echo "Start the polling daemon to populate snapshots:"
echo "  bash platform/scripts/start_db_proxy.sh &"
echo "  pip install psycopg2-binary --break-system-packages 2>/dev/null || pip install psycopg2-binary"
echo "  python3 $DIR/poll_daemon.py"
echo ""
echo "Daemon writes a snapshot every 20s and auto-pushes to GCS."
echo "============================================================"
