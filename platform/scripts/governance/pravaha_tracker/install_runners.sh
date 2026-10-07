#!/usr/bin/env bash
# Start (or stop) the headless Kimi runners for Streams A and B. Close the Kimi Code desktop sessions first.
#   start:  bash install_runners.sh            stop:  bash install_runners.sh --stop
#   one stream: bash install_runners.sh A      logs: /Users/Dev/pravaha/run/runner-{A,B}.log + run/runner/{A,B}/
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
STREAMS="C"; STOP=0   # A and B are Claude sessions since 2026-10-02; Kimi runs Stream C only
for a in "$@"; do case "$a" in --stop) STOP=1;; A|B|C) STREAMS="$a";; esac; done
for S in $STREAMS; do
  L=com.madhav.pravaha.runner.$S; DST="$HOME/Library/LaunchAgents/$L.plist"
  launchctl bootout "gui/$(id -u)/$L" 2>/dev/null || true
  if [ $STOP = 1 ]; then rm -f "$DST"; echo "runner $S stopped"; continue; fi
  rm -f /Users/Dev/pravaha/run/RUNNER_STOP_$S
  cp "$HERE/$L.plist" "$DST"; launchctl bootstrap "gui/$(id -u)" "$DST"; launchctl enable "gui/$(id -u)/$L"
  echo "runner $S started — log /Users/Dev/pravaha/run/runner-$S.log"
done
