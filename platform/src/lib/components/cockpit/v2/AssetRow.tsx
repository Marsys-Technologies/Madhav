'use client'

import type { AssetRow as AssetRowType } from '@/app/api/cockpit/registry/route'
import type { AssetStats } from '@/app/api/cockpit/stats/route'

interface Props {
  asset: AssetRowType
  stat: AssetStats | null
}

export function AssetRow({ asset, stat }: Props) {
  const hasError = stat?.error != null
  const isActive = asset.is_active

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

      {/* Status pill */}
      <div>
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
        ) : (
          <span
            className="marsys-chip"
            style={{
              background: 'rgba(62,124,75,0.15)',
              color: 'var(--marsys-success)',
              borderColor: 'var(--marsys-success)',
              fontSize: '9px',
            }}
          >
            LIVE
          </span>
        )}
      </div>
    </div>
  )
}
