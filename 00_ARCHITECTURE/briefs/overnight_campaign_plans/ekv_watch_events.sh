#!/usr/bin/env bash
# ekv_watch_events.sh — emits one line per meaningful EKAVAKYATA event.
# Local files (supervisor.log, stream logs) are tailed directly, so those are
# true real-time. The coordination branch and manifest live in git, which has
# no push mechanism, so those are diffed on a tight poll (45s) instead of
# tailed — still far tighter than checking every 30 minutes by hand.
# Exits (ending the watch) on a terminal marker: EKAVAKYATA COMPLETE or PARTIAL.
set -u
REPO=/Users/Dev/Vibe-Coding/Apps/Madhav
SHAD=/Users/Dev/shad_overnight
SUP_LOG="$HOME/.ekv-overnight-supervisor/supervisor.log"
COORD_FILE=00_ARCHITECTURE/briefs/CAMPAIGN_COORDINATION.md
MANIFEST_FILE=00_ARCHITECTURE/briefs/ekavakyata/ekv_manifest.json

STATE_DIR=$(mktemp -d)
: > "$STATE_DIR/coord.full.last"
: > "$STATE_DIR/manifest.last"

# --- real-time tails of local files -----------------------------------------
while [ ! -f "$SUP_LOG" ]; do sleep 2; done
tail -F -n0 "$SUP_LOG" 2>/dev/null | sed 's/^/[supervisor] /' &
TAIL_PIDS=($!)

for l in A B C D E; do
  f="$SHAD/ekv-logs/stream_${l}.log"
  ( while [ ! -f "$f" ]; do sleep 5; done
    echo "[stream-$l] log file appeared — stream launched"
    tail -F -n0 "$f" 2>/dev/null | grep -E --line-buffered "ERROR|FAILED|EKV-|LIVE|HANDOFF|BLOCKED|crash|Traceback|exit" \
      | sed "s/^/[stream-$l] /" ) &
  TAIL_PIDS+=($!)
done

cleanup() { for p in "${TAIL_PIDS[@]}"; do kill "$p" 2>/dev/null; done; }
trap cleanup EXIT

# --- poll loop: coordination branch + manifest (git has no push) -----------
FIRST=1
while true; do
  if ! pgrep -f "ekv_supervisor.sh" >/dev/null 2>&1; then
    echo "[ALERT] ekv_supervisor.sh is not running — supervision has stopped, investigate now"
  fi

  git -C "$REPO" fetch origin campaign-coordination --quiet 2>/dev/null
  content=$(git -C "$REPO" show "origin/campaign-coordination:$COORD_FILE" 2>/dev/null)
  if [ -n "$content" ]; then
    echo "$content" > "$STATE_DIR/coord.full.new"
    if [ "$FIRST" != "1" ]; then
      diff "$STATE_DIR/coord.full.last" "$STATE_DIR/coord.full.new" 2>/dev/null \
        | grep '^>' | grep -v '^> $' | sed 's/^> /[coord] /'
    fi
    mv "$STATE_DIR/coord.full.new" "$STATE_DIR/coord.full.last"

    term=$(echo "$content" | python3 "$SHAD/ekv_terminal_check.py")
    if [ "$term" = "COMPLETE" ]; then
      echo "[TERMINAL] EKAVAKYATA reports COMPLETE"
      exit 0
    fi
    if [ "$term" = "PARTIAL" ]; then
      echo "[TERMINAL] EKAVAKYATA reports PARTIAL — honest gated close, not a crash"
      exit 0
    fi
  fi

  manifest=$(git -C "$REPO" show "origin/campaign-coordination:$MANIFEST_FILE" 2>/dev/null)
  if [ -n "$manifest" ]; then
    echo "$manifest" > "$STATE_DIR/manifest.new"
    if [ "$FIRST" != "1" ] && [ -s "$STATE_DIR/manifest.last" ]; then
      python3 - "$STATE_DIR/manifest.last" "$STATE_DIR/manifest.new" <<'PYEOF'
import json, sys
def lanes(path):
    try:
        return {l["lane"]: l.get("status") for l in json.load(open(path)).get("lanes", [])}
    except Exception:
        return {}
old, new = lanes(sys.argv[1]), lanes(sys.argv[2])
for lane, st in new.items():
    if old.get(lane) != st:
        print(f"[lane] {lane}: {old.get(lane, 'new')} -> {st}")
PYEOF
    elif [ "$FIRST" == "1" ]; then
      echo "[manifest] seeded ($(echo "$manifest" | python3 -c 'import json,sys; print(len(json.load(sys.stdin).get("lanes",[])))' 2>/dev/null) lanes)"
    fi
    mv "$STATE_DIR/manifest.new" "$STATE_DIR/manifest.last"
  fi

  FIRST=0
  sleep 45
done
