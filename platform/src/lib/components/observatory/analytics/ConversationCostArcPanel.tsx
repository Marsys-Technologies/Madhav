'use client'

// Phase O — O.4 — Conversation Cost Arc panel.
//
// Two-pane layout:
//   Left  — table of top conversations within the date range (clickable rows
//           that select the conversation).
//   Right — line chart of cumulative_cost_usd vs. event index for the
//           currently-selected conversation, with a per-point tooltip
//           surfacing pipeline_stage / provider / event cost / cumulative.
//
// Authored by USTAD_S4_3_COST_ARC.

import { useEffect, useMemo, useState } from 'react'
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import { formatUsd } from '@/lib/components/observatory/kpi'
import type {
  ConversationArcResult,
  ConversationSummary,
  ConversationTurn,
} from '@/lib/observatory/analytics/cost_arc'

export interface ConversationCostArcPanelProps {
  /** Optional initial conversations. When provided, the panel skips its
   *  initial fetch and renders these. The Next.js page passes the SSR
   *  payload through here. */
  initialConversations?: ConversationSummary[]
  /** Date window (inclusive start / exclusive end) used by the list fetch. */
  dateStart: string
  dateEnd: string
}

interface ListResponse {
  conversations: ConversationSummary[]
  date_start: string
  date_end: string
}

function formatDuration(startIso: string, endIso: string): string {
  const startMs = Date.parse(startIso)
  const endMs = Date.parse(endIso)
  if (!Number.isFinite(startMs) || !Number.isFinite(endMs)) return '—'
  const ms = Math.max(0, endMs - startMs)
  const minutes = Math.round(ms / 60_000)
  if (minutes < 60) return `${minutes}m`
  const hours = Math.floor(minutes / 60)
  const mins = minutes % 60
  if (hours < 24) return mins === 0 ? `${hours}h` : `${hours}h ${mins}m`
  const days = Math.floor(hours / 24)
  const remHours = hours % 24
  return remHours === 0 ? `${days}d` : `${days}d ${remHours}h`
}

interface ChartRow {
  index: number
  cumulative: number
  event_cost: number
  started_at: string
  pipeline_stage: string
  provider: string
  model: string
}

function turnsToChartRows(turns: ConversationTurn[]): ChartRow[] {
  return turns.map((t, i) => ({
    index: i + 1,
    cumulative: t.cumulative_cost_usd,
    event_cost: t.computed_cost_usd,
    started_at: t.started_at,
    pipeline_stage: t.pipeline_stage,
    provider: t.provider,
    model: t.model,
  }))
}

interface ArcTooltipPayload {
  payload?: ChartRow
}

interface ArcTooltipProps {
  active?: boolean
  payload?: ArcTooltipPayload[]
}

function ArcTooltip({ active, payload }: ArcTooltipProps) {
  if (!active || !payload || payload.length === 0) return null
  const row = payload[0]?.payload
  if (!row) return null
  return (
    <div
      data-testid="cost-arc-tooltip"
      className="rounded border bg-background p-2 text-xs shadow"
    >
      <div className="font-medium">Event #{row.index}</div>
      <div className="text-muted-foreground">{row.started_at}</div>
      <div className="mt-1">
        <span className="text-muted-foreground">Stage: </span>
        <span>{row.pipeline_stage}</span>
      </div>
      <div>
        <span className="text-muted-foreground">Provider: </span>
        <span>{row.provider}</span>
      </div>
      <div>
        <span className="text-muted-foreground">Event cost: </span>
        <span className="tabular-nums">{formatUsd(row.event_cost)}</span>
      </div>
      <div>
        <span className="text-muted-foreground">Cumulative: </span>
        <span className="tabular-nums font-medium">
          {formatUsd(row.cumulative)}
        </span>
      </div>
    </div>
  )
}

export function ConversationCostArcPanel({
  initialConversations,
  dateStart,
  dateEnd,
}: ConversationCostArcPanelProps) {
  const [conversations, setConversations] = useState<ConversationSummary[]>(
    initialConversations ?? [],
  )
  const [listLoading, setListLoading] = useState<boolean>(
    initialConversations == null,
  )
  const [listError, setListError] = useState<string | null>(null)

  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [arc, setArc] = useState<ConversationArcResult | null>(null)
  const [arcLoading, setArcLoading] = useState(false)
  const [arcError, setArcError] = useState<string | null>(null)

  // Fetch the list when no initial payload is provided, or when the date
  // window changes.
  useEffect(() => {
    if (initialConversations && conversations === initialConversations) {
      // First render with SSR payload — no fetch needed.
      return
    }
    let cancelled = false
    const initialFetch = setTimeout(() => {
      setListLoading(true)
      setListError(null)
      const url = new URL(
        '/api/admin/observatory/analytics/cost-arc',
        window.location.origin,
      )
      url.searchParams.set('date_start', dateStart)
      url.searchParams.set('date_end', dateEnd)
      fetch(url.toString())
        .then(async r => {
          if (!r.ok) throw new Error(`HTTP ${r.status}`)
          return (await r.json()) as ListResponse
        })
        .then(body => {
          if (cancelled) return
          setConversations(body.conversations)
        })
        .catch(err => {
          if (cancelled) return
          setListError(err instanceof Error ? err.message : 'Failed to load')
        })
        .finally(() => {
          if (cancelled) return
          setListLoading(false)
        })
    }, 0)
    return () => {
      cancelled = true
      clearTimeout(initialFetch)
    }
    // initialConversations is intentionally not in the dep list — it only
    // gates the first render.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dateStart, dateEnd])

  // Fetch the arc whenever the selected conversation changes.
  useEffect(() => {
    if (!selectedId) return
    let cancelled = false
    const initialFetch = setTimeout(() => {
      setArcLoading(true)
      setArcError(null)
      fetch(
        `/api/admin/observatory/analytics/cost-arc/${encodeURIComponent(
          selectedId,
        )}`,
      )
        .then(async r => {
          if (!r.ok) throw new Error(`HTTP ${r.status}`)
          return (await r.json()) as ConversationArcResult
        })
        .then(body => {
          if (cancelled) return
          setArc(body)
        })
        .catch(err => {
          if (cancelled) return
          setArcError(err instanceof Error ? err.message : 'Failed to load')
        })
        .finally(() => {
          if (cancelled) return
          setArcLoading(false)
        })
    }, 0)
    return () => {
      cancelled = true
      clearTimeout(initialFetch)
    }
  }, [selectedId])

  const activeArc = selectedId ? arc : null

  const chartRows = useMemo<ChartRow[]>(
    () => (activeArc ? turnsToChartRows(activeArc.turns) : []),
    [activeArc],
  )

  return (
    <div
      data-testid="conversation-cost-arc-panel"
      className="grid grid-cols-1 gap-4 lg:grid-cols-[minmax(0,420px)_minmax(0,1fr)]"
    >
      <section
        aria-label="Top conversations"
        className="rounded border bg-card"
      >
        <header className="border-b px-3 py-2 text-sm font-medium">
          Top conversations
        </header>
        {listLoading && (
          <div
            data-testid="cost-arc-list-loading"
            role="status"
            aria-live="polite"
            className="p-4 text-xs text-muted-foreground"
          >
            Loading conversations…
          </div>
        )}
        {listError && (
          <div
            data-testid="cost-arc-list-error"
            role="alert"
            className="p-4 text-xs text-destructive"
          >
            Failed to load conversations: {listError}
          </div>
        )}
        {!listLoading && !listError && conversations.length === 0 && (
          <div
            data-testid="cost-arc-list-empty"
            className="p-4 text-xs text-muted-foreground"
          >
            No conversations in this range.
          </div>
        )}
        {!listLoading && !listError && conversations.length > 0 && (
          <div className="max-h-[600px] overflow-auto">
            <table className="w-full text-xs">
              <thead className="sticky top-0 bg-card text-left text-muted-foreground">
                <tr>
                  <th className="px-3 py-2 font-medium">Conversation</th>
                  <th className="px-3 py-2 text-right font-medium">Total</th>
                  <th className="px-3 py-2 text-right font-medium">Events</th>
                  <th className="px-3 py-2 text-right font-medium">Span</th>
                </tr>
              </thead>
              <tbody>
                {conversations.map(c => {
                  const selected = c.conversation_id === selectedId
                  return (
                    <tr
                      key={c.conversation_id}
                      data-testid={`cost-arc-row-${c.conversation_id}`}
                      data-selected={selected ? 'true' : 'false'}
                      className={
                        'cursor-pointer border-t hover:bg-muted/50 ' +
                        (selected ? 'bg-muted' : '')
                      }
                      onClick={() => setSelectedId(c.conversation_id)}
                    >
                      <td className="px-3 py-2">
                        <div className="font-medium">{c.conversation_name}</div>
                        <div className="text-[10px] text-muted-foreground">
                          {c.providers.join(', ')}
                        </div>
                      </td>
                      <td className="px-3 py-2 text-right tabular-nums">
                        {formatUsd(c.total_cost_usd)}
                      </td>
                      <td className="px-3 py-2 text-right tabular-nums">
                        {c.event_count}
                      </td>
                      <td className="px-3 py-2 text-right tabular-nums">
                        {formatDuration(c.first_event_at, c.last_event_at)}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section
        aria-label="Cost arc"
        className="rounded border bg-card"
      >
        <header className="flex items-center justify-between border-b px-3 py-2 text-sm">
          <span className="font-medium">
            {activeArc ? activeArc.conversation_name : 'Cost arc'}
          </span>
          {activeArc && (
            <span className="tabular-nums text-muted-foreground">
              Total: {formatUsd(activeArc.total_cost_usd)}
            </span>
          )}
        </header>
        <div className="p-3">
          {!selectedId && (
            <div
              data-testid="cost-arc-empty"
              className="flex h-72 items-center justify-center text-sm text-muted-foreground"
            >
              Select a conversation to see its cost arc
            </div>
          )}
          {selectedId && arcLoading && (
            <div
              data-testid="cost-arc-loading"
              role="status"
              aria-live="polite"
              className="flex h-72 animate-pulse items-center justify-center rounded bg-muted text-sm text-muted-foreground"
            >
              Loading arc…
            </div>
          )}
          {selectedId && arcError && (
            <div
              data-testid="cost-arc-error"
              role="alert"
              className="flex h-72 items-center justify-center text-sm text-destructive"
            >
              Failed to load arc: {arcError}
            </div>
          )}
          {selectedId && !arcLoading && !arcError && activeArc && (
            <div data-testid="cost-arc-chart" className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartRows}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="index"
                    tick={{ fontSize: 11 }}
                    label={{
                      value: 'Event #',
                      position: 'insideBottom',
                      offset: -4,
                      style: { fontSize: 11 },
                    }}
                  />
                  <YAxis
                    tickFormatter={(v: number) => formatUsd(v)}
                    tick={{ fontSize: 11 }}
                    width={84}
                  />
                  <Tooltip content={<ArcTooltip />} />
                  <Line
                    type="monotone"
                    dataKey="cumulative"
                    name="Cumulative cost"
                    stroke="#6366f1"
                    strokeWidth={2}
                    dot={{ r: 3 }}
                    activeDot={{ r: 5 }}
                    isAnimationActive={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      </section>
    </div>
  )
}
