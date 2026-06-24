---
session_id: TRACE-T2
title: Query Trace — Lifecycle Graph + Step Detail UI
status: COMPLETE
phase: TRACE-T2
executor: Anti-Gravity (Claude Code, claude-sonnet-4-6)
created_date: 2026-05-05
prerequisite: TRACE-T1 ACs confirmed (trace API returns full TraceDocument)
reference_plan: 00_ARCHITECTURE/QUERY_TRACE_REDESIGN_v1_0.md
---

# TRACE-T2 — Query Trace UI: Lifecycle Graph + Step Detail

## Objective

Build the visible trace UI: the modal frame, the lifecycle graph (left zone), the step detail panel
(center zone), the query header strip, and the timing/cost ribbon. The right-zone Health Rail is T3.

After this session, opening `/admin/trace/:query_id` renders a fully interactive trace with the
complete lifecycle graph, all seven step-detail variants, and keyboard navigation.

**Prerequisite:** T1 must be complete and `GET /api/admin/trace/:query_id` must return the full
`TraceDocument` shape. Do not start until T1 ACs are confirmed.

---

## Scope

```
may_touch:
  - platform/src/app/(super-admin)/admin/trace/[query_id]/page.tsx   # CREATE
  - platform/src/components/trace/TraceModal.tsx                     # CREATE
  - platform/src/components/trace/QueryHeaderStrip.tsx               # CREATE
  - platform/src/components/trace/TimingRibbon.tsx                   # CREATE
  - platform/src/components/trace/LifecycleGraph.tsx                 # CREATE
  - platform/src/components/trace/lifecycle/                         # CREATE directory
  - platform/src/components/trace/StepDetail.tsx                     # CREATE
  - platform/src/components/trace/step_detail/                       # CREATE directory
  - platform/src/components/trace/RawPayloadDialog.tsx               # CREATE
  - platform/src/lib/admin/trace_client.ts                           # CREATE
  - platform/src/__tests__/components/trace/                         # CREATE test files

must_not_touch:
  - platform/src/lib/admin/trace_assembler.ts        # T1 — do not change
  - platform/src/app/api/admin/trace/                # T1 — do not change
  - platform/src/lib/db/                             # T1 — do not change
  - platform/supabase/migrations/                    # T1 — do not change
  - platform/src/components/trace/health/            # T3
  - platform/src/components/trace/HealthRail.tsx     # T3
  - any existing non-trace UI routes or components
  - any test files outside components/trace/
```

---

## Design reference

Full spec is in `00_ARCHITECTURE/QUERY_TRACE_REDESIGN_v1_0.md`. Key parameters:

**Modal:** 92vw × 92vh, dark background, `--brand-gold` 1px border at 0.4 opacity, 12px radius.

**Three-zone grid (Row 2):**
```
grid-template-columns: 380px 1fr 320px
```
- Left 380px: LifecycleGraph (fixed, scrolls vertically)
- Center 1fr: StepDetail (fluid, scrolls vertically, sticky sub-header)
- Right 320px: HealthRail placeholder div in T2 (T3 fills it)

**Brand tokens:**
- `--brand-gold: oklch(0.78 0.13 80)` / hex approximation `#d4af37`
- Active gold: `bg-[rgba(212,175,55,0.12)] border border-[rgba(212,175,55,0.22)] text-[#d4af37]`
- Charcoal bg: `bg-[var(--brand-charcoal,oklch(0.10_0.012_70))]`
- Status: green = `text-emerald-400`, amber = `text-amber-400`, red = `text-red-400`

---

## Task 1 — Trace client

**New file:** `platform/src/lib/admin/trace_client.ts`

```typescript
import type { TraceDocument } from './trace_assembler'

export async function fetchTrace(queryId: string): Promise<TraceDocument> {
  const res = await fetch(`/api/admin/trace/${queryId}`, { cache: 'no-store' })
  if (!res.ok) throw new Error(`Trace fetch failed: ${res.status}`)
  return res.json() as Promise<TraceDocument>
}
```

---

## Task 2 — Page route

**New file:** `platform/src/app/(super-admin)/admin/trace/[query_id]/page.tsx`

```tsx
import { Suspense } from 'react'
import { TraceModal } from '@/components/trace/TraceModal'

export default function TracePage({ params }: { params: { query_id: string } }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <Suspense fallback={
        <div className="flex items-center gap-2 text-[rgba(212,175,55,0.6)] text-sm">
          <span className="animate-spin">◎</span> Loading trace…
        </div>
      }>
        <TraceModal queryId={params.query_id} />
      </Suspense>
    </div>
  )
}
```

This page is only accessible via the existing super-admin layout (which already enforces role checks). Do not add a second role check — rely on the layout.

---

## Task 3 — TraceModal

**New file:** `platform/src/components/trace/TraceModal.tsx`

```tsx
'use client'

import { useEffect, useRef, useState, useCallback } from 'react'
import { fetchTrace } from '@/lib/admin/trace_client'
import type { TraceDocument } from '@/lib/admin/trace_assembler'
import { QueryHeaderStrip } from './QueryHeaderStrip'
import { LifecycleGraph } from './LifecycleGraph'
import { StepDetail } from './StepDetail'
import { TimingRibbon } from './TimingRibbon'

interface TraceModalProps { queryId: string }

export function TraceModal({ queryId }: TraceModalProps) {
  const [trace, setTrace] = useState<TraceDocument | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [selectedStepId, setSelectedStepId] = useState<string>('synthesis')
  
  useEffect(() => {
    fetchTrace(queryId)
      .then(t => { setTrace(t); setSelectedStepId('synthesis') })
      .catch(e => setError(String(e)))
  }, [queryId])

  // Keyboard navigation
  // j/k = prev/next step, Esc = navigate back, c = copy step JSON, ? = toggle help
  // ...implement keyboard handler

  if (error) return (
    <div className="w-[92vw] h-[92vh] rounded-xl border border-[rgba(212,175,55,0.4)] bg-[oklch(0.10_0.012_70)] flex items-center justify-center">
      <p className="text-red-400 text-sm">Failed to load trace: {error}</p>
    </div>
  )

  if (!trace) return null

  return (
    <div
      data-testid="trace-modal"
      className="w-[92vw] h-[92vh] rounded-xl border border-[rgba(212,175,55,0.4)] bg-[oklch(0.10_0.012_70)] flex flex-col overflow-hidden"
    >
      {/* Row 1: Header strip */}
      <QueryHeaderStrip trace={trace} />
      
      {/* Row 2: Three-zone work area */}
      <div className="flex-1 min-h-0 grid" style={{ gridTemplateColumns: '380px 1fr 320px' }}>
        {/* Left: Lifecycle graph */}
        <div className="border-r border-[rgba(212,175,55,0.1)] overflow-y-auto">
          <LifecycleGraph
            trace={trace}
            selectedStepId={selectedStepId}
            onSelectStep={setSelectedStepId}
          />
        </div>
        
        {/* Center: Step detail */}
        <div className="overflow-y-auto">
          <StepDetail trace={trace} selectedStepId={selectedStepId} />
        </div>
        
        {/* Right: Health rail placeholder (T3) */}
        <div
          data-testid="health-rail-placeholder"
          className="border-l border-[rgba(212,175,55,0.1)] p-4 flex items-center justify-center"
        >
          <p className="text-[rgba(212,175,55,0.25)] text-xs text-center">
            Health rail<br/>(coming T3)
          </p>
        </div>
      </div>
      
      {/* Row 3: Timing + cost ribbon */}
      <TimingRibbon trace={trace} selectedStepId={selectedStepId} onSelectStep={setSelectedStepId} />
    </div>
  )
}
```

---

## Task 4 — QueryHeaderStrip

**New file:** `platform/src/components/trace/QueryHeaderStrip.tsx`

Renders the 56px top bar:
- Left: query text (truncated at 80 chars, full text via `title` attribute), max 50% width.
- Center pills: classification type + confidence (e.g. `holistic · 0.87`), total latency, total cost.
- Right: health badge (`HEALTHY`/`DEGRADED`/`FAILED`), query_id (mono 10px + copy button on hover), close button (links to `/admin/audit` or calls `window.history.back()`).

Health badge colors:
- HEALTHY: `bg-emerald-400/10 border border-emerald-400/30 text-emerald-400`
- DEGRADED: `bg-amber-400/10 border border-amber-400/30 text-amber-400`
- FAILED: `bg-red-400/10 border border-red-400/30 text-red-400`
- UNKNOWN: `bg-zinc-400/10 border border-zinc-400/30 text-zinc-400`

---

## Task 5 — LifecycleGraph

**New file:** `platform/src/components/trace/LifecycleGraph.tsx`

This is the main left-panel visualization. Renders as a vertical flow of nodes with connecting edges.

**Node components to create in `components/trace/lifecycle/`:**
- `ClassifyNode.tsx`
- `PlanNode.tsx`
- `FetchNode.tsx` (used for all fetch types — sql, gcs, vector — with `variant` prop)
- `ContextAssemblyNode.tsx`
- `SynthesisNode.tsx`
- `GhostPill.tsx` (alternatives: dim, dashed border, 0.4 opacity, tooltip with rationale)
- `EdgeConnector.tsx` (vertical line between nodes; horizontal lines for parallel fan-out/fan-in)

**Node visual spec:**

```tsx
// Shared node wrapper
function NodeWrapper({
  children, selected, status, testId
}: {
  children: React.ReactNode
  selected: boolean
  status: 'ok' | 'empty' | 'failed' | 'skipped'
  testId: string
}) {
  const borderClass = {
    ok: 'border-[rgba(212,175,55,0.5)]',
    empty: 'border-amber-400/50 border-dashed',
    failed: 'border-red-400/60',
    skipped: 'border-zinc-600/50',
  }[status]
  
  const ringClass = selected
    ? 'ring-2 ring-[rgba(212,175,55,0.8)] ring-offset-1 ring-offset-[oklch(0.10_0.012_70)]'
    : ''
  
  return (
    <div
      data-testid={testId}
      className={`rounded-lg border ${borderClass} ${ringClass} bg-[oklch(0.13_0.012_70)] p-3 cursor-pointer
        hover:border-[rgba(212,175,55,0.7)] transition-colors`}
    >
      {children}
    </div>
  )
}
```

**LifecycleGraph layout:**

Render nodes vertically with 16px gaps. Parallel fetch nodes render as a horizontal flex row (wrapping if >4 nodes, max 2 columns). Connecting lines use absolutely-positioned thin divs or SVG paths (your choice — keep it simple).

```tsx
// Structure:
// [ClassifyNode]
//   ↓ edge
// [PlanNode] + ghost pills for excluded bundles below
//   ↓ fan-out
// [FetchNode 1] [FetchNode 2] [FetchNode 3] ...  ← horizontal row
//   ↓ fan-in
// [ContextAssemblyNode]
//   ↓ edge
// [SynthesisNode]
```

**Inline content per node type:**

ClassifyNode:
```tsx
<p className="text-xs font-semibold text-[#d4af37]">classify</p>
<p className="text-xs text-zinc-300">{trace.classify?.type ?? '—'} · {trace.classify?.confidence?.toFixed(2) ?? '—'}</p>
{/* Top-3 alternative pills below: */}
<div className="mt-2 flex flex-wrap gap-1">
  {(trace.classify?.alternatives ?? []).slice(0,3).map((alt, i) => (
    <GhostPill key={i} label={`${alt.type} ${(alt.confidence*100).toFixed(0)}%`} tooltip={alt.rationale ?? ''} selected={i===0} />
  ))}
</div>
```

PlanNode:
```tsx
<p className="text-xs font-semibold text-[#d4af37]">plan</p>
<p className="text-xs text-zinc-300">{trace.plan?.included_bundles.length ?? 0} bundles</p>
{/* Excluded bundle ghost pills */}
<div className="mt-2 flex flex-wrap gap-1">
  {(trace.plan?.excluded_bundles ?? []).map((b, i) => (
    <GhostPill key={i} label={b.name} tooltip={b.rationale ?? 'No rationale'} selected={false} />
  ))}
</div>
```

FetchNode:
```tsx
const statusColor = fetch.error_class !== 'OK' ? 'text-red-400'
  : fetch.kept_count === 0 ? 'text-amber-400' : 'text-emerald-400'
// Shows: bundle name, raw→kept count, latency
<p className="text-xs font-semibold text-[#d4af37]">{fetch.bundle}</p>
<p className={`text-xs ${statusColor}`}>{fetch.raw_count}→{fetch.kept_count} items · {fetch.latency_ms}ms</p>
```

ContextAssemblyNode: Show `{included}/{total} items · {tokens_used}k tokens · {dropped} dropped`

SynthesisNode: Show `{model} · {input_tokens}in · {output_tokens}out · Q {scorecard?.composite_score?.toFixed(2) ?? '—'}`

---

## Task 6 — StepDetail + seven variants

**New file:** `platform/src/components/trace/StepDetail.tsx`

The center panel. Reads `selectedStepId` and renders the appropriate variant. Sticky 48px sub-header.

```tsx
export function StepDetail({ trace, selectedStepId }: { trace: TraceDocument; selectedStepId: string }) {
  const variant = resolveVariant(selectedStepId)
  // Variants: 'classify' | 'plan' | 'fetch_sql' | 'fetch_gcs' | 'fetch_vector' | 'context_assembly' | 'synthesis'
  return (
    <div className="flex flex-col h-full">
      {/* Sticky sub-header */}
      <div className="sticky top-0 z-10 bg-[oklch(0.10_0.012_70)] border-b border-[rgba(212,175,55,0.1)] px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <StepTypeBadge variant={variant} />
          <span className="text-sm font-medium text-zinc-200">{selectedStepId}</span>
        </div>
        <button onClick={() => copyStepJson(trace, selectedStepId)} className="text-xs text-zinc-500 hover:text-zinc-300">
          Copy JSON
        </button>
      </div>
      
      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {variant === 'classify' && <ClassifyDetail trace={trace} />}
        {variant === 'plan' && <PlanDetail trace={trace} />}
        {variant === 'fetch_sql' && <FetchSqlDetail trace={trace} stepId={selectedStepId} />}
        {variant === 'fetch_gcs' && <FetchGcsDetail trace={trace} stepId={selectedStepId} />}
        {variant === 'fetch_vector' && <FetchVectorDetail trace={trace} stepId={selectedStepId} />}
        {variant === 'context_assembly' && <ContextAssemblyDetail trace={trace} />}
        {variant === 'synthesis' && <SynthesisDetail trace={trace} />}
      </div>
    </div>
  )
}
```

**Create each variant in `components/trace/step_detail/`:**

**InputDecisionOutput wrapper** (shared by all variants):
```tsx
function Section({ title, children }: { title: 'Input' | 'Decision' | 'Output'; children: React.ReactNode }) {
  return (
    <div>
      <h3 className="text-[10px] font-semibold uppercase tracking-widest text-[rgba(212,175,55,0.4)] mb-2">{title}</h3>
      {children}
    </div>
  )
}
```

**ClassifyDetail** (Input / Decision / Output per §5.1 in plan doc):
- Input: query text in mono block.
- Decision: ranked list of alternatives. Selected has gold left border. Each row: rank, type label, confidence bar, rationale.
- Output: final type + confidence + one-line routing summary.

**PlanDetail** (§5.2):
- Input: classification result, available bundles count, model.
- Decision: two-column table (Included | Excluded) with rationale.
- Output: QueryPlan JSON block (pre-code, max-height 300px, overflow scroll).

**FetchSqlDetail** (§5.3):
- Input: SQL (syntax-highlighted mono block), parameters.
- Decision: filter description.
- Output: two-tab table (Kept | Dropped). Each row: item_id, score (bar), drop_reason (Dropped tab only). Paginate at 20 rows.

**FetchGcsDetail** (§5.4):
- Input: GCS URIs list.
- Decision: resolution map (cache hit / fresh / 404).
- Output: document list, tabs Loaded | Skipped | Failed. Click row → inline preview (first 500 chars).

**FetchVectorDetail** (§5.5):
- Input: embedder model, query text, top_K.
- Decision: `Rechart` bar chart of similarity score distribution. Threshold line.
- Output: ranked table. Columns: rank, chunk_id, similarity (bar), snippet, was_kept.

**ContextAssemblyDetail** — The hero visualization (§5.6):
- Input: per-bundle summaries.
- Decision: The Context Waterfall:
  ```
  Horizontal stacked bar (Preamble | L1 | L2.5) full-width
  ─────────────────────────────────────────────────────────
  Below: vertical list of all items in priority order.
  Each row: rank · source_item_id (truncated) · layer badge ·
            token_cost · relevance bar · status badge (INCLUDED/TRUNCATED/DROPPED)
  INCLUDED: emerald  TRUNCATED: amber  DROPPED: red/zinc
  ```
  Items are sorted by `item_rank`. Show INCLUDED first, then TRUNCATED, then DROPPED.
  Click any row → inline expand showing drop_reason and token budget info.
- Output: token ledger table (total, budget, preamble, L1, L2.5, dropped count).

**SynthesisDetail** (§5.7):
- Input: model, temperature, max_tokens, stop_reason.
- Decision: token usage (input/output/cache).
- Output: full response text. Below: quality scorecard table (5 rows, each with green/amber/red dot + check name + value).

---

## Task 7 — TimingRibbon

**New file:** `platform/src/components/trace/TimingRibbon.tsx`

88px tall, full-width bottom row.

Top 44px: horizontal Gantt. Map each step to a horizontal segment:
- x position = start time as fraction of total wall time
- width = duration as fraction of total wall time
- Color: gold for plan, blue for fetch, emerald for assemble, violet for synthesis

Parallel fetch steps stack in the same horizontal band (multiple colored bars stacked at 8px height with 2px gaps).

Hovering a Gantt segment calls `onSelectStep(stepId)`.

Bottom 44px: simple flex row showing cost breakdown:
- Plan: `${planCost}`
- Fetch: (flat cost if available)
- Synthesis: `${synthCost}`
- Total: `$${total}`

If `trace.synthesis` is null or costs are not available, show `—` placeholders.

---

## Task 8 — GhostPill component

**New file:** `platform/src/components/trace/lifecycle/GhostPill.tsx`

```tsx
interface GhostPillProps {
  label: string
  tooltip: string
  selected: boolean
}

export function GhostPill({ label, tooltip, selected }: GhostPillProps) {
  return (
    <div
      title={tooltip}
      className={`rounded px-1.5 py-0.5 text-[10px] border cursor-default ${
        selected
          ? 'border-[rgba(212,175,55,0.5)] text-[#d4af37] bg-[rgba(212,175,55,0.08)]'
          : 'border-zinc-700/50 text-zinc-500 opacity-50'
      }`}
    >
      {label}
    </div>
  )
}
```

---

## Task 9 — RawPayloadDialog

**New file:** `platform/src/components/trace/RawPayloadDialog.tsx`

A nested dialog (dialog within the trace modal) triggered by "View raw" links in step detail variants.

```tsx
interface RawPayloadDialogProps {
  title: string
  payload: unknown
  onClose: () => void
}

export function RawPayloadDialog({ title, payload, onClose }: RawPayloadDialogProps) {
  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [onClose])

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/70">
      <div className="w-[80vw] h-[70vh] rounded-xl border border-[rgba(212,175,55,0.3)] bg-[oklch(0.08_0.01_70)] flex flex-col">
        <div className="flex items-center justify-between px-4 py-3 border-b border-[rgba(212,175,55,0.1)]">
          <p className="text-sm font-medium text-[#d4af37]">{title}</p>
          <button onClick={onClose} className="text-zinc-400 hover:text-white text-sm">✕ Close</button>
        </div>
        <pre className="flex-1 overflow-auto p-4 text-xs text-zinc-300 font-mono whitespace-pre-wrap break-words">
          {JSON.stringify(payload, null, 2)}
        </pre>
      </div>
    </div>
  )
}
```

---

## Task 10 — Keyboard navigation in TraceModal

Implement the keyboard handler inside `TraceModal`:

```typescript
const STEP_ORDER = ['classify', 'plan', ...trace.fetches.map(f => f.bundle), 'context_assembly', 'synthesis']

useEffect(() => {
  const handler = (e: KeyboardEvent) => {
    if (e.key === 'j') {
      const idx = STEP_ORDER.indexOf(selectedStepId)
      if (idx < STEP_ORDER.length - 1) setSelectedStepId(STEP_ORDER[idx + 1])
    }
    if (e.key === 'k') {
      const idx = STEP_ORDER.indexOf(selectedStepId)
      if (idx > 0) setSelectedStepId(STEP_ORDER[idx - 1])
    }
    if (e.key === 'c') {
      // Copy selected step JSON
      const stepData = extractStepData(trace, selectedStepId)
      void navigator.clipboard.writeText(JSON.stringify(stepData, null, 2))
    }
    // Number keys 1-9 jump to step N
    const num = parseInt(e.key)
    if (!isNaN(num) && num >= 1 && num <= STEP_ORDER.length) {
      setSelectedStepId(STEP_ORDER[num - 1])
    }
  }
  window.addEventListener('keydown', handler)
  return () => window.removeEventListener('keydown', handler)
}, [selectedStepId, trace])
```

---

## Task 11 — TypeScript check

```bash
cd platform && npx tsc --noEmit 2>&1 | tail -30
```

Zero new type errors in files you touched.

---

## Task 12 — Tests

```bash
cd platform && npx vitest run \
  src/__tests__/components/trace/ \
  --reporter=verbose 2>&1 | tail -80
```

Write RTL tests covering:
1. `TraceModal` — renders loading state, renders with trace data, handles fetch error.
2. `QueryHeaderStrip` — HEALTHY / DEGRADED / FAILED health badge rendering.
3. `LifecycleGraph` — renders all step types, selected node has gold ring, click calls onSelectStep.
4. `ClassifyDetail` — renders alternatives ranked list, confidence bars visible.
5. `ContextAssemblyDetail` — INCLUDED items in emerald, DROPPED items show drop_reason, TRUNCATED items in amber.
6. `SynthesisDetail` — quality scorecard rows render, composite_score visible.
7. `TimingRibbon` — renders Gantt segments for each step, cost totals visible.
8. `GhostPill` — selected vs non-selected visual classes.
9. Keyboard navigation: `j`/`k` change selectedStepId, number keys jump to step N.

Minimum 30 tests.

---

## Acceptance Criteria

| AC | Check |
|---|---|
| AC.T2.1 | `/admin/trace/:query_id` renders the `TraceModal` with all three zones visible |
| AC.T2.2 | `LifecycleGraph` renders ClassifyNode, PlanNode, all FetchNodes, ContextAssemblyNode, SynthesisNode with correct inline data |
| AC.T2.3 | Ghost pills visible for classification alternatives (dim, dashed, tooltip on hover) and excluded plan bundles |
| AC.T2.4 | Clicking any lifecycle node updates center StepDetail panel content |
| AC.T2.5 | Selected node has gold ring; non-connected edges dim on selection |
| AC.T2.6 | All 7 step-detail variants render Input/Decision/Output sections with real data from trace |
| AC.T2.7 | ContextAssemblyDetail Context Waterfall renders INCLUDED/TRUNCATED/DROPPED rows with color coding |
| AC.T2.8 | TimingRibbon Gantt shows proportional segments for each step; hovering a segment calls onSelectStep |
| AC.T2.9 | Keyboard shortcuts `j`/`k`/`1-9`/`c` work as specified |
| AC.T2.10 | `RawPayloadDialog` opens from "View raw" link, closes on Esc |
| AC.T2.11 | `tsc --noEmit` exits clean |
| AC.T2.12 | ≥ 30 RTL tests pass |

---

## Priority order

1. Must ship: Tasks 3, 4, 5 (TraceModal + Header + LifecycleGraph)
2. Must ship: Task 6 — Classify, Plan, ContextAssembly, Synthesis variants (most diagnostic value)
3. Should ship: Fetch detail variants (FetchSql, FetchGcs, FetchVector)
4. Should ship: Tasks 7, 8, 9, 10 (TimingRibbon, GhostPill, RawPayloadDialog, keyboard nav)
5. Always run: Tasks 11, 12 (tsc + tests)

---

## Do NOT do

- Do not implement the Health Rail (that's T3 — leave the 320px column as a placeholder)
- Do not modify T1 backend code
- Do not change any existing audit view or observatory components
- Do not add real-time streaming or WebSocket — use fetch + no-store cache

---

## How to start

Open the Madhav project (`/Users/Dev/Vibe-Coding/Apps/Madhav/`) in Anti-Gravity.
Run: **"Read CLAUDECODE_BRIEF_TRACE_T2.md and execute it."**
