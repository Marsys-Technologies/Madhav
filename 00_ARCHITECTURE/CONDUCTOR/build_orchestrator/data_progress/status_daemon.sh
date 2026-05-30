#!/usr/bin/env bash
# status_daemon.sh — Show daemon liveness, heartbeat age, and process info.
# Usage: bash 00_ARCHITECTURE/CONDUCTOR/build_orchestrator/data_progress/status_daemon.sh
DIR="$(cd "$(dirname "$0")" && pwd)"
PIDFILE="$DIR/daemon.pid"

if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
  echo "✓ Daemon running (supervisor pid $(cat "$PIDFILE"))"
  ps -p "$(cat "$PIDFILE")" -o pid,etime,command 2>/dev/null || true
  if [ -f "$DIR/daemon_heartbeat.json" ]; then
    HB_FILE="$DIR/daemon_heartbeat.json"
    python3 -c "
import json, datetime, pathlib
try:
    hb = json.loads(pathlib.Path('$HB_FILE').read_text())
    last = hb.get('last_heartbeat_at', 'unknown')
    pid  = hb.get('daemon_pid', '?')
    ver  = hb.get('daemon_version', '?')
    print(f'Last heartbeat : {last}')
    print(f'Daemon pid     : {pid}  version: {ver}')
    if last != 'unknown':
        dt = datetime.datetime.fromisoformat(last.replace('Z', '+00:00'))
        age = (datetime.datetime.now(datetime.timezone.utc) - dt).total_seconds()
        suffix = '(STALE)' if age > 120 else '(fresh)'
        print(f'Heartbeat age  : {int(age)}s {suffix}')
except Exception as e:
    print(f'Could not parse heartbeat: {e}')
"
  fi
else
  echo "✗ Daemon NOT running"
  if [ -f "$PIDFILE" ]; then
    echo "  (stale pidfile present — pid $(cat "$PIDFILE"))"
  fi
fi
