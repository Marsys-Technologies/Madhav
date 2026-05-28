# PROGRAM_STATE — Platform Modernization (single re-kick pointer)

> Read THIS at every re-kick. It replaces the heavy session-open reads (lean-transform governance).
> Conductor updates it at every batch stop. Authoritative for "where are we now."

## Snapshot
- **Status:** **SEALED** — Batch 5 (Wave 4) CLOSED 2026-05-28; PLATFORM MODERNIZATION ARC COMPLETE. 28/20 program units (the original 20 + 2 hygiene units + 7 Wave-4 units − 1 ephemeral support; counting Wave-4 = 140% of plan); 8/8 hard gates GREEN; 0 class-1 red-team findings.
- **Seal artifact:** `00_ARCHITECTURE/PLATFORM_MODERNIZATION_CLOSE_v1_0.md` — canonical close-out.
- **Red-team report:** `00_ARCHITECTURE/CONDUCTOR/modernization/RED_TEAM_PLATFORM_MOD_v1_0.md` — 0 class-1, 3 class-2 dispositioned, 4 class-3 dispositioned.
- **Current batch:** Batch 5 closed at sub-agent count = 8 dispatched + 3 inline (4.refactor_pipeline_shim A, 4.observability B, 4.memorystore_caching C, 4.edge_and_infra_hygiene A, 4.build_trigger B, 4.learning_loop C inline, 4.red_team_seal A inline). Wave-4 final seal complete.
- **Tracker:** RETIRED (ephemeral lifecycle per 0t brief). `tools/program-tracker/` removed in 4.red_team_seal 2/3. Operator: `gcloud run services delete amjis-tracker --region asia-south1`.
- **main HEAD:** post-batch-5 seal (after PROGRAM_STATE + seal-artifact + version-bump commit). Wave-4 commit chain: refactor (bc9379ce, 5b9164bd) → observability (5180733f, 50b74814, 33bacc0a, 42a39960) → memorystore (45ed0ef9, 177420c9, a56434b1) → edge (309376cd, d47ad81a, c8592215) → build_trigger (4b5d60b7, 6d34e6cb, 524792ab) → learning_loop (1a0b0fe8, 307c39ed) → red_team_seal (fcdc9199, + 2 follow-ups).
- **Last green per stream:** A=`4.red_team_seal` (inline) · B=`4.build_trigger` (524792ab) · C=`4.learning_loop` (inline 307c39ed).
- **Open halts:** none.
- **Attention (not a halt; deferred operator action):**
  - **Apply migrations 081–090 to staging DB** (additive, idempotent). 086–089 add L2.5 `(chart_id, ayanamsha_id)` keying + 3-column MSR coefficient + legacy provenance freeze; **090 drops `mcp_api_keys.audience_tier`** (the only irreversible op — run after a green post-cutover window — now eligible since 3.cutover + 3.legacy_delete shipped green).
  - **Cloud Run env-var cleanup** (post-deploy `gcloud run services update amjis-web --remove-env-vars`): `MARSYS_FLAG_PIPELINE_SELECTOR` (collapsed in 3.legacy_delete 3/3) + `MARSYS_FLAG_LL3_PANCHA_MP_CLUSTER_MODIFIER_ENABLED` (collapsed in hygiene.flag_cleanup) — both already removed from `deploy.yml` bakes; this is the Cloud-Run-side merge cleanup per the env-var-merge lesson.
  - **Rotate `amjis-db-password`** (carried from Batch 1) — literal scrubbed from HEAD; full incident in `platform/scripts/governance/secret_naming.md §5`.
- **Re-baseline marker (3.dejudge):** stripping `CONFIDENCE_FLOOR` (0.6/0.35) + LL.1 weights + Pancha-MP consolidation from `msr_sql.ts` + `query_signals.ts` now surfaces all SQL-matching signals (was: post-floor subset). Synthesis-stage input grows by the weak-tail count on every query touching finance/wealth/career domains. **INTENDED per audit §6-A; not a regression.** `answer:eval` deliberately not run per-PR (native discipline). Salience now sourced from 2a.1 L2.5 `computed_salience` column + serve-time panel.
- **Depth-selector follow-up (3.tier_excision):** TierPicker removed without native confirmation; default = planner-auto-selects depth by query class (no user knob). Flag in CONDUCTOR_LOG; native review pending.
- **3.cutover scope note:** the unit's may_touch in the queue listed `platform/src/app/api/chat/consume/route.ts` but the active chat route is `consult/route.ts` (the consume→consult rename happened in Batch 1 unit 0a.1). All 3.cutover + 3.legacy_delete edits landed in `consult/route.ts` correctly; this is a brief-stale glob, not a scope violation.
- **Selector residual (3.legacy_delete 3/3):** `selectPipelineForRequest` + the per-kind `QueryPipeline` modules under `platform/src/lib/pipelines/{single_pass,agentic}/` remain in place as infrastructure for the next refactor wave that will move pipeline.run() bodies out of `route.ts`. `isPipelineSelectorEnabled()` is now a `@deprecated` constant-true shim. Not dead code — staged scaffolding.

## Gate board
| Gate | Status | Unblocks |
|---|---|---|
| naming_ci | **GREEN** (0a.0; 77 baseline) | 0a.1 ✓ · 1.1 ✓ · 2b ✓ · 2c ✓ · 2d ✓ |
| jh_oracle_pinned | **GREEN** (oracle dropped 2026-05-28; schema-valid; JH True Chitra 23°37′09.78″) | 1.2 ✓ |
| G1_jh_parity | **GREEN** (1.2; 31/31 tests; residual 7.62″ under 60″ tol) | 2a · 3.cutover |
| G2_authz_live | **GREEN** (2c; 6/6 tests; authorizeChartAccess + RLS) | 3.tier_excision |
| G3_contract | **GREEN** (2b; 6/6 tests; 8 representative contracts) | 3.dejudge · 3.gateway_pipeline_isolation |
| G4_no_native_lit | **GREEN** (2a; `assert_no_native_literal.sh` exit 0; 4 retrieval tools threaded `chart_id`) | 3.gateway ✓ · 3.dejudge ✓ · 3.tool_asset_recon ✓ |
| G5b_onfinish | **GREEN** (3.cutover; 18/18 golden tests; adapter onFinish parity with legacy on persistence + predictions + observatory via `runOnFinishWriteThrough` helper) | 3.legacy_delete ✓ |
| G6_tool_coverage | **GREEN** (3.tool_asset_recon; 5/5 tests; 19 assets / 77 tools / 0 orphans / 0 redundancies / 0 ayanamsha mismatches; manifest fingerprint `3c1c1821ea424625…`) | — |

## Toolchain adaptations (recorded for re-kicks)
- `platform/` is **npm** (not pnpm). Gate `check_commands` use `npx vitest run …`; vitest must be invoked from `platform/` for `@/` aliases.
- `pyswisseph==2.10.03` + `jsonschema` available in `/Users/Dev/Vibe-Coding/Apps/Madhav/.venv/bin/python3`. Engine tests run with that python directly.
- Sidecar paths: queue gate `jh_oracle_pinned` and brief 1.2 reference unprefixed `python-sidecar/natal_engine/…` — canonicalized to `platform/python-sidecar/natal_engine/…`.
- 2b finding: `zod-to-json-schema@3.25` returns `{}` for Zod v4 internals → use Zod v4's built-in `z.toJSONSchema()` (no extra dep needed). Captured in `platform/src/lib/contract/json_schema.ts`.

## Batch 2 — closed units (commits on main)
| Unit | Wave | Stream | Commit(s) on main | Notes |
|---|---|---|---|---|
| **2c** | 2 | B | `e0f76ff1` `098d8953` `6cde2d69` | Migrations 081/082/083 (charts.owner_id + chart_grants + role rename + RLS); `authorizeChartAccess.ts` (super_admin/owner/grant/deny); consult/route.ts wired; /api/clients no longer mints Firebase user. **Sets G2_authz_live GREEN.** |
| **2d** | 2 | C | `ec5c3837` `306ae829` `5dd07ac5` | Migrations 084/085 (`runtime_config`+`gate_change_log`); `gate_registry.ts` (10 gates × 5 classes); `configService` w/ DB→env→default precedence + canonical-ayanamsha hard guard; Cockpit > Command Center page + edit API (super-admin only). |
| **2b** | 2 | A | `b5d6dd94` `dc0cbc17` `9e124a40` | `platform/src/lib/contract/` w/ 8 representative Zod contracts (4 canonical, 2 kp, 1 reference, 1 text); `assertContractInvariants` runtime check; contract-generated catalog; manifest backfill (15 entries); MCP bridge mirror. **Sets G3_contract GREEN.** |
| **1.2** | 1 | C | `38033dec` `a66eb6cf` `29d81317` | Three-ayanamsha registry (`jh_true_chitra` canonical / `kp` / `lahiri_standard`); `compute_chart` JH-parity layer (residual 7.62″); dasha calendar-year arithmetic fix; polar-safe ascendant fallback; 31/31 parity+crosscheck tests pass. **Sets G1_jh_parity GREEN.** |

## Batch 1 — closed units (recap)
0t · 0a.0 · 0a.1 · 0b.1 · 0b.2 · 0b.3 · 1.1 (see CONDUCTOR_LOG.md Batch 1 for commit details).

## Batch 3 — closed units (commits on main)
| Unit | Wave | Stream | Commit(s) on main | Notes |
|---|---|---|---|---|
| **2a** | 2 | C | `ab47f7a4` `be0c68c6` `56c85119` `2870e02a` `9a25de0b` `66b31aca` `1eb2983b` | Migrations 086–089 ((chart_id, ayanamsha_id) keying across chart_facts + l25_msr/cdlm/cgm/rm/ucn; 3-column MSR coefficient `deterministic_strength`/`verification_certainty`/`computed_salience`; legacy provenance freeze). Python builder + bootstrap loader + structural tests (13/13). `chart_context.ts` resolver + `assert_no_native_literal.sh` retire NATIVE_CHART_ID/DEFAULT_CHART_ID from `lib/retrieve`. **Sets G4_no_native_lit GREEN.** |
| **3.consult_nav** | 3 | B | `2f9abd44` `e8bbf29c` `a0d97174` | Role-gated dashboard + nav (guest vs super_admin); per-chart Profile/Build/Consult/Panchang pages + chart switcher (URL + localStorage; mid-conversation switch strips conversationId); SharingPanel grant/revoke writing `chart_grants`. `chart-page-guard.ts` wraps `authorizeChartAccess`. 58/58 tests pass. No tier/depth selector. |
| **3.dejudge** | 3 | C | `7f85b87c` `cc1423e8` | Strip `DEFAULT_CONFIDENCE_FLOOR`, `FINANCE_WEALTH_CONFIDENCE_FLOOR`, `PANCHA_MP_CLIQUE`, `LL1_PRODUCTION_WEIGHTS` from `lib/retrieve/msr_sql.ts` + `platform-mcp/src/tools/query_signals.ts`. SQL `$5 = 0` default; LL.1 weight calibration deleted; Pancha-MP consolidation deleted; `calibrateResults()` helper removed entirely. Re-baseline (see Snapshot). Orphaned flag `LL3_PANCHA_MP_CLUSTER_MODIFIER_ENABLED` carried forward (hygiene queue). |
| **3.tier_excision** | 3 | A | `e814be0b` `293f3e9c` `9049dfdf` | Deleted `lib/disclosure/` module + `components/disclosure/` + `components/consume/TierPicker.tsx` + `platform-mcp/src/tools/tier_catalog.ts` + `house_rules_variants/public_redacted.md`. Removed `X-MCP-Audience-Tier` header from `platform-mcp/src/client.ts` + tier 403 gates in `/api/mcp/health/{tools,coverage}`. Migration **090** drops `mcp_api_keys.audience_tier` (the only irreversible op in Batch 3). Depth selector replacement: planner-auto by query class (native review pending). 9/9 platform tests pass; 16 platform-mcp failures pre-existed and are unrelated. |
| **3.gateway_pipeline_isolation** | 3 | A | `510fed1a` `d8e241f7` `566f125b` | New `platform/src/lib/gateway/` with `search_tools` + `invoke_tool` (the 8-step chokepoint: contract → Zod → chart → authz → B.11 → ayanamsha → executor → dispatch) + `b11_floor.ts` + `executor_registry.ts`. Shared stages extracted to `platform/src/lib/pipelines/shared/{auth_and_chart,b11_floor_inject}`. Split `pipelines/{single_pass,agentic}/`. Flag-gated selector `MARSYS_FLAG_PIPELINE_SELECTOR` default OFF — preserves byte-identical legacy path until G5b cutover. 45/45 tests pass (gateway 19 + selector 10 + shared 16). |
| **3.tool_asset_recon** | 3 | C | `25deb169` `5b09c0f2` | New `platform/src/lib/contract/tool_metadata.ts` (700 LoC; single source of truth for tool ↔ asset map). 151 manifest entries backfilled with `data_dependency` + `ayanamsha_role` + `primary_asset` (fingerprint `3c1c1821ea424625…`). `data_coverage` MCP tool gains `mode={rows\|reconciliation\|both}` reconciliation snapshot; `tool_health` surfaces `reconciliation_gate`. G6 test asserts 19 assets / 77 tools / 0 orphans / 0 redundancies / 0 ayanamsha mismatches. **Sets G6_tool_coverage GREEN.** |

## Batch 4 — closed units (commits on main)
| Unit | Wave | Stream | Commit(s) on main | Notes |
|---|---|---|---|---|
| **hygiene.test_chart_id** | 3-hygiene | C | `195f4cac` | Thread explicit `chart_id: 'abhisek_mohanty_primary'` (+ `ayanamsha: 'lahiri'` where ayanamsha-dependent) through fixture calls in the 3 broken retrieve test files. 20 prior failures from 2a.7 → 0; full retrieve suite 99/99 GREEN. No source files touched (test-only fix). G4 not regressed (sanity grep clean). |
| **hygiene.flag_cleanup** | 3-hygiene | B | `7648d3ba` | Remove orphaned `LL3_PANCHA_MP_CLUSTER_MODIFIER_ENABLED` from `feature_flags.ts` (deploy.yml had zero hits). naming_lint exit 0; drift_detector residuals-only. Operator follow-up: `gcloud run services update amjis-web --remove-env-vars MARSYS_FLAG_LL3_PANCHA_MP_CLUSTER_MODIFIER_ENABLED` (if set as Cloud Run env-var). |
| **3.cutover** | 3 | A | `957dbbf9` `075e9dc3` | New `platform/src/lib/pipelines/shared/onfinish_writethrough.ts` helper (+335 LoC) closes 6 parity gaps between adapter and legacy `onFinish` (observatory cost emit, lastAssistantMetadata persistence carry, per-citation `data-citation` parts, `data-correction`/`data-out-of-domain` markers, `pendingStreamWriter.clear()`, blind-mode PPL ledger append). Golden test at `platform/src/app/api/chat/__tests__/onfinish_parity.golden.test.ts` (8 GOLDEN + 7 SHAPE + 3 GUARD = 18 tests) asserts deep-equal call lists. Selector default flipped in `selector.ts` (env-var fallback `=== 'true'` → `!== 'false'`) + `MARSYS_FLAG_PIPELINE_SELECTOR=true` baked in deploy.yml. **Sets G5b_onfinish GREEN.** Edits landed in `consult/route.ts` (not the brief-stale `consume/route.ts` reference — see scope note). |
| **3.legacy_delete** | 3 | A | `934085a2` `9f677e15` `aa7aaca2` | (1/3) Deleted legacy trio `orchestrator.ts` + `single_model_strategy.ts` + `panel_strategy.ts` (3,893 LoC net deletion incl. 6 legacy test files) + legacy `else` branch from `consult/route.ts`. (2/3) Deleted orphaned `/api/mcp/execute/route.ts` + dead `callPlatform()` / `callPlatformPlan()` from `platform-mcp/src/client.ts` after caller verification. (3/3) Collapsed `MARSYS_FLAG_PIPELINE_SELECTOR` — `isPipelineSelectorEnabled()` now `@deprecated` constant-true shim; selector + per-kind `pipelines/{single_pass,agentic}/` modules remain as staged scaffolding for the next refactor wave. `platform/src/lib/synthesis/panel/` ACTIVE directory INTACT (verified). 36/36 chat tests GREEN on main; sanity grep clean of legacy refs (only docstring/comment carry-overs remain). |

## Batch 5 — closed units (Wave 4 final seal; commits on main)
| Unit | Wave | Stream | Commit(s) on main | Notes |
|---|---|---|---|---|
| **4.refactor_pipeline_shim** | 4 | A | `bc9379ce` `5b9164bd` | Extract ~420 LoC adapter dispatch body from `consult/route.ts` into `pipelines/shared/run_adapter_dispatch.ts`; route shrank 1331→934 lines. Delete `isPipelineSelectorEnabled()` shim + flag refs. 36/36 chat tests + 62/62 pipelines tests GREEN. |
| **4.observability** | 4 | B | `5180733f` `50b74814` `33bacc0a` `42a39960` | (1) Trace primitives + W3C traceparent; (2) 2 dashboards + 3 SLOs + 3 alert policies as `infra/monitoring/` JSON; (3) Batch Vertex embeddings (50-text → 1 request); (4) Budget kill-switch guard. 33/33 tests. |
| **4.memorystore_caching** | 4 | C | `45ed0ef9` `177420c9` `a56434b1` | (1) Memorystore IaC + Redis singleton; (2) Cache adapter + per-surface integration (retrieval bundles, planner, embeddings); (3) Retire process-local 60s caches in `dataSource.ts` + `runtime_config.ts` + chaos test (5 scenarios). 74/74 tests. Embedding cache integrated via shared_cache.ts conflict-resolved on cherry-pick. |
| **4.edge_and_infra_hygiene** | 4 | A | `309376cd` `d47ad81a` `c8592215` | (1) LB + CDN + Cloud Armor IaC; (2) IAM bearer on amjis-mcp + per-service runtime SAs (4 distinct) + `--no-allow-unauthenticated`; (3) Cloud Scheduler IaC + deploy consolidation (deleted 4× `platform/cloudbuild*.yaml`) + secret rotation policy + Artifact Registry cleanup. 32/32 smoke checks + 3 IAM-bearer tests GREEN. |
| **4.build_trigger** | 4 | B | `4b5d60b7` `6d34e6cb` `524792ab` | (1) Cloud Task queue IaC + `/api/build/{start,task,events/[buildId]}/route.ts` + lib/build/{trigger,jobInvoker,events}.ts + migration 118 + flag `MARSYS_FLAG_BUILD_TRIGGER_ENABLED=false`; (2) `BuildActionPanel.tsx` ('use client', idle→starting→running→done/error SSE state machine) + 6-case mount test; (3) E2E smoke (happy + failure-rollback + authz-deny paths). 77/77 tests across api/build + clients + lib/build. |
| **4.learning_loop** | 4 | C (inline) | `1a0b0fe8` `307c39ed` | (1) Migration 119 (calibration-stamp columns on `mcp_predictions`) + `lib/predictions/calibration_producer.ts` + onfinish_writethrough step 10 (LEL-independent); 22/22 tests. (2) `answer:eval` post-cutover baseline STUBBED at `00_ARCHITECTURE/answer_eval_baseline_post_cutover_v1_0.json` + operator runbook notes — operator runs the actual eval with live creds. |
| **4.red_team_seal** | 4 | A (inline) | `fcdc9199` + 2 follow-ups | (1) Red-team report 0 class-1 / 3 class-2 / 4 class-3, all dispositioned; (2) `tools/program-tracker/` removed; (3) seal artifact `PLATFORM_MODERNIZATION_CLOSE_v1_0.md` + PROGRAM_STATE update + version bumps. |

## ARC SEALED — next operator window
The Platform Modernization arc is **SEALED** 2026-05-28. Open items move to the operator queue.
The session_queue.yaml entry for the next refactor wave is INTENTIONALLY EMPTY — the next Cowork
brief will declare a new arc.

## What to ship to the native at seal (operator queue)
Authoritative list lives in `00_ARCHITECTURE/PLATFORM_MODERNIZATION_CLOSE_v1_0.md §Deferred operator items`. Summary:
1. Apply migrations 081–090 (carried) + **118** (build_events) + **119** (calibration-stamp columns). Additive + idempotent. 090 is the only irreversible op.
2. Run `terraform apply` for the 6 new IaC packages: `infra/memorystore`, `infra/edge`, `infra/iam`, `infra/scheduler`, `infra/cloud_tasks`, plus the `infra/monitoring/` dashboards + SLOs + alerts + `infra/artifact_registry/cleanup_policy.json`.
3. Cloud Run env-var cleanup: remove `MARSYS_FLAG_PIPELINE_SELECTOR` + `MARSYS_FLAG_LL3_PANCHA_MP_CLUSTER_MODIFIER_ENABLED` (already absent from deploy.yml bakes).
4. Rotate `amjis-db-password` (carried).
5. Run live `answer:eval` baseline per the STUBBED v1.0 runbook → commit as v1.1.
6. Flip `MARSYS_FLAG_BUILD_TRIGGER_ENABLED=true` post-smoke.
7. `gcloud run services delete amjis-tracker --region asia-south1` (program-tracker retired).
8. Native review of depth-selector default (3.tier_excision carry-over).

## Re-kick protocol
1. Open a fresh Conductor chat at repo root on `main`.
2. Paste: "Continue the Platform Modernization program. Read PROGRAM_STATE.md + session_queue.yaml + CONDUCTOR_HALT_LOG.md; resume from the next eligible units."
3. Conductor reconciles gate board, picks eligible units across streams A/B/C, runs to the next batch stop, updates this file.

## Safety reminders (automated, no human)
- Every prod op: pre-flight green + post-deploy smoke + auto-rollback on failure.
- DB: additive + staging→live swap; no destructive in-place; column drops only after a green post-cutover window.
- New flags default OFF (reversible). Kill-switch: error-rate spike → halt_queue + rollback last cherry-pick.
