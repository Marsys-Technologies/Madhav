# PROGRAM_STATE — Platform Modernization (single re-kick pointer)

> Read THIS at every re-kick. It replaces the heavy session-open reads (lean-transform governance).
> Conductor updates it at every batch stop. Authoritative for "where are we now."

## Snapshot
- **Status:** RUNNING — Batch 4 CLOSED; 21/20 program units (the original 20 + 2 hygiene units; 105% counting hygiene); 8/8 hard gates GREEN (G5b set this batch).
- **Current batch:** Batch 4 closed at sub-agent count = 4 (hygiene.test_chart_id, hygiene.flag_cleanup, 3.cutover, 3.legacy_delete). G5b_onfinish GREEN. Legacy synthesis trio deleted. Pipeline-selector flag retired.
- **Tracker:** LIVE at `http://localhost:8787` (PID logged in `/tmp/madhav-tracker.log`).
- **main HEAD:** `aa7aaca2` (3.legacy_delete 3/3 collapse pipeline-selector flag).
- **Last green per stream:** A=`3.legacy_delete` (`aa7aaca2` chain 934085a2→9f677e15→aa7aaca2) · B=`hygiene.flag_cleanup` (`7648d3ba`) · C=`hygiene.test_chart_id` (`195f4cac`).
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

## Eligible-now / queued (Batch 5 — staged scaffolding completion + operator window)
- **Next refactor wave** — move `QueryPipeline.run()` bodies out of `route.ts` into `pipelines/{single_pass,agentic}/` and delete the deprecated `isPipelineSelectorEnabled()` shim. Brief not yet authored.
- **4.scale_and_close** — wave 4 close-out (queue marks `status: not_yet_detailed`).

## What to ship to the native at re-kick
1. **Native review of depth-selector default** (3.tier_excision shipped TierPicker removal with planner-auto-by-query-class). Still pending from Batch 3.
2. **Apply migrations 081–090 to staging DB** — now eligible (3.cutover + 3.legacy_delete shipped + held green). Migration 090 (drop `mcp_api_keys.audience_tier`) is the only irreversible op — run after a green post-cutover smoke window.
3. **Cloud Run env-var cleanup** — `gcloud run services update amjis-web --remove-env-vars MARSYS_FLAG_PIPELINE_SELECTOR,MARSYS_FLAG_LL3_PANCHA_MP_CLUSTER_MODIFIER_ENABLED` (both env-vars already removed from `deploy.yml` bakes; this is the merge-side cleanup).
4. **Next refactor wave brief** (Cowork authoring): move pipeline.run() bodies out of route.ts; delete the deprecated `isPipelineSelectorEnabled()` shim and any remaining single_model_strategy docstring/comment references that are stale post-deletion.
5. (Carried) **Rotate `amjis-db-password`**.

## Re-kick protocol
1. Open a fresh Conductor chat at repo root on `main`.
2. Paste: "Continue the Platform Modernization program. Read PROGRAM_STATE.md + session_queue.yaml + CONDUCTOR_HALT_LOG.md; resume from the next eligible units."
3. Conductor reconciles gate board, picks eligible units across streams A/B/C, runs to the next batch stop, updates this file.

## Safety reminders (automated, no human)
- Every prod op: pre-flight green + post-deploy smoke + auto-rollback on failure.
- DB: additive + staging→live swap; no destructive in-place; column drops only after a green post-cutover window.
- New flags default OFF (reversible). Kill-switch: error-rate spike → halt_queue + rollback last cherry-pick.
