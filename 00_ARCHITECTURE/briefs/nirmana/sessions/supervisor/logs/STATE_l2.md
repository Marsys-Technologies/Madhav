# STATE_l2 — L2 Bodha lane (v2.5 overnight) — rewritten 2026-09-09T01:30+05:30 — cycle #76

## POSITION

**New this cycle: resolved the stale lane-worktree diff that cycles #73/#74/#75 all flagged and
deferred.** Verified every uncommitted item against `origin/main` byte-for-byte before touching
anything (no `git clean -fd`/`reset --hard` — surgical per-file checks):

- Staged `migrations/929_...output_digest_spec.sql` + `930_...natural_key_partition.sql`: `git
  diff origin/main -- <file>` was EMPTY — byte-identical to PR #2451 (already MERGED, "L2:
  migrations 929/930 — bo_laksana output_digest_spec + natural_key_partition (W4 post-dispatch)").
  Pure stale duplicate. Unstaged + `rm`'d.
- Modified `dispatch_nirmana_campaign_wave.py`, `definitions.ts`, `definitions.test.ts`: diffed
  against `origin/main` and found the working-tree version was OLDER — missing the #2450 v2
  digest-schema ruling, the D-NATIVE-13 mid-campaign-supersession function
  (`supersedeNirmanaElevationDefinitionMidCampaign`), `assertLayerFreezeLifecycleComplete`, and
  more, all now legitimately shipped on `main`. Zero net-new content in the working copy beyond
  what main already has — a pure revert, never a WIP addition. `git checkout --` on all three.
- `platform/.tmp_verifier_scratch/` (16 files: `definitions.clean.ts`, `campaign-control-writer.ts`,
  evidence JSONs, `issue_bo_laksana_integrity.md`, etc.): manual verifier scratch from the
  bo_laksana integrity investigation (S10208/#2455 lineage) whose findings already shipped via
  merged PRs #2458/#2460/#2461/#2463. Purpose already served. `rm -rf`'d.
- `platform/python-sidecar/backfill_missing_signal_embeddings.py` (untracked): `git show
  origin/main:<path> | diff -` → byte-identical to the file that's ALREADY on `origin/main` (added
  by a commit this branch's HEAD predates). Untracked only because this branch's HEAD is stale, not
  because it was new work. `rm`'d.

`git status` is now **clean** (`nothing to commit, working tree clean`). Remaining `git diff
origin/main --stat` is exactly "this branch is 25 commits behind" (expected — branch
`l2-bo-arudha-predispatch-contract-926-927` already fully merged as PR #2469; no rebase needed,
just don't build new work on this HEAD — use a fresh `origin/main` worktree per the standing
constraint below).

**#1770 (trap 99 tie-break, unchanged from cycle #75):** #2470 re-verified live: `state: OPEN`,
`mergeable: MERGEABLE`, `mergeStateStatus: BLOCKED` — BLOCKED is CI-pending, not failing:
`gh pr checks 2470` shows exactly 2 non-terminal jobs ("Build Check (PR only)" IN_PROGRESS,
"Governance Gates (drift/schema/edge/native-literal/py-sidecar)" IN_PROGRESS), everything else
SUCCESS/pass. No new failure, no action available — do not re-close/reopen anything (trap 99's
tie-break holds: #2470 is the sole permanent vehicle). #2471 re-confirmed `state: CLOSED,
mergedAt: null` — stays closed, do not touch.

**Deploy status (re-checked, changed slightly since cycle #75):** live deployed image is STILL
`fda7af916cfa931baf8ceb558b9f9622e414c20f` (pre-#2468, pre-#2469). Deploy run `34270580682`
(headSha `b4b9a3c3a`, pre-#2468) still `in_progress`. The `90327f52c` (includes #2468+#2469) deploy
run that was `pending` last cycle (`34271205286`) came back `conclusion: cancelled` — GitHub Actions
cancelled it, almost certainly superseded by the *newer* commit landing while it queued (normal
serialize-forward behavior, not a failure) — a fresh run `34271271457` for the same `90327f52c`
headSha is now queued (`status: pending`, no conclusion yet). **Neither #2468 nor #2469 nor #2470
(once merged) is live yet.** Do not resubmit `accepted_rebuild_observed` for bo_vargottama_dhana,
and do not expect bo_laksana's stranded generation to resume, until a deploy run for the relevant
headSha shows `conclusion: success` AND `gcloud run services describe amjis-web --region=asia-south1
--format="value(spec.template.spec.containers[0].image)"` shows a SHA descending from the needed
merge commit.

**Fleet slot:** FREE (no build_run dispatched this cycle — nothing newly unblocked; bounded unit
was the worktree-hygiene cleanup, priority stack items 1-2 are still gated on the deploy above).

**bo_laksana:** unchanged — dead generation stays dead; next fresh attempt gated on #2470 merging
AND deploying AND a fresh trigger.

**bo_vargottama_dhana:** unchanged — 4/6 milestones done; #2468 merged but not yet deployed —
resubmission still blocked on deploy, not on the PR.

**Frozen under live t1 (unchanged, re-confirm before next dispatch):** bo_arudha, bo_sudarshana,
bo_nakshatra_semantic, bo_special_lagna (4/5 — bo_laksana is the 5th, still not frozen).

## WHAT CYCLE #76 DID

1. Read RESOLUTION_L2.md (unchanged v4) and STATE #75 in full.
2. PR hygiene per STEP 1: `gh pr list --search "is:pr is:queued"` → empty (nothing of mine
   queued). Directly re-verified #2470/#2471 live state via `gh pr view --json
   state,mergedAt,mergeStateStatus,mergeable,autoMergeRequest` (trap 98 discipline). No change
   needed — #2470 still OPEN+BLOCKED-on-pending-CI (confirmed via `gh pr checks 2470`, 2 jobs
   IN_PROGRESS, rest pass), #2471 still CLOSED permanently. No action taken (correctly — trap 99's
   fix was to STOP reacting).
3. Re-checked deploy status (`gh run list --workflow="Deploy to Cloud Run" --branch main` +
   `gcloud run services describe amjis-web`) — live image unchanged from cycle #75; noted the
   `90327f52c` deploy run's cancel-and-requeue (see POSITION above), not a failure.
4. Since priority-stack items 1/2 (bo_laksana resume, chain dispatch) are still hard-gated on the
   deploy above with nothing new to check, and item 5's "stale lane-worktree diff... genuinely
   needs a dedicated cycle" had been carried open since cycle #73, took that as this cycle's
   bounded unit: fetched `origin/main`, diffed every uncommitted file (staged + modified +
   untracked) against it individually, confirmed each was either a byte-identical duplicate of
   already-merged content or a pure revert with zero net-new lines, then discarded them file-by-file
   (`git restore --staged`, `rm`, `git checkout --`, `rm -rf` — never a blanket `git clean`/`reset
   --hard`, which would also have wiped `node_modules`/pycache per the `git clean -ndx` dry-run).
5. Verified `git status` clean and `git diff origin/main --stat` shows only the expected
   behind-count, nothing else.
6. Did not dispatch any build_run — nothing newly unblocked this cycle.

Wall-clock: ~16 min.

## NEXT ACTION (in order)

1. **Check #2470's merge state fresh** (`gh pr view 2470 --json state,mergedAt,mergeStateStatus`).
   If merged: watch the next "Deploy to Cloud Run" run for its headSha (must be a descendant of
   #2470's merge commit) to `conclusion: success`, THEN re-check `gcloud run services describe
   amjis-web` for the deployed image SHA before acting on anything gated on the #1770 fix. **Do
   not reopen #2471 regardless of what happens to #2470** (trap 99).
2. **Check whether bo_laksana's stranded generation auto-resumes** once #2470 deploys — if not,
   needs a fresh dispatch/resubmission trigger. Priority-1 per RESOLUTION_L2.md v4. **Use a fresh
   `origin/main` worktree for this, NOT `/Users/Dev/nirmana-s/l2`** (this worktree's branch is
   fully merged/stale at 25+ commits behind; symlink `node_modules` from here to skip reinstall,
   remove the symlink before committing anything new).
3. **Once #2468 is confirmed in the LIVE deployed image** (not just merged): resubmit
   `accepted_rebuild_observed` for `bo_vargottama_dhana` (trap 93 payload, fresh `observed_at`) →
   `integrity_verified` → `asset_frozen` via fresh-context verifier subagent.
4. Per RESOLUTION_L2.md v4 priority 2: once bo_laksana is FROZEN, dispatch the DAG chain in
   ancestor order (bo_bimba/bo_samskara expected first; bo_samskara re-sequenced to run LAST per
   prior Conductor ruling — re-verify before dispatch).
5. #2450: structural fix (#2461) already deployed; issue itself still OPEN as bookkeeping only —
   re-check for an explicit Conductor closure ruling next cycle.
6. #2434 (embedding backfill) is CLOSED — no further action. (Confirmed this cycle: the backfill
   script itself is already on `origin/main` — nothing outstanding here.)

## TRAPS (permanent — cite before every future dispatch)

**Trap 100 (cycle #76, NEW):** when a lane worktree accumulates uncommitted diffs across several
cycles, don't defer the cleanup indefinitely on "needs a dedicated cycle" — diff EACH item
individually against `origin/main` (`git diff origin/main -- <path>` for tracked/modified files,
`git show origin/main:<path> | diff - <path>` for untracked files that might already exist
upstream). A modified file whose diff vs `origin/main` shows the working copy is MISSING content
(all changed lines on the "removed" side) is a stale revert, not WIP — safe to `git checkout --`
once confirmed empty of net-new lines. Never blanket `git clean -fd`/`reset --hard` to do this —
`git clean -ndx` dry-run first; it will also flag `node_modules`/caches that must NOT be swept.
**Trap 99 (cycle #75):** trap 98's race can also manifest as a double-open (both duplicate PRs
simultaneously OPEN with auto-merge armed). Fix: pick a fixed, asymmetric tie-break once and state
it permanently on the issue thread — do not keep reactively closing/reopening.
**Trap 98 (cycle #74):** a "closed X as superseded by Y" comment does NOT guarantee Y is actually
open at the time you read it — always check both PRs' live `state`/`mergedAt` directly.
**Trap 97 (cycle #73):** check for an existing PR FIRST before building your own fix for an issue
another lane might also be racing to fix.
**Trap 96b (cycle #73):** run `git fetch origin main && git log --oneline HEAD..origin/main` on
the lane worktree at the START of any cycle that's about to build non-trivial code.
**Trap 96 (cycle #72):** a prior cycle's claim that a background process "survives session
boundaries" is NOT verified fact — verify with `ps aux` + a fresh measurement.
**Trap 95/94 (cycle #71/70):** re-read full issue threads every cycle for anything marked
"awaiting a ruling" — a ruling landing between two STATE checkpoints can go unsurfaced.
**Trap 93 (cycle #69):** `accepted_rebuild_observed`'s server-side check has its own independent
`run.started_at > authorization.recorded_at` check — fix is #2468 (merged, NOT yet deployed).
**Trap 92 (cycle #69):** `implementation_accepted`'s `source_kind='git_commit'` requires
`source_ref` to equal the CURRENTLY DEPLOYED commit at submission time.
**Trap 91/90 (cycle #68):** `--wave` is a dependency-depth index, not W1-W4 vocabulary;
`--commit` requires `--expected-manifest-digest` from a prior dry-run.
**Trap 89 (cycle #68):** evidence events live in `nirmana_evidence.nirmana_elevation_campaign_events`
(NOT `nirmana_evidence.build_runs`).
**Trap 88 (cycle #67):** W1 is one-shot per generation — only W2 freely resubmits.
**Trap 87 (cycle #66):** `output_digest`/`output_digest_spec_sha256` are READ, never hand-computed.
**Trap 86 (cycle #66):** TS canonical helpers can't be bare-`npx tsx`'d outside the Next.js app.
**Trap 85 (cycle #66):** submit `implementation_accepted` LAST, immediately before
`accepted_rebuild_observed`.
**Trap 84 (cycle #65/66):** `build_run_authorized` uses `entity_type: "build_run"`; every other
lifecycle event uses `entity_type: "asset"`.
**Trap 83 (cycle #65):** run `dispatch_nirmana_campaign_wave.py` from a CLEAN worktree at the
exact deployed commit — never the dirty lane worktree.
**Trap 82 (cycle #65):** evidence payload key is `evidence_payload`, not `data`.
**Trap 81 (cycle #65):** a deployed commit change can shift `analysis_digest`/live-registry-recompute
results while leaving `registry_fingerprint_sha256` identical or vice versa.
**Trap 80/80b:** `build_run_authorized`'s own acceptance predicate is a DIFFERENT check from
`accepted_rebuild_observed`'s internal re-verification (trap 93).
**Trap 78:** identify a deploy's actual shipped commit via `gcloud run services describe
amjis-web --region=asia-south1 --format="value(spec.template.spec.containers[0].image)"`.
**Trap 77:** canonical digest scheme is `nirmana-asset-analysis-receipt/v2`.
**Trap 76:** bo_laksana pre-#2458 signal_ids are NOT derivable from stored rows.
**Trap 75:** own-contract-changed = FULL W1/W2 re-run as executor + redispatch, refined by trap 88.
**Trap 74:** grep open PRs for a migration number prefix before arming any migration PR.
**Trap 73:** bo_vargottama_dhana WP-6 blast radius: ~337k kala_activation, 100,195 embeddings,
20,497 kala_convergence, L4 rows, 5 no-FK orphan sets.
**Trap 72:** before integrity_verified check `asset_registry.integrity_check_sql IS NOT NULL`.
**Trap 71:** verdict `'correct'` IS change-required → implementation_accepted needed.
**Trap 70:** `--reviewed-deployment-sha` = the accepted pair's OWN recorded source_ref.
**Trap 69:** build_run_authorized MUST use `source_kind='campaign_authorization'`.
**Trap 68:** authorization 10-minute window from run created_at, evaluated at submission.
**Trap 67:** `--snapshot-ref` changes the manifest digest — dry-run with exact commit flags.
See git history of this file for traps 1–66.

## STANDING CONSTRAINTS (carried forward, verify each cycle)

- Live deployed commit as of cycle #76's check: `fda7af916cfa931baf8ceb558b9f9622e414c20f`
  (migration 933) — RE-VERIFY before reuse; #2468/#2469 merged but NOT yet deployed; #2470 not
  yet merged. Deploy `34270580682` (headSha `b4b9a3c3a`, in_progress) and a fresh `90327f52c`
  requeue `34271271457` (pending, supersedes the cancelled `34271205286`) are serializing forward.
- **Lane main worktree (`/Users/Dev/nirmana-s/l2`) is now CLEAN as of cycle #76** (was 23-25
  commits behind + stale uncommitted diffs at cycles #73-75; diffs verified redundant and
  discarded this cycle — see TRAP 100). It is still ~25 commits behind `origin/main` and its own
  branch (`l2-bo-arudha-predispatch-contract-926-927`) is already fully merged (as #2469) — **do
  not build new campaign work on this worktree's HEAD; use a fresh `origin/main` worktree**,
  symlink `node_modules` from this worktree to skip reinstall, remove the symlink before
  committing.
- `nrec` = `bash platform/scripts/nirmana/nrec`; `--as executor` for W1/W2/implementation/rebuild/
  authorization, `--as verifier` for integrity_verified/asset_frozen; body needs top-level
  `"command":"record_evidence"` + `idempotency_key` + `definition_revision` + `observed_at` +
  `evidence_payload` + correct `entity_type` (trap 84).
- ONE non-terminal build_run per chart (fleet cap 3). **Fleet slot FREE.**
- `--definition-revision t1-2026-09-08-be255ffe` always explicit.
- DATABASE_URL export each cycle: `postgresql://amjis_app:50mii04kTKDUUu54CAKdS4Bv2gx1IoWy@localhost:5432/amjis`;
  explicit timeout on every psql/dispatch invocation. Never `git stash`. No heartbeat branches.
  Never self-certify capsules. `gh pr merge <n> --auto` bare flag only (merge-queue-managed org —
  a strategy flag on top of `--auto` gets rejected).
- Issues ledger: **#2434 CLOSED**; **#2467 — RULED, fix #2468 MERGED, NOT yet deployed — WATCH
  deploy**; **#1770 — RULED, sole live fix #2470 (permanent tie-break), NOT yet merged — WATCH, do
  not reopen #2471 or create a third PR**; **#2450 OPEN** but structural fix deployed (#2461) —
  closure is bookkeeping only; **#2447 OPEN**; **#2443 OPEN** (F-L3-12, half-discharged; also the
  bo_laksana stall report that led to the #1770 ruling); **#2446 OPEN**; **#2415 OPEN**.
- PRs: **#2470 OPEN, mergeable, auto-merge armed, BLOCKED on 2 pending CI jobs (not failing) —
  WATCH**; **#2471 CLOSED PERMANENTLY** (do not reopen); **#2469 MERGED** (bo_arudha migrations
  926/927, now on `origin/main`); #2468/#2461/#2454/#2457/#2451 MERGED+on `origin/main` (deploy
  status per above).
- Frozen under live t1: bo_arudha, bo_sudarshana, bo_nakshatra_semantic, bo_special_lagna (4/5).
  bo_vargottama_dhana: build_run `93dc7283...` COMPLETED; evidence chain 4/6 milestones done;
  BLOCKED until #2468's fix is in the LIVE deployed image. bo_laksana: dead generation
  `425a432c0a...:da8c5ed1c69...`, stays dead per #1770's ruling; next fresh attempt gated on #2470
  merging + deploying + a fresh trigger.
