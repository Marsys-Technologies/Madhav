# Merge PR #303 (cockpit-DAG fix) + verify the rings close

**Paste in Claude Code (Antigravity). Lands the cockpit-DAG ring fix on main + confirms the running cockpit shows
the closed rings. The FIX EXISTS but is UNMERGED — this just merges it and verifies. Verify the Cloud Run revision
matches the merge SHA before the final prod cockpit check (the phantom-bug trap).**

---

## THE STATE (verified 2026-06-20)
- **The fix is on `origin/feature/cockpit-dag-remediation` (PR #303), NOT on main.** Confirmed: that branch's
  `ArmillaryGraph.tsx` line ~66 = `built = assets.filter(a => a.state === 'lit' || a.state === 'service_ok' ||
  a.build_state_stale).length`. `origin/main` still has the OLD `state === 'lit'` only.
- **Symptom on the running (pre-fix) cockpit:** Brahmagyan 20/22 ring open (the 2 service assets `bg_panchanga` +
  `bg_ephemeris_engine`), Gaṇita 16/17 ring open (service asset `ga_pyjhora_engine`). These are SERVICE assets
  (`asset_type: 'service'`) — they legitimately have no rows, so old aggregate() excludes them from `built`. The
  fix counts service_ok as built → rings close at 22/22 and 17/17.
- **Heads-up — other unmerged cockpit branches exist** (`fix/cockpit-mount-and-pipeline-gaps`,
  `fix/ga-cockpit-to-main`). Check whether they touch ArmillaryGraph/stats before/after this merge to avoid a
  conflict or a re-revert. If they're stale/superseded by #303, note for cleanup; do NOT merge them blindly.

## STEP 1 — Merge PR #303 to main
1. Confirm PR #303 CI is green (the 22 cockpit tests incl. the 6 new aggregate() assertions).
2. Merge PR #303 (`feature/cockpit-dag-remediation`) → `main` via the PR (squash/merge per your convention).
3. `git fetch origin && git checkout main && git pull` → confirm main's `ArmillaryGraph.tsx` now has the
   `|| a.state === 'service_ok' || a.build_state_stale` line (the fix is on main).

## STEP 2 — Get the fix onto the branch the cockpit RUNS
The localhost cockpit runs whatever branch is checked out. Two cases:
- **If you run localhost off `main`:** just restart the dev server (`next dev --webpack` per [[feedback-turbopack-1624-cpu-thrash]]) — the fix is now on main.
- **If you run localhost off `feature/l2-bodha`:** merge main into it (`git checkout feature/l2-bodha && git merge origin/main`) OR cherry-pick the ArmillaryGraph fix, then restart. (l2-bodha is 20-ahead/4-behind main — a clean `git merge origin/main` brings the fix in.)
RESTART the dev server after the branch update (the .tsx change needs a rebuild).

## STEP 3 — VERIFY the rings close
1. **Local cockpit** (localhost:3000, against prod data): open the Nirmāṇa tracker for 482012f1; hover the DAG
   layer nodes — **Brahmagyan = 22/22, Gaṇita = 17/17, Bodha = 10/10**, all outer rings CLOSED. (Service assets now count as built.)
2. **Prod cockpit** (after the deploy): verify the Cloud Run revision == the PR #303 merge SHA FIRST
   ([[feedback-verify-cloud-run-revision-before-chrome-probe]]), then confirm the same closed rings on the deployed URL.
3. Spot-check the service assets themselves render as `service_ok` (not error/grey) in the expanded layer rows.

## EXPECTED RESULT
All three layer rings closed: Brahmagyan 22/22, Gaṇita 17/17, Bodha 10/10. The ring now reflects DATA + SERVICE
completeness (the §N.4 "count_sql authoritative" principle + service assets are legitimately built-without-rows).
No code change needed beyond merging #303 — the fix is already written + tested.

## HARD STOPS
- If after the merge + restart the rings STILL show 20/22 / 16/17 → the running branch didn't get the fix (wrong
  branch checked out, or dev server not restarted) → re-confirm Step 2.
- prod ≠ merge SHA when probing the prod cockpit → wait for the deploy.
- A cockpit branch conflict (the other 2 cockpit branches) → resolve in favor of #303's aggregate() logic; do NOT revert the service_ok/build_state_stale counting.

**Begin: Step 1 — merge PR #303 to main. Go.**
