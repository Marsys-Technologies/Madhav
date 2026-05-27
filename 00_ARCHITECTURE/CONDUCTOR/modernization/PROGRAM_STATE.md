# PROGRAM_STATE — Platform Modernization (single re-kick pointer)

> Read THIS at every re-kick. It replaces the heavy session-open reads (lean-transform governance).
> Conductor updates it at every batch stop. Authoritative for "where are we now."

## Snapshot
- **Status:** RUNNING — Batch 3 in flight; 13/20 units green (65%); 6/8 gates GREEN.
- **Current batch:** Batch 3 — 2a + 3.consult_nav landed on main; 3.tier_excision (A) + 3.dejudge (C) in flight; 3.gateway (A) + 3.tool_asset_recon (C) queued behind serialization fence.
- **Tracker:** LIVE at `http://localhost:8787` (PID logged in `/tmp/madhav-tracker.log`).
- **main HEAD:** `a0d97174` (3.consult_nav 3/3 sharing UI).
- **Last green per stream:** A=`2b` (`9e124a40`) · B=`3.consult_nav` (`a0d97174`) · C=`2a` (`1eb2983b`).
- **Open halts:** none.
- **Attention (not a halt; deferred operator action):**
  - **Apply migrations 081–089 to staging DB** (additive, idempotent) — adds 086–089 (L2.5 (chart_id, ayanamsha_id) keying + 3-column MSR coefficient + legacy-corpus provenance freeze). No destructive ops; the legacy rows stay live under partial unique indexes.
  - **Rotate `amjis-db-password`** (carried from Batch 1) — literal scrubbed from HEAD; full incident in `platform/scripts/governance/secret_naming.md §5`.

## Gate board
| Gate | Status | Unblocks |
|---|---|---|
| naming_ci | **GREEN** (0a.0; 77 baseline) | 0a.1 ✓ · 1.1 ✓ · 2b ✓ · 2c ✓ · 2d ✓ |
| jh_oracle_pinned | **GREEN** (oracle dropped 2026-05-28; schema-valid; JH True Chitra 23°37′09.78″) | 1.2 ✓ |
| G1_jh_parity | **GREEN** (1.2; 31/31 tests; residual 7.62″ under 60″ tol) | 2a · 3.cutover |
| G2_authz_live | **GREEN** (2c; 6/6 tests; authorizeChartAccess + RLS) | 3.tier_excision |
| G3_contract | **GREEN** (2b; 6/6 tests; 8 representative contracts) | 3.dejudge · 3.gateway_pipeline_isolation |
| G4_no_native_lit | **GREEN** (2a; `assert_no_native_literal.sh` exit 0; 4 retrieval tools threaded `chart_id`) | 3.gateway · 3.dejudge · 3.tool_asset_recon |
| G5b_onfinish | PENDING — 0b.1 contributes (citation-gate-on-adapter half done); full set in cutover | 3.legacy_delete |
| G6_tool_coverage | PENDING (set by 3.tool_asset_recon) | — |

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

## Batch 3 — closed units so far (commits on main)
| Unit | Wave | Stream | Commit(s) on main | Notes |
|---|---|---|---|---|
| **2a** | 2 | C | `e044b361` `ca59e74d` `0fa6e367` `2870e02a` `9a25de0b` `66b31aca` `1eb2983b` | Migrations 086–089 ((chart_id, ayanamsha_id) keying across chart_facts + l25_msr/cdlm/cgm/rm/ucn; 3-column MSR coefficient; legacy provenance freeze). Python builder + bootstrap loader + structural tests (13/13). `chart_context.ts` resolver + `assert_no_native_literal.sh` retire NATIVE_CHART_ID/DEFAULT_CHART_ID from `lib/retrieve`. **Sets G4_no_native_lit GREEN.** |
| **3.consult_nav** | 3 | B | `730ab040` `e8bbf29c` `a0d97174` | Role-gated dashboard + nav (guest vs super_admin); per-chart Profile/Build/Consult/Panchang pages + chart switcher (URL + localStorage; mid-conversation switch strips conversationId); SharingPanel grant/revoke writing `chart_grants`. `chart-page-guard.ts` wraps `authorizeChartAccess`. 58/58 tests pass. No tier/depth selector. |

## In flight
- **3.tier_excision** (A) — disclosure module + TierPicker removal + migration 090 (drop `audience_tier`). Concurrent with 3.consult_nav and 2a (no fence collisions).
- **3.dejudge** (C) — `msr_sql.ts` + `query_signals.ts` floor/clique/weights strip. Serialized in tool-layer fence.

## Eligible-now / queued
- **3.gateway_pipeline_isolation** (A) — UNBLOCKED (G3 + 2a). Queued behind 3.tier_excision draining Stream A; serialized vs 3.dejudge/3.tool_asset_recon (shared `lib/retrieve`).
- **3.tool_asset_recon** (C, sets G6_tool_coverage) — UNBLOCKED (G3 + 2a). Queued behind 3.dejudge draining Stream C; serialized vs 3.gateway (shared `lib/contract` + `lib/retrieve`).
- **3.cutover** — waits on **2a** ✓ (G1 ✓ · 2c ✓ · 2a ✓ — ELIGIBLE; brief not yet detailed in queue).
- **3.legacy_delete** — waits on **G5b_onfinish** (0b.1 contributes half; full set lands at cutover).

## What to ship to the native at re-kick
1. **Wave-3 briefs** (Cowork authoring): `2a`, `3.dejudge`, `3.gateway_pipeline_isolation`, `3.consult_nav`, `3.tier_excision`, `3.tool_asset_recon`. Drop at `00_ARCHITECTURE/CONDUCTOR/modernization/briefs/` + remove `status: not_yet_detailed` from queue entries.
2. (Optional) **Apply migrations 081–085** to staging DB.
3. (Carried) **Rotate `amjis-db-password`**.

## Re-kick protocol
1. Open a fresh Conductor chat at repo root on `main`.
2. Paste: "Continue the Platform Modernization program. Read PROGRAM_STATE.md + session_queue.yaml + CONDUCTOR_HALT_LOG.md; resume from the next eligible units."
3. Conductor reconciles gate board, picks eligible units across streams A/B/C, runs to the next batch stop, updates this file.

## Safety reminders (automated, no human)
- Every prod op: pre-flight green + post-deploy smoke + auto-rollback on failure.
- DB: additive + staging→live swap; no destructive in-place; column drops only after a green post-cutover window.
- New flags default OFF (reversible). Kill-switch: error-rate spike → halt_queue + rollback last cherry-pick.
