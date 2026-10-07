#!/usr/bin/env bash
# precheck_bg.sh <ITEM> — start the pre-push check DETACHED from the current cycle.
# The supervisor kills a cycle's whole process group when the cycle ends, so a check started in the cycle (foreground or with &)
# dies with it and the next cycle starts it again — the "runaway test" of 2026-10-07. This launcher double-forks into its own
# session; the check finishes on its own and the NEXT cycle reads the result:
#   $KY_ROOT/run/precheck/<lane>.status   RUNNING | GREEN | RED        $KY_ROOT/run/precheck/<lane>.log   the full output
# Idempotent: a check already RUNNING for this lane is not started twice. Run it from the lane worktree's root.
set -u
KY_ROOT="${KY_ROOT:-/Users/Dev/kalayantra}"; lane="${KY_LANE:?KY_LANE must be set}"; item="${1:-${KY_ITEM:-}}"
[ -n "$item" ] || { echo "usage: precheck_bg.sh <ITEM-ID>"; exit 2; }
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; D="$KY_ROOT/run/precheck"; mkdir -p "$D"
WT="$(git rev-parse --show-toplevel 2>/dev/null)" || { echo "run this from inside your lane worktree"; exit 2; }
if [ "$(cat "$D/$lane.status" 2>/dev/null)" = RUNNING ] && pgrep -f "precheck_bg_run $lane " >/dev/null 2>&1; then
  echo "a check is already RUNNING for $lane (item $(cat "$D/$lane.item" 2>/dev/null)); read $D/$lane.status next cycle"; exit 0
fi
echo RUNNING > "$D/$lane.status"; echo "$item" > "$D/$lane.item"; : > "$D/$lane.log"; rm -f "$D/$lane.exit"
/opt/homebrew/bin/python3 - "$HERE/precheck.sh" "$WT" "$lane" "$item" "$D" <<'PYEOF'
import os, sys
script, wt, lane, item, d = sys.argv[1:6]
if os.fork(): os._exit(0)
os.setsid()
if os.fork(): os._exit(0)
log = os.open(f"{d}/{lane}.log", os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600); null = os.open(os.devnull, os.O_RDONLY)
os.dup2(null, 0); os.dup2(log, 1); os.dup2(log, 2); os.chdir(wt); os.environ["KY_ITEM"] = item; os.environ["KY_LANE"] = lane
cmd = f'bash "$2"; rc=$?; echo $rc > "{d}/{lane}.exit"; if [ $rc -eq 0 ]; then echo GREEN > "{d}/{lane}.status"; else echo RED > "{d}/{lane}.status"; fi'
os.execvp("bash", ["bash", "-c", cmd, "precheck_bg_run", lane, script, item])
PYEOF
echo "precheck started detached for $lane / $item → $D/$lane.status (RUNNING); log $D/$lane.log. End this cycle; read the status next cycle."
