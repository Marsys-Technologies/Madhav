#!/bin/sh
# Dependency-free desktop/mobile browser smoke check for the loopback-only CG-0 proof.
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
TRACKER="$ROOT/00_ARCHITECTURE/briefs/pariprashna_assurance/tracker"
CHROME=${CHROME_BIN:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}
RUNTIME=$(mktemp -d /private/tmp/pariprashna-browser-XXXXXX)
DOM=$(mktemp /private/tmp/pariprashna-dom-XXXXXX)
SHOT=$(mktemp /private/tmp/pariprashna-mobile-XXXXXX).png
PORT=8791
PID=

cleanup() {
  status=$?
  trap - EXIT
  if [ -n "$PID" ]; then kill "$PID" 2>/dev/null || true; fi
  rm -rf "$RUNTIME" "$DOM" "$SHOT"
  exit "$status"
}
trap cleanup EXIT INT TERM

test -x "$CHROME"
python3 "$TRACKER/demo.py" --runtime "$RUNTIME" >/dev/null
python3 "$TRACKER/server.py" --runtime "$RUNTIME" --port "$PORT" >/dev/null 2>&1 &
PID=$!

until curl -fsS "http://127.0.0.1:$PORT/api/projection" >/dev/null; do sleep 0.1; done
"$CHROME" --headless=new --disable-gpu --no-first-run --dump-dom "http://127.0.0.1:$PORT/" >"$DOM" 2>/dev/null
rg -q 'Campaign overview' "$DOM"
rg -q 'Tracker Integrity and Audit' "$DOM"
"$CHROME" --headless=new --disable-gpu --no-first-run --window-size=390,844 --screenshot="$SHOT" "http://127.0.0.1:$PORT/" >/dev/null 2>&1
test -s "$SHOT"
echo 'browser smoke: desktop landmarks and 390px mobile screenshot passed'
