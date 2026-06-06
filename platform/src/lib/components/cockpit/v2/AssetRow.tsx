'use client'

import type { AssetRow as AssetRowType } from '@/app/api/cockpit/registry/route'
import type { AssetStats } from '@/app/api/cockpit/stats/route'
import { BuildActionButton } from './BuildActionButton'
import { ClearIconButton } from './ClearIconButton'
import { formatDate } from '@/lib/utils/date'

const STATE_CHIP: Record<string, { label: string; bg: string; color: string; border: string }> = {
  dormant:  { label: 'NOT BUILT', bg: 'transparent',               color: 'var(--on-dark-faint)', border: 'var(--black-line)' },
  building: { label: 'BUILDING',  bg: 'rgba(59,130,246,0.15)',      color: '#60a5fa',              border: '#3b82f6' },
  lit:      { label: 'LIVE',      bg: 'rgba(62,124,75,0.15)',       color: 'var(--marsys-success)', border: 'var(--marsys-success)' },
  stale:    { label: 'STALE',     bg: 'rgba(212,175,55,0.12)',      color: '#d4af37',              border: '#a47a28' },
  error:    { label: 'ERROR',     bg: 'rgba(181,71,76,0.15)',       color: 'var(--marsys-error)',  border: 'var(--marsys-error)' },
}

interface Props {
  asset: AssetRowType
  stat: AssetStats | null
  chartId: string
  activeRunId: string | null
  activeRunPaused: boolean
  highlighted?: boolean
  onRunStarted: () => void
}

export function AssetRow({ asset, stat, chartId, activeRunId, activeRunPaused, highlighted, onRunStarted }: Props) {
  const isActive = asset.is_active
  const hasError = stat?.error != null && stat.error !== 'missing_table'

  // Derive state: prefer throughput state, fallback to row-count heuristic
  const throughputState = stat?.state
  const derivedState: string = !isActive
    ? 'not_migrated'
    : throughputState ?? (stat?.actual_rows ? 'lit' : 'dormant')

  const chipConfig = isActive
    ? (STATE_CHIP[derivedState] ?? STATE_CHIP.dormant)
    : { label: 'NOT MIGRATED', bg: 'rgba(124,114,91,0.10)', color: 'var(--on-dark-faint)', border: 'var(--black-line)' }

  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: '40% 15% 15% 20% 10%',
        gap: '8px',
        alignItems: 'center',
        padding: '8px 12px',
        borderBottom: '1px solid rgba(255,255,255,0.04)',
        fontFamily: 'var(--ui-stack)',
        background: highlighted ? 'rgba(236,197,106,0.08)' : 'transparent',
        boxShadow: highlighted ? 'inset 0 0 0 1px rgba(236,197,106,0.25)' : 'none',
        transition: 'background 0.4s ease, box-shadow 0.4s ease',
      }}
    >
      {/* Asset name — two-line */}
      <div style={{ minWidth: 0 }}>
        <div style={{ fontSize: '13px', color: 'var(--on-dark)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
          {asset.english_name}
        </div>
        <div style={{ fontSize: '10px', fontFamily: 'var(--mono-stack)', color: 'var(--on-dark-faint)', marginTop: '1px' }}>
          {asset.asset_id}
        </div>
      </div>

      {/* Rows */}
      <div style={{ textAlign: 'right', fontFamily: 'var(--mono-stack)', fontSize: '12px' }}>
        {!isActive ? (
          <span style={{ color: 'var(--on-dark-faint)' }}>—</span>
        ) : stat?.actual_rows != null ? (
          <span style={{ color: 'var(--on-dark)' }}>{stat.actual_rows.toLocaleString()}</span>
        ) : (
          <span style={{ color: 'var(--on-dark-faint)' }}>—</span>
        )}
      </div>

      {/* State chip */}
      <div>
        <span
          className="marsys-chip"
          style={{
            background: chipConfig.bg,
            color: chipConfig.color,
            borderColor: chipConfig.border,
            fontSize: '9px',
          }}
        >
          {chipConfig.label}
        </span>
        {hasError && stat?.error && (
          <div style={{ fontSize: '9px', color: 'var(--marsys-error)', marginTop: '2px', fontFamily: 'var(--mono-stack)' }}>
            {stat.error.slice(0, 24)}
          </div>
        )}
      </div>

      {/* Last built */}
      <div style={{ fontSize: '11px', color: 'var(--on-dark-faint)', fontFamily: 'var(--mono-stack)' }}>
        {stat?.last_built_at ? formatDate(stat.last_built_at) : '—'}
      </div>

      {/* Actions: build button + clear */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '2px' }}>
        {isActive && (
          <>
            <BuildActionButton
              chartId={chartId}
              scope="asset"
              scopeTarget={asset.asset_id}
              size="sm"
              stats={{
                total: 1,
                dormant: derivedState === 'dormant' ? 1 : 0,
                stale: derivedState === 'stale' ? 1 : 0,
                active_run_id: activeRunId,
                is_paused: activeRunPaused,
              }}
              onRunStarted={onRunStarted}
              onRunStateChange={onRunStarted}
            />
            <ClearIconButton
              chartId={chartId}
              scope="asset"
              scopeTarget={asset.asset_id}
              size={22}
              onSuccess={onRunStarted}
            />
          </>
        )}
      </div>
    </div>
  )
}
