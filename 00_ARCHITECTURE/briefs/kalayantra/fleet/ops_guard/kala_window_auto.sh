#!/bin/bash
# Auto-dispatches the protected Kāla migration window (deploy.yml kala_schema_migration=true) whenever origin/main's derived membership
# lists a migration not covered by the last SUCCESSFUL window, and only when main's head has a completed, successful
# "CI — Ganga Quality Gate" run. Owner A3 hand-off (2026-10-15).
# A8 item 19: before dispatching the SAME set again it reads why the last run failed (kala_window_decide.py): a gate/SQL/unknown
# failure holds until main moves; an infrastructure failure retries after 30 min, at most 3 times per head. Installed at
# /Users/Dev/kalayantra/ops-guard/kala_window_auto.sh (launchd com.madhav.kalayantra.kalawindow); this file is its repo source (W2-M-08).
# W2-M-08: just before it dispatches, it runs window_lease_gate.py (installed beside it in ops-guard) and holds while a production lease other
# than KY_KWA_OWN_LEASE (none by default) is ACTIVE on origin/campaign-coordination, or the lease table cannot be read (fail closed).
R="${KY_REPO:-/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-review}"; S="${KY_KWA_STATE:-/Users/Dev/kalayantra/run/KALA_WINDOW_STATE.json}"
G="${KY_KWA_GUARD:-/Users/Dev/kalayantra/ops-guard}"; GATE="${KY_KWA_LEASE_GATE:-$G/window_lease_gate.py}"; FAIL="${KY_KWA_FAIL:-$G/kala_window_last_failure.json}"; D="${KY_KWA_DECIDE:-$G/kala_window_decide.py}"
export PATH="$PATH:/opt/homebrew/bin:/usr/local/bin"
cd "$R" || exit 1
last_hold=""
while true; do
  git fetch -q origin main 2>/dev/null
  head=$(git rev-parse origin/main)
  # madhav-6d 2026-10-17: membership is DERIVED by the repo's own selector at origin/main (the .txt is only the legacy seed)
  new=$(python3 $G/kala_window_select.py $R $S 2>>$G/kala_window_auto.log) || new=""
  listed=$(python3 -c "import importlib.util as u;s=u.spec_from_file_location('s','$G/kala_window_select.py');m=u.module_from_spec(s);s.loader.exec_module(m);print('\n'.join(m.derived('$R')))" 2>/dev/null)
  if [ -n "$new" ]; then
    c=$(gh run list --commit "$head" --workflow "CI — Ganga Quality Gate" --json status,conclusion -q '.[0].status+"/"+(.[0].conclusion//"")' 2>/dev/null)
    if [ "$c" = "completed/success" ]; then
      verdict=$(python3 "$D" decide "$FAIL" "$head" $new 2>/dev/null); drc=$?
      if [ $drc -ne 0 ]; then
        [ "$verdict" != "$last_hold" ] && echo "$(date -u +%FT%TZ) $verdict"; last_hold="$verdict"   # logged once per change, not every tick
      else
        lease=$(python3 "$GATE" --repo "$R" --own-lease "${KY_KWA_OWN_LEASE:-}" 2>&1); lrc=$?   # W2-M-08: any failure of the gate, even a missing script, holds
        if [ $lrc -ne 0 ]; then
          [ "$lease" != "$last_hold" ] && echo "$(date -u +%FT%TZ) HOLD lease gate: ${lease:-gate did not run}"; last_hold="$lease"
          sleep 180; continue
        fi
        last_hold=""
        echo "$(date -u +%FT%TZ) dispatching window at $head for: $(echo $new | tr '\n' ' ')"
        gh workflow run deploy.yml --ref main -f kala_schema_migration=true ${KY_KWA_OWN_LEASE:+-f window_lease_id="$KY_KWA_OWN_LEASE"} 2>&1 | tail -1
        sleep 30; rid=$(gh run list --workflow deploy.yml --event workflow_dispatch --limit 1 --json databaseId -q '.[0].databaseId')
        until [ "$(gh run view $rid --json status -q .status 2>/dev/null)" = completed ]; do sleep 60; done
        concl=$(gh run view $rid --json conclusion -q .conclusion); echo "$(date -u +%FT%TZ) run $rid: $concl"
        if [ "$concl" = success ]; then
          rm -f "$FAIL"
          python3 -c "
import json,sys;json.dump({'applied':sys.argv[1].split(),'last_run':'$rid','head':'$head','ts':'$(date -u +%FT%TZ)'},open('$S','w'),indent=1)" "$listed"
        else
          cause=$(gh run view $rid --log-failed 2>/dev/null | head -400 | python3 "$D" classify); cls=${cause%%$'\t'*}; line=${cause#*$'\t'}
          python3 "$D" record "$FAIL" "$rid" "$head" "$cls" "$line" $new
          echo "$(date -u +%FT%TZ) run $rid failed: class=$cls ${line:0:160}"
        fi
      fi
    fi
  fi
  sleep 180
done
