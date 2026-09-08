# STATE_l2 — L2 Bodha lane (v2.5 overnight) — rewritten 2026-09-09T01:35+05:30 — cycle #77

## POSITION

**Nothing newly unblocked this cycle — priority stack items 1-3 remain hard-gated on deploy
catch-up. This cycle's value is a fresh, from-scratch re-verification (not trusting cycle #76's
cached numbers) that corrected two stale facts and confirmed the campaign is exactly where #76
left it, just one commit further along the deploy queue.**

**PR hygiene (STEP 1):** `gh pr list --search "is:pr is:queued"` → `#2470` (sole result, mine).
Re-verified directly: `mergeStateStatus: CLEAN`, `mergeable: MERGEABLE`, all CI checks pass
(`gh pr checks 2470` — every job SUCCESS/pass, none failing). Attempted `gh pr merge 2470 --auto`
defensively → response was `"already queued to merge"`, confirming it's genuinely in the
merge-queue pipeline, not stalled. **Correction to cycle #76's read:** #76 described #2470 as
"BLOCKED on 2 pending CI jobs" from a snapshot mid-run; those jobs have since finished (all green)
and the PR is now merge-queue-queued, which per the brief's own rule ("is:queued is the only
truth") means **healthy, no action needed** — do not intervene further, just watch for it to land.
#2471 re-confirmed `state: CLOSED, mergedAt: null` — unchanged, do not touch (trap 99 holds).

**Deploy status (re-derived from first principles, not carried forward):** live image is now
`296923c052b8cb475f5175c4265dd013188ff97d` (commit `296923c05`, **#2464** "L3: ka_yojaka —
generalize always_on_reason disclosure", *not* a bo_* commit) — confirmed via
`gcloud run revisions describe amjis-web-02185-bb7 --format="value(spec.containers[0].image)"`
resolved to a digest, then matched against `gcloud artifacts docker images list --include-tags`
which shows that digest tagged both `296923c052b8...` and `latest`, pushed most recently of any
tag in the registry. Revision `amjis-web-02185-bb7` was created `2026-09-08T19:54:11Z`, which lines
up with deploy run `34270580682` (headSha `b4b9a3c3a`, **#2466**, success, `updatedAt
19:54:44Z`) — **so the b4b9a3c3a/#2466 deploy run redeployed the amjis-web image, but that
run's own commit (a migration-only rename, #934) didn't trigger a fresh web build; Cloud Run just
got redeployed with whatever image was already tagged `latest` from the prior web-touching commit,
which was #2464.** This is a NEW trap (below, #101) — **image tag ≠ headSha of the triggering
deploy run** when the triggering commit doesn't touch web-buildable paths.

**Git commit order correction (do not repeat #76's near-miss):** `git log origin/main --oneline`
lists NEWEST first. Chronological (oldest→newest) order of the recent chain is: `fda7af916` (#2463)
→ `296923c05` (#2464, **currently live**) → `b4b9a3c3a` (#2466) → `ea78a6508` (#2468, the
accepted_rebuild_observed temporal fix) → `90327f52c` (#2469, bo_arudha migrations 926/927) →
(pending) `#2470` (trap-99 tie-break fix). **So the live deploy has advanced ONE commit since
cycle #76's check (from #2463 to #2464) but is still 3 commits short of #2468.** Neither #2468 nor
#2469 nor #2470 is live. Do not resubmit `accepted_rebuild_observed` for bo_vargottama_dhana, and
do not expect bo_laksana's stranded generation to resume, until a revision built from a commit
at-or-after `ea78a6508` (#2468) is confirmed live via this same digest-matching method (image tag
alone is not proof — confirm via the artifact-registry push-order + revision-creation-time
cross-check, per trap 101).

**#2450 narrowed:** independently confirmed `#2461` ("L2: nirmana-asset-analysis-receipt/v2 —
per-asset digest identity scoping", the structural fix for #2450) is `4bfef737e`, which sits
**below** (older than) `fda7af916`/#2463 in the chain above — i.e. #2461's fix **is already live**,
has been since before #76's check. The remaining blocker for bo_vargottama_dhana resubmission is
narrower than #76 stated: it is `#2468` alone (the accepted_rebuild_observed temporal window fix,
trap 93), not #2450/#2461. #2450 the issue stays OPEN as bookkeeping only — its fix has been live
for several cycles; no new Conductor ruling closing it was found this cycle (checked
`gh issue view 2450` comments — last comment is still the cycle-320 implementation note).

**Fleet slot: FREE.** Queried `public.build_runs` directly — zero rows with `state NOT IN
('completed','failed','stopped')` across the whole table (not just bo_* — confirmed empty result
set). Confirms trap 89's schema location (`public.build_runs`, not `nirmana_evidence.build_runs`
— that schema/table combination doesn't exist; corrected from a wrong guess mid-cycle, costless
since caught before any dispatch attempt).

**No new Conductor rulings this cycle** on any gating issue — checked `#2450`, `#2467` (CLOSED,
unchanged), `#1770` (OPEN, unchanged, last comment still cycle #75's tie-break note), `#2447`,
`#2443` (stale bo_laksana-stall comment predates the #1770 ruling that already accepted the dead
generation — no action, not reopening a settled question), `#2446`, `#2415` — all unchanged from
#76's read.

**bo_nakshatra_semantic:** confirmed already FROZEN (issue #2406 CLOSED, resolved by the
D-NATIVE-13 t1 flip on 2026-09-08 09:39 UTC — well before this lane's tracking window). Correctly
listed under "Frozen under live t1" — no outstanding action, RESOLUTION_L2 v4 priority-4 item is
fully discharged, not merely parked.

**bo_laksana:** unchanged — dead generation `425a432c0a...:da8c5ed1c69...` stays dead per #1770's
ruling; most recent build_run (`a7c45a8b...`, completed 2026-09-08T18:22:49Z) produced no
subsequent `integrity_verified`/`asset_frozen` evidence. Next fresh attempt gated on #2470 merging
AND deploying (commit at/after `ea78a6508`) AND a fresh dispatch trigger from a clean
`origin/main` worktree (not this stale one).

**bo_vargottama_dhana:** unchanged — 4/6 milestones done (`build_run 93dc7283...` completed
2026-09-08T19:02:49Z); resubmission blocked on #2468 reaching the live image (not #2450/#2461,
which are already live — see correction above).

## WHAT CYCLE #77 DID

1. Read RESOLUTION_L2.md (unchanged v4) and STATE #76 in full — treated its cached facts as
   claims to re-verify, not ground truth, per the brief's own "trust it" applying to the brief, not
   to a prior cycle's numbers.
2. PR hygiene: `gh pr list --search "is:pr is:queued"` (one result, #2470) → verified its
   `mergeStateStatus`/`mergeable`/checks live, attempted a defensive `gh pr merge --auto` which
   confirmed "already queued to merge" rather than doing anything — no dirty/red/unqueued PR of
   mine existed, so no fix was needed, but the attempt itself surfaced that #2470's true state
   (merge-queued, healthy) differs from #76's stale "BLOCKED on CI" snapshot.
3. Re-derived deploy status from scratch: `gh run list` for recent deploy runs, then resolved the
   *actual* served image via `gcloud run revisions describe <latest-ready-revision>
   --format="value(spec.containers[0].image)"` (a digest) and cross-referenced it against
   `gcloud artifacts docker images list --include-tags` to find which git-sha tag shares that
   digest, then matched push/revision timestamps to attribute it to the correct deploy run. This
   caught trap 101 (image tag can lag the triggering run's headSha when that commit doesn't touch
   web-buildable paths) and corrected a git-log direction slip before it became a real error
   (double-checked oldest→newest ordering explicitly rather than eyeballing `--oneline` output).
4. Queried `public.build_runs` directly for non-terminal rows (fleet-slot check) and for
   bo_laksana/bo_vargottama_dhana's own row history — confirmed both match #76's account exactly,
   fleet slot free, no silent progress.
5. Re-read all 7 gating issues' live state/last-comment directly (not from memory/STATE) — no new
   Conductor ruling found on any of them.
6. Independently confirmed #2461 (the #2450 structural fix) is already live — narrows the
   remaining bo_vargottama_dhana blocker to #2468 alone; recorded this as a correction, not a new
   finding requiring action (RESOLUTION_L2 v4's "wait for the ruling" instruction was already
   satisfied by #2461 landing+deploying; the remaining wait is purely for #2468, already tracked).
7. Did not dispatch any build_run — nothing newly unblocked. Did not resubmit any evidence — both
   gating deploys (#2468 for bo_vargottama_dhana, #2470 for bo_laksana) still not live.

Wall-clock: ~14 min.

## NEXT ACTION (in order)

1. **Check #2470's merge-queue outcome fresh** (`gh pr view 2470 --json state,mergedAt`). If
   merged: watch for the next "Deploy to Cloud Run" run whose headSha descends from it, confirm
   `conclusion: success`, THEN re-derive the live image via the digest-matching method in trap 101
   (do not trust the raw `spec.template.spec.containers[0].image` tag alone if there's any doubt —
   cross-check against `gcloud artifacts docker images list --include-tags` push order). **Do not
   reopen #2471 regardless** (trap 99).
2. **The moment a commit at-or-after `ea78a6508` (#2468) is confirmed live** (by the method
   above): resubmit `accepted_rebuild_observed` for `bo_vargottama_dhana` (trap 93 payload, fresh
   `observed_at`) → `integrity_verified` → `asset_frozen` via fresh-context verifier subagent. This
   no longer needs to wait on #2450/#2461 — that fix has been live for several cycles.
3. **Once #2470 (bo_laksana's trap-99 fix) is confirmed live**, trigger a fresh bo_laksana
   dispatch from a **clean `origin/main` worktree** (not `/Users/Dev/nirmana-s/l2`, which remains
   ~25+ commits behind and fully merged as #2469 — symlink `node_modules` from here to skip
   reinstall, remove the symlink before committing anything new) → run the full evidence chain →
   `integrity_verified` → `asset_frozen` via fresh-context verifier subagent. BO_LAKSANA FROZEN is
   still the campaign's hinge (RESOLUTION_L2 v4 priority 1).
4. **Once bo_laksana is FROZEN:** dispatch the DAG chain in ancestor order (bo_bimba/bo_samskara
   expected first per prior notes; bo_samskara re-sequenced to run LAST per a prior Conductor
   ruling — re-verify that ruling is still current before dispatch, don't assume it's unchanged).
5. #2450: bookkeeping-only OPEN state, fix live — re-check next cycle for an explicit Conductor
   closure comment, otherwise leave as is; do not chase this further, it is not blocking anything.
6. #2434: CLOSED, no further action (unchanged, re-confirmed no regression).

## TRAPS (permanent — cite before every future dispatch)

**Trap 101 (cycle #77, NEW):** a deploy run's headSha is NOT proof of what image actually got
redeployed. If the triggering commit doesn't touch web-buildable paths (e.g. a migration-only or
non-web change), the pipeline redeploys Cloud Run with whatever image is already tagged `latest`
from the last commit that DID trigger a real web build — the newly-tagged `latest`/`<sha>` pair in
`gcloud artifacts docker images list --include-tags` can be a git-sha OLDER than the deploy run
that pushed it. To find the true live commit: resolve the serving revision's image to a digest
(`gcloud run revisions describe <revision> --format="value(spec.containers[0].image)"`), match that
digest's tag in the artifact registry, and only trust the git-sha in that tag — never assume the
most recent deploy run's headSha is what's actually serving.
**Trap 100 (cycle #76):** a lane worktree accumulating uncommitted diffs across cycles — diff EACH
item individually against `origin/main` before discarding; never blanket `git clean -fd`/`reset
--hard`. (Resolved as of #76; worktree confirmed still clean this cycle, no new diffs appeared.)
**Trap 99 (cycle #75):** a double-open (both duplicate PRs simultaneously OPEN with auto-merge
armed) — fix by a fixed, asymmetric tie-break stated once on the issue thread; don't keep
reactively closing/reopening.
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
**Trap 89 (cycle #68):** evidence events live in `nirmana_evidence.nirmana_elevation_campaign_events`;
build_runs live in **`public.build_runs`** (NOT `nirmana_evidence.build_runs` — that combination
doesn't exist, confirmed this cycle).
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
**Trap 78:** identify a deploy's actual shipped commit via the revision→digest→artifact-tag method
(sharpened into trap 101 this cycle — the naive `gcloud run services describe
--format="value(spec.template.spec.containers[0].image)"` can show a tag that doesn't match the
triggering run).
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

- Live deployed commit as of cycle #77's check: `296923c05` (**#2464**, one commit further than
  #76's `fda7af916`/#2463) — served via revision `amjis-web-02185-bb7`. RE-VERIFY via trap 101's
  method before reuse; #2466/#2468/#2469 merged but NOT yet deployed; #2470 merge-queued, not yet
  merged. Deploy run `34271271457` (headSha `90327f52c`/#2469) still `in_progress` as of this
  cycle's check — watch this one; it's the closest to landing #2469.
- **Lane main worktree (`/Users/Dev/nirmana-s/l2`) confirmed still CLEAN this cycle** (no new
  diffs since #76's cleanup) — still ~25+ commits behind `origin/main`, branch already fully
  merged as #2469 — **do not build new campaign work on this worktree's HEAD; use a fresh
  `origin/main` worktree**, symlink `node_modules` from here to skip reinstall, remove the symlink
  before committing.
- `nrec` = `bash platform/scripts/nirmana/nrec`; `--as executor` for W1/W2/implementation/rebuild/
  authorization, `--as verifier` for integrity_verified/asset_frozen; body needs top-level
  `"command":"record_evidence"` + `idempotency_key` + `definition_revision` + `observed_at` +
  `evidence_payload` + correct `entity_type` (trap 84).
- ONE non-terminal build_run per chart (fleet cap 3). **Fleet slot FREE** (confirmed via direct
  `public.build_runs` query, zero non-terminal rows anywhere).
- `--definition-revision t1-2026-09-08-be255ffe` always explicit.
- DATABASE_URL export each cycle: `postgresql://amjis_app:50mii04kTKDUUu54CAKdS4Bv2gx1IoWy@localhost:5432/amjis`;
  explicit timeout on every psql/dispatch invocation. Never `git stash`. No heartbeat branches.
  Never self-certify capsules. `gh pr merge <n> --auto` bare flag only (merge-queue-managed org —
  a strategy flag on top of `--auto` gets rejected).
- Issues ledger: **#2434 CLOSED**; **#2467 CLOSED**; **#1770 — RULED, sole live fix #2470
  merge-queued (not yet merged) — WATCH, do not reopen #2471 or create a third PR**; **#2450
  OPEN** but structural fix (#2461) confirmed LIVE — closure is bookkeeping only, remaining
  bo_vargottama_dhana blocker is #2468 alone, not this issue; **#2447 OPEN**; **#2443 OPEN**
  (stale bo_laksana-stall comment predates the #1770 ruling, no action); **#2446 OPEN**; **#2415
  OPEN**; **#2406 CLOSED** (bo_nakshatra_semantic already frozen).
- PRs: **#2470 OPEN, merge-queued (`is:queued` confirmed) — WATCH for merge**; **#2471 CLOSED
  PERMANENTLY** (do not reopen); **#2469 MERGED** (bo_arudha migrations 926/927, on `origin/main`,
  not yet deployed); #2468/#2466/#2464/#2463/#2461/#2460/#2458/#2457/#2454/#2453/#2452/#2451 all
  MERGED+on `origin/main` (deploy status per POSITION above — #2464 is the newest one actually
  live).
- Frozen under live t1: bo_arudha, bo_sudarshana, bo_nakshatra_semantic, bo_special_lagna (4/5).
  bo_vargottama_dhana: build_run `93dc7283...` COMPLETED; evidence chain 4/6 milestones done;
  BLOCKED until #2468 (not #2450/#2461, already live) is in the LIVE deployed image. bo_laksana:
  dead generation `425a432c0a...:da8c5ed1c69...`, stays dead per #1770's ruling; next fresh
  attempt gated on #2470 merging + deploying + a fresh trigger from a clean worktree.
