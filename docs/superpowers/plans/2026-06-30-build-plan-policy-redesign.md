# Build Plan Policy Redesign — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the "rebuild one asset → cascade to all downstream layers" behavior with scoped, pre-flight-gated builds: single-asset rebuilds only touch that asset, layer rebuilds stay within the layer, and nothing starts if upstream dependencies are not ready.

**Architecture:** All policy logic lives in `plan.ts` (`preflight()` + `computeWaves()` + updated `resolveBuildPlan()`). The API routes return the new `BuildPlan` shape (`status`, `plan_waves`, `blockers`). Two new modal components replace `CascadePreviewModal`: `BuildBlockedModal` (dep-not-ready gate) and `BuildConfirmModal` (scoped confirmation). The Python orchestrator is unchanged — it reads a flat `plan` list from the DB and already handles parallel execution internally.

**Tech Stack:** TypeScript, Next.js App Router, Vitest, React, Tailwind CSS, PostgreSQL (via `pg`)

**Spec:** `docs/superpowers/specs/2026-06-30-build-plan-policy-redesign.md`

---

## File Map

| Status | File | Role |
|---|---|---|
| Modify | `platform/src/lib/build/plan.ts` | Core types + all build policy logic |
| Delete | `platform/src/lib/build/__tests__/plan.staleness-gate.test.ts` | Retiring `checkStalenessGate` |
| Create | `platform/src/lib/build/__tests__/plan.preflight.test.ts` | Tests for pre-flight gate |
| Create | `platform/src/lib/build/__tests__/plan.waves.test.ts` | Tests for wave computation |
| Modify | `platform/src/app/api/cockpit/plan/route.ts` | Return new `BuildPlan` shape |
| Modify | `platform/src/app/api/cockpit/runs/route.ts` | Replace Gate 4; adapt `plan_waves.flat()` usage |
| Create | `platform/src/components/cockpit/BuildBlockedModal.tsx` | Blocked-dep modal (dismiss-only) |
| Create | `platform/src/components/cockpit/BuildConfirmModal.tsx` | Scoped-confirm modal |
| Modify | `platform/src/lib/components/cockpit/v2/AssetRow.tsx` | Handle `blocked`/`ok`/no-op states |

---

## Task 1: Update `plan.ts` types — add `service_down`, new `BuildPlan`, `BlockerEntry`

**Files:**
- Modify: `platform/src/lib/build/plan.ts`
- Delete: `platform/src/lib/build/__tests__/plan.staleness-gate.test.ts`

- [ ] **Step 1: Delete the staleness-gate test file**

```bash
rm platform/src/lib/build/__tests__/plan.staleness-gate.test.ts
```

- [ ] **Step 2: Update types in `plan.ts`**

Replace lines 1–30 (the type block at the top of the file) **AND delete the existing non-exported `ResolveBuildPlanArgs` interface at lines 67–73** (it becomes the exported version below). Leaving both copies causes a TypeScript duplicate-identifier error. The full replacement block:

```typescript
export type AssetId = string
export type AssetState =
  | 'dormant' | 'building' | 'lit' | 'stale' | 'error' | 'service_ok' | 'service_down'
export type BuildAction = 'build' | 'update' | 'rebuild' | 'cascade'
export type BuildScope = 'global' | 'layer' | 'asset'

export interface RegistryEntry {
  asset_id: AssetId
  layer: string
  depends_on: AssetId[]
  estimated_seconds: number | null
}

export interface ThroughputEntry {
  asset_id: AssetId
  state: AssetState
}

export interface BlockerEntry {
  dep_asset_id: AssetId
  dep_state: AssetState
  required_by: AssetId[]    // which in-scope assets need this dep
  guidance?: string         // non-empty for L0 dormant/error deps
}

export interface BuildPlan {
  status: 'ok' | 'blocked'
  plan_waves: AssetId[][]   // empty when blocked or when build no-ops a lit asset
  blockers: BlockerEntry[]  // empty when ok
  estimated_seconds: number | null  // always null when status is 'blocked'
}

export interface StalenessGateEntry {
  asset_id: AssetId
  state: string
  required_by: AssetId[]
}

export interface ResolveBuildPlanArgs {
  scope: BuildScope
  scope_target: string | null
  action: BuildAction
  registry: RegistryEntry[]
  throughput: Map<AssetId, ThroughputEntry>
}
```

Note: `StalenessGateEntry` stays for now — it is removed in Task 4 once `checkStalenessGate` is deleted.

- [ ] **Step 3: Verify TypeScript compiles**

```bash
cd platform && npx tsc --noEmit
```

Expected: zero errors (the removed test file no longer imports `checkStalenessGate`, but `plan.ts` itself still exports it — that's fine for now; it gets removed in Task 4).

- [ ] **Step 4: Commit**

```bash
git add platform/src/lib/build/plan.ts
git rm platform/src/lib/build/__tests__/plan.staleness-gate.test.ts
git commit -m "refactor(plan): update types — service_down, BlockerEntry, new BuildPlan shape"
```

---

## Task 2: Implement `preflight()` helper + tests

**Files:**
- Modify: `platform/src/lib/build/plan.ts`
- Create: `platform/src/lib/build/__tests__/plan.preflight.test.ts`

> **TDD note:** Tests call `preflight()` directly (not through `resolveBuildPlan`) so Task 2 is fully self-contained. `preflight()` must be exported from `plan.ts`. The `resolveBuildPlan` wiring happens in Task 4.

- [ ] **Step 1: Write the failing tests**

Create `platform/src/lib/build/__tests__/plan.preflight.test.ts`:

```typescript
import { describe, it, expect } from 'vitest'
import { preflight } from '../plan'
import type { RegistryEntry, ThroughputEntry } from '../plan'

function reg(asset_id: string, layer: string, depends_on: string[] = []): RegistryEntry {
  return { asset_id, layer, depends_on, estimated_seconds: null }
}
function tp(asset_id: string, state: string): [string, ThroughputEntry] {
  return [asset_id, { asset_id, state: state as ThroughputEntry['state'] }]
}

const REGISTRY = [
  reg('bg_texts', 'brahmagyan'),
  reg('ga_positions', 'ganita', ['bg_texts']),
  reg('bo_bimba', 'bodha', ['ga_positions']),
  reg('ka_sangam', 'kala', ['bo_bimba', 'ga_positions']),
  reg('ka_vighnakara', 'kala', ['ka_sangam']),
  reg('ka_kalasutra', 'kala', ['bo_bimba']),
]

// preflight() is called with (candidates, scope, scope_target, registry, throughput)
describe('preflight() — single asset scope', () => {
  it('blocks when a direct dep is stale', () => {
    const throughput = new Map([
      tp('bg_texts', 'lit'), tp('ga_positions', 'lit'), tp('bo_bimba', 'stale'),
    ])
    const result = preflight(['ka_sangam'], 'asset', 'ka_sangam', REGISTRY, throughput)
    expect(result).toHaveLength(1)
    expect(result[0].dep_asset_id).toBe('bo_bimba')
    expect(result[0].dep_state).toBe('stale')
    expect(result[0].required_by).toContain('ka_sangam')
  })

  it('blocks when a direct dep is dormant', () => {
    const throughput = new Map([tp('ga_positions', 'lit'), tp('bo_bimba', 'dormant')])
    const result = preflight(['ka_sangam'], 'asset', 'ka_sangam', REGISTRY, throughput)
    expect(result[0].dep_state).toBe('dormant')
  })

  it('blocks when a direct dep is in error', () => {
    const throughput = new Map([tp('ga_positions', 'lit'), tp('bo_bimba', 'error')])
    const result = preflight(['ka_sangam'], 'asset', 'ka_sangam', REGISTRY, throughput)
    expect(result[0].dep_state).toBe('error')
  })

  it('blocks when a direct dep is service_down', () => {
    const throughput = new Map([tp('ga_positions', 'lit'), tp('bo_bimba', 'service_down')])
    const result = preflight(['ka_sangam'], 'asset', 'ka_sangam', REGISTRY, throughput)
    expect(result[0].dep_state).toBe('service_down')
  })

  it('returns empty when all deps are lit', () => {
    const throughput = new Map([tp('ga_positions', 'lit'), tp('bo_bimba', 'lit')])
    const result = preflight(['ka_sangam'], 'asset', 'ka_sangam', REGISTRY, throughput)
    expect(result).toEqual([])
  })

  it('treats service_ok as ready', () => {
    const throughput = new Map([tp('ga_positions', 'service_ok'), tp('bo_bimba', 'lit')])
    const result = preflight(['ka_sangam'], 'asset', 'ka_sangam', REGISTRY, throughput)
    expect(result).toEqual([])
  })

  it('L0 dormant dep includes guidance message', () => {
    const throughput = new Map([tp('bg_texts', 'dormant')])
    const result = preflight(['ga_positions'], 'asset', 'ga_positions', REGISTRY, throughput)
    expect(result).toHaveLength(1)
    expect(result[0].dep_asset_id).toBe('bg_texts')
    expect(result[0].guidance).toBe("L0 dependency not built — run the Brahmagyan layer first")
  })
})

describe('preflight() — layer scope', () => {
  it('blocks when any cross-layer dep is stale', () => {
    const throughput = new Map([tp('ga_positions', 'stale'), tp('bo_bimba', 'lit')])
    const candidates = ['ka_sangam', 'ka_vighnakara', 'ka_kalasutra']
    const result = preflight(candidates, 'layer', 'kala', REGISTRY, throughput)
    const blocker = result.find(b => b.dep_asset_id === 'ga_positions')
    expect(blocker).toBeDefined()
    expect(blocker?.required_by).toContain('ka_sangam')
    expect(blocker?.required_by).toContain('ka_kalasutra')
  })

  it('does NOT flag intra-layer deps — DAG handles them', () => {
    // ka_vighnakara depends on ka_sangam (same layer) — not a pre-flight blocker
    const throughput = new Map([tp('ga_positions', 'lit'), tp('bo_bimba', 'lit')])
    const candidates = ['ka_sangam', 'ka_vighnakara', 'ka_kalasutra']
    const result = preflight(candidates, 'layer', 'kala', REGISTRY, throughput)
    expect(result).toEqual([])
  })
})
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd platform && npx vitest run src/lib/build/__tests__/plan.preflight.test.ts
```

Expected: all tests FAIL with import errors or assertion errors (pre-flight not yet implemented).

- [ ] **Step 3: Add `export function preflight()` to `plan.ts`**

Add this function after `computeUpstreamClosure()` (around line 155). It must be exported so the tests can call it directly:

```typescript
const READY_STATES = new Set<AssetState>(['lit', 'service_ok'])

/**
 * Checks whether all relevant deps of `candidates` are ready.
 * For layer scope: only cross-layer deps are checked (intra-layer handled by DAG).
 * For asset/global scope: all direct deps of each candidate are checked.
 * Returns an array of BlockerEntry — empty means pre-flight passed.
 */
function preflight(
  candidates: AssetId[],
  scope: BuildScope,
  scope_target: string | null,
  registry: RegistryEntry[],
  throughput: Map<AssetId, ThroughputEntry>
): BlockerEntry[] {
  const regMap = new Map(registry.map(r => [r.asset_id, r]))
  const blockerMap = new Map<AssetId, BlockerEntry>()

  for (const candidate of candidates) {
    const entry = regMap.get(candidate)
    if (!entry) continue

    for (const dep of entry.depends_on) {
      // Layer scope: skip intra-layer deps — DAG will order them correctly
      if (scope === 'layer' && scope_target) {
        const depEntry = regMap.get(dep)
        if (depEntry?.layer === scope_target) continue
      }

      const depState = throughput.get(dep)?.state ?? 'dormant'
      if (READY_STATES.has(depState)) continue

      if (!blockerMap.has(dep)) {
        const isL0 = regMap.get(dep)?.layer === 'brahmagyan'
        blockerMap.set(dep, {
          dep_asset_id: dep,
          dep_state: depState,
          required_by: [],
          ...(isL0 ? { guidance: 'L0 dependency not built — run the Brahmagyan layer first' } : {}),
        })
      }
      blockerMap.get(dep)!.required_by.push(candidate)
    }
  }

  return Array.from(blockerMap.values())
}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd platform && npx vitest run src/lib/build/__tests__/plan.preflight.test.ts
```

Expected: all tests PASS. Tests call `preflight()` directly — no dependency on `resolveBuildPlan()` wiring.

- [ ] **Step 5: Commit**

```bash
git add platform/src/lib/build/plan.ts \
        platform/src/lib/build/__tests__/plan.preflight.test.ts
git commit -m "feat(plan): add preflight() helper + tests — blocks on unready deps"
```

---

## Task 3: Implement `computeWaves()` helper + tests

**Files:**
- Modify: `platform/src/lib/build/plan.ts`
- Create: `platform/src/lib/build/__tests__/plan.waves.test.ts`

- [ ] **Step 1: Write the failing tests**

Create `platform/src/lib/build/__tests__/plan.waves.test.ts`:

```typescript
import { describe, it, expect } from 'vitest'
import { resolveBuildPlan } from '../plan'
import type { RegistryEntry, ThroughputEntry } from '../plan'

function reg(asset_id: string, layer: string, depends_on: string[] = []): RegistryEntry {
  return { asset_id, layer, depends_on, estimated_seconds: null }
}
function tp(asset_id: string, state: string): [string, ThroughputEntry] {
  return [asset_id, { asset_id, state: state as ThroughputEntry['state'] }]
}

describe('computeWaves — layer scope', () => {
  it('two independent assets land in wave 0', () => {
    const registry = [
      reg('bo_x', 'bodha'),
      reg('ka_a', 'kala', ['bo_x']),
      reg('ka_b', 'kala', ['bo_x']),
    ]
    const throughput = new Map([tp('bo_x', 'lit')])
    const result = resolveBuildPlan({
      scope: 'layer', scope_target: 'kala', action: 'rebuild',
      registry, throughput,
    })
    expect(result.status).toBe('ok')
    expect(result.plan_waves).toHaveLength(1)
    expect(result.plan_waves[0].sort()).toEqual(['ka_a', 'ka_b'])
  })

  it('chain A → B → C produces three waves', () => {
    const registry = [
      reg('ka_a', 'kala', []),
      reg('ka_b', 'kala', ['ka_a']),
      reg('ka_c', 'kala', ['ka_b']),
    ]
    const result = resolveBuildPlan({
      scope: 'layer', scope_target: 'kala', action: 'rebuild',
      registry, throughput: new Map(),
    })
    expect(result.status).toBe('ok')
    expect(result.plan_waves).toHaveLength(3)
    expect(result.plan_waves[0]).toEqual(['ka_a'])
    expect(result.plan_waves[1]).toEqual(['ka_b'])
    expect(result.plan_waves[2]).toEqual(['ka_c'])
  })

  it('diamond pattern: A → B, A → C, B → D, C → D', () => {
    const registry = [
      reg('ka_a', 'kala', []),
      reg('ka_b', 'kala', ['ka_a']),
      reg('ka_c', 'kala', ['ka_a']),
      reg('ka_d', 'kala', ['ka_b', 'ka_c']),
    ]
    const result = resolveBuildPlan({
      scope: 'layer', scope_target: 'kala', action: 'rebuild',
      registry, throughput: new Map(),
    })
    expect(result.status).toBe('ok')
    expect(result.plan_waves[0]).toEqual(['ka_a'])
    expect(result.plan_waves[1].sort()).toEqual(['ka_b', 'ka_c'])
    expect(result.plan_waves[2]).toEqual(['ka_d'])
  })

  it('cross-layer deps do not affect wave assignment for layer scope', () => {
    // bo_x is cross-layer (pre-flighted); within kala, ka_a has no intra-layer deps → wave 0
    const registry = [
      reg('bo_x', 'bodha'),
      reg('ka_a', 'kala', ['bo_x']),
      reg('ka_b', 'kala', ['ka_a']),
    ]
    const throughput = new Map([tp('bo_x', 'lit')])
    const result = resolveBuildPlan({
      scope: 'layer', scope_target: 'kala', action: 'rebuild',
      registry, throughput,
    })
    expect(result.plan_waves[0]).toEqual(['ka_a'])
    expect(result.plan_waves[1]).toEqual(['ka_b'])
  })
})

describe('computeWaves — single asset scope', () => {
  it('always produces exactly one wave with one asset', () => {
    const registry = [reg('bo_x', 'bodha'), reg('ka_a', 'kala', ['bo_x'])]
    const throughput = new Map([tp('bo_x', 'lit')])
    const result = resolveBuildPlan({
      scope: 'asset', scope_target: 'ka_a', action: 'rebuild',
      registry, throughput,
    })
    expect(result.plan_waves).toEqual([['ka_a']])
  })
})

describe('computeWaves — global scope', () => {
  it('cross-layer deps determine wave order', () => {
    const registry = [
      reg('ga_a', 'ganita', []),
      reg('bo_a', 'bodha', ['ga_a']),
    ]
    const result = resolveBuildPlan({
      scope: 'global', scope_target: null, action: 'rebuild',
      registry, throughput: new Map(),
    })
    expect(result.plan_waves[0]).toEqual(['ga_a'])
    expect(result.plan_waves[1]).toEqual(['bo_a'])
  })
})
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd platform && npx vitest run src/lib/build/__tests__/plan.waves.test.ts
```

Expected: FAIL — `computeWaves` not yet implemented.

- [ ] **Step 3: Add `computeWaves()` to `plan.ts`**

Add this function after `preflight()`:

```typescript
/**
 * Groups topo-sorted candidates into waves. Assets in the same wave have no
 * in-scope dependencies on each other and can execute in parallel.
 * Cross-layer deps are treated as external for layer-scope wave computation.
 */
export function computeWaves(
  candidates: AssetId[],
  registry: RegistryEntry[],
  scope: BuildScope,
  scope_target: string | null
): AssetId[][] {
  const sorted = topoSort(candidates, registry)
  const candidateSet = new Set(candidates)
  const regMap = new Map(registry.map(r => [r.asset_id, r]))
  const waveOf = new Map<AssetId, number>()

  for (const id of sorted) {
    const entry = regMap.get(id)
    const inScopeDeps = (entry?.depends_on ?? []).filter(d => {
      if (!candidateSet.has(d)) return false
      // For layer scope: cross-layer deps are pre-flighted, not counted for wave assignment
      if (scope === 'layer' && scope_target) {
        const depEntry = regMap.get(d)
        if (depEntry && depEntry.layer !== scope_target) return false
      }
      return true
    })

    const wave = inScopeDeps.length === 0
      ? 0
      : Math.max(...inScopeDeps.map(d => waveOf.get(d) ?? 0)) + 1
    waveOf.set(id, wave)
  }

  if (waveOf.size === 0) return []
  const maxWave = Math.max(...waveOf.values())
  const waves: AssetId[][] = []
  for (let w = 0; w <= maxWave; w++) {
    const group = [...waveOf.entries()]
      .filter(([, v]) => v === w)
      .map(([k]) => k)
    if (group.length > 0) waves.push(group)
  }
  return waves
}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd platform && npx vitest run src/lib/build/__tests__/plan.waves.test.ts
```

Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add platform/src/lib/build/plan.ts \
        platform/src/lib/build/__tests__/plan.waves.test.ts
git commit -m "feat(plan): add computeWaves() helper + tests — parallel DAG execution groups"
```

---

## Task 4: Rewrite `resolveBuildPlan()` + remove `checkStalenessGate`

**Files:**
- Modify: `platform/src/lib/build/plan.ts`

- [ ] **Step 1: Replace `resolveBuildPlan()` completely**

Delete the existing `resolveBuildPlan` function (lines 157–274) and `checkStalenessGate` (lines 40–65) and `StalenessGateEntry` interface. Replace with:

```typescript
export function resolveBuildPlan({
  scope,
  scope_target,
  action,
  registry,
  throughput,
}: ResolveBuildPlanArgs): BuildPlan {
  // ── 1. Determine candidates ───────────────────────────────────────────────
  let candidates: AssetId[]

  if (action === 'build') {
    const scopeAssets = assetsInScope(scope, scope_target, registry)
    if (scope === 'asset' && scope_target) {
      // No-op if already lit
      const state = throughput.get(scope_target)?.state
      if (state === 'lit' || state === 'service_ok') {
        return { status: 'ok', plan_waves: [], blockers: [], estimated_seconds: null }
      }
      candidates = [scope_target]
    } else {
      candidates = scopeAssets.filter(id => {
        const t = throughput.get(id)
        return !t || t.state === 'dormant' || t.state === 'error'
      })
    }
  } else if (action === 'rebuild') {
    candidates = assetsInScope(scope, scope_target, registry)
  } else if (action === 'update') {
    // Unchanged from prior implementation
    const scopeAssets = assetsInScope(scope, scope_target, registry)
    const stale = scopeAssets.filter(id => throughput.get(id)?.state === 'stale')
    const dormant = scopeAssets.filter(id => {
      const t = throughput.get(id)
      return !t || t.state === 'dormant'
    })
    const downstreamAll = transitiveDownstream(stale, registry)
    const downstreamFiltered = scope === 'asset'
      ? downstreamAll
      : downstreamAll.filter(id => scopeAssets.includes(id))
    candidates = Array.from(new Set([...stale, ...dormant, ...downstreamFiltered]))
  } else {
    // cascade: unchanged from prior implementation
    const scopeAssets = assetsInScope(scope, scope_target, registry)
    const stale = registry
      .filter(r => throughput.get(r.asset_id)?.state === 'stale')
      .map(r => r.asset_id)
    candidates = transitiveDownstream(stale, registry)
      .filter(id => scopeAssets.includes(id))
  }

  if (candidates.length === 0) {
    return { status: 'ok', plan_waves: [], blockers: [], estimated_seconds: null }
  }

  // ── 2. Pre-flight gate (build + rebuild at asset/layer scope only) ────────
  if ((action === 'build' || action === 'rebuild') && scope !== 'global') {
    const blockers = preflight(candidates, scope, scope_target, registry, throughput)
    if (blockers.length > 0) {
      return { status: 'blocked', plan_waves: [], blockers, estimated_seconds: null }
    }
  }

  // ── 3. Compute waves ──────────────────────────────────────────────────────
  const plan_waves = computeWaves(candidates, registry, scope, scope_target)

  // ── 4. Estimate duration ──────────────────────────────────────────────────
  const regMap = new Map(registry.map(r => [r.asset_id, r]))
  let estimated_seconds: number | null = 0
  for (const id of plan_waves.flat()) {
    const entry = regMap.get(id)
    if (!entry || entry.estimated_seconds == null) {
      estimated_seconds = null
      break
    }
    estimated_seconds = (estimated_seconds ?? 0) + entry.estimated_seconds
  }

  return { status: 'ok', plan_waves, blockers: [], estimated_seconds }
}
```

Also remove the `StalenessGateEntry` interface and `checkStalenessGate` export entirely from `plan.ts`.

- [ ] **Step 2: Run all plan tests**

```bash
cd platform && npx vitest run src/lib/build/__tests__/
```

Expected: `plan.preflight.test.ts` and `plan.waves.test.ts` all PASS. Any other plan tests in the directory should also pass (update assertions if they check old `BuildPlan` shape).

- [ ] **Step 3: TypeScript check**

```bash
cd platform && npx tsc --noEmit
```

Expected: zero errors. If `runs/route.ts` or `cascade-preview/route.ts` error because they still import `checkStalenessGate`, note the error — it will be fixed in Task 5.

- [ ] **Step 4: Commit**

```bash
git add platform/src/lib/build/plan.ts
git commit -m "feat(plan): rewrite resolveBuildPlan — scoped builds, pre-flight gate, wave output"
```

---

## Task 5: Update API routes — `plan/route.ts` and `runs/route.ts`

**Files:**
- Modify: `platform/src/app/api/cockpit/plan/route.ts`
- Modify: `platform/src/app/api/cockpit/runs/route.ts`

- [ ] **Step 1: Update `plan/route.ts`**

The route calls `resolveBuildPlan()` and returns the result. Key changes:
1. The old `plan.plan` flat array → `planResult.plan_waves.flat()` for estimated-seconds lookup (already handled inside `resolveBuildPlan`)
2. The route previously enriched `plan` with historical duration medians from `build_run_assets` — this now feeds into `estimated_seconds` inside `resolveBuildPlan` if `registry` includes `estimated_seconds` per entry. Verify the registry query (line 28–29) populates `estimated_seconds` on each `RegistryEntry`.
3. Return the full `BuildPlan` as the JSON response:

```typescript
// In the POST handler, after calling resolveBuildPlan():
const planResult = resolveBuildPlan({ scope, scope_target, action, registry, throughput })

// If the route previously computed estimated_seconds separately from build_run_assets,
// merge it into the result here (only when status is 'ok'):
if (planResult.status === 'ok' && planResult.estimated_seconds === null) {
  // compute median from build_run_assets for plan_waves.flat()
  // ... existing estimation query logic, applied to plan_waves.flat() ...
  // planResult.estimated_seconds = computed value
}

return NextResponse.json(planResult)
```

Remove the old `blocked_assets` and `includes_upstream_count` fields from the response.

- [ ] **Step 2: Update `runs/route.ts` — Gate 4 and flat-plan adaptation**

In `runs/route.ts`, find the three areas to change:

**Area 1 — Remove import of `checkStalenessGate`** (line 4):
```typescript
// DELETE this import line:
import { checkStalenessGate, resolveBuildPlan, ... } from '@/lib/build/plan'
// Keep: resolveBuildPlan and other imports
```

**Area 2 — Replace Gate 4** (around line 133–149):

Old Gate 4:
```typescript
const staleGate = checkStalenessGate(plan.plan, planRegistry, throughput)
if (staleGate.length > 0) {
  return NextResponse.json({ error: 'stale_upstream', gate: staleGate }, { status: 422 })
}
```

New Gate 4:
```typescript
// Gate 4: Pre-flight gate — block if any dep is not ready
if (planResult.status === 'blocked') {
  return NextResponse.json(
    { error: 'deps_not_ready', blockers: planResult.blockers },
    { status: 422 }
  )
}
```

**Area 3 — Adapt flat `plan` usage throughout the file**:

The variable in `runs/route.ts` is a bare `plan` (destructured from the old `resolveBuildPlan` result). After the rewrite, `resolveBuildPlan` returns a `BuildPlan` object — so change the destructuring at line 133 from:
```typescript
const { plan, blocked_assets, includes_upstream_count } = resolveBuildPlan(...)
```
to:
```typescript
const planResult = resolveBuildPlan(...)
const plan = planResult.plan_waves.flat()   // flat list used throughout
```

Then update every remaining reference to `blocked_assets` and `includes_upstream_count`. All six locations in the file:
- **Line 133** — destructuring (replaced above)
- **Line 148** — `plan.length === 0` guard → `plan.length === 0` (unchanged; `plan` is now the flat result of `.flat()`)
- **Line 315** — `JSON.stringify(plan)` → `JSON.stringify(plan)` (unchanged; `plan` is already flat — Python orchestrator reads this from DB)
- **Line 363** — response body: remove `blocked_assets` and `includes_upstream_count` fields; keep `plan`
- **Line 372** — DB insert of plan in the clear-before path: `JSON.stringify(plan)` (unchanged)
- **Line 417** — response body: same as line 363

- [ ] **Step 3: TypeScript check**

```bash
cd platform && npx tsc --noEmit
```

Expected: zero errors.

- [ ] **Step 4: Commit**

```bash
git add platform/src/app/api/cockpit/plan/route.ts \
        platform/src/app/api/cockpit/runs/route.ts
git commit -m "feat(api): plan + runs routes return new BuildPlan shape; Gate 4 uses blockers"
```

---

## Task 6: Create `BuildBlockedModal.tsx`

**Files:**
- Create: `platform/src/components/cockpit/BuildBlockedModal.tsx`

- [ ] **Step 1: Create the component**

```typescript
'use client'

import type { BlockerEntry } from '@/lib/build/plan'

interface Props {
  open: boolean
  onClose: () => void
  /** Human-readable name of the asset or layer the user tried to build */
  targetLabel: string
  blockers: BlockerEntry[]
  /** Optional: map from asset_id to display name */
  assetNames?: Record<string, string>
}

const STATE_LABELS: Record<string, string> = {
  stale: 'stale',
  dormant: 'not built',
  error: 'error',
  service_down: 'service down',
  building: 'building',
}

const STATE_COLORS: Record<string, string> = {
  stale: 'text-amber-400 bg-amber-400/10',
  dormant: 'text-stone-400 bg-stone-400/10',
  error: 'text-red-400 bg-red-400/10',
  service_down: 'text-red-400 bg-red-400/10',
  building: 'text-blue-400 bg-blue-400/10',
}

export default function BuildBlockedModal({
  open,
  onClose,
  targetLabel,
  blockers,
  assetNames = {},
}: Props) {
  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div className="w-full max-w-lg rounded-lg border border-amber-600/40 bg-[#0e0c09] p-6 shadow-2xl">
        <h2 className="mb-1 text-base font-semibold text-amber-400">
          Cannot build — dependencies not ready
        </h2>
        <p className="mb-5 text-sm text-stone-400">
          <span className="text-stone-200">{targetLabel}</span> cannot start until the
          following dependencies are ready.
        </p>

        <ul className="space-y-3 max-h-72 overflow-y-auto pr-1">
          {blockers.map(b => {
            const name = assetNames[b.dep_asset_id] ?? b.dep_asset_id
            const colorClass = STATE_COLORS[b.dep_state] ?? 'text-stone-400 bg-stone-400/10'
            const label = STATE_LABELS[b.dep_state] ?? b.dep_state
            return (
              <li key={b.dep_asset_id} className="rounded border border-white/5 bg-white/[0.02] p-3">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-sm text-stone-200">{name}</span>
                  <span className={`rounded px-2 py-0.5 text-xs font-medium ${colorClass}`}>
                    {label}
                  </span>
                </div>
                {b.guidance && (
                  <p className="mt-1 text-xs text-amber-500/80">{b.guidance}</p>
                )}
                {b.required_by.length > 0 && (
                  <p className="mt-1 text-xs text-stone-500">
                    Required by: {b.required_by.map(id => assetNames[id] ?? id).join(', ')}
                  </p>
                )}
              </li>
            )
          })}
        </ul>

        <div className="mt-6 flex justify-end">
          <button
            onClick={onClose}
            className="rounded px-4 py-2 text-sm font-medium text-stone-300 hover:text-stone-100 border border-white/10 hover:border-white/20 transition-colors"
          >
            Dismiss
          </button>
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd platform && npx tsc --noEmit
```

Expected: zero errors.

- [ ] **Step 3: Commit**

```bash
git add platform/src/components/cockpit/BuildBlockedModal.tsx
git commit -m "feat(ui): add BuildBlockedModal — dep-not-ready gate with blocker list"
```

---

## Task 7: Create `BuildConfirmModal.tsx`

**Files:**
- Create: `platform/src/components/cockpit/BuildConfirmModal.tsx`

- [ ] **Step 1: Create the component**

```typescript
'use client'

interface Props {
  open: boolean
  onClose: () => void
  onConfirm: () => void
  /** Human-readable name of the asset or layer being built */
  targetLabel: string
  /** Flat list of asset IDs in the plan */
  assetIds: string[]
  /** Optional: map from asset_id to display name */
  assetNames?: Record<string, string>
  estimatedSeconds: number | null
  action: 'build' | 'rebuild'
  isSubmitting?: boolean
}

function formatDuration(seconds: number): string {
  if (seconds < 60) return `~${seconds}s`
  return `~${Math.round(seconds / 60)}m`
}

export default function BuildConfirmModal({
  open,
  onClose,
  onConfirm,
  targetLabel,
  assetIds,
  assetNames = {},
  estimatedSeconds,
  action,
  isSubmitting = false,
}: Props) {
  if (!open) return null

  const verb = action === 'rebuild' ? 'Rebuild' : 'Build'

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div className="w-full max-w-lg rounded-lg border border-white/10 bg-[#0e0c09] p-6 shadow-2xl">
        <h2 className="mb-1 text-base font-semibold text-stone-100">
          {verb} {targetLabel}?
        </h2>
        {estimatedSeconds != null && (
          <p className="mb-4 text-sm text-stone-400">
            Estimated time: {formatDuration(estimatedSeconds)}
          </p>
        )}

        {assetIds.length > 1 && (
          <>
            <p className="mb-2 text-xs text-stone-500 uppercase tracking-wide">
              {assetIds.length} assets
            </p>
            <ul className="space-y-1 max-h-60 overflow-y-auto pr-1 mb-5">
              {assetIds.map(id => (
                <li key={id} className="text-sm text-stone-300 py-0.5">
                  {assetNames[id] ?? id}
                </li>
              ))}
            </ul>
          </>
        )}

        {assetIds.length === 1 && (
          <p className="mb-5 text-sm text-stone-400">
            This will {verb.toLowerCase()} <span className="text-stone-200">{assetNames[assetIds[0]] ?? assetIds[0]}</span>.
          </p>
        )}

        <div className="flex justify-end gap-3">
          <button
            onClick={onClose}
            disabled={isSubmitting}
            className="rounded px-4 py-2 text-sm font-medium text-stone-300 hover:text-stone-100 border border-white/10 hover:border-white/20 transition-colors disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            disabled={isSubmitting}
            className="rounded px-4 py-2 text-sm font-medium bg-amber-500 text-black hover:bg-amber-400 transition-colors disabled:opacity-50"
          >
            {isSubmitting ? 'Starting…' : `Confirm ${verb.toLowerCase()}`}
          </button>
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd platform && npx tsc --noEmit
```

Expected: zero errors.

- [ ] **Step 3: Commit**

```bash
git add platform/src/components/cockpit/BuildConfirmModal.tsx
git commit -m "feat(ui): add BuildConfirmModal — scoped asset list, no cross-layer cascade"
```

---

## Task 8: Update `AssetRow.tsx` + wire new modals

**Files:**
- Modify: `platform/src/lib/components/cockpit/v2/AssetRow.tsx`

- [ ] **Step 1: Add imports for new modals and `BlockerEntry` type**

At the top of `AssetRow.tsx`, add:
```typescript
import BuildBlockedModal from '@/components/cockpit/BuildBlockedModal'
import BuildConfirmModal from '@/components/cockpit/BuildConfirmModal'
import type { BlockerEntry } from '@/lib/build/plan'
```

Remove the import of `CascadePreviewModal` if it exists in this file.

- [ ] **Step 2: Add `pendingBlock` state alongside existing `pendingCascade`**

Find the existing state declarations and add:
```typescript
const [pendingBlock, setPendingBlock] = useState<{
  targetLabel: string
  blockers: BlockerEntry[]
} | null>(null)
```

- [ ] **Step 3: Update `handleRebuildClick()` (around line 180)**

Replace the existing handler body with:

```typescript
async function handleRebuildClick() {
  const action = throughputState === 'dormant' || throughputState === 'error' ? 'build' : 'rebuild'
  
  const res = await fetch('/api/cockpit/plan', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      chart_id,
      scope: 'asset',
      scope_target: asset.asset_id,
      action,
    }),
  })
  
  if (!res.ok) return  // network error — surface separately
  
  const planResult = await res.json()
  
  if (planResult.status === 'blocked') {
    // Dep-not-ready gate: show blocker modal
    setPendingBlock({
      targetLabel: asset.display_name ?? asset.asset_id,
      blockers: planResult.blockers,
    })
    return
  }
  
  // status === 'ok'
  if (!planResult.plan_waves || planResult.plan_waves.flat().length === 0) {
    // No-op: asset already lit under 'build' action
    return
  }
  
  // Enrich with display names from allAssets
  const flatPlan: string[] = planResult.plan_waves.flat()
  const planInfo = flatPlan.map((id: string) => {
    const a = allAssets?.find(x => x.asset_id === id)
    return { asset_id: id, display_name: a?.display_name ?? id, layer: a?.layer ?? '' }
  })
  
  setPendingCascade({
    assetId: asset.asset_id,
    action,
    plan: flatPlan,
    planInfo,
    estimatedSeconds: planResult.estimated_seconds ?? null,
  })
}
```

- [ ] **Step 4: Replace modal rendering**

Find where `CascadePreviewModal` (or the old confirm dialog) is rendered and replace with:

```tsx
{/* Dep-not-ready gate modal */}
{pendingBlock && (
  <BuildBlockedModal
    open={true}
    onClose={() => setPendingBlock(null)}
    targetLabel={pendingBlock.targetLabel}
    blockers={pendingBlock.blockers}
    assetNames={Object.fromEntries(
      (allAssets ?? []).map(a => [a.asset_id, a.display_name ?? a.asset_id])
    )}
  />
)}

{/* Scoped confirm modal */}
{pendingCascade && (
  <BuildConfirmModal
    open={true}
    onClose={() => setPendingCascade(null)}
    onConfirm={handleConfirmBuild}
    targetLabel={pendingCascade.planInfo[0]?.display_name ?? pendingCascade.assetId}
    assetIds={pendingCascade.plan}
    assetNames={Object.fromEntries(
      (pendingCascade.planInfo ?? []).map((p: any) => [p.asset_id, p.display_name])
    )}
    estimatedSeconds={pendingCascade.estimatedSeconds}
    action={pendingCascade.action}
    isSubmitting={isSubmitting}
  />
)}
```

- [ ] **Step 5: TypeScript check**

```bash
cd platform && npx tsc --noEmit
```

Expected: zero errors.

- [ ] **Step 6: Run all tests**

```bash
cd platform && npx vitest run
```

Expected: all tests PASS.

- [ ] **Step 7: Commit**

```bash
git add platform/src/lib/components/cockpit/v2/AssetRow.tsx
git commit -m "feat(nirmana): AssetRow uses BuildBlockedModal + BuildConfirmModal — no downstream cascade"
```

---

## Note: Python sidecar `plan_waves` storage (deferred)

The spec lists `platform/python-sidecar/` as a file to change with: "Accept optional `plan_waves` in payload; store for auditability." However, the Python orchestrator never receives the TypeScript payload directly — it reads `plan` (flat list) from the `build_runs` table in PostgreSQL. Storing `plan_waves` requires a new `JSONB` column on `build_runs` and a DB migration.

**This is deferred to a follow-up.** The system is fully functional without it: the orchestrator uses the flat `plan` list (backward-compatible) and its existing DAG scheduler handles parallel execution. The `plan_waves` structure is available in the TypeScript API response for UI display.

When ready to add auditability: create migration `ADD COLUMN plan_waves JSONB` on `build_runs`; update `runs/route.ts` line 315 to also write `plan_waves`; update `runner.py`'s `load_run()` to read it.

---

## Task 9: End-to-end verification

- [ ] **Step 1: Start the dev server**

```bash
cd platform && npm run dev
```

- [ ] **Step 2: Navigate to the Nirmana build tracker**

Open `http://localhost:3000/clients/482012f1-710e-4a25-994a-93821f5871aa/nirmana`

- [ ] **Step 3: Expand Kāla layer and click Rebuild on `ka_sangam`**

Expected: confirmation dialog shows **only `ka_sangam`** — no Phala or Mīmāṃsā assets listed.

- [ ] **Step 4: Verify the blocker modal appears when a dep is stale**

If `ka_sangam` currently shows `build-state stale` badge, first stale one of its deps (or use browser DevTools to mock the `/api/cockpit/plan` response with `status: 'blocked'`). Confirm the `BuildBlockedModal` appears with amber styling and Dismiss-only button.

- [ ] **Step 5: Verify layer rebuild stays within the layer**

Click the Layer-level Rebuild button for Kāla. Expected: confirmation dialog shows only the Kāla assets (10–12), not Phala or Mīmāṃsā.

- [ ] **Step 6: Final commit and push**

```bash
git push origin main
```
