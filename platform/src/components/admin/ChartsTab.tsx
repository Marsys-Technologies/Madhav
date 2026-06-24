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
  grantCounts: Record<string, number>
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
          if (a.granted !== b.granted) return a.granted ? -1 : 1
          if (a.is_own !== b.is_own) return a.is_own ? 1 : -1
          return 0
        })
    )
    onGrantMutated()
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

  const grantedCount = localCharts.filter(c => c.granted && !c.is_own).length
  const totalCount = localCharts.filter(c => !c.is_own).length

  return (
    <div className="flex flex-1 flex-col">
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
  const [fromUsers, setFromUsers] = useState(!!guestParam)

  useEffect(() => {
    if (guestParam) {
      setSelectedId(guestParam)
      setFromUsers(true)
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const [grantCounts, setGrantCounts] = useState<Record<string, number>>({})

  function handleSelectGuest(id: string) {
    setSelectedId(id)
    setFromUsers(false)
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
