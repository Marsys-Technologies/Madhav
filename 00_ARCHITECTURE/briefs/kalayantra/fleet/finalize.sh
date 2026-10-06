#!/usr/bin/env bash
# External finalizer v1.2 (charter §12) — run by the executor on a `finalize` request after C-2 is done and the close PR merged.
# TWO PHASES, and a failure in either is recorded as a failure, never as an accepted receipt:
#   1. DRAIN  — stop every lane except v1, prove their locks released, remove only CLEAN worktrees → run/DRAIN_RECEIPT.json
#               (result ACCEPTED only when every lane stopped, none is dirty, every removal succeeded). C-3 reads this.
#   2. FINAL  — wait for lane v1's independent final review (run/reviews/FINAL_REVIEW.json) and for v1 to stop itself; remove
#               its clean worktree; verify all ten lanes stopped and their worktrees gone; write run/FINAL_RECEIPT.json and
#               run/FINAL_MESSAGE.md (from the reviewed draft plus the measured shutdown facts). C-4 reads this.
# Never removes wt/campaign, a branch or evidence. Never removes a dirty or busy worktree.
set -u
KY_ROOT="${KY_ROOT:-/Users/Dev/kalayantra}"; RUN="$KY_ROOT/run"; WT="$KY_ROOT/wt"; GIT="$WT/campaign"; PY=/opt/homebrew/bin/python3
DRAIN_WAIT_MIN="${KY_DRAIN_WAIT_MIN:-120}"; FINAL_WAIT_MIN="${KY_FINAL_WAIT_MIN:-180}"; POLL_S="${KY_FINAL_POLL_S:-60}"   # the three are shortened only by tests
OTHERS=(sutradhara adhikarin v2 k1 k2 k3 k4 k5 k6)
lock_free() { "$PY" -c 'import fcntl, sys
f = open(sys.argv[1], "a+")
try: fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
except BlockingIOError: sys.exit(1)' "$RUN/$1.lock"; }
remove_clean() {   # remove_clean <lane> → prints the lane's state
  local wt="$WT/$1"
  if [ ! -e "$wt/.git" ]; then echo "absent"; return 0; fi
  if [ -n "$(git -C "$wt" status --porcelain 2>/dev/null)" ]; then echo "dirty_kept"; return 1; fi
  git -C "$GIT" worktree remove "$wt" >/dev/null 2>&1 && { echo "removed"; return 0; } || { echo "remove_failed"; return 1; }
}
receipt() { "$PY" -c 'import datetime, json, sys
out, result, states, extra = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
d = {"ts": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), "result": result,
     "lanes": dict(kv.split("=", 1) for kv in states.split() if "=" in kv), "branches": "kept", "campaign_worktree": "kept"}
d.update(json.loads(extra)); json.dump(d, open(out, "w"), indent=1)' "$@"; }

# ── phase 1: drain ────────────────────────────────────────────────────────────────────────────────────────────────────────
for l in "${OTHERS[@]}"; do touch "$RUN/STOP_$l"; done
busy=""; for i in $(seq 1 "$DRAIN_WAIT_MIN"); do
  busy=""; for l in "${OTHERS[@]}"; do lock_free "$l" || busy="$busy $l"; done
  [ -z "$busy" ] && break; sleep "$POLL_S"
done
states=""; ok=1
for l in "${OTHERS[@]}"; do
  if echo " $busy " | grep -q " $l "; then states="$states $l=busy_kept"; ok=0; continue; fi
  s="$(remove_clean "$l")" || ok=0; states="$states $l=$s"
done
touch /Users/Dev/pravaha/run/RUNNER_STOP_A /Users/Dev/pravaha/run/RUNNER_STOP_B /Users/Dev/pravaha/run/RUNNER_STOP_C 2>/dev/null || true
receipt "$RUN/DRAIN_RECEIPT.json" "$([ $ok -eq 1 ] && echo ACCEPTED || echo FAILED)" "$states" '{"phase": "drain", "v1": "left running for the final review", "pravaha_writers": "frozen (RUNNER_STOP_* written)"}'
cat "$RUN/DRAIN_RECEIPT.json"
[ $ok -eq 1 ] || { echo "DRAIN FAILED — nothing further is removed; the final receipt is not written"; exit 1; }
KY_STREAM=S "$KY_ROOT/bin/ky" done C-3 --evidence "run/DRAIN_RECEIPT.json ACCEPTED" >/dev/null 2>&1 || true    # the conductor is stopped; the tracker's guard still decides

# ── phase 2: final ────────────────────────────────────────────────────────────────────────────────────────────────────────
for i in $(seq 1 "$FINAL_WAIT_MIN"); do
  if [ -s "$RUN/reviews/FINAL_REVIEW.json" ] && lock_free v1; then break; fi; sleep "$POLL_S"
done
review="$("$PY" -c 'import json, sys
try: print(json.load(open(sys.argv[1])).get("result", "MISSING"))
except Exception: print("MISSING")' "$RUN/reviews/FINAL_REVIEW.json")"
v1state="busy_kept"; ok=1
if lock_free v1; then v1state="$(remove_clean v1)" || ok=0; else ok=0; fi
remaining="$(pgrep -fl 'codex exec' | grep -c "$WT/" || true)"; left="$(ls "$WT" 2>/dev/null | grep -vx campaign | tr '\n' ' ')"
[ "${remaining:-0}" = 0 ] && [ -z "$left" ] && [ "$review" != MISSING ] || ok=0
receipt "$RUN/FINAL_RECEIPT.json" "$([ $ok -eq 1 ] && echo ACCEPTED || echo FAILED)" "$states v1=$v1state" \
  "{\"phase\": \"final\", \"fleet_processes_remaining\": ${remaining:-0}, \"worktrees_remaining\": \"$left\", \"final_review_result\": \"$review\"}"
if [ -s "$RUN/FINAL_MESSAGE_DRAFT.md" ]; then
  { cat "$RUN/FINAL_MESSAGE_DRAFT.md"; printf '\n\n---\nPhysical shutdown (measured by the finalizer, not by an agent): %s. Receipt: %s\n' "$([ $ok -eq 1 ] && echo 'all ten lanes stopped and their worktrees removed' || echo 'INCOMPLETE — see the receipt')" "$RUN/FINAL_RECEIPT.json"; } > "$RUN/FINAL_MESSAGE.md"
fi
cat "$RUN/FINAL_RECEIPT.json"
[ $ok -eq 1 ] && KY_STREAM=S "$KY_ROOT/bin/ky" done C-4 --evidence "run/FINAL_RECEIPT.json ACCEPTED; run/reviews/FINAL_REVIEW.json $review" >/dev/null 2>&1 || true
[ $ok -eq 1 ]
