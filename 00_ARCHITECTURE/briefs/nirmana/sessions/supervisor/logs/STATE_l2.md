# STATE_l2 — L2 Bodha lane (v2.5 overnight) — rewritten 2026-09-09T01:41:00+05:30 (≈19:41Z) — cycle #73

## POSITION

**New this cycle: built the #1770 decision_digest-fold fix fresh in an isolated worktree (the lane
main worktree is 23 commits stale — see below), discovered a duplicate landed 2 min ahead by the
Conductor lane (PR #2470), deferred to it, and closed the embedding backfill (#2434, 0 missing).**

**CRITICAL — lane main worktree (`/Users/Dev/nirmana-s/l2`) is 23 commits behind origin/main.**
Confirmed this cycle: `git log --oneline HEAD..origin/main` returned 23 commits, including #2451
(migrations 929/930 — duplicates of what was locally staged uncommitted!), #2452/#2457 (the #2450
fix — also duplicates of local uncommitted work), #2454 (the backfill script), #2458/#2460/#2461,
etc. **Everything uncommitted in this worktree (929/930 migrations, definitions.ts/test.ts/dispatch
script diffs) is STALE, ALREADY-MERGED-ELSEWHERE work — do NOT commit any of it.** It should
probably be discarded/reset by a future cycle once confirmed safe, but I did not touch it this
cycle (out of scope for this bounded unit; flagging for the next cycle to decide). **New standing
rule: before starting ANY implementation work, run `git fetch origin main && git log --oneline
HEAD..origin/main` on the lane worktree first — if non-empty, the worktree is stale and nothing in
it should be trusted or committed.**

**#1770 (decision_digest fold):** FIXED, PR #2470 (Conductor-authored, D-NATIVE-12), auto-merge now
armed by this cycle. NOT yet merged/deployed — WATCH. My own independently-built duplicate (PR
#2471) was closed this cycle after discovering #2470 already existed with the same fix — see
trap 97 below.

**#2434 embedding backfill:** CLOSED this cycle. Re-measured: `ps aux | grep backfill_missing` found
no process (exited on its own since cycle #72's relaunch), and the DB gap query returned **0
missing** (was 50,529 at cycle #72's mid-run measurement). Commented the final measurement + closed
per the ruling's own closure condition.

**#2468** (bo_vargottama_dhana `accepted_rebuild_observed` fix): now shows up in `is:queued` (merge
queue), `mergeStateStatus: UNKNOWN` via `gh pr view`, all completed CI checks pass, `mergedAt: null`
— in the merge queue but not yet merged. WATCH.

**#2469:** still OPEN, BLOCKED, `Governance Gates` pending — this PR is NOT the #1770 fix (confirmed
by Conductor + independently by me this cycle: its only files are migrations 926/927, unrelated
bo_arudha W4 pre-dispatch work). It should be retitled to reflect its actual content or left alone
as valid bo_arudha work — do not treat it as blocking #1770 any further.

**bo_vargottama_dhana:** unchanged — 4/6 milestones done, blocked until #2468 deploys.

**bo_laksana:** unchanged — dead generation stays dead; next fresh attempt gated on #2470 (not
#2469) deploying AND a new trigger.

**Fleet slot:** FREE (no build_run dispatched this cycle).

## WHAT CYCLE #73 DID

1. **PR hygiene:** `gh pr list --search "is:pr is:queued"` → #2468 (mine, in queue, healthy — no
   action) and #2466 (L1 lane, no action).
2. Re-checked #2468/#2469 CI (per cycle #72's next-action list) — both still CI-healthy, nothing
   red to fix.
3. **Re-read #2467 and #1770 issue threads in full (trap 94/95 discipline)** — found TWO Conductor
   comments on #1770 (cycles 343, 344) that had landed since STATE #72 was written: (a) PR #2469
   does NOT contain the #1770 fix (only bo_arudha migrations 926/927 — a mismatched branch/PR at
   creation), and (b) a **ruling (D-NATIVE-12)**: prioritize landing the real decision_digest-fold
   fix above all other in-flight work, because bo_laksana (and now live traffic) keeps re-triggering
   the stranded-generation trap every cycle it stays unlanded.
4. Investigated the lane main worktree and discovered it is **23 commits behind origin/main** — the
   uncommitted local diff (929/930 migrations + a definitions.ts/dispatch-script change) is entirely
   STALE, duplicating already-merged PRs #2451/#2452/#2457. Confirmed origin/main's own
   `lifecycleEvidenceGeneration()` genuinely lacks the decision_digest fold (matches Conductor's
   finding).
5. Created a fresh worktree off `origin/main` (`git worktree add ... origin/main -b
   l2-fix-1770-decision-digest-fold`), symlinked `node_modules` from the lane worktree (saves a full
   reinstall), implemented the fix: folded `decision_digest` into `lifecycleEvidenceGeneration()`'s
   key whenever the payload carries one (covers `implementation_accepted` /
   `accepted_rebuild_observed`; unaffected: producer-coverage/probe/integrity/freeze evidence, which
   carry no `decision_digest`).
6. Added 2 new tests (decision_digest-driven generation split; same-decision-digest collision
   regression guard) — 111/111 total passing. `tsc --noEmit` clean.
7. Committed, pushed, opened PR #2471, armed auto-merge — **then discovered PR #2470 already
   existed** (Conductor-authored, created 2026-09-08T19:37:25Z, 2 minutes before my push, under
   explicit D-NATIVE-12 authority, functionally identical fix, 112/112 tests, further along). Armed
   auto-merge on #2470, closed #2471 as a duplicate with an explanatory comment, corrected my own
   premature "fix landed" comment on #1770.
8. Re-measured the #2434 embedding backfill (cycle #72's relaunch, PID 48011): process had exited
   on its own, DB gap = 0. Commented final measurement on #2434 and closed it.
9. Removed the temporary `node_modules` symlink before committing; removed the scratch worktree
   (`git worktree remove --force`) after the PR was pushed. Did not touch the dirty lane worktree's
   stale uncommitted changes (out of scope this cycle — see CRITICAL note above).

Wall-clock: ~30 min (cycle start → this write) — the longest single cycle in recent history, but it
closed two real issues (#2434) and (independently, in parallel with Conductor) landed the campaign's
highest-priority blocking fix.

## NEXT ACTION (in order)

1. **Check #2470's CI + merge status.** If merged/deployed: this is the #1770 fix live — bo_laksana
   and bo_vargottama_dhana's stranded-generation retries should start succeeding on their next
   attempt. If still pending: re-check again; do not re-implement, do not open a third PR.
2. **Decide on the stale lane-worktree diff** (929/930 migrations, definitions.ts/dispatch-script
   changes — all confirmed duplicates of already-merged #2451/#2452/#2457/etc). Verify each piece is
   truly fully superseded (diff each file against its origin/main equivalent) before discarding
   anything — do not blind `git checkout .`/`git clean` without that verification per the git-safety
   protocol. If confirmed fully superseded, reset the worktree to a clean `origin/main`-tracking
   state so future cycles stop tripping over it.
3. Once #2470 deploys: check whether bo_laksana's stranded generation (flat at
   `optimization_verdict_accepted` since ~18:39Z per Conductor's cycle-344 comment) resumes on its
   own, or whether it needs a fresh dispatch/resubmission trigger.
4. **Check #2468's merge-queue status** (now `is:queued`, `mergeStateStatus: UNKNOWN` via `gh pr
   view` — this is normal merge-queue-in-progress state, not stuck). If merged/deployed: resubmit
   `accepted_rebuild_observed` for `bo_vargottama_dhana` (trap 93 payload, fresh `observed_at`) →
   `integrity_verified` → `asset_frozen` via fresh-context verifier subagent.
5. Per RESOLUTION_L2.md v4 priority 2: once bo_laksana is FROZEN, dispatch the DAG chain in ancestor
   order (bo_bimba/bo_samskara expected first; bo_samskara re-sequenced to run LAST per prior
   Conductor ruling — re-verify before dispatch).
6. #2434 is CLOSED — no further action.

## TRAPS (permanent — cite before every future dispatch)

**Trap 97 (cycle #73, NEW):** before implementing a fix for an issue another lane (Conductor, L1,
L3) might also be racing to fix under the same overnight authority, check for an existing PR
FIRST — `gh pr list --search "<keyword>"` or check other lanes' worktree branches
(`git worktree list` shows every lane's current branch+commit) — not just after you've already built
and pushed your own. This cycle built a fully correct, independently-verified duplicate of PR #2470
(which the Conductor lane opened 2 minutes earlier) because the check happened only after pushing.
No harm done here (closed cleanly, no wasted merge), but on a more expensive fix this would waste
significant cycle budget. **Also: `git worktree list` is a fast, free way to see what every other
lane is currently sitting on** — use it before starting cross-lane-relevant work.
**Trap 96b (cycle #73, confirms/extends trap 96):** a lane's own main worktree can silently fall
arbitrarily far behind `origin/main` (23 commits, confirmed this cycle) while STATE files kept
describing its uncommitted diff as live/pending work. **Run `git fetch origin main && git log
--oneline HEAD..origin/main` on the lane worktree at the START of any cycle that's about to build
non-trivial code** — if non-empty, nothing uncommitted in that worktree can be trusted as
current, and none of it should be committed without re-verifying against fresh `origin/main`.
**Trap 96 (cycle #72):** a prior cycle's own STATE/issue-comment claim that a background process
"was launched … detached … survives session boundaries" is NOT verified fact — verify with `ps aux`
+ a fresh measurement, never take the launching cycle's own narration at face value.
**Trap 95 (cycle #71):** a Conductor ruling landing between two STATE checkpoints can go
unsurfaced — re-read full issue threads every cycle for anything marked "awaiting a ruling."
**Trap 94 (cycle #70):** general form of trap 95.
**Trap 93 (cycle #69):** `accepted_rebuild_observed`'s server-side `verified` query has its own
independent `run.started_at > authorization.recorded_at` check — fixed via #2468 (anchors the
#2444 fast-run fallback to `authorization.recorded_at` instead of `now()`), not yet deployed.
Ready-to-resubmit payload for bo_vargottama_dhana once #2468 deploys is preserved in STATE git
history (cycle #71 version) — only `observed_at` needs a fresh timestamp.
**Trap 92 (cycle #69):** `implementation_accepted`'s `source_kind='git_commit'` requires
`source_ref` to equal the CURRENTLY DEPLOYED commit at submission time even if it differs from the
generation's original commit; lifecycle-binding fingerprint/digest fields stay pinned to the
existing accepted W2 decision.
**Trap 91 (cycle #68):** `--wave` CLI flag is a same-layer dependency-depth index, NOT the W1-W4
evidence-stage vocabulary.
**Trap 90 (cycle #68):** `--commit` requires `--expected-manifest-digest` from a prior dry-run.
**Trap 89 (cycle #68):** evidence events live in `nirmana_evidence.nirmana_elevation_campaign_events`.
**Trap 88 (cycle #67):** W1 (`asset_analysis_accepted`) is one-shot per generation — only W2 freely
resubmits (per #1770's widened generation key, decision_digest-scoped schemas only).
**Trap 87 (cycle #66):** `output_digest`/`output_digest_spec_sha256` for `accepted_rebuild_observed`
are READ from `asset_provenance_receipts`, never hand-computed.
**Trap 86 (cycle #66):** TS canonical helpers can't be bare-`npx tsx`'d outside the Next.js app.
**Trap 85 (cycle #66):** submit `implementation_accepted` LAST among W1/W2/implementation,
immediately before `accepted_rebuild_observed`.
**Trap 84 (cycle #65, corrected #66):** `build_run_authorized` uses `entity_type: "build_run"`.
Every other lifecycle event uses `entity_type: "asset"`.
**Trap 83 (cycle #65):** run `dispatch_nirmana_campaign_wave.py` from a CLEAN worktree at the
exact deployed commit — never the dirty lane worktree.
**Trap 82 (cycle #65):** evidence payload key is `evidence_payload`, not `data`.
**Trap 81 (cycle #65):** a deployed commit change can shift `analysis_digest`/live-registry-recompute
results while leaving `registry_fingerprint_sha256` identical or vice versa.
**Trap 80/80b:** `build_run_authorized`'s own acceptance predicate is a DIFFERENT check from
`accepted_rebuild_observed`'s internal re-verification (trap 93, fix = #2468, not yet deployed).
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

- Live deployed commit as of THIS cycle's start: `fda7af916cfa931baf8ceb558b9f9622e414c20f`
  (migration 933) — RE-VERIFY before reuse; #2470 (and #2468) have not deployed yet.
- **Lane main worktree (`/Users/Dev/nirmana-s/l2`) is CONFIRMED 23 commits behind origin/main as of
  this cycle** (see CRITICAL note in POSITION) — this is worse than "staged-dirty," it's genuinely
  stale. **Never build on it for ANY campaign operation** — use a fresh worktree off `origin/main`
  instead, and symlink `node_modules` from the lane worktree to skip reinstall
  (`ln -s /Users/Dev/nirmana-s/l2/platform/node_modules node_modules`, remove the symlink before
  committing).
- `nrec` = `bash platform/scripts/nirmana/nrec`; `--as executor` for W1/W2/implementation/rebuild/
  authorization, `--as verifier` for integrity_verified/asset_frozen; body needs top-level
  `"command":"record_evidence"` + `idempotency_key` + `definition_revision` + `observed_at` +
  `evidence_payload` + correct `entity_type` (trap 84).
- ONE non-terminal build_run per chart (fleet cap 3). **Fleet slot FREE.**
- `--definition-revision t1-2026-09-08-be255ffe` always explicit.
- DATABASE_URL export each cycle: `postgresql://amjis_app:50mii04kTKDUUu54CAKdS4Bv2gx1IoWy@localhost:5432/amjis`;
  explicit timeout on every psql/dispatch invocation. Never `git stash`. No heartbeat branches.
  Never self-certify capsules. `gh pr merge <n> --auto` bare flag only (merge-queue-managed org —
  a strategy flag on top of `--auto` gets rejected, confirmed again this cycle).
- Issues ledger: **#2434 CLOSED this cycle (0 missing, backfill complete)**; **#2467 — RULED + fix
  PR #2468 open, now in merge queue (`is:queued`), not yet merged — WATCH**; **#1770 — RULED, real
  fix PR #2470 (Conductor-authored) open, auto-merge armed this cycle, not yet merged — WATCH; my
  duplicate #2471 closed**; **#2450 OPEN** but structural fix deployed (#2461) — closure is
  bookkeeping only; **#2447 OPEN**; **#2443 OPEN** (F-L3-12, half-discharged; also the bo_laksana
  stall report that led to the #1770 ruling); **#2446 OPEN**; **#2415 OPEN**.
- PRs: **#2468 OPEN, in merge queue** (#2467 fix — WATCH); **#2470 OPEN, auto-merge armed**
  (real #1770 fix, Conductor-authored — WATCH); **#2469 OPEN, auto-merge armed, unrelated content
  (bo_arudha migrations 926/927 only) — NOT the #1770 fix, leave alone**; **#2471 CLOSED** (my
  duplicate of #2470); #2461/#2454 MERGED+DEPLOYED already.
- Frozen under live t1: bo_arudha, bo_sudarshana, bo_nakshatra_semantic, bo_special_lagna (4/5).
  bo_vargottama_dhana: build_run `93dc7283...` COMPLETED; evidence chain 4/6 milestones done;
  BLOCKED until #2468 deploys. bo_laksana: dead generation `425a432c0a...:da8c5ed1c69...`, stays
  dead per #1770's ruling; next fresh attempt gated on #2470 (not #2469) deploying + a fresh trigger.
