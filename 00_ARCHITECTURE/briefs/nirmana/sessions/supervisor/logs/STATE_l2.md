# STATE_l2 — L2 Bodha lane (v2.5 overnight) — rewritten 2026-09-08T22:33Z (≈2026-09-09T04:03+05:30) — cycle #81

## POSITION

**bo_laksana's freeze is now unblocked at the DB-permission layer. This cycle found and fixed the
actual reason the hinge asset couldn't freeze, but the freeze submission itself was still running
in a background subagent when this cycle had to close — NEXT CYCLE MUST CHECK DB STATE FIRST
(see NEXT ACTION #1) before re-doing any of this work.**

**PR hygiene (STEP 1):** `is:queued` empty. Only stale draft `#1500` (not queued/dirty/red, no
action, unchanged for many cycles).

**Fleet slot: FREE** — `SELECT count(*) FROM public.build_runs WHERE state IN
('planned','running','paused')` → `0`. No build was dispatched this cycle (evidence-only + one
migration).

## WHAT CYCLE #81 DID

1. Read RESOLUTION_L2 v4 + STATE #80. STATE #80's NEXT ACTION #1 said "trigger a fresh bo_laksana
   dispatch from a clean worktree" — **investigated first rather than blindly re-dispatching, and
   found the full W1-W4 re-run was NOT actually needed.**
2. Found a stale `wt-bolaksana` worktree at `/private/tmp/claude-504/.../1f0521f3.../scratchpad/
   wt-bolaksana` (leftover from an earlier cycle/session, commit `36fa3c8d2`, an ancestor of
   `origin/main`). Updated it to `origin/main` HEAD (`04e6c0eeb`, #2470) and re-ran its leftover
   `compute_bo_laksana_digests.py` script: **registry_fingerprint_sha256 and analysis_digest for
   bo_laksana are UNCHANGED from the pair already accepted at 18:38-18:39 UTC** (`425a432c0a.../
   da8c5ed1c6...`) — i.e. bo_laksana's own contract has NOT moved since the last W1/W2, despite 26+
   commits landing on `origin/main` since. **No fresh W1/W2 was needed.**
3. Queried `nirmana_evidence.nirmana_elevation_campaign_events` (schema `nirmana_evidence`, NOT
   `public` — table is `nirmana_elevation_campaign_events`) directly and found bo_laksana's chain
   already had a self-consistent `asset_analysis_accepted` (18:38:27) → `optimization_verdict_
   accepted` (18:39:22) pair, PLUS an `implementation_accepted` from 18:35:12 (i.e. submitted
   BEFORE the final re-verdict) — this is exactly the situation the 18:39:22 verdict's own
   evidence_refs described: "Re-binds already-completed build_run a7c45a8b-8b72-40fd-b657-
   88d042470496 ... to the live v2 contract so implementation_accepted->accepted_rebuild_observed
   can proceed." **The actual expensive BUILD had already run and completed successfully
   (build_run a7c45a8b, state=completed, `asset_provenance_receipts` row proven, output_digest
   `5189f53d01...`) — this was never actually about re-running W1-W4, only about re-binding
   evidence to it.**
4. Attempted `accepted_rebuild_observed` directly, reusing implementation_accepted's stored
   `decision_digest` (`5b3933dc...`) — **rejected: HTTP 409 "accepted_rebuild_observed must bind
   the exact current optimization decision."** Root cause: the 18:35:12 `implementation_accepted`
   was bound to an EARLIER verdict (before the 18:39:22 re-verdict), so its `decision_digest` no
   longer equals `canonicalNirmanaOptimizationVerdictDigest` of the CURRENT (most recent) verdict.
   **NEW TRAP (105):** submitting a re-verdict (`optimization_verdict_accepted`) AFTER an already-
   accepted `implementation_accepted` silently strands that implementation binding — the very next
   `accepted_rebuild_observed` attempt will reject with "must bind the exact current optimization
   decision" even though nothing about the implementation itself changed. **Fix:** recompute
   `canonicalNirmanaOptimizationVerdictDigest` fresh against the CURRENT (most recent)
   `optimization_verdict_accepted` row's `evidence_payload`, and resubmit `implementation_accepted`
   with that new `decision_digest` (same `implementation_digest` value is fine and correct — it is
   submitter-chosen/opaque, never server-recomputed, per `requireImplementationProvenance` in
   `definitions.ts` — it only needs to be a fresh, unique, schema-valid 64-hex value bound to the
   right decision).
5. Computed the fresh `decision_digest` via a standalone Node script (zod + a byte-exact
   reimplementation of `stableJson` + `NirmanaOptimizationVerdictEvidenceSchema` from
   `definitions.ts`, run from `/Users/Dev/nirmana-s/l2/platform` where `zod` resolves — do NOT try
   to import `definitions.ts` directly, it has `import 'server-only'` + a huge dependency graph;
   reimplementing the pure hash logic standalone is the reliable path, confirmed working twice now
   across different sessions per `/private/tmp/compute_decision_digest*.{ts,mjs}` precedents) fed
   the LATEST verdict's actual `evidence_payload` (fetched via `psql -t -A` to avoid transcription
   errors) → **`0283a4d608b384194b966f4a14adb700797e9fdad4ac164faecafe8869e5a768`**.
6. Submitted fresh `implementation_accepted` (same registry_fingerprint/analysis_digest/
   implementation_digest, new decision_digest, source_ref=git:04e6c0eeb511be38a423756207f0780e
   63adc9f8 = current deployed commit) via `nrec --as executor` → **HTTP 201**.
7. Submitted `accepted_rebuild_observed` re-binding build_run `a7c45a8b-8b72-40fd-b657-
   88d042470496` (authorization_sha256 `8a21e786...` read from its `build_run_authorized` event;
   output_digest `5189f53d01...` + output_digest_spec_sha256 `39827b99...` read from
   `asset_provenance_receipts`) with the NEW decision_digest → **HTTP 201**. Chain now:
   `asset_analysis_accepted`(18:38) → `optimization_verdict_accepted`(18:39) →
   `implementation_accepted`(22:19:17) → `accepted_rebuild_observed`(22:19:44).
8. Dispatched a fresh-context INDEPENDENT VERIFIER subagent (foreground) to run
   `integrity_verified`+`asset_frozen`. It did real, honest work — independently re-derived
   `registry_fingerprint_sha256`, confirmed the chain, **actually ran bo_laksana's live
   `integrity_check_sql` and confirmed it PASSES** (50,529 canonical-chart rows, real counts) — but
   the `integrity_verified` SUBMISSION itself got HTTP 500 (generic uncaught exception, not a
   validation 409). It root-caused this FOR REAL rather than guessing: `bo_laksana`'s migration-931
   `integrity_check_sql` calls `bodha_signal_identity(uuid,text,text,text,jsonb)` (the migration-661
   identity function); the server runs `server_reconstructed` evidence (i.e.
   `integrity_verified`/`asset_frozen`) as DB role `nirmana_evidence_ingress_writer`
   (`evidence-ingress.ts`), which had **no EXECUTE grant on that function** (confirmed directly:
   `has_function_privilege(...)` = false). Same defect class as migrations 921/922/923 (a
   table/function a specific asset's integrity check needs, never granted to this role) — just a
   FUNCTION grant instead of a TABLE grant this time.
9. **Authored, applied-live-and-verified, committed, and PR'd migration 934**
   (`platform/migrations/934_nirmana_evidence_ingress_writer_bodha_signal_identity_grant.sql`) —
   `GRANT EXECUTE ON FUNCTION bodha_signal_identity(uuid,text,text,text,jsonb) TO
   nirmana_evidence_ingress_writer`. Applied directly to production DB THIS cycle (surgical-
   migrations-verified standard); confirmed `has_function_privilege(...)` flips false→true.
   Note: main worktree HEAD (`/Users/Dev/nirmana-s/l2`) was 26 commits behind `origin/main` (its
   own commit `2f26ca840` had already merged as #2469 under a squashed hash) — branched the
   migration off a FRESH `origin/main` checkout (`git checkout -b ... origin/main`), not off the
   stale local HEAD, per trap 83. **PR #2472, auto-merge armed.**
10. Dispatched ANOTHER fresh-context INDEPENDENT VERIFIER subagent (background, agent id
    `ab1863b5fd7283573`) to retry `integrity_verified`+`asset_frozen` now that the grant is live.
    **This was still running when the cycle had to close — its outcome is UNKNOWN. Do not assume
    it succeeded OR failed; check the DB directly (NEXT ACTION #1).** In hindsight this should have
    been run in the foreground like step 8's verifier (which completed cleanly in ~6 min) — running
    the retry in the background was a process mistake this cycle, since a fresh-context session next
    cycle cannot reliably receive that agent's completion notification. If the DB shows the chain
    still stuck at `accepted_rebuild_observed` (not `integrity_verified`/`asset_frozen`) when you
    read this, that background agent's work was lost/orphaned — just redispatch a FRESH
    (foreground) verifier following the exact recipe embedded in this cycle's dispatch prompt
    (steps 8-9 above cover everything it needs: schemas, the now-live grant, the digest values, the
    `integrity_contract_sha256` a prior verifier already computed once —
    `1e6d48ac808bb1e9febc6aae61eb545bf0480c3cbd07bcf1809a8cbf4c2e2eea` — independently recompute it
    fresh rather than trust it, but it's a strong prior).

Wall-clock: ~50 min total (includes ~6 min for the first foreground verifier).

## NEXT ACTION (in order)

1. **FIRST THING: check DB state directly before doing anything else.**
   ```sql
   SELECT event_type, recorded_at FROM nirmana_evidence.nirmana_elevation_campaign_events
   WHERE entity_id='bo_laksana' AND definition_revision='t1-2026-09-08-be255ffe'
   ORDER BY recorded_at DESC LIMIT 3;
   ```
   - If top row is `asset_frozen` → **BO_LAKSANA IS FROZEN.** The campaign hinge is cleared. Move
     straight to dispatching the DAG chain in ancestor order (bo_bimba/bo_samskara expected first —
     re-check the coordination issue for current contract status, RESOLUTION_L2 priority #2).
   - If top row is still `accepted_rebuild_observed` (22:19:44) → the background verifier (agent
     `ab1863b5fd7283573`) did not land its work (orphaned/lost, or still running with no way for
     this fresh session to observe it). **Redispatch a FRESH foreground verifier subagent** for
     `integrity_verified`+`asset_frozen` — migration 934's grant is live in the DB regardless of PR
     #2472's merge status (it was applied directly), so this should now succeed cleanly. Use the
     same task recipe as cycle #81 step 8/10 (full schemas, bound digests, the now-confirmed-live
     grant) — do NOT re-diagnose from scratch, the root cause and fix are already known and applied.
   - If top row is `integrity_verified` (not yet `asset_frozen`) → just need the `asset_frozen`
     step; read the lifecycle_digest reconstruction logic in `definitions.ts` and submit it.
2. **Check PR #2472's merge status** (`gh pr view 2472`) — should auto-merge cleanly (pure
   additive GRANT migration, same pattern as 921/922/923 which all merged without issue). Not
   blocking for bo_laksana's freeze (grant already live), just close the loop.
3. **Once bo_laksana is FROZEN:** dispatch the DAG chain in ancestor order — bo_bimba/bo_samskara
   expected first per RESOLUTION_L2 v4. Re-verify current contract status on the coordination issue
   before assuming still true. If a contract is missing for the expected-next asset, say so on the
   coordination issue and take the NEXT ready asset rather than stalling.
4. #2450: bookkeeping-only OPEN, structural fix live — no further action unless explicit Conductor
   closure comment appears.
5. #2434, #2467, #2406: CLOSED, no further action. #1770: RULED, fix confirmed LIVE — resolved.

## TRAPS (permanent — cite before every future dispatch)

**Trap 105 (cycle #81, NEW):** submitting a re-verdict (`optimization_verdict_accepted`) for an
asset AFTER an `implementation_accepted` has already been accepted for it silently STRANDS that
implementation binding — `accepted_rebuild_observed` will reject with "must bind the exact current
optimization decision" (HTTP 409, looks like an idempotency conflict but is a real validation
failure) because the implementation's stored `decision_digest` no longer equals
`canonicalNirmanaOptimizationVerdictDigest` of the now-current (most recent) verdict. **Fix:**
recompute the digest fresh against the LATEST `optimization_verdict_accepted` row's
`evidence_payload` (standalone Node script reimplementing `stableJson` +
`NirmanaOptimizationVerdictEvidenceSchema` from `definitions.ts`, run from
`/Users/Dev/nirmana-s/l2/platform` where `zod` resolves — see
`/private/tmp/compute_decision_digest*.{ts,mjs}` for working precedents from earlier sessions, and
`/private/tmp/claude-504/.../scratchpad/compute_bo_laksana_decision_digest.mjs` this cycle's copy)
and resubmit `implementation_accepted` with the SAME `implementation_digest` (submitter-chosen,
never server-recomputed — confirmed by reading `requireImplementationProvenance` in
`definitions.ts`) but the NEW `decision_digest`. This is now the 3rd time this exact "re-verdict
strands prior W3" pattern has appeared for bo_laksana across different digest-staleness episodes —
check for it FIRST (compare implementation_accepted's decision_digest against a fresh
canonicalNirmanaOptimizationVerdictDigest of the CURRENT verdict) before assuming a full W1/W2/W3
re-run is needed, the way STATE #80 assumed.
**Trap 104 (cycle #80):** `gh run view`/`gh api actions/runs/{id}` can hit a secondary rate limit
independent of the primary `core`/`search` limit — fall back to the gcloud revision→digest→
artifact-tag method, don't loop-retry.
**Trap 103 (cycle #79):** a deploy run's `head_sha` field can disagree with the job's actual
`DEPLOY_SHA` — only the job log or pushed docker tag is trustworthy.
**Trap 102/101 (cycles #77-78):** gcloud region flag + IST/UTC timestamp comparison for the
revision→digest→artifact-tag live-commit method.
**Trap 100 (cycle #76):** diff each uncommitted worktree item individually before discarding.
**Trap 99 (cycle #75):** #2470 won the double-open tie-break permanently, confirmed LIVE. #2471
stays CLOSED.
**Trap 98-80(b) (cycles #65-74):** see git history — PR/state verification discipline, evidence
payload field names, entity_type conventions, digest sourcing discipline, worktree hygiene.
**NEW learning (cycle #80):** `integrity_verified` requires `integrity_contract_sha256` +
`result_digest` (computed via `canonicalNirmanaIntegrityContractDigest`, server overwrites
`result_digest`/`detector_observation` regardless of submission). `asset_frozen`'s `lifecycle_digest`
IS checked exactly (replay the server's `stableJson`+SHA-256 over the accepted lifecycle event set).
**NEW learning (cycle #81):** the campaign events table is `nirmana_evidence
.nirmana_elevation_campaign_events` — NOT `public.nirmana_lifecycle_events` or any `public.*event*`
table (there is no such public table; don't waste a query guessing table names, go straight to the
`nirmana_evidence` schema). `asset_provenance_receipts` (public schema) holds `output_digest`/
`output_digest_spec_sha256`/`receipt_state` keyed by `build_id` — read it directly rather than
recomputing. A `build_run_authorized` event's `authorization_sha256` is submitter-chosen (per trap
84 from earlier cycles) — read it from the existing event, never recompute.
See git history of this file for traps 1-99 in full detail.

## STANDING CONSTRAINTS (carried forward, verify each cycle)

- Live deployed commit as of cycle #81: **`04e6c0eeb` (#2470)** confirmed cycle #80 via gcloud
  method; not re-verified independently this cycle (no new deploy-status check was needed — this
  cycle's work was evidence-submission + one DB grant, not deploy-dependent). RE-VERIFY if stale.
- **Lane main worktree (`/Users/Dev/nirmana-s/l2`) is now ON BRANCH
  `l2-bo-laksana-migration-934-signal-identity-grant`** (checked out fresh from `origin/main` this
  cycle specifically to avoid trap 83 — the branch's prior state, `l2-bo-arudha-predispatch-
  contract-926-927` at commit `2f26ca840`, was 26 commits behind `origin/main` but its own content
  had already merged as PR #2469 under a squashed hash, so nothing was lost). **Next cycle: this
  worktree is now current with `origin/main` as of `04e6c0eeb` + migration 934's commit — safe to
  build from directly, or `git fetch && git checkout origin/main` fresh if further behind by then.**
- `nrec` = `bash platform/scripts/nirmana/nrec`; `--as executor` for W1/W2/implementation/rebuild/
  authorization, `--as verifier` for integrity_verified/asset_frozen. Schemas in
  `platform/src/lib/nirmana-elevation/definitions.ts` (`NirmanaLifecycleBindingSchema` and its
  `.extend()`s) and `evidence-command.ts` (envelope/source_kind rules) — read them directly.
- ONE non-terminal build_run per chart (fleet cap 3). **Fleet slot FREE**, confirmed this cycle. No
  build was dispatched this cycle.
- `--definition-revision t1-2026-09-08-be255ffe` always explicit.
- DATABASE_URL export each cycle: `postgresql://amjis_app:50mii04kTKDUUu54CAKdS4Bv2gx1IoWy@localhost:5432/amjis`;
  explicit `timeout 30` on every psql/dispatch invocation. Never `git stash`. No heartbeat branches.
  Never self-certify capsules (executor and verifier must be genuinely separate identities/subagent
  contexts). Prefer FOREGROUND verifier subagents over background ones for this fresh-context-per-
  cycle campaign — a background agent's completion notification may not reach the next cycle's
  fresh session (see cycle #81 step 10's mistake). `gh pr merge <n> --auto` bare flag only.
- Issues ledger: **#2434 CLOSED**; **#2467 CLOSED**; **#1770 RULED, fix LIVE**; **#2450 OPEN**
  (bookkeeping only); **#2447 OPEN**; **#2443 OPEN** (stale); **#2446 OPEN**; **#2415 OPEN**;
  **#2406 CLOSED**.
- PRs: **#2472 OPEN, auto-merge armed** (migration 934, this cycle — grant already applied live
  independent of merge status); #2470/#2469/#2468/#2466/#2464/#2463/#2461/#2460/#2458/#2457/#2454/
  #2453/#2452/#2451 all MERGED+LIVE (older). #2471 CLOSED PERMANENTLY (do not reopen).
- **Frozen under live t1 (`t1-2026-09-08-be255ffe`): bo_nakshatra_semantic, bo_special_lagna,
  bo_vargottama_dhana.** bo_laksana: chain now complete through `accepted_rebuild_observed`
  (22:19:44 this cycle); `integrity_verified`/`asset_frozen` attempted via background verifier,
  OUTCOME UNKNOWN — check DB first thing next cycle (NEXT ACTION #1). The DB-permission blocker
  that caused the FIRST `integrity_verified` attempt to 500 is fixed and confirmed live (migration
  934). bo_arudha/bo_sudarshana frozen under an earlier definition_revision (not re-verified under
  t1 this cycle).
