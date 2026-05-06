'use client'

import * as React from 'react'
import { LayoutGrid, ChevronRight, Filter } from 'lucide-react'
import { EventTable } from '../events/EventTable'
import { EventSidePanel } from '../events/EventSidePanel'
import { QueryGroupCard, type GroupedRow } from '../events/QueryGroupCard'
import type { EventRow } from '../events/types'
import { FiltersBar } from '../filters/FiltersBar'
import { useObservatoryFilters } from '../filters/useObservatoryFilters'
import { ExportPanel } from '../export/ExportPanel'
import {
  dateOnlyToFromIso,
  dateOnlyToToIso,
} from './filterAdapter'
import type { EventsParams } from '@/lib/api-clients/observatory'
import { cn } from '@/lib/utils'
import { ObsPageShell, ObsCard, SectionLabel } from '../shared'

const PAGE_LIMIT = 50

export function EventsClient(): React.ReactElement {
  const { filters, setFilters } = useObservatoryFilters()
  const [selectedEventId, setSelectedEventId] = React.useState<string | null>(null)
  const [groupByQuery, setGroupByQuery] = React.useState(false)
  const [groupedRows, setGroupedRows] = React.useState<GroupedRow[]>([])
  const [groupedLoading, setGroupedLoading] = React.useState(false)

  const fetchParams: EventsParams = React.useMemo(
    () => ({
      from: dateOnlyToFromIso(filters.date_range.from),
      to: dateOnlyToToIso(filters.date_range.to),
      provider: filters.providers.length > 0 ? filters.providers : undefined,
      model: filters.models.length > 0 ? filters.models : undefined,
      pipeline_stage:
        filters.pipeline_stages.length > 0 ? filters.pipeline_stages : undefined,
      status: filters.statuses[0],
      search: filters.search || undefined,
      limit: PAGE_LIMIT,
    }),
    [filters],
  )

  React.useEffect(() => {
    if (!groupByQuery) return
    setGroupedLoading(true)
    const params = new URLSearchParams({ from: fetchParams.from, to: fetchParams.to, groupByQuery: 'true' })
    fetch(`/api/admin/observatory/events?${params.toString()}`)
      .then((r) => r.json())
      .then((data: { type: string; rows: GroupedRow[] }) => {
        if (data.type === 'grouped') setGroupedRows(data.rows)
      })
      .catch(() => setGroupedRows([]))
      .finally(() => setGroupedLoading(false))
  }, [groupByQuery, fetchParams.from, fetchParams.to])

  const tableKey = React.useMemo(
    () =>
      JSON.stringify([
        fetchParams.from,
        fetchParams.to,
        fetchParams.provider,
        fetchParams.model,
        fetchParams.pipeline_stage,
        fetchParams.status,
        fetchParams.search,
      ]),
    [fetchParams],
  )

  const handleRowClick = React.useCallback((row: EventRow) => {
    setSelectedEventId(row.event_id)
  }, [])

  const headerRight = (
    <button
      type="button"
      onClick={() => setGroupByQuery(g => !g)}
      role="switch"
      aria-checked={groupByQuery}
      className={cn(
        'obs-glass inline-flex items-center gap-2 rounded-full px-3 py-1.5 text-[11px] font-medium transition-colors',
        groupByQuery
          ? 'text-[var(--brand-gold)] shadow-[inset_0_0_0_1px_color-mix(in_oklch,var(--brand-gold)_30%,transparent)]'
          : 'text-[rgba(212,175,55,0.50)] hover:text-[var(--brand-gold)]',
      )}
    >
      <LayoutGrid size={12} aria-hidden />
      {groupByQuery ? 'Grouped' : 'Group by query'}
    </button>
  )

  const headerBottom = (
    <details className="group">
      <summary className="inline-flex cursor-pointer items-center gap-1.5 bt-label bt-label-upper text-[rgba(212,175,55,0.45)] hover:text-[var(--brand-gold)] list-none select-none">
        <Filter size={11} aria-hidden className="opacity-70" />
        <span className="transition-transform group-open:rotate-90">
          <ChevronRight size={11} aria-hidden />
        </span>
        Advanced filters
      </summary>
      <div className="mt-3">
        <FiltersBar filters={filters} modelOptions={[]} onFiltersChange={setFilters} />
      </div>
    </details>
  )

  return (
    <ObsPageShell
      title="LLM Events"
      subtitle="Per-call telemetry across all provider stacks"
      testId="observatory-events"
      headerRight={headerRight}
      headerBottom={headerBottom}
    >
      {/* Export panel — collapsed by default, lives inside the shell */}
      <ExportPanel />

      {/* Content */}
      <section>
        <SectionLabel>{groupByQuery ? 'Queries' : 'Events'}</SectionLabel>
        <ObsCard padding="none" className="overflow-hidden">
          {groupByQuery ? (
            groupedLoading ? (
              <p className="p-4 text-xs text-[rgba(212,175,55,0.45)]">Loading grouped data…</p>
            ) : groupedRows.length === 0 ? (
              <div className="flex flex-col items-center justify-center gap-3 py-16 text-center">
                <span className="text-3xl text-[var(--brand-gold)] opacity-40">◎</span>
                <p className="text-sm font-medium text-[rgba(212,175,55,0.50)]">
                  No grouped data in range
                </p>
              </div>
            ) : (
              <div className="flex flex-col gap-2 p-3">
                {groupedRows.map((row, i) => (
                  <QueryGroupCard key={row.conversation_id ?? i} row={row} />
                ))}
              </div>
            )
          ) : (
            <EventTable
              key={tableKey}
              fetchParams={fetchParams}
              onRowClick={handleRowClick}
              selectedEventId={selectedEventId}
            />
          )}
        </ObsCard>
      </section>

      <EventSidePanel
        eventId={selectedEventId}
        dateRange={{ from: fetchParams.from, to: fetchParams.to }}
        onClose={() => setSelectedEventId(null)}
        onSelectEvent={(id) => setSelectedEventId(id)}
      />
    </ObsPageShell>
  )
}
