#!/bin/bash
LOG_DIR="/Users/Dev/shad_overnight/sampurti-overnight-logs"
if ! pgrep -f run_sampurti_overnight.sh >/dev/null 2>&1; then
  echo "⚠ supervisor NOT running. Start:"
  echo "  nohup caffeinate -i /Users/Dev/shad_overnight/run_sampurti_overnight.sh </dev/null >/dev/null 2>&1 & disown"
  exit 1
fi
echo "waiting for conductor output…"
for _ in $(seq 1 120); do
  f=$(ls -t "$LOG_DIR"/attempt_*.log 2>/dev/null | head -1)
  [ -n "$f" ] && [ -s "$f" ] && break
  sleep 2
done
[ -z "$f" ] || [ ! -s "$f" ] && { echo "no output after 4 min — check $LOG_DIR/supervisor.log"; exit 1; }
echo "── watching: $f (Ctrl-C stops watching only; re-run to attach to newer attempt) ──"
tail -n 200 -f "$f" | python3 -u /Users/Dev/shad_overnight/watch_parishkara.py
