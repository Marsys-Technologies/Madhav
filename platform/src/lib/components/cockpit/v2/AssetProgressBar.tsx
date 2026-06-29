'use client'

import { motion } from 'framer-motion'
import type { BuildStage, SubstepInfo } from './buildStage'
import { stageFill } from './buildStage'

interface AssetProgressBarProps {
  state: string
  sseState?: string
  actualRows?: number | null
  targetVolume?: number | null      // retained for API compat; fill is stage-based per N.4
  stage?: BuildStage
  substep?: SubstepInfo
  isQueued?: boolean
}

const STATE_COLORS: Record<string, {
  fill: string; stroke: string; pill: string; pillColor: string
}> = {
  dormant:      { fill: 'rgba(122,86,24,0.0)',    stroke: 'rgba(122,86,24,0.35)',   pill: 'NOT BUILT',    pillColor: 'rgba(155,131,80,0.7)' },
  building:     { fill: 'rgba(210,162,60,0.85)',   stroke: 'rgba(210,162,60,0.7)',   pill: 'BUILDING',     pillColor: 'rgba(236,197,106,0.95)' },
  lit:          { fill: 'rgba(176,137,58,0.9)',    stroke: 'rgba(212,166,72,0.8)',   pill: 'LIVE',         pillColor: 'rgba(236,197,106,0.95)' },
  service_ok:   { fill: 'rgba(176,137,58,0.9)',    stroke: 'rgba(212,166,72,0.8)',   pill: 'LIVE',         pillColor: 'rgba(236,197,106,0.95)' },
  stale:        { fill: 'rgba(166,108,52,0.65)',   stroke: 'rgba(196,128,64,0.7)',   pill: 'OUT OF SYNC',  pillColor: 'rgba(232,180,108,0.95)' },
  error:        { fill: 'rgba(181,71,76,0.5)',     stroke: 'rgba(181,71,76,0.8)',    pill: 'FAILED',       pillColor: 'rgba(232,108,108,1)' },
  not_migrated: { fill: 'rgba(80,70,50,0.0)',      stroke: 'rgba(80,70,50,0.25)',    pill: 'NOT MIGRATED', pillColor: 'rgba(120,110,90,0.65)' },
  reconnecting: { fill: 'rgba(236,197,106,0.08)',  stroke: 'rgba(236,197,106,0.35)', pill: 'RECONNECTING', pillColor: 'rgba(236,197,106,0.85)' },
  retired:      { fill: 'rgba(80,80,80,0.0)',       stroke: 'rgba(110,110,110,0.25)', pill: 'RETIRED',      pillColor: 'rgba(150,150,150,0.6)' },
}

export function AssetProgressBar({
  state, sseState, actualRows, stage, substep,
}: AssetProgressBarProps) {
  const prefersReducedMotion = typeof window !== 'undefined'
    && typeof window.matchMedia === 'function'
    && window.matchMedia('(prefers-reduced-motion: reduce)').matches

  const effectiveState = sseState ?? state
  const isBuilding = effectiveState === 'building'
  const isLit      = effectiveState === 'lit' || effectiveState === 'service_ok' || stage === 'lit'
  const isError    = effectiveState === 'error'
  const colors = STATE_COLORS[effectiveState] ?? STATE_COLORS.dormant

  // Fill % — stage-based per N.4
  let fillPct = 0
  if (isBuilding && stage) fillPct = stageFill(stage, substep)
  else if (isLit)  fillPct = 100
  else if (isError) fillPct = 100

  // Left label — row count when lit, step indicator when building
  let leftLabel = ''
  if (isBuilding) {
    if (substep && substep.total > 0) {
      leftLabel = `${substep.index}/${substep.total}`
    } else if (stage === 'queued')     { leftLabel = 'Queued' }
    else if (stage === 'committing')   { leftLabel = 'Committing' }
    else                               { leftLabel = 'Starting' }
  } else if (isLit && actualRows != null && actualRows > 0) {
    leftLabel = actualRows.toLocaleString()
  }

  const hasSubsteps = isBuilding && substep != null && substep.total > 1

  const springTransition = prefersReducedMotion
    ? { duration: 0.1 }
    : { type: 'spring' as const, stiffness: 90, damping: 22 }

  return (
    // Three-column layout: [left label] [bar] [state badge]
    // All text sits outside the bar — no overlapping, consistent badge on right for every state.
    <div style={{ display: 'flex', alignItems: 'center', gap: 6, width: '100%' }}>

      {/* Left label — rows count or build step, fixed width so bar stays aligned */}
      <div style={{
        fontFamily: 'var(--mono-stack)',
        fontSize: '9px',
        fontVariantNumeric: 'tabular-nums',
        color: isBuilding ? 'var(--on-dark-mut)' : 'var(--on-dark-faint)',
        minWidth: '52px',
        textAlign: 'right',
        flexShrink: 0,
        whiteSpace: 'nowrap',
        overflow: 'hidden',
        textOverflow: 'ellipsis',
      }}>
        {leftLabel}
      </div>

      {/* Bar — 5px thin track, either segmented (substeps) or continuous fill */}
      <div style={{ flex: 1, position: 'relative', height: '5px' }}>
        {hasSubsteps ? (
          // Segmented substep bar — one block per substep
          <div style={{ display: 'flex', gap: '2px', height: '5px' }}>
            {Array.from({ length: substep!.total }, (_, i) => {
              const isDone   = i < (substep!.index - 1)
              const isActive = i === (substep!.index - 1)
              return (
                <div
                  key={i}
                  style={{
                    flex: 1,
                    height: '5px',
                    borderRadius: '2px',
                    position: 'relative',
                    overflow: 'hidden',
                    background: isDone
                      ? colors.fill
                      : isActive
                        ? 'rgba(210,162,60,0.45)'
                        : 'rgba(122,86,24,0.14)',
                    border: `1px solid ${isDone || isActive ? colors.stroke : 'rgba(122,86,24,0.18)'}`,
                    transition: prefersReducedMotion ? 'none' : 'background 0.3s ease',
                  }}
                >
                  {isActive && !prefersReducedMotion && (
                    <div style={{
                      position: 'absolute', inset: 0, pointerEvents: 'none',
                      background: 'linear-gradient(90deg, transparent 0%, rgba(236,197,106,0.45) 50%, transparent 100%)',
                      animation: 'shimmer 1.8s linear infinite',
                    }} />
                  )}
                </div>
              )
            })}
          </div>
        ) : (
          // Continuous fill bar
          <>
            {/* Track */}
            <div style={{
              position: 'absolute', inset: 0, borderRadius: '3px',
              background: 'rgba(15,12,8,0.7)',
              border: `1px solid ${colors.stroke}`,
            }} />
            {/* Animated fill */}
            <motion.div
              style={{
                position: 'absolute', top: 0, left: 0, bottom: 0,
                borderRadius: '3px',
                background: isError ? 'rgba(181,71,76,0.5)' : colors.fill,
                overflow: 'hidden',
              }}
              animate={{ width: `${isBuilding ? Math.max(2, fillPct) : fillPct}%` }}
              transition={springTransition}
            >
              {/* Shimmer while building */}
              {isBuilding && !prefersReducedMotion && (
                <div style={{
                  position: 'absolute', inset: 0, pointerEvents: 'none',
                  background: 'linear-gradient(90deg, transparent 0%, rgba(236,197,106,0.28) 50%, transparent 100%)',
                  animation: 'shimmer 2s linear infinite',
                }} />
              )}
              {/* Leading-edge cap */}
              {isBuilding && !prefersReducedMotion && fillPct > 3 && (
                <div style={{
                  position: 'absolute', top: 0, right: 0, bottom: 0,
                  width: '2px',
                  background: '#ECC56A',
                  boxShadow: '0 0 5px rgba(236,197,106,0.8)',
                }} />
              )}
            </motion.div>
          </>
        )}
      </div>

      {/* State badge — always on the right, never inside the bar */}
      <div style={{
        fontFamily: 'var(--mono-stack)',
        fontSize: '8px',
        letterSpacing: '0.06em',
        textTransform: 'uppercase',
        color: colors.pillColor,
        flexShrink: 0,
        padding: '1px 5px',
        borderRadius: '3px',
        background: 'rgba(10,8,6,0.7)',
        border: `1px solid ${colors.stroke}`,
        whiteSpace: 'nowrap',
      }}>
        {colors.pill}
      </div>

    </div>
  )
}
