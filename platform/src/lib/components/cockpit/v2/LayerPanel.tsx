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
        <span style={{ color: 'var(--on-dark-mut)', fontSize: '12px' }}>
          {expanded ? '▼' : '▶'}
        </span>
        <span
          style={{
            fontFamily: 'var(--ui-stack)',
            fontSize: '14px',
            fontWeight: 500,
            color: 'var(--on-dark)',
          }}
        >
          {layerLabel}
        </span>
        <span
          style={{
            fontFamily: 'var(--display-stack)',
            fontSize: '12px',
            fontStyle: 'italic',
            color: 'var(--on-dark-faint)',
            marginLeft: '4px',
          }}
        >
          {sanskritName}
        </span>
        <span
          style={{
            marginLeft: 'auto',
            fontSize: '11px',
            color: 'var(--on-dark-faint)',
            fontFamily: 'var(--mono-stack)',
          }}
        >
          {assets.length} assets
        </span>
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
