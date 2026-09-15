'use client'

import { useSyncExternalStore, useMemo, useCallback } from 'react'
import { useRouter, useSearchParams, usePathname } from 'next/navigation'
import { ClientCard } from './ClientCard'
import { RosterStatsRibbon } from './RosterStatsRibbon'
import { RosterFilters, type ViewMode } from './RosterFilters'
import { RosterTableView } from './RosterTableView'
import { RosterEmptyWizard } from './RosterEmptyWizard'
import {
  applyFilters,
  parseFilterFromParams,
  filterToParams,
  distinctPlaces,
  DEFAULT_FILTER,
} from '@/lib/roster/filter'
import type { ChartWithMeta, FilterState, RosterStats } from '@/lib/roster/types'

const VIEW_STORAGE_KEY = 'marsys.roster.view'
const VIEW_CHANGE_EVENT = 'marsys:roster-view-change'

function subscribeToView(onChange: () => void): () => void {
  window.addEventListener('storage', onChange)
  window.addEventListener(VIEW_CHANGE_EVENT, onChange)
  return () => {
    window.removeEventListener('storage', onChange)
    window.removeEventListener(VIEW_CHANGE_EVENT, onChange)
  }
}

function getViewSnapshot(): ViewMode {
  const stored = localStorage.getItem(VIEW_STORAGE_KEY)
  return stored === 'table' ? 'table' : 'grid'
}

const getServerViewSnapshot = (): ViewMode => 'grid'

interface Props {
  charts: ChartWithMeta[]
  stats: RosterStats
}

export function ClientRoster({ charts, stats }: Props) {
  const router = useRouter()
  const pathname = usePathname()
  const searchParams = useSearchParams()

  // View mode — persisted to localStorage
  const view = useSyncExternalStore(subscribeToView, getViewSnapshot, getServerViewSnapshot)
  function handleViewChange(next: ViewMode) {
    localStorage.setItem(VIEW_STORAGE_KEY, next)
    window.dispatchEvent(new Event(VIEW_CHANGE_EVENT))
  }

  // Filter state — lives in URL
  const filters: FilterState = useMemo(
    () => parseFilterFromParams(searchParams),
    [searchParams]
  )

  const handleFilterChange = useCallback(
    (next: Partial<FilterState>) => {
      const updated = { ...filters, ...next }
      const params = filterToParams(updated)
      const qs = params.toString()
      router.replace(qs ? `${pathname}?${qs}` : pathname, { scroll: false })
    },
    [filters, pathname, router]
  )

  const handleFilterShortcut = useCallback(
    (key: string, value: string) => {
      handleFilterChange({ [key]: key === 'buildMin' || key === 'buildMax' ? parseInt(value, 10) : value })
    },
    [handleFilterChange]
  )

  const places = useMemo(() => distinctPlaces(charts), [charts])
  const filtered = useMemo(() => applyFilters(charts, filters), [charts, filters])

  // True empty state — no charts at all
  if (charts.length === 0) {
    return <RosterEmptyWizard />
  }

  return (
    <div className="space-y-4">
      <RosterStatsRibbon
        total={stats.total}
        inActiveBuild={stats.inActiveBuild}
        consumedToday={stats.consumedToday}
        predictionsOverdue={stats.predictionsOverdue}
        onFilterShortcut={handleFilterShortcut}
      />

      <RosterFilters
        filters={filters}
        view={view}
        places={places}
        onFilterChange={handleFilterChange}
        onViewChange={handleViewChange}
      />

      {view === 'table' ? (
        <RosterTableView charts={filtered} />
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((chart) => (
            <ClientCard key={chart.id} chart={chart} />
          ))}
          {filtered.length === 0 && (
            <p className="col-span-full py-12 text-center text-sm text-muted-foreground">
              No charts match the current filters.
            </p>
          )}
        </div>
      )}
    </div>
  )
}
