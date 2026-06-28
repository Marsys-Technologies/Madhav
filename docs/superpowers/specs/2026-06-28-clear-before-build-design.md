# Clear-Before-Build + Real-Time Progress Design

**Date:** 2026-06-28  
**Status:** APPROVED FOR IMPLEMENTATION  
**Scope:** Nirmāṇa Build Tracker (Cockpit v2)

---

## Problem

1. Rebuilding assets without clearing first can produce mixed old+new data.
2. Progress bars are broken: `deriveState()` returns `'lit'` the moment any row is written during a build, making the bar show 100% at 10% completion.
3. Progress bar updates lag by 5s (stats poll interval) and the fill is barely visible at low fill percentages.
4. Layer-scope rebuild button exists but does not function correctly.

---

## Solution Overview

Five coordinated changes across backend and frontend. Each stands alone and can be reviewed independently.

---

## Change 1 — `deriveState` Bug Fix (stats/route.ts)

**File:** `platform/src/app/api/cockpit/stats/route.ts`

**Two-part fix required:**

### Part A — `fetchAllCounts` fast-path (line ~112)

The fast-path for assets with a throughput row hardcodes `state: 'dormant'` on the returned object:
```ts
// Current (buggy): state is hardcoded 'dormant' so deriveState never sees 'building'
if (!liveMode && tp != null && tp.rows_written != null) {
  return { ..., state: 'dormant' as const, ... }
}
```

Fix: pass `tp.state` through so `deriveState` receives the real throughput state:
```ts
// Fixed: keep tp.state so deriveState can distinguish 'building' from 'lit'
if (!liveMode && tp != null && tp.rows_written != null) {
  return { ..., state: (tp.state ?? 'dormant') as AssetState, ... }
}
```

### Part B — `deriveState` priority (line ~28)

**Current (buggy):**
```ts
if (actualRows != null && actualRows > 0) return 'lit'
if (throughputState === 'building') return 'building'
```

**Fixed:**
```ts
if (throughputState === 'building') return 'building'
if (actualRows != null && actualRows > 0) return 'lit'
```

**Why both parts are needed:** The fast-path sets `actual_rows = tp.rows_written` (climbing during build). If `rows_written > 0` and `state = 'dormant'` (fast-path Part A bug), `deriveState` sees `actualRows > 0` and returns `'lit'` regardless of Part B. Even after fixing Part B, if Part A still passes `state = 'dormant'`, the `throughputState` argument to `deriveState` is `'dormant'`, not `'building'`, so the priority swap in Part B has no effect. Both fixes must land together.

**Side effect (positive):** `rows_written` field in `AssetStats` is now populated during build (it gates on `derivedState === 'building'`), which `AssetProgressBar` uses for progress percentage.

---

## Change 2 — Poll Interval + Enhanced pollingStream (stats + SSE)

### 2a. Stats poll interval

**File:** `platform/src/hooks/useAssetStats.ts`

Change the build-mode poll interval from 5s to 2s:
```ts
const pollMs = isBuilding ? 2_000 : 30_000  // was 5_000
```

The stats API reads `asset_throughput.rows_written` via a single fast batch query (<100ms). 2s is safe.

### 2b. Enhanced pollingStream SSE

**File:** `platform/src/app/api/cockpit/sse/route.ts`

When Pub/Sub is disabled (`pollingStream` fallback), the current implementation only emits `run.state_change` on terminal states. Enhance it to also emit synthetic `asset.progress` events:

- Poll `SELECT asset_id, rows_written FROM asset_throughput WHERE chart_id=$1 AND state='building' ORDER BY asset_id` every 2s within the existing poll loop (no `LIMIT` — emit progress for ALL building assets so multi-asset layer builds animate all bars simultaneously).
- Track `lastRowsWritten: Map<string, number>` across ticks. For each asset where `rows_written` changed since last tick, emit: `event: asset.progress\ndata: { type: 'asset.progress', asset_id, rows_written, chart_id }\n\n`
- This flows through `DataAssetsView.handleSSEEvent → sseOverlay.actual_rows` for continuous animation of every in-flight bar.

**Combined effect:** 2s stats poll catches state; synthetic SSE events drive smooth animation between polls.

---

## Change 3 — Progress Bar Visual Fix (AssetProgressBar.tsx)

**File:** `platform/src/lib/components/cockpit/v2/AssetProgressBar.tsx`

Two visual improvements:

1. **Minimum fill width:** Replace `animate={{ width: `${fillPct}%` }}` with `animate={{ width: `${Math.max(1.5, fillPct)}%` }}`. A 0% fill is invisible; 1.5% is a visible stripe on any reasonable bar width.

2. **Build-phase fill brightness:** Change building fill from `rgba(168,124,48,0.7)` to `rgba(210,162,60,0.88)` — stays on-brand amber-gold but is more legible against the `rgba(15,12,8,0.6)` track.

---

## Change 4 — Clear-Before-Build (runs/route.ts + PlanModal.tsx)

### 4a. Backend: `runs/route.ts`

Accept an optional `clear_before?: boolean` field on the POST body.

When `clear_before: true`, the POST handler follows this strict gate order:

**Gate 0 — Active run check (existing 409 gate — unchanged, runs first).**

**Gate 1 — L0 double-confirm check (new, runs after auth/isSuperAdmin resolution, before registry queries).**
- If `scope === 'layer'` and `scope_target === 'brahmagyan'` and `force_l0` is not set: return HTTP 202 `{ requires_double_confirm: true, message: 'This will clear L0 Brahmagyan — confirm?' }` immediately. No DB reads beyond the active-run check.

**Gate 2 — Auth and scope validation (existing gates — unchanged).**

**Gate 3 — Precondition check (existing gate — runs BEFORE any clear).**
- The `bo_*` upstream check (lines 120-163) must run against the current DB state, before any clear operation, so it reflects real data. The spec's implementation must not reorder these checks.

**Then — Execute clear atomically within a single pool client transaction:**

Open a pool client with `BEGIN`:
1. **Compute clear scope** from the build scope using `filterScopeAssets`, excluding `brahmagyan` assets when `scope !== 'layer' || scope_target !== 'brahmagyan'` (or when `force_l0` is not set for brahmagyan scope).
2. **Execute DELETEs:** Use `EXPLICIT_CLEAR_OPS` + `deriveDeleteSqlFromCountSql` (same resolution as `clear/execute/route.ts`) to build and run DELETE statements within the transaction. No `preview_hash` needed.
3. **Reset throughput:** `UPDATE asset_throughput SET state='dormant', rows_written=0 WHERE chart_id=$1 AND asset_id = ANY($2)` within the same transaction.
4. **Mark downstream stale:** `UPDATE asset_throughput SET state='stale' WHERE chart_id=$1 AND asset_id = ANY($3)` within the same transaction.
5. **Insert `build_runs`** and return `run_id`.
6. `COMMIT`.

**Response:** `{ run_id, cleared_asset_count }` — same shape as today, with `cleared_asset_count` added.

### 4b. Frontend: `PlanModal.tsx`

**Button label:**
- `action === 'build'` → "Run plan" (nothing to clear)
- `action === 'rebuild'` → "Clear & Rebuild" (communicates the auto-clear)

**On confirm click:**
```ts
const r = await fetch('/api/cockpit/runs', {
  method: 'POST',
  body: JSON.stringify({
    chart_id: chartId,
    scope,
    scope_target: scopeTarget,
    action,
    clear_before: action === 'rebuild',
  }),
})
```

**Loading state during clear:** existing `loading === 'run'` path; update button text to "Clearing…" for the first 500ms (set via a flag), then "Starting…".

**L0 double-confirm:** if response is `{ requires_double_confirm: true }`, render an inline warning panel inside PlanModal with a second "Confirm — clear L0" button. That button re-posts with `force_l0: true`. No new modal needed.

---

## Change 5 — Layer-Scope Build Fix (resolveBuildPlan)

**File:** `platform/src/lib/build/plan.ts` (to be confirmed during implementation)

**Suspected cause:** `resolveBuildPlan` with `action='rebuild'` and `scope='layer'` skips already-lit assets (treating 'rebuild' as 'only build what needs it'). For a rebuild, all active assets in scope should always be included.

**Fix:** In `resolveBuildPlan`, for `action === 'rebuild'`, include all `is_active` assets whose `throughputState !== 'building'`, regardless of their current lit/stale/dormant state. The build overwrites existing data.

---

## Count Propagation (No Code Change Needed)

`LayerPanel.tsx` already computes `totalRows = assets.reduce((sum, a) => sum + (stats.get(a.asset_id)?.actual_rows ?? 0), 0)`.

With Changes 1 and 2 in place:
- **Mid-build:** `actual_rows` = `rows_written` (partial, climbing) → layer total updates every 2s.
- **Post-build:** `refetchLive()` fires on run completion → count_sql canonical counts → layer total finalizes.

No additional work needed.

---

## File Scope

| File | Change | Type |
|---|---|---|
| `platform/src/app/api/cockpit/stats/route.ts` | `deriveState` priority fix | Bug fix |
| `platform/src/hooks/useAssetStats.ts` | Poll interval 5s → 2s during build | Performance |
| `platform/src/app/api/cockpit/sse/route.ts` | pollingStream emits synthetic `asset.progress` events | Feature |
| `platform/src/lib/components/cockpit/v2/AssetProgressBar.tsx` | Min fill width + fill brightness | Visual |
| `platform/src/app/api/cockpit/runs/route.ts` | `clear_before` flag + atomic clear | Feature |
| `platform/src/lib/components/cockpit/v2/PlanModal.tsx` | "Clear & Rebuild" label + L0 double-confirm | Feature |
| `platform/src/lib/build/plan.ts` | Layer rebuild includes lit assets | Bug fix |

**Must not touch:** `clear/route.ts` (preview endpoint), `clear/execute/route.ts` (standalone clear path), `ClearConfirmModal.tsx`, `ClearIconButton.tsx`, orchestrator.

---

## L0 Brahmagyan Protection Rules

| Trigger | Auto-clear L0? | Behavior |
|---|---|---|
| Global rebuild | No | brahmagyan excluded from clear scope automatically |
| Layer rebuild (non-L0) | No | only the target layer is cleared |
| Layer rebuild (brahmagyan) | Only with double-confirm | returns `requires_double_confirm: true` on first call |
| Asset rebuild (brahmagyan asset) | No — gated at auth layer | runs route already rejects global-scope assets at asset scope |

---

## Acceptance Criteria

1. Clicking "Clear & Rebuild" on any layer or asset clears that scope's data and starts the build in a single user interaction.
2. L0 (brahmagyan) is never auto-cleared during global or non-L0 layer rebuilds.
3. L0 rebuild shows a second confirmation before clearing.
4. Progress bar shows correct partial fill (not 100%) while an asset is building.
5. Progress bar fill advances on every stats poll (every 2s during build).
6. Layer row total in `LayerPanel` header counts up live during a build.
7. Layer-scope rebuild button successfully enqueues and runs all assets in the layer.
8. All pre-existing TypeScript build errors remain only in test files; no new errors introduced.
