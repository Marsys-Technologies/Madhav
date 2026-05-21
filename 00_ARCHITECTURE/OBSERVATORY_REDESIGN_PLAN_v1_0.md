---
artifact: OBSERVATORY_REDESIGN_PLAN_v1_0
canonical_id: OBSERVATORY_REDESIGN_PLAN
version: 1.0
status: CURRENT
created_date: 2026-05-05
project_code: MARSYS-JIS
phase_context: M5-incoming
authored_by: COWORK-OBS-ANALYSIS-2026-05-05
---

# Observatory Redesign Plan v1.0

*Complete execution plan for making the LLM Cost & Usage Observatory fully operational with accurate data and a portal-native UI.*

---

## §1 — Executive Summary

The Observatory currently shows zero LLM usage data despite the platform having served many queries since `MARSYS_FLAG_OBSERVATORY_ENABLED=true`. This is not a UI bug — the underlying data pipeline never writes to the Observatory's data store (`llm_usage_events`). Additionally, the Observatory's visual design is completely disconnected from the portal design system, making it feel like a different product.

Three independent failure layers must be addressed in order:

| Layer | Problem | Fix |
|---|---|---|
| **0 — Data** | AI SDK calls bypass the observed adapters; `llm_usage_events` is always empty | Wire synthesis + planner `onFinish` to `persistObservation()`; seed pricing |
| **1 — Design System** | `ObservatoryLayout` is a standalone design with no brand tokens, own nav, own header | Replace with `AppShell` + portal-native sub-navigation pattern |
| **2 — UX** | Information overload, non-functional date picker, no empty state, 10+ nav items | Redesign Overview: 3 hero KPIs above fold, progressive disclosure, actionable empty states |

Layer 0 must ship before Layer 1 or Layer 2 produce any observable improvement. The UI is structurally fine once it has data — the real urgency is the pipeline wiring gap.

---

## §2 — Root Cause Diagnosis

### §2.1 — Why `llm_usage_events` is empty

The Observatory queries exclusively from `llm_usage_events` (migration 038). The only code path that inserts into this table is `persistObservation()` in `platform/src/lib/llm/observability/persist.ts`. This function is called by the five `*_observed.ts` provider adapters:

```
anthropic_observed.ts  →  persistObservation()  →  llm_usage_events
openai_observed.ts     →  persistObservation()  →  llm_usage_events
gemini_observed.ts     →  persistObservation()  →  llm_usage_events
deepseek_observed.ts   →  persistObservation()  →  llm_usage_events
nim_observed.ts        →  persistObservation()  →  llm_usage_events
```

**Neither of the two active hot paths ever calls these adapters:**

**Hot path 1 — Planner** (`platform/src/lib/pipeline/manifest_planner.ts`):
Uses Vercel AI SDK `generateText()` directly with a raw `anthropic(model)` provider instance. It never touches `anthropic_observed.ts`. Token usage from `result.usage` is available in the `onFinish`-equivalent pattern but is never forwarded to `persistObservation()`.

**Hot path 2 — Synthesis** (`platform/src/lib/synthesis/single_model_strategy.ts`):
Uses Vercel AI SDK `streamText()` directly. The `onFinish` hook writes `cost_usd: null` to `llm_call_log` (migration 032 — a completely different table). An explicit TODO comment at line ~543 acknowledges: `// TODO(G.2): cost_usd is null — compute from...`. This code path never writes to `llm_usage_events`.

**Secondary gap — `writeObservatoryQueryEvent`** (added in GANGA-PLANNER-FIX-S1):
This writes one rollup row per query to `observatory_query_events`, not to `llm_usage_events`. It records `null` for all token counts and cost. This is a useful audit trail but does not feed the Observatory's KPI or chart queries, which all read `llm_usage_events`.

**Tertiary gap — pricing seed not verified**:
`computeCost()` in `cost.ts` requires rows in `llm_pricing_versions`. The seed script at `platform/src/lib/db/seed/observatory_pricing/seed_v1.ts` must be executed against production. If the table is empty, `PricingNotFoundError` is thrown and `computed_cost_usd` is null even when tokens are present.

### §2.2 — Why the design looks wrong

`ObservatoryLayout` in `platform/src/lib/components/observatory/Layout.tsx` renders its own full-page shell: its own `<header>`, its own `<nav>` sidebar with 10+ links, its own reload/settings icon buttons (currently disabled). It wraps children from `app/(super-admin)/observatory/layout.tsx` which bypasses `AppShell` entirely.

The portal brand system (`globals.css`) defines:
- `--brand-gold: oklch(0.78 0.13 80)` — the gold accent used throughout the rail, audit view, cockpit
- `--brand-charcoal`, `--brand-ink`, `--brand-vellum` — surface hierarchy tokens
- Chart tokens `--color-chart-1` through `--color-chart-5`
- `AppShellRail` already lists Observatory in `NAV_ITEMS` and activates it when `pathname.startsWith('/observatory')`

The Observatory never uses any of these tokens — it uses raw Tailwind utilities (`border-b`, `text-muted-foreground`, `bg-background`) without the brand layer, making it visually incoherent with the rest of the portal.

### §2.3 — UX Anti-Patterns Identified

1. **Non-functional date picker in `FiltersBar`**: The `ObservatoryLayout` header has a hardcoded "Last 7 days" text with disabled reload and settings buttons. The actual `DateRangePicker` component exists and works, but the layout's header controls are decorative-only.

2. **10+ navigation links with zero data**: The sidebar nav exposes: Overview, Events, Reconciliation, Budgets, Cost Arc, Cache, Pricing Diff, Anomaly, Cost/Quality, Replay, Export. Every one of these pages shows empty states or zeros. The visual weight of 10+ nav sections communicates complexity without delivering value.

3. **6 KPI tiles + 3 charts when all values are zero**: The Overview renders `KpiTilesRow` (6 tiles: Total cost, Requests, Total tokens, Avg cost/request, Latency p50/p95, Reconciliation variance) plus `CostOverTimeChart` plus 2x `CostByModelChart`. When `llm_usage_events` is empty, all values are `$0.00`, `0`, `0ms` — a screen full of zeros that communicates nothing actionable.

4. **No empty state with root cause explanation**: When data is absent, the UI does not tell the user *why* it is absent or what to do. A super-admin landing on this page has no indication that the data pipeline needs to be wired.

5. **Information hierarchy lost in the grid**: The 6-tile KPI grid treats `Total cost` (the primary metric) identically to `Reconciliation variance` (an operational detail). There is no visual hierarchy between "what you need to see at a glance" and "deep operational data."

---

## §3 — Execution Plan

Three sessions. Each is a self-contained `CLAUDECODE_BRIEF` targeting Anti-Gravity (Claude Code).

### §3.1 — Session OBS-S1: Data Pipeline Wiring

**Goal:** Every LLM call (planner + synthesis) writes a row to `llm_usage_events` with accurate token counts and computed cost. After this session, the Observatory Overview shows real numbers.

**Brief ID:** `OBS-S1-DATA-WIRING`

**Changes:**

**OBS-S1-A — Synthesis telemetry hook** (`single_model_strategy.ts`):

In the `onFinish` callback of `streamText()`, resolve the G.2 TODO:

```typescript
// After streamText onFinish receives usage:
import { persistObservation } from '@/lib/llm/observability/persist'
import { computeCost } from '@/lib/llm/observability/cost'

// Inside onFinish({ usage, finishReason }):
const costResult = await computeCost({
  provider: stack,                    // 'anthropic' | 'openai' | etc.
  model: selected_model_id,
  inputTokens: usage.promptTokens,
  outputTokens: usage.completionTokens,
}).catch(() => null)

await persistObservation({
  provider: stack,
  model: selected_model_id,
  pipeline_stage: 'synthesis',
  query_id: context.queryId ?? null,
  input_tokens: usage.promptTokens,
  output_tokens: usage.completionTokens,
  cache_read_tokens: (usage as any).cacheReadInputTokens ?? null,
  cache_creation_tokens: (usage as any).cacheCreationInputTokens ?? null,
  computed_cost_usd: costResult?.totalCost ?? null,
  pricing_version_id: costResult?.pricingVersionId ?? null,
  finish_reason: finishReason,
  latency_ms: Date.now() - requestStartMs,
  request_id: null,
  raw_request_body: null,     // redaction: omit prompt body from Observatory
  raw_response_body: null,
})
```

**OBS-S1-B — Planner telemetry hook** (`manifest_planner.ts`):

After `generateText()` returns, emit an observation from `result.usage`:

```typescript
// After: const result = await generateText({ ... })
const costResult = await computeCost({
  provider: PLANNER_STACK,
  model: plannerModel,
  inputTokens: result.usage.promptTokens,
  outputTokens: result.usage.completionTokens,
}).catch(() => null)

await persistObservation({
  provider: PLANNER_STACK,
  model: plannerModel,
  pipeline_stage: 'planner',
  query_id: opts.queryId ?? null,
  input_tokens: result.usage.promptTokens,
  output_tokens: result.usage.completionTokens,
  cache_read_tokens: null,
  cache_creation_tokens: null,
  computed_cost_usd: costResult?.totalCost ?? null,
  pricing_version_id: costResult?.pricingVersionId ?? null,
  finish_reason: result.finishReason,
  latency_ms: Date.now() - plannerStartMs,
  request_id: null,
  raw_request_body: null,
  raw_response_body: null,
})
```

**OBS-S1-C — Pricing seed verification**:

Run `platform/src/lib/db/seed/observatory_pricing/seed_v1.ts` against production Cloud SQL and verify `SELECT COUNT(*) FROM llm_pricing_versions` returns > 0. This is a prerequisite for `computeCost()` to succeed. If the seed has already run (INSERT ON CONFLICT DO NOTHING), this is a no-op.

Command: `cd platform && NEXT_PUBLIC_DATABASE_URL=$DATABASE_URL npx tsx src/lib/db/seed/observatory_pricing/seed_v1.ts`

**OBS-S1-D — `writeLlmCallLog` cost backfill**:

While wiring the synthesis hook, also resolve the `cost_usd: null` in `llm_call_log` writes (same `onFinish` callback) by populating `cost_usd` from `costResult?.totalCost ?? null`. This closes the G.2 TODO fully and keeps `llm_call_log` consistent with `llm_usage_events`.

**OBS-S1-E — `query_id` threading to planner**:

The planner currently does not receive `queryId`. The consume route generates `queryId` before calling the planner. Thread `queryId` as an optional parameter through:
- `consume/route.ts` → `PipelineRunner` → `ManifestPlanner.plan()` → `persistObservation()`

This enables per-query drilldown in the Observatory Events view.

**OBS-S1 Acceptance Criteria:**

| AC | Criterion |
|---|---|
| AC.S1.1 | `SELECT COUNT(*) FROM llm_usage_events` > 0 after one live query |
| AC.S1.2 | `computed_cost_usd IS NOT NULL` for at least one synthesis row |
| AC.S1.3 | `pipeline_stage = 'planner'` rows appear alongside `pipeline_stage = 'synthesis'` rows |
| AC.S1.4 | Observatory Overview KPIs show non-zero values after one live query |
| AC.S1.5 | `llm_pricing_versions` has ≥ 1 row in production |
| AC.S1.6 | tsc --noEmit exits 0 |
| AC.S1.7 | All pre-existing tests still pass; zero new failures |

**Files touched:**
- `platform/src/lib/synthesis/single_model_strategy.ts`
- `platform/src/lib/pipeline/manifest_planner.ts`
- `platform/src/lib/pipeline/pipeline_runner.ts` (queryId threading)
- `platform/src/app/api/chat/consume/route.ts` (queryId threading)
- `platform/src/lib/db/seed/observatory_pricing/seed_v1.ts` (run, not modified)

---

### §3.2 — Session OBS-S2: Design System Integration

**Goal:** Observatory looks and feels like it belongs to the portal. Same sidebar rail, same brand tokens, same header pattern. The standalone `ObservatoryLayout` is removed.

**Brief ID:** `OBS-S2-DESIGN-SYSTEM`

**Changes:**

**OBS-S2-A — Remove standalone `ObservatoryLayout`**:

Delete the standalone layout wrapper. Update `app/(super-admin)/observatory/layout.tsx` to use `AppShell` directly, exactly as `admin/layout.tsx` does:

```typescript
// app/(super-admin)/observatory/layout.tsx
import { AppShell } from '@/components/shared/AppShell'
import { ObservatorySubNav } from '@/components/observatory/ObservatorySubNav'

export default async function ObservatoryLayout({ children }) {
  const ctx = await getServerUserWithProfile()
  if (!ctx || ctx.profile.role !== 'super_admin') redirect('/dashboard')

  return (
    <AppShell
      user={ctx.user}
      profile={ctx.profile}
      breadcrumb={[{ label: 'Observatory', href: '/observatory', current: false }]}
    >
      <div className="flex h-full">
        <ObservatorySubNav />
        <main className="flex-1 overflow-auto p-6">{children}</main>
      </div>
    </AppShell>
  )
}
```

**OBS-S2-B — Create `ObservatorySubNav`** (replaces the sidebar inside `ObservatoryLayout`):

Consolidated from 10+ links to 4 primary sections with role-appropriate labels:

```
Overview          /observatory
Events            /observatory/events
Reconciliation    /observatory/reconciliation
Budgets           /observatory/budgets
─── Analytics ───
Cost Arc          /observatory/analytics/cost-arc
Cache             /observatory/analytics/cache
Anomalies         /observatory/analytics/anomaly
```

The three low-traffic analytics pages (Pricing Diff, Cost/Quality, Replay) are collapsed under an "Analytics" group header. Export is surfaced as a button on the Overview page, not a nav link.

Styling uses brand tokens: active link uses `bg-[rgba(212,175,55,0.12)] border border-[rgba(212,175,55,0.22)] text-[var(--brand-gold)]` (matching AppShellRail's active state pattern).

**OBS-S2-C — Apply brand tokens to all Observatory components**:

Sweep the following files and replace raw Tailwind utilities with brand tokens:

| Component | Replace | With |
|---|---|---|
| `KpiTile.tsx` | `bg-card border-border` card wrapper | `bg-[var(--brand-charcoal)] border border-[rgba(212,175,55,0.15)]` |
| `CostOverTimeChart.tsx` | Recharts `stroke` hardcoded color | `var(--color-chart-1)` |
| `CostByModelChart.tsx` | Recharts bar fill `hsl(var(...))` | `var(--color-chart-1)` through `var(--color-chart-5)` |
| `EventTable.tsx` | `text-muted-foreground` row text | Keep — this is a semantic token that already maps to correct value |
| `FiltersBar.tsx` | `bg-background border-border` toolbar | `bg-[var(--brand-charcoal)] border-b border-[rgba(212,175,55,0.15)]` |
| Section headings | Plain `text-foreground font-semibold` | Add `text-[var(--brand-gold-light)]` for section labels |

**OBS-S2-D — Wire the `DateRangePicker` into `FiltersBar`**:

The `DateRangePicker` component is correctly implemented and tested. `FiltersBar` already imports it. The issue is that `ObservatoryLayout`'s header had a non-functional "Last 7 days" text button. With `ObservatoryLayout` removed, `FiltersBar` is now the sole filter surface. Verify `useObservatoryFilters` default preset is `'7d'` and the picker fires `onChange` correctly through to the API query params.

**OBS-S2 Acceptance Criteria:**

| AC | Criterion |
|---|---|
| AC.S2.1 | Navigating to `/observatory` shows the portal `AppShellRail` with "Ob" active — no separate sidebar header |
| AC.S2.2 | Observatory sub-nav shows exactly 7 links (Overview, Events, Reconciliation, Budgets, Cost Arc, Cache, Anomalies) |
| AC.S2.3 | `ObservatoryLayout.tsx` is deleted; no import of it anywhere |
| AC.S2.4 | DateRangePicker responds to clicks and updates KPI data for the selected range |
| AC.S2.5 | KPI tile borders use `rgba(212,175,55,0.15)` — visible gold tint matching audit/cockpit card style |
| AC.S2.6 | tsc --noEmit exits 0; all Observatory component tests pass |

**Files touched:**
- `platform/src/app/(super-admin)/observatory/layout.tsx` (rewritten)
- `platform/src/lib/components/observatory/Layout.tsx` (deleted)
- `platform/src/components/observatory/ObservatorySubNav.tsx` (new)
- `platform/src/lib/components/observatory/kpi/KpiTile.tsx`
- `platform/src/lib/components/observatory/charts/CostOverTimeChart.tsx`
- `platform/src/lib/components/observatory/charts/CostByModelChart.tsx`
- `platform/src/lib/components/observatory/filters/FiltersBar.tsx`

---

### §3.3 — Session OBS-S3: UX Redesign

**Goal:** The Overview page communicates the three most important facts instantly, degrades gracefully when empty, and invites rather than overwhelms. Events drilldown is navigable per-query.

**Brief ID:** `OBS-S3-UX`

**Changes:**

**OBS-S3-A — Redesign Overview page layout**:

Replace the current flat 6-tile + 3-chart layout with a three-zone composition:

**Zone 1 — Hero KPIs (above the fold, always visible):**
Three large tiles with high visual weight, brand gold accents:

```
┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐
│  Total Cost          │  │  LLM Calls           │  │  Avg Latency        │
│  $0.0024             │  │  47                  │  │  p50: 2.1s          │
│  ▲ +12% vs yesterday │  │  ↔ —                 │  │  p95: 8.4s          │
└─────────────────────┘  └─────────────────────┘  └─────────────────────┘
```

Styled using `bg-[var(--brand-charcoal)] border border-[rgba(212,175,55,0.20)]` cards with the cost tile's primary value in `text-[var(--brand-gold)]`.

**Zone 2 — Cost over time chart (full width):**
`CostOverTimeChart` preserved as-is but with brand color tokens applied. Add a "by stage" toggle to split planner vs. synthesis costs in the same line chart.

**Zone 3 — Secondary breakdown (collapsible row):**
`CostByModelChart` (provider breakdown) + `TokenSplitBar` summary side by side. Default collapsed on mobile. On desktop, shown as a two-column row below the main chart.

Remove from Overview: the sixth KPI tile (Reconciliation variance) belongs on the Reconciliation page, not the Overview. Remove `CostByModelChart` second instance (pipeline_stage breakdown) — this is now in Zone 3.

**OBS-S3-B — Empty state with actionable guidance**:

When `llm_usage_events` has zero rows, render instead of the KPI grid:

```tsx
<EmptyObservatoryState />
```

Content:
```
Observatory is connected — waiting for LLM calls.

Every query you send through the portal is automatically
tracked here once the data pipeline is active.

If you're seeing this after sending queries:
  → Check that the pricing seed has been applied
  → Verify MARSYS_FLAG_OBSERVATORY_ENABLED=true
  → Check /observatory/events for any partial rows
```

This is a client-side check: if `summary.totalRequests === 0`, render `<EmptyObservatoryState>` instead of `<KpiTilesRow>`. The date range controls remain functional.

**OBS-S3-C — Events page: per-query drilldown**:

The Events table currently shows individual `llm_usage_events` rows. Add a `query_id` grouping toggle:

- **Default (flat view):** each row = one LLM call, sortable by `created_at`, `computed_cost_usd`, `latency_ms`
- **Grouped view:** rows grouped by `query_id`, showing: total cost for the query, call count (e.g., "1 planner + 1 synthesis"), total tokens, collapsed by default with an expand chevron

This requires a small API change in `events/route.ts`: add `groupByQuery=true` query param that returns aggregated rows. `query_plan_log` already has `query_id` — this can be JOINed to show the query text alongside each cost row.

**OBS-S3-D — Budget page: contextual threshold line on chart**:

`BudgetUtilizationChart.tsx` currently shows utilization bars. Add a reference line at the budget threshold. This is a single Recharts `<ReferenceLine>` addition — low-effort, high clarity.

**OBS-S3 Acceptance Criteria:**

| AC | Criterion |
|---|---|
| AC.S3.1 | Overview above-the-fold shows exactly 3 hero KPIs (Total Cost, LLM Calls, Avg Latency) |
| AC.S3.2 | When `totalRequests === 0`, `EmptyObservatoryState` renders with actionable copy |
| AC.S3.3 | Events page has a "Group by query" toggle that collapses per-LLM-call rows into per-query summaries |
| AC.S3.4 | Overview KPI for Total Cost renders in `var(--brand-gold)` color |
| AC.S3.5 | Reconciliation variance KPI is no longer on the Overview page |
| AC.S3.6 | tsc --noEmit exits 0; all Observatory tests pass |

**Files touched:**
- `platform/src/lib/components/observatory/pages/OverviewClient.tsx` (restructured)
- `platform/src/lib/components/observatory/kpi/KpiTilesRow.tsx` (3-tile hero layout)
- `platform/src/lib/components/observatory/EmptyObservatoryState.tsx` (new)
- `platform/src/lib/components/observatory/pages/EventsClient.tsx` (group toggle)
- `platform/src/app/api/admin/observatory/events/route.ts` (groupByQuery param)
- `platform/src/lib/components/observatory/charts/BudgetUtilizationChart.tsx` (reference line)

---

## §4 — Session Execution Order

Sessions are strictly sequential. OBS-S1 is the hard prerequisite.

```
OBS-S1 (Data)  →  OBS-S2 (Design)  →  OBS-S3 (UX)
```

OBS-S2 and OBS-S3 can be partially combined if capacity allows, but OBS-S1 must ship and be verified against production before either visual session begins. Without live data, visual changes cannot be evaluated for correctness.

**Trigger phrases for Anti-Gravity:**
- OBS-S1: `"Read CLAUDECODE_BRIEF_OBS_S1.md and execute it."` (brief to be authored at session start)
- OBS-S2: `"Read CLAUDECODE_BRIEF_OBS_S2.md and execute it."` (after OBS-S1 ACs confirmed)
- OBS-S3: `"Read CLAUDECODE_BRIEF_OBS_S3.md and execute it."` (after OBS-S2 ACs confirmed)

---

## §5 — Deferred (Out of Scope for This Plan)

| Item | Reason for deferral |
|---|---|
| Replay pricing diff pages (full redesign) | Low-traffic analytics; lower ROI than core pipeline wiring |
| Export panel UI | Functional; cosmetic brand alignment deferred to OBS-S2 sweep |
| Multi-native Observatory (Phase 11+ scope) | Observatory currently scoped to native production queries only |
| Real-time streaming metrics | Requires SSE/WebSocket infrastructure not in scope for M5 |
| Cost forecasting / budget projection charts | Requires ≥ 30 days of data history — premature until data flows |
| Mobile Observatory layout | Super-admin tool; desktop-first is acceptable |

---

## §6 — Key File Reference

| File | Purpose | Touched by |
|---|---|---|
| `lib/synthesis/single_model_strategy.ts` | AI SDK synthesis path — G.2 TODO lives here | OBS-S1 |
| `lib/pipeline/manifest_planner.ts` | AI SDK planner path — no telemetry today | OBS-S1 |
| `lib/llm/observability/persist.ts` | `persistObservation()` — the single insert point for `llm_usage_events` | OBS-S1 (read-only) |
| `lib/llm/observability/cost.ts` | `computeCost()` — queries `llm_pricing_versions` | OBS-S1 (read-only) |
| `lib/db/seed/observatory_pricing/seed_v1.ts` | Pricing seed — must be run against production | OBS-S1 (execute) |
| `lib/observatory/queries.ts` | All Observatory DB queries — reads `llm_usage_events` | Background reference |
| `lib/components/observatory/Layout.tsx` | Standalone layout — to be deleted | OBS-S2 |
| `app/(super-admin)/observatory/layout.tsx` | Section shell — to be rewritten to use AppShell | OBS-S2 |
| `components/shared/AppShellRail.tsx` | Portal nav rail — already has Observatory entry | OBS-S2 (read-only) |
| `lib/components/observatory/pages/OverviewClient.tsx` | Overview page — Zone 1/2/3 restructure | OBS-S3 |
| `app/globals.css` | Brand tokens — source of truth for all design | Background reference |

---

## §7 — Post-OBS-S1 Verification Protocol

After OBS-S1 merges and deploys, run the following verification sequence before authorizing OBS-S2:

1. Send one live query via the portal (any query class).
2. Query production DB: `SELECT pipeline_stage, provider, model, computed_cost_usd, input_tokens, output_tokens, created_at FROM llm_usage_events ORDER BY created_at DESC LIMIT 10;`
3. Expected result: ≥ 2 rows (1 planner + 1 synthesis), with `computed_cost_usd IS NOT NULL` for at least the synthesis row (planner may be null if `claude-haiku-4-5` pricing not in seed).
4. Load Observatory Overview in portal — confirm KPI tiles show non-zero values.
5. Confirm `Date range picker` responds (preset buttons update displayed date range).
6. Only then: authorize OBS-S2 brief authoring.

If `computed_cost_usd` is null for all rows, the pricing seed has not been applied or `llm_pricing_versions` is missing the relevant model entry. Extend `seed_v1.ts` to add the missing model before proceeding.

---

*End of OBSERVATORY_REDESIGN_PLAN_v1_0.md. Three sessions: OBS-S1 (data wiring), OBS-S2 (design system), OBS-S3 (UX). OBS-S1 is the hard prerequisite for everything else.*
