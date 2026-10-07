#!/usr/bin/env bash
# Operator-run executor loop v1.1 (charter §7). Source ~/.config/kalayantra/executor.env FIRST (it holds the credentials).
#   executor.sh up      snapshot executor.py to $KY_ROOT/exec/ and start it detached (restarts on exit)
#   executor.sh down    stop after in-flight operations finish          executor.sh status
# The executor runs from a SNAPSHOT taken at `up`, and reads its operations table and every script from origin/main —
# so nothing an agent edits in a working tree can change what it does. After a merged change to executor.py: down, then up.
set -u
KY_ROOT="${KY_ROOT:-/Users/Dev/kalayantra}"; SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/executor.py"
RUN="$KY_ROOT/run"; LOGD="$KY_ROOT/logs"; PY="$KY_ROOT/venv/bin/python"; LIVE="$KY_ROOT/exec/executor.py"
mkdir -p "$RUN/ops" "$LOGD" "$KY_ROOT/exec"
case "${1:-status}" in
  up)
    [ -x "$PY" ] || { echo "campaign venv missing at $PY — run fleet/preflight.sh bootstrap first"; exit 1; }
    [ -n "${KY_BUILDER_DATABASE_URL:-}" ] || echo "note: KY_BUILDER_DATABASE_URL is not set — production build operations will be refused with capability_missing (everything else runs)"
    [ -n "${KY_OWNER_DATABASE_URL:-}" ]   || echo "note: KY_OWNER_DATABASE_URL is not set — the small-test teardown will be refused; the small tests then wait (no retention alternative)"
    if pgrep -f "$LIVE" >/dev/null 2>&1; then echo "executor already running"; exit 0; fi
    cp "$SRC" "$LIVE"; rm -f "$RUN/STOP_executor"
    /opt/homebrew/bin/python3 -c 'import os, sys
if os.fork(): os._exit(0)
os.setsid()
if os.fork(): os._exit(0)
log = os.open(sys.argv[3], os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600); null = os.open(os.devnull, os.O_RDONLY)
os.dup2(null, 0); os.dup2(log, 1); os.dup2(log, 2)
os.execvp("bash", ["bash", "-c", "while [ ! -f \"$1\" ]; do \"$2\" \"$3\"; sleep 30; done", "executor-loop", sys.argv[4], sys.argv[1], sys.argv[2]])' "$PY" "$LIVE" "$LOGD/executor.out" "$RUN/STOP_executor"
    sleep 3; echo "executor started from $LIVE; capabilities → $RUN/ops/CAPABILITIES.json"; cat "$RUN/ops/CAPABILITIES.json" 2>/dev/null ;;
  down) touch "$RUN/STOP_executor"; echo "stop requested; in-flight operations finish first" ;;
  status) cat "$RUN/ops/CAPABILITIES.json" 2>/dev/null || echo "no capabilities file — executor not running"; echo "requests waiting: $(ls "$RUN/ops/requests" 2>/dev/null | wc -l | tr -d ' ')  in flight: $(ls "$RUN/ops/inflight" 2>/dev/null | wc -l | tr -d ' ')"; tail -3 "$LOGD/executor.log" 2>/dev/null ;;
  *) echo "usage: $0 up|down|status"; exit 2 ;;
esac
