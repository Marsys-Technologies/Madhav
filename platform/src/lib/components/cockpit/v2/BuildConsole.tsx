'use client'

import { useEffect, useState } from 'react'
import type { ActiveRun } from '@/hooks/useActiveRun'
import { PlanBar } from './PlanBar'

// ---------------------------------------------------------------------------
// Layer metadata
// ---------------------------------------------------------------------------

const LAYER_PREFIXES: { prefix: string; name: string; sanskrit: string; color: string }[] = [
  { prefix: 'bg_', name: 'brahmagyan', sanskrit: 'Brahmagyan',  color: '#ECC56A' },
  { prefix: 'ga_', name: 'ganita',     sanskrit: 'Gaṇita',      color: '#D2A23C' },
  { prefix: 'bo_', name: 'bodha',      sanskrit: 'Bodha',        color: '#A87C2A' },
  { prefix: 'ka_', name: 'kala',       sanskrit: 'Kāla',         color: '#8A5E12' },
  { prefix: 'ph_', name: 'phala',      sanskrit: 'Phala',        color: '#B98A2E' },
  { prefix: 'mi_', name: 'mimamsa',    sanskrit: 'Mīmāṃsā',     color: '#6E4E0F' },
]

function layerForAssetId(assetId: string) {
  return LAYER_PREFIXES.find(l => assetId.startsWith(l.prefix)) ?? null
}

function sanskritForScope(scope: string, scopeTarget: string | null): string {
  if (scope === 'layer' && scopeTarget) {
    const hit = LAYER_PREFIXES.find(l => l.name === scopeTarget || l.prefix === scopeTarget + '_')
    return hit ? hit.sanskrit : scopeTarget
  }
  return ''
}

// ---------------------------------------------------------------------------
// Elapsed timer helper
// ---------------------------------------------------------------------------

function formatElapsed(startedAt: string | null): string {
  if (!startedAt) return '00:00'
  const ms = Math.max(0, Date.now() - new Date(startedAt).getTime())
  const totalSecs = Math.floor(ms / 1000)
  const mm = Math.floor(totalSecs / 60).toString().padStart(2, '0')
  const ss = (totalSecs % 60).toString().padStart(2, '0')
  return `${mm}:${ss}`
}

// ---------------------------------------------------------------------------
// Scope chip label
// ---------------------------------------------------------------------------

function scopeChipLabel(
  scope: string,
  scopeTarget: string | null,
  planLength: number,
): string {
  if (scope === 'global') return 'Full chart'
  if (scope === 'layer') {
    const sanskrit = sanskritForScope(scope, scopeTarget)
    return `${sanskrit || scopeTarget} layer only`
  }
  if (scope === 'asset') {
    const downstream = planLength - 1
    if (!scopeTarget) return 'Asset'
    return downstream > 0 ? `${scopeTarget} + ${downstream} downstream` : scopeTarget
  }
  return scope
}

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

export interface BuildConsoleProps {
  activeRun: ActiveRun | null
  assets: { asset_id: string; state: string }[]
  isBuilding: boolean
  sidecarHealthy: boolean | null
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function SidecarDot({ healthy }: { healthy: boolean | null }) {
  const color =
    healthy === true  ? 'var(--color-ok, #4caf50)' :
    healthy === false ? 'var(--color-error, #e53935)' :
                        'var(--color-muted, #555)'
  return (
    <span
      title={healthy === null ? 'Sidecar unknown' : healthy ? 'Sidecar healthy' : 'Sidecar unreachable'}
      style={{
        display: 'inline-block',
        width: 6,
        height: 6,
        borderRadius: '50%',
        background: color,
        flexShrink: 0,
      }}
    />
  )
}

// Mini per-layer segment bar shown in idle state
function LayerMiniBar({ assets }: { assets: { asset_id: string; state: string }[] }) {
  // Determine which layers have any assets, and how many are "done"
  const layerStats = LAYER_PREFIXES.map(layer => {
    const layerAssets = assets.filter(a => a.asset_id.startsWith(layer.prefix))
    const done = layerAssets.filter(a => a.state === 'complete' || a.state === 'done').length
    return { ...layer, total: layerAssets.length, done }
  }).filter(l => l.total > 0)

  if (layerStats.length === 0) return null

  return (
    <div style={{ display: 'flex', gap: 3, alignItems: 'center' }}>
      {layerStats.map(l => {
        const fullyLit = l.total > 0 && l.done === l.total
        return (
          <div
            key={l.name}
            title={`${l.sanskrit}: ${l.done}/${l.total}`}
            style={{
              width: 18,
              height: 6,
              borderRadius: 2,
              background: fullyLit ? l.color : 'var(--surface-3, #2a2a2a)',
              border: fullyLit ? 'none' : '1px solid var(--border-subtle, #333)',
              transition: 'background 0.3s',
            }}
          />
        )
      })}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export function BuildConsole({ activeRun, assets, isBuilding, sidecarHealthy }: BuildConsoleProps) {
  const [elapsed, setElapsed] = useState<string>('00:00')

  // Tick elapsed every second when building
  useEffect(() => {
    if (!isBuilding || !activeRun?.started_at) {
      setElapsed('00:00')
      return
    }
    setElapsed(formatElapsed(activeRun.started_at))
    const t = setInterval(() => {
      setElapsed(formatElapsed(activeRun.started_at))
    }, 1000)
    return () => clearInterval(t)
  }, [isBuilding, activeRun?.started_at])

  // Asset counts for building state
  const planAssets = activeRun?.plan ?? []
  const doneAssets = assets.filter(
    a => a.state === 'complete' || a.state === 'done'
  ).length
  const totalAssets = planAssets.length

  // Idle state metrics
  const totalComplete = assets.filter(a => a.state === 'complete' || a.state === 'done').length
  const totalAll = assets.length
  const overallPct = totalAll > 0 ? Math.round((totalComplete / totalAll) * 100) : 0

  const liveLayers = LAYER_PREFIXES.filter(l =>
    assets.some(a => a.asset_id.startsWith(l.prefix))
  ).length
  const totalLayers = LAYER_PREFIXES.length

  // Scope chip text
  const chipLabel = activeRun
    ? scopeChipLabel(activeRun.scope, activeRun.scope_target, activeRun.plan.length)
    : ''

  // Shared container style
  const containerStyle: React.CSSProperties = {
    fontFamily: 'var(--mono-stack, "JetBrains Mono", "Fira Mono", monospace)',
    background: 'var(--surface-1, #141414)',
    border: '1px solid var(--border-subtle, #2e2e2e)',
    borderRadius: 8,
    padding: '12px 16px',
    display: 'flex',
    flexDirection: 'column',
    gap: 10,
    minHeight: 64,
  }

  // ── BUILDING STATE ──────────────────────────────────────────────────────
  if (isBuilding && activeRun) {
    return (
      <div style={containerStyle}>
        {/* Row 1: status + sidecar dot */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            {/* Pulsing gold dot */}
            <span
              className="obs-live-pulse"
              style={{
                display: 'inline-block',
                width: 8,
                height: 8,
                borderRadius: '50%',
                background: 'var(--gold-mid, #D2A23C)',
                flexShrink: 0,
              }}
            />
            <span
              style={{
                fontSize: 12,
                fontWeight: 600,
                color: 'var(--gold-mid, #D2A23C)',
                letterSpacing: '0.06em',
                textTransform: 'uppercase',
              }}
            >
              Building
            </span>

            {/* Scope chip */}
            <span
              style={{
                fontSize: 10,
                color: 'var(--text-muted, #888)',
                background: 'var(--surface-2, #1e1e1e)',
                border: '1px solid var(--border-subtle, #2e2e2e)',
                borderRadius: 4,
                padding: '1px 6px',
                letterSpacing: '0.03em',
              }}
            >
              {chipLabel}
            </span>
          </div>

          <SidecarDot healthy={sidecarHealthy} />
        </div>

        {/* Row 2: elapsed + asset count */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 4 }}>
            <span style={{ fontSize: 10, color: 'var(--text-muted, #666)', letterSpacing: '0.05em' }}>
              ELAPSED
            </span>
            <span
              style={{
                fontSize: 13,
                color: 'var(--text-primary, #e8e8e8)',
                fontVariantNumeric: 'tabular-nums',
                letterSpacing: '0.04em',
              }}
            >
              {elapsed}
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'baseline', gap: 4 }}>
            <span style={{ fontSize: 10, color: 'var(--text-muted, #666)', letterSpacing: '0.05em' }}>
              ASSETS
            </span>
            <span
              style={{
                fontSize: 13,
                color: 'var(--text-primary, #e8e8e8)',
                fontVariantNumeric: 'tabular-nums',
              }}
            >
              {doneAssets}
              <span style={{ color: 'var(--text-muted, #666)' }}>/{totalAssets}</span>
            </span>
          </div>
        </div>

        {/* PlanBar */}
        <PlanBar
          plan={activeRun.plan}
          currentAssetId={activeRun.current_asset_id}
          assetStateMap={new Map(assets.map(a => [a.asset_id, a.state]))}
        />
      </div>
    )
  }

  // ── IDLE STATE ──────────────────────────────────────────────────────────
  return (
    <div style={containerStyle}>
      {/* Row 1: status label + sidecar dot */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span
            style={{
              display: 'inline-block',
              width: 8,
              height: 8,
              borderRadius: '50%',
              background: 'var(--text-muted, #555)',
              flexShrink: 0,
            }}
          />
          <span
            style={{
              fontSize: 12,
              fontWeight: 600,
              color: 'var(--text-muted, #666)',
              letterSpacing: '0.06em',
              textTransform: 'uppercase',
            }}
          >
            Idle
          </span>
        </div>
        <SidecarDot healthy={sidecarHealthy} />
      </div>

      {/* Row 2: layer mini-bar + counts */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <LayerMiniBar assets={assets} />

        <span
          style={{
            fontSize: 10,
            color: 'var(--text-muted, #666)',
            letterSpacing: '0.04em',
            whiteSpace: 'nowrap',
          }}
        >
          {liveLayers}/{totalLayers} layers
        </span>

        <span
          style={{
            fontSize: 10,
            color: 'var(--text-muted, #666)',
            letterSpacing: '0.04em',
            marginLeft: 'auto',
          }}
        >
          {overallPct}% complete
        </span>
      </div>
    </div>
  )
}

export default BuildConsole
