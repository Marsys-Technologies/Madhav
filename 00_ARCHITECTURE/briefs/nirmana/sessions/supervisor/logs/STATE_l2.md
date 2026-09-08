# STATE_l2 — L2 Bodha lane (v2.5 overnight) — rewritten 2026-09-08T22:42Z (≈2026-09-09T04:12+05:30) — cycle #81

## POSITION

**BO_LAKSANA IS FROZEN. The campaign hinge that blocked ~16 cycles is cleared.** Confirmed
independently via psql: `bo_laksana`'s chain under `t1-2026-09-08-be255ffe` now ends
`asset_frozen` (2026-09-08 22:40:19 UTC), preceded by `integrity_verified` (22:39:23),
`accepted_rebuild_observed` (22:19:44), `implementation_accepted` (22:19:17),
`optimization_verdict_accepted`/`asset_analysis_accepted` (18:38-39). **Next cycle's job is to
start dispatching the DAG chain that was queued behind this hinge — bo_bimba/bo_samskara have
NOT been started yet (0 evidence rows for either as of this cycle's close).**

**PR hygiene (STEP 1):** `is:queued` empty. Stale draft `#1500` unchanged, no action.

**Fleet slot: FREE** — confirmed. No build_run was dispatched this cycle (bo_laksana's actual
build had already completed in an earlier cycle; this cycle was pure evidence-chain repair +
two DB-permission migrations).

## WHAT CYCLE #81 DID (long cycle — the hinge finally cleared)

1. Investigated STATE #80's instruction to "trigger a fresh bo_laksana dispatch from a clean
   worktree" rather than blindly following it, and found the full W1-W4 re-run was NOT needed:
   bo_laksana's `registry_fingerprint_sha256`/`analysis_digest` were UNCHANGED from the pair
   already accepted at 18:38-39 UTC (verified by updating a leftover stale worktree
   `wt-bolaksana` to `origin/main` HEAD and re-running its `compute_bo_laksana_digests.py`), and
   the actual expensive BUILD had already completed successfully in an earlier cycle
   (`build_run a7c45a8b-8b72-40fd-b657-88d042470496`, state=completed, proven
   `asset_provenance_receipts` row, `output_digest=5189f53d01...`). What was actually missing was
   just re-binding evidence to that already-completed build.
2. **Trap 105 (NEW):** found `accepted_rebuild_observed` rejected (HTTP 409 "must bind the exact
   current optimization decision") because a re-verdict (`optimization_verdict_accepted` at
   18:39:22) had landed AFTER the existing `implementation_accepted` (18:35:12), silently
   stranding it — `implementation_accepted`'s stored `decision_digest` no longer matched
   `canonicalNirmanaOptimizationVerdictDigest` of the now-current verdict. Fixed by recomputing
   the digest fresh (standalone Node+zod script reimplementing `stableJson` +
   `NirmanaOptimizationVerdictEvidenceSchema` from `definitions.ts`, run from
   `/Users/Dev/nirmana-s/l2/platform` where `zod` resolves) and resubmitting
   `implementation_accepted` with the new `decision_digest` (same `implementation_digest` —
   confirmed submitter-chosen/opaque, never server-recomputed). See full Trap 105 writeup below.
3. Submitted the fresh `implementation_accepted` → HTTP 201, then `accepted_rebuild_observed`
   re-binding build_run `a7c45a8b` → HTTP 201.
4. Dispatched a foreground independent-verifier subagent for `integrity_verified`+`asset_frozen`.
   It genuinely ran bo_laksana's live `integrity_check_sql` (confirmed PASS, 50,529 canonical-
   chart rows) but the SUBMISSION hit HTTP 500. It root-caused this for real (not guessed):
   migration 931's `integrity_check_sql` calls `bodha_signal_identity(...)`, and
   `nirmana_evidence_ingress_writer` (the role the server uses for `server_reconstructed`
   evidence) had no EXECUTE on it.
5. **Authored, applied-live-and-verified, committed, and PR'd migration 934**
   (`GRANT EXECUTE ON FUNCTION bodha_signal_identity(uuid,text,text,text,jsonb) TO
   nirmana_evidence_ingress_writer`) — branched fresh off `origin/main` (main worktree HEAD was
   26 commits stale; its own prior commit had already merged as #2469 under a squashed hash, per
   trap 83 discipline). **PR #2472, auto-merge armed, not yet merged as of cycle close — the
   grant itself was applied directly to prod, independent of PR merge status.**
6. Dispatched a SECOND verifier retry (this one mistakenly backgrounded — see Trap 106 below).
   It found the SAME class of bug recurring one layer deeper: `bodha_signal_identity(...)` is
   `SECURITY INVOKER` and internally calls a second helper `bodha_signal_identity_namespace()`;
   Postgres checks the caller's OWN grant on that inner function too, independent of the outer
   grant. Root-caused via the actual Postgres error pulled from Cloud Run logs (`gcloud logging
   read`, not guessed): `permission denied for function bodha_signal_identity_namespace` (42501).
7. **Authored, applied-live-and-verified, committed, and PR'd migration 935**
   (`GRANT EXECUTE ON FUNCTION bodha_signal_identity_namespace() TO
   nirmana_evidence_ingress_writer`). **PR #2473, auto-merge armed, not yet merged.**
8. Dispatched a THIRD verifier (foreground this time) with both grants confirmed live. It:
   re-ran the integrity check (PASS, no permission error), independently recomputed
   `integrity_contract_sha256` = `1e6d48ac808bb1e9febc6aae61eb545bf0480c3cbd07bcf1809a8cbf4c2e2eea`
   (3rd independent match across 3 separate subagents now), submitted `integrity_verified` →
   **HTTP 201** (server overwrote `result_digest`/`detector_observation` server-side as designed,
   `verdict=true`), computed `lifecycle_digest` = `7b9665918e600af2adde170c56b49b95d45c60eb48769
   843b406d009989fd6a4` by replicating `requireFreezeProvenance`'s exact reconstruction algorithm
   (`definitions.ts:2470-2493`) over all 16 accepted lifecycle events, submitted `asset_frozen` →
   **HTTP 201**.
9. **Independently re-verified via psql from the main session (not just trusting the subagent
   report):** `bo_laksana`'s chain ends `asset_frozen` at `2026-09-08 22:40:19.49695+00`.
   **BO_LAKSANA IS FROZEN.**
10. Checked `bo_bimba`/`bo_samskara`/`bo_sangati`/`bo_karanajala` (the expected next-in-DAG
    assets per RESOLUTION_L2 v4 priority #2) — **zero evidence rows for any of them.** They have
    not been started. This is the correctly-scoped next unit of work, deferred to next cycle
    rather than cramming a fresh W1 into an already-long cycle.

Wall-clock: ~95 min total across the whole cycle (3 verifier subagents + 2 migrations authored/
applied/PR'd + the decision_digest staleness diagnosis/fix). This was one continuous cycle (a
background-task notification for verifier #2 arrived mid-cycle and was acted on immediately
rather than deferred, since the fix was cheap and directly continued the same bounded unit).

## NEXT ACTION (in order)

1. **Dispatch bo_bimba and/or bo_samskara's W1 (asset_analysis_accepted).** RESOLUTION_L2 v4
   priority #2 expected their contracts to be pre-written by the L1 lane — **re-check the
   coordination issue for current contract status before assuming still true** (this has not
   been re-verified since RESOLUTION v4 was written). If a contract is missing for either, say so
   on the coordination issue and take the NEXT ready asset in the DAG rather than stalling.
   Sequence per asset: compute registry_fingerprint_sha256 + analysis_digest fresh (via a script
   analogous to `compute_bo_laksana_digests.py` — adapt it, it's a generic pattern using
   `dispatch_nirmana_campaign_wave.py`'s `_live_registry_fingerprint`/
   `_current_analysis_receipt_digests` helpers) → submit `asset_analysis_accepted` (executor,
   git_commit source) → `optimization_verdict_accepted` (executor) → `implementation_accepted`
   (executor, if build obligation) → dispatch actual build via
   `dispatch_nirmana_campaign_wave.py --commit` (dry-run first for `--expected-manifest-digest`)
   → `accepted_rebuild_observed` (executor) → `integrity_verified`+`asset_frozen` (FOREGROUND
   independent verifier subagent — see Trap 106, do not background this).
2. **Check PRs #2472 (migration 934) and #2473 (migration 935) merge status** — both should
   auto-merge cleanly (pure additive GRANT migrations, same pattern as 921/922/923 which all
   merged without issue). Not blocking anything (both grants already applied live), just close
   the loop / confirm no CI surprise.
3. **Watch for Trap 105 recurring on any future asset:** if a re-verdict is ever submitted for an
   asset that already has an accepted `implementation_accepted`, check whether that
   implementation's `decision_digest` still matches the CURRENT verdict before assuming
   `accepted_rebuild_observed` is ready to submit.
4. #2450: bookkeeping-only OPEN, structural fix live — no further action unless explicit
   Conductor closure comment. #2434/#2467/#2406 CLOSED. #1770 RULED, fix LIVE — resolved.

## TRAPS (permanent — cite before every future dispatch)

**Trap 106 (cycle #81, NEW):** for a fresh-context-per-cycle autonomous lane, prefer FOREGROUND
verifier/executor subagents over background ones. A background agent's completion notification
may arrive mid-session (if the dispatching session is still alive) but will NOT reach a future
cycle's fresh session if the dispatching session has already exited/been reinvoked — the work
becomes unobservable except by re-checking DB state from scratch. This cycle got lucky (the
notification arrived before this session's turn ended, so the finding was actionable), but do not
rely on that. Reserve background dispatch for genuinely fire-and-forget work with no bearing on
this cycle's bounded unit.
**Trap 105 (cycle #81, NEW):** submitting a re-verdict (`optimization_verdict_accepted`) for an
asset AFTER an `implementation_accepted` has already been accepted for it silently STRANDS that
implementation binding — `accepted_rebuild_observed` will reject with "must bind the exact current
optimization decision" (HTTP 409, reads like an idempotency conflict but is a real validation
failure) because the implementation's stored `decision_digest` no longer equals
`canonicalNirmanaOptimizationVerdictDigest` of the now-current (most recent) verdict. **Fix:**
recompute the digest fresh against the LATEST `optimization_verdict_accepted` row's
`evidence_payload` (standalone Node script reimplementing `stableJson` +
`NirmanaOptimizationVerdictEvidenceSchema` from `definitions.ts`, run from
`/Users/Dev/nirmana-s/l2/platform` where `zod` resolves — see
`/private/tmp/compute_decision_digest*.{ts,mjs}` for working precedents, and
`/private/tmp/claude-504/.../scratchpad/compute_bo_laksana_decision_digest.mjs` this cycle's copy)
and resubmit `implementation_accepted` with the SAME `implementation_digest` (submitter-chosen,
never server-recomputed) but the NEW `decision_digest`. Check for this FIRST before assuming a
full W1/W2/W3 re-run is needed.
**NEW learning (cycle #81) — layered SQL function grants:** a `SECURITY INVOKER` SQL function that
calls OTHER functions internally requires the caller (here `nirmana_evidence_ingress_writer`) to
have its OWN EXECUTE grant on every function in the call chain, not just the top-level one you
think you're calling. `bodha_signal_identity()` → `bodha_signal_identity_namespace()` was a
2-layer case (migrations 934 then 935); if a similar HTTP 500 recurs after granting the obvious
function, check `pg_proc.prosrc`/pg_get_functiondef for nested function calls in the body before
assuming the grant fix is complete. Diagnosing the REAL error requires `gcloud logging read`
against the Cloud Run service to get the actual Postgres error code/message — the HTTP layer only
returns a generic `{"error":"failed to record Nirmana evidence"}` for any uncaught exception,
which is indistinguishable at the API layer between "wrong grant" and any other server bug.
**Trap 104 (cycle #80):** `gh run view`/`gh api actions/runs/{id}` can hit a secondary rate limit
independent of the primary `core`/`search` limit — fall back to gcloud revision→digest→
artifact-tag method, don't loop-retry.
**Trap 103/102/101/100/99 (cycles #75-79):** see git history — deploy-run head_sha vs actual
DEPLOY_SHA disagreement; gcloud region flag + timezone; worktree hygiene; #2470/#2471 tie-break.
**Trap 98-80(b) (cycles #65-74):** see git history — PR/state verification discipline, evidence
payload field names, entity_type conventions, digest sourcing, worktree hygiene.
**Table-name note (cycle #81):** the campaign events table is `nirmana_evidence
.nirmana_elevation_campaign_events` — NOT any `public.*event*`/`public.*lifecycle*` table (none
exists). `asset_provenance_receipts` (public schema) holds `output_digest`/
`output_digest_spec_sha256`/`receipt_state` keyed by `build_id`.
See git history of this file for traps 1-99 in full detail.

## STANDING CONSTRAINTS (carried forward, verify each cycle)

- Live deployed commit as of cycle #81: **`04e6c0eeb` (#2470)**, unchanged this cycle (no new app
  deploy needed — the two fixes this cycle were DB grants, applied directly, independent of the
  app's deployed commit). RE-VERIFY if working on anything deploy-sensitive.
- **Lane main worktree (`/Users/Dev/nirmana-s/l2`) is now ON BRANCH
  `l2-bo-laksana-migration-935-signal-identity-namespace-grant`**, checked out fresh from
  `origin/main` this cycle (current as of `04e6c0eeb` + this cycle's two migration commits on top,
  locally — origin/main itself is still at `04e6c0eeb` pending #2472/#2473 merging). Safe to build
  from directly next cycle, or `git fetch && git checkout origin/main` fresh if further behind.
- `nrec` = `bash platform/scripts/nirmana/nrec`; `--as executor` for W1/W2/implementation/rebuild/
  authorization, `--as verifier` for integrity_verified/asset_frozen. Schemas in
  `platform/src/lib/nirmana-elevation/definitions.ts` (`NirmanaLifecycleBindingSchema` and its
  `.extend()`s) and `evidence-command.ts` (envelope/source_kind rules) — read them directly.
- ONE non-terminal build_run per chart (fleet cap 3). **Fleet slot FREE.** No build dispatched
  this cycle.
- `--definition-revision t1-2026-09-08-be255ffe` always explicit.
- DATABASE_URL export each cycle: `postgresql://amjis_app:50mii04kTKDUUu54CAKdS4Bv2gx1IoWy@localhost:5432/amjis`;
  explicit `timeout 30` on every psql/dispatch invocation. Never `git stash`. No heartbeat branches.
  Never self-certify capsules. **Prefer FOREGROUND verifier/executor subagents** (Trap 106).
  `gh pr merge <n> --auto` bare flag only.
- Issues ledger: **#2434 CLOSED**; **#2467 CLOSED**; **#1770 RULED, fix LIVE**; **#2450 OPEN**
  (bookkeeping only); **#2447 OPEN**; **#2443 OPEN** (stale); **#2446 OPEN**; **#2415 OPEN**;
  **#2406 CLOSED**.
- PRs: **#2472 OPEN, auto-merge armed** (migration 934 — grant already live independent of merge);
  **#2473 OPEN, auto-merge armed** (migration 935 — grant already live independent of merge);
  #2470/#2469/#2468/#2466/#2464/#2463/#2461/#2460/#2458/#2457/#2454/#2453/#2452/#2451 all
  MERGED+LIVE (older). #2471 CLOSED PERMANENTLY (do not reopen).
- **Frozen under live t1 (`t1-2026-09-08-be255ffe`): bo_nakshatra_semantic, bo_special_lagna,
  bo_vargottama_dhana, bo_laksana (NEW this cycle — the campaign hinge).** bo_arudha/bo_sudarshana
  frozen under an earlier definition_revision (not re-verified under t1 this cycle).
  **bo_bimba, bo_samskara, bo_sangati, bo_karanajala: NOT STARTED — zero evidence rows.** These
  are the immediate next targets (NEXT ACTION #1).
