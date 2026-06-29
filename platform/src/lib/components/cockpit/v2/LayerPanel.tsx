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

// Layer-level status dot — mirrors AssetRow's StatusDot at the layer grain.
// green = all lit · amber = building OR partially lit · red = any error · dim = all dormant
function LayerStatusDot({
  layerIsBuilding,
  litCount,
  activeCount,
  errorCount,
}: {
  layerIsBuilding: boolean
  litCount: number
  activeCount: number
  errorCount: number
}) {
  const allLit = activeCount > 0 && litCount === activeCount
  const partialLit = litCount > 0 && !allLit
  const color = layerIsBuilding || partialLit
    ? '#ECC56A'
    : errorCount > 0
      ? 'rgba(220,80,80,0.95)'
      : allLit
        ? 'rgba(83,200,100,0.95)'
        : 'rgba(255,255,255,0.22)'
  const shadow = (layerIsBuilding || partialLit || allLit || errorCount > 0) ? `0 0 5px ${color}` : 'none'
  const title = layerIsBuilding
    ? 'Building…'
    : errorCount > 0
      ? `${errorCount} error(s)`
      : allLit
        ? 'All assets lit'
        : partialLit
          ? `${litCount} / ${activeCount} lit`
          : `0 / ${activeCount} — not built`
  return (
    <span
      title={title}
      style={{
        width: 8, height: 8, borderRadius: '50%',
        background: color, boxShadow: shadow,
        flexShrink: 0, display: 'inline-block',
      }}
    />
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
  const litCount = activeAssets.filter(a => {
    const s = stats.get(a.asset_id)
    return s?.state === 'lit' || s?.state === 'service_ok'
  }).length
  const layerIsBuilding = activeRun != null && layerOwnsBuildingAsset

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
          display: 'grid',
          gridTemplateColumns: '220px 230px 1fr',
          alignItems: 'center',
          columnGap: '20px',
          padding: '12px 16px',
          cursor: 'pointer',
          background: 'var(--black-raised)',
        }}
      >
        {/* Left: rotating caret + status dot + bilingual name block */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', minWidth: 0 }}>
          <motion.svg
            width="11" height="11" viewBox="0 0 12 12" fill="none"
            stroke="var(--on-dark-mut)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"
            aria-hidden="true" style={{ flexShrink: 0 }}
            animate={{ rotate: expanded ? 90 : 0 }}
            transition={{ duration: DUR.base, ease: EASE.out }}
          >
            <path d="M4 2 L8 6 L4 10" />
          </motion.svg>

          {/* Name block — status dot sits beside Sanskrit name */}
          <div style={{ minWidth: 0 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '7px' }}>
              <LayerStatusDot
                layerIsBuilding={layerIsBuilding}
                litCount={litCount}
                activeCount={activeAssets.length}
                errorCount={errorCount}
              />
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
            </div>
            <div
              style={{
                fontFamily: 'var(--ui-stack)',
                fontSize: '14px',
                lineHeight: 1.2,
                color: 'rgba(255,255,255,0.90)',
                marginTop: '2px',
                paddingLeft: '15px',
              }}
            >
              {layerNames.en}
            </div>
          </div>
        </div>

        {/* Gauge — fixed 230px grid column */}
        <div
          style={{ fontFamily: 'var(--mono-stack)' }}
          onClick={e => e.stopPropagation()}
        >
          {/* Two-column numeric row */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: '3px' }}>
            <div>
              <div style={{ fontSize: '8.5px', color: 'var(--on-dark-faint)', letterSpacing: '0.07em', textTransform: 'uppercase', marginBottom: '1px' }}>
                Assets Built
              </div>
              <div style={{ fontSize: '13px', fontVariantNumeric: 'tabular-nums' }}>
                <span style={{ color: 'var(--gold-high)', fontWeight: 600 }}>{litCount}</span>
                <span style={{ color: 'var(--on-dark-faint)', fontWeight: 400, fontSize: '11px' }}>{' / '}{activeAssets.length}</span>
              </div>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: '8.5px', color: 'var(--on-dark-faint)', letterSpacing: '0.07em', textTransform: 'uppercase', marginBottom: '1px' }}>
                Rows
              </div>
              <div style={{ fontSize: '11px', fontVariantNumeric: 'tabular-nums', color: totalRows > 0 ? 'var(--on-dark-mut)' : 'var(--on-dark-faint)' }}>
                {totalRows > 0 ? totalRows.toLocaleString() : '—'}
              </div>
            </div>
          </div>
          {/* 3px completion bar */}
          <div style={{ position: 'relative', height: '3px', borderRadius: '2px', background: 'rgba(122,86,24,0.25)', overflow: 'hidden' }}>
            <div style={{
              position: 'absolute', top: 0, left: 0, bottom: 0, borderRadius: '2px',
              width: activeAssets.length > 0 ? ((litCount / activeAssets.length) * 100) + '%' : '0%',
              background: layerIsBuilding ? 'rgba(210,162,60,0.88)' : 'rgba(176,137,58,0.92)',
              transition: 'width 0.6s ease-out',
            }} />
            {layerIsBuilding && (
              <div style={{
                position: 'absolute', inset: 0, pointerEvents: 'none',
                background: 'linear-gradient(90deg, transparent 0%, rgba(236,197,106,0.3) 50%, transparent 100%)',
                animation: 'shimmer 2.2s linear infinite',
              }} />
            )}
          </div>
        </div>

        {/* Actions — 1fr column, buttons right-anchored */}
        <div
          style={{ display: 'flex', alignItems: 'center', gap: '8px', justifyContent: 'flex-end' }}
          onClick={e => e.stopPropagation()}
        >
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
