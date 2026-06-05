'use client'

/**
 * LayerTower — Bottom-up layer visualization for the Brahma build cockpit.
 *
 * Renders L0 (Brahmagyan) at bottom, L5 (Mīmāṃsā) at top.
 * L0 = bedrock styling (always visible, solid foundation).
 * L5 = always-active "listening" state even when not-built.
 *
 * StatusChip colors:
 *   built      = green
 *   building   = amber + pulse animation
 *   not-built  = gray
 *   not_started= gray
 *   failed     = red
 *   attention  = orange
 *
 * PipRail = one colored dot per asset, animate fill left-to-right on change.
 *
 * WS-1-S3-B: onConsultClick prop — "Consult now (Gaṇita)" affordance on L1
 * band when status === 'built'.
 */

import { useCallback } from 'react'

export type LayerStatus = 'built' | 'building' | 'failed' | 'attention' | 'not-built' | 'not_started'

export interface Asset {
  asset_key: string
  status: LayerStatus
}

export interface Layer {
  layer: string
  name: string
  status: LayerStatus
  asset_count: number
  assets: Asset[]
}

interface LayerTowerProps {
  layers: Layer[]
  /** Called when a pip is clicked; receives the asset_key */
  onAssetClick?: (assetKey: string) => void
  /** Currently selected asset key */
  selectedAsset?: string | null
  /**
   * WS-1-S3-B: When provided, renders a "Consult now (Gaṇita)" button on the
   * L1 band when L1 status === 'built'. The callback receives the chart ID.
   */
  onConsultClick?: () => void
}

// ── Status chip ────────────────────────────────────────────────────────────────

const STATUS_CHIP_CLASSES: Record<string, string> = {
  built: 'bg-emerald-100 text-emerald-800 border border-emerald-300',
  building: 'bg-amber-100 text-amber-800 border border-amber-300 animate-pulse',
  failed: 'bg-red-100 text-red-800 border border-red-300',
  attention: 'bg-orange-100 text-orange-800 border border-orange-300',
  'not-built': 'bg-gray-100 text-gray-500 border border-gray-200',
  not_started: 'bg-gray-100 text-gray-500 border border-gray-200',
}

const STATUS_LABELS: Record<string, string> = {
  built: 'built',
  building: 'building…',
  failed: 'failed',
  attention: 'attention',
  'not-built': 'not built',
  not_started: 'not built',
}

function StatusChip({ status }: { status: LayerStatus }) {
  const cls = STATUS_CHIP_CLASSES[status] ?? STATUS_CHIP_CLASSES['not-built']
  const label = STATUS_LABELS[status] ?? 'not built'
  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${cls}`}
      role="status"
      aria-label={label}
    >
      {label}
    </span>
  )
}

// ── Pip colors ─────────────────────────────────────────────────────────────────

const PIP_CLASSES: Record<string, string> = {
  built: 'bg-emerald-500',
  building: 'bg-amber-400 animate-pulse',
  failed: 'bg-red-500',
  attention: 'bg-orange-400',
  'not-built': 'bg-gray-300',
  not_started: 'bg-gray-300',
}

function PipRail({
  assets,
  onPipClick,
  selectedAsset,
}: {
  assets: Asset[]
  onPipClick?: (assetKey: string) => void
  selectedAsset?: string | null
}) {
  if (!assets.length) {
    return <span className="text-xs text-gray-400 italic">no assets</span>
  }
  return (
    <div className="flex flex-wrap gap-1" role="list" aria-label="asset pips">
      {assets.map((a) => {
        const pipCls = PIP_CLASSES[a.status] ?? PIP_CLASSES['not-built']
        const isSelected = selectedAsset === a.asset_key
        return (
          <button
            key={a.asset_key}
            role="listitem"
            title={`${a.asset_key}: ${a.status}`}
            aria-label={`${a.asset_key} ${a.status}`}
            aria-pressed={isSelected}
            onClick={() => onPipClick?.(a.asset_key)}
            className={[
              'h-3 w-3 rounded-full transition-all duration-300',
              pipCls,
              isSelected ? 'ring-2 ring-offset-1 ring-blue-500 scale-125' : '',
              onPipClick ? 'cursor-pointer hover:scale-110' : 'cursor-default',
            ].join(' ')}
          />
        )
      })}
    </div>
  )
}

// ── Layer band ─────────────────────────────────────────────────────────────────

function LayerBand({
  layer,
  isBedrock,
  isAlwaysActive,
  onAssetClick,
  selectedAsset,
  onConsultClick,
}: {
  layer: Layer
  isBedrock: boolean
  isAlwaysActive: boolean
  onAssetClick?: (assetKey: string) => void
  selectedAsset?: string | null
  /** WS-1-S3-B: shown on L1 band when status==='built' */
  onConsultClick?: () => void
}) {
  // Normalise status for display (L5 always shows "listening" if not built)
  const displayStatus: LayerStatus =
    isAlwaysActive && (layer.status === 'not-built' || layer.status === 'not_started')
      ? 'building'
      : layer.status

  const bandBase =
    'flex items-center gap-3 rounded-lg px-4 py-3 transition-colors duration-300'

  const bandVariant = isBedrock
    ? 'bg-indigo-950 border border-indigo-700 text-white shadow-lg'
    : isAlwaysActive
      ? 'bg-violet-50 border border-violet-200 text-gray-800'
      : 'bg-white border border-gray-200 text-gray-800 hover:bg-gray-50'

  return (
    <div
      className={`${bandBase} ${bandVariant}`}
      data-testid={`layer-band-${layer.layer.toLowerCase()}`}
      data-layer={layer.layer}
      data-status={layer.status}
    >
      {/* Layer label */}
      <div className="min-w-[140px]">
        <span className={`font-semibold text-sm ${isBedrock ? 'text-indigo-100' : 'text-gray-900'}`}>
          {layer.name}
        </span>
        <div className={`text-xs mt-0.5 ${isBedrock ? 'text-indigo-300' : 'text-gray-500'}`}>
          {layer.layer}
          {isAlwaysActive && layer.status !== 'built' ? ' · listening' : ''}
          {isBedrock ? ' · bedrock' : ''}
        </div>
      </div>

      {/* Status chip */}
      <StatusChip status={displayStatus} />

      {/* Asset count */}
      <span
        className={`text-xs tabular-nums ${isBedrock ? 'text-indigo-300' : 'text-gray-400'}`}
        aria-label={`${layer.asset_count} assets`}
      >
        {layer.asset_count} {layer.asset_count === 1 ? 'asset' : 'assets'}
      </span>

      {/* Pip rail */}
      <div className="flex-1">
        <PipRail assets={layer.assets} onPipClick={onAssetClick} selectedAsset={selectedAsset} />
      </div>

      {/* WS-1-S3-B: "Consult now (Gaṇita)" affordance — L1 band only, built status only */}
      {layer.layer === 'L1' && layer.status === 'built' && onConsultClick && (
        <button
          type="button"
          onClick={onConsultClick}
          className="ml-2 shrink-0 inline-flex items-center gap-1.5 rounded-md bg-emerald-600 px-3 py-1.5 text-xs font-semibold text-white shadow-sm hover:bg-emerald-700 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-1 transition-colors"
          data-testid="consult-now-btn"
          aria-label="Consult now — Gaṇita layer is built"
        >
          Consult now (Gaṇita)
        </button>
      )}
    </div>
  )
}

// ── LayerTower ─────────────────────────────────────────────────────────────────

export function LayerTower({ layers, onAssetClick, selectedAsset, onConsultClick }: LayerTowerProps) {
  const handlePipClick = useCallback(
    (assetKey: string) => {
      onAssetClick?.(assetKey)
    },
    [onAssetClick],
  )

  if (!layers.length) {
    return (
      <div className="rounded-lg border border-gray-200 p-6 text-center text-sm text-gray-500">
        No layer data available
      </div>
    )
  }

  // Render bottom-up: L0 at bottom, L5 at top
  // CSS flex-col-reverse or manual ordering via [...].reverse()
  const orderedLayers = [...layers].reverse()

  return (
    <div
      className="flex flex-col gap-2"
      data-testid="layer-tower"
      role="region"
      aria-label="Build layer tower"
    >
      {orderedLayers.map((layer) => {
        const isBedrock = layer.layer === 'L0'
        const isAlwaysActive = layer.layer === 'L5'
        return (
          <LayerBand
            key={layer.layer}
            layer={layer}
            isBedrock={isBedrock}
            isAlwaysActive={isAlwaysActive}
            onAssetClick={handlePipClick}
            selectedAsset={selectedAsset}
            onConsultClick={onConsultClick}
          />
        )
      })}
    </div>
  )
}
