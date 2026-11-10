'use client'

import { useCallback } from 'react'
import type { FilterState } from '@/lib/roster/types'

export type ViewMode = 'grid' | 'table'

interface RosterFiltersProps {
  filters: FilterState
  view: ViewMode
  places: string[]
  onFilterChange: (next: Partial<FilterState>) => void
  onViewChange: (view: ViewMode) => void
}

const filterControl = 'min-h-11 min-w-0 max-w-full rounded-md border border-[var(--folio-boundary)] bg-[var(--folio-panel)] px-3 text-base text-[var(--folio-ink)] placeholder:text-[var(--folio-muted)] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--folio-focus)]'

export function RosterFilters({
  filters,
  view,
  places,
  onFilterChange,
  onViewChange,
}: RosterFiltersProps) {
  const handleBuildRangeChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      onFilterChange({ buildMax: parseInt(e.target.value, 10) })
    },
    [onFilterChange]
  )

  return (
    <div className="flex flex-wrap items-center gap-2">
      {/* Search */}
      <input
        aria-label="Search charts"
        value={filters.q}
        onChange={(e) => onFilterChange({ q: e.target.value })}
        placeholder="Search name or place…"
        className={`${filterControl} w-full sm:max-w-xs`}
      />

      {/* Birth place */}
      <select
        aria-label="Filter by birth place"
        value={filters.place}
        onChange={(e) => onFilterChange({ place: e.target.value })}
        className={filterControl}
      >
        <option value="">All places</option>
        {places.map((p) => (
          <option key={p} value={p}>
            {p}
          </option>
        ))}
      </select>

      {/* Dasha — disabled until Phase 14C */}
      <select
        aria-label="Filter by current dasha"
        disabled
        title="Dasha data available after Phase 14C"
        className={`${filterControl} opacity-60 cursor-not-allowed`}
      >
        <option>Current dasha</option>
      </select>

      {/* Build % max slider */}
      <label className="flex min-h-11 items-center gap-2 text-[var(--folio-muted)] text-sm">
        <span className="whitespace-nowrap">Build ≤ {filters.buildMax}%</span>
        <input
          type="range"
          min={0}
          max={100}
          step={10}
          value={filters.buildMax}
          onChange={handleBuildRangeChange}
          className="w-20 accent-[var(--folio-action)] focus-visible:outline-2 focus-visible:outline-[var(--folio-focus)]"
        />
      </label>

      {/* Last activity */}
      <select
        aria-label="Filter by last activity"
        value={filters.since}
        onChange={(e) => onFilterChange({ since: e.target.value })}
        className={filterControl}
      >
        <option value="">Any activity</option>
        <option value={sinceDate(7)}>Last 7 days</option>
        <option value={sinceDate(30)}>Last 30 days</option>
        <option value={sinceDate(90)}>Last 90 days</option>
      </select>

      {/* Spacer */}
      <span className="flex-1" />

      {/* Grid / Table toggle */}
      <div
        role="group"
        aria-label="View mode"
        className="flex items-center rounded-lg border border-[var(--folio-boundary)] bg-[var(--folio-panel)] p-1 text-sm"
      >
        {(['grid', 'table'] as ViewMode[]).map((v) => (
          <button
            key={v}
            onClick={() => onViewChange(v)}
            aria-pressed={view === v}
            className={`inline-flex min-h-11 items-center justify-center rounded-md px-3 font-medium capitalize focus-visible:outline-2 focus-visible:outline-[var(--folio-focus)] ${
              view === v
                ? 'bg-[var(--folio-selected)] text-[var(--folio-ink)] underline decoration-[var(--folio-action)] underline-offset-4'
                : 'text-[var(--folio-muted)] hover:text-[var(--folio-action)]'
            }`}
          >
            {v}
          </button>
        ))}
      </div>
    </div>
  )
}

function sinceDate(daysAgo: number): string {
  const d = new Date()
  d.setDate(d.getDate() - daysAgo)
  return d.toISOString().slice(0, 10)
}
