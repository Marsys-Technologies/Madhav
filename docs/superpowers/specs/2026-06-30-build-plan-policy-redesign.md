# Build Plan Policy Redesign
**Date:** 2026-06-30  
**Status:** APPROVED FOR IMPLEMENTATION  
**Scope:** `platform/src/lib/build/plan.ts`, `/api/cockpit/plan/route.ts`, `AssetRow.tsx`, `CascadePreviewModal.tsx` (split), Python orchestrator build execution

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

**Single asset (`scope='asset'`):**
```
candidates = [scope_target]
pre-flight:
  for each dep in scope_target.depends_on:
    if dep.state not in {lit, service_ok} → add to blockers
  if blockers non-empty → return { status: 'blocked', blockers }
  else → return { status: 'ok', plan_waves: [[scope_target]] }
```

**Layer (`scope='layer'`):**
```
candidates = all assets where asset.layer == scope_target
pre-flight:
  for each candidate:
    for each dep in candidate.depends_on where dep.layer != scope_target:
      if dep.state not in {lit, service_ok} → add to blockers (dep → required_by candidate)
  if blockers non-empty → return { status: 'blocked', blockers }
  else:
    compute plan_waves from intra-layer DAG (cross-layer deps already verified)
    return { status: 'ok', plan_waves }
```

**Global (`scope='global'`):**
```
candidates = all assets, all layers
no pre-flight gate
compute plan_waves from full DAG
return { status: 'ok', plan_waves }
(runtime: each asset checks its deps at execution time; first error halts run)
```

### 2. New Return Type

```typescript
// service_down added as a first-class AssetState
export type AssetState =
  | 'dormant' | 'building' | 'lit' | 'stale' | 'error' | 'service_ok' | 'service_down'

export interface BlockerEntry {
  dep_asset_id: AssetId        // the dep that is not ready
  dep_state: AssetState        // its current state
  required_by: AssetId[]       // which candidates in this scope need it
}

export interface BuildPlan {
  status: 'ok' | 'blocked'
  plan_waves: AssetId[][]      // empty outer array when blocked
  blockers: BlockerEntry[]     // empty when ok
  estimated_seconds: number | null
}
```

**Removed from current `BuildPlan`:**
- `plan: AssetId[]` — replaced by `plan_waves: AssetId[][]`; callers needing flat list use `plan_waves.flat()`
- `includes_upstream_count` — no longer meaningful (no auto-pull upstream)
- `blocked_assets` — replaced by top-level `blockers`

### 3. Wave Computation Algorithm

Waves determine which assets within a scope can execute in parallel.

```
wave_assignment = {}
for each candidate (topo-sorted):
  in_scope_deps = candidate.depends_on filtered to candidates set
  if in_scope_deps is empty:
    wave_assignment[candidate] = 0
  else:
    wave_assignment[candidate] = max(wave_assignment[dep] for dep in in_scope_deps) + 1

plan_waves = group candidates by wave_assignment value, ordered by wave number
```

For **single asset**: always `[[scope_target]]` — one wave, one asset.  
For **layer**: only intra-layer deps determine wave levels (cross-layer deps pre-flighted, treated as ready).  
For **global**: all deps (including cross-layer) determine wave levels.

### 4. Python Orchestrator — Parallel Wave Execution

**Payload sent from TypeScript to Python changes:**

Before:
```json
{ "chart_id": "...", "plan": ["ka_kalasutra", "ka_vighnakara", "ka_sangam"] }
```

After:
```json
{ "chart_id": "...", "plan_waves": [["ka_kalasutra", "ka_vighnakara"], ["ka_sangam"]] }
```

**Python execution per wave:**
```python
for wave in plan_waves:
    results = await asyncio.gather(*[run_asset(chart_id, asset_id) for asset_id in wave],
                                   return_exceptions=True)
    errors = [r for r in results if isinstance(r, Exception)]
    if errors:
        # Global scope: halt immediately
        # Layer scope: halt immediately (pre-flight already guaranteed cross-layer readiness)
        raise BuildHaltedError(errors)
```

Assets within a wave run concurrently. The next wave starts only when all assets in the current wave succeed.

### 5. Frontend Changes

**`AssetRow.tsx` — `handleRebuildClick()`:**
- Calls `/api/cockpit/plan` (unchanged)
- If `status: 'blocked'` → set `pendingBlock` state → open `BuildBlockedModal`
- If `status: 'ok'` → set `pendingCascade` state → open `BuildConfirmModal`

**`CascadePreviewModal.tsx` → split into two components:**

`BuildConfirmModal`:
- Shows in-scope assets only (`plan_waves.flat()`) — no cross-layer grouping
- Estimated build time if available
- Confirm / Cancel buttons
- For single asset: shows one row; for layer: shows layer's assets grouped; for global: shows all

`BuildBlockedModal`:
- Header: "Cannot build — dependencies not ready"
- Lists each `BlockerEntry`: dep name, state badge (stale / dormant / error / service down), which assets in scope require it
- Dismiss-only — no confirm option
- Visual treatment: amber/red tone, distinct from the confirm dialog

**`/api/cockpit/plan/route.ts`:**
- Returns new `BuildPlan` shape
- Computes `plan_waves` via wave algorithm before responding
- `plan_waves` sent to orchestrator on confirm; `plan_waves.flat()` used for display

---

## Removals

| What | Where | Why |
|---|---|---|
| Transitive downstream in `action='rebuild'` (lines 184–192 of `plan.ts`) | `plan.ts` | Replaced by single-asset-only policy |
| Auto-pull dormant upstream (lines 202–256 of `plan.ts`) | `plan.ts` | Pre-flight gate supersedes this |
| `checkStalenessGate()` export | `plan.ts` | Superseded by pre-flight embedded in `resolveBuildPlan()` |
| `includes_upstream_count` | `BuildPlan` type + API response | No longer meaningful |
| `blocked_assets` field | `BuildPlan` type + API response | Replaced by `blockers` |

---

## Files to Change

| File | Change |
|---|---|
| `platform/src/lib/build/plan.ts` | New scope semantics, pre-flight gate, wave computation, new return type |
| `platform/src/app/api/cockpit/plan/route.ts` | Return new `BuildPlan` shape; send `plan_waves` |
| `platform/src/lib/components/cockpit/v2/AssetRow.tsx` | Handle `status: 'blocked'` vs `status: 'ok'` |
| `platform/src/components/cockpit/CascadePreviewModal.tsx` | Split into `BuildConfirmModal` + `BuildBlockedModal` |
| `platform/python-sidecar/orchestrator/` | Accept `plan_waves`, execute waves in parallel with asyncio.gather, halt on error |

---

## Out of Scope

- Changes to staleness propagation (remains as-is — the staleness marking feeds the pre-flight gate)
- Changes to the `build` vs `rebuild` distinction within the new policy (both follow the same pre-flight and scope rules)
- Exposing `plan_waves` structure in the Nirmana UI (waves are an execution detail; UI shows flat asset list)
- Service asset rebuild mechanics (services are always-on; they appear only as pre-flight dep targets, never as build candidates)
