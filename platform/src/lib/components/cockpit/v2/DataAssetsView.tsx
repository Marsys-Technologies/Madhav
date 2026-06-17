'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import { useAssetRegistry } from '@/hooks/useAssetRegistry'
import { useAssetStats } from '@/hooks/useAssetStats'
import { useActiveRun } from '@/hooks/useActiveRun'
import { useCockpitSSE } from '@/hooks/useCockpitSSE'
import type { CockpitEvent } from '@/hooks/useCockpitSSE'
import dynamic from 'next/dynamic'
import { LayerPanel } from './LayerPanel'
import type { AssetWithState } from './LiveDependencyGraph'

// SSE-live substep overlay — fields that come from asset.substep events only
export interface SubstepOverlay {
  actual_rows: number
  substep_index: number
  substep_total: number
  substep_label: string
}

// Instrument pane: the armillary graph (replaces the orbital LiveDependencyGraph).
// LiveDependencyGraph.tsx is retained in place for the AssetWithState type + easy revert.
const InstrumentGraph = dynamic(
  () => import('./ArmillaryGraph').then(m => m.ArmillaryGraph),
  {
    ssr: false,
    loading: () => (
      <div className="w-full h-full flex items-center justify-center text-white/40 text-sm">
        Loading instrument…
      </div>
    ),
  }
)

const LAYER_ORDER = [
  'brahmagyan',
  'ganita',
  'bodha',
  'kala',
  'phala',
  'mimamsa',
] as const

interface Props {
  chartId: string
  /** Called whenever the merged asset+state list changes — used by CockpitShell to drive the header label */
  onAssetsReady?: (assets: AssetWithState[]) => void
}

export function DataAssetsView({ chartId, onAssetsReady }: Props) {
  const { assets, isLoading, error } = useAssetRegistry()
  const { run: activeRun, refresh: refreshRun } = useActiveRun(chartId)
  // Poll at 5s during active builds so the 'building' state window in asset_throughput
  // is actually caught. Without this, stats poll at 30s and always miss the window.
  const { stats, refetch: refetchStats } = useAssetStats({ chartId, isBuilding: activeRun !== null })
  const [focusedAssetId, setFocusedAssetId] = useState<string | null>(null)
  // Bidirectional bond: which asset is hovered anywhere (row or bead). Shared
  // so hovering a row lights the matching bead and vice versa.
  const [hoveredAssetId, setHoveredAssetId] = useState<string | null>(null)
  // Responsive: stack the two panes below a narrow breakpoint.
  const [narrow, setNarrow] = useState(false)
  useEffect(() => {
    const mq = window.matchMedia('(max-width: 900px)')
    const apply = () => setNarrow(mq.matches)
    apply()
    mq.addEventListener('change', apply)
    return () => mq.removeEventListener('change', apply)
  }, [])
  const layerRefs = useRef<Map<string, HTMLDivElement>>(new Map())

  // Live SSE overlay: patches from the orchestrator overwrite stats for DAG rendering
  const [sseOverlay, setSseOverlay] = useState<Map<string, Partial<AssetWithState>>>(new Map())

  // Live substep overlay — separate from sseOverlay so it doesn't pollute AssetWithState
  const [substepOverlay, setSubstepOverlay] = useState<Map<string, SubstepOverlay>>(new Map())

  const handleSSEEvent = useCallback((e: CockpitEvent) => {
    if (e.type === 'asset.state_change') {
      setSseOverlay(prev => {
        const next = new Map(prev)
        // Terminal states: yield immediately to polled stats (count_sql truth).
        // Non-terminal: write the overlay so the bar shows live in-flight state.
        const TERMINAL = e.to_state === 'lit' || e.to_state === 'error' || e.to_state === 'dormant'
        if (TERMINAL) next.delete(e.asset_id)
        else next.set(e.asset_id, { ...prev.get(e.asset_id), state: e.to_state })
        return next
      })
    } else if (e.type === 'asset.progress') {
      setSseOverlay(prev => {
        const next = new Map(prev)
        next.set(e.asset_id, { ...prev.get(e.asset_id), actual_rows: e.rows_written })
        return next
      })
    } else if (e.type === 'asset.substep') {
      setSubstepOverlay(prev => {
        const next = new Map(prev)
        next.set(e.asset_id, {
          actual_rows: e.rows_written,
          substep_index: e.index,
          substep_total: e.total,
          substep_label: e.substep_label,
        })
        return next
      })
    } else if (e.type === 'run.state_change') {
      refreshRun()
      // On run end, clear all overlays so polled stats become the single source of truth,
      // then force an immediate re-poll so the cleared overlay is backfilled at once.
      const RUN_DONE = ['complete', 'failed', 'stopped', 'cancelled'].includes(e.state)
      if (RUN_DONE) {
        setSseOverlay(new Map())
        setSubstepOverlay(new Map())
        refetchStats()
      }
    }
  }, [refreshRun, refetchStats])

  useCockpitSSE(chartId, handleSSEEvent)

  const handleNodeClick = useCallback((assetId: string) => {
    const asset = assets.find(a => a.asset_id === assetId)
    if (!asset) return
    console.log('[DAG] node click:', assetId)
    setFocusedAssetId(assetId)
    // Wait 80ms for forceExpand to open the layer, then scroll to the specific row
    setTimeout(() => {
      const row = document.querySelector(`[data-asset-id="${assetId}"]`)
      row?.scrollIntoView({ behavior: 'smooth', block: 'center' })
    }, 80)
    // Clear highlight after 1.5s
    setTimeout(() => setFocusedAssetId(null), 1500)
  }, [assets])

  // Merge assets + stats + SSE overlay — computed before early returns so the
  // useEffect below can be called unconditionally (Rules of Hooks).
  const assetsWithState: AssetWithState[] = assets.map(a => {
    const s = stats.get(a.asset_id)
    const overlay = sseOverlay.get(a.asset_id)
    return {
      ...a,
      state: overlay?.state ?? s?.state ?? 'dormant',
      last_built_at: s?.last_built_at ?? null,
      actual_rows: overlay?.actual_rows ?? s?.actual_rows ?? null,
    }
  })

  // Notify parent (CockpitShell) whenever the merged state list changes.
  // Must be above early returns — hooks must be called unconditionally.
  useEffect(() => {
    if (assetsWithState.length > 0) {
      onAssetsReady?.(assetsWithState)
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [assetsWithState.map(a => a.state).join(','), assetsWithState.length])

  if (isLoading && assets.length === 0) {
    return (
      <div
        style={{
          padding: '32px 24px',
          color: 'var(--on-dark-mut)',
          fontFamily: 'var(--ui-stack)',
          fontSize: '14px',
        }}
      >
        Loading assets…
      </div>
    )
  }

  if (error) {
    return (
      <div
        style={{
          padding: '32px 24px',
          color: 'var(--marsys-error)',
          fontFamily: 'var(--ui-stack)',
          fontSize: '14px',
        }}
      >
        Failed to load registry: {error}
      </div>
    )
  }

  // Group assets by layer in canonical order
  const byLayer = new Map<string, typeof assets>()
  for (const layer of LAYER_ORDER) byLayer.set(layer, [])

  for (const asset of assets) {
    const bucket = byLayer.get(asset.layer)
    if (bucket) bucket.push(asset)
    else byLayer.set(asset.layer, [asset])
  }

  // Build display order: canonical layers first, then any extras
  const orderedLayers: string[] = [
    ...LAYER_ORDER.filter((l) => (byLayer.get(l)?.length ?? 0) > 0),
    ...[...byLayer.keys()].filter(
      (l) => !LAYER_ORDER.includes(l as (typeof LAYER_ORDER)[number])
    ),
  ]

  // Auto-expand layers that have an active run in scope
  const activeRunPlan: string[] = activeRun?.plan ?? []
  function isLayerExpanded(layer: string): boolean {
    if (!activeRun) return false
    if (activeRun.scope === 'layer' && activeRun.scope_target === layer) return true
    if (activeRun.scope === 'global' && activeRunPlan.some(id => id.startsWith(layer + '.'))) return true
    return false
  }

  // First-run: every asset dormant → the instrument has not been built yet.
  const allDormant = assetsWithState.length > 0 &&
    assetsWithState.every(a => a.state === 'dormant' || a.state === 'not_migrated')

  const fadeMask = 'linear-gradient(180deg, transparent 0, #000 14px, #000 calc(100% - 14px), transparent 100%)'

  return (
    <div style={{ display: 'flex', flexDirection: narrow ? 'column' : 'row', gap: '24px', height: '100%', overflow: narrow ? 'auto' : 'hidden' }}>
      {/* 60% — layer panels: independently scrolls, fade-masked top/bottom */}
      <div
        style={{
          flex: narrow ? '1 1 auto' : '0 0 60%',
          minWidth: 0,
          width: narrow ? '100%' : undefined,
          height: narrow ? 'auto' : '100%',
          overflowY: narrow ? 'visible' : 'auto',
          padding: '8px 0',
          WebkitMaskImage: narrow ? undefined : fadeMask,
          maskImage: narrow ? undefined : fadeMask,
        }}
      >
        {orderedLayers.map((layer) => {
          const layerAssets = byLayer.get(layer) ?? []
          const focusedInLayer = focusedAssetId != null && layerAssets.some(a => a.asset_id === focusedAssetId)
          return (
            <div
              key={layer}
              ref={el => { if (el) layerRefs.current.set(layer, el) }}
            >
              <LayerPanel
                layer={layer}
                assets={layerAssets}
                allAssets={assets}
                stats={stats}
                defaultExpanded={isLayerExpanded(layer)}
                forceExpand={focusedInLayer}
                focusedAssetId={focusedAssetId}
                hoveredAssetId={hoveredAssetId}
                onHover={setHoveredAssetId}
                chartId={chartId}
                activeRun={activeRun}
                substepOverlay={substepOverlay}
                onRunStarted={refreshRun}
              />
            </div>
          )
        })}
      </div>

      {/* 40% — armillary instrument: anchored, does not scroll with left pane */}
      <div
        style={{
          flex: narrow ? '1 1 auto' : '0 0 40%',
          minWidth: 0,
          width: narrow ? '100%' : undefined,
          height: narrow ? '360px' : '100%',
          overflow: 'hidden',
          position: 'relative',
        }}
      >
        <InstrumentGraph
          assets={assetsWithState}
          activeRun={activeRun}
          onNodeClick={handleNodeClick}
          hoveredId={hoveredAssetId}
          onHover={setHoveredAssetId}
        />
        {/* First-run invocation — classical welcome over the dormant cage */}
        {allDormant && (
          <div
            style={{
              position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column',
              alignItems: 'center', justifyContent: 'center', textAlign: 'center',
              pointerEvents: 'none', padding: '24px',
            }}
          >
            <div style={{ fontFamily: 'var(--display-stack)', fontVariant: 'small-caps', color: 'var(--gold-high)', fontSize: '22px', letterSpacing: '0.04em', marginBottom: '6px' }}>
              The instrument awaits
            </div>
            <div style={{ fontFamily: 'var(--ui-stack)', color: 'var(--on-dark-mut)', fontSize: '13px', maxWidth: '34ch', lineHeight: 1.6 }}>
              This chart has not been built. We begin with Brahma Jñāna.
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
