#!/usr/bin/env bash
# run_daemon.sh — Run poll_daemon under nohup with respawn-on-crash.
# Survives terminal close. Logs to daemon.log (rotated automatically by Python).
# Usage: bash 00_ARCHITECTURE/CONDUCTOR/build_orchestrator/data_progress/run_daemon.sh
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
PIDFILE="$DIR/daemon.pid"

# If already running, abort
if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
  echo "Daemon already running (pid $(cat "$PIDFILE"))"
  exit 0
fi

# Confirm cloud-sql-proxy alive; start if not
if ! pg_isready -h localhost -p 5433 -q 2>/dev/null; then
  echo "Starting cloud-sql-proxy..."
  bash /Users/Dev/Vibe-Coding/Apps/Madhav/platform/scripts/start_db_proxy.sh >/dev/null 2>&1 &
  sleep 5
fi

# Wrapper that respawns on crash (5 attempts within 60s → give up)
cat > "$DIR/_supervisor.sh" <<'SUPERVISOR'
#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CRASH_COUNT=0
LAST_CRASH=0
while true; do
  NOW=$(date +%s)
  if [ $((NOW - LAST_CRASH)) -gt 60 ]; then CRASH_COUNT=0; fi
  if [ $CRASH_COUNT -ge 5 ]; then
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) Too many crashes (5 in 60s); giving up" >> "$SCRIPT_DIR/daemon.log"
    exit 1
  fi
  python3 "$SCRIPT_DIR/poll_daemon.py"
  EXIT_CODE=$?
  [ $EXIT_CODE -eq 0 ] && exit 0
  CRASH_COUNT=$((CRASH_COUNT + 1))
  LAST_CRASH=$(date +%s)
  echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) Daemon crashed (exit $EXIT_CODE); respawning in 5s" >> "$SCRIPT_DIR/daemon.log"
  sleep 5
done
SUPERVISOR
chmod +x "$DIR/_supervisor.sh"

nohup "$DIR/_supervisor.sh" >> "$DIR/daemon.log" 2>&1 &
echo $! > "$PIDFILE"
echo "Daemon supervisor started: pid $(cat "$PIDFILE")"
echo "Logs: tail -f $DIR/daemon.log"
echo "Stop: bash $DIR/stop_daemon.sh"
