'use client'

import type { AssetRow as AssetRowType } from '@/app/api/cockpit/registry/route'
import type { AssetStats } from '@/app/api/cockpit/stats/route'
import { BuildActionButton } from './BuildActionButton'

interface Props {
  asset: AssetRowType
  stat: AssetStats | null
  chartId: string
  activeRunId: string | null
  activeRunPaused: boolean
  onRunStarted: () => void
}

export function AssetRow({ asset, stat, chartId, activeRunId, activeRunPaused, onRunStarted }: Props) {
  const hasError = stat?.error != null
  const isActive = asset.is_active
  const isDormant = isActive && !stat?.actual_rows && !hasError

  const dotColor = !isActive
    ? 'var(--black-line)'
    : hasError
      ? 'var(--marsys-error)'
      : 'var(--jewel-emerald)'

  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: '16px 1fr 160px 120px 90px',
        gap: '8px',
        alignItems: 'center',
        padding: '8px 16px',
        borderBottom: '1px solid var(--black-line)',
        fontFamily: 'var(--ui-stack)',
      }}
    >
      {/* Status dot */}
      <span
        style={{
          width: '10px',
          height: '10px',
          borderRadius: '50%',
          background: dotColor,
          display: 'inline-block',
        }}
      />

      {/* Name */}
      <div>
        <div style={{ fontSize: '13px', color: 'var(--on-dark)' }}>
          {asset.english_name}
        </div>
        <div
          style={{
            fontSize: '11px',
            fontFamily: 'var(--display-stack)',
            fontStyle: 'italic',
            color: 'var(--on-dark-faint)',
          }}
        >
          {asset.sanskrit_name}
        </div>
      </div>

      {/* Storage */}
      <div>
        <div
          style={{
            fontSize: '9.5px',
            textTransform: 'uppercase',
            letterSpacing: '0.08em',
            color: 'var(--on-dark-faint)',
          }}
        >
          STORAGE
        </div>
        <div
          style={{
            fontSize: '11px',
            fontFamily: 'var(--mono-stack)',
            color: 'var(--on-dark)',
          }}
        >
          {asset.storage_type}
          {asset.target_table ? ` · ${asset.target_table}` : ''}
        </div>
      </div>

      {/* Rows */}
      <div style={{ fontFamily: 'var(--mono-stack)', fontSize: '12px' }}>
        {!isActive ? (
          <span style={{ color: 'var(--on-dark-faint)' }}>not migrated</span>
        ) : stat?.actual_rows != null ? (
          <span style={{ color: 'var(--on-dark)' }}>
            {stat.actual_rows.toLocaleString()} rows
          </span>
        ) : (
          <span style={{ color: 'var(--on-dark-faint)' }}>—</span>
        )}
      </div>

      {/* Status pill + build button */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap' }}>
        {!isActive ? (
          <span
            className="marsys-chip"
            style={{
              background: 'rgba(124,114,91,0.10)',
              color: 'var(--on-dark-faint)',
              borderColor: 'var(--black-line)',
              fontSize: '9px',
            }}
          >
            NOT MIGRATED
          </span>
        ) : hasError ? (
          <>
            <span
              className="marsys-chip"
              style={{
                background: 'rgba(181,71,76,0.15)',
                color: 'var(--marsys-error)',
                borderColor: 'var(--marsys-error)',
                fontSize: '9px',
              }}
            >
              {(stat!.error ?? 'ERROR').toUpperCase()}
            </span>
            <BuildActionButton
              chartId={chartId}
              scope="asset"
              scopeTarget={asset.asset_id}
              size="sm"
              stats={{ total: 1, dormant: 0, stale: 0, active_run_id: activeRunId, is_paused: activeRunPaused }}
              onRunStarted={onRunStarted}
              onRunStateChange={onRunStarted}
            />
          </>
        ) : (
          <>
            <span
              className="marsys-chip"
              style={{
                background: isDormant ? 'transparent' : 'rgba(62,124,75,0.15)',
                color: isDormant ? 'var(--on-dark-faint)' : 'var(--marsys-success)',
                borderColor: isDormant ? 'var(--black-line)' : 'var(--marsys-success)',
                fontSize: '9px',
              }}
            >
              {isDormant ? 'NOT BUILT' : 'LIVE'}
            </span>
            <BuildActionButton
              chartId={chartId}
              scope="asset"
              scopeTarget={asset.asset_id}
              size="sm"
              stats={{
                total: 1,
                dormant: isDormant ? 1 : 0,
                stale: 0,
                active_run_id: activeRunId,
                is_paused: activeRunPaused,
              }}
              onRunStarted={onRunStarted}
              onRunStateChange={onRunStarted}
            />
          </>
        )}
      </div>
    </div>
  )
}
