#!/bin/bash
# Live view of a Δ-stream conductor: watch_dh.sh d1|d2|d3
S="${1:?usage: watch_dh.sh d1|d2|d3}"
case "$S" in d1|d2|d3) ;; *) echo "usage: watch_dh.sh d1|d2|d3"; exit 1;; esac
LOG_DIR="/Users/Dev/shad_overnight/dh-$S-logs"
if ! pgrep -f "run_dh_$S.sh" >/dev/null 2>&1; then
  echo "⚠ stream $S supervisor NOT running. Start:"
  echo "  nohup caffeinate -i /Users/Dev/shad_overnight/run_dh_$S.sh </dev/null >/dev/null 2>&1 & disown"
  exit 1
fi
echo "waiting for $S conductor output…"
for _ in $(seq 1 120); do
  f=$(ls -t "$LOG_DIR"/attempt_*.log 2>/dev/null | head -1)
  [ -n "$f" ] && [ -s "$f" ] && break
  sleep 2
done
[ -z "$f" ] || [ ! -s "$f" ] && { echo "no output after 4 min — check $LOG_DIR/supervisor.log"; exit 1; }
echo "── [$S] watching: $f (Ctrl-C stops watching only; re-run to attach newer) ──"
tail -n 200 -f "$f" | python3 -u /Users/Dev/shad_overnight/watch_parishkara.py
