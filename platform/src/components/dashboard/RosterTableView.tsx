'use client'

import { useState, useMemo } from 'react'
import Link from 'next/link'
import { formatDate } from '@/lib/utils/date'
import type { ChartWithMeta } from '@/lib/roster/types'

type SortKey = 'name' | 'buildPct' | 'activity'

interface RosterTableViewProps {
  charts: ChartWithMeta[]
}

export function RosterTableView({ charts }: RosterTableViewProps) {
  const [sortKey, setSortKey] = useState<SortKey>('name')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc')

  const sorted = useMemo(() => {
    return [...charts].sort((a, b) => {
      let cmp = 0
      if (sortKey === 'name') cmp = a.name.localeCompare(b.name)
      else if (sortKey === 'buildPct') cmp = a.readiness.percent - b.readiness.percent
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
    <div role="region" aria-label="Charts table" tabIndex={0} className="overflow-x-auto rounded-lg border border-[var(--folio-divider)] bg-[var(--folio-panel)] text-[var(--folio-ink)] focus-visible:outline-2 focus-visible:outline-[var(--folio-focus)]">
      <table className="w-full text-xs">
        <thead className="bg-[var(--folio-selected)]">
          <tr>
            <th
              scope="col"
              className="bt-label bt-label-upper px-3 py-2 text-left whitespace-nowrap"
              style={{ color: 'var(--folio-muted)' }}
              aria-sort={sortKey === 'name' ? (sortDir === 'asc' ? 'ascending' : 'descending') : 'none'}
            >
              <button
                onClick={() => toggle('name')}
                aria-label={`Sort by name${sortKey === 'name' ? `, currently ${sortDir}ending` : ''}`}
                className="cursor-pointer select-none hover:underline focus-visible:outline-2 focus-visible:outline-[var(--folio-focus)]"
              >
                Name{sortIndicator('name')}
              </button>
            </th>
            <th
              scope="col"
              className="bt-label bt-label-upper px-3 py-2 text-left"
              style={{ color: 'var(--folio-muted)' }}
            >
              Birth details
            </th>
            <th
              scope="col"
              className="bt-label bt-label-upper px-3 py-2 text-left whitespace-nowrap"
              style={{ color: 'var(--folio-muted)' }}
              aria-sort={sortKey === 'buildPct' ? (sortDir === 'asc' ? 'ascending' : 'descending') : 'none'}
            >
              <button
                onClick={() => toggle('buildPct')}
                aria-label={`Sort by build percentage${sortKey === 'buildPct' ? `, currently ${sortDir}ending` : ''}`}
                className="cursor-pointer select-none hover:underline focus-visible:outline-2 focus-visible:outline-[var(--folio-focus)]"
              >
                Build{sortIndicator('buildPct')}
              </button>
            </th>
            <th
              scope="col"
              className="bt-label bt-label-upper px-3 py-2 text-left whitespace-nowrap"
              style={{ color: 'var(--folio-muted)' }}
              aria-sort={sortKey === 'activity' ? (sortDir === 'asc' ? 'ascending' : 'descending') : 'none'}
            >
              <button
                onClick={() => toggle('activity')}
                aria-label={`Sort by last activity${sortKey === 'activity' ? `, currently ${sortDir}ending` : ''}`}
                className="cursor-pointer select-none hover:underline focus-visible:outline-2 focus-visible:outline-[var(--folio-focus)]"
              >
                Last activity{sortIndicator('activity')}
              </button>
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-[var(--folio-divider)]">
          {sorted.map((c) => (
            <tr key={c.id} className="hover:bg-[var(--folio-selected)]">
              <td className="px-3 py-2">
                <Link
                  href={`/clients/${c.id}`}
                  className="bt-heading inline-flex min-h-11 items-center break-words rounded-sm text-[var(--folio-action)] underline-offset-4 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--folio-focus)]"
                >
                  {c.name}
                </Link>
              </td>
              <td className="px-3 py-2">
                <p className="bt-label text-[var(--folio-muted)]">{formatDate(c.birth_date)}</p>
                <p className="bt-label text-[var(--folio-muted)]">{c.birth_place}</p>
              </td>
              <td className="whitespace-nowrap px-3 py-2">
                <span className="tabular-nums font-[var(--font-mono)] text-[var(--folio-action)]">{c.readiness.percent}%</span>
                <span className="bt-label ml-2 text-[var(--folio-muted)]">{c.readiness.label}</span>
              </td>
              <td className="whitespace-nowrap px-3 py-2 bt-label text-[var(--folio-muted)]">
                {formatDate(c.lastLayerActivity)}
              </td>
            </tr>
          ))}
          {sorted.length === 0 && (
            <tr>
              <td colSpan={4} className="px-3 py-6 text-center text-[var(--folio-muted)]">
                No charts match the current filters.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  )
}
