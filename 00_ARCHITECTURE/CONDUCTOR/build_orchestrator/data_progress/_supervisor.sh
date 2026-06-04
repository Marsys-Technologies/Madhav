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
