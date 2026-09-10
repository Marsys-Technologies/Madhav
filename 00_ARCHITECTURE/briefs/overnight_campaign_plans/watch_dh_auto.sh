#!/bin/bash
# Auto-following watcher for a Δ-stream: watch_dh_auto.sh d1|d2|d3
# Unlike watch_dh.sh, this survives attempt-log rotation (session cycling) by
# re-attaching to the newest attempt_*.log whenever the supervisor starts one.
S="${1:?usage: watch_dh_auto.sh d1|d2|d3}"
case "$S" in d1|d2|d3) ;; *) echo "usage: watch_dh_auto.sh d1|d2|d3"; exit 1;; esac
LOG_DIR="/Users/Dev/shad_overnight/dh-$S-logs"

if ! pgrep -f "run_dh_$S.sh" >/dev/null 2>&1; then
  echo "⚠ stream $S supervisor NOT running. Start:"
  echo "  nohup caffeinate -i /Users/Dev/shad_overnight/run_dh_$S.sh </dev/null >/dev/null 2>&1 & disown"
  exit 1
fi

CURRENT=""
while true; do
  NEWEST=$(ls -t "$LOG_DIR"/attempt_*.log 2>/dev/null | head -1)
  if [ -z "$NEWEST" ]; then
    echo "waiting for first conductor output…"; sleep 3; continue
  fi
  if [ "$NEWEST" != "$CURRENT" ]; then
    CURRENT="$NEWEST"
    echo
    echo "── [$S] attached: $(basename "$CURRENT")  ($(date +%H:%M:%S))  — Ctrl-C to stop watching ──"
  fi
  # tail -f this file; exit the tail loop the moment a NEWER file appears.
  # Process-substitution (not a literal `|`) so $! is tail's OWN pid, not the
  # python consumer's — a bare pipe backgrounds tail invisibly, so killing $!
  # (python) on rotation orphaned tail forever, still attached to the OLD
  # file (confirmed live 2026-08-14: 5+ orphaned tails piled up per stream,
  # and the watcher stopped detecting rotation was even visible in the log).
  tail -n 0 -f "$CURRENT" 2>/dev/null > >(python3 -u /Users/Dev/shad_overnight/watch_parishkara.py) &
  TAILPID=$!
  while kill -0 $TAILPID 2>/dev/null; do
    LATEST=$(ls -t "$LOG_DIR"/attempt_*.log 2>/dev/null | head -1)
    if [ "$LATEST" != "$CURRENT" ] && [ -n "$LATEST" ]; then
      kill $TAILPID 2>/dev/null
      break
    fi
    sleep 2
  done
  wait $TAILPID 2>/dev/null
done
