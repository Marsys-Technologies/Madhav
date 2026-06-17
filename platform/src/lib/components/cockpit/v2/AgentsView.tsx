'use client'

import { useActiveRun, type ActiveRunAsset } from '@/hooks/useActiveRun'
import { formatDateTime, formatRelative } from '@/lib/utils/date'

interface Props {
  chartId: string
}

function elapsed(ra: ActiveRunAsset): string {
  if (!ra.started_at) return '—'
  const from = new Date(ra.started_at).getTime()
  const to = ra.ended_at ? new Date(ra.ended_at).getTime() : Date.now()
  const s = Math.round((to - from) / 1000)
  if (s < 60) return `${s}s`
  return `${Math.floor(s / 60)}m ${s % 60}s`
}

function AgentCard({ ra }: { ra: ActiveRunAsset }) {
  return (
    <div style={{
      padding: '14px 16px',
      background: 'rgba(96,165,250,0.06)',
      border: '1px solid rgba(96,165,250,0.25)',
      borderRadius: '8px',
      fontFamily: 'var(--ui-stack)',
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
        <div style={{ fontFamily: 'var(--mono-stack)', fontSize: '11px', color: 'var(--on-dark)', wordBreak: 'break-all' }}>
          {ra.asset_id}
        </div>
        <span style={{
          fontSize: '9px', textTransform: 'uppercase', letterSpacing: '0.06em',
          color: '#60a5fa', background: 'rgba(96,165,250,0.15)',
          padding: '2px 6px', borderRadius: '3px', flexShrink: 0, marginLeft: '8px',
        }}>
          {ra.state}
        </span>
      </div>
      <div style={{ display: 'flex', gap: '16px', fontSize: '11px', color: 'var(--on-dark-faint)', fontFamily: 'var(--mono-stack)' }}>
        <span>Started {ra.started_at ? formatRelative(ra.started_at) : '—'}</span>
        <span>Elapsed {elapsed(ra)}</span>
      </div>
      {ra.error && (
        <div style={{ marginTop: '8px', fontSize: '10px', color: 'var(--marsys-error, #e05252)', fontFamily: 'var(--mono-stack)' }}>
          {ra.error}
        </div>
      )}
    </div>
  )
}

function CompletedRow({ ra }: { ra: ActiveRunAsset }) {
  return (
    <div style={{
      display: 'grid', gridTemplateColumns: '1fr 80px 80px 80px',
      gap: '8px', alignItems: 'center',
      padding: '5px 8px',
      borderBottom: '1px solid rgba(255,255,255,0.04)',
      fontFamily: 'var(--mono-stack)', fontSize: '11px',
    }}>
      <span style={{ color: 'var(--on-dark)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{ra.asset_id}</span>
      <span style={{ color: 'var(--marsys-success, #4caf50)', fontSize: '9px', textTransform: 'uppercase' }}>complete</span>
      <span style={{ color: 'var(--on-dark-faint)' }}>{elapsed(ra)}</span>
      <span style={{ color: 'var(--on-dark-faint)', textAlign: 'right' }}>
        {ra.ended_at ? formatDateTime(ra.ended_at).slice(11) : '—'}
      </span>
    </div>
  )
}

function ErrorRow({ ra }: { ra: ActiveRunAsset }) {
  return (
    <div style={{
      padding: '8px 12px',
      background: 'rgba(232,108,108,0.06)',
      border: '1px solid rgba(232,108,108,0.25)',
      borderRadius: '6px',
      marginBottom: '4px',
      fontFamily: 'var(--mono-stack)',
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px' }}>
        <span style={{ color: 'var(--on-dark)' }}>{ra.asset_id}</span>
        <span style={{ color: 'var(--marsys-error, #e05252)', fontSize: '9px', textTransform: 'uppercase' }}>failed</span>
      </div>
      {ra.error && (
        <div style={{ marginTop: '4px', fontSize: '10px', color: 'var(--marsys-error, #e05252)' }}>{ra.error}</div>
      )}
    </div>
  )
}

export function AgentsView({ chartId }: Props) {
  const { run: activeRun, assets: runAssets } = useActiveRun(chartId)

  if (!activeRun) {
    return (
      <div style={{ padding: '48px 24px', color: 'var(--on-dark-faint)', fontFamily: 'var(--ui-stack)', fontSize: '14px' }}>
        No active run. Trigger a build from the Data assets tab.
      </div>
    )
  }

  const building = runAssets.filter(ra => ra.state === 'building')
  const completed = runAssets.filter(ra => ra.state === 'complete').slice(-5)
  const errors = runAssets.filter(ra => ra.state === 'error')

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Active agents */}
      <section>
        <h3 style={{
          fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.06em',
          color: 'var(--on-dark-faint)', marginBottom: '12px', fontFamily: 'var(--ui-stack)',
        }}>
          Active agents ({building.length})
        </h3>
        {building.length === 0 ? (
          <div style={{ color: 'var(--on-dark-faint)', fontSize: '13px', fontFamily: 'var(--ui-stack)' }}>
            No active agents. Build may be queued, or between assets.
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '12px' }}>
            {building.map(ra => <AgentCard key={ra.asset_id} ra={ra} />)}
          </div>
        )}
      </section>

      {/* Recently completed */}
      {completed.length > 0 && (
        <section>
          <h3 style={{
            fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.06em',
            color: 'var(--on-dark-faint)', marginBottom: '8px', fontFamily: 'var(--ui-stack)',
          }}>
            Recently completed
          </h3>
          <div style={{ border: '1px solid var(--black-line)', borderRadius: '6px', overflow: 'hidden' }}>
            {completed.map(ra => <CompletedRow key={ra.asset_id} ra={ra} />)}
          </div>
        </section>
      )}

      {/* Errors */}
      {errors.length > 0 && (
        <section>
          <h3 style={{
            fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.06em',
            color: 'var(--marsys-error, #e05252)', marginBottom: '8px', fontFamily: 'var(--ui-stack)',
          }}>
            Errors this run ({errors.length})
          </h3>
          {errors.map(ra => <ErrorRow key={ra.asset_id} ra={ra} />)}
        </section>
      )}
    </div>
  )
}
