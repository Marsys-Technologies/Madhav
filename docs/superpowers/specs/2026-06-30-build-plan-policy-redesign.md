# Build Plan Policy Redesign
**Date:** 2026-06-30  
**Status:** APPROVED FOR IMPLEMENTATION  
**Scope:** `platform/src/lib/build/plan.ts`, `/api/cockpit/plan/route.ts`, `/api/cockpit/runs/route.ts`, `AssetRow.tsx`, `CascadePreviewModal.tsx` (split), Python orchestrator wire payload

---

## Problem Statement

The current `resolveBuildPlan()` implements a "90/10 semantic": rebuilding a single asset cascades to its full transitive downstream across all layers. Triggering a rebuild on `ka_sangam` (Kāla, L3) produces a dialog listing 7 Kāla assets + all 9 Phala assets + all Mīmāṃsā assets. This violates the principle of scoped intentionality — the operator asked to rebuild one asset, not three layers.

Additionally, there is no pre-flight gate: the current system attempts to build and fails at runtime if upstream dependencies are not ready. The new design surfaces dependency problems before the build starts.

---

## Core Policy

### Three scopes, three contracts

| Scope | Plan contains | Pre-flight gate | Execution | On failure |
|---|---|---|---|---|
| Single asset | Only that asset | ALL direct deps (any layer, any service) must be ready | Immediate or block | Block, flag all bad deps |
| Layer | All assets in that layer | All cross-layer deps of all layer assets must be ready | Intra-layer DAG waves, parallel where independent | Block entire layer pre-flight |
| Global | All assets, all layers | None — runtime enforces dep readiness | Full DAG waves, parallel where independent | Halt on first asset error |

### Blocking conditions (uniform across scopes)

A dependency is **not ready** if its state is any of:
- `stale` — data exists but is outdated
- `dormant` — never built, no data
- `error` — build failed
- `service_down` — service asset is not LIVE

A dependency is **ready** if its state is `lit` or `service_ok`.

There is no "warn but allow" path. If any dependency is not ready, the plan does not proceed.

---

## Design

### 1. Plan Resolution — New Scope Semantics

**Action coverage:**

This spec redesigns `build` and `rebuild` only. The `update` and `cascade` actions retain their current implementation in `plan.ts` (lines 173–198) unchanged. Both will return the new `BuildPlan` shape (`status`, `plan_waves`, `blockers`) but always with `status: 'ok'` and no pre-flight gate — their existing behavior is correct and out of scope here.

**`build` vs `rebuild` action distinction:**
- `action='build'`: include the target only if its current state is `dormant` or `error`. A `lit` asset under `build` action is a no-op (returns `plan_waves: []`, no pre-flight run).
- `action='rebuild'`: include the target regardless of current state (force re-run).
- Both actions apply the same pre-flight gate and scope semantics described below.

**Single asset (`scope='asset'`):**
```
if action='build' and target.state is lit → return { status: 'ok', plan_waves: [] }
candidates = [scope_target]
pre-flight:
  for each dep in scope_target.depends_on:
    if dep.state not in {lit, service_ok} → add to blockers
  if blockers non-empty → return { status: 'blocked', blockers, estimated_seconds: null }
  else → return { status: 'ok', plan_waves: [[scope_target]] }
```

**Layer (`scope='layer'`):**
```
candidates = all assets where asset.layer == scope_target
  (for action='build': filter to dormant/error only;
   for action='rebuild': all assets in layer)
pre-flight:
  for each candidate:
    for each dep in candidate.depends_on where dep.layer != scope_target:
      if dep.state not in {lit, service_ok} → add to blockers (dep → required_by candidate)
  if blockers non-empty → return { status: 'blocked', blockers, estimated_seconds: null }
  else:
    compute plan_waves from intra-layer DAG (cross-layer deps already verified)
    return { status: 'ok', plan_waves }
```

Note: intra-layer deps are not part of the pre-flight — they are handled by DAG ordering within execution. If asset A in the layer depends on asset B in the same layer, both are candidates and B will be placed in an earlier wave than A.

**Global (`scope='global'`):**
```
candidates = all assets, all layers
  (for action='build': filter to dormant/error only;
   for action='rebuild': all assets)
no pre-flight gate
compute plan_waves from full DAG (cycle-detecting topo-sort)
return { status: 'ok', plan_waves }
(runtime: orchestrator halts on first asset error; no new waves start after a failure)
```

**L0 (Brahmagyan) assets:** If a cross-layer dep that is `dormant` or `error` is a `bg_*` (L0) asset, the `BlockerEntry` message must surface a specific guidance string: `"L0 dependency not built — run the Brahmagyan layer first"`. This preserves the operator guidance previously in the `blocked_assets[].reason` field.

### 2. New Return Type

```typescript
// service_down added as a first-class AssetState
export type AssetState =
  | 'dormant' | 'building' | 'lit' | 'stale' | 'error' | 'service_ok' | 'service_down'

export interface BlockerEntry {
  dep_asset_id: AssetId        // the dep that is not ready
  dep_state: AssetState        // its current state
  required_by: AssetId[]       // which candidates in this scope need it
  guidance?: string            // optional: shown for L0 dormant deps
}

export interface BuildPlan {
  status: 'ok' | 'blocked'
  plan_waves: AssetId[][]      // empty outer array when blocked or when build no-ops a lit asset
  blockers: BlockerEntry[]     // empty when ok
  estimated_seconds: number | null  // always null when status is 'blocked'
}
```

**Removed from current `BuildPlan`:**
- `plan: AssetId[]` — replaced by `plan_waves: AssetId[][]`; callers needing a flat list use `plan_waves.flat()`
- `includes_upstream_count` — no longer meaningful (no auto-pull upstream)
- `blocked_assets` — replaced by top-level `blockers`

### 3. Wave Computation Algorithm

Waves determine which assets within a scope can execute in parallel. Wave computation uses the existing `topoSort()` function in `plan.ts`, which is **cycle-detecting** (throws `Error('Cycle detected involving asset: ...')` on a cycle). A cycle in `asset_registry.depends_on` is a data-integrity error; the plan endpoint returns HTTP 500 with the cycle diagnostic — it is not a user-recoverable condition.

```
// Input: candidates (already topo-sorted, cycle-free)
wave_assignment = {}
for each candidate in topo-sorted order:
  in_scope_deps = candidate.depends_on ∩ candidates_set
  if in_scope_deps is empty:
    wave_assignment[candidate] = 0
  else:
    wave_assignment[candidate] = max(wave_assignment[dep] for dep in in_scope_deps) + 1

plan_waves = group candidates by wave_assignment value, ordered by wave number
```

For **single asset**: always `[[scope_target]]` — one wave, one asset.  
For **layer**: only intra-layer deps determine wave levels (cross-layer deps pre-flighted and treated as ready for wave computation).  
For **global**: all deps (including cross-layer) determine wave levels.

### 4. Python Orchestrator — Wire Payload Change Only

The Python orchestrator (`execute_dag` / `_schedule_parallel`) **already implements wave-parallel execution** internally using `ThreadPoolExecutor`: assets whose deps are satisfied run concurrently, and each asset waits for its upstream before starting. No change to the orchestrator's execution model is needed.

The only orchestrator change is the wire payload format accepted from TypeScript:

**Before:**
```json
{ "chart_id": "...", "plan": ["ka_kalasutra", "ka_vighnakara", "ka_sangam"] }
```

**After:**
```json
{ "chart_id": "...", "plan": ["ka_kalasutra", "ka_vighnakara", "ka_sangam"],
  "plan_waves": [["ka_kalasutra", "ka_vighnakara"], ["ka_sangam"]] }
```

`plan` (flat list) is kept for backward-compatibility and is what the orchestrator uses for execution order. `plan_waves` is stored alongside for auditability and potential future use. The orchestrator's existing dep-graph logic determines actual parallelism — it does not need to read `plan_waves` to function correctly.

**Halt-on-error for global scope:** The orchestrator already marks a `build_run` as failed when any asset errors. No new logic is required — the existing `on_complete` callback + error propagation handles this. The TypeScript layer communicates the global halt-on-error expectation via documentation, not a new wire field.

### 5. Frontend Changes

**`AssetRow.tsx` — `handleRebuildClick()`:**
- Calls `/api/cockpit/plan` (unchanged)
- If `status: 'blocked'` → set `pendingBlock` state → open `BuildBlockedModal`
- If `status: 'ok'` and `plan_waves` is non-empty → set `pendingCascade` state → open `BuildConfirmModal`
- If `status: 'ok'` and `plan_waves` is empty → no-op (asset already lit, `build` action on a lit asset)

**`CascadePreviewModal.tsx` → split into two components:**

`BuildConfirmModal`:
- Shows in-scope assets only (`plan_waves.flat()`) — no cross-layer grouping
- Estimated build time if available (`estimated_seconds`)
- Confirm / Cancel buttons
- For single asset: shows one row; for layer: shows layer's assets; for global: shows all

`BuildBlockedModal`:
- Header: "Cannot build — dependencies not ready"
- Lists each `BlockerEntry`: dep name, state badge (`stale` / `dormant` / `error` / `service down`), which assets in scope require it
- For L0 blockers: renders `guidance` string ("run the Brahmagyan layer first") beneath the dep name
- Dismiss-only — no confirm option
- Visual treatment: amber/red tone, distinct from the confirm dialog

**`/api/cockpit/plan/route.ts`:**
- Returns new `BuildPlan` shape (`status`, `plan_waves`, `blockers`, `estimated_seconds`)
- Computes `plan_waves` via wave algorithm
- `estimated_seconds` computed from `plan_waves.flat()`; set to `null` when `status: 'blocked'`

**`/api/cockpit/runs/route.ts`:**
- Currently calls `checkStalenessGate()` as "Gate 4" before inserting `build_run`
- Replace Gate 4 with a check against the `BuildPlan.blockers` returned by `resolveBuildPlan()` — if `status: 'blocked'`, reject the run request with HTTP 422 and return `blockers`
- This ensures the stale-upstream guard still exists at the execution layer, not just at the plan-preview layer; direct API callers (bypassing the UI) are still protected

---

## Removals

| What | Where | Why |
|---|---|---|
| Transitive downstream in `action='rebuild'` (lines 184–192 of `plan.ts`) | `plan.ts` | Replaced by single-asset-only policy |
| Auto-pull dormant upstream (lines 202–256 of `plan.ts`) | `plan.ts` | Pre-flight gate supersedes this |
| `checkStalenessGate()` export | `plan.ts` | Superseded by pre-flight in `resolveBuildPlan()`; Gate 4 in `runs/route.ts` replaced inline |
| `plan.staleness-gate.test.ts` | `platform/src/lib/build/__tests__/` | Tests for retired function; replace with pre-flight gate tests |
| `includes_upstream_count` | `BuildPlan` type + API response | No longer meaningful |
| `blocked_assets` field | `BuildPlan` type + API response | Replaced by `blockers` |

---

## Files to Change

| File | Change |
|---|---|
| `platform/src/lib/build/plan.ts` | New scope semantics, pre-flight gate, wave computation, new return type; retire `checkStalenessGate` export |
| `platform/src/app/api/cockpit/plan/route.ts` | Return new `BuildPlan` shape with `plan_waves`, `blockers`, `estimated_seconds: null` on blocked |
| `platform/src/app/api/cockpit/runs/route.ts` | Replace `checkStalenessGate` Gate 4 with inline `blockers` check from `resolveBuildPlan()`; adapt all downstream uses of the old flat `plan` array to `plan_waves.flat()` (DB inserts, `invokeRunJob`, response body); rename `blocked_assets` references to `blockers`; update `plan.length === 0` guard to `plan_waves.flat().length === 0` |
| `platform/src/lib/build/__tests__/plan.staleness-gate.test.ts` | Delete; replace with new pre-flight gate test file |
| `platform/src/lib/components/cockpit/v2/AssetRow.tsx` | Handle `status: 'blocked'` vs `status: 'ok'`; handle empty `plan_waves` no-op |
| `platform/src/components/cockpit/CascadePreviewModal.tsx` | Split into `BuildConfirmModal` + `BuildBlockedModal` |
| `platform/python-sidecar/` (build run handler) | Accept optional `plan_waves` in payload alongside `plan`; store for auditability |

---

## Out of Scope

- Changes to staleness propagation (remains as-is — staleness marking feeds the pre-flight gate)
- Changes to the orchestrator's execution model (existing `execute_dag` + `ThreadPoolExecutor` already handles wave-parallel execution)
- Exposing `plan_waves` wave structure in the Nirmana UI (waves are an execution detail; UI shows flat asset list)
- Service asset rebuild mechanics (services are always-on; they appear only as pre-flight dep targets, never as build candidates)
