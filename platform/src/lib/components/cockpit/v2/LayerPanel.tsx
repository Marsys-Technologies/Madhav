'use client'

import { useState, useEffect, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
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
import { DUR, EASE, STAGGER } from './motion'

// Layer identity is a value-step within the gold ramp (not a jewel hue) —
// each layer's sun-node sits a notch differently on the burnished-gold scale.
const LAYER_GOLD: Record<string, string> = {
  brahmagyan: '#ECC56A',
  ganita:     '#D2A23C',
  bodha:      '#A87C2A',
  kala:       '#8A5E12',
  phala:      '#B98A2E',
  mimamsa:    '#6E4E0F',
}

// Sun-node mark — the brand's sanctioned glyph, tinted per layer along the gold ramp.
function SunNode({ color, size = 11 }: { color: string; size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 12 12" fill="none" stroke={color} strokeWidth="1" strokeLinejoin="round" aria-hidden="true" style={{ flexShrink: 0 }}>
      <path d="M6 0.5 L7.2 4.8 L11.5 6 L7.2 7.2 L6 11.5 L4.8 7.2 L0.5 6 L4.8 4.8 Z" />
    </svg>
  )
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
  hoveredAssetId?: string | null
  onHover?: (assetId: string | null) => void
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
  hoveredAssetId,
  onHover,
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

  // Task 5: sync when defaultExpanded prop changes (e.g. build starts and auto-expands)
  useEffect(() => {
    if (defaultExpanded) setExpanded(true)
  }, [defaultExpanded])

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
  const staleCount = useMemo(
    () => activeAssets.filter(a => stats.get(a.asset_id)?.state === 'stale').length,
    [activeAssets, stats]
  )
  const errorCount = activeAssets.filter(a => stats.get(a.asset_id)?.state === 'error').length

  // Active run overlaps this layer if scope is global or scope_target matches this layer
  const layerRunActive = activeRun != null && (
    activeRun.scope === 'global' ||
    (activeRun.scope === 'layer' && activeRun.scope_target === layer)
  )
  const layerRunId = layerRunActive ? activeRun!.id : null
  const layerRunPaused = layerRunActive && activeRun!.state === 'paused'
  // Only the layer that owns the currently-building asset surfaces a Stop control. Without this
  // a global run lights up Stop on every (idle) layer, which is misleading — every Stop just
  // halts the whole run. The build advances one asset at a time, so scope to current_asset_id.
  const buildingAssetId = activeRun?.current_asset_id ?? null
  const layerOwnsBuildingAsset = buildingAssetId != null && activeAssets.some(a => a.asset_id === buildingAssetId)

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
        role="button"
        tabIndex={0}
        aria-expanded={expanded}
        aria-label={`${layerNames.sa} layer, ${expanded ? 'expanded' : 'collapsed'}`}
        onClick={() => setExpanded(!expanded)}
        onKeyDown={e => {
          if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); setExpanded(v => !v) }
        }}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          padding: '12px 16px',
          cursor: 'pointer',
          background: 'var(--black-raised)',
        }}
      >
        {/* Rotating caret + per-layer sun-node mark (gold hairline language, no jewel stripe) */}
        <motion.svg
          width="11" height="11" viewBox="0 0 12 12" fill="none"
          stroke="var(--on-dark-mut)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"
          aria-hidden="true" style={{ flexShrink: 0 }}
          animate={{ rotate: expanded ? 90 : 0 }}
          transition={{ duration: DUR.base, ease: EASE.out }}
        >
          <path d="M4 2 L8 6 L4 10" />
        </motion.svg>
        <SunNode color={LAYER_GOLD[layer] ?? 'var(--gold-core)'} />

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
              {stats.size > 0 ? (
                totalRows > 0 ? `${totalRows.toLocaleString()} rows` : '— rows'
              ) : (
                <span
                  aria-label="Loading row count"
                  style={{
                    display: 'inline-block',
                    width: '4.5ch',
                    height: '0.85em',
                    borderRadius: '2px',
                    background: 'var(--obsidian-border-mid, #252119)',
                    verticalAlign: 'middle',
                    animation: 'pulse 1.4s ease-in-out infinite',
                  }}
                />
              )}
            </span>
            {errorCount > 0 && (
              <>
                <span aria-hidden style={{ width: '1px', height: '14px', background: 'rgba(255,255,255,0.14)' }} />
                <span style={{ color: '#ff6b6b', fontFamily: 'var(--mono-stack)', fontSize: '11px', minWidth: '60px', textAlign: 'right' }}>
                  {errorCount} error{errorCount > 1 ? 's' : ''}
                </span>
              </>
            )}
          </div>

          {/* Build/Rebuild — hidden when layer run active; role-gated for brahmagyan */}
          {!layerRunId && (isSuperAdmin || layer !== 'brahmagyan') && (
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
              // Stop only on the layer actually building; idle layers during a run show nothing
              layerOwnsBuildingAsset
                ? <StopIconButton runId={layerRunId} size={28} onStopped={onRunStarted} />
                : null
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

      {/* Body — animated expand/collapse */}
      <AnimatePresence initial={false}>
        {expanded && (
          <motion.div
            key="body"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: DUR.panel, ease: EASE.inOut }}
            style={{ background: 'var(--black)', overflow: 'hidden' }}
          >
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
              <div style={{ textAlign: 'center' }}>Progress</div>
              <div style={{ textAlign: 'center' }}>Last built</div>
              <div style={{ textAlign: 'center' }}>Actions</div>
            </div>
            {[...assets].sort((a, b) => {
              // services first, then data assets; stable within each group
              const aSvc = (a.asset_type === 'service' || a.asset_kind === 'service') ? 0 : 1
              const bSvc = (b.asset_type === 'service' || b.asset_kind === 'service') ? 0 : 1
              return aSvc - bSvc
            }).map((asset, i) => {
              const assetRunActive = activeRun != null && (
                activeRun.scope === 'global' ||
                (activeRun.scope === 'layer' && activeRun.scope_target === layer) ||
                (activeRun.scope === 'asset' && activeRun.scope_target === asset.asset_id)
              )
              return (
                <motion.div
                  key={asset.asset_id}
                  initial={{ opacity: 0, y: 4 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: DUR.base, ease: EASE.out, delay: i * STAGGER }}
                  onMouseEnter={() => onHover?.(asset.asset_id)}
                  onMouseLeave={() => onHover?.(null)}
                >
                  <AssetRowComponent
                    asset={asset}
                    stat={stats.get(asset.asset_id) ?? null}
                    chartId={chartId}
                    activeRunId={assetRunActive ? activeRun!.id : null}
                    activeRunPaused={assetRunActive && activeRun!.state === 'paused'}
                    isActiveAsset={assetRunActive && activeRun!.current_asset_id === asset.asset_id}
                    highlighted={focusedAssetId === asset.asset_id || hoveredAssetId === asset.asset_id}
                    allAssets={allAssets}
                    substep={substepOverlay?.get(asset.asset_id) ?? null}
                    onRunStarted={onRunStarted}
                  />
                </motion.div>
              )
            })}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
