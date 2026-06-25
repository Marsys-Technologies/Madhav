# Chart Sharing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Charts tab to the admin panel that lets a super admin grant or revoke guest access to any platform chart, with a matching shortcut from the Users tab.

**Architecture:** The `chart_grants` table and `authorizeChartAccess()` already exist — this is entirely UI + two read-only API routes. The Charts tab is a split panel: guests on the left, chart access on the right. Grant/revoke calls reuse the existing `/api/clients/[id]/grants` endpoints. Tab state is driven by `?tab=` URL search params so browser Back works naturally and the Users tab can deep-link into the Charts tab with a guest pre-selected.

**Tech Stack:** Next.js 15 App Router, TypeScript, React Query (`@tanstack/react-query`), PostgreSQL via `pg.Pool` (`query()` from `@/lib/db/client`), Tailwind CSS (brand-gold/ink tokens in `styles.ts`), Sonner toasts.

**Spec:** `docs/superpowers/specs/2026-06-25-chart-sharing-design.md`

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `src/components/admin/types.ts` | Modify | Add `AdminChart`, `AdminChartGrant` interfaces |
| `src/lib/admin/audit.ts` | Modify | Add `chart_grant`, `chart_revoke` to `AuditAction` union |
| `src/app/api/admin/charts/route.ts` | **Create** | GET all platform charts (super_admin only) |
| `src/app/api/admin/users/[id]/chart-grants/route.ts` | **Create** | GET all charts + grant status for one guest |
| `src/app/api/clients/[id]/grants/route.ts` | Modify | Add `writeAuditLog` to POST + DELETE |
| `src/components/admin/ChartsTab.tsx` | **Create** | Split-panel Charts tab component |
| `src/components/admin/AdminClient.tsx` | Modify | Convert to URL-param tab system, add Charts tab |
| `src/components/admin/UsersTable.tsx` | Modify | Add "Manage chart access" to Actions dropdown |
| `src/app/admin/page.tsx` | Modify | Wrap `<AdminClient>` in `<Suspense>` (required for `useSearchParams`) |

---

## Task 1: Extend types and audit action union

**Files:**
- Modify: `src/components/admin/types.ts`
- Modify: `src/lib/admin/audit.ts`

- [ ] **Step 1: Add `AdminChart` and `AdminChartGrant` to `types.ts`**

Open `src/components/admin/types.ts` and append:

```typescript
export interface AdminChart {
  id: string
  name: string
  subject_name: string | null
  birth_date: string
  birth_place: string
  owner_id: string
  owner_username: string | null
  owner_name: string | null
  grant_count: number
}

export interface AdminChartGrant {
  id: string
  subject_name: string | null
  birth_date: string
  birth_place: string
  owner_id: string
  owner_username: string | null
  is_own: boolean
  granted: boolean
}
```

- [ ] **Step 2: Add `chart_grant` and `chart_revoke` to `AuditAction` in `audit.ts`**

In `src/lib/admin/audit.ts`, update the `AuditAction` type:

```typescript
export type AuditAction =
  | 'create_user'
  | 'edit_username'
  | 'disable_user'
  | 'enable_user'
  | 'delete_user'
  | 'role_change'
  | 'reset_password'
  | 'chart_grant'
  | 'chart_revoke'
```

- [ ] **Step 3: Verify TypeScript compiles**

```bash
cd platform && npx tsc --noEmit 2>&1 | head -20
```

Expected: no errors related to these files.

- [ ] **Step 4: Commit**

```bash
git add src/components/admin/types.ts src/lib/admin/audit.ts
git commit -m "feat(admin): add chart sharing types and audit actions"
```

---

## Task 2: API route — GET /api/admin/charts

**Files:**
- Create: `src/app/api/admin/charts/route.ts`

- [ ] **Step 1: Create the route file**

```typescript
// src/app/api/admin/charts/route.ts
import { NextResponse } from 'next/server'
import { requireSuperAdmin } from '@/lib/auth/access-control'
import { query } from '@/lib/db/client'
import { res } from '@/lib/errors'
import type { AdminChart } from '@/components/admin/types'

export async function GET() {
  const auth = await requireSuperAdmin()
  if (auth instanceof NextResponse) return auth

  try {
    const { rows } = await query<AdminChart>(`
      SELECT
        c.id,
        c.name,
        COALESCE(c.preferred_name, c.subject_name, c.name) AS subject_name,
        c.birth_date::text                                  AS birth_date,
        c.birth_place,
        c.owner_id,
        p.id       AS owner_profile_id,
        p.username AS owner_username,
        p.name     AS owner_name,
        COUNT(g.id)::int AS grant_count
      FROM charts c
      LEFT JOIN profiles p ON p.id = c.owner_id
      LEFT JOIN chart_grants g ON g.chart_id = c.id
      GROUP BY c.id, p.id, p.username, p.name
      ORDER BY c.created_at DESC
    `)
    return NextResponse.json({ charts: rows })
  } catch (err) {
    console.error('[admin/charts] GET failed', err)
    return res.internal('Failed to load charts.')
  }
}
```

- [ ] **Step 2: Verify the route responds correctly**

Make sure the dev server is running (`pnpm dev` in `platform/`), then in a separate terminal with auth cookies or via the browser console (logged in as super admin):

```bash
# From browser console on /admin page:
fetch('/api/admin/charts').then(r => r.json()).then(console.log)
```

Expected: `{ charts: [ { id, name, subject_name, birth_date, birth_place, owner_id, owner_username, owner_name, grant_count }, ... ] }`

- [ ] **Step 3: Verify non-super-admin gets 401/403**

Log out or use a guest account — the route should return 401 or 403.

- [ ] **Step 4: Commit**

```bash
git add src/app/api/admin/charts/route.ts
git commit -m "feat(admin): GET /api/admin/charts — all platform charts"
```

---

## Task 3: API route — GET /api/admin/users/[id]/chart-grants

**Files:**
- Create: `src/app/api/admin/users/[id]/chart-grants/route.ts`

Note: This file lives at `users/[id]/chart-grants/route.ts` — a new nested route under the existing `users/[id]/` directory which already contains `route.ts` and `send-reset/route.ts`.

- [ ] **Step 1: Create the route file**

```typescript
// src/app/api/admin/users/[id]/chart-grants/route.ts
import { NextResponse } from 'next/server'
import { requireSuperAdmin } from '@/lib/auth/access-control'
import { query } from '@/lib/db/client'
import { res } from '@/lib/errors'
import type { AdminChartGrant } from '@/components/admin/types'

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const auth = await requireSuperAdmin()
  if (auth instanceof NextResponse) return auth

  const { id: guestId } = await params

  // Confirm the target user exists
  const { rows: userRows } = await query<{ id: string }>(
    'SELECT id FROM profiles WHERE id = $1',
    [guestId]
  )
  if (!userRows[0]) return res.notFound('User not found.')

  try {
    const { rows } = await query<AdminChartGrant>(`
      SELECT
        c.id,
        COALESCE(c.preferred_name, c.subject_name, c.name) AS subject_name,
        c.birth_date::text AS birth_date,
        c.birth_place,
        c.owner_id,
        p.username AS owner_username,
        (c.owner_id = $1)        AS is_own,
        (g.id IS NOT NULL)       AS granted
      FROM charts c
      LEFT JOIN profiles p  ON p.id  = c.owner_id
      LEFT JOIN chart_grants g ON g.chart_id = c.id AND g.principal_id = $1
      ORDER BY
        (g.id IS NOT NULL) DESC,   -- granted first
        (c.owner_id = $1)  ASC,    -- own charts last
        c.created_at DESC
    `, [guestId])
    return NextResponse.json({ charts: rows })
  } catch (err) {
    console.error('[admin/users/chart-grants] GET failed', err)
    return res.internal('Failed to load chart grants.')
  }
}
```

- [ ] **Step 2: Verify the route responds correctly**

With a valid guest user id (e.g. from the Users tab):

```bash
# From browser console on /admin page (replace UID):
fetch('/api/admin/users/GUEST_UID_HERE/chart-grants').then(r => r.json()).then(console.log)
```

Expected: `{ charts: [ { id, subject_name, birth_date, birth_place, owner_id, owner_username, is_own, granted }, ... ] }`
- Granted charts appear first (`granted: true`)
- Own charts have `is_own: true`

- [ ] **Step 3: Verify 404 for unknown user**

```bash
fetch('/api/admin/users/nonexistent-uid/chart-grants').then(r => r.json()).then(console.log)
```

Expected: `{ error: { code: 'DATA_NOT_FOUND', ... } }` with status 404.

- [ ] **Step 4: Commit**

```bash
git add src/app/api/admin/users/[id]/chart-grants/route.ts
git commit -m "feat(admin): GET /api/admin/users/[id]/chart-grants — charts with grant status"
```

---

## Task 4: Add audit logging to grants route

**Files:**
- Modify: `src/app/api/clients/[id]/grants/route.ts`

> ⚠️ **Auth pattern note:** This file has its own local `requireSuperAdmin` that returns `{ error, user }`. The guard is `if (auth.error) return auth.error` — NOT `instanceof NextResponse`. Do not change this. Just add `writeAuditLog` calls after successful mutations.

- [ ] **Step 1: Import `writeAuditLog` at the top of the grants route**

Add to the imports section:

```typescript
import { writeAuditLog } from '@/lib/admin/audit'
```

- [ ] **Step 2: Add audit log call to POST (grant)**

First extend the chart existence check to also fetch `name` (needed for audit detail). Find the `chartCheck` query and replace it:

```typescript
  const chartCheck = await query<{ id: string; name: string }>(
    'SELECT id, name FROM charts WHERE id=$1',
    [id]
  )
  if (!chartCheck.rows[0]) {
    return NextResponse.json({ error: 'chart_not_found' }, { status: 404 })
  }
```

Then, immediately **before** the existing `return NextResponse.json({ grant: rows[0] }, { status: 201 })` line, insert:

```typescript
  await writeAuditLog(auth.user!.uid, 'chart_grant', principalId, {
    chart_id: id,
    chart_name: chartCheck.rows[0].name,
  })
  return NextResponse.json({ grant: rows[0] }, { status: 201 })
```

- [ ] **Step 3: Add audit log call to DELETE (revoke)**

The DELETE handler does not currently fetch the chart name. Add a name lookup before the delete, then add the audit call immediately **before** the existing `return NextResponse.json({ revoked: rows[0].id })`:

```typescript
  // Fetch name for audit detail before deleting
  const { rows: chartMeta } = await query<{ name: string }>(
    'SELECT name FROM charts WHERE id=$1', [id]
  )

  const { rows } = await query<{ id: string }>(
    'DELETE FROM chart_grants WHERE chart_id=$1 AND principal_id=$2 RETURNING id',
    [id, principalId]
  )
  if (rows.length === 0) {
    return NextResponse.json({ error: 'grant_not_found' }, { status: 404 })
  }

  await writeAuditLog(auth.user!.uid, 'chart_revoke', principalId, {
    chart_id: id,
    chart_name: chartMeta[0]?.name ?? null,
  })
  return NextResponse.json({ revoked: rows[0].id })
```

- [ ] **Step 4: Verify TypeScript compiles**

```bash
npx tsc --noEmit 2>&1 | head -20
```

Expected: no errors.

- [ ] **Step 5: Commit**

```bash
git add src/app/api/clients/[id]/grants/route.ts
git commit -m "feat(admin): audit log chart_grant and chart_revoke actions"
```

---

## Task 5: Build ChartsTab component

**Files:**
- Create: `src/components/admin/ChartsTab.tsx`

This is the largest task. The component receives `users` (already fetched by `AdminClient`) and `onGrantMutated` (to trigger an audit log refetch). It manages its own chart-grants query per selected guest.

- [ ] **Step 1: Create `ChartsTab.tsx`**

```typescript
'use client'

import { useState, useEffect, useMemo } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'
import { toast } from 'sonner'
import { adminCard } from './styles'
import type { AdminUser, AdminChartGrant } from './types'

// ── Helpers ──────────────────────────────────────────────────────────────────

async function fetchJson<T>(url: string): Promise<T> {
  const r = await fetch(url)
  if (!r.ok) throw new Error(`Request failed: ${r.status}`)
  return r.json() as Promise<T>
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString(undefined, {
    year: 'numeric', month: 'short', day: 'numeric',
  })
}

// ── Left panel ────────────────────────────────────────────────────────────────

function GuestList({
  guests,
  selectedId,
  grantCounts,
  onSelect,
}: {
  guests: AdminUser[]
  selectedId: string | null
  grantCounts: Record<string, number>  // known grant counts per guest (populated lazily)
  onSelect: (id: string) => void
}) {
  if (guests.length === 0) {
    return (
      <div className="px-4 py-8 text-center text-xs text-muted-foreground">
        No guests yet — create one in the Users tab.
      </div>
    )
  }

  return (
    <div className="space-y-1 p-2">
      {guests.map((g) => {
        const isSelected = g.id === selectedId
        const count = grantCounts[g.id]
        return (
          <button
            key={g.id}
            onClick={() => onSelect(g.id)}
            className={[
              'flex w-full items-center justify-between rounded-md px-3 py-2 text-left transition-colors',
              isSelected
                ? 'border border-[rgba(var(--brand-gold-rgb),0.35)] bg-[rgba(var(--brand-gold-rgb),0.08)]'
                : 'border border-transparent hover:bg-[rgba(var(--brand-gold-rgb),0.04)]',
            ].join(' ')}
          >
            <div className="min-w-0">
              <div className={`truncate text-sm font-medium ${isSelected ? 'text-brand-gold' : 'text-muted-foreground'}`}>
                {g.username ?? g.name ?? g.id}
              </div>
              <div className="truncate text-[11px] text-muted-foreground/60">{g.email}</div>
            </div>
            {/* Badge — shown only after the guest's chart-grants have been fetched at least once */}
            {count !== undefined && count > 0 && (
              <span className="ml-2 shrink-0 rounded-full border border-[rgba(var(--brand-gold-rgb),0.3)] bg-[rgba(var(--brand-gold-rgb),0.12)] px-1.5 py-0.5 text-[10px] text-brand-gold">
                {count}
              </span>
            )}
          </button>
        )
      })}
    </div>
  )
}

// ── Chart row ─────────────────────────────────────────────────────────────────

function ChartRow({
  chart,
  guestId,
  onToggled,
}: {
  chart: AdminChartGrant
  guestId: string
  onToggled: (chartId: string, nowGranted: boolean) => void
}) {
  const [loading, setLoading] = useState(false)

  async function handleToggle() {
    setLoading(true)
    try {
      if (chart.granted) {
        const r = await fetch(
          `/api/clients/${chart.id}/grants?principal_id=${encodeURIComponent(guestId)}`,
          { method: 'DELETE' }
        )
        const body = await r.json().catch(() => ({}))
        if (!r.ok) {
          toast.error(body?.error?.detail ?? body?.error?.message ?? 'Revoke failed.')
          return
        }
        onToggled(chart.id, false)
      } else {
        const r = await fetch(`/api/clients/${chart.id}/grants`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ principal_id: guestId }),
        })
        const body = await r.json().catch(() => ({}))
        if (!r.ok) {
          toast.error(body?.error?.detail ?? body?.error?.message ?? 'Grant failed.')
          return
        }
        onToggled(chart.id, true)
      }
    } catch {
      toast.error('Network error.')
    } finally {
      setLoading(false)
    }
  }

  const label = chart.subject_name ?? '—'
  const owner = chart.owner_username ?? chart.owner_id

  return (
    <div
      className={[
        'flex items-center justify-between rounded-lg border px-4 py-3 transition-colors',
        chart.is_own
          ? 'border-[rgba(255,255,255,0.04)] opacity-40'
          : chart.granted
            ? 'border-emerald-700/25 bg-emerald-950/20'
            : 'border-[rgba(var(--brand-gold-rgb),0.08)]',
      ].join(' ')}
    >
      <div className="min-w-0 flex-1">
        <div className="flex items-baseline gap-2">
          <span className="font-serif text-sm text-brand-gold-cream">{label}</span>
          <span className="text-[11px] text-muted-foreground">{formatDate(chart.birth_date)}</span>
          {chart.owner_username && !chart.is_own && (
            <span className="text-[11px] text-muted-foreground/50">by {owner}</span>
          )}
        </div>
        <div className="mt-0.5 text-[11px] text-muted-foreground">{chart.birth_place}</div>
      </div>

      <div className="ml-4 shrink-0">
        {chart.is_own ? (
          <span className="text-[11px] italic text-muted-foreground">their own chart</span>
        ) : (
          <button
            onClick={handleToggle}
            disabled={loading}
            className={[
              'rounded-md border px-3 py-1.5 text-[11px] font-medium transition-colors disabled:cursor-wait disabled:opacity-50',
              chart.granted
                ? 'border-emerald-700/50 bg-emerald-950/30 text-emerald-400 hover:bg-red-950/30 hover:border-red-700/50 hover:text-red-400'
                : 'border-[rgba(var(--brand-gold-rgb),0.3)] bg-transparent text-brand-gold hover:border-brand-gold',
            ].join(' ')}
          >
            {loading
              ? '…'
              : chart.granted
                ? '✓ Granted · Revoke'
                : '+ Grant access'}
          </button>
        )}
      </div>
    </div>
  )
}

// ── Right panel ───────────────────────────────────────────────────────────────

function ChartAccessPanel({
  guest,
  fromUsers,
  onGrantMutated,
  onGrantCountKnown,
}: {
  guest: AdminUser
  fromUsers: boolean
  onGrantMutated: () => void
  onGrantCountKnown: (guestId: string, count: number) => void
}) {
  const router = useRouter()
  const [search, setSearch] = useState('')

  const { data, isError, refetch } = useQuery({
    queryKey: ['admin', 'chart-grants', guest.id],
    queryFn: () => fetchJson<{ charts: AdminChartGrant[] }>(
      `/api/admin/users/${guest.id}/chart-grants`
    ),
  })

  const [localCharts, setLocalCharts] = useState<AdminChartGrant[]>([])

  // Sync React Query data into local state for optimistic updates.
  // Also report the grant count to the parent so the left panel badge can update.
  useEffect(() => {
    if (data?.charts) {
      setLocalCharts(data.charts)
      const count = data.charts.filter(c => c.granted && !c.is_own).length
      onGrantCountKnown(guest.id, count)
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data?.charts])

  function handleToggled(chartId: string, nowGranted: boolean) {
    setLocalCharts(prev =>
      prev
        .map(c => c.id === chartId ? { ...c, granted: nowGranted } : c)
        .sort((a, b) => {
          // granted first, own last
          if (a.granted !== b.granted) return a.granted ? -1 : 1
          if (a.is_own !== b.is_own) return a.is_own ? 1 : -1
          return 0
        })
    )
    onGrantMutated()
    // Background refetch to sync
    refetch()
  }

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase()
    if (!q) return localCharts
    return localCharts.filter(c =>
      (c.subject_name ?? '').toLowerCase().includes(q) ||
      c.birth_place.toLowerCase().includes(q)
    )
  }, [localCharts, search])

  const grantedCount = localCharts.filter(c => c.granted).length
  const totalCount = localCharts.filter(c => !c.is_own).length

  return (
    <div className="flex flex-1 flex-col">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-[rgba(var(--brand-gold-rgb),0.1)] px-5 py-4">
        <div>
          <div className="flex items-center gap-2">
            {fromUsers && (
              <button
                onClick={() => router.push('/admin?tab=users')}
                className="rounded border border-[rgba(255,255,255,0.06)] bg-[rgba(255,255,255,0.03)] px-2 py-0.5 text-[10px] text-muted-foreground hover:text-brand-gold-cream"
              >
                ← from Users
              </button>
            )}
            <span className="font-serif text-base text-brand-gold-cream">
              {guest.username ?? guest.name ?? guest.id}&apos;s chart access
            </span>
          </div>
          <div className="mt-0.5 text-[11px] text-muted-foreground">
            {grantedCount} of {totalCount} charts shared
          </div>
        </div>
        <input
          type="search"
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder="Search charts…"
          className="w-44 rounded-md border border-[rgba(var(--brand-gold-rgb),0.18)] bg-brand-ink px-3 py-1.5 text-sm text-brand-gold-cream placeholder:text-muted-foreground focus:border-brand-gold focus:outline-none"
        />
      </div>

      {/* Chart list */}
      <div className="flex-1 overflow-y-auto px-4 py-3">
        {isError ? (
          <p className="py-8 text-center text-sm text-red-400">Could not load charts — check DB proxy.</p>
        ) : localCharts.length === 0 ? (
          <p className="py-8 text-center text-sm text-muted-foreground">No charts on the platform yet.</p>
        ) : filtered.length === 0 ? (
          <p className="py-6 text-center text-sm text-muted-foreground">No charts match &ldquo;{search}&rdquo;.</p>
        ) : (
          <div className="space-y-2">
            {filtered.map(c => (
              <ChartRow
                key={c.id}
                chart={c}
                guestId={guest.id}
                onToggled={handleToggled}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

// ── Main export ───────────────────────────────────────────────────────────────

export function ChartsTab({
  users,
  onGrantMutated,
}: {
  users: AdminUser[]
  onGrantMutated: () => void
}) {
  const router = useRouter()
  const searchParams = useSearchParams()
  const guestParam = searchParams.get('guest')

  const guests = useMemo(
    () => users.filter(u => u.role === 'guest'),
    [users]
  )

  const [selectedId, setSelectedId] = useState<string | null>(guestParam)
  // fromUsers: true only when arriving via the deep-link from Users tab.
  // Reset to false when the admin manually clicks a different guest.
  const [fromUsers, setFromUsers] = useState(!!guestParam)

  // Sync from URL on mount only (covers browser Back/Forward navigation)
  useEffect(() => {
    if (guestParam) {
      setSelectedId(guestParam)
      setFromUsers(true)
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []) // intentionally run once on mount

  // Track grant counts per guest — populated lazily as guests are selected.
  const [grantCounts, setGrantCounts] = useState<Record<string, number>>({})

  function handleSelectGuest(id: string) {
    setSelectedId(id)
    setFromUsers(false)  // manual navigation — hide breadcrumb
    router.replace(`/admin?tab=charts&guest=${id}`, { scroll: false })
  }

  function handleGrantCountKnown(guestId: string, count: number) {
    setGrantCounts(prev => ({ ...prev, [guestId]: count }))
  }

  const selectedGuest = useMemo(
    () => guests.find(g => g.id === selectedId) ?? null,
    [guests, selectedId]
  )

  return (
    <section className={adminCard + ' overflow-hidden'}>
      <header className="border-b border-[rgba(var(--brand-gold-rgb),0.15)] px-6 py-4">
        <h2 className="font-serif text-lg text-brand-gold-cream">Charts</h2>
        <p className="mt-0.5 text-xs text-muted-foreground">
          Share platform charts with guest users.
        </p>
      </header>

      <div className="flex" style={{ minHeight: '480px' }}>
        {/* Left: guest list */}
        <div className="w-56 shrink-0 border-r border-[rgba(var(--brand-gold-rgb),0.12)] bg-[rgba(0,0,0,0.2)]">
          <div className="border-b border-[rgba(var(--brand-gold-rgb),0.08)] px-4 py-3">
            <span className="text-[10px] uppercase tracking-[0.16em] text-muted-foreground">Guests</span>
          </div>
          <GuestList
            guests={guests}
            selectedId={selectedId}
            grantCounts={grantCounts}
            onSelect={handleSelectGuest}
          />
        </div>

        {/* Right: chart access panel or placeholder */}
        {selectedGuest ? (
          <ChartAccessPanel
            key={selectedGuest.id}
            guest={selectedGuest}
            fromUsers={fromUsers}
            onGrantMutated={onGrantMutated}
            onGrantCountKnown={handleGrantCountKnown}
          />
        ) : (
          <div className="flex flex-1 items-center justify-center">
            <p className="text-sm text-muted-foreground">
              Select a guest to manage their chart access.
            </p>
          </div>
        )}
      </div>
    </section>
  )
}
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
npx tsc --noEmit 2>&1 | head -20
```

Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add src/components/admin/ChartsTab.tsx
git commit -m "feat(admin): ChartsTab split-panel component"
```

---

## Task 6: Refactor AdminClient to URL-param tab system and add Charts tab

**Files:**
- Modify: `src/components/admin/AdminClient.tsx`
- Modify: `src/app/admin/page.tsx`

The current `AdminClient` is a vertical stack with no tabs. This task converts it to a tab system driven by the `?tab=` URL search param, and mounts `ChartsTab` as the third tab.

- [ ] **Step 1: Wrap `<AdminClient>` in `<Suspense>` in `page.tsx`**

`useSearchParams()` inside a `'use client'` component requires a `<Suspense>` boundary in the parent Server Component. Update `src/app/admin/page.tsx`:

```typescript
import { Suspense } from 'react'
import { getServerUserWithProfile } from '@/lib/auth/access-control'
import { redirect } from 'next/navigation'
import { AdminClient } from '@/components/admin/AdminClient'

export default async function AdminPage() {
  const ctx = await getServerUserWithProfile()
  if (!ctx) redirect('/login')
  return (
    <Suspense>
      <AdminClient currentUserId={ctx.user.uid} />
    </Suspense>
  )
}
```

- [ ] **Step 2: Rewrite `AdminClient.tsx` with tab system**

Replace the full file contents:

```typescript
'use client'

import { useQuery } from '@tanstack/react-query'
import { useRouter, useSearchParams } from 'next/navigation'
import { PendingRequestsTable } from './PendingRequestsTable'
import { UsersTable } from './UsersTable'
import { AuditLogPanel } from './AuditLogPanel'
import { ChartsTab } from './ChartsTab'
import type { AdminAccessRequest, AdminUser } from './types'
import type { AuditLogEntry } from '@/app/api/admin/audit-log/route'

type Tab = 'pending' | 'users' | 'charts' | 'audit'

const TABS: { id: Tab; label: string }[] = [
  { id: 'pending', label: 'Pending Requests' },
  { id: 'users',   label: 'Users' },
  { id: 'charts',  label: 'Charts' },
  { id: 'audit',   label: 'Audit Log' },
]

async function fetchJson<T>(url: string): Promise<T> {
  const res = await fetch(url)
  if (!res.ok) throw new Error(`Request failed: ${res.status}`)
  return (await res.json()) as T
}

export function AdminClient({ currentUserId }: { currentUserId: string }) {
  const router = useRouter()
  const searchParams = useSearchParams()
  const activeTab = (searchParams.get('tab') as Tab | null) ?? 'pending'

  function setTab(tab: Tab) {
    router.push(`/admin?tab=${tab}`, { scroll: false })
  }

  const requestsQuery = useQuery({
    queryKey: ['admin', 'access-requests'],
    queryFn: () => fetchJson<{ requests: AdminAccessRequest[] }>('/api/admin/access-requests'),
  })
  const usersQuery = useQuery({
    queryKey: ['admin', 'users'],
    queryFn: () => fetchJson<{ users: AdminUser[] }>('/api/admin/users'),
  })
  const auditQuery = useQuery({
    queryKey: ['admin', 'audit-log'],
    queryFn: () => fetchJson<{ entries: AuditLogEntry[] }>('/api/admin/audit-log'),
  })

  function refetchAll() {
    requestsQuery.refetch()
    usersQuery.refetch()
    auditQuery.refetch()
  }

  const pendingCount = (requestsQuery.data?.requests ?? []).filter(r => r.status === 'pending').length

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-serif text-3xl font-medium tracking-wide text-brand-gold-cream">
          Administration
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Manage users, chart access, and platform activity.
        </p>
      </div>

      {/* Tab bar */}
      <div className="flex border-b border-[rgba(var(--brand-gold-rgb),0.18)]">
        {TABS.map(tab => (
          <button
            key={tab.id}
            onClick={() => setTab(tab.id)}
            className={[
              'relative px-5 py-3 text-[11px] uppercase tracking-[0.14em] transition-colors',
              activeTab === tab.id
                ? 'text-brand-gold after:absolute after:bottom-0 after:left-0 after:right-0 after:h-[2px] after:bg-brand-gold'
                : 'text-muted-foreground hover:text-brand-gold-cream',
            ].join(' ')}
          >
            {tab.label}
            {tab.id === 'pending' && pendingCount > 0 && (
              <span className="ml-1.5 rounded-full bg-amber-950/60 border border-amber-700/40 px-1.5 py-0.5 text-[10px] text-amber-400">
                {pendingCount}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Tab panels */}
      {activeTab === 'pending' && (
        requestsQuery.isError ? (
          <p className="text-sm text-red-400">Could not load access requests — check DB proxy.</p>
        ) : (
          <PendingRequestsTable
            requests={requestsQuery.data?.requests ?? []}
            onMutated={refetchAll}
          />
        )
      )}

      {activeTab === 'users' && (
        usersQuery.isError ? (
          <p className="text-sm text-red-400">Could not load users — check DB proxy.</p>
        ) : (
          <UsersTable
            users={usersQuery.data?.users ?? []}
            currentUserId={currentUserId}
            onMutated={refetchAll}
          />
        )
      )}

      {activeTab === 'charts' && (
        usersQuery.isError ? (
          <p className="text-sm text-red-400">Could not load guests — check DB proxy.</p>
        ) : (
          <ChartsTab
            users={usersQuery.data?.users ?? []}
            onGrantMutated={auditQuery.refetch}
          />
        )
      )}

      {activeTab === 'audit' && (
        auditQuery.isError ? (
          <p className="text-sm text-red-400">Could not load audit log.</p>
        ) : (
          <AuditLogPanel entries={auditQuery.data?.entries ?? []} />
        )
      )}
    </div>
  )
}
```

- [ ] **Step 3: Verify TypeScript compiles**

```bash
npx tsc --noEmit 2>&1 | head -20
```

- [ ] **Step 4: Smoke test in browser**

1. Navigate to `/admin` — should default to Pending Requests tab
2. Click each tab — content should switch
3. Navigate to `/admin?tab=charts` — Charts tab should be active, right panel shows "Select a guest…"
4. Click a guest — right panel should load and show charts with grant status

- [ ] **Step 5: Commit**

```bash
git add src/components/admin/AdminClient.tsx src/app/admin/page.tsx
git commit -m "feat(admin): URL-param tab system with Charts tab"
```

---

## Task 7: Add "Manage chart access" to UsersTable

**Files:**
- Modify: `src/components/admin/UsersTable.tsx`

- [ ] **Step 1: Add `useRouter` import**

`UsersTable.tsx` already uses `DropdownMenuItem`. Add `useRouter` to the imports:

```typescript
import { useRouter } from 'next/navigation'
```

- [ ] **Step 2: Initialise router inside the component**

At the top of the `UsersTable` function body, add:

```typescript
const router = useRouter()
```

- [ ] **Step 3: Add "Manage chart access" item to the Actions dropdown**

In the dropdown, insert before the first `<DropdownMenuSeparator />` (before the role change items):

```typescript
<DropdownMenuItem
  onClick={() => router.push(`/admin?tab=charts&guest=${u.id}`)}
>
  ✦ Manage chart access
</DropdownMenuItem>
<DropdownMenuSeparator />
```

The full dropdown order becomes:
1. Edit username
2. Send password reset link
3. **✦ Manage chart access** ← new
4. — separator —
5. Promote / Demote
6. — separator —
7. Disable / Enable
8. — separator —
9. Delete

- [ ] **Step 4: Verify TypeScript compiles**

```bash
npx tsc --noEmit 2>&1 | head -20
```

- [ ] **Step 5: Smoke test the full user-first flow**

1. Go to `/admin?tab=users`
2. Click Actions on a guest → should see "✦ Manage chart access" in the dropdown
3. Click it → should navigate to `/admin?tab=charts&guest=<uid>`
4. Charts tab should open with that guest already selected in the left panel
5. A "← from Users" chip should appear in the right panel header
6. Click "← from Users" → should return to `/admin?tab=users`

- [ ] **Step 6: Commit**

```bash
git add src/components/admin/UsersTable.tsx
git commit -m "feat(admin): 'Manage chart access' shortcut in Users tab Actions"
```

---

## Final verification checklist

Before marking this complete:

- [ ] Grant flow: go to Charts tab, select a guest, click "+ Grant access" on a chart → row turns green immediately. Refresh — grant persists.
- [ ] Revoke flow: click "✓ Granted · Revoke" → row returns to ungold state. Refresh — revoke persists.
- [ ] Own charts: guest's own charts show "their own chart" with no button.
- [ ] Guest's chart access is real: log in as the guest user and verify they can now see the shared chart in whatever chart-browsing surface exists.
- [ ] Audit log: after grant + revoke, go to Audit Log tab — `chart_grant` and `chart_revoke` entries should appear.
- [ ] "No charts" empty state: if platform has no charts, right panel shows the empty message.
- [ ] Search: type in the search box — chart rows filter client-side without re-fetching.
- [ ] Browser Back: from Charts tab (arrived via "Manage chart access"), clicking Back returns to Users tab.
- [ ] TypeScript: `npx tsc --noEmit` passes with no errors.
