'use client'

import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Trash2 } from 'lucide-react'
import { formatDate } from '@/lib/utils/date'
import { useCockpitStatus } from '@/hooks/useCockpitStatus'
import { BuildActionButton } from './BuildActionButton'
import { RefreshIconButton } from './RefreshIconButton'
import { StopIconButton } from './StopIconButton'
import type { ActiveRun } from '@/hooks/useActiveRun'

// Sun-node mark — the brand's sanctioned sacred-geometry glyph (replaces the
// uncontrolled ◆ Unicode lozenge). A small 4-point star drawn at 1px stroke,
// same hand as the TabBar icons.
function SunNode({ size = 9 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1" strokeLinejoin="round" aria-hidden="true">
      <path d="M6 0.5 L7.2 4.8 L11.5 6 L7.2 7.2 L6 11.5 L4.8 7.2 L0.5 6 L4.8 4.8 Z" />
    </svg>
  )
}

/** Format pg TIME string "HH:MM:SS" → "HH:MM" (24-hour) */
function formatBirthTime(t: string | null | undefined): string {
  if (!t) return ''
  const parts = t.split(':')
  return parts.length >= 2 ? `${parts[0]}:${parts[1]}` : t
}

function deriveGlobalLabel(assets: { state: string }[]): 'Build' | 'Rebuild' {
  const total = assets.length
  if (total === 0) return 'Build'
  const dormant = assets.filter(a => a.state === 'dormant' || a.state === 'not_migrated').length
  if (dormant === total) return 'Build'
  return 'Rebuild'
}

interface Props {
  chartId: string
  chartName?: string | null
  birthDate?: string | null
  birthTime?: string | null
  birthPlace?: string | null
  assets?: { asset_id: string; state: string }[]
  /** Task 1: active run lifted from CockpitShell — no longer fetched here */
  activeRun?: ActiveRun | null
  /** Task 1: isBuilding flag (activeRun !== null) lifted from CockpitShell */
  isBuilding?: boolean
  /** Task 7: count of assets currently in error state — shown as badge when > 0 */
  errorCount?: number
  proMode?: boolean
  onProModeToggle?: () => void
  onGlobalClear?: () => void
  onGlobalRebuild?: () => void
  onRefreshed?: () => void
  /** Task 1: callback to refresh the active run (was `refreshRun` inside this component) */
  onRunRefresh?: () => void
  /** 'card' = standalone bordered card (default). 'inline' = compact, no card
   *  chrome — sits at the top of the scrolling ledger column. */
  variant?: 'card' | 'inline'
}

export function CockpitHeader({
  chartId,
  chartName,
  birthDate,
  birthTime,
  birthPlace,
  assets = [],
  activeRun = null,
  isBuilding = false,
  errorCount = 0,
  proMode = false,
  variant = 'card',
  onProModeToggle,
  onGlobalClear,
  onGlobalRebuild,
  onRefreshed,
  onRunRefresh,
}: Props) {
  const [sidecarHealthy, setSidecarHealthy] = useState<boolean | null>(null)
  // Task 1: useActiveRun removed — activeRun + isBuilding received as props from CockpitShell

  useEffect(() => {
    const check = async () => {
      try {
        const r = await fetch('/api/sidecar/health', {
          credentials: 'include',
          cache: 'no-store',
        })
        const body = await r.json()
        setSidecarHealthy(!!body.healthy)
      } catch {
        setSidecarHealthy(false)
      }
    }
    check()
    const t = setInterval(check, 30_000)
    return () => clearInterval(t)
  }, [])

  const sidecarLabel = sidecarHealthy === null ? '…' : sidecarHealthy ? 'OK' : 'DOWN'
  const cockpitStatus = useCockpitStatus()

  const globalRunId = activeRun?.id ?? null
  const globalRunPaused = activeRun?.state === 'paused'

  const dormantCount = assets.filter(a => a.state === 'dormant' || a.state === 'not_migrated').length
  const staleCount = assets.filter(a => a.state === 'stale').length

  // B2: global progress bar — only shown during an active run
  const assetStateMap = new Map(assets.map(a => [a.asset_id, a.state]))
  const planIds = activeRun?.plan ?? []
  const planTotal = planIds.length
  const planLit = planIds.filter(id => assetStateMap.get(id) === 'lit').length
  const globalProgressPct = planTotal > 0 ? Math.min((planLit / planTotal) * 100, 100) : 0
  const showGlobalBar = globalRunId != null && planTotal > 0

  // Subtitle: date · time · place — only show parts that are available
  const datePart = formatDate(birthDate) || null
  const timePart = formatBirthTime(birthTime) || null
  const placePart = birthPlace ?? null
  const subtitleParts = [datePart, timePart, placePart].filter(Boolean)
  const subtitle = subtitleParts.join(' · ')

  const inline = variant === 'inline'

  return (
    <div
      style={inline ? {
        // compact: no card chrome, hairline divider below; lives at top of the ledger
        padding: '0 0 12px 0',
        margin: '0 0 10px 0',
        borderBottom: '1px solid var(--black-line)',
      } : {
        background: 'var(--black-raised)',
        border: '1px solid var(--black-line)',
        borderRadius: 'var(--r-card)',
        padding: '20px 24px',
        margin: '0 0 8px 0',
      }}
    >
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        {/* Left: chart name + pro pill + date/time/location */}
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <h1
              style={{
                fontFamily: 'var(--display-stack)',
                color: 'var(--gold-high)',
                fontSize: '20px',
                fontVariant: 'small-caps',
                margin: 0,
              }}
            >
              {chartName ?? 'Loading chart…'}
            </h1>
            <button
              onClick={onProModeToggle}
              aria-pressed={proMode}
              data-icon-btn
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '4px',
                padding: '2px 8px',
                borderRadius: '12px',
                background: proMode ? 'color-mix(in srgb, var(--gold-core) 26%, transparent)' : 'color-mix(in srgb, var(--gold-core) 10%, transparent)',
                border: `1px solid ${proMode ? 'var(--gold-engrave)' : 'color-mix(in srgb, var(--gold-core) 35%, transparent)'}`,
                color: proMode ? 'var(--gold-bright)' : 'var(--on-dark-faint)',
                fontSize: '10px',
                fontFamily: 'var(--ui-stack)',
                fontWeight: 600,
                letterSpacing: '0.05em',
                cursor: 'pointer',
                transition: 'all 0.15s',
                whiteSpace: 'nowrap',
              }}
            >
              <SunNode /> Pro
            </button>
          </div>
          {subtitle && (
            <div
              style={{
                fontFamily: 'var(--ui-stack)',
                fontSize: '12px',
                color: 'var(--on-dark-mut)',
                marginTop: '3px',
              }}
            >
              {subtitle}
            </div>
          )}
        </div>

        {/* Right: [error badge] [Build/Rebuild] [Refresh] [Stop | Delete] */}
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>

          {/* Task 7: run-level error badge — appears when run=completed but assets errored */}
          {!isBuilding && errorCount > 0 && (
            <div
              className="flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-mono"
              style={{
                background: 'rgba(181, 71, 76, 0.12)',
                border: '1px solid rgba(181, 71, 76, 0.35)',
                color: 'var(--danger, #e89a9a)',
                letterSpacing: '0.06em',
              }}
            >
              <span style={{ color: 'var(--marsys-error, #B5474C)' }}>&#9873;</span>
              {errorCount} {errorCount === 1 ? 'asset' : 'assets'} failed
            </div>
          )}

          {/* Build/Rebuild — hidden when a run is active */}
          {!globalRunId && (
            <BuildActionButton
              chartId={chartId}
              scope="global"
              scopeTarget={null}
              stats={{
                total: assets.length || 1,
                dormant: dormantCount,
                stale: staleCount,
                active_run_id: null,
                is_paused: false,
              }}
              onRunStarted={onRunRefresh}
              onRunStateChange={onRunRefresh}
              onRebuildOverride={deriveGlobalLabel(assets) === 'Rebuild' ? onGlobalRebuild : undefined}
            />
          )}

          {/* Refresh — always visible */}
          <RefreshIconButton
            chartId={chartId}
            scope="global"
            size={28}
            onRefreshed={onRefreshed}
          />

          {/* Stop (when running) or Delete (when idle) */}
          {globalRunId ? (
            <StopIconButton runId={globalRunId} size={28} onStopped={onRunRefresh} />
          ) : (
            <button
              title="Clear instrument"
              onClick={() => onGlobalClear?.()}
              data-icon-btn
              className="w-[28px] h-[28px] flex items-center justify-center rounded text-white/40 transition-colors"
              onMouseEnter={e => {
                e.currentTarget.style.color = 'var(--marsys-error)'
                e.currentTarget.style.background = 'color-mix(in srgb, var(--marsys-error) 16%, transparent)'
              }}
              onMouseLeave={e => {
                e.currentTarget.style.color = ''
                e.currentTarget.style.background = 'transparent'
              }}
            >
              <Trash2 size={15} />
            </button>
          )}
        </div>
      </div>

      {/* Telemetry strip — instrument readout; announces BUILD/SIDECAR changes */}
      <div
        aria-live="polite"
        style={{
          marginTop: '12px',
          display: 'flex',
          gap: '16px',
          fontSize: '11px',
          color: 'var(--on-dark-faint)',
          fontFamily: 'var(--mono-stack)',
          flexWrap: 'wrap',
        }}
      >
        {([
          ['WRITERS', String(cockpitStatus.writers ?? '…')],
          ['QUEUE',   String(cockpitStatus.queue   ?? '…')],
          ['BUILD',   String(cockpitStatus.build   ?? '…')],
          ['SIDECAR', sidecarLabel],
        ] as [string, string][]).map(([k, v]) => {
          const buildRunning = k === 'BUILD' && v === 'running'
          const sidecarDown = k === 'SIDECAR' && v === 'DOWN'
          const lampColor = buildRunning ? 'var(--gold-high)' : sidecarDown ? 'var(--marsys-error)' : null
          return (
            <span key={k} style={{ display: 'inline-flex', alignItems: 'center', gap: '5px' }}>
              <span style={{ textTransform: 'uppercase', fontSize: '9.5px', letterSpacing: '0.08em' }}>
                {k}
              </span>
              {lampColor && (
                <span
                  aria-hidden
                  style={{
                    width: '5px', height: '5px', borderRadius: '50%', background: lampColor,
                    boxShadow: `0 0 5px ${lampColor}`,
                    animation: buildRunning ? 'obs-live-pulse 1.4s ease-in-out infinite' : undefined,
                  }}
                />
              )}
              <span style={{
                color: buildRunning ? 'var(--gold-high)'
                     : sidecarDown ? 'var(--marsys-error)'
                     : 'var(--on-dark)',
              }}>
                {v}
              </span>
            </span>
          )
        })}
      </div>

      {/* B2: Overall run progress bar — visible only during an active build run */}
      <AnimatePresence>
        {showGlobalBar && (
          <motion.div
            key="global-progress"
            initial={{ opacity: 0, height: 0, marginTop: 0 }}
            animate={{ opacity: 1, height: 'auto', marginTop: 10 }}
            exit={{ opacity: 0, height: 0, marginTop: 0 }}
            transition={{ duration: 0.25, ease: [0.16, 1, 0.3, 1] }}
            style={{ overflow: 'hidden' }}
          >
            <div style={{ position: 'relative', height: '6px', borderRadius: '3px', background: 'rgba(122,86,24,0.25)', border: '1px solid rgba(122,86,24,0.3)', overflow: 'hidden' }}>
              <motion.div
                style={{ position: 'absolute', top: 0, left: 0, bottom: 0, background: 'rgba(176,137,58,0.85)', borderRadius: '3px' }}
                animate={{ width: `${globalProgressPct}%` }}
                transition={{ type: 'spring', stiffness: 60, damping: 18 }}
              />
              {/* Shimmer while building (not 100%) — keyframe lives in globals.css */}
              {globalProgressPct < 100 && (
                <div style={{
                  position: 'absolute', inset: 0, pointerEvents: 'none',
                  background: 'linear-gradient(90deg, transparent 0%, rgba(236,197,106,0.3) 50%, transparent 100%)',
                  animation: 'shimmer 2.2s linear infinite',
                }} />
              )}
            </div>
            <div style={{ marginTop: '3px', fontSize: '10px', color: 'rgba(212,166,72,0.75)', fontFamily: 'var(--mono-stack)', letterSpacing: '0.05em' }}>
              {planLit} / {planTotal} assets complete
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
