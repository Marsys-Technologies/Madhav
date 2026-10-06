#!/usr/bin/env bash
# External finalizer v1.1 (charter §12) — run by the executor on a `finalize` request after C-2 is done and the close PR merged.
# Stops every lane EXCEPT v1 (which performs the final acceptance C-4 and then stops itself), verifies no other campaign
# process remains, removes only CLEAN lane worktrees (branches kept), freezes the absorbed Pravāha writers, and writes
# run/FINAL_RECEIPT.json (the detector of C-3). Never removes wt/campaign or wt/v1.
set -u
KY_ROOT="${KY_ROOT:-/Users/Dev/kalayantra}"; RUN="$KY_ROOT/run"; WT="$KY_ROOT/wt"; GIT="$WT/campaign"
LANES=(sutradhara adhikarin v2 k1 k2 k3 k4 k5 k6)
for l in "${LANES[@]}"; do touch "$RUN/STOP_$l"; done
for i in $(seq 1 120); do   # up to 2 h: active cycles finish inside their cap, then the lane locks release
  busy=0
  for l in "${LANES[@]}"; do
    /opt/homebrew/bin/python3 -c 'import fcntl, sys
f = open(sys.argv[1], "a+")
try: fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
except BlockingIOError: sys.exit(1)' "$RUN/$l.lock" || busy=1
  done
  [ $busy -eq 0 ] && break; sleep 60
done
remaining="$(pgrep -fl 'codex exec' | grep "$WT/" | grep -vc "$WT/v1" || true)"
removed=(); kept=("v1:final_acceptance" "campaign:kept")
for l in "${LANES[@]}"; do
  wt="$WT/$l"; [ -e "$wt/.git" ] || continue
  if [ -z "$(git -C "$wt" status --porcelain 2>/dev/null)" ]; then git -C "$GIT" worktree remove "$wt" >/dev/null 2>&1 && removed+=("$l") || kept+=("$l:remove_failed"); else kept+=("$l:dirty"); fi
done
touch /Users/Dev/pravaha/run/RUNNER_STOP_A /Users/Dev/pravaha/run/RUNNER_STOP_B /Users/Dev/pravaha/run/RUNNER_STOP_C 2>/dev/null || true
/opt/homebrew/bin/python3 -c 'import datetime, json, sys
json.dump({"ts": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), "fleet_processes_remaining": int(sys.argv[2] or 0),
           "lanes_still_busy_after_wait": int(sys.argv[5]), "worktrees_removed": sys.argv[3].split(), "worktrees_kept": sys.argv[4].split(),
           "branches": "kept", "pravaha_writers": "frozen (RUNNER_STOP_* written)", "v1": "running for C-4; stops itself after the final verdict"},
          open(sys.argv[1], "w"), indent=1)' "$RUN/FINAL_RECEIPT.json" "$remaining" "${removed[*]:-}" "${kept[*]}" "$busy"
cat "$RUN/FINAL_RECEIPT.json"
