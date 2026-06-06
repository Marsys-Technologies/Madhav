'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import { useActiveRun, type ActiveRunAsset } from '@/hooks/useActiveRun'
import { useCockpitSSE, type CockpitEvent } from '@/hooks/useCockpitSSE'
import { formatDateTime, formatRelative } from '@/lib/utils/date'

interface Props {
  chartId: string
}

const STATE_COLOR: Record<string, string> = {
  queued:    'var(--on-dark-faint)',
  building:  '#60a5fa',
  complete:  'var(--marsys-success, #4caf50)',
  error:     'var(--marsys-error, #e05252)',
  skipped:   'var(--on-dark-mut)',
}

const EVENT_COLOR: Record<string, string> = {
  'asset.state_change': '#ECC56A',
  'asset.progress':     '#6B9FD4',
  'run.state_change':   '#9B7FD4',
  'edge.first_signal':  '#5BAF7A',
}

interface LogEntry {
  id: number
  time: string
  type: string
  label: string
}

let logCounter = 0

function PlanTimeline({ assets, currentAssetId }: { assets: ActiveRunAsset[]; currentAssetId: string | null }) {
  if (assets.length === 0) {
    return <div style={{ color: 'var(--on-dark-faint)', fontSize: '13px' }}>No plan assets yet.</div>
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
      {assets.map(ra => {
        const isBuilding = ra.state === 'building' || ra.asset_id === currentAssetId
        const stateColor = STATE_COLOR[ra.state] ?? STATE_COLOR.queued
        const elapsedMs = ra.started_at
          ? (ra.ended_at ? new Date(ra.ended_at).getTime() : Date.now()) - new Date(ra.started_at).getTime()
          : null
        const elapsedStr = elapsedMs != null
          ? elapsedMs < 60_000 ? `${Math.round(elapsedMs / 1000)}s` : `${Math.round(elapsedMs / 60_000)}m`
          : null

        return (
          <div
            key={ra.asset_id}
            style={{
              display: 'grid',
              gridTemplateColumns: '1fr 90px 70px',
              gap: '8px',
              alignItems: 'center',
              padding: '6px 8px',
              borderRadius: '4px',
              background: isBuilding ? 'rgba(96,165,250,0.06)' : 'transparent',
              border: isBuilding ? '1px solid rgba(96,165,250,0.2)' : '1px solid transparent',
              fontFamily: 'var(--ui-stack)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', minWidth: 0 }}>
              <span style={{
                width: '6px', height: '6px', borderRadius: '50%',
                background: stateColor, flexShrink: 0,
                boxShadow: isBuilding ? `0 0 6px ${stateColor}` : 'none',
              }} />
              <span style={{
                fontFamily: 'var(--mono-stack)', fontSize: '11px',
                color: 'var(--on-dark)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
              }}>
                {ra.asset_id}
              </span>
            </div>
            <div style={{ fontSize: '10px', color: stateColor, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              {ra.state}
            </div>
            <div style={{ fontSize: '10px', color: 'var(--on-dark-faint)', fontFamily: 'var(--mono-stack)', textAlign: 'right' }}>
              {elapsedStr ?? (ra.started_at ? formatRelative(ra.started_at) : '—')}
            </div>
          </div>
        )
      })}
    </div>
  )
}

function EventLogTail({ entries }: { entries: LogEntry[] }) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [entries.length])

  return (
    <div
      style={{
        height: '400px',
        overflowY: 'auto',
        background: 'rgba(0,0,0,0.3)',
        border: '1px solid var(--black-line)',
        borderRadius: '6px',
        padding: '8px',
        fontFamily: 'var(--mono-stack)',
        fontSize: '10px',
      }}
    >
      {entries.length === 0 ? (
        <div style={{ color: 'var(--on-dark-faint)', padding: '8px' }}>Waiting for events…</div>
      ) : (
        entries.map(entry => (
          <div key={entry.id} style={{ display: 'flex', gap: '8px', padding: '2px 0', borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
            <span style={{ color: 'var(--on-dark-faint)', flexShrink: 0, minWidth: '55px' }}>{entry.time}</span>
            <span style={{ color: EVENT_COLOR[entry.type] ?? 'var(--on-dark-mut)', flexShrink: 0, minWidth: '110px' }}>{entry.type}</span>
            <span style={{ color: 'var(--on-dark)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{entry.label}</span>
          </div>
        ))
      )}
      <div ref={bottomRef} />
    </div>
  )
}

export function WorkflowView({ chartId }: Props) {
  const { run: activeRun, assets: runAssets } = useActiveRun(chartId)
  const [logEntries, setLogEntries] = useState<LogEntry[]>([])

  const handleEvent = useCallback((e: CockpitEvent) => {
    const time = new Date().toISOString().slice(11, 19)
    let label = ''
    if (e.type === 'asset.state_change') label = `${e.asset_id}: ${e.from_state} → ${e.to_state}`
    else if (e.type === 'asset.progress') label = `${e.asset_id}: ${e.rows_written.toLocaleString()} rows`
    else if (e.type === 'run.state_change') label = `run ${e.run_id.slice(0, 8)}: ${e.state}`
    else if (e.type === 'edge.first_signal') label = `${e.from_asset_id} → ${e.to_asset_id}`

    setLogEntries(prev => {
      const next = [...prev, { id: ++logCounter, time, type: e.type, label }]
      return next.length > 50 ? next.slice(-50) : next
    })
  }, [])

  useCockpitSSE(chartId, handleEvent)

  if (!activeRun) {
    return (
      <div style={{ padding: '48px 24px', color: 'var(--on-dark-faint)', fontFamily: 'var(--ui-stack)', fontSize: '14px' }}>
        No build in flight. Trigger one from the Data assets tab.
      </div>
    )
  }

  const startedLabel = activeRun.started_at ? formatDateTime(activeRun.started_at) : 'pending'

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {/* Run summary bar */}
      <div style={{
        display: 'flex', gap: '24px', alignItems: 'center',
        padding: '10px 16px',
        background: 'var(--black-raised)',
        border: '1px solid var(--black-line)',
        borderRadius: '6px',
        fontFamily: 'var(--mono-stack)', fontSize: '11px',
        color: 'var(--on-dark-faint)',
      }}>
        <span>Run <span style={{ color: 'var(--on-dark)' }}>{activeRun.id.slice(0, 8)}</span></span>
        <span>Scope <span style={{ color: 'var(--on-dark)' }}>{activeRun.scope}{activeRun.scope_target ? `:${activeRun.scope_target}` : ''}</span></span>
        <span>Action <span style={{ color: 'var(--gold-high)' }}>{activeRun.action}</span></span>
        <span>State <span style={{ color: activeRun.state === 'running' ? '#60a5fa' : 'var(--on-dark)' }}>{activeRun.state}</span></span>
        <span>Started <span style={{ color: 'var(--on-dark)' }}>{startedLabel}</span></span>
        <span>{runAssets.length} / {activeRun.plan.length} assets</span>
      </div>

      {/* Timeline + event log */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '24px', alignItems: 'flex-start' }}>
        <div>
          <div style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--on-dark-faint)', marginBottom: '8px' }}>
            Plan timeline
          </div>
          <PlanTimeline assets={runAssets} currentAssetId={activeRun.current_asset_id} />
        </div>
        <div>
          <div style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--on-dark-faint)', marginBottom: '8px' }}>
            Live events
          </div>
          <EventLogTail entries={logEntries} />
        </div>
      </div>
    </div>
  )
}
