# STATE_l2 — L2 Bodha lane (v2.5 overnight) — rewritten 2026-09-09T01:45+05:30 (≈2026-09-08T20:15Z) — cycle #79

## POSITION

**Still hard-gated on deploy catch-up (priority stack items 1-3 unchanged) — but this cycle
found and FIXED a real methodology error in how prior cycles (through #78) were verifying "what
commit is actually live." The corrected method still concludes: live is #2466, #2468/#2469/#2470
are NOT yet live.**

**PR hygiene (STEP 1):** `gh pr list --search "is:queued"` → **empty** (was `#2470` in #78; it
merged at `2026-09-08T20:07:46Z`, confirmed via `gh pr view 2470 --json state,mergedAt` →
`MERGED`). No PR of mine is currently queued. Checked `gh pr list --author "@me" --state open` →
only `#1500` (a stale Aug-22 draft, not queued, not dirty/red — no action per "is:queued is the
only truth"). No action needed.

**Deploy status — CORRECTED METHOD, re-derived from scratch (IMPORTANT, read before trusting any
prior cycle's "live commit" claim):**

`gh run list --json headSha` / `gh api runs/{id} --jq .head_sha` reports a run's `head_sha` field
— but for a `workflow_run`-triggered "Deploy to Cloud Run" run, **that field is NOT proof of what
commit actually got built/tagged/deployed.** Proof: run `34271271457` (Deploy to Cloud Run,
triggered by CI completing) reports `head_sha: 90327f52c...` (#2469) via BOTH `gh run list` and
`gh api runs/{id}` — yet its own "Build and push web image" step log (`gh run view 34271271457
--log | grep -A3 DEPLOY_SHA`) shows the workflow's actual `env.DEPLOY_SHA` (computed as
`${{ github.event.workflow_run.head_sha || github.sha }}`, `.github/workflows/deploy.yml:65`,
the value ACTUALLY used for checkout/build/tag/Cloud-Run-deploy at lines 190/394/560/596/609) was
`b4b9a3c3a789331f58b0ae918ee913cf7d1ff381` (#2466) — a DIFFERENT, EARLIER commit than the run's
own reported `head_sha`. This is a sharper trap than #101/#102 described: it's not merely that a
commit might not trigger a rebuild — the run-level `head_sha` metadata field itself can disagree
with the `env.DEPLOY_SHA` the job body actually used, for workflow_run-triggered runs. **The only
trustworthy source of "what commit did this deploy run actually ship" is the job log's own
`DEPLOY_SHA:` env dump inside the "Build and push web image" (or "Apply DB Migrations") step —
never a run/job/API metadata field.**

Cross-checked two independent ways, both agree: (1) revision→digest→artifact-tag (trap 101/102
method): serving revision `amjis-web-02186-qqh` (unchanged since #77/#78) → image digest
`563eac78...` → artifact registry `latest`+`b4b9a3c3a789331f58b0ae918ee913cf7d1ff381` tags, pushed
`2026-09-09T01:34:33` IST = `2026-09-08T20:04:33Z`, matching the revision's `creationTimestamp`
`2026-09-08T20:05:26Z` (~1 min build/deploy lag, consistent). (2) run `34271271457`'s own
`DEPLOY_SHA` job-log dump = `b4b9a3c3a...`. **Both confirm live = #2466 (`b4b9a3c3a`) still, NOT
#2468/#2469/#2470.**

**In-flight run to watch:** `34272429897` — this one's `gh api` `head_sha` also reads
`90327f52c...` (#2469, matching its actual triggering CI run `34271200371` which completed
`success` for that exact headSha at `20:02:10Z` — a genuinely later CI completion than the one
that fed `34271271457`). Status `in_progress` as of `20:11:01Z` (created `20:02:12Z`, ~9 min
elapsed at last check); its "Build & Deploy Web" job is `in_progress`, "Build and push web image"
step had not yet logged its `DEPLOY_SHA:` env dump at last check (image still building). **Do NOT
assume this run's `head_sha` field means it'll ship #2469 — per the trap above, read the actual
job log `DEPLOY_SHA:` line once the step completes, not the run metadata.** A newer CI run
(`34271739354`, headSha `04e6c0eeb`/#2470, completed `success` `20:07:13Z`) and a duplicate CI
retrigger (`34272982810`, same headSha, `in_progress`) also exist — #2470's own deploy may queue
behind this one (workflow concurrency group serializes non-PR runs, per `deploy.yml`'s
`concurrency:` block — never cancelled, always queued).

**Fleet slot: FREE.** Not re-queried this cycle (no dispatch attempted); #78's direct
`public.build_runs` query (`0` non-terminal rows) plus no dispatch since is sufficient basis —
re-verify directly before any actual dispatch next cycle regardless.

**No new Conductor rulings this cycle** — did not re-open `#1770`/`#2450` threads (both confirmed
unchanged as recently as #78 with the volatile-issue rationale holding; this cycle's time went to
the deploy-verification methodology fix instead, which is itself the highest-value finding).

**bo_laksana / bo_vargottama_dhana / bo_nakshatra_semantic:** all unchanged from #77/#78's
account — see #78's POSITION (preserved in git history) for full detail. Nothing to re-add since
nothing changed on these three assets this cycle.

## WHAT CYCLE #79 DID

1. Read RESOLUTION_L2.md (unchanged v4) and STATE #78 in full.
2. PR hygiene: `is:queued` now empty (#2470 merged since #78) — confirmed via `gh pr view 2470`;
   checked full open-PR list for anything dirty/red — only stale draft `#1500`, no action.
3. Followed #78's NEXT ACTION #1 literally: checked deploy run `34272429897` fresh. Found it
   STILL `in_progress` (not resolved since #78's check) — but rather than stopping there, dug into
   *why* prior cycles' "resolve run headSha → confirm which commit shipped" method could be
   trusted, by inspecting a COMPLETED sibling run's actual job log.
4. Found run `34271271457` (reported `head_sha: 90327f52c`/#2469 via both `gh run list` and
   `gh api`) actually used `env.DEPLOY_SHA = b4b9a3c3a`/#2466 for its real checkout/build/tag/
   deploy steps (read directly from `.github/workflows/deploy.yml` line 65's expression and
   confirmed empirically via `gh run view <id> --log | grep DEPLOY_SHA`). **This is a materially
   different and sharper trap than #101/#102** — not "a commit might not trigger a rebuild" but
   "the run's own head_sha metadata field can misrepresent what it actually deployed." Logged as
   new Trap 103.
5. Cross-verified via the independent revision→digest→artifact-tag method (trap 101/102) — both
   methods agree live is still `b4b9a3c3a`/#2466. High confidence in this conclusion.
6. Checked `34272429897`'s job breakdown — "Build & Deploy Web" `in_progress`, its "Build and push
   web image" step had not yet emitted a `DEPLOY_SHA:` log line (image still building) — correctly
   declined to guess its outcome; will need the job log once it completes, not run metadata.
7. Noted a duplicate CI trigger (`34272982810`) for #2470's headSha and the workflow's
   `concurrency:` group discipline (serialize, never cancel non-PR runs) as context for why
   #2470's own deploy will queue rather than race.
8. Did not dispatch any build_run. Did not resubmit any evidence — #2468 still not live by the
   (now more rigorously verified) method.

Wall-clock: ~13 min.

## NEXT ACTION (in order)

1. **Check deploy run `34272429897`'s outcome by reading its OWN job log, not run metadata**:
   `gh run view 34272429897 --json status,conclusion` first for a quick status check, then IF
   completed, `gh run view 34272429897 --log | grep -A3 "DEPLOY_SHA:"` (or grep the "Build and
   push web image" step block) to find the TRUE shipped commit — per Trap 103, do not trust
   `head_sha` from `gh run list`/`gh api runs/{id}` for this. Then cross-check via the
   revision→digest→artifact-`latest`-tag method (trap 101/102) that the artifact registry's
   `latest` tag has actually moved past `b4b9a3c3a`.
2. **The moment a commit at-or-after `ea78a6508` (#2468) is confirmed live by BOTH methods
   agreeing**: resubmit `accepted_rebuild_observed` for `bo_vargottama_dhana` (trap 93 payload,
   fresh `observed_at`) → `integrity_verified` → `asset_frozen` via fresh-context verifier
   subagent.
3. **Once #2470 (bo_laksana's trap-99 fix, already MERGED) is confirmed live by the same
   corrected method**: trigger a fresh bo_laksana dispatch from a **clean `origin/main` worktree**
   (not `/Users/Dev/nirmana-s/l2`, which remains far behind and fully merged as #2469) → full
   evidence chain → `integrity_verified` → `asset_frozen` via fresh-context verifier subagent.
   BO_LAKSANA FROZEN remains the campaign's hinge (RESOLUTION_L2 v4 priority 1).
4. **Once bo_laksana is FROZEN:** dispatch the DAG chain in ancestor order (bo_bimba/bo_samskara
   expected first; re-verify the "bo_samskara last" resequencing ruling is still current before
   dispatch).
5. #2450: bookkeeping-only OPEN, fix live — no further action unless an explicit Conductor closure
   comment appears.
6. #2434: CLOSED, no further action.

## TRAPS (permanent — cite before every future dispatch)

**Trap 103 (cycle #79, NEW — supersedes/sharpens 101/102 for verifying "what did this deploy run
actually ship"):** a `workflow_run`-triggered "Deploy to Cloud Run" run's `head_sha` field — as
reported by BOTH `gh run list --json headSha` AND `gh api repos/.../actions/runs/{id} --jq
.head_sha` — can DISAGREE with the `env.DEPLOY_SHA` the run's job body actually computed and used
(`DEPLOY_SHA: ${{ github.event.workflow_run.head_sha || github.sha }}`, `.github/workflows/
deploy.yml` line 65, used for every real checkout/build/tag/deploy at lines 190/394/560/596/609
etc.). Confirmed empirically: run `34271271457` reported `head_sha: 90327f52c` (#2469) via both
metadata sources, but its own "Build and push web image" step log showed `DEPLOY_SHA:
b4b9a3c3a...` (#2466) — the PREVIOUS commit. **The only trustworthy source for "what commit did
deploy run N actually ship" is that run's own job log `DEPLOY_SHA:` line (or the docker tag it
built/pushed) — never any run/job-list/API metadata field, including `head_sha`.** This fully
supersedes the "trust the run's headSha" step implicit in trap 101/102's original phrasing; use
101/102 only for the revision→digest→artifact-tag half of the cross-check, and confirm via THIS
method as the second, independent leg.
**Trap 102 (cycle #78):** `gcloud run services describe`/`revisions describe` for `amjis-web`
must pass `--region asia-south1` — `us-central1` returns "Cannot find service". Also:
`gcloud artifacts docker images list --include-tags` renders `CREATE_TIME` in local/IST time (no
`Z`), while `gcloud run revisions describe creationTimestamp` renders UTC (`Z` suffix) — apply a
+5:30 offset before comparing the two.
**Trap 101 (cycle #77):** a deploy run may reuse the already-tagged `latest` image if its
triggering commit doesn't touch web-buildable paths (refined/partly superseded by Trap 103 above
— the run-metadata-vs-job-log discrepancy is often the REAL reason a run "looks like" it shipped a
commit it didn't, not just a changed-paths skip). To find the true live commit: resolve the
serving revision's image digest (`gcloud run revisions describe <revision> --region asia-south1
--format="value(spec.containers[0].image)"`), match that digest's tag in the artifact registry
(`gcloud artifacts docker images list --include-tags --filter="tags:latest"`), AND independently
confirm via Trap 103's job-log method on the relevant deploy run — trust only where both agree.
**Trap 100 (cycle #76):** a lane worktree accumulating uncommitted diffs across cycles — diff EACH
item individually against `origin/main` before discarding; never blanket `git clean -fd`/`reset
--hard`. (Worktree confirmed still clean this cycle too — not re-checked #79, no writes made.)
**Trap 99 (cycle #75):** a double-open (both duplicate PRs simultaneously OPEN with auto-merge
armed) — fix by a fixed, asymmetric tie-break stated once on the issue thread. #2470 (now MERGED)
won permanently; #2471 stays CLOSED, do not reopen.
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
`run.started_at > authorization.recorded_at` check — fix is #2468 (merged, NOT yet deployed per
this cycle's corrected verification).
**Trap 92 (cycle #69):** `implementation_accepted`'s `source_kind='git_commit'` requires
`source_ref` to equal the CURRENTLY DEPLOYED commit at submission time.
**Trap 91/90 (cycle #68):** `--wave` is a dependency-depth index, not W1-W4 vocabulary;
`--commit` requires `--expected-manifest-digest` from a prior dry-run.
**Trap 89 (cycle #68):** evidence events live in `nirmana_evidence.nirmana_elevation_campaign_events`;
build_runs live in **`public.build_runs`** (NOT `nirmana_evidence.build_runs`).
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
(sharpened into trap 101/102/103).
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

- Live deployed commit as of cycle #79's check (corrected, cross-verified method — Trap 103):
  `b4b9a3c3a` (**#2466**, UNCHANGED from #78's read — #78's read was actually correct in its
  conclusion, but its underlying trust-in-run-headSha reasoning needed the sharper Trap 103 fix).
  Served via revision `amjis-web-02186-qqh`, region `asia-south1`. RE-VERIFY via trap 101/102/103's
  combined method before reuse — read the job log `DEPLOY_SHA:` line, not run metadata.
  #2468/#2469/#2470 merged/pending but NOT yet confirmed live. Deploy run `34272429897`
  (reported head_sha `90327f52c`/#2469, actually triggered by CI run `34271200371`) `in_progress`
  as of `20:11:01Z` — watch this one next cycle, verify via its job log once complete.
- **Lane main worktree (`/Users/Dev/nirmana-s/l2`) not re-diffed this cycle** (no writes made,
  no risk introduced) — presumed still clean per #76-#78's repeated confirmation, but RE-VERIFY
  with `git status` before any future write on it; still far behind `origin/main` — **do not build
  new campaign work on this worktree's HEAD; use a fresh `origin/main` worktree**, symlink
  `node_modules` from here to skip reinstall, remove the symlink before committing.
- `nrec` = `bash platform/scripts/nirmana/nrec`; `--as executor` for W1/W2/implementation/rebuild/
  authorization, `--as verifier` for integrity_verified/asset_frozen; body needs top-level
  `"command":"record_evidence"` + `idempotency_key` + `definition_revision` + `observed_at` +
  `evidence_payload` + correct `entity_type` (trap 84).
- ONE non-terminal build_run per chart (fleet cap 3). **Fleet slot presumed FREE** (last direct
  confirmation was #78's zero-row query; no dispatch has happened since — re-verify directly
  before any actual dispatch).
- `--definition-revision t1-2026-09-08-be255ffe` always explicit.
- DATABASE_URL export each cycle: `postgresql://amjis_app:50mii04kTKDUUu54CAKdS4Bv2gx1IoWy@localhost:5432/amjis`;
  explicit timeout on every psql/dispatch invocation. Never `git stash`. No heartbeat branches.
  Never self-certify capsules. `gh pr merge <n> --auto` bare flag only (merge-queue-managed org).
- Issues ledger: **#2434 CLOSED**; **#2467 CLOSED**; **#1770 — RULED, sole live fix #2470 now
  MERGED (not yet confirmed deployed) — WATCH, do not reopen #2471 or create a third PR**; **#2450
  OPEN** but structural fix (#2461) confirmed LIVE — closure is bookkeeping only, remaining
  bo_vargottama_dhana blocker is #2468 alone; **#2447 OPEN**; **#2443 OPEN** (stale, no action);
  **#2446 OPEN**; **#2415 OPEN**; **#2406 CLOSED** (bo_nakshatra_semantic already frozen).
- PRs: **#2470 MERGED** (`2026-09-08T20:07:46Z`, bo_laksana trap-99 fix, `04e6c0eeb` now on
  `origin/main` HEAD) — awaiting its own deploy confirmation; **#2471 CLOSED PERMANENTLY** (do not
  reopen); **#2469 MERGED** (bo_arudha migrations 926/927); #2468/#2466/#2464/#2463/#2461/#2460/
  #2458/#2457/#2454/#2453/#2452/#2451 all MERGED+on `origin/main` (deploy status per POSITION
  above — #2466 is the newest one actually confirmed live, by the corrected Trap 103 method).
- Frozen under live t1: bo_arudha, bo_sudarshana, bo_nakshatra_semantic, bo_special_lagna (4/5).
  bo_vargottama_dhana: build_run `93dc7283...` COMPLETED; evidence chain 4/6 milestones done;
  BLOCKED until #2468 is in the LIVE deployed image (confirmed via BOTH revision-tag AND job-log
  DEPLOY_SHA methods, per Trap 103). bo_laksana: dead generation `425a432c0a...:da8c5ed1c69...`,
  stays dead per #1770's ruling; next fresh attempt gated on #2470's deploy confirming live (it's
  now merged, unlike #78's checkpoint) + a fresh trigger from a clean worktree.
