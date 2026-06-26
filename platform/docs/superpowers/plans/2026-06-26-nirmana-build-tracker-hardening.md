# Nirmāṇa Build Tracker — Full-System Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make every aspect of the Nirmāṇa build tracker correct, robust, accurate, and beautiful: a global Build that walks L1–L5 in DAG order for every registered asset; build/rebuild/refresh/delete correct at global+layer+asset scope with the DAG honored (never build a dependent before its upstream); a complete, reconciled asset catalog; DB-true numbers with no stale data; live progress bars and a live DAG that react during a build; a reconciling delete preview with a structured (not raw-id) downstream list; and a service-vs-data visual distinction. Enhance the existing armillary aesthetic with framer-motion — do not replace it.

**Architecture:** Correctness first (it gates trust), then live-feedback/UX. The build path is TypeScript-resolved (`resolveBuildPlan` in `lib/build/plan.ts` topo-sorts `asset_registry.depends_on`) and dispatched to the external `brahma-build-pipeline-job` Cloud Run Job; the Python orchestrator (separate repo) walks the plan and publishes per-asset Pub/Sub events. The FROZEN orchestrator contract is honored by all writers — fixes here are in routes, the TS plan resolver, the v2 cockpit React components, registry data, and prod env config; **no orchestrator-contract change is in scope** (a needed one is STOP-and-raise).

**Tech Stack:** Next.js (App Router, ISR), React, TypeScript, Tailwind v4 + brand tokens (`globals.css`, `lib/styles/marsys-theme.css`), framer-motion `^12.38.0` (already a dep, `package.json:69`), lucide-react. Postgres via `query()`. SSE over Pub/Sub (`cockpit-events` topic). Python sidecar writers under `python-sidecar/pipeline/orchestrator/`.

**Source handoff:** `00_ARCHITECTURE/NIRMANA_BUILD_TRACKER_HARDENING_HANDOFF_v2_0.md`
**Verified-audit memory:** `project_nirmana_tracker_audit.md`

---

## §0a — Native rulings (RESOLVED — these were the STOP-and-raise questions; now binding)

The three open decisions are answered. **No longer STOP-and-raise — implement as ruled:**

- **Decision 1 (A4 / L0 in global build) — L0 is EXCLUDED from global build/rebuild.** `bg_*` (L0) can be triggered ONLY by `super_admin`, and ONLY via an explicit **L0-layer** trigger or an **individual L0-asset** trigger. It must NEVER build from the global Build/Rebuild button, for any role. **Consequence for A1:** the upstream-closure auto-pull must NOT pull `bg_*` assets into a global or cross-layer downstream plan. If a downstream (L1+) asset's `bg_` dependency is dormant, surface it as a **blocked / "L0 dependency not built — run the Brahmagyan layer first"** state — do not silently build L0. Non-L0 upstream (L1–L4) IS auto-pulled per A1.
- **Decision 2 (C2 / count truth) — HYBRID.** Global `bg_*` assets display recorded `asset_throughput.rows_written` by default; run live `count_sql` ONLY on (i) an explicit Refresh and (ii) immediately after build completion. No live count on the idle/poll path. Per-chart assets stay live as today.
- **Decision 3 (A2 / ka_gochara + ka_tulana) — CLASSIFY BOTH AS SERVICE; DO NOT RETIRE.** Both have live consumers (`ka_sangam.py:26` imports `KaGocharaService`; `ph_muhurta` reads `ka_gochara`; `ka_tulana` is a query-time compare/verdict service with a live test suite asserting no DB). Set `asset_kind='service'` on both in the seed (no `count_sql`, no table to materialize). They render as service nodes (health pill, not progress bar). Do NOT add a `writers/ka_gochara.py` adapter and do NOT delete their seed rows.

## §0 — Audit corrections (READ FIRST — the handoff was wrong on these)

A full re-verification against main `b4b3c764` corrected several headline handoff claims. **Do NOT spend effort on these — they are already correct:**

| Handoff claim | Verified verdict | Evidence |
|---|---|---|
| `bg_dignity_reference` has a writer but NO registry row; cites a nonexistent migration | **FALSE** — has writer, registry row (mig `298`), and cited mig `250_bg_dignity_reference.sql` exists | `bg_dignity_reference.py:481`, `platform/migrations/298_*.sql`, `platform/migrations/250_*.sql` |
| F-W1-001: a `bg_rules` writer calls `conn.rollback()` directly | **FALSE** — zero commit/rollback/close in `bg_rules.py`; ZERO real FROZEN-contract violations across all 60+ writers | `writers/bg_rules.py` (full read); GA `owns_conn` branches inert under orchestrator |
| Orchestrator may not emit asset-level Pub/Sub events | **PRESENT** — `asset.state_change` / `asset.progress` / `asset.substep` all published | `asset_runner.py:413-416, 488-494, 255-297`; `events.py:17-42` |
| L0 is excluded from global build | **ROLE-CONDITIONAL** — super_admin global build INCLUDES L0 (all `bg_*` rows are `scope='global'`); exclusion is only for non-super-admin | `runs/route.ts:41,90`; `asset_registry_seed.ts` (bg_* `scope:'global'`) |
| committing stage caps at 88% | committing = **93%** | `buildStage.ts:10-23` |
| `SunNode` is a standalone file | inline helper inside `CockpitHeader.tsx:15-21` | — |

**The real defects are catalogued per-workstream below.** Each carries verified `file:line` evidence.

---

## File Map

| File | Change type | What changes |
|---|---|---|
| `src/lib/build/plan.ts` | Modify | Wire `computeUpstreamClosure` into `resolveBuildPlan` for layer/asset build+rebuild (auto-pull dormant upstream, DAG-ordered) |
| `src/app/api/cockpit/runs/route.ts` | Modify | Explicit, documented L0 gate; ensure global scope = all active L1–L5 for the build path; pass upstream-pull through |
| `src/app/api/build/cascade-preview/route.ts` | Rewrite | Retire `build_dependencies`; compute downstream from `asset_registry.depends_on` via `computeDownstreamClosure`; return layer + human names |
| `src/app/api/build/cascade/route.ts` | Modify | Repoint to `asset_registry.depends_on` (same source as build path) |
| `src/app/api/build/data-readiness/route.ts` | Modify | Repoint off `build_dependencies` |
| `migrations/154_build_dependencies.sql` + `_archive/158_*` | Deprecate | Mark table retired (drop deferred per ROOT_FILE_POLICY/destructive-gate); remove code citations first |
| `scripts/seed/asset_registry_seed.ts` | Modify | Remove dead `ga_pyjhora_engine`; confirm `ka_gochara`/`ka_tulana` kind; fill any service `asset_kind` gaps |
| `src/app/api/cockpit/registry/route.ts` | Modify | Dedupe duplicated SELECT line (`:51-52`); ensure `sanskrit_name`+`english_name`+`asset_type`+`asset_kind` reach clients |
| `src/app/api/cockpit/stats/route.ts` | Modify | Single count-truth policy; let `build_state_stale` reconcile for global assets; keep per_chart live |
| `src/app/api/cockpit/sse/route.ts` | Modify | Heartbeat-only mode must still deliver `run.state_change` (completion) so the UI refetches; log Pub/Sub fallback loudly |
| `src/app/api/cockpit/refresh/route.ts` | Modify | Make refresh meaningful (bust registry ISR cache / recompute), or document the client-driven contract |
| `src/hooks/useAssetStats.ts` | Modify | Force immediate refetch on run-completion regardless of SSE mode (poll run-state to completion as fallback) |
| `src/hooks/useActiveRun.ts` | Read | `plan` already exposed (`:21`) — consumed by graph + bars |
| `src/lib/components/cockpit/v2/CockpitShell.tsx` | Modify | Wire global `onRefreshed` to real `refetchStats`+`refreshRun`+registry refetch (currently `() => {}` `:127`) |
| `src/lib/components/cockpit/v2/CockpitHeader.tsx` | Modify | Add overall/global progress bar (assets-lit / rows aggregate), framer-motion driven |
| `src/lib/components/cockpit/v2/AssetProgressBar.tsx` | Modify | Drive fill from live rows/target; framer-motion spring; shimmer while building; settle at 100% |
| `src/lib/components/cockpit/v2/buildStage.ts` | Modify | Keep stage as fallback (no target_floor); blend so fill never regresses, lands exactly 100% at lit |
| `src/lib/components/cockpit/v2/ArmillaryGraph.tsx` | Modify | Seed building/queued state from `activeRun.plan`; visible building distinction; reveal beads during build; service/data node glyph |
| `src/lib/components/cockpit/v2/AssetRow.tsx` | Modify | Leading service/data icon in name cell (keyed off existing `asset_type`/`asset_kind`) |
| `src/lib/components/cockpit/v2/ClearConfirmModal.tsx` | Modify | One reconciling summary (rows / assets clearable-vs-not / tables); structured layer-grouped downstream tree with full count |
| `src/components/cockpit/CascadePreviewModal.tsx` | Modify | Structured layer-grouped tree with Sanskrit+English names (not raw-id dump); shared visual language with ClearConfirm |
| `python-sidecar/.../writers/*` | None | FROZEN-contract conformant — no change (see §0) |

---

## §A — WORKSTREAM A: Build correctness (DAG, scopes, catalog) — **CORRECTNESS, do first**

### Task A1: Wire upstream-closure into the plan resolver (the core DAG bug)

**Files:** Modify `src/lib/build/plan.ts`; touch `src/app/api/cockpit/runs/route.ts`.

**Root cause (verified):** `computeUpstreamClosure` is defined (`plan.ts:94`) but **never called** by `resolveBuildPlan`. `assetsInScope` (`:57-65`) returns only the literal scope set; `topoSort` only orders deps that are already `inScope` (`:45`). So a layer- or asset-scoped **build/rebuild** of a downstream asset whose cross-layer upstream is `dormant` neither builds nor correctly orders that upstream → the dependent reads an absent source → silent data loss. (Global scope is safe because all assets are in-scope.)

- [ ] **Step 1:** In `resolveBuildPlan`, for `action==='build'` and `action==='rebuild'` at `scope==='asset'` and `scope==='layer'`, compute `upstream = computeUpstreamClosure(candidates, registry)` and union any upstream asset whose throughput state is missing/`dormant`/`error` into `candidates` **before** `topoSort` (`:157`). Do not re-run already-lit upstream on a `build` (respect skip-if-lit for the pulled-in upstream); for `rebuild`, pulled-in upstream that is lit need not be force-rebuilt unless the user chose a cascade — keep current rebuild semantics for the explicit target+downstream, only ADD missing upstream so the build is runnable. **L0 EXCLUSION (native ruling, §0a-D1):** the auto-pull must NEVER add an `bg_*` (L0) asset to the plan. Filter L0 out of the computed upstream set. If a candidate's `depends_on` includes a dormant `bg_*` asset, do NOT build it — instead mark that candidate **blocked** with reason "L0 dependency `<id>` not built — run the Brahmagyan layer first" and exclude it from the runnable plan (surface the blocked list to `PlanModal`). Only L1–L4 upstream is auto-pulled.
- [ ] **Step 2:** Confirm `topoSort` (`:32-55`) then orders the unioned set correctly across layer boundaries (it will, since deps are now in-scope). Keep cycle detection.
- [ ] **Step 3:** Surface pulled-in upstream in the returned plan metadata (there is already `upstreamCount` at `:159`) so `PlanModal` can show "+N upstream dependencies will also build."
- [ ] **Step 4 (verify):** Unit test in `src/lib/build/__tests__/` (or alongside existing `plan.test.ts`): asset-scope build of an L4 asset depending on a dormant L2 asset MUST include the L2 asset, ordered before the L4 asset. Layer-scope build of L4 with dormant L2 upstream MUST include it. A `build` must NOT re-run lit upstream. Empty `depends_on` asset is still included as a root (regression guard). **L0 guard:** asset-scope build of an L1 asset depending on a dormant `bg_*` asset MUST NOT include the `bg_*` asset in the plan, and MUST mark the L1 asset blocked with the L0-dependency reason (not silently built).

### Task A2: Catalog reconciliation — one source of truth

**Files:** Modify `scripts/seed/asset_registry_seed.ts`, `src/app/api/cockpit/registry/route.ts`.

**Verified state:** Single source of truth = `asset_registry_seed.ts` (76 rows; numbered migrations converge to it via `ON CONFLICT DO UPDATE`). 65 production `@register` writers; every production data writer maps to a registry row with a `count_sql`. Remaining divergences are small and specific:

- [ ] **Step 1:** Remove the dead `ga_pyjhora_engine` registry row (INSERTed by `supabase/migrations/205_ga1_pyjhora_service.sql`, absent from the seed superset → stale). Add a forward migration that deletes it; confirm nothing reads it.
- [ ] **Step 2 (native ruling §0a-D3 — RESOLVED):** `ka_gochara` is a **service with live consumers** (`ka_sangam.py:26` imports `KaGocharaService`; `ph_muhurta.py` reads it). Set `asset_kind='service'` on its seed row. Do NOT add a `writers/ka_gochara.py` adapter; do NOT retire it. The dead-looking `@register('ka_gochara')` in `services/ka_gochara/writer.py:73` is for the service self-test, not a build writer — leave it.
- [ ] **Step 3 (native ruling §0a-D3 — RESOLVED):** `ka_tulana` is a **query-time compare/verdict service** (live test suite asserts no `db_conn`). Set `asset_kind='service'` on its seed row. No `@register`, no table, no `count_sql` — correct by design. Do NOT retire.
- [ ] **Step 4:** Dedupe `registry/route.ts:51-52` (the `asset_kind, service_health, last_invoked_at, last_selftest_at, selftest_detail` SELECT line is repeated verbatim).
- [ ] **Step 5:** Confirm every service asset (`bg_panchanga`, `bg_ephemeris_engine`, `ka_graha_sancara`, `ka_dasha_kala`, `ka_muhurta_seva`, and post-decision `ka_gochara`/`ka_tulana`) has `asset_kind='service'` (or `asset_type='service'`) set in the seed so Workstream F's icon + the stats service-health path key correctly. `null` `count_sql` is correct for services.
- [ ] **Step 6 (verify):** Add a catalog-reconciliation test/script: every `@register` id (minus known service/test/dead) has a seed row with non-empty `count_sql` (data) or `asset_kind='service'` (service), and a `depends_on` that resolves to existing ids. Run it in CI.

### Task A3: Retire the second DAG (cascade-preview phantom schema)

**Files:** Rewrite `src/app/api/build/cascade-preview/route.ts`; modify `src/app/api/build/cascade/route.ts`, `src/app/api/build/data-readiness/route.ts`; deprecate `migrations/154_build_dependencies.sql`.

**Root cause (verified, doubly broken):** cascade-preview walks the legacy `build_dependencies` table (`migrations/154`) which (a) is keyed on the **dead `A1..A22 / META_*` id scheme**, not `bg_/ga_/bo_/...`, and (b) is queried with a **phantom column** `depends_on_asset_id` / `descendant_id` that does not exist (real schema: `asset_id`, `depends_on text[]`). It would fail at runtime and never matches what actually builds.

- [ ] **Step 1:** Rewrite `cascade-preview/route.ts` to compute the downstream closure from `asset_registry.depends_on` using the existing `computeDownstreamClosure(seeds, registry)` in `plan.ts` (the SAME source the build path uses). Return for each downstream asset: `asset_id`, `layer`, `sanskrit_name`, `english_name` (all present in `asset_registry`), preserving DAG order.
- [ ] **Step 2:** Repoint `cascade/route.ts` and `data-readiness/route.ts` off `build_dependencies` to the same `asset_registry.depends_on` source. Grep for every remaining `build_dependencies` reference (incl. `plan.test.ts`) and update or remove.
- [ ] **Step 3:** Per the destructive-brief reverse-citation gate: grep all live code for `build_dependencies` BEFORE dropping the table. Only after zero live citations remain, add a forward migration marking `build_dependencies` retired (defer the physical `DROP TABLE` to a follow-up per ROOT_FILE_POLICY; a commented retirement migration is acceptable now).
- [ ] **Step 4 (verify):** cascade-preview for a global clear returns the real `bo_/ga_/ph_` downstream set with layer + human names, matching the set `resolveBuildPlan` would rebuild. Test the route returns 200 (not the prior phantom-column 500).

### Task A4: Confirm L0 gating + scope correctness at the build path

**Files:** Modify `src/app/api/cockpit/runs/route.ts`.

**Verified:** L0 exclusion is role-conditional via `allowedScopes` (`:41,90`); the handoff's absolute "L0 excluded" is wrong. Make the intended behaviour explicit and documented so it can't silently regress.

- [ ] **Step 1:** Document + assert the contract at `runs/route.ts`: global/per-chart build walks **all active L1–L5**; L0 (`bg_*`, `scope='global'`) builds **only** via an explicit Brahmagyan-layer trigger by `super_admin`. Verify the scope filter encodes exactly this (it currently lets super_admin global builds include L0 — decide WITH the native whether that is intended; if not, exclude `layer='brahmagyan'` from `scope='global'` builds explicitly). **STOP-and-raise this one question to the native before changing behaviour.**
- [ ] **Step 2:** Confirm Nirmāṇa build access remains owner/admin-only (existing rule): build = `owner_id` match OR `super_admin`; view-grantees read-only. Do not regress `ae9a4634`'s permission semantics.
- [ ] **Step 3 (verify):** A super_admin global Build produces a plan covering every active L1–L5 asset, DAG-ordered, with L0 handled per the Step-1 decision. A non-super-admin cannot trigger L0 or layer='brahmagyan'.

---

## §B — WORKSTREAM C: Accurate numbers / no stale data — **CORRECTNESS, do second**

(Numbered C to match the handoff; it gates the live-feedback workstreams.)

### Task C1: Force a stats refetch on build completion in every SSE mode

**Files:** Modify `src/app/api/cockpit/sse/route.ts`, `src/hooks/useAssetStats.ts`; touch `src/lib/components/cockpit/v2/DataAssetsView.tsx`.

**Root cause (verified):** In heartbeat-only SSE mode (`sse/route.ts:118-148`, taken when `PUBSUB_DISABLED` set or `GOOGLE_CLOUD_PROJECT` absent, OR silently on Pub/Sub subscribe failure `:87-90`) the stream forwards **zero** orchestrator events — no `run.state_change`. So `DataAssetsView.tsx:113-115`'s completion-triggered `refetchStats()` never fires; the UI waits out the 30s idle poll (`useAssetStats.ts:65`).

- [ ] **Step 1:** Make heartbeat-only mode still deliver a `run.state_change` on completion: have `pollingStream` poll the run row (`/api/cockpit/runs/active` or a direct query) and emit a synthetic `run.state_change` frame when the run transitions to `completed`/`failed`/`stopped`. This keeps the existing `DataAssetsView` refetch path working without Pub/Sub.
- [ ] **Step 2:** As a belt-and-suspenders client fallback, in `useAssetStats` (or `useActiveRun`) detect the active-run transition to terminal and trigger an immediate one-shot `refetch()` rather than waiting for the next 30s tick.
- [ ] **Step 3:** Log the Pub/Sub→heartbeat fallback loudly (it is currently silent at `:87-90`) so prod misconfig is visible.
- [ ] **Step 4 (verify):** With Pub/Sub disabled, completing a build refreshes counts within ~5s (the active-build poll cadence), not 30s.

### Task C2: Single count-truth policy + reconcile the stale badge

**Files:** Modify `src/app/api/cockpit/stats/route.ts`.

**Root cause (verified):** Global `bg_*` assets return recorded `asset_throughput.rows_written` (`:123-137`), not a live count; the `build_state_stale` badge (`:270-272`) structurally cannot fire for them (`:135` hardcodes `false`). Per-chart assets are already live+accurate — keep that.

- [ ] **Step 1 (native ruling §0a-D2 — HYBRID):** Global `bg_*` assets display recorded `asset_throughput.rows_written` by default (the idle/poll path keeps the current cheap shortcut at `stats/route.ts:123-137`). Run live `count_sql` for global assets ONLY when the request is (i) an explicit Refresh (a query param / header the Refresh path sets — see C3) or (ii) the post-build-completion refetch. Add a `mode=live` (or equivalent) branch to the stats route that, when set, bypasses the `rows_written` shortcut for global assets and runs `count_sql`. Confirm clear/rebuild still resets `rows_written` (it does — `execute/route.ts:190-199` sets dormant), so the default display reads 0 after a clear either way.
- [ ] **Step 2:** Allow `build_state_stale` (or an equivalent reconciliation) to surface for global assets too — compute it on the live-count path so the count_sql-vs-throughput delta is detectable; replace the bare badge with a reconciliation that explains the delta. No bare unexplained badge.
- [ ] **Step 3 (verify):** After a clear, a global asset reads 0. On the idle poll, a global asset shows `rows_written` (no per-poll query). On an explicit Refresh or post-build, the same asset shows the live `count_sql` value, and any throughput-vs-live delta surfaces as an explained reconciliation state — never a silent wrong number.

### Task C3: Make Refresh meaningful (and fix the global no-op)

**Files:** Modify `src/lib/components/cockpit/v2/CockpitShell.tsx`, `src/app/api/cockpit/refresh/route.ts`; touch `src/app/api/cockpit/registry/route.ts`.

**Root cause (verified):** Global Refresh is a **no-op** — `CockpitShell.tsx:127` passes `onRefreshed={() => {}}`. The endpoint only bumps `asset_throughput.updated_at` (`refresh/route.ts:46-53`); it neither recomputes nor busts the 60s registry ISR cache (`registry/route.ts:4,74`). Layer/asset Refresh ARE wired (`onRunStarted`) but never refetch the registry.

- [ ] **Step 1:** Wire `CockpitShell`'s global `onRefreshed` to a real handler: `refetchStats()` + `refreshRun()` + `useAssetRegistry.refetch()` (the hook exposes `refetch` at `useAssetRegistry.ts:19`, currently unused by any refresh path).
- [ ] **Step 2:** On a manual Refresh, bust the registry cache (e.g. fetch with `cache: 'no-store'` / a cache-busting query param) so newly-built/edited assets, names, and `count_sql` changes appear immediately instead of after 60s (+30s SWR). **Also fetch stats with the `mode=live` signal (per C2 §0a-D2)** so global assets show a live `count_sql` count on an explicit Refresh, not the cached `rows_written`.
- [ ] **Step 3:** Make `/api/cockpit/refresh` either recompute a meaningful freshness signal or be explicitly documented as a soft client-driven refresh; remove the false "Refreshed" toast when nothing changed.
- [ ] **Step 4 (verify):** Clicking global Refresh updates stats, run state, and registry-derived names/counts immediately. Layer/asset Refresh also refetch registry.

---

## §C — WORKSTREAM E: Delete/clear modal — reconcile + structure — **CORRECTNESS, do third**

### Task E1: One reconciling clear summary

**Files:** Modify `src/app/api/cockpit/clear/route.ts`, `src/lib/components/cockpit/v2/ClearConfirmModal.tsx`.

**Root cause (verified):** Three groupings over disjoint populations are shown side-by-side and cannot agree: `tables[]` (clearable-only, table-keyed, collapses many-assets→one-table, `route.ts:160-170`) < `affected_assets`/`layer_summary.asset_count` (ALL scope assets incl. not_clearable/0-row, `:178,213-218`) < (row-contributing assets, never displayed). Only `total_rows` (`:177`) reconciles. The modal also flips axis by scope (global→layer, asset/layer→table; `ClearConfirmModal.tsx:106,174-208`).

- [ ] **Step 1:** Have the route return one coherent, reconciling structure: `total_rows`, `assets_clearable` (contribute rows), `assets_reset_only` (0-row / not_clearable, reset to dormant), `tables_touched`, and a per-layer rollup — so every displayed number ties out (`assets_clearable + assets_reset_only = affected_assets.length`).
- [ ] **Step 2:** In the modal, present ONE summary with the SAME grouping across asset/layer/global scope. Show 0-row assets explicitly as "0 rows (reset only)" so the arithmetic is obviously correct. Stop flipping the footer label between "N tables" and "N assets."
- [ ] **Step 3 (verify):** For asset, layer, and global clears, the displayed rows/assets/tables all reconcile; "reset N" never exceeds (clearable + reset-only); a many-assets-one-table case (e.g. several `ga_*`→`chart_facts`) is shown without a contradiction.

### Task E2: Structured, named downstream/cascade tree

**Files:** Modify `src/lib/components/cockpit/v2/ClearConfirmModal.tsx`, `src/components/cockpit/CascadePreviewModal.tsx`.

**Root cause (verified):** Downstream-stale rendered as `slice(0,3).join(', ')+'…'` with no remainder count (`ClearConfirmModal.tsx:227-234`); CascadePreview is a flat vertical dump of raw `asset_id` strings, no layer headers, no names, 70+ on a global clear (`CascadePreviewModal.tsx:166-194`). `asset_registry` has BOTH `sanskrit_name` and `english_name` — fully feasible to render a tree.

- [ ] **Step 1:** Render the affected downstream as a structured tree grouped by layer (Brahmagyan→Mīmāṃsā order), each asset shown with Sanskrit + English name (not raw id), full count, expand/collapse, DAG order preserved. framer-motion for expand.
- [ ] **Step 2:** Pass the names + layer into `CascadePreviewModal` (it currently receives only `plan: string[]`); render the same structured layer-grouped tree for the rebuild plan. Depends on Task A3 (cascade-preview now returns layer + names).
- [ ] **Step 3:** Unify the two modals' visual language (consistent truncation: always show a `+N more` count; no bare `…`). Asset/layer/global delete + the rebuild offer should feel like one flow.
- [ ] **Step 4 (verify):** A global clear shows a readable layer-grouped, human-named tree with an accurate total count and expand/collapse — no raw-id dump, no uncounted ellipsis.

---

## §D — WORKSTREAM B: Live progress bars — **LIVE FEEDBACK, do after correctness**

### Task B1: Drive fill from live rows, framer-motion spring

**Files:** Modify `src/lib/components/cockpit/v2/AssetProgressBar.tsx`, `src/lib/components/cockpit/v2/buildStage.ts`.

**Root cause (verified):** Fill is discrete stage constants, "row-count-independent" (`AssetProgressBar.tsx:53`; `buildStage.ts:10-23`, committing=93). Single-`run` writers (no substeps — most L1/L2) sit at 12% then snap to 100%. `actualRows` (live `rows_written` via SSE `asset.progress`/`asset.substep` + stats `rows_written`) and `targetVolume`/`target_floor` ALREADY reach the component (`AssetRow.tsx:264-270`) but are used only as a text label.

- [ ] **Step 1:** While building, compute `rowsFill = clamp(actualRows / targetVolume * 100, 0..100)` when `targetVolume>0`. Blend with the stage value so the bar never goes backward (`max(stageFloor, rowsFill)` with a monotonic guard) and lands exactly 100% at `lit`.
- [ ] **Step 2:** For assets with no `target_floor`, fall back to substep/stage fill (current behaviour) — but still animate.
- [ ] **Step 3:** Use framer-motion (already imported `:3`) for a smooth spring fill that grows with the row count, a subtle shimmer/pulse while building, and a satisfying settle at 100%.
- [ ] **Step 4 (verify):** A single-`run` asset with a `target_floor` shows a growing bar (not 12%→100% blink); a substep asset still advances smoothly; a no-target service asset shows the `ServiceHealthPill` (Workstream F) not a bar.

### Task B2: Overall/global progress bar in the header

**Files:** Modify `src/lib/components/cockpit/v2/CockpitHeader.tsx`; touch `CockpitShell.tsx`/`DataAssetsView.tsx` for inputs.

**Verified:** No global progress bar exists (`CockpitHeader.tsx:236-283` is a text telemetry strip). Inputs exist: per-asset state + `actual_rows` in `assetsWithState`, `activeRun.plan` for the denominator.

- [ ] **Step 1:** Add a framer-motion overall bar: `lit-in-scope / total-in-scope` (and optionally a rows aggregate) during a global/layer build, driven from the assembled per-asset state + `activeRun.plan`.
- [ ] **Step 2 (verify):** During a global build the header bar advances as assets complete and reaches 100% at run completion; idle shows no bar (or a full/empty resting state).

---

## §E — WORKSTREAM D: Live DAG (ArmillaryGraph reacts) — **LIVE FEEDBACK**

### Task D1: Seed building/queued state from the plan; make building visibly distinct

**Files:** Modify `src/lib/components/cockpit/v2/ArmillaryGraph.tsx`.

**Root cause (verified):** ArmillaryGraph is the ACTIVE graph (one planet/layer). `aggregate()` (`:75-84`) marks a layer building only while some asset's polled state is literally `'building'` — a ~1s window the 5s poll misses and heartbeat-only SSE never delivers. It **ignores `activeRun.plan`** (available, `useActiveRun.ts:21`; already passed in but only used as `isBuild` boolean). The dead `v2/LiveDependencyGraph.tsx:236-242` had the exact missing pattern (seed building-state from `activeRun.plan`). Beads are hidden unless the layer is bloomed/hovered (`:362-366`).

- [ ] **Step 1:** Seed per-asset/per-layer building+queued state from `activeRun.plan` + the run's current position: an asset in the active plan that isn't yet lit reads as building (current) or queued (ahead in plan), independent of catching the 1s throughput window. Port the pattern from the dead graph.
- [ ] **Step 2:** Make a building node visibly distinct: pulsing glow, flowing edges to/from it, the built-fraction arc advancing as its assets complete. Build vs idle must look clearly different.
- [ ] **Step 3:** Wire real-time row growth into the node (planet atmosphere/arc reflects rows/target while building) so the DAG and the bars tell the same live story.
- [ ] **Step 4:** Reveal the asset beads during an active build (not only on hover) so the asset-level DAG is visible while building; reflect per-asset progress, not just per-layer.
- [ ] **Step 5 (verify):** During a real build (or a simulated plan), the correct planet(s) light/pulse, queued layers read distinctly, beads are visible, and the arc advances with completion — verified visually via Chrome MCP before/after on `1c826d5a`.

### Task D2: Confirm prod Pub/Sub emit so live feedback has data

**Files:** prod env config (Cloud Run job) + a smoke check; no app-code change.

**Verified:** Orchestrator emits asset-level events; delivery requires the Cloud Run job to have `PUBSUB_TOPIC` set and `PUBSUB_DISABLED` unset, and the web SSE route to have `GOOGLE_CLOUD_PROJECT`.

- [ ] **Step 1:** Confirm prod `brahma-build-pipeline-job` and `amjis-web` have the Pub/Sub env correctly set (else live DAG + bars are starved and the C1 heartbeat fallback carries completion only). Document the required env in the deploy config.
- [ ] **Step 2 (verify):** A prod build streams `asset.progress`/`asset.substep` frames (observe via the SSE endpoint / network panel). If not, C1's synthetic completion event still keeps counts correct.

---

## §F — WORKSTREAM F: Service vs data distinction — **independent, low-risk quick win**

### Task F1: Leading service/data icon in the asset row + DAG node

**Files:** Modify `src/lib/components/cockpit/v2/AssetRow.tsx`, `src/lib/components/cockpit/v2/ArmillaryGraph.tsx`.

**Verified:** Rows show only StatusDot + names (`AssetRow.tsx:243-256`); the only current distinction is the progress column branch (`ServiceHealthPill` vs `AssetProgressBar`, `:260-261`), which already reads `asset_type`/`asset_kind`. Both fields already reach the component via the registry route. No new plumbing.

- [ ] **Step 1:** Add a small leading icon in the name cell (`AssetRow.tsx:246-251`): a data/storage glyph for data assets, a service/gear glyph for service assets, keyed off existing `asset_type`/`asset_kind`. House style = inline SVG (match `SunNode`/`Trash2`); lucide-react also available.
- [ ] **Step 2:** Apply the same distinction to ArmillaryGraph nodes/beads so services read differently in the DAG.
- [ ] **Step 3:** Depends on Task A2 Step 5 (every service asset's kind correctly set in the registry).
- [ ] **Step 4 (verify):** Service assets (e.g. `bg_panchanga`, `ka_dasha_kala`) show the service glyph + `ServiceHealthPill`; data assets show the data glyph + progress bar, in both the row and the DAG.

---

## §F2 — WORKSTREAM F2: Brand-theme regression — revert green progress paths to gold — **independent, do anytime (quick win)**

### Task F2.1: Revert lit/healthy progress fills + pills from green back to brand gold

**Files:** Modify `src/lib/components/cockpit/v2/AssetProgressBar.tsx`, `src/lib/components/cockpit/v2/AssetRow.tsx`.

**Root cause (verified):** At some point the lit/healthy progress path turned **green**, violating the gold design system. `STATE_COLORS.lit.fill` is correctly gold (`rgba(176,137,58,0.92)`, `AssetProgressBar.tsx:22`), but the `fillColor` override at `AssetProgressBar.tsx:76-80` **forces green** (`rgba(83,180,95,0.55)`) whenever `isLit` — so a completed progress bar renders green instead of gold. The `lit.pillColor` is also green (`rgba(140,210,140,0.95)`, `:22`), and the `ServiceHealthPill` `isGreen` branch in `AssetRow.tsx:52-54` uses the same green family (`rgba(83,180,95,..)` fill/stroke, `rgba(140,210,140,0.95)` pill).

**Decision (native, this session):** Revert ONLY the green lit/healthy/`service_ok` states to the **gold already in use on the Nirmāṇa tracker** — reuse the existing `lit.fill` / `lit.stroke` values, do not introduce a new gold. Keep `error`=red and `building`=amber unchanged. Canonical brand gold = `--brand-gold` `oklch(0.78 0.13 80)` ≈ `#d4af37` (`globals.css:56`); the tracker's in-use lit gold is `rgba(176,137,58,0.92)` fill / `rgba(212,166,72,0.9)` stroke.

- [ ] **Step 1:** In `AssetProgressBar.tsx:76-80`, remove the green lit override so the lit fill falls through to `colors.fill` (already the correct gold `rgba(176,137,58,0.92)`). Keep the `isError`→red branch. Net: `fillColor = isError ? red : colors.fill` (no green).
- [ ] **Step 2:** In `AssetProgressBar.tsx:22`, change `lit.pillColor` from green `rgba(140,210,140,0.95)` to the gold pill color used for healthy states — match the tracker's gold pill (e.g. `rgba(236,197,106,0.95)`, the same warm gold used by `building`/`stale` pills) so "LIVE" reads gold, not green.
- [ ] **Step 3:** In `AssetRow.tsx:52-54`, change the `ServiceHealthPill` `isGreen` branch fill/stroke/pillColor from the green family to the same gold (fill `rgba(176,137,58,0.92)`, stroke `rgba(212,166,72,0.9)`, pillColor `rgba(236,197,106,0.95)`). The `isGreen` variable name can stay (semantic = healthy); only the colors change. Leave `isError`=red, `isRunning`=amber.
- [ ] **Step 4:** Grep the v2 cockpit dir for any other lit/healthy green (`83,180,95` / `140,210,140` / `emerald` / green hex) and revert to the gold family. Do NOT touch the `StatusDot` semantics if green there is an intentional health signal — confirm with the native if any non-progress green is found; the reported violation is specifically the **progress paths**.
- [ ] **Step 5 (verify):** Update/adjust the `AssetRow_CockpitPolishR2` tests that assert "green" for lit/service rows (`__tests__/AssetRow_CockpitPolishR2.test.tsx:109,159,199,283,301`) to assert the gold values instead. Visually confirm via Chrome MCP on `1c826d5a`: a lit asset's progress bar and "LIVE" pill render gold, a building asset amber, a failed asset red — no green anywhere on the progress paths.

---

## §G — Execution order, guardrails, acceptance

**Priority order (correctness gates trust; live-feedback depends on the SSE/count fixes landing):**
1. **A2** catalog reconciliation (foundational — counts/DAG/global completeness depend on it).
2. **A1** upstream-closure DAG fix + **A4** scope/L0 confirmation + **A3** retire second DAG.
3. **C1/C2/C3** accurate numbers / refresh (+ **D2** confirm prod Pub/Sub emit).
4. **E1/E2** delete modal reconcile + structured tree.
5. **B1/B2** live progress bars (need the live-rows stream from C1).
6. **D1** live DAG reaction (needs C1 + plan-seeding).
7. **F1** service/data icons (independent — slot anytime).
8. **F2** green→gold brand revert (independent, lowest-risk — slot anytime; a pure color fix).

**Guardrails:**
- **FROZEN orchestrator contract** — fix via conforming routes/components/registry/env only. A needed contract change is **STOP-and-raise**.
- The three prior STOP-and-raise questions are **RESOLVED** by native ruling (§0a) — implement as ruled (L0 excluded from global; hybrid counts; ka_gochara/ka_tulana = service). Any NEW ambiguity outside these is still STOP-and-raise.
- **Destructive ops** (retiring `build_dependencies`) go through the reverse-citation gate (grep live code for every kill target first; reclassify any with active citations as KEEP-OR-REPOINT). Defer physical `DROP TABLE` per ROOT_FILE_POLICY.
- **Migrations:** surgical, forward-only; numbering note — two migration dirs lexical-merge, platform-migs max is higher than supabase-migs; verify the next free number before authoring (the `330+` not `251` trap).
- framer-motion (already a dep) for all new motion; brand tokens from `globals.css`/`marsys-theme.css`; **enhance the armillary aesthetic, don't replace it.**

**Acceptance criteria — every fix verified against PROD truth on non-native `1c826d5a` (SAFE); NEVER destructive on native `482012f1`:**
- `[verify-against: prod] [via: psql_prod | curl_prod]` — A1: asset-scope build of a downstream asset with dormant upstream includes+orders the upstream.
- `[verify-against: prod]` — A3: cascade-preview returns 200 with real `bo_/ga_/ph_` downstream + layer + names (no phantom-column 500).
- `[verify-against: prod] [via: chrome_mcp]` — C3: global Refresh visibly updates counts/names immediately.
- `[verify-against: prod] [via: chrome_mcp]` — E1/E2: clear preview numbers reconcile; downstream shown as a named layer-grouped tree.
- `[verify-against: prod] [via: chrome_mcp before/after]` — B1/B2/D1/F1: bars grow with rows, header bar advances, DAG planets light from the plan, service/data glyphs render.
- **Truth bar:** tracker display == DB reality; full success or an explicit failure list; never silent partial success.
- **Verify Cloud Run revision before Chrome MCP probes** (`gcloud run services describe ... revisionName` matches the merge SHA; CDN cache adds 30–60s).

**Coordination:** This build-SYSTEM work is PARALLEL to the PRE_REGEN data-audit campaign. They intersect at A2 (registry reconciliation) — do that reconciliation ONCE and share it. The writer-contract findings here are CLEAN (no F-W1-001 fix needed), which simplifies coordination.
