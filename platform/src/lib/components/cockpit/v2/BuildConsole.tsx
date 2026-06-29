'use client'

import { useEffect, useState } from 'react'
import type { ActiveRun } from '@/hooks/useActiveRun'
import { PlanBar } from './PlanBar'

// ---------------------------------------------------------------------------
// Layer metadata
// ---------------------------------------------------------------------------

const LAYER_PREFIXES: { prefix: string; name: string; sanskrit: string; color: string }[] = [
  { prefix: 'bg_', name: 'brahmagyan', sanskrit: 'Brahma Jñāna', color: '#ECC56A' },
  { prefix: 'ga_', name: 'ganita',     sanskrit: 'Gaṇita',       color: '#D2A23C' },
  { prefix: 'bo_', name: 'bodha',      sanskrit: 'Bodha',        color: '#A87C2A' },
  { prefix: 'ka_', name: 'kala',       sanskrit: 'Kāla',         color: '#8A5E12' },
  { prefix: 'ph_', name: 'phala',      sanskrit: 'Phala',        color: '#B98A2E' },
  { prefix: 'mi_', name: 'mimamsa',    sanskrit: 'Mīmāṃsā',     color: '#6E4E0F' },
]

// State is 'lit' or 'service_ok' — not 'complete'/'done' (those don't exist in this project)
function isLit(state: string) {
  return state === 'lit' || state === 'service_ok'
}

function formatElapsed(startedAt: string | null): string {
  if (!startedAt) return '00:00'
  const ms = Math.max(0, Date.now() - new Date(startedAt).getTime())
  const totalSecs = Math.floor(ms / 1000)
  const mm = Math.floor(totalSecs / 60).toString().padStart(2, '0')
  const ss = (totalSecs % 60).toString().padStart(2, '0')
  return `${mm}:${ss}`
}

function scopeChipLabel(scope: string, scopeTarget: string | null, planLength: number): string {
  if (scope === 'global') return 'Full chart'
  if (scope === 'layer') {
    const hit = LAYER_PREFIXES.find(l => l.name === scopeTarget)
    return `${hit?.sanskrit ?? scopeTarget} layer only`
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
    healthy === true  ? '#4caf50' :
    healthy === false ? 'var(--marsys-error, #B5474C)' :
                        'rgba(255,255,255,0.2)'
  const glow = healthy === true ? '0 0 5px rgba(76,175,80,0.5)' : 'none'
  return (
    <span
      title={healthy === null ? 'Sidecar: checking…' : healthy ? 'Sidecar: healthy' : 'Sidecar: unreachable'}
      style={{
        display: 'inline-block',
        width: 6,
        height: 6,
        borderRadius: '50%',
        background: color,
        boxShadow: glow,
        flexShrink: 0,
      }}
    />
  )
}

// Per-layer completion mini-segments (idle state)
function LayerMiniBar({ assets }: { assets: { asset_id: string; state: string }[] }) {
  const layerStats = LAYER_PREFIXES.map(layer => {
    const layerAssets = assets.filter(a => a.asset_id.startsWith(layer.prefix))
    const done = layerAssets.filter(a => isLit(a.state)).length
    return { ...layer, total: layerAssets.length, done }
  }).filter(l => l.total > 0)

  if (layerStats.length === 0) return null

  return (
    <div style={{ display: 'flex', gap: 2, alignItems: 'center' }}>
      {layerStats.map(l => {
        const fullyLit = l.total > 0 && l.done === l.total
        const partiallyLit = !fullyLit && l.done > 0
        return (
          <div
            key={l.name}
            title={`${l.sanskrit}: ${l.done}/${l.total}`}
            style={{
              width: 16,
              height: 5,
              borderRadius: 2,
              background: fullyLit
                ? l.color
                : partiallyLit
                  ? l.color + '55'
                  : 'rgba(122,86,24,0.15)',
              border: `1px solid ${fullyLit ? l.color + '88' : 'rgba(122,86,24,0.25)'}`,
              transition: 'background 0.4s ease',
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

  useEffect(() => {
    if (!isBuilding || !activeRun?.started_at) {
      setElapsed('00:00')
      return
    }
    setElapsed(formatElapsed(activeRun.started_at))
    const t = setInterval(() => setElapsed(formatElapsed(activeRun.started_at)), 1000)
    return () => clearInterval(t)
  }, [isBuilding, activeRun?.started_at])

  // Metrics
  const planAssets = activeRun?.plan ?? []
  const litAssets = assets.filter(a => isLit(a.state)).length
  const planDone = planAssets.filter(id => isLit(assets.find(a => a.asset_id === id)?.state ?? '')).length

  const totalAll = assets.length
  const overallPct = totalAll > 0 ? Math.round((litAssets / totalAll) * 100) : 0

  const liveLayers = LAYER_PREFIXES.filter(l =>
    assets.some(a => a.asset_id.startsWith(l.prefix))
  )
  const litLayerCount = liveLayers.filter(l =>
    assets.filter(a => a.asset_id.startsWith(l.prefix)).every(a => isLit(a.state))
  ).length

  const chipLabel = activeRun
    ? scopeChipLabel(activeRun.scope, activeRun.scope_target, activeRun.plan.length)
    : ''

  // Shared container — Marsys dark theme tokens, hairline separator from name row above
  const containerStyle: React.CSSProperties = {
    fontFamily: 'var(--mono-stack)',
    background: 'rgba(10,8,6,0.45)',
    border: '1px solid var(--black-line)',
    borderRadius: 'var(--r-btn, 6px)',
    padding: '6px 12px',
    marginTop: 8,
  }

  // ── BUILDING STATE ──────────────────────────────────────────────────────
  if (isBuilding && activeRun) {
    return (
      <div style={containerStyle}>
        {/* Single row: pulsing dot + Building + scope chip ·· elapsed + assets + sidecar */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
          {/* Left cluster */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 7, flex: 1, minWidth: 0 }}>
            <span style={{
              display: 'inline-block', width: 7, height: 7, borderRadius: '50%',
              background: '#ECC56A',
              boxShadow: '0 0 6px rgba(236,197,106,0.6)',
              animation: 'obs-live-pulse 1.4s ease-in-out infinite',
              flexShrink: 0,
            }} />
            <span style={{ fontSize: 11, fontWeight: 600, color: 'var(--gold-high)', letterSpacing: '0.06em', textTransform: 'uppercase' }}>
              Building
            </span>
            <span style={{
              fontSize: 9.5, color: 'var(--on-dark-mut)',
              background: 'rgba(168,124,42,0.12)',
              border: '1px solid rgba(168,124,42,0.25)',
              borderRadius: 10, padding: '1px 7px',
              letterSpacing: '0.03em', whiteSpace: 'nowrap',
            }}>
              {chipLabel}
            </span>
          </div>
          {/* Right cluster */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexShrink: 0 }}>
            <span style={{ fontSize: 10, color: 'var(--on-dark-faint)', letterSpacing: '0.04em' }}>
              <span style={{ fontSize: 8, textTransform: 'uppercase', marginRight: 3 }}>Elapsed</span>
              <span style={{ color: 'var(--on-dark-mut)', fontVariantNumeric: 'tabular-nums' }}>{elapsed}</span>
            </span>
            <span style={{ fontSize: 10, color: 'var(--on-dark-faint)', letterSpacing: '0.04em' }}>
              <span style={{ fontSize: 8, textTransform: 'uppercase', marginRight: 3 }}>Assets</span>
              <span style={{ color: 'var(--gold-high)', fontWeight: 600 }}>{planDone}</span>
              <span style={{ color: 'var(--on-dark-faint)' }}>/{planAssets.length}</span>
            </span>
            <SidecarDot healthy={sidecarHealthy} />
          </div>
        </div>
        {/* Plan bar — below the single row */}
        <div style={{ marginTop: 7 }}>
          <PlanBar
            plan={activeRun.plan}
            currentAssetId={activeRun.current_asset_id}
            assetStateMap={new Map(assets.map(a => [a.asset_id, a.state]))}
          />
        </div>
      </div>
    )
  }

  // ── IDLE STATE — single compact row ─────────────────────────────────────
  return (
    <div style={containerStyle}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        {/* Left: idle label + mini-bars + layer count */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flex: 1, minWidth: 0 }}>
          <span style={{
            fontSize: 9.5, fontWeight: 600, letterSpacing: '0.08em', textTransform: 'uppercase',
            color: 'var(--on-dark-faint)',
          }}>
            Idle
          </span>
          <span style={{ width: 1, height: 10, background: 'rgba(255,255,255,0.1)', flexShrink: 0 }} />
          <LayerMiniBar assets={assets} />
          <span style={{ fontSize: 9.5, color: 'var(--on-dark-faint)', whiteSpace: 'nowrap' }}>
            <span style={{ color: 'var(--on-dark-mut)' }}>{litLayerCount}</span>
            {' / '}{liveLayers.length} layers live
          </span>
        </div>
        {/* Right: sidecar dot + complete % */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexShrink: 0 }}>
          <SidecarDot healthy={sidecarHealthy} />
          <span style={{ fontSize: 9.5, color: 'var(--on-dark-faint)', whiteSpace: 'nowrap' }}>
            <span style={{ color: 'var(--on-dark-mut)', fontVariantNumeric: 'tabular-nums' }}>{overallPct}%</span>
            {' complete'}
          </span>
        </div>
      </div>
    </div>
  )
}

export default BuildConsole
