'use client'

import { useState, useEffect } from 'react'
import type { AssetRow } from '@/app/api/cockpit/registry/route'
import type { AssetStats } from '@/app/api/cockpit/stats/route'
import type { ActiveRun } from '@/hooks/useActiveRun'
import type { SubstepOverlay } from './DataAssetsView'
import { AssetRow as AssetRowComponent } from './AssetRow'
import { BuildActionButton } from './BuildActionButton'
import { ClearIconButton } from './ClearIconButton'
import { RefreshIconButton } from './RefreshIconButton'
import { StopIconButton } from './StopIconButton'
import { useUserRole } from '@/hooks/useUserRole'

const LAYER_COLOR: Record<string, string> = {
  brahmagyan: 'var(--gold-high)',
  ganita: '#6B9FD4',
  bodha: '#5BAF7A',
  kala: '#4AAFAF',
  phala: '#9B7FD4',
  mimamsa: 'var(--on-dark-mut)',
}

const LAYER_NAMES: Record<string, { sa: string; en: string }> = {
  brahmagyan: { sa: 'Brahma Jñāna', en: 'Foundation' },
  ganita:     { sa: 'Gaṇita',       en: 'Chart facts' },
  bodha:      { sa: 'Bodha',        en: 'Chart intelligence' },
  kala:       { sa: 'Kāla',         en: 'Temporal' },
  phala:      { sa: 'Phala',        en: 'Prediction' },
  mimamsa:    { sa: 'Mīmāṃsā',      en: 'Learning' },
}

interface Props {
  layer: string
  assets: AssetRow[]
  allAssets?: AssetRow[]
  stats: Map<string, AssetStats>
  defaultExpanded?: boolean
  forceExpand?: boolean
  focusedAssetId?: string | null
  chartId: string
  activeRun: ActiveRun | null
  substepOverlay?: Map<string, SubstepOverlay>
  onRunStarted: () => void
}

export function LayerPanel({
  layer,
  assets,
  allAssets,
  stats,
  defaultExpanded = false,
  forceExpand,
  focusedAssetId,
  chartId,
  activeRun,
  substepOverlay,
  onRunStarted,
}: Props) {
  const [expanded, setExpanded] = useState(defaultExpanded)
  const { isSuperAdmin } = useUserRole()

  useEffect(() => {
    if (forceExpand) setExpanded(true)
  }, [forceExpand])

  const layerNames = LAYER_NAMES[layer] ?? { sa: layer, en: layer }

  const totalRows = assets.reduce((sum, asset) => {
    const s = stats.get(asset.asset_id)
    return sum + (s?.actual_rows ?? 0)
  }, 0)

  // Derive scope stats for BuildActionButton
  const activeAssets = assets.filter(a => a.is_active)
  const dormantCount = activeAssets.filter(a => {
    const s = stats.get(a.asset_id)
    return !s?.actual_rows && !s?.error
  }).length
  const staleCount = 0 // populated by throughput state in Phase 9

  // Active run overlaps this layer if scope is global or scope_target matches this layer
  const layerRunActive = activeRun != null && (
    activeRun.scope === 'global' ||
    (activeRun.scope === 'layer' && activeRun.scope_target === layer)
  )
  const layerRunId = layerRunActive ? activeRun!.id : null
  const layerRunPaused = layerRunActive && activeRun!.state === 'paused'

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

        {/* Name column — bilingual two-line: Sanskrit (22px gold) above, English (14px) below */}
        <div style={{ flex: 1, minWidth: 0 }}>
          <div
            style={{
              fontFamily: 'var(--font-serif)',
              fontSize: '22px',
              lineHeight: 1.1,
              fontWeight: 400,
              color: 'var(--gold-high)',
            }}
          >
            {layerNames.sa}
          </div>
          <div
            style={{
              fontFamily: 'var(--ui-stack)',
              fontSize: '14px',
              lineHeight: 1.2,
              color: 'rgba(255,255,255,0.90)',
              marginTop: '2px',
            }}
          >
            {layerNames.en}
          </div>
        </div>

        {/* Right: asset count + rows + [Build/Rebuild] [Refresh] [Stop | Delete] */}
        <div
          style={{ display: 'flex', alignItems: 'center', gap: '16px', flexShrink: 0 }}
          onClick={e => e.stopPropagation()}
        >
          {/* Metric group — two distinct figures separated by a hairline divider */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', fontFamily: 'var(--mono-stack)', fontSize: '11px' }}>
            <span style={{ minWidth: '58px', textAlign: 'right', color: 'var(--on-dark-faint)' }}>
              {assets.length} assets
            </span>
            <span aria-hidden style={{ width: '1px', height: '14px', background: 'rgba(255,255,255,0.14)' }} />
            <span style={{ minWidth: '88px', textAlign: 'right', color: 'var(--on-dark-mut)' }}>
              {totalRows > 0 ? `${totalRows.toLocaleString()} rows` : '— rows'}
            </span>
          </div>

          {/* Build/Rebuild — hidden when layer run active */}
          {!layerRunId && (
            <BuildActionButton
              chartId={chartId}
              scope="layer"
              scopeTarget={layer}
              size="sm"
              stats={{
                total: activeAssets.length,
                dormant: dormantCount,
                stale: staleCount,
                active_run_id: null,
                is_paused: false,
              }}
              onRunStarted={onRunStarted}
              onRunStateChange={onRunStarted}
            />
          )}

          {/* Refresh — always (role-gated for brahmagyan) */}
          {(isSuperAdmin || layer !== 'brahmagyan') && (
            <RefreshIconButton
              chartId={chartId}
              scope="layer"
              scopeTarget={layer}
              size={28}
              onRefreshed={onRunStarted}
            />
          )}

          {/* Stop (when running) or Delete (when idle) — role-gated for brahmagyan */}
          {(isSuperAdmin || layer !== 'brahmagyan') && (
            layerRunId ? (
              <StopIconButton runId={layerRunId} size={28} onStopped={onRunStarted} />
            ) : (
              <ClearIconButton
                chartId={chartId}
                scope="layer"
                scopeTarget={layer}
                size={28}
                onSuccess={onRunStarted}
              />
            )
          )}
        </div>
      </div>

      {/* Body */}
      {expanded && (
        <div style={{ background: 'var(--black)' }}>
          {/* Column headers */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'minmax(0,42%) minmax(0,28%) minmax(0,14%) minmax(0,16%)',
              gap: '16px',
              padding: '6px 12px',
              fontSize: '11px',
              textTransform: 'uppercase',
              letterSpacing: '0.06em',
              color: 'var(--on-dark-faint)',
              borderBottom: '1px solid rgba(255,255,255,0.06)',
              fontFamily: 'var(--ui-stack)',
            }}
          >
            <div>Asset</div>
            <div>Progress</div>
            <div>Last built</div>
            <div style={{ textAlign: 'right' }}>Actions</div>
          </div>
          {assets.map((asset) => {
            const assetRunActive = activeRun != null && (
              activeRun.scope === 'global' ||
              (activeRun.scope === 'layer' && activeRun.scope_target === layer) ||
              (activeRun.scope === 'asset' && activeRun.scope_target === asset.asset_id)
            )
            return (
              <AssetRowComponent
                key={asset.asset_id}
                asset={asset}
                stat={stats.get(asset.asset_id) ?? null}
                chartId={chartId}
                activeRunId={assetRunActive ? activeRun!.id : null}
                activeRunPaused={assetRunActive && activeRun!.state === 'paused'}
                highlighted={focusedAssetId === asset.asset_id}
                allAssets={allAssets}
                substep={substepOverlay?.get(asset.asset_id) ?? null}
                onRunStarted={onRunStarted}
              />
            )
          })}
        </div>
      )}
    </div>
  )
}
