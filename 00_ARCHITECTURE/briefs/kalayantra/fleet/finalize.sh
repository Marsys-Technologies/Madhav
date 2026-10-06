#!/usr/bin/env bash
# External finalizer v1.2 (charter §12) — run by the executor on a `finalize` request after C-2 is done and the close PR merged.
# TWO PHASES, and a failure in either is recorded as a failure, never as an accepted receipt:
#   1. DRAIN  — stop every lane except v1, prove their locks released, remove only CLEAN worktrees → run/DRAIN_RECEIPT.json
#               (result ACCEPTED only when every lane stopped, none is dirty, every removal succeeded). C-3 reads this.
#   2. FINAL  — record C-3 through the tracker's guard (retried until v1 has accepted the drain receipt); wait for v1's independent
#               final review (run/reviews/FINAL_REVIEW.json: result ACCEPTED, by v1, bound to this drain receipt's sha256) and for
#               v1 to stop itself; remove
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

# ── phase 2: final ────────────────────────────────────────────────────────────────────────────────────────────────────────
c3_done=0     # the conductor is stopped; C-3 completes through the tracker's guard once v1 has independently accepted the drain receipt
for i in $(seq 1 "$FINAL_WAIT_MIN"); do
  if [ "$c3_done" -eq 0 ]; then
    KY_STREAM=S "$KY_ROOT/bin/ky" done C-3 --evidence "$RUN/DRAIN_RECEIPT.json; independent artifact acceptance" >/dev/null 2>&1 && c3_done=1
  fi
  if [ "$c3_done" -eq 1 ] && [ -s "$RUN/reviews/FINAL_REVIEW.json" ] && lock_free v1; then break; fi
  sleep "$POLL_S"
done
review="$("$PY" -c 'import hashlib, json, pathlib, sys
root = pathlib.Path(sys.argv[1])
try:
    r = json.loads((root / "reviews/FINAL_REVIEW.json").read_text())
    digest = hashlib.sha256((root / "DRAIN_RECEIPT.json").read_bytes()).hexdigest()
    accepted = r.get("result") == "ACCEPTED" and r.get("by") == "v1" and r.get("drain_sha256") == digest
except (OSError, ValueError): accepted = False
print("ACCEPTED" if accepted else "MISSING_OR_REJECTED")' "$RUN")"
v1state="busy_kept"; ok=1
if lock_free v1; then v1state="$(remove_clean v1)" || ok=0; else ok=0; fi
remaining="$(pgrep -fl 'codex exec' | grep -c "$WT/" || true)"; left="$(ls "$WT" 2>/dev/null | grep -vx campaign | tr '\n' ' ')"
[ "$c3_done" -eq 1 ] && [ "${remaining:-0}" = 0 ] && [ -z "$left" ] && [ "$review" = ACCEPTED ] && [ -s "$RUN/FINAL_MESSAGE_DRAFT.md" ] || ok=0
receipt "$RUN/FINAL_RECEIPT.json" "$([ $ok -eq 1 ] && echo ACCEPTED || echo FAILED)" "$states v1=$v1state" \
  "{\"phase\": \"final\", \"fleet_processes_remaining\": ${remaining:-0}, \"worktrees_remaining\": \"$left\", \"final_review_result\": \"$review\"}"
if [ -s "$RUN/FINAL_MESSAGE_DRAFT.md" ]; then
  { cat "$RUN/FINAL_MESSAGE_DRAFT.md"; printf '\n\n---\nPhysical shutdown (measured by the finalizer, not by an agent): %s. Receipt: %s\n' "$([ $ok -eq 1 ] && echo 'all ten lanes stopped and their worktrees removed' || echo 'INCOMPLETE — see the receipt')" "$RUN/FINAL_RECEIPT.json"; } > "$RUN/FINAL_MESSAGE.md"
fi
cat "$RUN/FINAL_RECEIPT.json"
if [ "$ok" -eq 1 ]; then
  KY_STREAM=S "$KY_ROOT/bin/ky" done C-4 --evidence "$RUN/FINAL_RECEIPT.json; $RUN/reviews/FINAL_REVIEW.json" >/dev/null 2>&1 || { echo "the tracker refused C-4's guarded completion"; exit 1; }
fi
[ $ok -eq 1 ]
