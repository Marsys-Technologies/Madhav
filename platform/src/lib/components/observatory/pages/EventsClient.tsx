'use client'

import * as React from 'react'
import { EventTable } from '../events/EventTable'
import { EventSidePanel } from '../events/EventSidePanel'
import { QueryGroupCard, type GroupedRow } from '../events/QueryGroupCard'
import type { EventRow } from '../events/types'
import { FiltersBar } from '../filters/FiltersBar'
import { useObservatoryFilters } from '../filters/useObservatoryFilters'
import {
  dateOnlyToFromIso,
  dateOnlyToToIso,
} from './filterAdapter'
import type { EventsParams } from '@/lib/api-clients/observatory'
import { cn } from '@/lib/utils'
import { ObsPageShell, SectionLabel } from '../shared'

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

  // Re-key the EventTable on filter change so it remounts and refetches from
  // page 1 (the table holds its own paging state internally).
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

  return (
    <ObsPageShell
      title="LLM Events"
      subtitle="Per-call telemetry across all provider stacks"
      testId="observatory-events"
      headerRight={
        <button
          type="button"
          onClick={() => setGroupByQuery(g => !g)}
          className={cn(
            'rounded-lg border px-3 py-1.5 text-xs font-medium transition-colors',
            groupByQuery
              ? 'border-[rgba(212,175,55,0.4)] bg-[rgba(212,175,55,0.12)] text-[#d4af37]'
              : 'border-[rgba(212,175,55,0.12)] text-[rgba(212,175,55,0.45)] hover:text-[#d4af37]',
          )}
        >
          {groupByQuery ? '⊞ Grouped view' : '⊞ Group by query'}
        </button>
      }
    >
      {/* Advanced filters collapsible */}
      <details className="group">
        <summary className="inline-flex cursor-pointer items-center gap-1.5 text-[11px] font-medium text-[rgba(212,175,55,0.35)] hover:text-[rgba(212,175,55,0.65)] list-none select-none">
          <span aria-hidden="true" className="transition-transform group-open:rotate-90">▶</span>
          Advanced filters
        </summary>
        <div className="mt-3">
          <FiltersBar filters={filters} modelOptions={[]} onFiltersChange={setFilters} />
        </div>
      </details>

      {/* Content */}
      <section>
        <SectionLabel>{groupByQuery ? 'Queries' : 'Events'}</SectionLabel>
        <div className="rounded-xl border border-[rgba(212,175,55,0.10)] bg-[oklch(0.11_0.010_70)]">
          {groupByQuery ? (
            groupedLoading ? (
              <p className="p-4 text-xs text-[rgba(212,175,55,0.45)]">Loading grouped data…</p>
            ) : groupedRows.length === 0 ? (
              <div className="flex flex-col items-center justify-center gap-3 py-16 text-center">
                <span className="text-3xl opacity-30">◎</span>
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
        </div>
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
