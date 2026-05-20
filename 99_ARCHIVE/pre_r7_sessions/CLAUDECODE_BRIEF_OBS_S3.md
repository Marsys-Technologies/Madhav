---
session_id: OBS-S3
title: Observatory — UX Redesign
status: COMPLETE
phase: OBS-S3
executor: Anti-Gravity (Claude Code, claude-sonnet-4-6)
created_date: 2026-05-05
prerequisite: OBS-S1 + OBS-S2 ACs confirmed (data flows, portal shell integrated)
reference_plan: 00_ARCHITECTURE/OBSERVATORY_REDESIGN_PLAN_v1_0.md §3.3
---

# OBS-S3 — Observatory UX Redesign

## Objective

Restructure the Overview page so it communicates the three most important metrics
at a glance, degrades gracefully when no data exists, and uses the brand gold accent
for the primary value. Add an actionable empty state. Simplify the section headings.
Add a group-by-query toggle to the Events page.

**Do not start this session until OBS-S1 and OBS-S2 are both confirmed complete.**

---

## Scope

```
may_touch:
  - platform/src/lib/components/observatory/pages/OverviewClient.tsx
  - platform/src/lib/components/observatory/kpi/KpiTilesRow.tsx
  - platform/src/lib/components/observatory/kpi/KpiTile.tsx
  - platform/src/lib/components/observatory/EmptyObservatoryState.tsx   # CREATE
  - platform/src/lib/components/observatory/pages/EventsClient.tsx
  - platform/src/app/api/admin/observatory/events/route.ts

must_not_touch:
  - platform/src/lib/observatory/queries.ts                   # query layer — not this session
  - platform/src/components/observatory/ObservatorySubNav.tsx # done in OBS-S2
  - platform/src/app/(super-admin)/observatory/layout.tsx     # done in OBS-S2
  - platform/src/lib/components/observatory/charts/          # done in OBS-S2
  - platform/src/lib/components/observatory/filters/         # done in OBS-S2
  - any migration files
```

---

## Task 1 — Create EmptyObservatoryState component

**New file:** `platform/src/lib/components/observatory/EmptyObservatoryState.tsx`

```tsx
'use client'

interface EmptyObservatoryStateProps {
  /** The date range currently selected — shown in the message so users
   *  know the filter is active and data might exist outside the range. */
  dateRangeLabel?: string
}

export function EmptyObservatoryState({ dateRangeLabel }: EmptyObservatoryStateProps) {
  return (
    <div
      data-testid="observatory-empty-state"
      className="flex flex-col items-center justify-center gap-4 rounded-lg border border-[rgba(212,175,55,0.18)] bg-[rgba(212,175,55,0.04)] px-8 py-14 text-center"
    >
      <div className="text-3xl opacity-40">◎</div>
      <div>
        <p className="text-sm font-medium text-[rgba(212,175,55,0.85)]">
          No LLM calls recorded{dateRangeLabel ? ` in the last ${dateRangeLabel}` : ''}
        </p>
        <p className="mt-1 text-xs text-muted-foreground">
          Every query you send through the portal is tracked here automatically.
        </p>
      </div>
      <div className="mt-2 rounded border border-[rgba(212,175,55,0.12)] bg-background/60 px-5 py-3 text-left text-xs text-muted-foreground">
        <p className="mb-1 font-semibold text-[rgba(212,175,55,0.6)]">If you've sent queries and still see this:</p>
        <ol className="list-decimal space-y-0.5 pl-4">
          <li>Check that the pricing seed has been applied to the database</li>
          <li>Verify <code className="rounded bg-muted px-1 py-0.5">MARSYS_FLAG_OBSERVATORY_ENABLED=true</code></li>
          <li>Open the Events tab — partial rows may appear there</li>
          <li>Try a wider date range — data may fall outside the current window</li>
        </ol>
      </div>
    </div>
  )
}
```

---

## Task 2 — Add hero-3 mode to KpiTilesRow

**File:** `platform/src/lib/components/observatory/kpi/KpiTilesRow.tsx`

### 2a — Add a `mode` prop

Add an optional `mode?: 'hero3' | 'full'` prop to `KpiTilesRowProps`. Default is `'full'`.

### 2b — Hero-3 layout branch

When `mode === 'hero3'`, render only three tiles (Total cost, Requests, Latency) in a
3-column grid with larger visual weight. When `mode === 'full'` (default), render exactly
as before with all 6 tiles — this preserves all existing tests.

Add this at the top of the render body (before the existing loading/error branch):

```tsx
  // hero3 mode: 3 large tiles above the fold
  if (mode === 'hero3') {
    const costDelta = summary
      ? buildDelta(summary.total_cost_usd, summary.total_cost_usd_delta, true)
      : null
    const latencyDelta = summary
      ? buildDelta(summary.p50_latency_ms, summary.p50_latency_ms_delta, true)
      : null
    return (
      <div
        data-testid="kpi-tiles-row-hero"
        className="grid grid-cols-1 gap-4 sm:grid-cols-3"
      >
        <KpiTile
          testId="kpi-cost-hero"
          label="Total cost"
          value={
            summary ? (
              <span className="text-2xl font-bold text-[var(--brand-gold,oklch(0.78_0.13_80))]">
                {formatUsd(summary.total_cost_usd)}
              </span>
            ) : undefined
          }
          delta={costDelta}
          loading={loading && !summary}
          error={error}
          onRetry={onRetry}
          title="Total computed cost across all LLM calls in the selected period"
        />
        <KpiTile
          testId="kpi-requests-hero"
          label="LLM Calls"
          value={summary ? formatRequests(summary.total_requests) : undefined}
          loading={loading && !summary}
          error={error}
          onRetry={onRetry}
          title="Total number of individual LLM API calls (planner + synthesis)"
        />
        <KpiTile
          testId="kpi-latency-hero"
          label="Avg latency"
          value={summary ? formatLatencyMs(summary.p50_latency_ms) : undefined}
          secondary={summary ? `p95 ${formatLatencyMs(summary.p95_latency_ms)}` : undefined}
          delta={latencyDelta}
          loading={loading && !summary}
          error={error}
          onRetry={onRetry}
          title="Median (p50) and 95th-percentile LLM call latency"
        />
      </div>
    )
  }
```

The `buildDelta`, `formatUsd`, `formatLatencyMs`, `formatRequests` are all already in
scope from the existing imports in this file. Do not change the existing `'full'` mode
render path at all.

---

## Task 3 — Restructure OverviewClient to hero layout

**File:** `platform/src/lib/components/observatory/pages/OverviewClient.tsx`

### 3a — Add import

```typescript
import { EmptyObservatoryState } from '../EmptyObservatoryState'
```

### 3b — Replace the return block

Replace the current `return (...)` with the restructured version below. The data-fetching
logic (`refetch`, `useEffect`, `useState`) is unchanged — only the JSX render changes.

```tsx
  // Determine if we have loaded data with zero calls
  const hasNoData = !loading && !error && summary !== null && summary.total_requests === 0

  return (
    <div data-testid="observatory-overview" className="flex flex-col gap-6 p-6">
      {/* Filter bar */}
      <FiltersBar
        filters={filters}
        modelOptions={modelOptions}
        onFiltersChange={setFilters}
      />

      {/* Error state */}
      {error ? (
        <div
          data-testid="observatory-overview-error"
          role="alert"
          className="rounded border border-destructive/40 bg-destructive/5 p-3 text-sm"
        >
          {error}
        </div>
      ) : null}

      {/* Empty state — shown only when data has loaded and is genuinely zero */}
      {hasNoData ? (
        <EmptyObservatoryState dateRangeLabel={filters.preset !== 'custom' ? filters.preset : undefined} />
      ) : (
        <>
          {/* Zone 1 — Hero KPIs */}
          <KpiTilesRow
            summary={summary ?? undefined}
            loading={loading && !summary}
            mode="hero3"
            onRetry={() => void refetch(filters)}
          />

          {/* Zone 2 — Cost over time */}
          <section data-testid="observatory-overview-timeseries">
            <h2 className="mb-3 text-xs font-semibold uppercase tracking-widest text-[rgba(212,175,55,0.45)]">
              Cost over time
            </h2>
            <CostOverTimeChart
              data={timeseries}
              dimension="provider"
              granularity="day"
              loading={loading && !timeseries}
              onRetry={() => void refetch(filters)}
            />
          </section>

          {/* Zone 3 — Secondary breakdowns (collapsible on mobile) */}
          <details open className="group">
            <summary className="mb-3 cursor-pointer list-none text-xs font-semibold uppercase tracking-widest text-[rgba(212,175,55,0.35)] hover:text-[rgba(212,175,55,0.6)]">
              ↳ Breakdown by provider &amp; stage
            </summary>
            <div className="grid gap-4 lg:grid-cols-2">
              <section data-testid="observatory-overview-provider-breakdown">
                <h3 className="mb-2 text-xs font-medium text-muted-foreground">By provider</h3>
                <CostByModelChart
                  data={breakdowns.provider}
                  loading={loading && !breakdowns.provider}
                  onRetry={() => void refetch(filters)}
                />
              </section>
              <section data-testid="observatory-overview-stage-breakdown">
                <h3 className="mb-2 text-xs font-medium text-muted-foreground">By pipeline stage</h3>
                <CostByModelChart
                  data={breakdowns.pipeline_stage}
                  loading={loading && !breakdowns.pipeline_stage}
                  onRetry={() => void refetch(filters)}
                />
              </section>
            </div>
          </details>

          {/* Full 6-tile KPI detail row */}
          <details className="group">
            <summary className="mb-3 cursor-pointer list-none text-xs font-semibold uppercase tracking-widest text-[rgba(212,175,55,0.35)] hover:text-[rgba(212,175,55,0.6)]">
              ↳ All metrics
            </summary>
            <KpiTilesRow
              summary={summary ?? undefined}
              loading={loading && !summary}
              onRetry={() => void refetch(filters)}
            />
          </details>
        </>
      )}
    </div>
  )
```

**Note:** The `filters.preset` field comes from `useObservatoryFilters` — check the
`ObservatoryFilters` type to confirm the exact field name for the preset.
If `filters` doesn't have a `preset` field, just pass `undefined` for `dateRangeLabel`.

---

## Task 4 — Events page: group-by-query toggle

This task has two parts: an API change and a UI change.

### 4a — API: add groupByQuery param to events route

**File:** `platform/src/app/api/admin/observatory/events/route.ts`

Read the file. In the GET handler, after parsing existing query params, check for
`groupByQuery=true`. If present, add a wrapper query that aggregates `llm_usage_events`
by `conversation_id` (which carries the query_id from the OBS-S1 wiring):

```typescript
// Inside the GET handler, before the main query:
const groupByQuery = url.searchParams.get('groupByQuery') === 'true'

if (groupByQuery) {
  // Aggregate: one row per conversation_id (= query)
  // Returns: conversation_id, call_count, total_cost_usd, total_input_tokens,
  //          total_output_tokens, min_started_at (as query timestamp)
  const groupedSql = `
    SELECT
      conversation_id,
      COUNT(*) AS call_count,
      SUM(computed_cost_usd) AS total_cost_usd,
      SUM(input_tokens) AS total_input_tokens,
      SUM(output_tokens) AS total_output_tokens,
      MIN(started_at) AS started_at,
      MAX(finished_at) AS finished_at,
      array_agg(DISTINCT pipeline_stage) AS stages
    FROM llm_usage_events
    WHERE started_at >= $1 AND started_at < $2
    GROUP BY conversation_id
    ORDER BY started_at DESC
    LIMIT 100
  `
  // Use the same from/to params already parsed for the main query
  // Return as JSON with a { type: 'grouped', rows: [...] } envelope
  // so EventsClient can detect the mode
  const result = await db.query(groupedSql, [from, to])
  return Response.json({ type: 'grouped', rows: result.rows })
}
// ...existing flat query follows
```

Adapt this pattern to match the actual structure of the route handler you find in the file.
If the route uses a different date range parameter name or db client, mirror that pattern.

### 4b — UI: add toggle button to EventsClient

**File:** `platform/src/lib/components/observatory/pages/EventsClient.tsx`

Read the file. Add a toggle button above the events table:

```tsx
const [groupByQuery, setGroupByQuery] = React.useState(false)
```

Above the `<EventTable>` render, add:

```tsx
<div className="flex items-center justify-between mb-3">
  <h2 className="text-xs font-semibold uppercase tracking-widest text-[rgba(212,175,55,0.45)]">
    LLM Call Events
  </h2>
  <button
    type="button"
    onClick={() => setGroupByQuery(g => !g)}
    className={cn(
      'rounded border px-3 py-1 text-xs font-medium transition-colors',
      groupByQuery
        ? 'border-[rgba(212,175,55,0.4)] bg-[rgba(212,175,55,0.12)] text-[#d4af37]'
        : 'border-border bg-card text-muted-foreground hover:text-foreground',
    )}
  >
    {groupByQuery ? 'Grouped by query' : 'Group by query'}
  </button>
</div>
```

Pass `groupByQuery` as a query parameter when fetching events. When `groupByQuery=true`,
if the API returns `{ type: 'grouped', rows: [...] }`, render a simplified table with
columns: Query ID, Calls, Total Cost, Tokens (in/out), Timestamp. When `groupByQuery=false`,
render the existing `<EventTable>` as before.

If adapting the EventsClient is complex due to the existing architecture, implement the
grouped view as a simple `<table>` rendered inline when `groupByQuery === true`, without
modifying `EventTable.tsx` (which has tests).

---

## Task 5 — TypeScript check

```bash
cd platform && npx tsc --noEmit 2>&1 | tail -30
```

Zero new errors in files you touched.

---

## Task 6 — Run affected tests

```bash
cd platform && npx vitest run \
  src/lib/components/observatory/__tests__/kpi/ \
  src/lib/components/observatory/__tests__/pages/OverviewClient.test.tsx \
  --reporter=verbose 2>&1 | tail -60
```

All KPI and OverviewClient tests must pass. The `hero3` mode adds new tiles with new
`data-testid` attributes — do not remove or rename any existing `data-testid` values that
the tests use.

---

## Acceptance Criteria

| AC | Check |
|---|---|
| AC.S3.1 | `EmptyObservatoryState.tsx` exists at `lib/components/observatory/EmptyObservatoryState.tsx` |
| AC.S3.2 | `OverviewClient` renders `EmptyObservatoryState` when `summary.total_requests === 0` and not loading |
| AC.S3.3 | `KpiTilesRow` accepts `mode='hero3'` and renders 3 tiles with `data-testid="kpi-tiles-row-hero"` |
| AC.S3.4 | Hero cost tile value uses `text-[var(--brand-gold,oklch(0.78_0.13_80))]` class |
| AC.S3.5 | Full 6-tile mode (`mode='full'` default) unchanged — existing tests pass |
| AC.S3.6 | Events page has a "Group by query" toggle button visible above the table |
| AC.S3.7 | `tsc --noEmit` exits 0 (or only pre-existing unrelated errors) |
| AC.S3.8 | All KPI and OverviewClient tests pass |

---

## Priority order

If Anti-Gravity runs out of context, deliver in this order:

1. **Must ship:** Tasks 1, 2, 3 (EmptyObservatoryState + hero KPIs — this is the core ask)
2. **Should ship:** Task 4 (Events grouping — useful but lower priority)
3. **Nice to have:** Task 5, 6 (tsc + tests — always run if possible)

---

## Do NOT do

- Do not rename or remove any existing `data-testid` attributes (tests depend on them)
- Do not modify `EventTable.tsx` — it has tests; add grouped view inline in `EventsClient`
- Do not modify `FiltersBar.tsx`, `KpiTile.tsx` internal structure (already done in OBS-S2)
- Do not add migrations
- Do not add `reconciliation_variance_pct` to the hero tiles — it belongs on Reconciliation page only

---

## How to start

Open the Madhav project (`/Users/Dev/Vibe-Coding/Apps/Madhav/`) in Anti-Gravity.
Run: **"Read CLAUDECODE_BRIEF_OBS_S3.md and execute it."**
