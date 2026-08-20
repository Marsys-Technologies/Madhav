'use client'

import { useState, useMemo } from 'react'
import Link from 'next/link'
import { cn } from '@/lib/utils'
import { formatDate } from '@/lib/utils/date'
import type { ChartWithMeta } from '@/lib/roster/types'

type SortKey = 'name' | 'buildPct' | 'activity'

interface RosterTableViewProps {
  charts: ChartWithMeta[]
}

const GHOST_BTN = "border border-[rgba(212,175,55,0.22)] bg-transparent text-[rgba(212,175,55,0.55)] text-xs font-semibold uppercase tracking-[0.08em] rounded-md px-3 py-1.5 hover:text-[#fce29a] hover:border-[rgba(212,175,55,0.4)] transition-colors"

export function RosterTableView({ charts }: RosterTableViewProps) {
  const [sortKey, setSortKey] = useState<SortKey>('name')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc')

  const sorted = useMemo(() => {
    return [...charts].sort((a, b) => {
      let cmp = 0
      if (sortKey === 'name') cmp = a.name.localeCompare(b.name)
      else if (sortKey === 'buildPct') cmp = a.pyramidPercent - b.pyramidPercent
      else if (sortKey === 'activity') {
        const ta = a.lastLayerActivity ? new Date(a.lastLayerActivity).getTime() : 0
        const tb = b.lastLayerActivity ? new Date(b.lastLayerActivity).getTime() : 0
        cmp = ta - tb
      }
      return sortDir === 'asc' ? cmp : -cmp
    })
  }, [charts, sortKey, sortDir])

  function toggle(key: SortKey) {
    if (sortKey === key) setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))
    else { setSortKey(key); setSortDir('asc') }
  }

  function sortIndicator(key: SortKey) {
    if (sortKey !== key) return null
    return sortDir === 'asc' ? ' ↑' : ' ↓'
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-[rgba(212,175,55,0.15)]">
      <table className="w-full text-xs">
        <thead className="bg-[rgba(8,6,3,0.6)]">
          <tr>
            <th
              scope="col"
              className="bt-label bt-label-upper px-3 py-2 text-left whitespace-nowrap"
              style={{ color: 'rgba(212,175,55,0.45)' }}
              aria-sort={sortKey === 'name' ? (sortDir === 'asc' ? 'ascending' : 'descending') : 'none'}
            >
              <button
                onClick={() => toggle('name')}
                aria-label={`Sort by name${sortKey === 'name' ? `, currently ${sortDir}ending` : ''}`}
                className="cursor-pointer select-none hover:text-[#d4af37] transition-colors"
              >
                Name{sortIndicator('name')}
              </button>
            </th>
            <th
              scope="col"
              className="bt-label bt-label-upper px-3 py-2 text-left"
              style={{ color: 'rgba(212,175,55,0.45)' }}
            >
              Birth
            </th>
            <th
              scope="col"
              className="bt-label bt-label-upper px-3 py-2 text-left"
              style={{ color: 'rgba(212,175,55,0.45)' }}
            >
              Current dasha
            </th>
            <th
              scope="col"
              className="bt-label bt-label-upper px-3 py-2 text-left whitespace-nowrap"
              style={{ color: 'rgba(212,175,55,0.45)' }}
              aria-sort={sortKey === 'buildPct' ? (sortDir === 'asc' ? 'ascending' : 'descending') : 'none'}
            >
              <button
                onClick={() => toggle('buildPct')}
                aria-label={`Sort by build percentage${sortKey === 'buildPct' ? `, currently ${sortDir}ending` : ''}`}
                className="cursor-pointer select-none hover:text-[#d4af37] transition-colors"
              >
                Build %{sortIndicator('buildPct')}
              </button>
            </th>
            <th
              scope="col"
              className="bt-label bt-label-upper px-3 py-2 text-left whitespace-nowrap"
              style={{ color: 'rgba(212,175,55,0.45)' }}
              aria-sort={sortKey === 'activity' ? (sortDir === 'asc' ? 'ascending' : 'descending') : 'none'}
            >
              <button
                onClick={() => toggle('activity')}
                aria-label={`Sort by last activity${sortKey === 'activity' ? `, currently ${sortDir}ending` : ''}`}
                className="cursor-pointer select-none hover:text-[#d4af37] transition-colors"
              >
                Last activity{sortIndicator('activity')}
              </button>
            </th>
            <th
              scope="col"
              className="bt-label bt-label-upper px-3 py-2 text-left"
              style={{ color: 'rgba(212,175,55,0.45)' }}
            >
              Actions
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-[rgba(212,175,55,0.1)]">
          {sorted.map((c) => (
            <tr key={c.id} className="hover:bg-[rgba(212,175,55,0.04)] transition-colors">
              <td className="px-3 py-2">
                <p className="bt-heading text-[#fce29a]">{c.name}</p>
              </td>
              <td className="px-3 py-2">
                <p className="bt-label text-[rgba(212,175,55,0.6)]">{formatDate(c.birth_date)}</p>
                <p className="bt-label text-[rgba(212,175,55,0.38)]">{c.birth_place}</p>
              </td>
              <td className="px-3 py-2 bt-label text-[rgba(212,175,55,0.38)] italic">
                —
              </td>
              <td className="whitespace-nowrap px-3 py-2 tabular-nums font-[var(--font-mono)] text-[#d4af37]">
                {c.pyramidPercent}%
              </td>
              <td className="whitespace-nowrap px-3 py-2 bt-label text-[rgba(212,175,55,0.42)]">
                {formatDate(c.lastLayerActivity)}
              </td>
              <td className="px-3 py-2">
                <div className="flex gap-1.5">
                  {c.canBuild ? (
                    <Link
                      href={`/clients/${c.id}/nirmana`}
                      className={cn(GHOST_BTN)}
                      aria-label={`Nirmāṇa (build) — ${c.name}`}
                    >
                      Nirmāṇa
                    </Link>
                  ) : (
                    <button
                      type="button"
                      disabled
                      aria-label={`Nirmāṇa (build) — ${c.name} — view-only`}
                      title="View-only — build restricted"
                      data-testid="nirmana-disabled"
                      className={cn(GHOST_BTN, 'cursor-not-allowed opacity-35')}
                    >
                      Nirmāṇa
                    </button>
                  )}
                  <Link
                    href={`/clients/${c.id}/pariprashna`}
                    className={cn(GHOST_BTN)}
                    aria-label={`Pariprashna (consult) — ${c.name}`}
                  >
                    Pariprashna
                  </Link>
                </div>
              </td>
            </tr>
          ))}
          {sorted.length === 0 && (
            <tr>
              <td colSpan={6} className="px-3 py-6 text-center text-[rgba(212,175,55,0.38)]">
                No charts match the current filters.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  )
}
