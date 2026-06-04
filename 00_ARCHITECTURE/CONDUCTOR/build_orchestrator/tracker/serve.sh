#!/usr/bin/env bash
# Persistent tracker server. Auto-restarts the HTTP server if it dies.
# Usage:
#   bash serve.sh                 # foreground (Ctrl+C to stop)
#   nohup bash serve.sh &         # background, survives terminal close
set -u
PORT="${TRACKER_PORT:-8765}"
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

# Free the port if a zombie is holding it
PID=$(lsof -ti :$PORT 2>/dev/null || true)
if [ -n "$PID" ]; then
  echo "Killing prior server on port $PORT (PID $PID)"
  kill "$PID" 2>/dev/null || true
  sleep 1
fi

echo "Tracker serving at http://localhost:$PORT  (auto-restart enabled)"
echo "Logs: $DIR/serve.log"

while true; do
  python3 -m http.server "$PORT" --bind 127.0.0.1 >> "$DIR/serve.log" 2>&1
  echo "[$(date)] Server exited; restarting in 2s" >> "$DIR/serve.log"
  sleep 2
done
