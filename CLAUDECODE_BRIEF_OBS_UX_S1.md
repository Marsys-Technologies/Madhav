---
session_id: OBS-UX-S1
status: COMPLETE
executor: claude-code-antigravity
phase: Observatory UX Elevation — Foundation + Charts
estimated_effort: medium (3–5 hours)
---

# CLAUDECODE_BRIEF — OBS-UX-S1: Foundation Parity + Chart Dark Mode

## Mission
The Observatory Overview page was redesigned in OBS-S1/S2/S3 and uses a rich dark charcoal + gold brand language. The three other tabs — Events, Budgets, Reconcile — were not updated to match. They still render with generic light-mode defaults that look completely out of place next to the Overview. Additionally, the two recharts components (CostOverTimeChart, CostByModelChart) have white SVG backgrounds that clash with the dark card they're embedded in.

This session establishes the foundation that S2/S3/S4 build on:
1. Extract shared Observatory UI primitives into a `shared/` folder
2. Apply the dark charcoal page shell to EventsClient, the Budgets page, and the Reconciliation page
3. Fix recharts dark theming in both chart components
4. Extend STAGE_COLORS in utils.ts for the three new pipeline stages unlocked by migration 041

## Design System Reference
All brand tokens to use — never deviate from these:

```
Page background:       bg-[var(--brand-charcoal,oklch(0.10_0.012_70))]
Card background:       bg-[oklch(0.11_0.010_70)]
Elevated card / input: bg-[oklch(0.13_0.008_70)]
Primary heading text:  text-[#fce29a]
Gold accent:           text-[#d4af37]   /   #d4af37
Section label text:    text-[rgba(212,175,55,0.45)]
Subtle label text:     text-[rgba(212,175,55,0.30)]
Border subtle:         border-[rgba(212,175,55,0.10)]
Border card:           border-[rgba(212,175,55,0.12)]
Border active:         border-[rgba(212,175,55,0.22)]
Active nav bg:         bg-[rgba(212,175,55,0.12)]
Recharts grid stroke:  rgba(212,175,55,0.08)
Recharts axis tick:    rgba(212,175,55,0.40)
Recharts axis line:    rgba(212,175,55,0.15)
```

## Deliverable 1 — Shared Observatory Primitives

Create `platform/src/lib/components/observatory/shared/` directory with:

### `platform/src/lib/components/observatory/shared/SectionLabel.tsx`
```tsx
export function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <p className="mb-3 text-[10px] font-semibold uppercase tracking-widest text-[rgba(212,175,55,0.40)]">
      {children}
    </p>
  )
}
```

### `platform/src/lib/components/observatory/shared/ObsPageShell.tsx`
A wrapper that applies the dark charcoal background, page header pattern, and optional QuickDateToggle. All Observatory pages that aren't Overview should use this.

```tsx
'use client'
import * as React from 'react'

interface ObsPageShellProps {
  title: string
  subtitle?: string
  headerRight?: React.ReactNode
  children: React.ReactNode
  testId?: string
}

export function ObsPageShell({ title, subtitle, headerRight, children, testId }: ObsPageShellProps) {
  return (
    <div
      data-testid={testId}
      className="min-h-full bg-[var(--brand-charcoal,oklch(0.10_0.012_70))]"
    >
      {/* Page header */}
      <div className="border-b border-[rgba(212,175,55,0.10)] px-6 py-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h1 className="font-heading text-xl font-semibold text-[#fce29a] tracking-wide">
              {title}
            </h1>
            {subtitle && (
              <p className="mt-0.5 text-xs text-[rgba(212,175,55,0.45)]">{subtitle}</p>
            )}
          </div>
          {headerRight && <div>{headerRight}</div>}
        </div>
      </div>

      {/* Page content */}
      <div className="flex flex-col gap-8 p-6">
        {children}
      </div>
    </div>
  )
}
```

### `platform/src/lib/components/observatory/shared/index.ts`
```ts
export { SectionLabel } from './SectionLabel'
export { ObsPageShell } from './ObsPageShell'
```

## Deliverable 2 — Update OverviewClient to use shared primitives

In `platform/src/lib/components/observatory/pages/OverviewClient.tsx`:
- Import `SectionLabel` from `../shared` instead of defining it inline
- Remove the inline `SectionLabel` function definition at the bottom
- Keep `QuickDateToggle` and `DATE_PRESETS` local to OverviewClient (they're Overview-specific)

## Deliverable 3 — Apply ObsPageShell to EventsClient

In `platform/src/lib/components/observatory/pages/EventsClient.tsx`:

Replace the outer `<div className="flex flex-col gap-4">` with `<ObsPageShell>`. The page should look like this:

```tsx
return (
  <ObsPageShell
    title="LLM Events"
    subtitle="Per-call telemetry across all provider stacks"
    testId="observatory-events"
    headerRight={
      <button
        type="button"
        onClick={() => setGroupByQuery(g => !g)}
        className={cn(
          'rounded-lg border px-3 py-1.5 text-xs font-medium transition-colors',
          groupByQuery
            ? 'border-[rgba(212,175,55,0.4)] bg-[rgba(212,175,55,0.12)] text-[#d4af37]'
            : 'border-[rgba(212,175,55,0.12)] text-[rgba(212,175,55,0.45)] hover:text-[#d4af37]',
        )}
      >
        {groupByQuery ? '⊞ Grouped view' : '⊞ Group by query'}
      </button>
    }
  >
    {/* Advanced filters collapsible */}
    <details className="group">
      <summary className="inline-flex cursor-pointer items-center gap-1.5 text-[11px] font-medium text-[rgba(212,175,55,0.35)] hover:text-[rgba(212,175,55,0.65)] list-none select-none">
        <span aria-hidden="true" className="transition-transform group-open:rotate-90">▶</span>
        Advanced filters
      </summary>
      <div className="mt-3">
        <FiltersBar filters={filters} modelOptions={[]} onFiltersChange={setFilters} />
      </div>
    </details>

    {/* Content */}
    <section>
      <SectionLabel>{groupByQuery ? 'Queries' : 'Events'}</SectionLabel>
      <div className="rounded-xl border border-[rgba(212,175,55,0.10)] bg-[oklch(0.11_0.010_70)]">
        {/* table content */}
      </div>
    </section>
  </ObsPageShell>
)
```

Move the `groupByQuery` toggle button into the `headerRight` slot. Remove the `<div className="flex items-center justify-between mb-3">` header row that currently holds it.

## Deliverable 4 — Fix recharts dark theming

### `platform/src/lib/components/observatory/charts/CostOverTimeChart.tsx`

The recharts SVG renders a white background by default inside the dark card. Fix by passing explicit dark props to every recharts primitive:

```tsx
// CartesianGrid
<CartesianGrid strokeDasharray="3 3" stroke="rgba(212,175,55,0.08)" />

// XAxis
<XAxis
  dataKey="time"
  tickFormatter={(v: string) => formatBucketTime(v, granularity)}
  minTickGap={24}
  stroke="rgba(212,175,55,0.15)"
  tick={{ fill: 'rgba(212,175,55,0.40)', fontSize: 11 }}
/>

// YAxis
<YAxis
  tickFormatter={(v: number) => formatCostUSD(v)}
  width={84}
  stroke="rgba(212,175,55,0.15)"
  tick={{ fill: 'rgba(212,175,55,0.40)', fontSize: 11 }}
/>

// Legend
<Legend wrapperStyle={{ color: 'rgba(212,175,55,0.60)', fontSize: '11px' }} />

// CostTooltip inner div
<div className="rounded-lg border border-[rgba(212,175,55,0.12)] bg-[oklch(0.13_0.008_70)] p-2 text-xs shadow-lg">
```

Also add `style={{ background: 'transparent' }}` to the `<AreaChart>` component itself to prevent white SVG bleed:
```tsx
<AreaChart data={chartRows} onClick={handleChartClick as never} style={{ background: 'transparent' }}>
```

Remove the awkward `border-2 border-primary/40` conditional for `isStagePrimary` — all variants use the same card border. Update the outer `<div>` to always be:
```tsx
<div
  data-testid="cost-over-time-chart"
  data-dimension={dimension}
  data-series-count={seriesValues.length}
  className="h-72 w-full"
>
```
(The rounded card border is provided by the OverviewClient wrapper, not the chart itself.)

### `platform/src/lib/components/observatory/charts/CostByModelChart.tsx`

Apply the same recharts dark mode fixes:
```tsx
<CartesianGrid strokeDasharray="3 3" stroke="rgba(212,175,55,0.08)" />
<XAxis stroke="rgba(212,175,55,0.15)" tick={{ fill: 'rgba(212,175,55,0.40)', fontSize: 11 }} />
<YAxis stroke="rgba(212,175,55,0.15)" tick={{ fill: 'rgba(212,175,55,0.40)', fontSize: 11 }} width={84} />
```
Tooltip inner `<div>`:
```tsx
<div className="rounded-lg border border-[rgba(212,175,55,0.12)] bg-[oklch(0.13_0.008_70)] p-2 text-xs shadow-lg">
```
Add `style={{ background: 'transparent' }}` to `<BarChart>`.

## Deliverable 5 — Extend STAGE_COLORS for new pipeline stages

In `platform/src/lib/components/observatory/charts/utils.ts`, the `STAGE_COLORS` map is missing the three new stages added by migration 041. Add:

```ts
export const STAGE_COLORS: Record<LlmPipelineStage, string> = {
  classify: '#6366f1',
  compose: '#06b6d4',
  retrieve: '#f59e0b',
  synthesize: '#10b981',
  audit: '#ef4444',
  other: '#94a3b8',
  // Added by migration 041
  planner: '#a78bfa',         // violet — planning layer
  title: '#f472b6',           // pink — title generation
  history_summary: '#34d399', // emerald — history compression
}
```

Also update the TypeScript type in `platform/src/lib/db/schema/observatory.ts` — the `LlmPipelineStage` union likely doesn't include these three yet. Add them:
```ts
'planner' | 'title' | 'history_summary'
```
Check the exact type definition and add them appropriately.

## Deliverable 6 — Apply ObsPageShell to Budgets and Reconciliation server pages

The Budgets and Reconciliation pages are **server components**. They import their client sub-components. The quickest approach is to wrap the content in each page in a `<div>` with the charcoal background and proper padding while leaving the title in a consistent header block.

For budgets (`platform/src/app/(super-admin)/observatory/budgets/page.tsx`):
- Read the current file
- Wrap rendered output in a `<div className="min-h-full bg-[var(--brand-charcoal,oklch(0.10_0.012_70))]">`
- Add a proper page header `<div className="border-b border-[rgba(212,175,55,0.10)] px-6 py-5">` with h1 using `text-[#fce29a]`
- Wrap content in `<div className="flex flex-col gap-8 p-6">`

For reconciliation (`platform/src/app/(super-admin)/observatory/reconciliation/page.tsx`):
- Same pattern

## Acceptance Criteria

- [ ] AC.S1.1 — `ObsPageShell` and `SectionLabel` exist in `shared/` and are exported from `shared/index.ts`
- [ ] AC.S1.2 — OverviewClient imports SectionLabel from `../shared` (no inline duplicate)
- [ ] AC.S1.3 — EventsClient wraps in `ObsPageShell` with title "LLM Events" and Group toggle in headerRight
- [ ] AC.S1.4 — Budgets page has dark charcoal wrapper + brand h1
- [ ] AC.S1.5 — Reconciliation page has dark charcoal wrapper + brand h1
- [ ] AC.S1.6 — CostOverTimeChart passes dark stroke/tick/bg props to all recharts primitives; tooltip uses dark bg
- [ ] AC.S1.7 — CostByModelChart same dark recharts fixes as S1.6
- [ ] AC.S1.8 — STAGE_COLORS extended with planner/title/history_summary; LlmPipelineStage type updated
- [ ] AC.S1.9 — `npx tsc --noEmit` passes with 0 new errors
- [ ] AC.S1.10 — `npm run test -- --testPathPattern="observatory"` all pass

## may_touch
```
platform/src/lib/components/observatory/shared/**
platform/src/lib/components/observatory/pages/OverviewClient.tsx
platform/src/lib/components/observatory/pages/EventsClient.tsx
platform/src/lib/components/observatory/charts/CostOverTimeChart.tsx
platform/src/lib/components/observatory/charts/CostByModelChart.tsx
platform/src/lib/components/observatory/charts/utils.ts
platform/src/lib/db/schema/observatory.ts
platform/src/app/\(super-admin\)/observatory/budgets/page.tsx
platform/src/app/\(super-admin\)/observatory/reconciliation/page.tsx
platform/src/lib/components/observatory/__tests__/**
```

## must_not_touch
```
platform/src/lib/components/observatory/events/**
platform/src/lib/components/observatory/budget/**
platform/src/lib/components/observatory/reconciliation/**
platform/src/lib/components/observatory/kpi/**
platform/src/lib/components/observatory/filters/**
platform/src/lib/observatory/**
platform/src/app/api/**
platform/migrations/**
```
