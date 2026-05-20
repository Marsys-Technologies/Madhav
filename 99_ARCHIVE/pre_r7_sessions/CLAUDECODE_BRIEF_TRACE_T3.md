---
session_id: TRACE-T3
title: Query Trace — Health Rail + Anomaly Detection + Polish
status: COMPLETE
phase: TRACE-T3
executor: Anti-Gravity (Claude Code, claude-sonnet-4-6)
created_date: 2026-05-05
prerequisite: TRACE-T1 + TRACE-T2 ACs confirmed
reference_plan: 00_ARCHITECTURE/QUERY_TRACE_REDESIGN_v1_0.md
---

# TRACE-T3 — Query Trace: Health Rail + Anomaly Detection + Polish

## Objective

Fill the right-zone Health & Performance Rail, wire the anomaly detection system,
add performance hardening (virtualized tables for large result sets), a11y pass,
search/filter, and the shortcut help overlay. Close the trace redesign with a clean,
production-ready diagnostic tool.

**Prerequisite:** T1 + T2 must both be confirmed complete with all ACs passing.

---

## Scope

```
may_touch:
  - platform/src/components/trace/HealthRail.tsx               # CREATE
  - platform/src/components/trace/health/                      # CREATE directory
  - platform/src/lib/admin/anomaly_detector.ts                 # CREATE
  - platform/src/lib/admin/baseline_resolver.ts                # CREATE (if not in T1)
  - platform/src/components/trace/TraceModal.tsx               # extend: wire HealthRail
  - platform/src/components/trace/ShortcutHelpOverlay.tsx      # CREATE
  - platform/src/components/trace/SearchFilter.tsx             # CREATE
  - platform/src/components/trace/LifecycleGraph.tsx           # extend: add search filter
  - platform/src/components/trace/step_detail/FetchSqlDetail.tsx   # extend: virtualize table
  - platform/src/components/trace/step_detail/ContextAssemblyDetail.tsx  # extend: virtualize
  - platform/src/__tests__/components/trace/health/           # CREATE test files
  - platform/src/__tests__/lib/admin/anomaly_detector.test.ts # CREATE

must_not_touch:
  - platform/src/app/api/admin/trace/                # T1 — already done
  - platform/src/lib/db/                             # T1 — already done
  - platform/supabase/migrations/                    # T1 — already done
  - any existing non-trace UI routes
  - existing Observatory components
  - existing Audit View components
```

---

## Task 1 — Anomaly detector

**New file:** `platform/src/lib/admin/anomaly_detector.ts`

Takes a `TraceDocument` and its baselines, returns an `Anomaly[]` array. Pure function — no DB calls.

```typescript
import type { TraceDocument } from './trace_assembler'

export type AnomalySeverity = 'ERROR' | 'WARNING' | 'INFO'

export interface Anomaly {
  stage: 'classify' | 'plan' | 'fetch' | 'context_assembly' | 'synthesis' | 'overall'
  severity: AnomalySeverity
  message: string
  step_id: string | null  // which lifecycle node to focus when clicked
  metric?: { actual: number; p50: number; ratio: number }
}

export function detectAnomalies(trace: TraceDocument): Anomaly[] {
  const anomalies: Anomaly[] = []
  const baselines = trace.baselines

  // 1. Plan latency outlier
  if (
    trace.plan?.latency_ms != null &&
    baselines?.p50_total_latency_ms != null &&
    baselines.p50_total_latency_ms > 0
  ) {
    const ratio = trace.plan.latency_ms / (baselines.p50_plan_latency_ms ?? baselines.p50_total_latency_ms)
    if (ratio > 2.0) {
      anomalies.push({
        stage: 'plan',
        severity: ratio > 3.0 ? 'ERROR' : 'WARNING',
        message: `Plan latency ${trace.plan.latency_ms}ms (${ratio.toFixed(1)}× p50)`,
        step_id: 'plan',
        metric: { actual: trace.plan.latency_ms, p50: baselines.p50_total_latency_ms, ratio },
      })
    }
  }

  // 2. Failed fetch steps
  for (const fetch of trace.fetches) {
    if (fetch.error_class !== 'OK') {
      anomalies.push({
        stage: 'fetch',
        severity: 'ERROR',
        message: `${fetch.bundle} fetch failed: ${fetch.error_class}`,
        step_id: fetch.bundle,
      })
    }
  }

  // 3. Empty fetch steps (non-error but returned 0 items)
  for (const fetch of trace.fetches) {
    if (fetch.error_class === 'OK' && fetch.kept_count === 0 && fetch.raw_count === 0) {
      anomalies.push({
        stage: 'fetch',
        severity: 'WARNING',
        message: `${fetch.bundle} returned 0 items — possible filter too narrow`,
        step_id: fetch.bundle,
      })
    }
  }

  // 4. Context assembly budget pressure
  if (trace.context_assembly) {
    const dropped = trace.context_assembly.token_ledger.dropped_count
    const total = trace.context_assembly.items.length
    if (total > 0 && dropped / total > 0.3) {
      anomalies.push({
        stage: 'context_assembly',
        severity: 'WARNING',
        message: `Context assembly dropped ${dropped}/${total} items (${Math.round(dropped/total*100)}%) — budget pressure`,
        step_id: 'context_assembly',
      })
    }
    // Priority violation: a DROPPED item that has higher relevance_score than an INCLUDED item
    const includedScores = trace.context_assembly.items
      .filter(i => i.status === 'INCLUDED' && i.relevance_score != null)
      .map(i => i.relevance_score!)
    const maxIncludedScore = includedScores.length > 0 ? Math.max(...includedScores) : null
    const droppedHigher = trace.context_assembly.items.filter(
      i => i.status === 'DROPPED' &&
           i.relevance_score != null &&
           maxIncludedScore != null &&
           i.relevance_score > maxIncludedScore
    )
    if (droppedHigher.length > 0) {
      anomalies.push({
        stage: 'context_assembly',
        severity: 'ERROR',
        message: `Priority violation: ${droppedHigher.length} dropped item(s) scored higher than included items`,
        step_id: 'context_assembly',
      })
    }
  }

  // 5. Synthesis citation density below threshold
  const scorecard = trace.synthesis?.scorecard as { citation_density?: number; composite_score?: number } | null
  if (scorecard?.citation_density != null && scorecard.citation_density < 0.5) {
    anomalies.push({
      stage: 'synthesis',
      severity: 'WARNING',
      message: `Low citation density: ${scorecard.citation_density.toFixed(2)} (expected ≥ 0.5)`,
      step_id: 'synthesis',
    })
  }
  if (scorecard?.composite_score != null && scorecard.composite_score < 0.6) {
    anomalies.push({
      stage: 'synthesis',
      severity: scorecard.composite_score < 0.4 ? 'ERROR' : 'WARNING',
      message: `Synthesis quality score: ${scorecard.composite_score.toFixed(2)} (below 0.6 threshold)`,
      step_id: 'synthesis',
    })
  }

  // Sort: errors first, then warnings, then info
  return anomalies.sort((a, b) => {
    const order: Record<AnomalySeverity, number> = { ERROR: 0, WARNING: 1, INFO: 2 }
    return order[a.severity] - order[b.severity]
  })
}
```

---

## Task 2 — HealthRail

**New file:** `platform/src/components/trace/HealthRail.tsx`

The right-zone panel (320px wide). Five stacked cards.

**Card 1 — Overall Health Verdict:**

```tsx
export function HealthVerdictCard({ health, summary }: { health: TraceDocument['query']['health']; summary: string }) {
  const config = {
    HEALTHY: { color: 'text-emerald-400', bg: 'bg-emerald-400/10', border: 'border-emerald-400/30', icon: '✓' },
    DEGRADED: { color: 'text-amber-400', bg: 'bg-amber-400/10', border: 'border-amber-400/30', icon: '⚠' },
    FAILED: { color: 'text-red-400', bg: 'bg-red-400/10', border: 'border-red-400/30', icon: '✗' },
    UNKNOWN: { color: 'text-zinc-400', bg: 'bg-zinc-400/10', border: 'border-zinc-400/30', icon: '?' },
  }[health] ?? { color: 'text-zinc-400', bg: 'bg-zinc-400/10', border: 'border-zinc-400/30', icon: '?' }
  
  return (
    <div data-testid="health-verdict-card" className={`rounded-lg border ${config.border} ${config.bg} p-4 text-center`}>
      <div className={`text-3xl font-mono ${config.color} mb-1`}>{config.icon}</div>
      <div className={`text-sm font-bold ${config.color}`}>{health}</div>
      <div className="mt-2 text-xs text-zinc-400 leading-relaxed">{summary}</div>
    </div>
  )
}
```

Compute `summary` from the anomalies array:
- 0 anomalies → "All stages nominal"
- 1+ ERRORs → "Critical failure in [stage]"
- 1+ WARNINGs only → "Degraded: [first warning message truncated]"

**Card 2 — Per-Stage Health Strip:**

Five rows. Each row has three columns: stage name, latency indicator, completeness dot.

```tsx
const stages = ['classify', 'plan', 'fetch', 'assemble', 'synthesize'] as const

function StageHealthRow({ stage, latencyRatio, completeness, qualityOk }: {
  stage: string
  latencyRatio: number | null  // actual / p50; null if no baseline
  completeness: number | null  // 0-1
  qualityOk: boolean | null
}) {
  const latencyColor = latencyRatio == null ? 'bg-zinc-600' :
    latencyRatio <= 1.2 ? 'bg-emerald-400' :
    latencyRatio <= 2.0 ? 'bg-amber-400' : 'bg-red-400'
  
  const barWidth = latencyRatio == null ? 0 : Math.min(100, (latencyRatio / 3) * 100)
  
  const completenessColor = completeness == null ? 'bg-zinc-600' :
    completeness >= 0.9 ? 'bg-emerald-400' :
    completeness >= 0.7 ? 'bg-amber-400' : 'bg-red-400'
  
  const qualityColor = qualityOk == null ? 'bg-zinc-600' :
    qualityOk ? 'bg-emerald-400' : 'bg-amber-400'
  
  return (
    <div className="flex items-center gap-2 py-1.5">
      <span className="text-xs text-zinc-400 w-16 shrink-0">{stage}</span>
      <div className="flex-1 h-1.5 rounded-full bg-zinc-800 overflow-hidden">
        <div className={`h-full rounded-full ${latencyColor}`} style={{ width: `${barWidth}%` }} />
      </div>
      <div className={`w-2 h-2 rounded-full shrink-0 ${completenessColor}`} title={`completeness ${completeness != null ? (completeness*100).toFixed(0)+'%' : '—'}`} />
      <div className={`w-2 h-2 rounded-full shrink-0 ${qualityColor}`} title={`quality ${qualityOk ? 'ok' : 'degraded'}`} />
    </div>
  )
}
```

Compute per-stage latency ratios from `trace.baselines`. Completeness:
- Classify: `trace.classify?.confidence ?? null`
- Plan: `(trace.plan?.included_bundles.length ?? 0) / Math.max(trace.plan?.included_bundles.length + trace.plan?.excluded_bundles.length, 1)`
- Fetch: `1 - (emptyFetchCount / Math.max(trace.fetches.length, 1))`
- Assemble: `1 - (trace.context_assembly?.token_ledger.dropped_count ?? 0) / Math.max(trace.context_assembly?.items.length ?? 1, 1)`
- Synthesize: `scorecard?.composite_score ?? null`

**Card 3 — Baseline Comparison:**

Use Recharts `BarChart` (horizontal). X-axis: metric names. Two bars per metric: this query (gold) vs p50 (grey).

```tsx
import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, Cell, ReferenceLine } from 'recharts'

const baselineData = [
  { name: 'Plan (s)', actual: (trace.plan?.latency_ms ?? 0) / 1000, p50: (trace.baselines?.p50_plan_latency_ms ?? 0) / 1000 },
  { name: 'Synth (s)', actual: (trace.synthesis?.latency_ms ?? 0) / 1000, p50: (trace.baselines?.p50_synth_latency_ms ?? 0) / 1000 },
  { name: 'Cost ($)', actual: trace.query.total_cost_usd ?? 0, p50: trace.baselines?.p50_total_cost_usd ?? 0 },
]
// Show "n={baselines.sample_size} queries" footnote
// If sample_size < 30, show amber "Baselines unreliable" warning above chart
```

**Card 4 — Anomaly Callouts:**

```tsx
function AnomalyCallouts({ anomalies, onFocus }: { anomalies: Anomaly[]; onFocus: (stepId: string) => void }) {
  const [filter, setFilter] = useState<'all' | 'errors' | 'warnings'>('all')
  
  const filtered = anomalies.filter(a =>
    filter === 'all' ? true : filter === 'errors' ? a.severity === 'ERROR' : a.severity === 'WARNING'
  )
  
  return (
    <div data-testid="anomaly-callouts">
      {/* Filter tabs */}
      <div className="flex gap-1 mb-2">
        {(['all','errors','warnings'] as const).map(f => (
          <button key={f} onClick={() => setFilter(f)}
            className={`text-[10px] px-2 py-0.5 rounded border ${filter === f ? 'border-[rgba(212,175,55,0.4)] text-[#d4af37]' : 'border-zinc-700 text-zinc-500'}`}>
            {f}
          </button>
        ))}
      </div>
      {filtered.length === 0 ? (
        <p className="text-xs text-zinc-600">No anomalies detected.</p>
      ) : (
        <div className="space-y-1.5">
          {filtered.map((a, i) => (
            <div key={i}
              onClick={() => a.step_id && onFocus(a.step_id)}
              className={`rounded px-2 py-1.5 text-xs cursor-pointer border ${
                a.severity === 'ERROR' ? 'border-red-400/30 bg-red-400/5 text-red-300' :
                a.severity === 'WARNING' ? 'border-amber-400/30 bg-amber-400/5 text-amber-300' :
                'border-zinc-600 bg-zinc-900 text-zinc-400'
              } hover:opacity-80`}
            >
              {a.message}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
```

**Card 5 — Cost & Token Ledger:**

Simple table: call (Classify / Plan / Synthesis), input_tokens, output_tokens, cost_usd. Total row.

---

## Task 3 — Wire HealthRail into TraceModal

**File:** `platform/src/components/trace/TraceModal.tsx`

Replace the T2 placeholder div with the real HealthRail:

```tsx
import { HealthRail } from './HealthRail'
import { detectAnomalies } from '@/lib/admin/anomaly_detector'

// Inside TraceModal render, compute anomalies:
const anomalies = useMemo(() => detectAnomalies(trace), [trace])

// Replace placeholder div:
<div className="border-l border-[rgba(212,175,55,0.1)] overflow-y-auto">
  <HealthRail
    trace={trace}
    anomalies={anomalies}
    onFocusStep={setSelectedStepId}
  />
</div>
```

---

## Task 4 — SearchFilter + LifecycleGraph integration

**New file:** `platform/src/components/trace/SearchFilter.tsx`

A small input that appears when the user presses `/` on the trace modal:

```tsx
interface SearchFilterProps {
  value: string
  onChange: (v: string) => void
  onClose: () => void
}

export function SearchFilter({ value, onChange, onClose }: SearchFilterProps) {
  const ref = useRef<HTMLInputElement>(null)
  useEffect(() => { ref.current?.focus() }, [])
  
  return (
    <div className="sticky top-0 z-20 bg-[oklch(0.10_0.012_70)] px-3 py-2 border-b border-[rgba(212,175,55,0.15)]">
      <div className="flex items-center gap-2">
        <span className="text-[rgba(212,175,55,0.5)] text-sm">/</span>
        <input
          ref={ref}
          value={value}
          onChange={e => onChange(e.target.value)}
          onKeyDown={e => { if (e.key === 'Escape') { onChange(''); onClose() } }}
          placeholder="Filter steps…"
          className="bg-transparent text-sm text-zinc-200 placeholder:text-zinc-600 outline-none flex-1"
        />
        {value && (
          <button onClick={() => { onChange(''); onClose() }} className="text-zinc-500 text-xs">✕</button>
        )}
      </div>
    </div>
  )
}
```

In `LifecycleGraph`, add a `searchFilter` prop. When set, dim nodes that don't match (0.2 opacity), keep matching nodes full opacity. Matching: step name, step type, or `bundle` field contains the filter string (case-insensitive).

In `TraceModal`, add the `/` key handler:

```typescript
if (e.key === '/' && !e.target.matches('input')) {
  e.preventDefault()
  setShowSearch(true)
}
```

---

## Task 5 — ShortcutHelpOverlay

**New file:** `platform/src/components/trace/ShortcutHelpOverlay.tsx`

A centered overlay (z-[55], dark background) triggered by `?` key:

```tsx
const shortcuts = [
  { key: 'j / k', desc: 'Next / previous step' },
  { key: '1 – 9', desc: 'Jump to step N' },
  { key: '/', desc: 'Filter lifecycle graph' },
  { key: 'c', desc: 'Copy step JSON to clipboard' },
  { key: '?', desc: 'Toggle this help' },
  { key: 'Esc', desc: 'Close / go back' },
]
```

Dismiss on `?` again, `Esc`, or click outside.

---

## Task 6 — Virtualize long result tables

**File:** `platform/src/components/trace/step_detail/FetchSqlDetail.tsx`

For the Kept/Dropped tabs: if `items.length > 100`, use windowed rendering. React's built-in approach without an external library:

```tsx
const PAGE_SIZE = 50
const [page, setPage] = useState(0)
const paged = items.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE)

// Render paged items + Prev/Next pagination buttons
```

Do the same in `ContextAssemblyDetail` for the waterfall item list.

---

## Task 7 — Accessibility pass

For all trace components:
- Every interactive element (buttons, node divs, tabs) has `role` and `aria-label` where needed.
- `data-testid` attributes are on all key elements for test targeting.
- Color is never the only means of conveying status — every status has a text label (INCLUDED / TRUNCATED / DROPPED, not just color).
- The trace modal has `role="dialog"`, `aria-modal="true"`, `aria-label="Query Trace"`.
- Focus is trapped inside the modal (basic focus trap: Tab cycles within modal, Shift-Tab reverses).
- GhostPill has `aria-label` with full label + tooltip text.

---

## Task 8 — Architecture documentation

**New file:** `platform/src/app/(super-admin)/admin/trace/README.md`

Wait — per ROOT_FILE_POLICY, docs go to `00_ARCHITECTURE/`. Create instead:

**New file:** `00_ARCHITECTURE/QUERY_TRACE_IMPLEMENTATION_v1_0.md`

Cover:
- The three-table data model (context_assembly_log, plan_alternatives_log, synthesis_quality_scorecard)
- The trace assembler contract (TraceDocument interface)
- How to add a new step type to the lifecycle graph (3-step guide: new node component, new step_detail variant, register in STEP_ORDER)
- How to add a new anomaly detector (add a function to anomaly_detector.ts + test)
- The baseline stats refresh cadence

Minimum 2 pages.

---

## Task 9 — TypeScript check

```bash
cd platform && npx tsc --noEmit 2>&1 | tail -30
```

Zero new type errors.

---

## Task 10 — Tests

```bash
cd platform && npx vitest run \
  src/__tests__/components/trace/health/ \
  src/__tests__/lib/admin/anomaly_detector.test.ts \
  --reporter=verbose 2>&1 | tail -60
```

Write tests covering:
1. `detectAnomalies` — plan latency outlier (>2× p50), failed fetch, empty fetch, budget pressure (>30% drop), priority violation, low citation density, good trace (0 anomalies).
2. `HealthVerdictCard` — HEALTHY / DEGRADED / FAILED renders correctly.
3. `StageHealthRow` — green/amber/red latency bar based on ratio.
4. `AnomalyCallouts` — renders each anomaly, filter by errors only, click calls onFocus with step_id.
5. `SearchFilter` — typing filters LifecycleGraph nodes, Esc clears.
6. `ShortcutHelpOverlay` — renders all shortcuts, dismisses on Esc.
7. Accessibility checks: trace modal has `role="dialog"`, nodes have `aria-label`.

Minimum 25 tests.

---

## Acceptance Criteria

| AC | Check |
|---|---|
| AC.T3.1 | HealthRail renders in the right zone (320px) for all recent queries |
| AC.T3.2 | Per-stage health strip shows green/amber/red latency bars vs baselines for each stage |
| AC.T3.3 | All 5 anomaly detectors fire correctly when their trigger conditions are met |
| AC.T3.4 | Clicking an anomaly callout selects the corresponding lifecycle node |
| AC.T3.5 | Anomaly severity filter (All / Errors / Warnings) works correctly |
| AC.T3.6 | If `baselines.sample_size < 30`, an amber "unreliable baselines" warning shows in Card 3 |
| AC.T3.7 | `/` key opens search filter; typing dims non-matching lifecycle nodes; Esc clears |
| AC.T3.8 | `?` key toggles ShortcutHelpOverlay with all 6 shortcuts listed |
| AC.T3.9 | Fetch result tables and context assembly waterfall paginate at 50 items (no DOM overflow) |
| AC.T3.10 | Trace modal has `role="dialog"` + `aria-modal="true"`; all status badges have text labels |
| AC.T3.11 | `tsc --noEmit` exits clean |
| AC.T3.12 | ≥ 25 tests pass |
| AC.T3.13 | `00_ARCHITECTURE/QUERY_TRACE_IMPLEMENTATION_v1_0.md` created covering data model + extension guides |

---

## Priority order

1. Must ship: Tasks 1, 2, 3 (anomaly detector + HealthRail + wiring — the core T3 value)
2. Should ship: Tasks 4, 5 (SearchFilter + ShortcutHelp)
3. Should ship: Task 6 (pagination hardening)
4. Nice to have: Task 7 (full a11y pass)
5. Nice to have: Task 8 (architecture doc)
6. Always run: Tasks 9, 10 (tsc + tests)

---

## Do NOT do

- Do not change T1 backend code or T2 UI components beyond the specific extensions listed
- Do not add a new DB migration
- Do not implement real-time data fetching or WebSocket
- Do not rename or remove any `data-testid` attributes added in T2

---

## How to start

Open the Madhav project (`/Users/Dev/Vibe-Coding/Apps/Madhav/`) in Anti-Gravity.
Run: **"Read CLAUDECODE_BRIEF_TRACE_T3.md and execute it."**
