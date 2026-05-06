'use client'

import * as React from 'react'
import { getEvents, type EventsParams } from '@/lib/api-clients/observatory'
import {
  ALL_EVENT_COLUMNS,
  COLUMN_LABELS,
  DEFAULT_VISIBLE_COLUMNS,
  type EventColumnId,
  type EventRow,
  type SortableColumnId,
  type SortState,
} from './types'
import { getCellValue } from './format'
import { StatusBadge } from './StatusBadge'
import { VirtualList } from './VirtualList'
import { useColumnVisibility } from './useColumnVisibility'
import { colorForProvider } from '../charts/utils'
import { cn } from '@/lib/utils'

const ROW_HEIGHT = 40
const SORTABLE: ReadonlySet<EventColumnId> = new Set([
  'timestamp',
  'cost_usd',
  'latency_ms',
])

interface EventTableProps {
  fetchParams: EventsParams
  onRowClick?: (event: EventRow) => void
  selectedEventId?: string | null
  fetcher?: typeof getEvents
  rowHeight?: number
  viewportHeight?: number
  initialData?: {
    events: EventRow[]
    next_cursor: string | null
    total_count: number
  }
}

export function EventTable({
  fetchParams,
  onRowClick,
  selectedEventId,
  fetcher = getEvents,
  rowHeight = ROW_HEIGHT,
  viewportHeight = 480,
  initialData,
}: EventTableProps): React.ReactElement {
  const [rows, setRows] = React.useState<EventRow[]>(initialData?.events ?? [])
  const [cursor, setCursor] = React.useState<string | null>(
    initialData?.next_cursor ?? null,
  )
  const [totalCount, setTotalCount] = React.useState<number>(
    initialData?.total_count ?? 0,
  )
  const [loading, setLoading] = React.useState(false)
  const [error, setError] = React.useState<string | null>(null)
  const [sort, setSort] = React.useState<SortState>({
    column: 'timestamp',
    direction: 'desc',
  })
  const [showColumnPanel, setShowColumnPanel] = React.useState(false)
  const { visible, isVisible, toggle, reset } = useColumnVisibility()

  const visibleColumns = React.useMemo<EventColumnId[]>(
    () => ALL_EVENT_COLUMNS.filter((c) => visible.includes(c)),
    [visible],
  )

  const loadPage = React.useCallback(
    async (nextCursor: string | null) => {
      setLoading(true)
      setError(null)
      try {
        const res = await fetcher({ ...fetchParams, cursor: nextCursor ?? undefined })
        setRows((prev) =>
          nextCursor === null ? res.events : [...prev, ...res.events],
        )
        setCursor(res.next_cursor)
        setTotalCount(res.total_count)
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to load events')
      } finally {
        setLoading(false)
      }
    },
    [fetcher, fetchParams],
  )

  React.useEffect(() => {
    if (initialData) return
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void loadPage(null)
  }, [initialData, loadPage])

  const sortedRows = React.useMemo(() => {
    const copy = [...rows]
    copy.sort((a, b) => {
      const dir = sort.direction === 'asc' ? 1 : -1
      switch (sort.column) {
        case 'timestamp':
          return dir * a.started_at.localeCompare(b.started_at)
        case 'cost_usd':
          return (
            dir *
            ((a.computed_cost_usd ?? 0) - (b.computed_cost_usd ?? 0))
          )
        case 'latency_ms':
          return dir * ((a.latency_ms ?? 0) - (b.latency_ms ?? 0))
      }
    })
    return copy
  }, [rows, sort])

  const handleSort = (col: EventColumnId) => {
    if (!SORTABLE.has(col)) return
    const c = col as SortableColumnId
    setSort((prev) =>
      prev.column === c
        ? { column: c, direction: prev.direction === 'asc' ? 'desc' : 'asc' }
        : { column: c, direction: 'desc' },
    )
  }

  const renderCell = (row: EventRow, col: EventColumnId): React.ReactNode => {
    if (col === 'status') return <StatusBadge status={row.status} />

    if (col === 'provider') {
      return (
        <span className="flex items-center gap-1.5">
          <span
            aria-hidden="true"
            className="inline-block h-2 w-2 shrink-0 rounded-full"
            style={{ backgroundColor: colorForProvider(row.provider) }}
          />
          <span className="truncate text-xs text-[rgba(212,175,55,0.60)]">
            {row.provider}
          </span>
        </span>
      )
    }

    if (col === 'cost_usd') {
      const cost = row.computed_cost_usd
      return (
        <span
          className={cn(
            'tabular-nums text-xs font-medium',
            cost != null && cost > 0.01
              ? 'text-amber-400'
              : 'text-[#fce29a]',
          )}
        >
          {getCellValue(row, col)}
        </span>
      )
    }

    if (col === 'latency_ms') {
      return (
        <span
          className={cn(
            'tabular-nums text-xs',
            row.latency_ms != null && row.latency_ms > 5000
              ? 'text-red-400'
              : 'text-[rgba(212,175,55,0.55)]',
          )}
        >
          {getCellValue(row, col)}
        </span>
      )
    }

    return (
      <span className="truncate" title={getCellValue(row, col)}>
        {getCellValue(row, col)}
      </span>
    )
  }

  return (
    <div data-testid="event-table" className="flex flex-col">
      {/* Top bar */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-[color-mix(in_oklch,var(--brand-gold)_8%,transparent)]">
        <span
          data-testid="event-table-count"
          className="bt-label bt-label-upper text-[rgba(212,175,55,0.55)] tabular-nums"
        >
          Showing <span className="text-[var(--brand-gold-cream)]">{rows.length}</span>
          {' of '}
          <span className="text-[var(--brand-gold-cream)]">{totalCount}</span>
        </span>
        <button
          type="button"
          data-testid="event-table-columns-toggle"
          onClick={() => setShowColumnPanel((s) => !s)}
          className={cn(
            'rounded-full px-3 py-1.5 text-[11px] font-medium transition-colors',
            showColumnPanel
              ? 'bg-[color-mix(in_oklch,var(--brand-gold)_16%,transparent)] text-[var(--brand-gold)] shadow-[inset_0_0_0_1px_color-mix(in_oklch,var(--brand-gold)_28%,transparent)]'
              : 'text-[rgba(212,175,55,0.55)] hover:bg-[color-mix(in_oklch,var(--brand-gold)_8%,transparent)] hover:text-[var(--brand-gold)]',
          )}
        >
          Columns
        </button>
      </div>

      {/* Column visibility panel */}
      {showColumnPanel ? (
        <div
          data-testid="event-table-columns-panel"
          className="mx-4 mb-3 rounded-xl border border-[rgba(212,175,55,0.12)] bg-[oklch(0.11_0.010_70)] p-4 shadow-xl"
        >
          <div className="mb-2 flex items-center justify-between">
            <span className="text-xs font-medium text-[rgba(212,175,55,0.65)]">
              Visible columns
            </span>
            <button
              type="button"
              data-testid="event-table-columns-reset"
              onClick={reset}
              className="rounded border border-[rgba(212,175,55,0.20)] px-2 py-1 text-[10px] text-[rgba(212,175,55,0.50)] hover:text-[#d4af37]"
            >
              Reset columns
            </button>
          </div>
          <ul className="grid grid-cols-2 gap-1">
            {ALL_EVENT_COLUMNS.map((col) => (
              <li key={col}>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    data-testid={`event-table-column-checkbox-${col}`}
                    checked={isVisible(col)}
                    onChange={() => toggle(col)}
                    className="accent-[#d4af37]"
                  />
                  <span className="text-xs text-[rgba(212,175,55,0.65)]">
                    {COLUMN_LABELS[col]}
                  </span>
                </label>
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {/* Column header row */}
      <div
        data-testid="event-table-header"
        className="grid grid-flow-col items-center gap-2 border-b border-[rgba(212,175,55,0.10)] px-4 py-2 text-[10px] font-semibold uppercase tracking-widest text-[rgba(212,175,55,0.35)]"
        style={{
          gridTemplateColumns: `repeat(${visibleColumns.length}, minmax(0, 1fr))`,
        }}
      >
        {visibleColumns.map((col) => {
          const sortable = SORTABLE.has(col)
          const isSorted = sort.column === col
          return (
            <button
              key={col}
              type="button"
              data-testid={`event-table-header-${col}`}
              data-sorted={isSorted ? sort.direction : 'none'}
              disabled={!sortable}
              onClick={() => handleSort(col)}
              className={cn(
                'flex items-center gap-1 text-left',
                sortable
                  ? 'cursor-pointer hover:text-[rgba(212,175,55,0.65)]'
                  : 'cursor-default',
              )}
            >
              <span>{COLUMN_LABELS[col]}</span>
              {sortable && isSorted ? (
                <span aria-hidden>{sort.direction === 'asc' ? '↑' : '↓'}</span>
              ) : null}
            </button>
          )
        })}
      </div>

      {/* Loading skeleton — initial load only */}
      {loading && rows.length === 0 ? (
        <div className="flex flex-col gap-1 px-4 py-2">
          {[0, 1, 2].map((i) => (
            <div
              key={i}
              className="h-10 animate-pulse rounded bg-[rgba(212,175,55,0.04)]"
            />
          ))}
        </div>
      ) : !loading && rows.length === 0 && !error ? (
        /* Empty state */
        <div className="flex flex-col items-center justify-center gap-3 py-16 text-center">
          <span className="text-3xl opacity-30">◎</span>
          <p className="text-sm font-medium text-[rgba(212,175,55,0.50)]">
            No events in this range
          </p>
          <p className="text-xs text-[rgba(212,175,55,0.30)]">
            Try adjusting the date filter or provider selection
          </p>
        </div>
      ) : error ? (
        /* Error state */
        <div className="mx-4 my-2 flex flex-col items-center gap-3 rounded-xl border border-red-500/20 bg-red-500/5 py-8 text-center">
          <p
            data-testid="event-table-error"
            className="text-sm text-red-400"
          >
            {error}
          </p>
          <button
            onClick={() => void loadPage(null)}
            className="rounded border border-red-500/30 px-3 py-1 text-xs text-red-400 hover:bg-red-500/10"
          >
            Retry
          </button>
        </div>
      ) : (
        /* Data rows */
        <VirtualList
          items={sortedRows}
          rowHeight={rowHeight}
          viewportHeight={viewportHeight}
          testId="event-table-virtual"
          renderRow={(row) => (
            <button
              type="button"
              data-testid={`event-row-${row.event_id}`}
              data-event-id={row.event_id}
              onClick={() => onRowClick?.(row)}
              className={cn(
                'grid w-full grid-flow-col items-center gap-2 border-b border-[color-mix(in_oklch,var(--brand-gold)_5%,transparent)] px-4 text-left text-xs transition-all',
                'hover:bg-[color-mix(in_oklch,var(--brand-gold)_5%,transparent)]',
                selectedEventId === row.event_id &&
                  'bg-[color-mix(in_oklch,var(--brand-gold)_10%,transparent)] shadow-[inset_3px_0_0_0_var(--brand-gold),inset_0_0_24px_color-mix(in_oklch,var(--brand-gold)_8%,transparent)]',
              )}
              style={{
                gridTemplateColumns: `repeat(${visibleColumns.length}, minmax(0, 1fr))`,
                height: rowHeight,
              }}
            >
              {visibleColumns.map((col) => (
                <div key={col} className="overflow-hidden">
                  {renderCell(row, col)}
                </div>
              ))}
            </button>
          )}
        />
      )}

      {/* Load more footer */}
      <div className="flex items-center justify-end px-4 py-2">
        <button
          type="button"
          data-testid="event-table-load-more"
          disabled={loading || cursor === null || !!error}
          onClick={() => void loadPage(cursor)}
          className="rounded-lg border border-[rgba(212,175,55,0.20)] bg-[rgba(212,175,55,0.06)] px-3 py-1.5 text-xs font-medium text-[rgba(212,175,55,0.70)] transition-colors hover:border-[rgba(212,175,55,0.35)] hover:text-[#d4af37] disabled:opacity-40"
        >
          {loading ? 'Loading…' : cursor === null ? 'All loaded' : 'Load more'}
        </button>
      </div>
    </div>
  )
}

// Re-export defaults so tests can rely on a stable surface.
export { DEFAULT_VISIBLE_COLUMNS, ALL_EVENT_COLUMNS }
