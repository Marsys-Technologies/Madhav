#!/usr/bin/env bash
# Keep the Suvarṇa tracker running: restart it if it ever exits. Stop with: touch $SUVARNA_HOME/run/TRACKER_STOP
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
export SUVARNA_HOME="${SUVARNA_HOME:-/Users/Dev/suvarna}"
RUN="$SUVARNA_HOME/run"; mkdir -p "$RUN"
PORT="${SUVARNA_TRACKER_PORT:-8765}"
rm -f "$RUN/TRACKER_STOP"
echo $$ > "$RUN/tracker_supervisor.pid"
while [ ! -f "$RUN/TRACKER_STOP" ]; do
  echo "$(date '+%F %T') starting tracker on :$PORT" >> "$RUN/tracker.log"
  ( cd "$HERE/.." && python3 -m suvarna_tracker.server --port "$PORT" ) >> "$RUN/tracker.log" 2>&1
  rc=$?  # capture before any other command (a $(date) substitution would reset it)
  echo "$(date '+%F %T') tracker exited (rc=$rc); restarting in 2s" >> "$RUN/tracker.log"
  sleep 2
done
echo "$(date '+%F %T') supervisor stopped by TRACKER_STOP" >> "$RUN/tracker.log"
