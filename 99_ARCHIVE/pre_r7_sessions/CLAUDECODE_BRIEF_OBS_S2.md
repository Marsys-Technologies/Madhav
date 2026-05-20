---
session_id: OBS-S2
title: Observatory — Design System Integration
status: ACTIVE
phase: OBS-S2
executor: Anti-Gravity (Claude Code, claude-sonnet-4-6)
created_date: 2026-05-05
prerequisite: OBS-S1 ACs confirmed (llm_usage_events shows real data in production)
reference_plan: 00_ARCHITECTURE/OBSERVATORY_REDESIGN_PLAN_v1_0.md §3.2
---

# OBS-S2 — Observatory Design System Integration

## Objective

Make the Observatory look and feel like it belongs to the portal. Remove the standalone
`ObservatoryLayout` shell and replace it with the portal's `AppShell` + a new compact
sub-navigation component. Apply brand gold tokens throughout. Wire the `DateRangePicker`
so it actually controls the displayed data range.

**Do not start this session until OBS-S1 is confirmed complete and live.**

---

## Background

The Observatory currently renders inside `ObservatoryLayout` (`lib/components/observatory/Layout.tsx`),
a standalone shell with its own header, its own sidebar nav (10+ links), and disabled
reload/settings buttons. It completely bypasses the portal's `AppShell`.

The portal's brand tokens (`globals.css`) define:
- `--brand-gold: oklch(0.78 0.13 80)`
- `--brand-charcoal: oklch(0.10 0.012 70)`
- `--brand-ink: oklch(0.04 0.005 70)`
- Active nav style: `bg-[rgba(212,175,55,0.12)] border border-[rgba(212,175,55,0.22)] text-[#d4af37]`
- Inactive nav style: `text-[rgba(212,175,55,0.28)] hover:bg-[rgba(212,175,55,0.08)] hover:text-[#d4af37]`

The `AppShellRail` already lists Observatory in `NAV_ITEMS` and activates when
`pathname.startsWith('/observatory')`. The goal is to make the Observatory *use* AppShell
instead of replacing it.

---

## Scope

```
may_touch:
  - platform/src/app/(super-admin)/observatory/layout.tsx          # rewrite to use AppShell
  - platform/src/lib/components/observatory/Layout.tsx             # DELETE this file
  - platform/src/components/observatory/ObservatorySubNav.tsx      # CREATE this file (new)
  - platform/src/lib/components/observatory/filters/FiltersBar.tsx # verify DateRangePicker wired
  - platform/src/lib/components/observatory/kpi/KpiTile.tsx        # brand tokens
  - platform/src/lib/components/observatory/charts/CostOverTimeChart.tsx  # brand tokens
  - platform/src/lib/components/observatory/charts/CostByModelChart.tsx   # brand tokens

must_not_touch:
  - platform/src/components/shared/AppShell.tsx          # do not modify AppShell
  - platform/src/components/shared/AppShellRail.tsx      # do not modify the rail
  - platform/src/lib/observatory/                        # query layer — not this session
  - platform/src/app/api/admin/observatory/              # API — not this session
  - platform/src/lib/components/observatory/pages/       # page components — not this session
  - any migration files
  - any test files
```

---

## Task 1 — Create ObservatorySubNav component

**New file:** `platform/src/components/observatory/ObservatorySubNav.tsx`

```tsx
'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'

const NAV_SECTIONS = [
  { href: '/observatory', label: 'Overview', exact: true },
  { href: '/observatory/events', label: 'Events', exact: false },
  { href: '/observatory/reconciliation', label: 'Reconciliation', exact: false },
  { href: '/observatory/budgets', label: 'Budgets', exact: false },
] as const

const ANALYTICS_LINKS = [
  { href: '/observatory/analytics/cost-arc', label: 'Cost Arc' },
  { href: '/observatory/analytics/cache', label: 'Cache' },
  { href: '/observatory/analytics/anomaly', label: 'Anomalies' },
] as const

export function ObservatorySubNav() {
  const pathname = usePathname()

  function isActive(href: string, exact: boolean) {
    return exact ? pathname === href : pathname.startsWith(href)
  }

  return (
    <nav
      aria-label="Observatory navigation"
      className="hidden w-44 shrink-0 flex-col border-r border-[rgba(212,175,55,0.12)] bg-[var(--brand-charcoal,oklch(0.10_0.012_70))] py-4 md:flex"
    >
      <p className="mb-2 px-3 text-[10px] font-semibold uppercase tracking-widest text-[rgba(212,175,55,0.35)]">
        Observatory
      </p>
      <div className="flex flex-col gap-0.5 px-2">
        {NAV_SECTIONS.map(({ href, label, exact }) => (
          <Link
            key={href}
            href={href}
            className={cn(
              'rounded px-2 py-1.5 text-xs font-medium transition-colors',
              isActive(href, exact)
                ? 'bg-[rgba(212,175,55,0.12)] border border-[rgba(212,175,55,0.22)] text-[#d4af37]'
                : 'text-[rgba(212,175,55,0.40)] hover:bg-[rgba(212,175,55,0.07)] hover:text-[#d4af37]',
            )}
          >
            {label}
          </Link>
        ))}
      </div>

      <p className="mb-2 mt-4 px-3 text-[10px] font-semibold uppercase tracking-widest text-[rgba(212,175,55,0.25)]">
        Analytics
      </p>
      <div className="flex flex-col gap-0.5 px-2">
        {ANALYTICS_LINKS.map(({ href, label }) => (
          <Link
            key={href}
            href={href}
            className={cn(
              'rounded px-2 py-1.5 text-xs font-medium transition-colors',
              pathname.startsWith(href)
                ? 'bg-[rgba(212,175,55,0.12)] border border-[rgba(212,175,55,0.22)] text-[#d4af37]'
                : 'text-[rgba(212,175,55,0.40)] hover:bg-[rgba(212,175,55,0.07)] hover:text-[#d4af37]',
            )}
          >
            {label}
          </Link>
        ))}
      </div>
    </nav>
  )
}
```

---

## Task 2 — Rewrite the Observatory section layout

**File:** `platform/src/app/(super-admin)/observatory/layout.tsx`

Replace the entire file with:

```tsx
import type { Metadata } from 'next'
import { redirect } from 'next/navigation'
import { getServerUserWithProfile } from '@/lib/auth/access-control'
import { AppShell } from '@/components/shared/AppShell'
import { ObservatorySubNav } from '@/components/observatory/ObservatorySubNav'

export const metadata: Metadata = {
  title: 'Observatory — MARSYS-JIS',
}

export default async function ObservatorySectionLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const ctx = await getServerUserWithProfile()
  if (!ctx) redirect('/login')
  if (ctx.profile.role !== 'super_admin') redirect('/dashboard')
  if (ctx.profile.status !== 'active') redirect('/login')

  return (
    <AppShell
      user={ctx.user}
      profile={ctx.profile}
      breadcrumb={[{ label: 'Observatory', href: '/observatory', current: false }]}
    >
      <div className="flex h-full min-h-0">
        <ObservatorySubNav />
        <div className="flex-1 overflow-auto">
          {children}
        </div>
      </div>
    </AppShell>
  )
}
```

---

## Task 3 — Delete the standalone ObservatoryLayout

**File to delete:** `platform/src/lib/components/observatory/Layout.tsx`

After confirming no other file imports from this path (run a grep first), delete the file.

Grep command: `grep -r "observatory/Layout" platform/src --include="*.tsx" --include="*.ts"`

Expected: zero results after the layout.tsx rewrite in Task 2 (which replaced the import with ObservatorySubNav). If any results remain, update those imports before deleting.

Also delete `platform/src/lib/components/observatory/AuthGate.tsx` ONLY IF it is no longer
imported anywhere after Task 2. Run:
`grep -r "AuthGate" platform/src --include="*.tsx" --include="*.ts"`

If zero results: delete it. If any remain: leave it.

---

## Task 4 — Apply brand tokens to KpiTile

**File:** `platform/src/lib/components/observatory/kpi/KpiTile.tsx`

Read the file first. Find the outermost Card or div wrapper of each tile. Apply these
brand token classes to it:

- Replace `className="..."` on the card wrapper to include:
  `border border-[rgba(212,175,55,0.15)] bg-[var(--brand-charcoal,oklch(0.10_0.012_70))]`

Keep all existing text color, padding, and layout classes. Only change the border and background
of the tile card wrapper. Do not change the inner content structure.

---

## Task 5 — Apply brand tokens to charts

**File:** `platform/src/lib/components/observatory/charts/CostOverTimeChart.tsx`

Read the file. Find any hardcoded hex or `hsl(var(...))` stroke/fill color on the primary
data series. Replace with `var(--color-chart-1)`. If the chart already uses CSS variables
for colors, leave it as-is.

**File:** `platform/src/lib/components/observatory/charts/CostByModelChart.tsx`

Same approach: replace hardcoded bar fill colors with `var(--color-chart-1)` through
`var(--color-chart-5)` for up to 5 distinct series. If already using CSS variables, leave
as-is.

---

## Task 6 — Verify DateRangePicker is wired

**File:** `platform/src/lib/components/observatory/filters/FiltersBar.tsx`

Read the file. Confirm:
1. `DateRangePicker` is imported and rendered within `FiltersBar`.
2. Its `onChange` prop calls back into the filter state (via `useObservatoryFilters` or
   equivalent).
3. There are no disabled buttons or placeholder "Last 7 days" text that suppresses the
   real picker.

If `FiltersBar` correctly renders the functional `DateRangePicker` component, no changes
needed — just confirm it. If the header in `ObservatoryLayout` had disabled buttons that
were suppressing the picker, those are now gone because `ObservatoryLayout` was deleted.

---

## Task 7 — TypeScript check

```bash
cd platform && npx tsc --noEmit 2>&1 | tail -30
```

Zero new errors in files you touched. Pre-existing errors in unrelated files are acceptable.

---

## Task 8 — Smoke test Observatory routes still resolve

```bash
cd platform && npx vitest run \
  src/lib/components/observatory/__tests__/ \
  --reporter=verbose 2>&1 | tail -50
```

All Observatory component tests must still pass. You are not adding new tests in this session.

---

## Acceptance Criteria

| AC | Check |
|---|---|
| AC.S2.1 | `ObservatorySubNav.tsx` exists at `platform/src/components/observatory/ObservatorySubNav.tsx` |
| AC.S2.2 | `app/(super-admin)/observatory/layout.tsx` uses `AppShell` — no reference to `ObservatoryLayout` |
| AC.S2.3 | `lib/components/observatory/Layout.tsx` is deleted (or confirmed zero imports remain) |
| AC.S2.4 | `ObservatorySubNav` has exactly 4 primary links + 3 analytics links (7 total) |
| AC.S2.5 | `KpiTile` card wrapper has `border-[rgba(212,175,55,0.15)]` class applied |
| AC.S2.6 | `DateRangePicker` is confirmed functional in `FiltersBar` (not suppressed by a disabled button) |
| AC.S2.7 | `tsc --noEmit` exits 0 (or only pre-existing errors unrelated to changed files) |
| AC.S2.8 | All Observatory component tests pass |

---

## Do NOT do

- Do not modify `AppShell.tsx` or `AppShellRail.tsx`
- Do not modify any Observatory query or API files
- Do not add migrations
- Do not modify existing test files
- Do not change the `BreadcrumbSegment` interface or AppShell props signature

---

## How to start

Open the Madhav project (`/Users/Dev/Vibe-Coding/Apps/Madhav/`) in Anti-Gravity.
Run: **"Read CLAUDECODE_BRIEF_OBS_S2.md and execute it."**
