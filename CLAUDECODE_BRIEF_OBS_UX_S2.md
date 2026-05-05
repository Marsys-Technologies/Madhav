---
session_id: OBS-UX-S2
status: COMPLETE
executor: claude-code-antigravity
phase: Observatory UX Elevation — Events Full Elevation
estimated_effort: heavy (5–7 hours)
---

# CLAUDECODE_BRIEF — OBS-UX-S2: Events Page Full Elevation

## Prerequisite
OBS-UX-S1 must be complete. This session assumes `ObsPageShell`, `SectionLabel`, and dark recharts fixes are already landed.

## Mission
The Events tab is the highest-frequency page in Observatory — it's where you diagnose expensive queries, slow stages, and anomalous calls. Right now it renders a raw HTML table for the grouped view and a functional-but-unstyled virtualized table for the event-level view. Neither uses the brand design system. This session delivers a complete, production-quality Events experience.

## Design System Reference
Same tokens as OBS-UX-S1. Key additions for events-specific elements:

```
Provider dot colors:   from PROVIDER_COLORS in charts/utils.ts
Stage badge colors:    from STAGE_COLORS in charts/utils.ts
Row hover:             hover:bg-[rgba(212,175,55,0.04)]
Row selected:          bg-[rgba(212,175,55,0.08)] border-l-2 border-[#d4af37]
Mono text:             font-mono text-[10px] text-[rgba(212,175,55,0.55)]
Cost value:            tabular-nums text-[#fce29a]
High cost indicator:   text-amber-400
Error status:          text-red-400 / bg-red-500/10 border-red-500/30
Success status:        text-emerald-400
```

## Deliverable 1 — QueryGroupCard component

Replace the raw `<table>` in the `groupByQuery` branch of EventsClient with a new `QueryGroupCard` component.

Create `platform/src/lib/components/observatory/events/QueryGroupCard.tsx`:

Each grouped row becomes a card that shows:
- Query ID (truncated to 8 chars + full on hover via `title` attr) — mono, gold-subtle
- Call count badge (small pill: "N calls")
- Total cost in `$X.XXXXXX` format — large-ish, gold text
- Token split: input / output with a small split bar visual
- Timestamp of first call
- Stage pipeline mini-badges (list of distinct stages as tiny colored dots with labels)
- A chevron `›` on the right indicating it's expandable (future scope — for now non-interactive)

Layout: horizontal card, left-to-right: [query-id mono] [cost bold] [calls badge] [tokens] [stages dots] [timestamp] [›]

Styling:
```tsx
<div className="group flex items-center gap-4 rounded-lg border border-[rgba(212,175,55,0.10)] bg-[oklch(0.11_0.010_70)] px-4 py-3 transition-colors hover:bg-[rgba(212,175,55,0.04)] hover:border-[rgba(212,175,55,0.18)]">
```

Query ID section:
```tsx
<div className="min-w-0 flex-1">
  <span
    className="font-mono text-[10px] text-[rgba(212,175,55,0.50)]"
    title={row.conversation_id ?? '—'}
  >
    {row.conversation_id ? row.conversation_id.slice(0, 8) + '…' : '—'}
  </span>
</div>
```

Cost section:
```tsx
<span className="tabular-nums text-sm font-semibold text-[#fce29a]">
  {row.total_cost_usd != null ? `$${Number(row.total_cost_usd).toFixed(6)}` : '—'}
</span>
```

Calls badge:
```tsx
<span className="rounded-full border border-[rgba(212,175,55,0.20)] bg-[rgba(212,175,55,0.08)] px-2 py-0.5 text-[10px] font-medium text-[#d4af37]">
  {row.call_count} calls
</span>
```

Stages mini-badges (use `row.stages` array):
```tsx
<div className="flex items-center gap-1">
  {(row.stages ?? []).slice(0, 4).map((stage) => (
    <span
      key={stage}
      className="rounded px-1.5 py-0.5 text-[9px] font-medium uppercase tracking-wide"
      style={{
        backgroundColor: `${colorForStage(stage)}22`,
        color: colorForStage(stage),
        border: `1px solid ${colorForStage(stage)}44`,
      }}
    >
      {stage}
    </span>
  ))}
  {(row.stages ?? []).length > 4 && (
    <span className="text-[9px] text-[rgba(212,175,55,0.35)]">+{row.stages.length - 4}</span>
  )}
</div>
```

Timestamp:
```tsx
<span className="shrink-0 font-mono text-[10px] text-[rgba(212,175,55,0.40)]">
  {row.started_at ? new Date(row.started_at).toLocaleString('en-US', {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  }) : '—'}
</span>
```

Create a wrapping list component in EventsClient for grouped view:
```tsx
<div className="flex flex-col gap-2">
  {groupedRows.map((row, i) => (
    <QueryGroupCard key={row.conversation_id ?? i} row={row} />
  ))}
</div>
```

## Deliverable 2 — Style the EventTable rows

The `EventTable` component uses a virtualized list. The rows need brand styling applied. In `platform/src/lib/components/observatory/events/EventTable.tsx`:

### Column header row
Replace generic `text-muted-foreground` with brand tokens:
```tsx
// Header row
<div className="flex items-center border-b border-[rgba(212,175,55,0.10)] px-4 py-2 text-[10px] font-semibold uppercase tracking-widest text-[rgba(212,175,55,0.35)]">
```

### Data rows (inside VirtualList / row renderer)
Find the row-render section. Apply:
```tsx
// Row container
className={cn(
  'flex items-center border-b border-[rgba(212,175,55,0.06)] px-4 transition-colors',
  'hover:bg-[rgba(212,175,55,0.04)]',
  isSelected && 'bg-[rgba(212,175,55,0.08)] border-l-2 border-l-[#d4af37]',
)}
```

### StatusBadge
In `platform/src/lib/components/observatory/events/StatusBadge.tsx`, update the badge variants to use brand colors:
```tsx
const STATUS_STYLES: Record<string, string> = {
  success: 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/25',
  error:   'bg-red-500/15 text-red-400 border border-red-500/25',
  timeout: 'bg-amber-500/15 text-amber-400 border border-amber-500/25',
  pending: 'bg-[rgba(212,175,55,0.10)] text-[rgba(212,175,55,0.60)] border border-[rgba(212,175,55,0.18)]',
}
// default fallback
const DEFAULT_STYLE = 'bg-[rgba(212,175,55,0.08)] text-[rgba(212,175,55,0.50)] border border-[rgba(212,175,55,0.12)]'
```
Badge shape: `rounded-full px-2 py-0.5 text-[10px] font-medium`

### Provider + model column
If there's a provider cell, add a small colored dot before the provider name using `colorForProvider`:
```tsx
<span className="flex items-center gap-1.5">
  <span
    aria-hidden="true"
    className="inline-block h-2 w-2 rounded-full shrink-0"
    style={{ backgroundColor: colorForProvider(row.provider) }}
  />
  <span className="text-xs text-[rgba(212,175,55,0.60)]">{row.provider}</span>
</span>
```

### Cost column
Apply `tabular-nums text-[#fce29a] text-xs font-medium` to cost cells. If cost > $0.01, add `text-amber-400` instead.

### Latency column
Apply `tabular-nums text-xs text-[rgba(212,175,55,0.55)]`. If latency_ms > 5000, apply `text-red-400`.

## Deliverable 3 — Style EventSidePanel

In `platform/src/lib/components/observatory/events/EventSidePanel.tsx`:

The side panel slides in from the right. Apply consistent brand tokens:

**Panel container:**
```tsx
className="fixed inset-y-0 right-0 z-40 flex w-[480px] max-w-full flex-col border-l border-[rgba(212,175,55,0.12)] bg-[oklch(0.10_0.012_70)] shadow-2xl"
```

**Panel header:**
```tsx
<div className="flex items-center justify-between border-b border-[rgba(212,175,55,0.10)] px-6 py-4">
  <h2 className="text-sm font-semibold text-[#fce29a]">Event detail</h2>
  <button
    type="button"
    onClick={onClose}
    className="rounded p-1 text-[rgba(212,175,55,0.40)] transition-colors hover:bg-[rgba(212,175,55,0.08)] hover:text-[#d4af37]"
    aria-label="Close panel"
  >
    ✕
  </button>
</div>
```

**Content area:**
```tsx
<div className="flex-1 overflow-y-auto px-6 py-4">
```

**Key-value pairs** (event metadata rows):
```tsx
<div className="flex items-baseline justify-between border-b border-[rgba(212,175,55,0.06)] py-2">
  <dt className="text-[10px] font-medium uppercase tracking-widest text-[rgba(212,175,55,0.35)]">{label}</dt>
  <dd className="ml-4 text-xs text-[rgba(212,175,55,0.80)] tabular-nums">{value}</dd>
</div>
```

**Stage chips** within the panel:
Use the same stage badge style as QueryGroupCard.

**Navigation buttons** (prev/next event):
```tsx
<button className="rounded-lg border border-[rgba(212,175,55,0.20)] bg-[rgba(212,175,55,0.06)] px-3 py-1.5 text-xs font-medium text-[rgba(212,175,55,0.70)] transition-colors hover:border-[rgba(212,175,55,0.35)] hover:text-[#d4af37]">
```

## Deliverable 4 — Column visibility panel styling

The EventTable has a column visibility toggle panel (`showColumnPanel`). Find it and style:
- Panel container: `rounded-xl border border-[rgba(212,175,55,0.12)] bg-[oklch(0.11_0.010_70)] p-4 shadow-xl`
- Checkbox labels: `text-xs text-[rgba(212,175,55,0.65)]`
- Active checkbox accent: use `accent-[#d4af37]` on the input element
- Reset button: `rounded border border-[rgba(212,175,55,0.20)] px-2 py-1 text-[10px] text-[rgba(212,175,55,0.50)] hover:text-[#d4af37]`
- Column toggle button (the trigger): same button style as the Group toggle in the header

## Deliverable 5 — Empty and loading states (brand-styled)

In EventTable, the empty state and loading skeleton currently use generic styles. Update:

**Loading skeleton rows** (3 of them):
```tsx
<div className="h-10 animate-pulse rounded bg-[rgba(212,175,55,0.04)]" />
```

**Empty state:**
```tsx
<div className="flex flex-col items-center justify-center gap-3 py-16 text-center">
  <span className="text-3xl opacity-30">◎</span>
  <p className="text-sm font-medium text-[rgba(212,175,55,0.50)]">No events in this range</p>
  <p className="text-xs text-[rgba(212,175,55,0.30)]">Try adjusting the date filter or provider selection</p>
</div>
```

**Error state:**
```tsx
<div className="flex flex-col items-center gap-3 rounded-xl border border-red-500/20 bg-red-500/5 py-8 text-center">
  <p className="text-sm text-red-400">Failed to load events</p>
  <button onClick={onRetry} className="rounded border border-red-500/30 px-3 py-1 text-xs text-red-400 hover:bg-red-500/10">
    Retry
  </button>
</div>
```

## Acceptance Criteria

- [ ] AC.S2.1 — QueryGroupCard exists at `events/QueryGroupCard.tsx`, renders conversation_id, cost, call count, stage badges, timestamp with brand tokens
- [ ] AC.S2.2 — EventsClient grouped view uses QueryGroupCard list (no raw `<table>` in grouped mode)
- [ ] AC.S2.3 — EventTable column header row uses brand token text colors
- [ ] AC.S2.4 — EventTable data rows have hover:bg brand color and selected state left-border highlight
- [ ] AC.S2.5 — StatusBadge uses brand-aligned status color map
- [ ] AC.S2.6 — Provider cells show colored dot via colorForProvider
- [ ] AC.S2.7 — Cost cells use tabular-nums + gold text; high-cost cells use amber
- [ ] AC.S2.8 — EventSidePanel container uses dark charcoal bg + brand border
- [ ] AC.S2.9 — EventSidePanel header, KV rows, and nav buttons use brand tokens
- [ ] AC.S2.10 — Empty/loading/error states in EventTable use brand styles
- [ ] AC.S2.11 — Column visibility panel uses brand tokens
- [ ] AC.S2.12 — `npx tsc --noEmit` 0 new errors
- [ ] AC.S2.13 — All existing observatory events tests pass

## may_touch
```
platform/src/lib/components/observatory/events/**
platform/src/lib/components/observatory/pages/EventsClient.tsx
platform/src/lib/components/observatory/__tests__/events/**
platform/src/lib/components/observatory/__tests__/pages/EventsClient.test.tsx
```

## must_not_touch
```
platform/src/lib/components/observatory/charts/**
platform/src/lib/components/observatory/kpi/**
platform/src/lib/components/observatory/budget/**
platform/src/lib/components/observatory/reconciliation/**
platform/src/lib/observatory/**
platform/src/app/api/**
platform/migrations/**
```
