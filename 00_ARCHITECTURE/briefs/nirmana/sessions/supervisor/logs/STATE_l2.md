# STATE_l2 — L2 Bodha lane (v2.5 overnight) — rewritten 2026-09-08T22:10Z (≈2026-09-09T03:40+05:30) — cycle #80

## POSITION

**Deploy caught up — confirmed live commit is now `04e6c0eeb` (#2470), which is a descendant of
`ea78a6508` (#2468, trap-93 fix) via `git merge-base --is-ancestor` on `origin/main`. This
unblocked bo_vargottama_dhana, and this cycle drove it all the way to FROZEN.**

**PR hygiene (STEP 1):** `gh pr list --search "is:queued"` → empty. Only own open PR is stale
draft `#1500` (not queued, not dirty/red) — no action.

**Deploy verification this cycle (gcloud method, gh Actions API unavailable — see below):**
`gcloud run services describe amjis-web --region asia-south1` → serving revision
`amjis-web-02188-9kq` (created `2026-09-08T20:27:40Z`), image digest
`sha256:974a8002...5324d63`. That exact digest appears in the artifact registry push batch at
`2026-09-09T01:56:23` IST (`=2026-09-08T20:26:23Z`), the SAME batch as the multi-arch manifest row
tagged `04e6c0eeb511be38a423756207f0780e63adc9f8` + `latest`. Timestamps line up (image pushed
~1 min before the revision's creation). **This is the revision→digest→artifact-tag method (trap
101/102) — did NOT get to cross-check via trap 103's job-log method this cycle because the
`gh api .../actions/runs/*` endpoint was returning `HTTP 403 API rate limit exceeded for user ID
214666590` for the specific runs/{id} lookup (see Trap 104 below) while `gh pr view`/`gh pr list`
worked fine seconds apart.** Confidence is still high: the revision-digest-registry-tag method
reads Cloud Run's actual serving state directly, which is stronger ground truth than a CI job log
— but the NEXT cycle should still do the job-log cross-check opportunistically if `gh run view`
recovers, purely for completeness, not because there's live doubt.

`git log --oneline origin/main` confirms ancestry: `04e6c0eeb (#2470)` → `90327f52c (#2469)` →
`ea78a6508 (#2468)` → `b4b9a3c3a (#2466)` → ... — i.e. **live now includes #2468, #2469, #2470,
all three previously-unconfirmed merges.**

**Fleet slot: FREE** — confirmed directly, `SELECT count(*) FROM public.build_runs WHERE state IN
('planned','running','paused')` → `0`, checked twice this cycle (before and after the evidence
work; evidence submission does not create build_runs, only build dispatch does).

## WHAT CYCLE #80 DID

1. Read RESOLUTION_L2.md (v4, unchanged) and STATE #79 in full.
2. PR hygiene: `is:queued` empty, no action.
3. Attempted STATE #79's NEXT ACTION #1 (check run `34272429897` via job log) — `gh run view` /
   `gh api runs/{id}` both hit `HTTP 403 rate limit exceeded for user ID 214666590` repeatedly for
   that specific call, while `gh pr view`/`gh pr list` succeeded seconds before and after (see Trap
   104). Pivoted to the independent gcloud revision→digest→artifact-tag method instead of
   waiting/retrying (LAWS: never poll in-session).
4. Found: current serving revision `amjis-web-02188-9kq` (created `20:27:40Z`) → image digest
   matches the artifact-registry push batch tagged `04e6c0eeb`(#2470)+`latest`, pushed `20:26:23Z`.
   **Live has moved past #2466 to #2470**, confirmed further via `git merge-base --is-ancestor
   ea78a6508 04e6c0eeb` → yes, #2468's trap-93 fix is included in what's live.
5. Per RESOLUTION_L2 priority + STATE #79 NEXT ACTION #2: with #2468 confirmed live, resubmitted
   `accepted_rebuild_observed` for `bo_vargottama_dhana` (fresh `observed_at`, referencing the
   already-COMPLETED build_run `93dc7283-a39b-4379-bb95-d3c7b7badc92`). Sourced every digest field
   by READING it (never hand-computed, per trap 87):
   - `analysis_digest`, `registry_fingerprint_sha256`, `decision_digest`, `implementation_digest`
     — read from the already-accepted `implementation_accepted` event's own `evidence_payload`.
   - `authorization_sha256` — read from the `build_run_authorized` event
     (`entity_type='build_run'`, `entity_id=<build_run uuid>`, per trap 84).
   - `output_digest` + `output_digest_spec_sha256` — read from
     `public.asset_provenance_receipts` (`receipt_state='proven'`, matched to `build_id=93dc7283...`).
   - `wave_index=0`, `build_run_id`, `source_ref='build_run:93dc7283...'`, `source_kind='build_run'`.
   Submitted via `nrec --as executor --file <cmd.json>` → **HTTP 201 `{"outcome":"created"}`**.
6. Dispatched a fresh-context INDEPENDENT VERIFIER subagent (not the executor identity) to:
   run `bo_vargottama_dhana`'s actual `integrity_check_sql` against the live DB itself (not trust
   the executor's claim), confirm a genuine pass with real row counts (10 `dhana_axis` +
   4 `vargottama_amplification` rows for the canonical chart), then submit `integrity_verified`
   and `asset_frozen` via `nrec --as verifier`. The subagent discovered `integrity_verified`'s real
   schema requires `integrity_contract_sha256` + `result_digest` (NOT the `{}`-payload my task
   brief guessed) — it computed `integrity_contract_sha256` by invoking the actual production
   `canonicalNirmanaIntegrityContractDigest` function (via a `server-only`-stubbed `tsx` shim),
   confirmed correct because the server's own independent re-execution of the integrity SQL
   (visible in the persisted row's `detector_observation`) matched. For `asset_frozen`'s
   `lifecycle_digest` (checked exactly, not server-recomputed), it replayed the server's own
   `stableJson`+SHA-256 algorithm (read verbatim from `definitions.ts`) against the real 7-event
   lifecycle chain in a small Node script — accepted on the first submission, confirming byte-exact
   correctness. Both submissions returned **HTTP 201**.
7. **Verified directly via psql** (not just trusting the subagent's report):
   ```
   entity_id=bo_vargottama_dhana, definition_revision=t1-2026-09-08-be255ffe:
   asset_analysis_accepted → optimization_verdict_accepted → asset_analysis_accepted →
   optimization_verdict_accepted → implementation_accepted → accepted_rebuild_observed →
   integrity_verified → asset_frozen   (8 rows, chain complete, ends in asset_frozen 22:06:48Z)
   ```
   **BO_VARGOTTAMA_DHANA IS NOW FROZEN UNDER LIVE t1.**
8. Did not attempt a fresh bo_laksana dispatch this cycle (RESOLUTION priority #1's hinge) — that
   is genuinely the next unit of work (a full W1/W2 re-run + redispatch from a clean worktree is a
   large bounded task on its own; this cycle's bounded unit was the bo_vargottama_dhana unblock).

Wall-clock: ~35 min (includes the ~8 min independent-verifier subagent).

## NEXT ACTION (in order)

1. **Trigger a fresh bo_laksana dispatch from a CLEAN `origin/main` worktree** (NOT
   `/Users/Dev/nirmana-s/l2`, which stays far behind `origin/main` and should never be built from
   directly — trap 83). This is now RESOLUTION_L2 v4's priority #1, the campaign's hinge — bo_bimba
   / bo_samskara and the rest of the DAG queue behind it. Sequence: fresh worktree at
   `origin/main` HEAD (now `04e6c0eeb`+ whatever's newer) → symlink `node_modules` from
   `/Users/Dev/nirmana-s/l2` (trap 83) → full W1/W2 re-run as executor (trap 75/88 — own-contract-
   changed requires full re-run, NOT just a resubmit) → dispatch → evidence chain
   (asset_analysis_accepted → optimization_verdict_accepted → implementation_accepted →
   build_run_authorized → accepted_rebuild_observed) → `integrity_verified` + `asset_frozen` via a
   fresh-context INDEPENDENT VERIFIER subagent (same pattern used successfully this cycle for
   bo_vargottama_dhana — reuse that pattern/prompt shape).
2. **Once bo_laksana is FROZEN:** dispatch the DAG chain in ancestor order — bo_bimba / bo_samskara
   expected first (their contracts were being pre-written by the L1 lane as of RESOLUTION v4;
   re-verify current status before assuming still true — re-read the coordination issue). If a
   contract is missing for the expected-next asset, say so on the coordination issue and take the
   NEXT ready asset per RESOLUTION_L2 v4 priority #2, rather than stalling.
3. **Opportunistic, not blocking:** if `gh run view`/`gh api actions/runs/{id}` has recovered from
   the rate-limit seen this cycle (Trap 104), do the trap-103 job-log cross-check on deploy run
   `34272429897`/`34271739354`'s "Build and push web image" step purely to close the loop — but do
   NOT let this block bo_laksana dispatch; the gcloud revision-digest-tag method already gives high
   confidence live=`04e6c0eeb`(#2470).
4. #2450: bookkeeping-only OPEN, structural fix live — no further action unless an explicit
   Conductor closure comment appears.
5. #2434, #2467, #2406: CLOSED, no further action.
6. #1770: RULED, fix #2470 now confirmed LIVE (this cycle) — consider this fully resolved; no
   further action unless new evidence contradicts.

## TRAPS (permanent — cite before every future dispatch)

**Trap 104 (cycle #80, NEW):** `gh run view <id>` / `gh api repos/.../actions/runs/{id}` can return
`HTTP 403 "API rate limit exceeded for user ID 214666590"` for that SPECIFIC call while `gh pr
view`/`gh pr list` succeed seconds before/after on the same token — this is NOT the primary
`core`/`search` rate limit (`gh api rate_limit` showed `remaining: 5000/5000` at the same moment).
Read as a secondary/abuse-detection throttle on the Actions-runs endpoint specifically, plausibly
from fleet-wide concurrent polling across lanes (conductor/L1/L2/L3 all watching deploy runs). **Do
NOT loop-retry this in-session (LAWS: never poll)** — fall back immediately to the independent
gcloud revision→digest→artifact-tag method (trap 101/102), which reads Cloud Run's actual serving
state directly and needs no GitHub Actions API call at all. Re-attempt the trap-103 job-log
cross-check next cycle only opportunistically, never as a gate.
**Trap 103 (cycle #79):** a `workflow_run`-triggered "Deploy to Cloud Run" run's `head_sha` field
(via `gh run list`/`gh api runs/{id}`) can DISAGREE with the `env.DEPLOY_SHA` the job body actually
used (`.github/workflows/deploy.yml` line 65) — only that run's own job-log `DEPLOY_SHA:` line (or
the docker tag it pushed) is trustworthy for "what did this run ship."
**Trap 102 (cycle #78):** `gcloud run services/revisions describe` for `amjis-web` needs
`--region asia-south1`. Artifact registry `CREATE_TIME` is IST (no `Z`); Cloud Run
`creationTimestamp` is UTC (`Z`) — apply +5:30 before comparing.
**Trap 101 (cycle #77):** to find the true live commit, resolve serving revision → image digest →
artifact-registry tag, AND cross-check via trap 103's job-log method where available.
**Trap 100 (cycle #76):** diff each uncommitted worktree item individually vs `origin/main` before
discarding; never blanket `git clean -fd`/`reset --hard`.
**Trap 99 (cycle #75):** #2470 (bo_laksana trap-99 fix) won the double-open tie-break permanently
— MERGED and now confirmed LIVE (cycle #80). #2471 stays CLOSED, do not reopen.
**Trap 98/97/96b/96/95/94 (cycles #73-74):** see git history — PR/state verification discipline.
**Trap 93 (cycle #69):** `accepted_rebuild_observed`'s independent `run.started_at >
authorization.recorded_at`-family check — fix #2468, confirmed LIVE this cycle (#80), and its
resubmission for `bo_vargottama_dhana` succeeded cleanly (HTTP 201) with no timing rejection.
**Trap 92/91/90/89/88/87/86/85/84/83/82/81/80(b) (cycles #65-69):** see git history — evidence
payload field names, entity_type conventions, digest sourcing discipline, worktree hygiene.
**NEW learning (cycle #80, not yet numbered as a trap — informational):** `integrity_verified`'s
real evidence_payload schema requires `integrity_contract_sha256` + `result_digest` in addition to
`registry_fingerprint_sha256` + `analysis_digest` — NOT an empty `{}` payload as might be assumed
from the base schema's `.default({})`. `integrity_contract_sha256` must be computed via the actual
production `canonicalNirmanaIntegrityContractDigest` function (`definitions.ts`) — the server
independently re-runs the integrity SQL and overwrites `result_digest`/`detector_observation`
server-side regardless of what's submitted, so a schema-valid placeholder for `result_digest` is
fine, but `integrity_contract_sha256` must be genuinely computed (cross-verify by checking the
server's own recomputed value matches in the persisted row). `asset_frozen`'s `lifecycle_digest` is
checked EXACTLY (not server-recomputed) — must replay the server's own `stableJson`+SHA-256
algorithm (read verbatim from `definitions.ts` lines ~2206-2213) against the real lifecycle event
rows for that entity/definition_revision. Full worked example: see cycle #80's verifier subagent
transcript, or replicate against `bo_vargottama_dhana`'s now-frozen chain as a reference.
See git history of this file for traps 1–92 in full detail.

## STANDING CONSTRAINTS (carried forward, verify each cycle)

- Live deployed commit as of cycle #80: **`04e6c0eeb` (#2470)**, confirmed via gcloud
  revision→digest→artifact-tag method (serving revision `amjis-web-02188-9kq`, region
  `asia-south1`, created `2026-09-08T20:27:40Z`). Ancestry-confirmed to include #2468 and #2469.
  RE-VERIFY before reuse if more than ~1hr has passed — deploys are landing frequently.
- **Lane main worktree (`/Users/Dev/nirmana-s/l2`) still far behind `origin/main`** — do not build
  new campaign work (e.g. the bo_laksana dispatch) on this worktree's HEAD; use a fresh
  `origin/main` worktree, symlink `node_modules` from here, remove the symlink before committing.
  Not re-diffed this cycle (no writes made here beyond reading files and running psql/nrec).
- `nrec` = `bash platform/scripts/nirmana/nrec`; `--as executor` for W1/W2/implementation/rebuild/
  authorization, `--as verifier` for integrity_verified/asset_frozen; body needs top-level
  `"command":"record_evidence"` + `idempotency_key` + `definition_revision` + `observed_at` +
  `evidence_payload` + correct `entity_type` (trap 84). Schemas live in
  `platform/src/lib/nirmana-elevation/definitions.ts` (search `NirmanaLifecycleBindingSchema`,
  `NirmanaRebuildEvidenceSchema`) and `evidence-command.ts` (search `assetReceipt`,
  `typedLifecyclePayloads`) — read them directly rather than guessing payload shape; this cycle's
  verifier subagent had to correct a wrong assumption about `integrity_verified`'s payload shape.
- ONE non-terminal build_run per chart (fleet cap 3). **Fleet slot FREE**, confirmed directly twice
  this cycle (`SELECT count(*) FROM public.build_runs WHERE state IN ('planned','running','paused')`
  → 0 both times).
- `--definition-revision t1-2026-09-08-be255ffe` always explicit.
- DATABASE_URL export each cycle: `postgresql://amjis_app:50mii04kTKDUUu54CAKdS4Bv2gx1IoWy@localhost:5432/amjis`;
  explicit `timeout 30` on every psql/dispatch invocation. Never `git stash`. No heartbeat branches.
  Never self-certify capsules (executor and verifier must be genuinely separate identities/subagent
  contexts — this cycle correctly used a fresh-context subagent for the verifier role rather than
  self-certifying). `gh pr merge <n> --auto` bare flag only (merge-queue-managed org).
- Issues ledger: **#2434 CLOSED**; **#2467 CLOSED**; **#1770 — RULED, fix #2470 CONFIRMED LIVE this
  cycle**; **#2450 OPEN** (bookkeeping only, structural fix #2461 live); **#2447 OPEN**; **#2443
  OPEN** (stale, no action); **#2446 OPEN**; **#2415 OPEN**; **#2406 CLOSED**.
- PRs: **#2470 MERGED + CONFIRMED LIVE** (cycle #80); **#2471 CLOSED PERMANENTLY** (do not reopen);
  **#2469 MERGED + LIVE** (bo_arudha migrations 926/927); **#2468 MERGED + LIVE** (trap-93 fix);
  #2466/#2464/#2463/#2461/#2460/#2458/#2457/#2454/#2453/#2452/#2451 all MERGED+LIVE (older).
- **Frozen under live t1 (definition_revision `t1-2026-09-08-be255ffe`): bo_nakshatra_semantic,
  bo_special_lagna, bo_vargottama_dhana (NEW this cycle).** bo_arudha/bo_sudarshana frozen under
  an earlier definition_revision (not re-verified under t1 this cycle — check on next touch if it
  matters for DAG-dependency purposes). **bo_laksana: NOT yet frozen** — dead generation
  `425a432c0a...:da8c5ed1c69...` stays dead per #1770's ruling (now fully resolved/live); needs a
  FRESH dispatch from a clean `origin/main` worktree (STATE NEXT ACTION #1 above) — this is now the
  single most important open item, RESOLUTION_L2 v4 priority #1, the campaign's hinge.
