---
artifact: NIRMANA_BUILD_TRACKER_HARDENING_HANDOFF_v2_0.md
canonical_id: NIRMANA_BUILD_TRACKER_HARDENING_HANDOFF
version: 2.0
status: ACTIVE
authored_by: Claude (Cowork) 2026-06-26
supersedes: BUILD_TRACKER_HARDENING_HANDOFF_v1_0.md (clear-focused; this is the full-system handoff)
purpose: >
  Complete, self-contained context to make the ENTIRE Nirmāṇa build tracker + orchestrator + build
  system correct, robust, accurate, and beautiful. Covers: global build that walks ALL layers L1–L5 in
  DAG order for every registered asset; the stale/incomplete orchestrator asset list; build/rebuild/
  refresh/delete at global+layer+asset scope; the dead progress bars; the non-live DAG; the
  non-reconciling delete modal + badly-dumped DAG lists; service-vs-data visual distinction; and overall
  UI/UX polish (framer-motion). Grounded in a direct code audit (file:line evidence throughout).
audience: Claude Code (Antigravity) — executed as its own focused workstream
related: PRE_REGEN_FULL_AUDIT_CAMPAIGN_v1_0 (this is the build-SYSTEM track, parallel to the data-audit
  campaign), reference-build-tracker-paths (memory)
---

# Nirmāṇa Build Tracker — Full-System Hardening Handoff

## §0 — Mission (the native's framing, expanded)
Make every aspect of the build tracker correct and excellent. The user called out specific symptoms;
treat them as representative of a CLASS, not an exhaustive list — fix the class. The pillars:
1. **Global build = build EVERYTHING.** Pressing global Build builds L1→L5 (all five upper layers) for
   every registered/visible asset, in DAG order. L0 Brahmagyan already exists and is NOT built by
   global/per-chart build — it builds ONLY via an explicit super_admin trigger on the Brahmagyan
   layer's Build/Rebuild button.
2. **DAG is mandatory.** Never build an asset before its upstream (or same-layer) dependency — that
   causes data loss (the dependent reads an absent source). Build/rebuild honors the DAG at every scope.
3. **Scopes:** build + rebuild work at global, layer (phase), and asset scope.
4. **The orchestrator's asset list is stale/incomplete** — it misses some assets / lacks updated info.
   The catalog must be complete and authoritative.
5. **Accurate numbers + no stale data** — the tracker must show DB truth, always.
6. **Live, beautiful build feedback** — progress bars that actually grow with the data; a DAG that
   visibly reacts during a build; clean reconciling delete previews; service-vs-data icons; modern
   motion (framer-motion is already a dependency).

Use a **superpowers** workflow plan (the project convention — `platform/docs/superpowers/plans/`) to
drive the audit+fix. Treat this handoff as the design input to that plan.

## §1 — System map (verified file:line — build on THESE, not memory)
**Backend / build path:**
- Build trigger: `POST /api/cockpit/runs` (`platform/src/app/api/cockpit/runs/route.ts`). NOT
  /api/build/start (decommissioned 410).
- Plan/DAG resolver: `platform/src/lib/build/plan.ts` `resolveBuildPlan` — reads
  `asset_registry.depends_on`, topo-sorts. THIS is the authoritative DAG source.
- Job invoker: `platform/src/lib/build/jobInvoker.ts` `invokeRunJob` → Cloud Run Job
  `brahma-build-pipeline-job` (asia-south1).
- Orchestrator: `platform/python-sidecar/pipeline/orchestrator/runner.py` `execute_run` — walks the
  plan, `run_asset` per asset, skip-if-lit bypassed when action='rebuild'.
- Asset discovery (Python): `@register('<id>')` decorators in
  `platform/python-sidecar/pipeline/orchestrator/writers/*.py`.
- Stats/Refresh: `platform/src/app/api/cockpit/stats/route.ts`.
- Clear preview: `platform/src/app/api/cockpit/clear/route.ts`; execute:
  `clear/execute/route.ts`; spec `platform/src/lib/cockpit/assetClearSpec.ts`.
- Registry route: `platform/src/app/api/cockpit/registry/route.ts` (selects asset_type, asset_kind).
- SSE: `platform/src/app/api/cockpit/sse/route.ts` (Pub/Sub OR heartbeat-only fallback).

**UI (v2 cockpit — the ACTIVE tree):**
- Page: `platform/src/app/clients/[id]/nirmana/page.tsx` → `CockpitShell`
  (`platform/src/lib/components/cockpit/v2/CockpitShell.tsx`).
- Header + telemetry strip + global build/clear: `.../v2/CockpitHeader.tsx` (telemetry is INLINE
  L236-283; there is NO standalone TelemetryStrip and NO overall/global progress bar).
- Main view: `.../v2/DataAssetsView.tsx`; layer accordion `.../v2/LayerPanel.tsx`; asset row
  `.../v2/AssetRow.tsx`.
- Per-asset progress bar: `.../v2/AssetProgressBar.tsx`; fill math `.../v2/buildStage.ts`.
- **Active DAG = `.../v2/ArmillaryGraph.tsx`** (one planet PER LAYER). `LiveDependencyGraph.tsx` is
  DEAD (kept only for a type) — do not edit it expecting effect.
- Build button `.../v2/BuildActionButton.tsx`; clear `.../v2/ClearIconButton.tsx`; refresh
  `.../v2/RefreshIconButton.tsx`; pause/stop `PauseStopGroup.tsx`/`StopIconButton.tsx`.
- Modals: `.../v2/ClearConfirmModal.tsx` (preview/confirm), `platform/src/components/cockpit/
  CascadePreviewModal.tsx` (post-clear rebuild offer), `.../v2/PlanModal.tsx`.
- Hooks: `useAssetRegistry`, `useAssetStats` (`platform/src/hooks/useAssetStats.ts`), `useActiveRun`
  (`useActiveRun.ts`), `useCockpitSSE` (`useCockpitSSE.ts`), `useCockpitStatus`.
- framer-motion already in `platform/package.json:69` (^12.38.0); lucide-react available (`:76`);
  design tokens in `globals.css` + `lib/styles/marsys-theme.css`.

## §2 — WORKSTREAM A: Build correctness (global build, DAG, scopes, stale asset list)

### A.1 — Global build must walk ALL of L1–L5 in DAG order
Audit `resolveBuildPlan` (plan.ts) + the runs route for scope='global': does it select EVERY active
asset across L1–L5 and topo-sort by depends_on? Confirm:
- global scope includes every `is_active` asset in L1..L5 (NOT just one layer);
- L0 (bg_) is EXCLUDED from global/per-chart build (built only via explicit Brahmagyan-layer trigger
  by super_admin) — verify the scope filter does this;
- the topo-sort never schedules an asset before any depends_on entry, ACROSS layer boundaries (an L4
  asset depending on an L2 asset must wait for it);
- a missing/empty `depends_on` does not silently drop an asset from the plan.
FIX any gap so global build = complete L1–L5 build, dependency-correct, single press.

### A.2 — The stale / incomplete asset list (root-cause it)
The orchestrator/cockpit misses assets or has stale info. Establish the SINGLE source of truth and
reconcile every divergence:
- **3 candidate asset lists exist** — (a) `@register` decorators in writers/*.py, (b) the
  `asset_registry` DB table (what plan.ts + stats + registry route read), (c) any seed file
  (asset_registry_seed.ts) or a `build_dependencies` table. Enumerate all three; diff them.
- CONCRETE known instance (Wave-1 finding F-W1-003): `bg_dignity_reference` has a `@register` writer
  but NO `asset_registry` row (its writer cites a nonexistent migration) → cockpit can't count it.
  Find EVERY such asset (registered writer with no registry row, or registry row with no/stale
  count_sql, or registry row whose depends_on is wrong/empty).
- Produce a reconciliation: every registered writer has a correct `asset_registry` row with a correct
  chart-scoped `count_sql`, correct `depends_on`, correct `asset_type`/`asset_kind`, and correct
  layer/sort_order. This is the "cockpit truth" standard — without it the asset is invisible or
  uncountable.
- **Two-DAG problem:** `asset_registry.depends_on` (plan builder, authoritative) vs `build_dependencies`
  table (cascade preview, cosmetic). Reconcile to ONE source (depends_on); make cascade preview read
  the same source so previews match what actually builds.

### A.3 — Build/Rebuild/Refresh/Delete at all three scopes
For global + layer + asset scope, confirm each operation:
- **Build** — builds the dormant/missing assets in scope, DAG-ordered. (plan.ts action='build')
- **Rebuild** — force re-runs lit assets (skip-if-lit bypassed), delete-then-insert per asset, +
  transitive downstream marked stale & rebuilt. Verify no row accretion (N==N).
- **Refresh** — re-reads DB truth (see Workstream C — stale numbers).
- **Delete/Clear** — see Workstream D (modal correctness).
Verify the FROZEN-contract conformance of every writer the global build touches (Wave-1 F-W1-001 found
a bg_rules writer calling `conn.rollback()` directly — that can unwind a whole multi-asset build's
uncommitted work; treat direct commit/rollback/close in any writer as a BLOCKER and fix to the
contract).

## §3 — WORKSTREAM B: Live progress bars (wired to real data + motion)
ROOT CAUSE (verified): `AssetProgressBar.tsx:54-63` sets fill from `stageFill()` in
`buildStage.ts:10-23` — DISCRETE STAGE CONSTANTS (queued 3%, running 12%, substeps 15–88%, lit 100%),
explicitly "row-count-independent" (comment `AssetProgressBar.tsx:53`). Most L1 assets have NO substeps
→ stuck at a flat **12%** the entire build, then snap to 100%. The live `rows_written` IS captured
(SSE `asset.progress`/`asset.substep` → `DataAssetsView.tsx:90-106`; stats `rows_written`
`stats/route.ts:279-281`) but only printed as a TEXT label, never used for fill.
FIX:
- Drive `fillPct` from live rows: `fillPct = clamp(actualRows / target_floor * 100, 0..100)` while
  building (both `actualRows` and `target_floor`/`targetVolume` already reach the component —
  `AssetRow.tsx:264-266`). Blend with stage so it never goes backward and lands exactly 100% at lit.
- For assets with no target_floor, fall back to substep/stage fill (current behavior) but still animate.
- Use framer-motion (already imported here) for a smooth spring fill that GROWS with the row count, not
  a 12%→100% snap. Add subtle motion: a shimmer/pulse while building, a satisfying settle at 100%.
- Consider an OVERALL/global progress bar (none exists today) in CockpitHeader — aggregate
  built-assets / total-in-scope during a global build, framer-motion driven.
DEPENDENCY: the live-rows path needs the SSE/poll to actually deliver rows during the build — see
Workstream C/E (SSE heartbeat-only gap). Wire the bar to whichever source is live (SSE preferred,
poll fallback).

## §4 — WORKSTREAM C: Accurate numbers / no stale data
ROOT CAUSES (verified): (1) 30s idle poll (`useAssetStats.ts:65`) → up to 30s stale after a build
unless an SSE `run.state_change` forces refetch (`DataAssetsView.tsx:107-116`) — which never fires in
heartbeat-only SSE mode. (2) For global bg_* assets the stats route returns recorded
`asset_throughput.rows_written`, NOT a live count (`stats/route.ts:122-137`) — per-chart assets are
live+accurate. (3) `build_state_stale` divergence badge (`stats/route.ts:270-272`) surfaces a
count_sql-vs-throughput disagreement instead of reconciling. (4) registry CDN cache 60s
(`registry/route.ts`).
FIX:
- On build completion, force an immediate stats refetch (don't wait for the 30s idle tick) — wire it to
  run-completion regardless of SSE mode (poll the run state to completion as a fallback trigger).
- Decide a single truth for counts: prefer live `count_sql` where affordable; if `rows_written` is used
  for global assets, ensure clear/rebuild keeps it correct (the L1 trap: clear must reset it). Confirm
  the per_chart path already bypasses rows_written (it does — keep it).
- Make the "refresh" button force a hard refetch of stats + registry + run state (bust the 60s registry
  cache for a manual refresh).
- Reconcile or clearly explain `build_state_stale` rather than showing a bare badge.

## §5 — WORKSTREAM D: Live DAG (ArmillaryGraph reacts during build)
ROOT CAUSE (verified): the ACTIVE graph is `ArmillaryGraph.tsx` (one planet per layer). Its
`aggregate()` (`ArmillaryGraph.tsx:80`) marks a layer "building" only if some asset has
`state==='building'` — a ~1s window per fast L1 asset that the 5s poll misses, and that SSE doesn't
deliver in heartbeat-only mode (`sse/route.ts:118-148`). It IGNORES `activeRun.plan` (available,
`useActiveRun.ts:21`). The DEAD `LiveDependencyGraph.tsx:236-242` solved this by seeding building-state
from `activeRun.plan` — ArmillaryGraph has no equivalent, so during a real build it just spins slightly
faster and no planet reliably lights.
FIX:
- Seed per-asset/per-layer "building" state from `activeRun.plan` + current run position (so a node in
  the active plan that isn't yet lit reads as building/queued), like the old graph did — independent of
  catching the 1s throughput window.
- Make a building node VISIBLY distinct: pulsing glow, flowing edges to/from it, the built-fraction arc
  advancing as its assets complete. During build vs idle must look clearly different.
- Wire real-time row growth into the node (e.g. the planet's atmosphere/arc reflects rows/target while
  building) so the DAG and the progress bars tell the same live story.
- Per the user: the DAG must also distinguish service vs data nodes (see Workstream F) — and reflect
  per-asset progress, not just per-layer. Consider surfacing the asset beads (currently hidden unless
  hovered, `ArmillaryGraph.tsx:357-392`) during an active build so the asset-level DAG is visible while
  building.
- Ensure the orchestrator actually PUBLISHES `asset.state_change`/`asset.progress`/`asset.substep` to
  Pub/Sub in prod (sse/route.ts only streams these when Pub/Sub is enabled) — confirm prod has Pub/Sub
  on, else the live DAG + live bars are starved. This is a prod-config + orchestrator-emit check.

## §6 — WORKSTREAM E: Delete/clear modal — reconcile numbers + render the DAG list well
ROOT CAUSES (verified):
- **Non-reconciling totals:** `clear/route.ts` computes THREE groupings shown side-by-side without
  explaining they differ: `tables[]` "N tables" (grouped by target_table, L159-177) vs `layer_summary[]`
  "N assets" (grouped by layer, L209-223) vs `affected_assets.length` "Reset N assets" which INCLUDES
  0-row not_clearable assets (L178 vs L177). So "N tables" ≠ "N assets", and "Reset N" exceeds the
  row-contributing asset count → arithmetic visibly doesn't close
  (`ClearConfirmModal.tsx:174-224`). Asset/layer scope shows the TABLE breakdown; global shows the LAYER
  breakdown — inconsistent across the 3 delete levels.
- **Badly-dumped DAG lists:** downstream-stale shown as `slice(0,3).join(', ') + '…'` — a 3-name comma
  run with no remainder count, no structure (`ClearConfirmModal.tsx:227-234`); the CascadePreview plan
  is a FLAT vertical dump of raw `asset_id` strings, no layer headers, no human names, 70+ ids for a
  global clear (`CascadePreviewModal.tsx:166-194`); tables capped at 5 with "and N more"
  (`ClearConfirmModal.tsx:198-202`).
FIX:
- Present ONE coherent reconciling summary: rows to delete, assets affected (clearable vs not, clearly
  separated so the totals close), tables touched — with consistent grouping across asset/layer/global
  scope. Make every displayed number tie out; if an asset contributes 0 rows, show it as "0 rows (reset
  only)" so the sum is obviously correct.
- Render the affected DAG/downstream list as a STRUCTURED, human-readable tree: grouped by layer, human
  (Sanskrit+English) names not raw ids, full count with expand/collapse (not a 3-name truncation), DAG
  order preserved, framer-motion for expand. The cascade rebuild plan should show the same structured
  layer-grouped view, not a monospace id dump.
- Unify the two modals' visual language so asset/layer/global delete + the rebuild offer feel like one
  coherent flow.

## §7 — WORKSTREAM F: Service vs data asset distinction
ROOT CAUSE (verified): asset rows show only StatusDot + names (`AssetRow.tsx:243-256`); the only current
service/data difference is the progress column (ServiceHealthPill vs AssetProgressBar,
`AssetRow.tsx:260-261`). `asset_type` + `asset_kind` ALREADY reach the component
(`registry/route.ts:27,34,51`; AssetRow already branches on them L260) — no new data plumbing needed.
FIX:
- Add a small LEADING icon in the name cell (`AssetRow.tsx:246-251`): a data/storage glyph for
  data assets, a service/gear glyph for service assets, keyed off existing `asset_type`/`asset_kind`.
  House style prefers inline SVG (match SunNode / the Trash2 glyph); lucide-react is also available.
- Apply the same distinction in the DAG (ArmillaryGraph nodes/beads) so services read differently there
  too.
- Confirm the data model: which assets are services (asset_type/asset_kind='service' — e.g.
  ga_transit_anchors is service-not-storage). Make sure every asset's kind is correctly set in the
  registry (ties to A.2 reconciliation).

## §8 — Execution approach + guardrails
- Drive this via a superpowers plan doc (`platform/docs/superpowers/plans/`) — audit → fix → verify per
  workstream. Workstreams A (build correctness) + C (stale numbers) + E (delete) are CORRECTNESS;
  B (bars) + D (live DAG) + F (icons) are live-feedback/UX. Do correctness first (they gate trust),
  then the live-feedback layer (which depends on the SSE/emit fix landing).
- VERIFY each fix DB-arbitrated on non-native `1c826d5a` (SAFE); never destructive on native
  `482012f1`. Chrome MCP (read-tier → Claude-in-Chrome) for UI verification with before/after.
- FROZEN orchestrator contract — fix via conforming writers/routes/adapters; a needed contract change
  is STOP-and-raise.
- Truth bar: tracker display == DB reality; full success or explicit failure list; never silent partial
  success.
- This build-SYSTEM work is PARALLEL to the PRE_REGEN data-audit campaign. The two intersect at A.2
  (the stale asset list / registry reconciliation also surfaces in the data audit) and at the
  Wave-1/2 writer-contract findings (F-W1-001 rollback). Coordinate: the registry reconciliation should
  be done ONCE and shared.
- framer-motion (already a dep) for all new motion; design tokens from globals.css/marsys-theme.css;
  match the existing armillary/brand aesthetic — enhance, don't replace, the visual language.

## §9 — Priority order (suggested)
1. **A.2 stale asset list / registry reconciliation** — foundational; everything else (counts, DAG,
   global build completeness) depends on a correct, complete catalog.
2. **A.1 global build walks L1–L5 in DAG order** + A.3 scopes + the FROZEN-contract writer fixes.
3. **C accurate numbers / refresh** (+ confirm Pub/Sub emit so live feedback has data).
4. **E delete modal reconciliation + structured DAG list.**
5. **B live progress bars** (needs the live-rows stream from #3).
6. **D live DAG reaction** (needs #3 + plan-seeding).
7. **F service/data icons** (independent, low-risk, satisfying quick win — can slot anytime).
