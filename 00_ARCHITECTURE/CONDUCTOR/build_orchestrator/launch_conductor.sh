#!/usr/bin/env bash
# Launch the MARSYS Build Orchestrator Conductor autonomously.
# Run from anywhere — script cd's to the repo first.
set -euo pipefail

REPO="/Users/Dev/Vibe-Coding/Apps/Madhav"
CDIR="$REPO/00_ARCHITECTURE/CONDUCTOR/build_orchestrator"
PROMPT="$CDIR/CLAUDE_CODE_KICKOFF_PROMPT.md"
PIDFILE="$CDIR/conductor.pid"
LOGFILE="$CDIR/CONDUCTOR_RUN.log"

cd "$REPO"

# Preflight
[ -f "$PROMPT" ] || { echo "ERROR: kickoff prompt missing at $PROMPT"; exit 1; }
command -v claude >/dev/null 2>&1 || { echo "ERROR: claude CLI not in PATH"; exit 1; }

# Kill any existing Conductor
if [ -f "$PIDFILE" ]; then
  OLD_PID=$(cat "$PIDFILE")
  if kill -0 "$OLD_PID" 2>/dev/null; then
    echo "Killing prior Conductor PID $OLD_PID"
    kill "$OLD_PID"
    sleep 2
  fi
  rm -f "$PIDFILE"
fi

# Extract the prompt block
PROMPT_BODY=$(sed -n '/^## PROMPT BEGIN/,/^## PROMPT END/p' "$PROMPT")
if [ -z "$PROMPT_BODY" ]; then
  echo "ERROR: PROMPT BEGIN/END markers not found in $PROMPT"; exit 1
fi

# Tracker check (warn only)
if ! curl -s -o /dev/null http://localhost:8765; then
  echo "WARN: tracker not running on :8765. Start with:"
  echo "  cd $CDIR/tracker && python3 -m http.server 8765 &"
fi

# Launch
echo "Launching Conductor…"
nohup env CLAUDE_CODE_MAX_OUTPUT_TOKENS=200000 \
  claude --dangerously-skip-permissions \
    --append-system-prompt "$PROMPT_BODY" \
    --print --output-format=stream-json \
    < /dev/null \
    > "$LOGFILE" 2>&1 &

NEW_PID=$!
echo "$NEW_PID" > "$PIDFILE"

echo "Conductor PID: $NEW_PID"
echo "Logs:          tail -f $LOGFILE"
echo "Tracker:       http://localhost:8765"
echo "Halt:          kill $NEW_PID  (or bash $CDIR/scripts/halt_all.sh once authored)"
