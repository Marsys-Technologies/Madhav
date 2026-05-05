---
session_id: OBS-UX-S4
status: COMPLETE
executor: claude-code-antigravity
phase: Observatory UX Elevation — Reconciliation Full Elevation
estimated_effort: medium (3–5 hours)
---

# CLAUDECODE_BRIEF — OBS-UX-S4: Reconciliation Page Full Elevation

## Prerequisite
OBS-UX-S1 must be complete (dark charcoal wrapper already on Reconciliation page). This session replaces the generic table/tabs/form internals with brand-quality components.

## Mission
The Reconciliation tab compares computed LLM costs against authoritative billing data from each provider. It's a precision instrument — the super-admin needs to see at a glance which providers are in-tolerance and which have variance requiring investigation. The current UI uses a plain HTML table with no visual hierarchy and boring link-style tabs. This session delivers a meaningful reconciliation experience using the brand design system.

## Design System Reference (same as S1/S2/S3 plus additions)

```
Variance in-tolerance:   text-emerald-400 / bg-emerald-500/10 / border-emerald-500/20
Variance warning (5–15%): text-amber-400   / bg-amber-500/10 / border-amber-500/20
Variance critical (>15%): text-red-400     / bg-red-500/10  / border-red-500/20
Variance positive (over-billing): text-sky-400 / bg-sky-500/10 / border-sky-500/20

Provider brand colors:
  anthropic: #d97757 (warm orange)
  openai:    #10a37f (teal-green)
  gemini:    #4285f4 (blue)
  deepseek:  #7e57c2 (purple)
  nim:       #76b900 (bright green)
```

## Deliverable 1 — ReconciliationSummaryRow (banner / hero)

The `ReconciliationBannerView` currently renders the "latest reconciliation per provider" as a strip. Elevate it to a proper provider status grid.

In `platform/src/lib/components/observatory/reconciliation/ReconciliationBannerView.tsx`:

Replace whatever the current view is with a provider-card grid:

```tsx
<div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-5">
  {rows.map((row) => (
    <ProviderStatusCard key={row.provider} row={row} />
  ))}
</div>
```

`ProviderStatusCard` (inline sub-component):
```tsx
function ProviderStatusCard({ row }: { row: ReconciliationBannerRow }) {
  const dotColor = PROVIDER_COLORS[row.provider as keyof typeof PROVIDER_COLORS] ?? '#64748b'
  const varClass = varianceClass(row.variance_pct)
  
  return (
    <div className="rounded-xl border border-[rgba(212,175,55,0.10)] bg-[oklch(0.11_0.010_70)] p-3">
      {/* Provider name + dot */}
      <div className="flex items-center gap-2 mb-2">
        <span
          aria-hidden="true"
          className="h-2.5 w-2.5 rounded-full shrink-0"
          style={{ backgroundColor: dotColor }}
        />
        <span className="text-xs font-semibold text-[rgba(212,175,55,0.70)] capitalize">
          {row.provider}
        </span>
      </div>
      {/* Status chip */}
      <div className={cn('inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-medium', chipClass(row.status))}>
        {row.status ?? 'no data'}
      </div>
      {/* Variance */}
      {row.variance_pct != null && (
        <div className={cn('mt-1.5 text-xs font-semibold tabular-nums', varClass)}>
          {row.variance_pct > 0 ? '+' : ''}{row.variance_pct.toFixed(2)}%
        </div>
      )}
      {/* Period */}
      {row.period_start && (
        <div className="mt-1 text-[10px] text-[rgba(212,175,55,0.30)]">
          {row.period_start}
        </div>
      )}
    </div>
  )
}
```

Helper functions:
```ts
import { PROVIDER_COLORS } from '@/lib/components/observatory/charts/utils'

function varianceClass(pct: number | null | undefined): string {
  if (pct == null) return 'text-[rgba(212,175,55,0.40)]'
  const abs = Math.abs(pct)
  if (abs <= 5)  return 'text-emerald-400'
  if (abs <= 15) return 'text-amber-400'
  return 'text-red-400'
}

function chipClass(status: string | null | undefined): string {
  switch (status) {
    case 'ok':       return 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400'
    case 'warning':  return 'bg-amber-500/10 border-amber-500/20 text-amber-400'
    case 'critical': return 'bg-red-500/10 border-red-500/20 text-red-400'
    default:         return 'bg-[rgba(212,175,55,0.06)] border-[rgba(212,175,55,0.12)] text-[rgba(212,175,55,0.40)]'
  }
}
```

## Deliverable 2 — Provider tab navigation (brand pill tabs)

In `ReconciliationHistoryView.tsx`, replace the `border-b` tab nav with a pill-style tab row:

```tsx
<nav
  data-testid="reconciliation-tabs"
  aria-label="Provider filter"
  className="flex flex-wrap items-center gap-1.5"
>
  {/* All tab */}
  <Link
    href="/observatory/reconciliation"
    data-testid="reconciliation-tab-all"
    aria-current={active === null ? 'page' : undefined}
    className={cn(
      'rounded-lg border px-3 py-1.5 text-xs font-medium transition-colors',
      active === null
        ? 'border-[rgba(212,175,55,0.30)] bg-[rgba(212,175,55,0.12)] text-[#d4af37]'
        : 'border-[rgba(212,175,55,0.10)] text-[rgba(212,175,55,0.45)] hover:border-[rgba(212,175,55,0.20)] hover:text-[#d4af37]',
    )}
  >
    All
  </Link>

  {/* Per-provider tabs with colored dot */}
  {TAB_PROVIDERS.map((p) => {
    const dotColor = PROVIDER_COLORS[p as keyof typeof PROVIDER_COLORS] ?? '#64748b'
    const isActiveProv = active === p
    return (
      <Link
        key={p}
        href={`/observatory/reconciliation?provider=${p}`}
        data-testid={`reconciliation-tab-${p}`}
        aria-current={isActiveProv ? 'page' : undefined}
        className={cn(
          'flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs font-medium transition-colors',
          isActiveProv
            ? 'border-[rgba(212,175,55,0.30)] bg-[rgba(212,175,55,0.12)] text-[#d4af37]'
            : 'border-[rgba(212,175,55,0.10)] text-[rgba(212,175,55,0.45)] hover:border-[rgba(212,175,55,0.20)] hover:text-[#d4af37]',
        )}
      >
        <span
          aria-hidden="true"
          className="h-2 w-2 rounded-full"
          style={{ backgroundColor: dotColor, opacity: isActiveProv ? 1 : 0.6 }}
        />
        {providerLabel(p)}
      </Link>
    )
  })}
</nav>
```

Import `PROVIDER_COLORS` from `@/lib/components/observatory/charts/utils`.

## Deliverable 3 — Reconciliation history table (brand-styled)

Replace the generic `<table>` in `ReconciliationHistoryView.tsx` with a brand-styled version.

**Table wrapper:**
```tsx
<div className="overflow-x-auto rounded-xl border border-[rgba(212,175,55,0.10)]">
  <table className="w-full text-xs">
```

**Table head:**
```tsx
<thead>
  <tr className="border-b border-[rgba(212,175,55,0.10)]">
    {['Date', 'Provider', 'Period', 'Status', 'Authoritative', 'Computed', 'Variance %'].map((h) => (
      <th key={h} className="px-4 py-3 text-left text-[10px] font-semibold uppercase tracking-widest text-[rgba(212,175,55,0.35)]">
        {h}
      </th>
    ))}
  </tr>
</thead>
```

**Table body rows:**
```tsx
{rows.map((row) => (
  <tr
    key={row.reconciliation_id}
    data-testid={`reconciliation-row-${row.reconciliation_id}`}
    className="border-b border-[rgba(212,175,55,0.06)] transition-colors hover:bg-[rgba(212,175,55,0.03)]"
  >
    {/* Date */}
    <td className="px-4 py-3 font-mono text-[10px] text-[rgba(212,175,55,0.50)]">
      {fmtDate(row.created_at)}
    </td>

    {/* Provider with colored dot */}
    <td className="px-4 py-3">
      <span className="flex items-center gap-2">
        <span
          aria-hidden="true"
          className="h-2 w-2 rounded-full shrink-0"
          style={{ backgroundColor: PROVIDER_COLORS[row.provider as keyof typeof PROVIDER_COLORS] ?? '#64748b' }}
        />
        <span className="text-xs text-[rgba(212,175,55,0.70)] capitalize">{providerLabel(row.provider)}</span>
      </span>
    </td>

    {/* Period */}
    <td className="px-4 py-3 font-mono text-[10px] text-[rgba(212,175,55,0.50)]">
      {fmtPeriod(row)}
    </td>

    {/* Status chip */}
    <td className="px-4 py-3">
      <StatusChip provider={row.provider} status={row.status} variancePct={row.variance_pct} />
    </td>

    {/* Authoritative cost */}
    <td className="px-4 py-3 text-right font-mono text-xs text-[rgba(212,175,55,0.70)]">
      {fmtUsd(row.authoritative_cost_usd)}
    </td>

    {/* Computed cost */}
    <td className="px-4 py-3 text-right font-mono text-xs text-[rgba(212,175,55,0.70)]">
      {fmtUsd(row.computed_cost_usd)}
    </td>

    {/* Variance % with color coding */}
    <td className="px-4 py-3 text-right">
      <VarianceBadge pct={row.variance_pct} />
    </td>
  </tr>
))}
```

Add `VarianceBadge` inline sub-component:
```tsx
function VarianceBadge({ pct }: { pct: number | null | undefined }) {
  if (pct == null || !Number.isFinite(pct)) {
    return <span className="font-mono text-[rgba(212,175,55,0.30)]">—</span>
  }
  const abs = Math.abs(pct)
  let cls: string
  if (abs <= 5)       cls = 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20'
  else if (abs <= 15) cls = 'text-amber-400 bg-amber-500/10 border-amber-500/20'
  else                cls = 'text-red-400 bg-red-500/10 border-red-500/20'

  const sign = pct > 0 ? '+' : ''
  return (
    <span className={cn('inline-flex items-center rounded-full border px-2 py-0.5 font-mono text-[10px] font-semibold tabular-nums', cls)}>
      {sign}{pct.toFixed(2)}%
    </span>
  )
}
```

## Deliverable 4 — Redesign StatusChip

In `platform/src/lib/components/observatory/reconciliation/StatusChip.tsx`:

```tsx
const STATUS_STYLES: Record<string, string> = {
  ok:          'bg-emerald-500/10 border-emerald-500/20 text-emerald-400',
  warning:     'bg-amber-500/10  border-amber-500/20  text-amber-400',
  critical:    'bg-red-500/10    border-red-500/20    text-red-400',
  pending:     'bg-[rgba(212,175,55,0.06)] border-[rgba(212,175,55,0.12)] text-[rgba(212,175,55,0.50)]',
  in_progress: 'bg-sky-500/10    border-sky-500/20    text-sky-400',
}

export function StatusChip({ status, variancePct, provider: _provider }: StatusChipProps) {
  const style = STATUS_STYLES[status ?? ''] ?? STATUS_STYLES['pending']
  return (
    <span className={cn('inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-medium capitalize', style)}>
      {status ?? '—'}
    </span>
  )
}
```

## Deliverable 5 — Redesign CSV upload form

In `ReconciliationHistoryView.tsx`, replace the upload form section:

```tsx
{showUpload && (
  <section className="rounded-xl border border-[rgba(212,175,55,0.12)] bg-[oklch(0.11_0.010_70)] p-5">
    <div className="mb-4">
      <h2 className="text-sm font-semibold text-[#fce29a]">Manual reconciliation upload</h2>
      <p className="mt-0.5 text-xs text-[rgba(212,175,55,0.40)]">
        DeepSeek and NIM don't expose billing APIs. Upload the invoice CSV for the period.
      </p>
    </div>

    <form
      data-testid="reconciliation-upload-form"
      action="/api/admin/observatory/reconciliation/upload"
      method="POST"
      encType="multipart/form-data"
      className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4"
    >
      {/* Provider select */}
      <div className="flex flex-col gap-1.5">
        <label className="text-[10px] font-semibold uppercase tracking-widest text-[rgba(212,175,55,0.40)]">
          Provider
        </label>
        <select
          name="provider"
          defaultValue={active && MANUAL_UPLOAD_PROVIDERS.has(active) ? active : 'deepseek'}
          data-testid="reconciliation-upload-provider"
          className="rounded-lg border border-[rgba(212,175,55,0.15)] bg-[oklch(0.13_0.008_70)] px-3 py-2 text-sm text-[rgba(212,175,55,0.85)] focus:border-[rgba(212,175,55,0.40)] focus:outline-none"
        >
          <option value="deepseek">DeepSeek</option>
          <option value="nim">NIM</option>
        </select>
      </div>

      {/* Period start */}
      <div className="flex flex-col gap-1.5">
        <label className="text-[10px] font-semibold uppercase tracking-widest text-[rgba(212,175,55,0.40)]">
          Period start
        </label>
        <input
          type="date"
          name="period_start"
          required
          data-testid="reconciliation-upload-period-start"
          className="rounded-lg border border-[rgba(212,175,55,0.15)] bg-[oklch(0.13_0.008_70)] px-3 py-2 text-sm text-[rgba(212,175,55,0.85)] focus:border-[rgba(212,175,55,0.40)] focus:outline-none"
        />
      </div>

      {/* Period end */}
      <div className="flex flex-col gap-1.5">
        <label className="text-[10px] font-semibold uppercase tracking-widest text-[rgba(212,175,55,0.40)]">
          Period end
        </label>
        <input
          type="date"
          name="period_end"
          required
          data-testid="reconciliation-upload-period-end"
          className="rounded-lg border border-[rgba(212,175,55,0.15)] bg-[oklch(0.13_0.008_70)] px-3 py-2 text-sm text-[rgba(212,175,55,0.85)] focus:border-[rgba(212,175,55,0.40)] focus:outline-none"
        />
      </div>

      {/* CSV file */}
      <div className="flex flex-col gap-1.5">
        <label className="text-[10px] font-semibold uppercase tracking-widest text-[rgba(212,175,55,0.40)]">
          CSV file
        </label>
        <input
          type="file"
          name="file"
          accept=".csv,text/csv"
          required
          data-testid="reconciliation-upload-file"
          className="rounded-lg border border-[rgba(212,175,55,0.15)] bg-[oklch(0.13_0.008_70)] px-3 py-2 text-sm text-[rgba(212,175,55,0.55)] file:mr-3 file:rounded file:border-0 file:bg-[rgba(212,175,55,0.12)] file:px-2 file:py-1 file:text-xs file:font-medium file:text-[#d4af37]"
        />
      </div>

      {/* Submit — spans full width on small, auto on large */}
      <div className="sm:col-span-2 lg:col-span-4">
        <button
          type="submit"
          data-testid="reconciliation-upload-submit"
          className="rounded-lg bg-gradient-to-r from-[#d4af37] to-[#fce29a] px-5 py-2 text-xs font-semibold text-[oklch(0.10_0.012_70)] transition-opacity hover:opacity-90"
        >
          Upload &amp; reconcile
        </button>
      </div>
    </form>
  </section>
)}
```

## Deliverable 6 — Page header for ReconciliationHistoryView

The current component has `<h1 className="text-xl font-semibold">Reconciliation History</h1>`. Replace this with the brand header pattern. Since this is a server-rendered view component (not using ObsPageShell directly), add the header inline:

```tsx
<section className="flex flex-col gap-6">
  {/* Header */}
  <div>
    <h1 className="font-heading text-xl font-semibold text-[#fce29a] tracking-wide">
      Reconciliation
    </h1>
    <p className="mt-0.5 text-xs text-[rgba(212,175,55,0.45)]">
      Per-provider cost reconciliation against authoritative billing · {total} total run{total === 1 ? '' : 's'}
    </p>
  </div>
```

## Deliverable 7 — Empty state for ReconciliationHistoryView

Replace the dashed border empty state:
```tsx
<div className="flex flex-col items-center gap-3 rounded-xl border border-dashed border-[rgba(212,175,55,0.15)] py-16 text-center">
  <span className="text-3xl opacity-20">⚖</span>
  <p className="text-sm font-medium text-[rgba(212,175,55,0.45)]">No reconciliation runs yet</p>
  <p className="text-xs text-[rgba(212,175,55,0.30)]">
    Trigger a reconciliation from the API, or upload a CSV below for DeepSeek / NIM
  </p>
</div>
```

## Acceptance Criteria

- [ ] AC.S4.1 — ReconciliationBannerView renders provider status cards (grid layout with colored dots, status chip, variance %)
- [ ] AC.S4.2 — Provider tabs use pill style with colored dots and gold active state (no underline tabs)
- [ ] AC.S4.3 — Reconciliation table has brand header row, dark hover rows, provider colored dots
- [ ] AC.S4.4 — VarianceBadge renders in-tolerance as emerald, warning as amber, critical as red
- [ ] AC.S4.5 — StatusChip uses brand-aligned color map
- [ ] AC.S4.6 — CSV upload form uses brand inputs, selects, file input, and gold gradient submit button
- [ ] AC.S4.7 — ReconciliationHistoryView h1 uses `text-[#fce29a]` brand heading style
- [ ] AC.S4.8 — Empty state uses brand dashed border + centered icon + brand text
- [ ] AC.S4.9 — `npx tsc --noEmit` 0 new errors
- [ ] AC.S4.10 — All existing reconciliation tests pass

## may_touch
```
platform/src/lib/components/observatory/reconciliation/**
platform/src/lib/components/observatory/__tests__/reconciliation/**
platform/src/app/\(super-admin\)/observatory/reconciliation/**
```

## must_not_touch
```
platform/src/lib/components/observatory/events/**
platform/src/lib/components/observatory/charts/**
platform/src/lib/components/observatory/kpi/**
platform/src/lib/components/observatory/budget/**
platform/src/lib/observatory/**
platform/src/app/api/**
platform/migrations/**
```
