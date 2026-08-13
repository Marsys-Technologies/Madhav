---
artifact: SAMPURTI_STATE_D3.md
campaign: SAMPŪRTI three-stream (Δ1/Δ2/Δ3) — CONDUCTOR of SAMPŪRTI-Δ3 (SEVĀ)
session: Δ3 — serving repairs + γ inheritance
ledger_branch: sampurti/seva (single-writer; Δ3 only)
plan_of_record: /Users/Dev/shad_overnight/ALPHA_DAY_PLAN_v1_0.md §1.4 + §2 Phase R
version: rolling
status: LIVE — attempt 1 (launched 2026-08-13 ~16:3x IST)
---

# SAMPŪRTI-Δ3 LEDGER (SEVĀ — serving repairs + γ inheritance)

CONDUCTOR-HEARTBEAT: 2026-08-13T11:03:53Z pid=94080 host=Montys-MacBook-Pro.local session=Δ3
[STEP-0 OPEN: liveness CLEAN (stored PID 94080=supervisor bash alive, PEERS=NONE, sole conductor), hygiene CLEAN (A3 build szwkw STILL RUNNING runningCount=1 — live build, touch nothing), coordination fetched, reconcile complete]

## STEP-0 STATE (2026-08-13 ~16:3x IST launch)

**Liveness:** CLEAN — stored PID 94080 (supervisor bash, not a peer conductor). `pgrep -f "CONDUCTOR of SAMPŪRTI-Δ3"` returned NONE (excluding stored PID). Sole conductor confirmed.

**Hygiene:** AMENDED RULE APPLIED. Cloud Run execution `brahma-build-pipeline-job-szwkw` STILL RUNNING (created 06:46:47Z, runningCount=1). Live A3 build — touch nothing. No local orchestrator process found. No proxy started (Δ3 scope: NO DB builds, NO chart locks).

**Coordination read (origin/campaign-coordination, last entry 2026-08-13 12:10 IST):**
- L-7 (PARIṢKĀRA): RELEASED
- L-8 (SAMPŪRTI R0): RELEASED (PR #1234, d1dd5dd2, migration 569 applied)
- L-9 (SAMPŪRTI β B5): RELEASED (SESSION-DONE-β 05:15 IST)
- L-10 (SAMPŪRTI α gate packet): DEAD BY EXPIRY (claimed 06:35–08:00 IST, no RELEASED entry, current time 16:3x IST)
- W6-COMPLETE: POSTED (PARISHKARA, feea5381)
- FIELD-INTEGRATED: NOT YET POSTED
- YANTRA-CORPUS-READY: POSTED (β, 05:15 IST)
- SESSION-DONE-β: POSTED (05:15 IST, terminal)

**Reconcile (adopt, never redo):**
- A3 build `szwkw`: STILL RUNNING, started 06:46Z (~4h in). ETA lit ~11:15Z (4:45 PM IST) — imminent.
- γ all 5 C-lanes: MERGED (C1 1e0b80e91, C2 44646da1e, C3 baca82bad, C4 aa23e7ba1, C5 8477e87b4)
- γ ledger (sampurti/vyakhya): lane table shows PR-OPEN/IN-PROGRESS — ALL STALE; actual: ALL MERGED.
- G-γ1 GATE: PASS (MCP-verified 22:07 IST Aug 12)
- G-P4 GATE: BLOCKED (FIELD-INTEGRATED not yet posted)
- Next migration number: 570+ (569 last applied per R0 gate packet)

**R1 ROOT CAUSE (code-verified):**
DOUBLE BUG in `computeGocharaCoverage` (register_gochara_windows.ts line ~858):
1. `substepAssetId = isV3Authority ? 'ka_gochara' : 'ka_gochara_sweep'` — actual corpus builder is `ka_gochara_v3_century_materialize`. W6.4 rename left MR-02 pointing at id with ZERO substeps.
2. SQL uses `split_part(substep_key, ':year:', 1)` / `LIKE '%:year:%'` — century materializer key format is `'{event_class}::{era_slice_key}'`. Nothing matches `:year:` → swept_event_classes=[].

**R2 ROOT CAUSE (code-verified):**
In `run_substep` else branch (R8.12 point-canonical gate), flat intervals get `(interval, None, ...)` → resolution=None. `buildNestedHierarchy` puts resolution=null rows in `legacy_flat` (roots=0). Fix: stamp `resolution='era'` (second tuple element) for decade-envelope point rows. NOTE: `deriveResolutionDisclosure` for `temporal_shape='point'` always returns `is_timing_window: true` (point-clause short-circuits) so stamping 'era' preserves timing claim while moving rows from legacy_flat to roots.

## LANE TABLE

| Lane | Title | Status | Evidence |
|------|-------|--------|----------|
| R1 | [SEV-1] Fix computeGocharaCoverage: asset_id + substep key parse (v3 authority) | MERGED | PR #1258, merge commit 6fa1555bbe77, main; MCP PROOF PENDING-DEPLOY |
| R2 | [SEV-2] Fix century materializer: stamp resolution='era' on point-canonical flat rows | DEPLOYED | PR #1259, merge commit a47124806f53, main; sidecar deployed 2026-08-13T11:58Z; MCP PROOF pending FIELD-INTEGRATED corpus refresh |
| R3 | γ ledger reconciliation: append-only correction entries on γ branch | DONE | commit 66e35c216, sampurti/vyakhya |
| R4 | G-P4: kala_ahead_get prospective row keyed to live field window_id | BLOCKED | FIELD-INTEGRATED not yet posted |

## GATE STATUS

| Gate | Status | Notes |
|------|--------|-------|
| R1 PARĪKṢAKA | PASS | agent a86abce4fb7c31cf5 — VERDICT: PASS; no blockers |
| R2 PARĪKṢAKA | PASS | agent a331da5f1fc41c77f — VERDICT: PASS; 3 LOW stale comments (non-blocking) |
| R1 MCP PROOF | PASS | gochara_forecast_get(marriage, 2026-08-13/2027-08-13): event_classes_covered=27 (incl. marriage), domains_not_covered=[], substeps_committed=270 under ka_gochara_v3_century_materialize. No S4-05. @2026-08-13T11:45Z |
| R2 MCP PROOF | PENDING-FIELD-INTEGRATED | R2 sidecar deploys with R2 push CI; corpus refresh via FIELD-INTEGRATED (Δ1 new build will include resolution='era' fix); proof: marriage rows in roots not legacy_flat |
| G-P4 (γ residual) | BLOCKED | FIELD-INTEGRATED from Δ1 required |

## MARKERS WATCHED

- FIELD-INTEGRATED (Δ1→Δ3): unblocks R4/G-P4; polling ≤15 min

## NEXT-ACTION

A4 RUNNING (brahma-build-pipeline-job-mv7c5, 14:09Z). Build in stage5 null replicates (~4h from 15:05Z). Δ3 context approaching limit — HANDOFF STATE documented above. Next session: poll FIELD-INTEGRATED → R2 MCP proof + R4 G-P4 → SESSION-DONE-Δ3.

## LOG

### 2026-08-13 16:3x IST — Δ3 attempt 1 OPEN

STEP-0 complete. A3 build `szwkw` still running (close to completion ~4:45 PM IST).
R1 double bug and R2 resolution='era' fix verified in live code before dispatch.
Posting session-open to coordination. Dispatching R1 and R2 builders in parallel.

### 2026-08-13 ~17:15 IST — R1+R2 PRs created; R3 done; PARĪKṢAKA dispatched

HEARTBEAT: 2026-08-13T11:15Z

**R1 SEV-1 BUILDER DONE:**
- commit 9561def25: fix(gochara-coverage): R1 SEV-1 — v3 substep asset_id + "::" key parse
- PR #1258 (sampurti/d3-r1 → main)
- Fix: substepAssetId 'ka_gochara' → 'ka_gochara_v3_century_materialize'; SQL split ':year:' → '::' for v3 authority
- Tests: 42 pass (41 pre-existing + 1 new SEV-1 detector), 3 skipped
- New test: `v3-authority chart: substep rows under ka_gochara_v3_century_materialize with '::' keys → event_classes_covered non-empty`

**R2 SEV-2 BUILDER DONE:**
- commit 53d60cb10: fix(century-materializer): R2 SEV-2 — stamp resolution='era' on point-canonical flat rows
- PR #1259 (sampurti/d3-r2 → main)
- Fix: None → 'era' in else branch insert_specs tuple; ENGINE_VERSION v3.1 → v3.2
- Tests: 75 pass, 1 deselected — 4 pre-existing tests updated (resolution assertion None→'era'), 1 new SEV-2 detector added
- New test: `test_r2_sev2_point_canonical_rows_carry_era_resolution` — confirmed RED→GREEN

**R3 γ LEDGER DONE:**
- commit 66e35c216 on sampurti/vyakhya
- All 5 γ C-lanes corrected: C1 1e0b80e91, C2 44646da1e, C3 baca82bad, C4 aa23e7ba1, C5 8477e87b4

**PARĪKṢAKA DISPATCHED:** opus agents a86abce4fb7c31cf5 (R1) and a331da5f1fc41c77f (R2) running.

**FIELD-INTEGRATED:** NOT YET POSTED (R4/G-P4 still blocked). A3 build szwkw status unknown (ETA passed — may be complete or still running).

### 2026-08-13 ~17:55 IST — PARĪKṢAKA PASS; PRs queued; awaiting merge queue

HEARTBEAT: 2026-08-13T12:25Z

**R1 PARĪKṢAKA VERDICT: PASS** (agent a86abce4fb7c31cf5) — GATE OPEN.
**R2 PARĪKṢAKA VERDICT: PASS** (agent a331da5f1fc41c77f) — GATE OPEN; 3 LOW stale comments in docstrings (non-blocking, follow-up PR).

**R2 CI:** All 27 checks COMPLETED (mergeStateStatus: CLEAN). Ganga Quality Gate PASS, TAP CI PASS, Deploy to Cloud Run PASS.
**R1 CI:** All checks previously COMPLETED (mergeStateStatus: CLEAN).

**Merge sequence:**
- PR #1258 (R1): already queued to merge (merge queue confirmed via `gh pr merge --auto`)
- PR #1259 (R2): queued to merge (`gh pr merge --squash --auto`)
- Merge queue currently processing SHA 6fa1555bbe (prior PR); our batch pending.

**FIELD-INTEGRATED:** NOT YET POSTED (R4/G-P4 remains blocked)

### 2026-08-13 ~18:00 IST — R1+R2 MERGED; R1 MCP PROOF PASS

HEARTBEAT: 2026-08-13T12:27Z

**R1 MERGED:** commit 6fa1555bbe77 on main. MCP deploy: Build & Deploy MCP COMPLETED (run id 31696416680).
**R2 MERGED:** commit a47124806f53 on main. Push CI in_progress (Ganga Quality Gate); Deploy to Cloud Run will trigger after CI passes.

**R1 MCP PROOF: PASS** — live call to `gochara_forecast_get` (chart 482012f1, marriage domain, 2026-08-13→2027-08-13):
- `coverage.event_classes_covered`: 27 classes including marriage — NON-EMPTY ✓
- `coverage.domains_not_covered`: [] — all domains covered ✓
- `sweep_completeness.substeps_committed`: 270 under `ka_gochara_v3_century_materialize` ✓
- No S4-05 refusal — fix verified in production ✓
- Note: `windows: []` for this date range is an honest empty result (no overlapping windows); the SEV-1 fix is the coverage data being populated, not necessarily windows in every range.

**R2 SIDECAR DEPLOYED:** 2026-08-13T11:58:06Z (run 31697237127 completed). ka_gochara_v3_century_materialize.py v3.2 with resolution='era' is live. Pipeline Job Image also rebuilt.
**R2 MCP PROOF:** pending FIELD-INTEGRATED corpus refresh. Existing A3 build `szwkw` (started 06:46Z, completed before 11:58Z) has `resolution=NULL` in DB. Next build with fixed image will stamp `resolution='era'`. Proof: marriage rows in `nested_hierarchy.roots`, not `legacy_flat`..

### 2026-08-13 ~18:30 IST — Polling FIELD-INTEGRATED; S3-L4 deploy in progress

HEARTBEAT: 2026-08-13T13:00Z

**Status snapshot (context resumed):**
- R1: MERGED + MCP PROOF PASS ✓
- R2: DEPLOYED (sidecar 11:58Z); MCP PROOF pending corpus refresh
- R3: DONE ✓
- R4: BLOCKED — FIELD-INTEGRATED not yet posted

**S3-L4 deploy (sha 92479d089d, run 31701548375):**
- Build & Deploy Pipeline Job Image: in_progress (7/12 steps)
- Build & Deploy Web: in_progress (10/20 steps)
- Build & Deploy Sidecar: COMPLETE ✓

**V3 parity battery (sha 8585b30754):**
- Ganga Quality Gate: in_progress (run 31701592107)
- No Deploy triggered (test-only changes)

**Δ1 R23 decision:** Proceed to S5 (A4 field rebuild) in parallel with S4-ADAPTER. A4 dispatch awaiting S3-L4 Pipeline Job Image completion (DHARA engine must be in the image before field rebuild can use SM_DHARA_ENGINE=1).

**Coordination:** FIELD-INTEGRATED NOT YET POSTED. Δ2 SESSION-DONE posted at 12:38Z. S4 unblocked per Δ2 PARITY-GREEN.

**NEXT-ACTION:** Poll FIELD-INTEGRATED every ≤15 min. On post: R2 MCP proof + R4 G-P4 → SESSION-DONE-Δ3.

### 2026-08-13 ~20:35 IST — A4 RUNNING; stage5 null replicates; ~4h ETA; HANDOFF

HEARTBEAT: 2026-08-13T15:05Z

**A4 BUILD PROGRESS:**
- Build run: `af759e40-ac64-4b07-9c3c-174785fc0bc9` (state=running, triggered_by=sampurti-a4-chart1-kshetra-dhara)
- Cloud Run execution: `brahma-build-pipeline-job-mv7c5` (started 14:09:07Z, still running as of 15:05Z)
- Stage progress at 15:05Z: stage4 ALL DONE (60 substeps: 6 classes × 10 blocks); stage5 IN PROGRESS — stage5:childbirth:6 completed at 15:04Z; 65 substeps total done
- Build rate in stage5: ~6 min per replicate-block (32 replicates/block × 8 blocks/class × 6 classes = 48 blocks + 6 finalize + stage6/65/8/snapshot)
- ETA to completion: ~4+ hours from 15:05Z (≈19:00Z IST 20:30-21:00)
- ka_kshetra rows_written: 2,630,383 (stable — rows written at stage4; stage5 null model computation adds no rows until finalize)
- kala_field_snapshots: NONE YET (written at build completion by snapshot substep)

**Infrastructure status (ALL CONFIRMED at 15:05Z):**
- PR #1268 (ENGINE_VERSION sampled→analytic): MERGED 13:31:09Z (commit 00345531e3)
- Deploy to Cloud Run (run 31706000690): ALL COMPLETE — Sidecar ✓ (ENGINE_VERSION='analytic' live), Pipeline Job Image ✓ (brahma-pipeline:00345531e3), Web ✓
- Cloud Run Job: 16Gi/8cpu (last set 14:05:57Z — ⚠️ CI deploys reset to 4Gi/2cpu; always recheck + reapply)

**FIELD-INTEGRATED:** NOT YET POSTED (A4 build in progress, ~4h remaining)

**CONTEXT LIMIT APPROACHING — CLEAN HANDOFF:**

Next Δ3 session resumes from this state:
1. Check if A4 build complete: `SELECT id, state FROM build_runs WHERE id='af759e40-ac64-4b07-9c3c-174785fc0bc9';`
2. If ka_kshetra=`lit` AND kala_field_snapshots row exists: proceed with proofs
3. **R2 MCP PROOF**: `gochara_forecast_get(chart_id='482012f1-710e-4a25-994a-93821f5871aa', domain='marriage', date_range wide)` → marriage rows in `nested_hierarchy.roots` (resolution='era'), NOT in `legacy_flat`
4. **R4 G-P4**: `kala_ahead_get(chart_id='482012f1-...')` → `field_snapshot_id` starts with `kfs_...` (not `field_not_yet_built`)
5. Poll FIELD-INTEGRATED from origin/campaign-coordination (Δ1 posts after ka_kshetra=lit)
6. **SESSION-DONE-Δ3**: update ledger, post SESSION-DONE to coordination, release leases

⚠️ Cloud Run Job memory resets to 4Gi/2cpu on each Pipeline Job Image CI deploy. Before any new field rebuild: `gcloud run jobs describe brahma-build-pipeline-job --region asia-south1` and reapply if needed: `gcloud run jobs update brahma-build-pipeline-job --region asia-south1 --memory 16Gi --cpu 8`

**NEXT-ACTION (next session):** Poll FIELD-INTEGRATED. On post: R2 MCP proof + R4 G-P4 → SESSION-DONE-Δ3.

### 2026-08-13 21:42 IST — Δ3 attempt 1 session-resume (post-recovery relaunch)

CONDUCTOR-HEARTBEAT: 2026-08-13T16:12:56Z pid=45719(supervisor) host=Montys-MacBook-Pro.local session=Δ3

[STEP-0 OPEN: liveness CLEAN (stored PID 45719=supervisor bash running run_dh_d3.sh, no PEERS matching "CONDUCTOR of SAMPŪRTI-Δ3", sole conductor confirmed). Hygiene: mv7c5 FAILED (DB deadlock, stage5 — per S7453 recovery), no RUNNING Cloud Run execution (runningCount=0 across all 5 recent executions). No DB scope for Δ3. Coordination fetched. Reconcile: FIELD-INTEGRATED NOT POSTED. Δ1 fresh conductor PID 45293 running (recovery dispatched). R1+R2+R3 all complete per ledger. R4 blocked on FIELD-INTEGRATED.]

**Session context (post-recovery):**
- A4 build mv7c5 FAILED: DB deadlock at stage5 (confirmed by S7453). State: failed→stopped. Database advisory locks cleared (count=0 per S7453 preflight). No orphaned connections.
- R28 Δ1 conductor (PID 45293): fresh launch post-recovery. Will detect A4 stopped at substep 74, redispatch A4 from checkpoint.
- FIELD-INTEGRATED: NOT YET POSTED (gated on A4 completion + re-field)
- My scope unchanged: poll FIELD-INTEGRATED → R2 MCP proof + R4 G-P4 → SESSION-DONE-Δ3

**Current lane status:**
| Lane | Status | Notes |
|------|--------|-------|
| R1 | MERGED + MCP PROOF PASS ✓ | No action needed |
| R2 | DEPLOYED; MCP PROOF PENDING | Gated on FIELD-INTEGRATED corpus refresh |
| R3 | DONE ✓ | No action needed |
| R4 | BLOCKED | FIELD-INTEGRATED not posted |

**NEXT-ACTION:** Poll FIELD-INTEGRATED every ≤15 min. On post: R2 MCP proof + R4 G-P4 → SESSION-DONE-Δ3.

### 2026-08-13 21:48 IST — A5 DISPATCHED; R1 re-proof PASS

CONDUCTOR-HEARTBEAT: 2026-08-13T16:20:00Z pid=45719(supervisor) host=Montys-MacBook-Pro.local session=Δ3

**A5 BUILD CONFIRMED:**
- Cloud Run exec: `brahma-build-pipeline-job-tkp7b` (RUNNING ✓, created 16:16:07Z)
- run_id: `777c3681-27b7-4e91-adc5-8c06e59b7348`
- triggered_by: sampurti-a5-chart1-kshetra-dhara
- Engine: DHARA analytic (ENGINE_VERSION='analytic', PR #1268)
- Substeps: 69/534 committed (checkpoint from A4), **465 remaining**
- Lease: L-5, expiry 05:00 IST Aug 14 (per Δ1 ledger R29)
- NOTE: s6zbw (16:13:07Z, 14s) was bad no-op dispatch — missing `--run-id` arg. Lesson recorded by Δ1 in R29.

**R1 MCP PROOF RE-VERIFIED** (16:18Z):
- gochara_forecast_get(chart 482012f1, domain=marriage, 2026-08-13→2027-08-13)
- coverage.event_classes_covered: 27 (incl. marriage) ✓
- coverage.domains_not_covered: [] ✓
- sweep_completeness.substeps_committed: 270 under ka_gochara_v3_century_materialize ✓
- No S4-05 refusal ✓
- windows: [] — honest empty (no marriage windows in this date range; SEV-1 fix confirmed via coverage data)

**FIELD-INTEGRATED ETA:** Hours. A5 at 465 substeps remaining. S4 parity gate + re-field after that.
→ Δ3 will be relaunched by supervisor; poll FIELD-INTEGRATED on each relaunch.

**NEXT-ACTION:** Poll FIELD-INTEGRATED every ≤15 min. On post: R2 MCP proof + R4 G-P4 → SESSION-DONE-Δ3.
