---
session_id: OBS-UX-S3
status: COMPLETE
executor: claude-code-antigravity
phase: Observatory UX Elevation — Budgets Full Elevation
estimated_effort: medium (3–5 hours)
---

# CLAUDECODE_BRIEF — OBS-UX-S3: Budgets Page Full Elevation

## Prerequisite
OBS-UX-S1 must be complete (dark charcoal wrapper already on Budgets page). This session replaces the generic card/form/chip internals with brand-quality components.

## Mission
The Budgets tab manages spend rules and alerts. The current UI uses `rounded border bg-background` cards, `bg-green-500` progress bars, and generic form inputs — none of which reflect the dark gold design system. A super-admin checking budget health needs at-a-glance clarity: which rules are in danger, which are fine, total committed vs. actual. This session delivers that.

## Design System Reference (same as S1/S2 plus additions)

```
Status ok:        #10b981 (emerald)  /  bg-emerald-500/10 border-emerald-500/25
Status warning:   #f59e0b (amber)    /  bg-amber-500/10 border-amber-500/25
Status alert:     #ef4444 (red)      /  bg-red-500/10 border-red-500/25
Status exceeded:  #dc2626 (deep red) /  bg-red-600/15 border-red-600/35
Progress ok fill:       from-emerald-500 to-emerald-400
Progress warning fill:  from-amber-500 to-amber-400
Progress alert fill:    from-red-500 to-red-400
Progress exceeded fill: from-red-600 to-red-500
Gold gradient:    from-[#d4af37] to-[#fce29a]
Form input:       bg-[oklch(0.13_0.008_70)] border-[rgba(212,175,55,0.15)] text-[rgba(212,175,55,0.85)] focus:border-[rgba(212,175,55,0.40)] focus:ring-0 focus:outline-none
```

## Deliverable 1 — BudgetHeroSummary component

Create `platform/src/lib/components/observatory/budget/BudgetHeroSummary.tsx`.

This sits at the top of the budgets page, above the rules list. It takes:
- `rules: BudgetRuleRow[]`
- `evaluations: BudgetEvaluationResult[]`

And renders a 3-tile summary row:

**Tile 1 — Total committed budget (monthly equivalent):**
Sum of all `amount_usd` for monthly rules. Display as `$X.XX / mo`.

**Tile 2 — Total current spend:**
Sum of `current_spend_usd` from evaluations. Display as `$X.XXXXXX`.

**Tile 3 — Health status:**
Count of rules by status. If any are `exceeded` → "⚠ Over budget" (red). If any are `alert` → "Alert" (red). If any are `warning` → "Warning" (amber). Else → "All clear" (emerald).

Tile layout:
```tsx
<div className="grid grid-cols-3 gap-4">
  {/* each tile: */}
  <div className="rounded-xl border border-[rgba(212,175,55,0.12)] bg-[oklch(0.11_0.010_70)] p-4">
    <p className="text-[10px] font-semibold uppercase tracking-widest text-[rgba(212,175,55,0.35)]">
      {label}
    </p>
    <p className="mt-2 text-2xl font-bold tabular-nums text-[#fce29a]">
      {value}
    </p>
    <p className="mt-1 text-xs text-[rgba(212,175,55,0.40)]">{sub}</p>
  </div>
</div>
```

The health tile uses `text-emerald-400`, `text-amber-400`, or `text-red-400` for the main value color.

## Deliverable 2 — Redesign BudgetRuleCard

In `platform/src/lib/components/observatory/budget/BudgetRuleCard.tsx`, completely replace the generic styling with brand tokens.

### Card container
```tsx
<div
  data-testid={`budget-rule-card-${rule.budget_rule_id}`}
  data-rule-id={rule.budget_rule_id}
  className="rounded-xl border border-[rgba(212,175,55,0.12)] bg-[oklch(0.11_0.010_70)] p-5 transition-colors hover:border-[rgba(212,175,55,0.20)]"
>
```

### Header row (name + status chip)
```tsx
<div className="flex items-start justify-between gap-3">
  <div>
    <div className="text-sm font-semibold text-[#fce29a]">{rule.name}</div>
    <div className="mt-0.5 text-xs text-[rgba(212,175,55,0.45)]">
      {scopeLabel} · {rule.period}
    </div>
  </div>
  {evaluation && <BudgetStatusChip status={evaluation.status} pct_used={evaluation.pct_used} />}
</div>
```

### Progress bar — replace `bg-green-500` etc. with gradient fills
```tsx
{/* Threshold label */}
<div className="mt-4 flex items-center justify-between text-xs">
  <span className="text-[rgba(212,175,55,0.40)]">
    Budget: <span className="font-semibold text-[rgba(212,175,55,0.70)]">{formatUsd(rule.amount_usd)}</span> / {rule.period.replace(/ly$/, '')}
  </span>
  {evaluation && (
    <span className={cn('font-semibold tabular-nums', statusTextColor(evaluation.status))}>
      {evaluation.pct_used.toFixed(1)}% used
    </span>
  )}
</div>

{/* Progress track */}
<div
  className="mt-2 h-2 w-full overflow-hidden rounded-full bg-[rgba(212,175,55,0.08)]"
  role="progressbar"
  aria-valuenow={Math.min(100, Math.round(evaluation?.pct_used ?? 0))}
  aria-valuemin={0}
  aria-valuemax={100}
>
  <div
    className={cn('h-full rounded-full bg-gradient-to-r transition-all duration-500', progressGradient(evaluation?.status))}
    style={{ width: `${Math.min(100, Math.max(0, evaluation?.pct_used ?? 0))}%` }}
  />
</div>

{/* Spend vs limit */}
{evaluation && (
  <div className="mt-1.5 flex items-center justify-between text-xs tabular-nums">
    <span className={cn('font-medium', statusTextColor(evaluation.status))}>
      {formatUsd(evaluation.current_spend_usd)} spent
    </span>
    <span className="text-[rgba(212,175,55,0.30)]">of {formatUsd(evaluation.amount_usd)}</span>
  </div>
)}
```

Add helper functions within the file (not exported):
```ts
function progressGradient(status?: string): string {
  switch (status) {
    case 'ok':       return 'from-emerald-500 to-emerald-400'
    case 'warning':  return 'from-amber-500 to-amber-400'
    case 'alert':    return 'from-red-500 to-red-400'
    case 'exceeded': return 'from-red-600 to-red-500'
    default:         return 'from-[rgba(212,175,55,0.40)] to-[rgba(212,175,55,0.25)]'
  }
}

function statusTextColor(status?: string): string {
  switch (status) {
    case 'ok':       return 'text-emerald-400'
    case 'warning':  return 'text-amber-400'
    case 'alert':
    case 'exceeded': return 'text-red-400'
    default:         return 'text-[rgba(212,175,55,0.60)]'
  }
}
```

### Alert thresholds section
```tsx
<div className="mt-3 text-[10px] text-[rgba(212,175,55,0.35)]">
  {alertThresholdsLabel(rule)}
</div>
```

### Skeleton state (while evaluation loads)
```tsx
<div className="mt-4 space-y-2">
  <div className="h-2 w-full animate-pulse rounded-full bg-[rgba(212,175,55,0.06)]" />
  <div className="h-3 w-1/3 animate-pulse rounded bg-[rgba(212,175,55,0.06)]" />
</div>
```

### Deactivate action
```tsx
{confirming ? (
  <div className="mt-4 flex items-center gap-2">
    <span className="text-xs text-[rgba(212,175,55,0.60)]">Deactivate this rule?</span>
    <button
      type="button"
      onClick={() => { setConfirming(false); onDeactivate() }}
      className="rounded-lg border border-red-500/40 px-2.5 py-1 text-xs font-medium text-red-400 transition-colors hover:bg-red-500/10"
    >
      Confirm
    </button>
    <button
      type="button"
      onClick={() => setConfirming(false)}
      className="rounded-lg border border-[rgba(212,175,55,0.15)] px-2.5 py-1 text-xs text-[rgba(212,175,55,0.50)] transition-colors hover:text-[#d4af37]"
    >
      Cancel
    </button>
  </div>
) : (
  <button
    type="button"
    onClick={() => setConfirming(true)}
    className="mt-4 rounded-lg border border-[rgba(212,175,55,0.12)] px-2.5 py-1 text-xs text-[rgba(212,175,55,0.40)] transition-colors hover:border-red-500/30 hover:text-red-400"
  >
    Deactivate
  </button>
)}
```

## Deliverable 3 — Redesign BudgetStatusChip

In `platform/src/lib/components/observatory/budget/BudgetStatusChip.tsx`:

```tsx
const CHIP_STYLES: Record<string, string> = {
  ok:       'bg-emerald-500/10 border-emerald-500/25 text-emerald-400',
  warning:  'bg-amber-500/10 border-amber-500/25 text-amber-400',
  alert:    'bg-red-500/10 border-red-500/25 text-red-400',
  exceeded: 'bg-red-600/15 border-red-600/35 text-red-300',
}

const CHIP_ICONS: Record<string, string> = {
  ok:       '✓',
  warning:  '!',
  alert:    '!!',
  exceeded: '⚠',
}

export function BudgetStatusChip({ status, pct_used }: { status: string; pct_used: number }) {
  const style = CHIP_STYLES[status] ?? 'bg-[rgba(212,175,55,0.08)] border-[rgba(212,175,55,0.15)] text-[rgba(212,175,55,0.60)]'
  const icon = CHIP_ICONS[status] ?? '?'
  return (
    <div className={cn('flex items-center gap-1 rounded-full border px-2.5 py-1 text-[10px] font-semibold', style)}>
      <span>{icon}</span>
      <span className="capitalize">{status}</span>
      <span className="tabular-nums opacity-70">· {pct_used.toFixed(0)}%</span>
    </div>
  )
}
```

## Deliverable 4 — Redesign CreateBudgetRuleForm

In `platform/src/lib/components/observatory/budget/CreateBudgetRuleForm.tsx`:

The form is currently unstyled. Apply brand tokens throughout.

**Form container / section header:**
```tsx
<section className="rounded-xl border border-[rgba(212,175,55,0.12)] bg-[oklch(0.11_0.010_70)] p-6">
  <div className="mb-5">
    <h2 className="text-sm font-semibold text-[#fce29a]">Create budget rule</h2>
    <p className="mt-0.5 text-xs text-[rgba(212,175,55,0.40)]">
      Set a spend limit and alert thresholds for a scope and period.
    </p>
  </div>
```

**Form field wrapper:**
```tsx
<div className="flex flex-col gap-1">
  <label className="text-[10px] font-semibold uppercase tracking-widest text-[rgba(212,175,55,0.40)]">
    {fieldLabel}
  </label>
  <input
    className="rounded-lg border border-[rgba(212,175,55,0.15)] bg-[oklch(0.13_0.008_70)] px-3 py-2 text-sm text-[rgba(212,175,55,0.85)] placeholder:text-[rgba(212,175,55,0.25)] focus:border-[rgba(212,175,55,0.40)] focus:outline-none"
    ...
  />
</div>
```

Apply the same class to `<select>` elements.

**Add threshold row button:**
```tsx
<button
  type="button"
  onClick={addThreshold}
  disabled={thresholds.length >= 3}
  className="rounded-lg border border-dashed border-[rgba(212,175,55,0.20)] px-3 py-1.5 text-xs text-[rgba(212,175,55,0.40)] transition-colors hover:border-[rgba(212,175,55,0.35)] hover:text-[rgba(212,175,55,0.70)] disabled:opacity-40"
>
  + Add alert threshold
</button>
```

**Submit button:**
```tsx
<button
  type="submit"
  disabled={submitting}
  className="rounded-lg bg-gradient-to-r from-[#d4af37] to-[#fce29a] px-5 py-2 text-xs font-semibold text-[oklch(0.10_0.012_70)] transition-opacity hover:opacity-90 disabled:opacity-50"
>
  {submitting ? 'Creating…' : 'Create rule'}
</button>
```

**Error display:**
```tsx
{error && (
  <div role="alert" className="rounded-lg border border-red-500/30 bg-red-500/5 px-3 py-2 text-xs text-red-400">
    {error}
  </div>
)}
```

## Deliverable 5 — BudgetsRulesList empty state

In `BudgetsRulesList.tsx`, replace the generic dashed border empty state:
```tsx
<div
  data-testid="budgets-empty"
  className="flex flex-col items-center gap-3 rounded-xl border border-dashed border-[rgba(212,175,55,0.15)] py-12 text-center"
>
  <span className="text-3xl opacity-20">◎</span>
  <p className="text-sm font-medium text-[rgba(212,175,55,0.45)]">No active budget rules</p>
  <p className="text-xs text-[rgba(212,175,55,0.30)]">Create a rule below to start tracking spend</p>
</div>
```

## Deliverable 6 — Wire BudgetHeroSummary into the Budgets page

In the Budgets server page (`platform/src/app/(super-admin)/observatory/budgets/page.tsx`):
- Import `BudgetHeroSummary`
- Pass `rules` and `evaluations` to it
- Render it as the first element inside the content div (after the page header, before `BudgetsRulesList`)

## Acceptance Criteria

- [ ] AC.S3.1 — BudgetHeroSummary exists with 3 tiles: committed budget, total spend, health status
- [ ] AC.S3.2 — BudgetRuleCard uses dark charcoal card container with brand borders
- [ ] AC.S3.3 — BudgetRuleCard progress bar uses gradient fills from `progressGradient()`, not hard-coded green/amber/red bg classes
- [ ] AC.S3.4 — BudgetStatusChip uses brand-aligned color map with icon + pct display
- [ ] AC.S3.5 — CreateBudgetRuleForm inputs/selects use brand token bg + border + focus styles
- [ ] AC.S3.6 — CreateBudgetRuleForm submit button uses gold gradient
- [ ] AC.S3.7 — BudgetsRulesList empty state uses brand dashed border + centered layout
- [ ] AC.S3.8 — BudgetHeroSummary is rendered on the budgets page above the rules list
- [ ] AC.S3.9 — `npx tsc --noEmit` 0 new errors
- [ ] AC.S3.10 — All existing budget tests pass

## may_touch
```
platform/src/lib/components/observatory/budget/**
platform/src/lib/components/observatory/__tests__/budget/**
platform/src/app/\(super-admin\)/observatory/budgets/**
```

## must_not_touch
```
platform/src/lib/components/observatory/events/**
platform/src/lib/components/observatory/charts/**
platform/src/lib/components/observatory/kpi/**
platform/src/lib/components/observatory/reconciliation/**
platform/src/lib/observatory/**
platform/src/app/api/**
platform/migrations/**
```
