---
artifact: QUERY_TRACE_IMPLEMENTATION_v1_0
title: Query Trace — Implementation Reference
version: 1.0.0
status: CURRENT
created: 2026-05-05
canonical_id: QUERY_TRACE_IMPL
---

# Query Trace — Implementation Reference

This document covers the data model, assembly contract, extension guides, and
operational notes for the Query Trace diagnostic tool built in TRACE-T1 through
TRACE-T3.

---

## 1. Overview

The Query Trace tool gives super-admins a full lifecycle view of any query
processed by the MARSYS pipeline. It shows:

- **Classify** — how the query was classified and with what confidence
- **Plan** — which retrieval bundles were selected and which excluded
- **Fetch** — per-bundle retrieval results (raw, kept, dropped)
- **Context Assembly** — how retrieved items were ranked, filtered, and assembled into the LLM context window
- **Synthesis** — the final LLM call: model, token counts, latency, quality scorecard
- **Health Rail** — per-stage health signals, baseline comparison, anomaly callouts, cost/token ledger

---

## 2. Data Model — Three Key Tables

### 2.1 `context_assembly_item_log`

One row per candidate item evaluated during context assembly. Populated by the
context assembly service after each retrieval cycle.

| Column | Type | Description |
|---|---|---|
| `query_id` | uuid | FK to `query_log` |
| `item_rank` | int | Evaluation rank (1 = highest priority) |
| `source_bundle` | text | Which retrieval bundle produced this item |
| `source_item_id` | text | Item identifier within that bundle |
| `layer` | text | `L1` or `L2_5` — which knowledge layer |
| `token_cost` | int | Estimated token cost of this item |
| `relevance_score` | float8 | Relevance score (0–1); null if not scored |
| `status` | text | `INCLUDED`, `TRUNCATED`, or `DROPPED` |
| `drop_reason` | text | Reason for drop/truncation (null if INCLUDED) |
| `cumulative_tokens_at_decision` | int | Running token total when this decision was made |
| `budget_at_decision` | int | Token budget at decision time |

### 2.2 `plan_alternatives_log`

One row per bundle considered by the planner. Both selected and rejected bundles
are logged.

| Column | Type | Description |
|---|---|---|
| `query_id` | uuid | FK to `query_log` |
| `bundle_name` | text | Name of the retrieval bundle |
| `was_selected` | bool | True if included in the plan |
| `rationale` | text | Planner reasoning for inclusion/exclusion |
| `expected_recall_score` | float8 | Planner's expected recall estimate |

### 2.3 `synthesis_quality_scorecard`

One row per query, written after synthesis completes.

| Column | Type | Description |
|---|---|---|
| `query_id` | uuid | FK to `query_log` |
| `composite_score` | float8 | Overall quality (0–1); below 0.6 triggers DEGRADED |
| `citation_density` | float8 | Fraction of claims with citations; below 0.5 triggers WARNING |
| `failures` | jsonb | Array of failure codes from the scorecard evaluator |

---

## 3. TraceDocument — The Assembler Contract

`assembleTrace(queryId, db)` in `platform/src/lib/admin/trace_assembler.ts` is
the single entry point. It runs seven parallel DB queries and returns a
`TraceDocument` object.

```typescript
interface TraceDocument {
  query: {
    id: string
    text: string | null
    type: string | null
    confidence: number | null
    total_ms: number | null
    total_cost_usd: number | null
    health: 'HEALTHY' | 'DEGRADED' | 'FAILED' | 'UNKNOWN'
  }
  classify: { ... } | null
  plan: { included_bundles[], excluded_bundles[], plan_json, latency_ms } | null
  fetches: Array<{ bundle, raw_count, kept_count, dropped_items[], kept_items[], latency_ms, error_class }>
  context_assembly: { items[], token_ledger } | null
  synthesis: { model, input_tokens, output_tokens, latency_ms, scorecard } | null
  baselines: { p50_total_latency_ms, p95_total_latency_ms, p50_total_cost_usd, p95_total_cost_usd, sample_size } | null
  anomalies: Array<{ stage, severity, message, step_id }>
  partial: boolean
}
```

**`partial: true`** means the query predates the `context_assembly_item_log`
instrumentation — context assembly data will be absent.

**`baselines`** comes from the `query_baseline_stats` materialized view
(refreshed by a periodic job). If `sample_size < 30`, baselines are marked
unreliable in the Health Rail UI.

The assembler also calls `detectAnomalies()` server-side (private function),
but the client also runs the exported `detectAnomalies()` from
`platform/src/lib/admin/anomaly_detector.ts` for the Health Rail, which
enriches anomalies with `step_id` values for focus navigation.

---

## 4. How to Add a New Step Type to the Lifecycle Graph

Follow these three steps:

### Step 1 — New node component

Create `platform/src/components/trace/lifecycle/MyNewNode.tsx`. Follow the
pattern of existing nodes (e.g., `ClassifyNode.tsx`):

```tsx
import { NodeWrapper } from './NodeWrapper'
import type { TraceDocument } from '@/lib/admin/trace_assembler'

interface MyNewNodeProps {
  trace: TraceDocument
  selected: boolean
  onSelect: () => void
}

export function MyNewNode({ trace, selected, onSelect }: MyNewNodeProps) {
  const data = trace.my_new_step
  const status = data == null ? 'skipped' : 'ok'

  return (
    <NodeWrapper
      testId="my-new-node"
      selected={selected}
      status={status}
      label="My new step"
      onClick={onSelect}
    >
      <p className="text-xs text-zinc-400">My New Step</p>
      {/* ... render step summary ... */}
    </NodeWrapper>
  )
}
```

### Step 2 — New step_detail variant

Create `platform/src/components/trace/step_detail/MyNewDetail.tsx`. Use the
`Section` wrapper for visual consistency:

```tsx
import { Section } from './Section'
import type { TraceDocument } from '@/lib/admin/trace_assembler'

export function MyNewDetail({ trace }: { trace: TraceDocument }) {
  const data = trace.my_new_step
  if (!data) return <p className="text-xs text-zinc-500">No data</p>

  return (
    <div className="space-y-6" data-testid="my-new-detail">
      <Section title="Input">...</Section>
      <Section title="Decision">...</Section>
      <Section title="Output">...</Section>
    </div>
  )
}
```

### Step 3 — Register in STEP_ORDER and StepDetail

1. In `TraceModal.tsx`, add `'my_new_step'` to `buildStepOrder()` return array.
2. In `LifecycleGraph.tsx`, add the new node with an appropriate `EdgeConnector`
   before/after it.
3. In `StepDetail.tsx`, add a branch to the step-type switch to render
   `<MyNewDetail trace={trace} />` when `selectedStepId === 'my_new_step'`.
4. Add the new step ID to `matchesFilter()` in `LifecycleGraph.tsx` if it has
   searchable bundle-level names.

---

## 5. How to Add a New Anomaly Detector

The anomaly detector lives entirely in
`platform/src/lib/admin/anomaly_detector.ts` as pure functions — no DB calls.

### Step 1 — Add a detector function body

Inside `detectAnomalies(trace: TraceDocument)`, add a new numbered block:

```typescript
// 6. My new detector
if (trace.my_new_step != null) {
  const value = trace.my_new_step.some_metric
  if (value > THRESHOLD) {
    anomalies.push({
      stage: 'overall',        // or the relevant stage name
      severity: 'WARNING',
      message: `Some metric ${value} exceeds threshold ${THRESHOLD}`,
      step_id: 'my_new_step', // must match a step ID in buildStepOrder()
    })
  }
}
```

### Step 2 — Write a test

In `platform/src/__tests__/lib/admin/anomaly_detector.test.ts`, add a test
case that constructs a `TraceDocument` with the trigger condition and asserts
the anomaly appears with the correct severity and step_id.

Anomalies are automatically surfaced in the Health Rail's Anomaly Callouts
card, where clicking them focuses the corresponding lifecycle node.

---

## 6. Baseline Stats Refresh Cadence

`query_baseline_stats` is a materialized view over `query_log`. It is refreshed
by a scheduled DB job. The view computes p50/p95 latency and cost across all
queries of a given `query_type`.

- **Refresh interval:** Daily (or on-demand via `REFRESH MATERIALIZED VIEW CONCURRENTLY query_baseline_stats`)
- **Warm-up period:** The view returns `sample_size = 0` until at least one
  query has been logged. The Health Rail shows "Baselines unreliable" for
  `sample_size < 30`.
- **Per-type granularity:** Currently all queries collapse to type `'unknown'`
  (see `baseline_resolver.ts`). To add per-type baselines, extend the WHERE
  clause and pass the actual `query_type` from the assembler.

---

## 7. Health Derivation Logic

Health is derived by `deriveHealth()` in `trace_assembler.ts`:

| Condition | Health |
|---|---|
| Any fetch `error_class !== 'OK'` | `FAILED` |
| `composite_score < 0.5` | `DEGRADED` |
| No fetches at all | `UNKNOWN` |
| Otherwise | `HEALTHY` |

The client-side `detectAnomalies()` adds finer-grained anomaly signals
(priority violations, budget pressure, low citation density) that do not change
the top-level health verdict but surface in the Health Rail.

---

## 8. File Map

```
platform/src/
  app/api/admin/trace/[queryId]/route.ts   # API route — assembleTrace → JSON
  lib/admin/
    trace_assembler.ts                     # assembleTrace() + TraceDocument
    trace_client.ts                        # fetchTrace() — client-side fetch
    baseline_resolver.ts                   # resolveBaseline() — DB baseline query
    anomaly_detector.ts                    # detectAnomalies() — pure function
  components/trace/
    TraceModal.tsx                         # Modal shell + keyboard nav
    LifecycleGraph.tsx                     # Left zone: execution flow
    StepDetail.tsx                         # Center zone: step detail router
    HealthRail.tsx                         # Right zone: health + anomalies
    SearchFilter.tsx                       # Filter bar (/ key)
    ShortcutHelpOverlay.tsx                # Keyboard help (? key)
    TimingRibbon.tsx                       # Bottom timing strip
    QueryHeaderStrip.tsx                   # Top header
    lifecycle/                             # Per-stage node components
    step_detail/                           # Per-stage detail panels
  __tests__/
    components/trace/                      # Component tests
    lib/admin/                             # Unit tests for assembler + detector
```
