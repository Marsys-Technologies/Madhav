#!/usr/bin/env bash
# stop_daemon.sh — Stop the poll_daemon supervisor (and the daemon it manages).
# Usage: bash 00_ARCHITECTURE/CONDUCTOR/build_orchestrator/data_progress/stop_daemon.sh
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
PIDFILE="$DIR/daemon.pid"

if [ ! -f "$PIDFILE" ]; then
  echo "No pidfile — daemon not running?"
  exit 0
fi

SUPERVISOR_PID=$(cat "$PIDFILE")

if kill -0 "$SUPERVISOR_PID" 2>/dev/null; then
  echo "Stopping supervisor pid=$SUPERVISOR_PID"
  kill -TERM "$SUPERVISOR_PID" 2>/dev/null || true
  pkill -P "$SUPERVISOR_PID" 2>/dev/null || true
  sleep 2
  kill -9 "$SUPERVISOR_PID" 2>/dev/null || true
else
  echo "Supervisor pid=$SUPERVISOR_PID no longer running (cleaning up stale files)"
fi
# Also kill any orphaned poll_daemon.py children (handles crash-respawn edge cases)
pkill -9 -f "poll_daemon.py" 2>/dev/null || true

rm -f "$PIDFILE" "$DIR/_supervisor.sh"
echo "Daemon stopped."
