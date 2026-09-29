#!/usr/bin/env bash
# Keep the Suvarṇa tracker running: restart it if it ever exits. Stop with: touch $SUVARNA_HOME/run/TRACKER_STOP
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
export SUVARNA_HOME="${SUVARNA_HOME:-/Users/Dev/suvarna}"
# CODE-17 (S13/C2): the register/ledger ref the detectors read, before the E4.3 cut-over the fold
# lanes land as fast-forwards to `campaign/nikasha-test`, never opening a PR — so the tracker reads
# it at `origin/campaign/nikasha-test`, fetched before each read (detectors.py
# `_fetch_nikasha_ref_if_needed`). Strategic Suvarṇa re-points this to `origin/suvarna/trunk` in one
# step at the cut-over (E4.3). NIKASHA_ROOT (detectors.py Config.nikasha_root) may be any checkout
# that has `origin` as a remote — it defaults to the hq worktree the server is started from.
export NIKASHA_REF="${NIKASHA_REF:-origin/campaign/nikasha-test}"
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
