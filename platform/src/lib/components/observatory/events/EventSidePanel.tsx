'use client'

import * as React from 'react'
import {
  getEvent,
  getEvents,
  type EventsParams,
} from '@/lib/api-clients/observatory'
import type { EventDetail, EventRow } from './types'
import { StatusBadge } from './StatusBadge'
import { formatCostUsd, formatTimestamp } from './format'
import { colorForStage } from '../charts/utils'
import { cn } from '@/lib/utils'

type TabId = 'prompt' | 'response' | 'meta'

const TABS: { id: TabId; label: string }[] = [
  { id: 'prompt', label: 'Prompt' },
  { id: 'response', label: 'Response' },
  { id: 'meta', label: 'Meta' },
]

interface EventSidePanelProps {
  eventId: string | null
  dateRange: { from: string; to: string }
  onClose: () => void
  onSelectEvent?: (id: string) => void
  fetchEvent?: typeof getEvent
  fetchEvents?: typeof getEvents
}

export function EventSidePanel({
  eventId,
  dateRange,
  onClose,
  onSelectEvent,
  fetchEvent = getEvent,
  fetchEvents = getEvents,
}: EventSidePanelProps): React.ReactElement | null {
  const [event, setEvent] = React.useState<EventDetail | null>(null)
  const [siblings, setSiblings] = React.useState<EventRow[]>([])
  const [tab, setTab] = React.useState<TabId>('prompt')
  const [loading, setLoading] = React.useState(false)
  const [error, setError] = React.useState<string | null>(null)
  const [collapsed, setCollapsed] = React.useState<{
    system_prompt: boolean
    parameters: boolean
  }>({ system_prompt: true, parameters: true })

  React.useEffect(() => {
    if (!eventId) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setEvent(null)
      setSiblings([])
      return
    }
    let cancelled = false
    setLoading(true)
    setError(null)
    setTab('prompt')
    void (async () => {
      try {
        const detail = await fetchEvent(eventId)
        if (cancelled) return
        setEvent(detail)
        const params: EventsParams = {
          from: dateRange.from,
          to: dateRange.to,
          conversation_id: detail.conversation_id,
          limit: 50,
        }
        const sibsResp = await fetchEvents(params)
        if (cancelled) return
        const ordered = [...sibsResp.events].sort((a, b) =>
          a.started_at.localeCompare(b.started_at),
        )
        setSiblings(ordered)
      } catch (e) {
        if (cancelled) return
        setError(e instanceof Error ? e.message : 'Failed to load event')
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [eventId, dateRange.from, dateRange.to, fetchEvent, fetchEvents])

  if (!eventId) return null

  return (
    <aside
      data-testid="event-side-panel"
      role="dialog"
      aria-label="Event details"
      className="fixed inset-y-0 right-0 z-40 flex w-[480px] max-w-full flex-col border-l border-[rgba(212,175,55,0.12)] bg-[oklch(0.10_0.012_70)] shadow-2xl"
    >
      {/* Header */}
      <header className="flex items-center justify-between border-b border-[rgba(212,175,55,0.10)] px-6 py-4">
        <div className="flex flex-col gap-0.5">
          <span className="text-[10px] font-medium uppercase tracking-widest text-[rgba(212,175,55,0.35)]">
            Event
          </span>
          <span
            data-testid="event-side-panel-id"
            className="font-mono text-sm text-[#fce29a]"
          >
            {eventId}
          </span>
        </div>
        <button
          type="button"
          data-testid="event-side-panel-close"
          onClick={onClose}
          aria-label="Close panel"
          className="rounded p-1 text-[rgba(212,175,55,0.40)] transition-colors hover:bg-[rgba(212,175,55,0.08)] hover:text-[#d4af37]"
        >
          ✕
        </button>
      </header>

      {/* Tabs */}
      <nav
        data-testid="event-side-panel-tabs"
        role="tablist"
        className="flex border-b border-[rgba(212,175,55,0.10)] text-sm"
      >
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            role="tab"
            aria-selected={tab === t.id}
            data-testid={`event-side-panel-tab-${t.id}`}
            onClick={() => setTab(t.id)}
            className={cn(
              'flex-1 px-4 py-2.5 text-xs font-medium transition-colors',
              tab === t.id
                ? 'border-b-2 border-[#d4af37] text-[#fce29a]'
                : 'text-[rgba(212,175,55,0.40)] hover:text-[rgba(212,175,55,0.70)]',
            )}
          >
            {t.label}
          </button>
        ))}
      </nav>

      {/* Body */}
      <div
        data-testid="event-side-panel-body"
        className="flex-1 overflow-y-auto px-6 py-4 text-sm"
      >
        {loading ? (
          <div
            data-testid="event-side-panel-loading"
            className="flex flex-col gap-2 pt-4"
          >
            {[0, 1, 2, 3].map((i) => (
              <div
                key={i}
                className="h-8 animate-pulse rounded bg-[rgba(212,175,55,0.04)]"
              />
            ))}
          </div>
        ) : error ? (
          <div
            data-testid="event-side-panel-error"
            className="flex flex-col items-center gap-3 rounded-xl border border-red-500/20 bg-red-500/5 py-8 text-center"
          >
            <p className="text-sm text-red-400">{error}</p>
          </div>
        ) : !event ? null : tab === 'prompt' ? (
          <PromptTab
            event={event}
            collapsed={collapsed}
            onToggle={(k) => setCollapsed((c) => ({ ...c, [k]: !c[k] }))}
          />
        ) : tab === 'response' ? (
          <ResponseTab event={event} />
        ) : (
          <MetaTab event={event} />
        )}
      </div>

      <ConversationThread
        siblings={siblings}
        currentId={eventId}
        onSelect={onSelectEvent}
      />
    </aside>
  )
}

function PromptTab({
  event,
  collapsed,
  onToggle,
}: {
  event: EventDetail
  collapsed: { system_prompt: boolean; parameters: boolean }
  onToggle: (k: 'system_prompt' | 'parameters') => void
}): React.ReactElement {
  return (
    <div className="flex flex-col gap-4" data-testid="event-side-panel-prompt">
      <section>
        <div className="mb-1.5 text-[10px] font-medium uppercase tracking-widest text-[rgba(212,175,55,0.35)]">
          Prompt text
        </div>
        <pre
          data-testid="event-prompt-text"
          className="overflow-x-auto rounded-lg border border-[rgba(212,175,55,0.10)] bg-[rgba(212,175,55,0.04)] p-3 text-xs text-[rgba(212,175,55,0.75)]"
        >
          {event.prompt_text ?? '(no prompt text captured)'}
        </pre>
      </section>

      <Collapsible
        title="System prompt"
        testIdPrefix="event-system-prompt"
        collapsed={collapsed.system_prompt}
        onToggle={() => onToggle('system_prompt')}
      >
        <pre className="overflow-x-auto rounded-lg border border-[rgba(212,175,55,0.10)] bg-[rgba(212,175,55,0.04)] p-3 text-xs text-[rgba(212,175,55,0.75)]">
          {event.system_prompt ?? '(none)'}
        </pre>
      </Collapsible>

      <Collapsible
        title="Parameters"
        testIdPrefix="event-parameters"
        collapsed={collapsed.parameters}
        onToggle={() => onToggle('parameters')}
      >
        <pre className="overflow-x-auto rounded-lg border border-[rgba(212,175,55,0.10)] bg-[rgba(212,175,55,0.04)] p-3 text-xs text-[rgba(212,175,55,0.75)]">
          {formatJson(event.parameters)}
        </pre>
      </Collapsible>
    </div>
  )
}

function ResponseTab({ event }: { event: EventDetail }): React.ReactElement {
  return (
    <div className="flex flex-col gap-4" data-testid="event-side-panel-response">
      <div className="flex items-center gap-2">
        <StatusBadge status={event.status} />
        {event.error_code ? (
          <span
            data-testid="event-error-code"
            className="text-xs text-red-400"
          >
            {event.error_code}
          </span>
        ) : null}
      </div>
      <section>
        <div className="mb-1.5 text-[10px] font-medium uppercase tracking-widest text-[rgba(212,175,55,0.35)]">
          Response text
        </div>
        <pre
          data-testid="event-response-text"
          className="overflow-x-auto rounded-lg border border-[rgba(212,175,55,0.10)] bg-[rgba(212,175,55,0.04)] p-3 text-xs text-[rgba(212,175,55,0.75)]"
        >
          {event.response_text ?? '(no response text captured)'}
        </pre>
      </section>
    </div>
  )
}

function MetaTab({ event }: { event: EventDetail }): React.ReactElement {
  return (
    <dl className="flex flex-col text-xs" data-testid="event-side-panel-meta">
      <KV label="provider" value={event.provider} />
      <KV label="model" value={event.model} />
      <KV label="pipeline_stage">
        <span
          className="rounded px-1.5 py-0.5 text-[9px] font-medium uppercase tracking-wide"
          style={{
            backgroundColor: `${colorForStage(event.pipeline_stage)}22`,
            color: colorForStage(event.pipeline_stage),
            border: `1px solid ${colorForStage(event.pipeline_stage)}44`,
          }}
        >
          {event.pipeline_stage}
        </span>
      </KV>
      <KV label="provider_request_id" value={event.provider_request_id ?? '—'} />
      <KV label="started_at" value={formatTimestamp(event.started_at)} />
      <KV label="finished_at" value={formatTimestamp(event.finished_at)} />
      <KV label="latency_ms" value={String(event.latency_ms ?? '—')} />
      <KV label="cost_usd" value={formatCostUsd(event.computed_cost_usd)} />
      <KV label="pricing_version_id" value={event.pricing_version_id ?? '—'} />
      <section className="py-2">
        <div className="mb-1.5 text-[10px] font-medium uppercase tracking-widest text-[rgba(212,175,55,0.35)]">
          feature_flag_state
        </div>
        <pre
          data-testid="event-feature-flag-state"
          className="overflow-x-auto rounded-lg border border-[rgba(212,175,55,0.10)] bg-[rgba(212,175,55,0.04)] p-3 text-xs text-[rgba(212,175,55,0.75)]"
        >
          {formatJson(event.feature_flag_state)}
        </pre>
      </section>
      <p
        data-testid="event-raw-payload-note"
        className="rounded-lg border border-dashed border-[rgba(212,175,55,0.15)] p-2 text-[rgba(212,175,55,0.35)]"
      >
        Raw provider payload not captured for this event (super-admin note: capture
        can be enabled in a future release).
      </p>
    </dl>
  )
}

function ConversationThread({
  siblings,
  currentId,
  onSelect,
}: {
  siblings: EventRow[]
  currentId: string
  onSelect?: (id: string) => void
}): React.ReactElement {
  return (
    <footer
      data-testid="event-side-panel-thread"
      className="border-t border-[rgba(212,175,55,0.10)] bg-[rgba(212,175,55,0.03)] px-6 py-3"
    >
      <div className="mb-2 text-[10px] font-medium uppercase tracking-widest text-[rgba(212,175,55,0.35)]">
        Conversation thread ({siblings.length})
      </div>
      <ul className="flex max-h-48 flex-col gap-1 overflow-y-auto">
        {siblings.map((s) => {
          const active = s.event_id === currentId
          return (
            <li key={s.event_id}>
              <button
                type="button"
                data-testid={`event-thread-sibling-${s.event_id}`}
                aria-current={active ? 'true' : undefined}
                disabled={!onSelect || active}
                onClick={() => onSelect?.(s.event_id)}
                className={cn(
                  'flex w-full items-center justify-between gap-2 rounded-lg border px-3 py-1.5 text-left text-xs transition-colors',
                  active
                    ? 'border-[rgba(212,175,55,0.30)] bg-[rgba(212,175,55,0.08)] font-medium text-[#d4af37]'
                    : 'border-[rgba(212,175,55,0.10)] text-[rgba(212,175,55,0.55)] hover:border-[rgba(212,175,55,0.25)] hover:text-[#d4af37]',
                )}
              >
                <span className="truncate font-mono">
                  {s.provider}/{s.model}
                </span>
                <span className="flex shrink-0 items-center gap-2 tabular-nums text-[rgba(212,175,55,0.40)]">
                  <span>{formatCostUsd(s.computed_cost_usd)}</span>
                  <span>{s.latency_ms ?? '—'}ms</span>
                </span>
              </button>
            </li>
          )
        })}
      </ul>
    </footer>
  )
}

function Collapsible({
  title,
  testIdPrefix,
  collapsed,
  onToggle,
  children,
}: {
  title: string
  testIdPrefix: string
  collapsed: boolean
  onToggle: () => void
  children: React.ReactNode
}): React.ReactElement {
  return (
    <section>
      <button
        type="button"
        data-testid={`${testIdPrefix}-toggle`}
        onClick={onToggle}
        className="flex items-center gap-1.5 text-[10px] font-medium uppercase tracking-widest text-[rgba(212,175,55,0.35)] hover:text-[rgba(212,175,55,0.65)]"
      >
        <span aria-hidden className="transition-transform" style={{ display: 'inline-block', transform: collapsed ? 'rotate(0deg)' : 'rotate(90deg)' }}>
          ▶
        </span>
        <span>{title}</span>
      </button>
      {collapsed ? null : (
        <div data-testid={`${testIdPrefix}-body`} className="mt-2">
          {children}
        </div>
      )}
    </section>
  )
}

function KV({
  label,
  value,
  children,
}: {
  label: string
  value?: string
  children?: React.ReactNode
}): React.ReactElement {
  return (
    <div className="flex items-baseline justify-between border-b border-[rgba(212,175,55,0.06)] py-2">
      <dt className="text-[10px] font-medium uppercase tracking-widest text-[rgba(212,175,55,0.35)]">
        {label}
      </dt>
      <dd className="ml-4 tabular-nums text-xs text-[rgba(212,175,55,0.80)]">
        {children ?? value}
      </dd>
    </div>
  )
}

function formatJson(value: unknown): string {
  if (value === null || value === undefined) return '(none)'
  try {
    return JSON.stringify(value, null, 2)
  } catch {
    return String(value)
  }
}
