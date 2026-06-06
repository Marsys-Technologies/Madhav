'use client'

import { useState } from 'react'
import type { AssetRow } from '@/app/api/cockpit/registry/route'
import type { AssetStats } from '@/app/api/cockpit/stats/route'
import { AssetRow as AssetRowComponent } from './AssetRow'

const LAYER_COLOR: Record<string, string> = {
  brahmagyan: 'var(--gold-core)',
  ganita: 'var(--jewel-sapphire)',
  bodha: 'var(--jewel-emerald)',
  kala: 'var(--jewel-teal)',
  phala: 'var(--jewel-amethyst)',
  mimamsa: 'var(--gold-engrave)',
}

const LAYER_CODENAME: Record<string, string> = {
  brahmagyan: 'L0',
  ganita: 'L1',
  bodha: 'L2',
  kala: 'L3',
  phala: 'L4',
  mimamsa: 'L5',
}

const LAYER_ENGLISH: Record<string, string> = {
  brahmagyan: 'Foundation',
  ganita: 'Chart facts',
  bodha: 'Chart intelligence',
  kala: 'Temporal',
  phala: 'Prediction',
  mimamsa: 'Learning',
}

interface Props {
  layer: string
  sanskritName: string
  assets: AssetRow[]
  stats: Map<string, AssetStats>
  defaultExpanded?: boolean
}

export function LayerPanel({
  layer,
  sanskritName,
  assets,
  stats,
  defaultExpanded = false,
}: Props) {
  const [expanded, setExpanded] = useState(defaultExpanded)

  const layerLabel = layer.charAt(0).toUpperCase() + layer.slice(1)

  const totalRows = assets.reduce((sum, asset) => {
    const s = stats.get(asset.asset_id)
    return sum + (s?.actual_rows ?? 0)
  }, 0)

  return (
    <div
      style={{
        marginBottom: '8px',
        border: '1px solid var(--black-line)',
        borderRadius: 'var(--r-card)',
        overflow: 'hidden',
      }}
    >
      {/* Header */}
      <div
        onClick={() => setExpanded(!expanded)}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          padding: '12px 16px',
          cursor: 'pointer',
          background: 'var(--black-raised)',
          borderLeft: `3px solid ${LAYER_COLOR[layer] ?? 'var(--black-line)'}`,
        }}
      >
        {/* Chevron */}
        <span style={{ color: 'var(--on-dark-mut)', fontSize: '12px', flexShrink: 0 }}>
          {expanded ? '▼' : '▶'}
        </span>

        {/* Name column — two-line layout */}
        <div style={{ flex: 1, minWidth: 0 }}>
          <div
            style={{
              fontFamily: 'var(--ui-stack)',
              fontSize: '14px',
              fontWeight: 500,
              color: 'var(--on-dark)',
            }}
          >
            {LAYER_ENGLISH[layer] ?? layerLabel}
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', marginTop: '1px' }}>
            <span
              style={{
                fontFamily: 'var(--display-stack)',
                fontSize: '11px',
                fontStyle: 'italic',
                color: 'var(--on-dark-faint)',
              }}
            >
              {sanskritName}
            </span>
            <span
              style={{
                fontFamily: 'var(--mono-stack)',
                fontSize: '10px',
                color: 'var(--on-dark-faint)',
                marginLeft: '6px',
              }}
            >
              · {LAYER_CODENAME[layer] ?? ''}
            </span>
          </div>
        </div>

        {/* Right: asset count + total rows */}
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center', flexShrink: 0 }}>
          <span
            style={{
              fontFamily: 'var(--mono-stack)',
              fontSize: '11px',
              color: 'var(--on-dark-faint)',
            }}
          >
            {assets.length} assets
          </span>
          {totalRows > 0 && (
            <span
              style={{
                fontFamily: 'var(--mono-stack)',
                fontSize: '11px',
                color: 'var(--on-dark-mut)',
              }}
            >
              {totalRows.toLocaleString()} rows
            </span>
          )}
        </div>
      </div>

      {/* Body */}
      {expanded && (
        <div style={{ background: 'var(--black)' }}>
          {assets.map((asset) => (
            <AssetRowComponent
              key={asset.asset_id}
              asset={asset}
              stat={stats.get(asset.asset_id) ?? null}
            />
          ))}
        </div>
      )}
    </div>
  )
}
