# Smart Build: Upstream Readiness Gate + Staleness Propagation — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add two coordinated integrity mechanisms: (1) a staleness gate that blocks any build whose out-of-plan upstream deps are stale, surfacing exactly which assets are blocking and why; (2) automatic downstream staleness propagation in the orchestrator after each asset completes, so the Nirmana tracker reflects reality in real time without a full-page refresh.

**Architecture:**  
- **Gate:** New `checkStalenessGate()` in `plan.ts` scans every plan asset's direct out-of-plan `depends_on` entries for stale state. A new Gate 4 in `runs/route.ts` calls this before any run is created and returns 422/`UPSTREAM_STALE` with a structured `stale_upstream` list. The frontend parses the structured error and shows named blockers — not a generic toast.  
- **Propagation:** New `staleness.py` Python module called via an `on_complete` callback added to `execute_dag()`. After each asset lands in `completed`, it bulk-marks transitive downstream assets (outside the current plan) as `stale` in `asset_throughput`, then emits `asset.state_change` SSE events so the tracker updates live.

**Tech Stack:** TypeScript/Next.js (`plan.ts`, `route.ts`, React), Python 3.12 (psycopg2, `emit_event`), PostgreSQL (`asset_throughput` UPDATE, `asset_registry` query), Vitest (TS), pytest (Python)

---

## Design Rationale: Why stale ≠ dormant

This is the key distinction that drives the whole design:

| Upstream state | Current behavior | New behavior | Why |
|---|---|---|---|
| `dormant` | Auto-pulled into plan | **Unchanged** | Never built; first-time build produces fresh data from scratch — safe |
| `error` | Auto-pulled into plan | **Unchanged** | Failed build; retry is correct and produces fresh data |
| `stale` | NOT auto-pulled; orchestrator deadlocks/blocks silently | **Hard block 422 before run is created** | Has data, but it's outdated; building downstream ON stale data produces wrong output |
| `lit` | Seeded into `completed` in orchestrator | Unchanged | Ready ✓ |

The two features interlock: Feature 2 (propagation) writes stale markers the moment upstream rebuilds; Feature 1 (gate) enforces the invariant before any new build starts. Together they close the integrity loop.

## How the features interact end-to-end

1. L1 asset `ga_positions` is rebuilt → **Feature 2** marks `bo_laksana`, `bo_bimba`, etc. as `stale` in `asset_throughput` → Nirmana tracker rows turn amber immediately via SSE.
2. User tries to build `bo_bimba` (depends on stale `bo_laksana`) → **Feature 1** returns 422 with `stale_upstream: [{ asset_id: 'bo_laksana', required_by: ['bo_bimba'] }]` → modal shows "bo_laksana is stale — rebuild it first."
3. User rebuilds `bo_laksana` → it becomes `lit` → **Feature 2** marks `bo_bimba` stale (it's now downstream of a freshly-rebuilt dep).
4. User rebuilds `bo_bimba` → upstream check passes (bo_laksana is lit) → build proceeds.

## Interaction with existing L0 blocking

The existing `blocked_assets` mechanism (plan.ts lines 188–215) handles dormant L0 (bg_*) deps — it removes those assets from the plan silently. The new Gate 4 (`UPSTREAM_STALE`) is a **separate** check that fires **after** plan resolution and handles stale non-L0 upstream. Neither replaces the other; both coexist.

## File Map

| File | Change |
|---|---|
| `platform/src/lib/build/plan.ts` | Add `checkStalenessGate()` + `StalenessGateEntry` type |
| `platform/src/lib/build/__tests__/plan.staleness-gate.test.ts` | New test file for gate |
| `platform/src/app/api/cockpit/runs/route.ts` | Add Gate 4 (`UPSTREAM_STALE` 422) after plan resolution |
| `platform/src/lib/components/cockpit/v2/AssetRow.tsx` | Parse `UPSTREAM_STALE` in `handleCascadeConfirm`; show named blockers |
| `platform/src/lib/components/cockpit/v2/PlanModal.tsx` | Parse `UPSTREAM_STALE`; set `error` state with named blockers |
| `platform/python-sidecar/pipeline/orchestrator/staleness.py` | New module: `compute_downstream_ids` + `propagate_downstream_staleness` |
| `platform/python-sidecar/pipeline/orchestrator/runner.py` | Add `on_complete` param to `execute_dag()`; wire propagation in `_schedule_parallel()` |
| `platform/python-sidecar/pipeline/orchestrator/tests/test_staleness.py` | New pytest file |

---

## Task 1 — `checkStalenessGate()` in plan.ts

**Files:**
- Modify: `platform/src/lib/build/plan.ts`
- Create: `platform/src/lib/build/__tests__/plan.staleness-gate.test.ts`

**What this does:** For every asset in the resolved plan, inspect its declared `depends_on` entries. For any dep that is **outside the plan** (DAG will handle in-plan deps), check if its throughput state is `stale`. Return one entry per stale dep, including which plan assets need it (`required_by`). Dormant/error deps are intentionally excluded — those are handled by auto-pull.

- [ ] **Step 1: Write the failing tests**

Create `platform/src/lib/build/__tests__/plan.staleness-gate.test.ts`:

```typescript
import { describe, it, expect } from 'vitest'
import { checkStalenessGate, type RegistryEntry, type ThroughputEntry } from '../plan'

function reg(asset_id: string, layer: string, depends_on: string[]): RegistryEntry {
  return { asset_id, layer, depends_on, estimated_seconds: null }
}
function tp(asset_id: string, state: ThroughputEntry['state']): [string, ThroughputEntry] {
  return [asset_id, { asset_id, state }]
}

const REGISTRY = [
  reg('ga_positions', 'ganita', []),
  reg('bo_laksana', 'bodha', ['ga_positions']),
  reg('bo_bimba', 'bodha', ['bo_laksana']),
  reg('ph_result', 'phala', ['bo_bimba']),
]

describe('checkStalenessGate', () => {
  it('returns empty when all out-of-plan upstream are lit', () => {
    const throughput = new Map([tp('ga_positions', 'lit'), tp('bo_laksana', 'lit')])
    const result = checkStalenessGate(['bo_bimba'], REGISTRY, throughput)
    expect(result).toHaveLength(0)
  })

  it('returns stale dep when direct upstream is stale', () => {
    // bo_laksana is stale (was built before ga_positions was rebuilt)
    const throughput = new Map([tp('ga_positions', 'lit'), tp('bo_laksana', 'stale')])
    const result = checkStalenessGate(['bo_bimba'], REGISTRY, throughput)
    expect(result).toHaveLength(1)
    expect(result[0].asset_id).toBe('bo_laksana')
    expect(result[0].state).toBe('stale')
    expect(result[0].required_by).toContain('bo_bimba')
  })

  it('does NOT flag in-plan deps — DAG handles those', () => {
    // bo_laksana is stale but it's in the plan so it will be rebuilt first
    const throughput = new Map([tp('ga_positions', 'lit'), tp('bo_laksana', 'stale')])
    const result = checkStalenessGate(['bo_laksana', 'bo_bimba'], REGISTRY, throughput)
    expect(result).toHaveLength(0)
  })

  it('lists multiple stale deps and their required_by', () => {
    const throughput = new Map([tp('bo_laksana', 'stale'), tp('bo_bimba', 'stale')])
    const result = checkStalenessGate(['bo_bimba', 'ph_result'], REGISTRY, throughput)
    const ids = result.map(r => r.asset_id)
    expect(ids).toContain('bo_laksana')
    expect(ids).toContain('bo_bimba')
  })

  it('does NOT flag dormant upstream — auto-pull or L0-gate handles those', () => {
    const throughput = new Map([tp('bo_laksana', 'dormant')])
    const result = checkStalenessGate(['bo_bimba'], REGISTRY, throughput)
    expect(result).toHaveLength(0)
  })

  it('returns empty for a root asset with no upstream', () => {
    const result = checkStalenessGate(['ga_positions'], REGISTRY, new Map())
    expect(result).toHaveLength(0)
  })

  it('same dep required by multiple plan assets is returned once with all required_by', () => {
    const REG2 = [
      reg('ga_positions', 'ganita', []),
      reg('bo_laksana', 'bodha', ['ga_positions']),
      reg('bo_bimba', 'bodha', ['ga_positions']),  // also depends on ga_positions directly
    ]
    const throughput = new Map([tp('ga_positions', 'stale')])
    const result = checkStalenessGate(['bo_laksana', 'bo_bimba'], REG2, throughput)
    expect(result).toHaveLength(1)
    expect(result[0].asset_id).toBe('ga_positions')
    expect(result[0].required_by).toContain('bo_laksana')
    expect(result[0].required_by).toContain('bo_bimba')
  })

  it('does NOT flag service_ok upstream — treated same as lit', () => {
    // service_ok is a valid healthy state; the Python side also treats it as non-stale.
    // Passing `state` via `as any` since service_ok is not in the TypeScript AssetState union
    // (the DB can have it for service assets like ga_chart_service).
    const throughput = new Map([['ga_chart_service', { asset_id: 'ga_chart_service', state: 'service_ok' as any }]])
    const SREG = [
      reg('ga_chart_service', 'ganita', []),
      reg('bo_laksana', 'bodha', ['ga_chart_service']),
    ]
    const result = checkStalenessGate(['bo_laksana'], SREG, throughput)
    expect(result).toHaveLength(0)
  })
})
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
cd platform && npx vitest run src/lib/build/__tests__/plan.staleness-gate.test.ts
```
Expected: FAIL — `checkStalenessGate is not a function` (export missing)

- [ ] **Step 3: Add the export type and function to plan.ts**

Add immediately after the `BuildPlan` interface (after line 24):

```typescript
export interface StalenessGateEntry {
  asset_id: AssetId
  state: string
  required_by: AssetId[]
}

/**
 * Returns one entry per out-of-plan upstream dep whose state is 'stale'.
 * A non-empty result means the build should be blocked: building downstream
 * on stale data produces wrong output. In-plan deps are excluded — the DAG
 * scheduler handles those by running deps before dependents.
 * Dormant/error upstream are not flagged here: auto-pull or L0-blocking
 * handles them separately.
 */
export function checkStalenessGate(
  plan: AssetId[],
  registry: RegistryEntry[],
  throughput: Map<AssetId, ThroughputEntry>
): StalenessGateEntry[] {
  const planSet = new Set(plan)
  const regMap = new Map(registry.map(r => [r.asset_id, r]))
  const staleBlockers = new Map<AssetId, Set<AssetId>>()

  for (const planAsset of plan) {
    for (const dep of regMap.get(planAsset)?.depends_on ?? []) {
      if (planSet.has(dep)) continue  // in-plan: DAG will handle it
      if (throughput.get(dep)?.state === 'stale') {
        if (!staleBlockers.has(dep)) staleBlockers.set(dep, new Set())
        staleBlockers.get(dep)!.add(planAsset)
      }
    }
  }

  return Array.from(staleBlockers.entries()).map(([dep, requiredBySet]) => ({
    asset_id: dep,
    state: throughput.get(dep)?.state ?? 'stale',
    required_by: Array.from(requiredBySet),
  }))
}
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
cd platform && npx vitest run src/lib/build/__tests__/plan.staleness-gate.test.ts
```
Expected: PASS (7/7)

- [ ] **Step 5: Run all existing plan tests — guard regressions**

```bash
cd platform && npx vitest run src/lib/build/__tests__/plan.test.ts src/lib/build/__tests__/plan.upstream.test.ts src/lib/build/__tests__/plan.l0-layer.test.ts src/lib/build/__tests__/staleness.test.ts
```
Expected: all PASS

- [ ] **Step 6: Commit**

```bash
git add platform/src/lib/build/plan.ts platform/src/lib/build/__tests__/plan.staleness-gate.test.ts
git commit -m "feat(plan): checkStalenessGate — block builds with stale out-of-plan upstream"
```

---

## Task 2 — Gate 4 (`UPSTREAM_STALE`) in runs/route.ts

**Files:**
- Modify: `platform/src/app/api/cockpit/runs/route.ts`

**What this does:** After `resolveBuildPlan()` (line 133), calls `checkStalenessGate()`. If any stale out-of-plan upstream exists, returns 422 with `code: 'UPSTREAM_STALE'` and the structured list. The run is **not created** — nothing is written to the DB.

Positioning relative to existing gates:
- Gate 0 (409): active run check — unchanged
- Gate 1 (202): L0 double-confirm — unchanged
- Existing plan resolution + `blocked_assets` — unchanged
- **Gate 4 (new, 422):** stale upstream check — fires after plan resolution, before Gate 3
- Gate 3 (422): L2 precondition hardcoded check — unchanged (Belt-and-suspenders for L2; may be removed later once Gate 4 is proven)

- [ ] **Step 1: Add `checkStalenessGate` to the import line**

In `runs/route.ts` line 4, update the import:

```typescript
import { resolveBuildPlan, computeDownstreamClosure, checkStalenessGate, type RegistryEntry, type ThroughputEntry, type BuildAction, type BuildScope } from '@/lib/build/plan'
```

- [ ] **Step 2: Insert Gate 4 after plan resolution**

After line 133 (`const { plan, blocked_assets } = resolveBuildPlan(...)`), and **before** the `plan.length === 0` check (line 135), insert:

```typescript
  // Gate 4: Stale upstream gate.
  // Blocks builds where any out-of-plan dep has stale data. Dormant/error upstream
  // are already handled by auto-pull (plan.ts). Only stale requires an explicit
  // upstream rebuild because building downstream on stale data produces wrong output.
  const staleGate = checkStalenessGate(plan, planRegistry, throughput)
  if (staleGate.length > 0) {
    return NextResponse.json({
      error: 'Build blocked: upstream assets have stale data and must be rebuilt first',
      code: 'UPSTREAM_STALE',
      stale_upstream: staleGate,
    }, { status: 422 })
  }
```

- [ ] **Step 3: Verify existing TypeScript compiles**

```bash
cd platform && npx tsc --noEmit
```
Expected: no new errors

- [ ] **Step 4: Manual API test**

With the dev server running, force a stale state on an asset:

```sql
UPDATE asset_throughput SET state = 'stale'
WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
  AND asset_id = 'bo_laksana';
```

Then POST to `/api/cockpit/runs` with `{ chart_id, scope: 'asset', scope_target: 'bo_bimba', action: 'rebuild' }`. Expect 422 with `code: 'UPSTREAM_STALE'` and `stale_upstream: [{ asset_id: 'bo_laksana', required_by: ['bo_bimba'] }]`.

- [ ] **Step 5: Commit**

```bash
git add platform/src/app/api/cockpit/runs/route.ts
git commit -m "feat(api/runs): Gate 4 — 422 UPSTREAM_STALE when out-of-plan upstream is stale"
```

---

## Task 3 — Asset-level stale error in AssetRow.tsx

**Files:**
- Modify: `platform/src/lib/components/cockpit/v2/AssetRow.tsx`

**What this does:** In `handleCascadeConfirm()` (line ~220), when the API returns `UPSTREAM_STALE`, shows a specific toast listing the stale asset IDs and the "rebuild them first" instruction — not the generic `body.error` string.

- [ ] **Step 1: Update handleCascadeConfirm to parse UPSTREAM_STALE**

Locate the `if (!r.ok)` block in `handleCascadeConfirm` (around line 235). Replace:

```typescript
      if (!r.ok) {
        toast.error(body?.error ?? 'Failed to start build')
        return
      }
```

With:

```typescript
      if (!r.ok) {
        if (body?.code === 'UPSTREAM_STALE' && Array.isArray(body?.stale_upstream)) {
          const names = (body.stale_upstream as { asset_id: string }[])
            .map((s: { asset_id: string }) => s.asset_id)
            .join(', ')
          toast.error(
            `Build blocked — stale upstream: ${names}. Rebuild those assets first, then retry.`,
            { duration: 8000 }
          )
        } else {
          toast.error(body?.error ?? 'Failed to start build')
        }
        return
      }
```

- [ ] **Step 2: Manual test**

With the dev server running:
1. Set `bo_laksana` to stale in the DB (see Task 2 Step 4 SQL)
2. Open the Nirmana tracker
3. Click Build/Rebuild on `bo_bimba` (which depends on `bo_laksana`)
4. Confirm in the cascade modal
5. Verify the toast reads: *"Build blocked — stale upstream: bo_laksana. Rebuild those assets first, then retry."*
6. Restore: `UPDATE asset_throughput SET state = 'lit' WHERE asset_id = 'bo_laksana' ...`

- [ ] **Step 3: Commit**

```bash
git add platform/src/lib/components/cockpit/v2/AssetRow.tsx
git commit -m "feat(AssetRow): show named stale-upstream blocker on UPSTREAM_STALE instead of generic toast"
```

---

## Task 4 — Layer/global stale error in PlanModal.tsx

**Files:**
- Modify: `platform/src/lib/components/cockpit/v2/PlanModal.tsx`

**What this does:** In `PlanModal`, the confirmed build POST already catches errors and calls `setError(...)` (line 101) which renders as a red message in the modal (lines 164–166). Enhance the catch block to detect `UPSTREAM_STALE` and format a detailed, named message that tells the user exactly which upstream assets are stale and which in-scope assets depend on them.

- [ ] **Step 1: Add UPSTREAM_STALE parsing in the POST error handler**

Locate the `if (!r.ok) throw new Error(...)` check in `PlanModal.tsx` (line 97). Replace it with:

```typescript
      if (!r.ok) {
        if (body?.code === 'UPSTREAM_STALE' && Array.isArray(body?.stale_upstream)) {
          const lines = (body.stale_upstream as { asset_id: string; required_by: string[] }[])
            .map(s => `• ${s.asset_id}  (needed by: ${s.required_by.join(', ')})`)
            .join('\n')
          throw new Error(
            `Build blocked — these upstream assets are stale and must be rebuilt first:\n${lines}`
          )
        }
        throw new Error(body.error ?? 'Failed to start run')
      }
```

The `setError(...)` at line 101 will receive this multi-line string. The modal's existing error display (lines 164–166) already renders it. Because the modal uses `font-family: var(--ui-stack)` (monospace-ish), newlines may not render as line breaks in HTML — add `whitespace-pre-wrap` to the error div:

In `PlanModal.tsx` around line 165, update the error `<div>` style:

```typescript
          <div style={{
            color: 'var(--marsys-error)',
            fontSize: '12px',
            fontFamily: 'var(--ui-stack)',
            whiteSpace: 'pre-wrap',   // add this
          }}>
            {error}
          </div>
```

- [ ] **Step 2: Manual test**

1. Set `ga_structural` to stale in the DB
2. Open Nirmana tracker → click "Rebuild" on the Bodha layer (which depends on ga_structural cross-layer)
3. In the PlanModal, click Confirm
4. Verify the modal error area shows something like:
   ```
   Build blocked — these upstream assets are stale and must be rebuilt first:
   • ga_structural  (needed by: bo_laksana, bo_bimba, ...)
   ```
5. Restore state

- [ ] **Step 3: Commit**

```bash
git add platform/src/lib/components/cockpit/v2/PlanModal.tsx
git commit -m "feat(PlanModal): show named stale-upstream blockers on UPSTREAM_STALE for layer builds"
```

---

## Task 5 — Python `staleness.py` propagation module

**Files:**
- Create: `platform/python-sidecar/pipeline/orchestrator/staleness.py`
- Create: `platform/python-sidecar/pipeline/orchestrator/tests/test_staleness.py`

**What this does:**
- `compute_downstream_ids(completed_asset_id, registry)` → `set[str]` — pure BFS over the reverse dep graph, no DB needed. Testable without mocks.
- `propagate_downstream_staleness(conn, cur, chart_id, completed_asset_id, plan_set, registry, emit_fn, run_id)` — bulk-marks transitive downstream (outside `plan_set`) as `stale` in `asset_throughput`, then emits SSE events.

Key constraints:
- Only marks assets with `state IN ('lit', 'service_ok')` — never marks `dormant` (nothing to be stale about) or `building` (in flight)
- Uses a RETURNING clause to know exactly which assets were actually updated, avoiding spurious SSE events
- Commits on the provided connection — caller provides a fresh connection (not the main advisory-lock connection)

- [ ] **Step 1: Create the tests package**

The `orchestrator/tests/` directory does not exist yet. Create it with an `__init__.py` so the relative imports (`from ..staleness import ...`) work with pytest:

```bash
mkdir -p platform/python-sidecar/pipeline/orchestrator/tests
touch platform/python-sidecar/pipeline/orchestrator/tests/__init__.py
```

Without `__init__.py`, pytest will fail with `attempted relative import with no known parent package` even after the module exists — a different error from "module not found" that would be confusing.

- [ ] **Step 2: Write the test file**

Create `platform/python-sidecar/pipeline/orchestrator/tests/test_staleness.py`:

```python
import pytest
from ..staleness import compute_downstream_ids

# Linear chain: ga_positions -> bo_laksana -> bo_bimba -> ph_result
REGISTRY = [
    {'asset_id': 'ga_positions', 'depends_on': []},
    {'asset_id': 'bo_laksana',   'depends_on': ['ga_positions']},
    {'asset_id': 'bo_bimba',     'depends_on': ['bo_laksana']},
    {'asset_id': 'ph_result',    'depends_on': ['bo_bimba']},
]

def test_compute_downstream_root():
    """Root asset: all others are downstream."""
    result = compute_downstream_ids('ga_positions', REGISTRY)
    assert result == {'bo_laksana', 'bo_bimba', 'ph_result'}

def test_compute_downstream_mid_chain():
    result = compute_downstream_ids('bo_laksana', REGISTRY)
    assert result == {'bo_bimba', 'ph_result'}

def test_compute_downstream_leaf():
    """Leaf asset: no downstream."""
    result = compute_downstream_ids('ph_result', REGISTRY)
    assert result == set()

def test_compute_downstream_does_not_include_self():
    result = compute_downstream_ids('bo_laksana', REGISTRY)
    assert 'bo_laksana' not in result

def test_compute_downstream_diamond():
    """Diamond dep: A -> B, A -> C, B -> D, C -> D. Downstream of A = {B, C, D}."""
    diamond = [
        {'asset_id': 'A', 'depends_on': []},
        {'asset_id': 'B', 'depends_on': ['A']},
        {'asset_id': 'C', 'depends_on': ['A']},
        {'asset_id': 'D', 'depends_on': ['B', 'C']},
    ]
    result = compute_downstream_ids('A', diamond)
    assert result == {'B', 'C', 'D'}
    # D must not appear twice (set dedup)
    assert len(result) == 3

def test_compute_downstream_isolated():
    """Asset with no dependents returns empty set."""
    result = compute_downstream_ids('ga_positions', [
        {'asset_id': 'ga_positions', 'depends_on': []},
    ])
    assert result == set()
```

- [ ] **Step 3: Run tests — verify they fail**

```bash
cd platform/python-sidecar && python -m pytest pipeline/orchestrator/tests/test_staleness.py -v
```
Expected: FAIL with `ModuleNotFoundError: No module named 'pipeline.orchestrator.staleness'`

- [ ] **Step 4: Create `staleness.py`**

Create `platform/python-sidecar/pipeline/orchestrator/staleness.py`:

```python
"""
Downstream staleness propagation.

After an asset transitions to 'lit', all transitive downstream assets that are
NOT in the current run's plan should be marked 'stale' in asset_throughput.
Dormant assets are excluded — they have no data to be stale. Building state is
excluded — leave in-flight assets alone.
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def compute_downstream_ids(
    completed_asset_id: str,
    registry: list[dict],
) -> set[str]:
    """
    BFS over the reverse dependency graph to find all transitive downstream
    assets of completed_asset_id. Pure function — no DB access.

    registry: list of dicts with keys 'asset_id' and 'depends_on' (list[str]).
    """
    # Build reverse graph: for each asset, which assets depend on it
    dependents: dict[str, set[str]] = {}
    for row in registry:
        for dep in row.get('depends_on') or []:
            dependents.setdefault(dep, set()).add(row['asset_id'])

    downstream: set[str] = set()
    queue = list(dependents.get(completed_asset_id, set()))
    while queue:
        nxt = queue.pop()
        if nxt in downstream:
            continue
        downstream.add(nxt)
        queue.extend(dependents.get(nxt, set()))
    return downstream


def propagate_downstream_staleness(
    conn,
    cur,
    chart_id: Optional[str],
    completed_asset_id: str,
    plan_set: set[str],
    registry: list[dict],
    emit_fn,
    run_id: str,
) -> None:
    """
    Mark transitive downstream of completed_asset_id as 'stale', then emit
    asset.state_change SSE events for each row actually updated.

    Excludes:
      - Assets in plan_set (they will be rebuilt in this run)
      - Assets with state 'dormant' (no data to be stale about)
      - Assets with state 'building' (leave in-flight workers alone)

    Uses RETURNING to emit events only for rows that actually changed.
    Commits on conn — caller must provide a dedicated connection (not the main
    advisory-lock connection) and must close it after.
    """
    downstream = compute_downstream_ids(completed_asset_id, registry)
    targets = list(downstream - plan_set)
    if not targets:
        return

    try:
        cur.execute(
            """
            UPDATE asset_throughput
               SET state = 'stale'
             WHERE chart_id = %s
               AND asset_id = ANY(%s::text[])
               AND state IN ('lit', 'service_ok')
            RETURNING asset_id
            """,
            (chart_id, targets),
        )
        rows = cur.fetchall()
        staled = [r[0] if isinstance(r, (tuple, list)) else r['asset_id'] for r in rows]
        conn.commit()

        for asset_id in staled:
            try:
                emit_fn({
                    "type": "asset.state_change",
                    "chart_id": chart_id,
                    "asset_id": asset_id,
                    "state": "stale",
                    "run_id": run_id,
                })
            except Exception as emit_err:
                logger.warning(
                    "[staleness] SSE emit failed for %s: %s", asset_id, emit_err
                )

        if staled:
            logger.info(
                "[staleness] %s completed → marked %d downstream stale: %s",
                completed_asset_id, len(staled), staled,
            )

    except Exception as exc:
        logger.error(
            "[staleness] propagation failed after %s: %s", completed_asset_id, exc
        )
        try:
            conn.rollback()
        except Exception:
            pass
```

- [ ] **Step 5: Run tests — verify they pass**

```bash
cd platform/python-sidecar && python -m pytest pipeline/orchestrator/tests/test_staleness.py -v
```
Expected: PASS (6/6)

- [ ] **Step 6: Commit**

```bash
git add platform/python-sidecar/pipeline/orchestrator/staleness.py \
        platform/python-sidecar/pipeline/orchestrator/tests/__init__.py \
        platform/python-sidecar/pipeline/orchestrator/tests/test_staleness.py
git commit -m "feat(orchestrator): staleness.py — compute and propagate downstream stale state"
```

---

## Task 6 — Add `on_complete` callback to `execute_dag()`

**Files:**
- Modify: `platform/python-sidecar/pipeline/orchestrator/runner.py`

**What this does:** Adds an optional `on_complete(asset_id: str)` callback to `execute_dag()`. Called in the scheduler loop after each future resolves successfully (added to `completed` set). This keeps `execute_dag` pure/DB-free — the concrete implementation lives in `_schedule_parallel()` (Task 7). Errors in `on_complete` are caught and logged; they must not crash the scheduler.

- [ ] **Step 1: Write the failing test**

The `orchestrator/tests/` package was created in Task 5. Create the new test file alongside the existing `test_staleness.py`:

Create `platform/python-sidecar/pipeline/orchestrator/tests/test_execute_dag_callbacks.py`:

```python
from ..runner import execute_dag

def test_on_complete_called_for_each_successful_asset():
    calls = []
    def run_fn(a): return 'lit'
    def on_complete(a): calls.append(a)

    plan = ['a', 'b', 'c']
    deps = {'a': [], 'b': ['a'], 'c': ['b']}
    failed, _ = execute_dag(
        plan=plan, deps_of=deps, run_fn=run_fn,
        worker_limit=2, on_complete=on_complete,
    )
    assert failed == set()
    assert set(calls) == {'a', 'b', 'c'}

def test_on_complete_not_called_for_failed_asset():
    calls = []
    def run_fn(a): return 'error' if a == 'b' else 'lit'

    execute_dag(
        plan=['a', 'b', 'c'], deps_of={'a': [], 'b': ['a'], 'c': ['b']},
        run_fn=run_fn, worker_limit=2,
        on_complete=lambda a: calls.append(a),
    )
    assert 'a' in calls       # succeeded before b
    assert 'b' not in calls   # failed
    assert 'c' not in calls   # blocked by b

def test_on_complete_exception_does_not_crash_scheduler():
    """A buggy on_complete must not kill the build."""
    def run_fn(a): return 'lit'
    def bad_on_complete(a): raise RuntimeError("oops")

    failed, terminal = execute_dag(
        plan=['a', 'b'], deps_of={'a': [], 'b': ['a']},
        run_fn=run_fn, worker_limit=2,
        on_complete=bad_on_complete,
    )
    # Both assets complete despite the callback error
    assert failed == set()
    assert terminal is None
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
cd platform/python-sidecar && python -m pytest pipeline/orchestrator/tests/test_execute_dag_callbacks.py -v
```
Expected: FAIL — `execute_dag() got unexpected keyword argument 'on_complete'`

- [ ] **Step 3: Update `execute_dag()` signature (runner.py line ~232)**

Add the new parameter to the signature:

```python
def execute_dag(
    plan: list[str],
    deps_of: dict[str, list[str]],
    run_fn,
    worker_limit: int,
    seed_completed: Optional[set] = None,
    on_block=None,
    should_stop=None,
    on_timeout=None,
    on_complete=None,   # NEW: called(asset_id) when asset lands in completed
) -> tuple[set[str], Optional[str]]:
```

Add the `_on_complete` alias alongside the existing ones (around line 261):

```python
    _on_complete = on_complete or (lambda a: None)
```

- [ ] **Step 4: Fire the callback in BOTH futures-resolution sites**

There are two places in `execute_dag` where futures land in `completed`:
1. The main done-loop (around line 302) — the normal case
2. The stop/pause drain loop (around line 323–331) — for workers in-flight when a stop signal arrives

Both must call `_on_complete`. Replace the single-line assignment in **each** location:

**Site 1 — main done-loop (around line 308):**

Replace:
```python
            (failed if fut.result() == "error" else completed).add(a)
```
With:
```python
            if fut.result() == "error":
                failed.add(a)
            else:
                completed.add(a)
                try:
                    _on_complete(a)
                except Exception as _oce:
                    logger.warning("[execute_dag] on_complete(%s) raised: %s", a, _oce)
```

**Site 2 — stop/pause drain loop (around line 329):**

Replace:
```python
                (failed if fut.result() == "error" else completed).add(a)
```
With:
```python
                if fut.result() == "error":
                    failed.add(a)
                else:
                    completed.add(a)
                    try:
                        _on_complete(a)
                    except Exception as _oce:
                        logger.warning("[execute_dag] on_complete(%s) raised: %s", a, _oce)
```

- [ ] **Step 5: Run all orchestrator tests**

```bash
cd platform/python-sidecar && python -m pytest pipeline/orchestrator/tests/ -v
```
Expected: all PASS (including the new test_execute_dag_callbacks.py)

- [ ] **Step 6: Commit**

```bash
git add platform/python-sidecar/pipeline/orchestrator/runner.py \
        platform/python-sidecar/pipeline/orchestrator/tests/test_execute_dag_callbacks.py
git commit -m "feat(orchestrator): add on_complete callback to execute_dag for post-asset hooks"
```

---

## Task 7 — Wire staleness propagation in `_schedule_parallel()`

**Files:**
- Modify: `platform/python-sidecar/pipeline/orchestrator/runner.py`

**What this does:** In `_schedule_parallel()`, (1) preloads the full `asset_registry` (not just plan deps — propagation needs all assets to find transitive downstream), then (2) defines an `on_complete` callback that calls `propagate_downstream_staleness()` on a fresh connection, then (3) passes it to `execute_dag()`.

Fresh connection rationale: the main `conn` holds the PostgreSQL advisory lock for the entire run. Propagation's `commit()` must not interfere with it. Using a dedicated connection for propagation is safe and clean.

- [ ] **Step 1: Add full registry preload in `_schedule_parallel()`**

After the existing `asset_deps` preload (around line 577–588 in `execute_run`), but inside `_schedule_parallel`, add a full-registry fetch. The function signature is unchanged; this is an internal preload:

```python
    # Preload full active registry for downstream staleness propagation.
    # asset_deps only covers plan assets; propagation needs all assets.
    cur.execute(
        "SELECT asset_id, COALESCE(depends_on, '{}') AS depends_on "
        "FROM asset_registry WHERE is_active = true"
    )
    full_registry = [
        {'asset_id': row['asset_id'], 'depends_on': list(row['depends_on'])}
        for row in cur.fetchall()
    ]
    conn.commit()  # release snapshot so subsequent reads are fresh
```

- [ ] **Step 2: Define `on_complete` callback using a fresh connection**

After the existing callback definitions (`on_block`, `on_timeout`) and before the `execute_dag(...)` call (around line 490):

```python
    from .staleness import propagate_downstream_staleness

    def on_complete(asset_id: str) -> None:
        # Fresh connection: must not use main conn (it holds the advisory lock).
        # Pass the run's chart_id — not eff(asset_id). eff() returns None for global
        # assets, but WHERE chart_id = NULL is always false in SQL. The staleness
        # UPDATE targets chart-specific rows in asset_throughput using the run's real
        # chart_id; the global asset's own throughput row (chart_id IS NULL) is never
        # a downstream target of itself, so the NULL-chart path is never needed here.
        _sconn = None
        try:
            _sconn = connect()
            _sconn.autocommit = False
            _scur = _sconn.cursor()
            propagate_downstream_staleness(
                conn=_sconn,
                cur=_scur,
                chart_id=chart_id,   # run's chart_id, not eff(asset_id)
                completed_asset_id=asset_id,
                plan_set=plan_set,
                registry=full_registry,
                emit_fn=emit_event,
                run_id=run_id,
            )
        except Exception as _pse:
            logger.error("[staleness] on_complete(%s) failed: %s", asset_id, _pse)
        finally:
            if _sconn is not None:
                try:
                    _sconn.close()
                except Exception:
                    pass
```

- [ ] **Step 3: Pass `on_complete` to `execute_dag()`**

Update the `execute_dag(...)` call (around line 490) to include:

```python
    return execute_dag(
        plan=pending,
        deps_of=deps_of,
        run_fn=worker,
        worker_limit=_WORKER_LIMIT,
        seed_completed=completed,
        on_block=on_block,
        should_stop=should_stop,
        on_timeout=on_timeout,
        on_complete=on_complete,   # NEW
    )
```

- [ ] **Step 4: Integration sanity check**

Trigger a real build of a single L1 asset (e.g. `ga_positions`) for chart `482012f1-710e-4a25-994a-93821f5871aa`. After it completes, query:

```sql
SELECT asset_id, state
FROM asset_throughput
WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
  AND state = 'stale'
ORDER BY asset_id;
```

Expect: all `bo_*`, `ka_*`, `ph_*`, `mi_*` assets that transitively depend on `ga_positions` should be `stale`.

Check orchestrator logs for lines like:
```
[staleness] ga_positions completed → marked 14 downstream stale: ['bo_laksana', ...]
```

- [ ] **Step 5: Commit**

```bash
git add platform/python-sidecar/pipeline/orchestrator/runner.py
git commit -m "feat(orchestrator): wire downstream staleness propagation after each asset completes"
```

---

## Task 8 — Verify stale state display in Nirmana tracker UI

**Files:**
- Read: `platform/src/lib/components/cockpit/v2/AssetRow.tsx` (already shows stale as amber at line 136 — likely no change needed)
- Possibly modify: SSE consumer / live state merger

**What this does:** Confirms the full path works: orchestrator emits `asset.state_change { state: 'stale' }` via SSE → frontend consumer updates the live state map → `AssetRow` re-renders with the amber `StatusDot` — all without a page reload.

- [ ] **Step 1: Trace the SSE consumer**

Search for `EventSource` or `useSSE` or `asset.state_change` in the cockpit v2 components to find where SSE events are consumed. Verify that the handler merges `state: 'stale'` into whatever local state feeds `AssetRow`'s `stat` prop.

```bash
grep -rn "asset.state_change\|EventSource\|useSSE" \
  platform/src/lib/components/cockpit/v2/ \
  platform/src/hooks/ \
  --include="*.ts" --include="*.tsx"
```

- [ ] **Step 2: Verify `stale` is handled in the merger**

If the SSE handler only handles `'building'` and `'lit'` transitions, add `'stale'` to the handled states. The merger should update `throughputState` or equivalent so `AssetRow` re-renders.

- [ ] **Step 3: Manual end-to-end test**

1. Ensure L1 is all `lit` and L2 is all `lit` in the tracker
2. Trigger a rebuild of `ga_positions` only (scope=asset, action=rebuild)
3. Watch the Nirmana tracker in real time:
   - `ga_positions` row: building (amber pulsing) → lit (green)
   - Immediately after: `bo_laksana`, `bo_bimba`, and other bo_* dependents should turn amber (stale) **without a page reload**
4. Confirm the amber appears within ~2 seconds of `ga_positions` completing

- [ ] **Step 4: Fix SSE consumer if stale state doesn't update**

If Step 3 shows the state doesn't update in real time (rows stay green), the fix is in the SSE handler: extend the state merge to include `stale` as a valid transition state. Follow the existing pattern for `building` and `lit`.

- [ ] **Step 5: Commit if any changes were made**

```bash
git add platform/src/lib/components/cockpit/v2/<modified-files> \
        platform/src/hooks/<modified-files>
git commit -m "fix(tracker): SSE consumer handles stale state_change — AssetRow updates in real time"
```

---

## Edge Cases and Design Guardrails

| Scenario | Behavior |
|---|---|
| **Global-scope rebuild** (all assets in plan) | No out-of-plan upstream → Gate 4 returns empty → no block. DAG handles ordering within the run. |
| **Layer rebuild with stale cross-layer upstream** | Gate 4 fires: "Build blocked — stale upstream: ga_structural." User rebuilds Gaṇita layer, retries. |
| **L0 (bg_*) asset rebuilds** | Propagation marks downstream ga_* assets for this chart as stale. `eff('bg_ontology')` returns `None` (global) → UPDATE targets `chart_id = NULL` rows and propagates to chart-specific rows via the DISTINCT ON throughput query. |
| **mi_* (L5 Mīmāṃsā) in structural mode** | They become stale if upstream rebuilds. Correct — they carry calibration state derived from upstream data. The amber badge tells the user they need refreshing. |
| **Asset currently `building` in another run** | Gate 0 (active run check) prevents concurrent runs for the same chart. This scenario cannot occur. |
| **Diamond dependency (A→B, A→C, B→D, C→D)** | BFS visits D once — `set` dedup prevents duplicate stale markers and duplicate SSE events. |
| **Dormant upstream** | Gate 4 ignores it (not `stale`). Auto-pull or L0-blocking handles dormant upstream as before. |
| **Propagation fails** (network blip, DB error) | Caught and logged in `on_complete`; does NOT fail the build. The asset is already `lit`. Stale markers may be missing but no data corruption occurs. The user can trigger a manual refresh. |
| **`on_complete` exception** | `execute_dag` catches and logs it; scheduler continues normally (tested in Task 6 Step 1). |
| **Very deep dep chain** | BFS is O(N) where N = total assets (~50). Single bulk UPDATE. Well within performance budget. |
| **Stale propagation on stop/pause** | In-flight workers finish; `on_complete` fires for those that succeeded. Correct — partial propagation is fine since any subsequent rebuild will re-propagate. |
| **Circular dependency** | Cannot occur — `topoSort()` at plan generation throws on any cycle. The reverse-graph BFS uses a `visited` set to guard anyway. |
