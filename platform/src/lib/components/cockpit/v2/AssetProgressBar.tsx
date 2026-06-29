'use client'

import { motion } from 'framer-motion'
import type { BuildStage, SubstepInfo } from './buildStage'
import { stageFill } from './buildStage'

interface AssetProgressBarProps {
  state: string
  sseState?: string
  actualRows?: number | null
  targetVolume?: number | null   // retained for API compat; fill is stage-based per N.4
  stage?: BuildStage
  substep?: SubstepInfo
  isQueued?: boolean
}

// Four milestone segments when no substep detail is available.
// These mark ¼, ½, ¾, full progress — a neutral scaffold visible in every state.
const MILESTONE_COUNT = 4

interface SegmentColors {
  filledBg: string
  filledBorder: string
  activeBg: string
  activeBorder: string
  emptyBg: string
  emptyBorder: string
  continuousFill: string
  trackBorder: string
}

const SEG: Record<string, SegmentColors> = {
  lit: {
    filledBg:     'rgba(168,124,42,0.82)',
    filledBorder: 'rgba(212,166,72,0.70)',
    activeBg:     'rgba(210,162,60,0.50)',
    activeBorder: 'rgba(210,162,60,0.55)',
    emptyBg:      'rgba(122,86,24,0.10)',
    emptyBorder:  'rgba(122,86,24,0.18)',
    continuousFill: 'rgba(168,124,42,0.82)',
    trackBorder:  'rgba(122,86,24,0.28)',
  },
  service_ok: {
    filledBg:     'rgba(168,124,42,0.82)',
    filledBorder: 'rgba(212,166,72,0.70)',
    activeBg:     'rgba(210,162,60,0.50)',
    activeBorder: 'rgba(210,162,60,0.55)',
    emptyBg:      'rgba(122,86,24,0.10)',
    emptyBorder:  'rgba(122,86,24,0.18)',
    continuousFill: 'rgba(168,124,42,0.82)',
    trackBorder:  'rgba(122,86,24,0.28)',
  },
  building: {
    filledBg:     'rgba(168,124,42,0.80)',
    filledBorder: 'rgba(212,166,72,0.65)',
    activeBg:     'rgba(210,162,60,0.42)',
    activeBorder: 'rgba(236,197,106,0.50)',
    emptyBg:      'rgba(122,86,24,0.08)',
    emptyBorder:  'rgba(122,86,24,0.16)',
    continuousFill: 'rgba(210,162,60,0.85)',
    trackBorder:  'rgba(122,86,24,0.25)',
  },
  stale: {
    filledBg:     'rgba(160,104,48,0.60)',
    filledBorder: 'rgba(196,128,64,0.55)',
    activeBg:     'rgba(160,104,48,0.35)',
    activeBorder: 'rgba(196,128,64,0.40)',
    emptyBg:      'rgba(122,86,24,0.08)',
    emptyBorder:  'rgba(122,86,24,0.14)',
    continuousFill: 'rgba(160,104,48,0.60)',
    trackBorder:  'rgba(122,86,24,0.22)',
  },
  error: {
    filledBg:     'rgba(181,71,76,0.38)',
    filledBorder: 'rgba(181,71,76,0.60)',
    activeBg:     'rgba(181,71,76,0.25)',
    activeBorder: 'rgba(181,71,76,0.45)',
    emptyBg:      'rgba(181,71,76,0.10)',
    emptyBorder:  'rgba(181,71,76,0.22)',
    continuousFill: 'rgba(181,71,76,0.45)',
    trackBorder:  'rgba(181,71,76,0.30)',
  },
  dormant: {
    filledBg:     'rgba(122,86,24,0.12)',
    filledBorder: 'rgba(122,86,24,0.20)',
    activeBg:     'rgba(122,86,24,0.18)',
    activeBorder: 'rgba(122,86,24,0.28)',
    emptyBg:      'rgba(122,86,24,0.06)',
    emptyBorder:  'rgba(122,86,24,0.12)',
    continuousFill: 'rgba(122,86,24,0.20)',
    trackBorder:  'rgba(122,86,24,0.16)',
  },
  not_migrated: {
    filledBg:     'rgba(80,70,50,0.10)',
    filledBorder: 'rgba(80,70,50,0.18)',
    activeBg:     'rgba(80,70,50,0.14)',
    activeBorder: 'rgba(80,70,50,0.22)',
    emptyBg:      'rgba(80,70,50,0.05)',
    emptyBorder:  'rgba(80,70,50,0.10)',
    continuousFill: 'rgba(80,70,50,0.20)',
    trackBorder:  'rgba(80,70,50,0.14)',
  },
  reconnecting: {
    filledBg:     'rgba(236,197,106,0.12)',
    filledBorder: 'rgba(236,197,106,0.32)',
    activeBg:     'rgba(236,197,106,0.20)',
    activeBorder: 'rgba(236,197,106,0.40)',
    emptyBg:      'rgba(122,86,24,0.06)',
    emptyBorder:  'rgba(122,86,24,0.12)',
    continuousFill: 'rgba(236,197,106,0.25)',
    trackBorder:  'rgba(236,197,106,0.22)',
  },
  retired: {
    filledBg:     'rgba(80,80,80,0.08)',
    filledBorder: 'rgba(110,110,110,0.16)',
    activeBg:     'rgba(80,80,80,0.12)',
    activeBorder: 'rgba(110,110,110,0.22)',
    emptyBg:      'rgba(80,80,80,0.04)',
    emptyBorder:  'rgba(80,80,80,0.10)',
    continuousFill: 'rgba(80,80,80,0.20)',
    trackBorder:  'rgba(80,80,80,0.12)',
  },
}

export function AssetProgressBar({
  state, sseState, actualRows, stage, substep,
}: AssetProgressBarProps) {
  const prefersReducedMotion = typeof window !== 'undefined'
    && typeof window.matchMedia === 'function'
    && window.matchMedia('(prefers-reduced-motion: reduce)').matches

  const effectiveState = sseState ?? state
  const isBuilding    = effectiveState === 'building'
  const isLit         = effectiveState === 'lit' || effectiveState === 'service_ok' || stage === 'lit'
  const isError       = effectiveState === 'error'
  const isStale       = effectiveState === 'stale'
  const c = SEG[effectiveState] ?? SEG.dormant

  // Substep-segmented vs. continuous fill
  const hasSubsteps    = isBuilding && substep != null && substep.total > 1
  const useContinuous  = isBuilding && !hasSubsteps

  // Segment data
  const segCount = hasSubsteps ? substep!.total : MILESTONE_COUNT

  type SegState = 'filled' | 'active' | 'empty'
  const segStates: SegState[] = Array.from({ length: segCount }, (_, i) => {
    if (hasSubsteps) {
      const done  = i < (substep!.index - 1)
      const cur   = i === (substep!.index - 1)
      return done ? 'filled' : cur ? 'active' : 'empty'
    }
    // Fixed milestones: lit / error / stale fill all; everything else empties
    return (isLit || isError || isStale) ? 'filled' : 'empty'
  })

  // Above-bar label row
  let leftLabel  = ''
  let rightLabel = ''

  if (isBuilding) {
    if (hasSubsteps) {
      // Row count on left while building (updates in real time)
      if (actualRows != null && actualRows > 0) leftLabel = actualRows.toLocaleString()
      rightLabel = `${substep!.index} / ${substep!.total}`
    } else {
      // Stage label for builds with no substep detail yet
      leftLabel =
        stage === 'queued'     ? 'Queued'      :
        stage === 'committing' ? 'Committing'  :
        'Starting'
    }
  } else if ((isLit || isStale) && actualRows != null && actualRows > 0) {
    leftLabel = actualRows.toLocaleString()
  }

  const showLabels = leftLabel !== '' || rightLabel !== ''

  // Continuous fill % (building, no substeps)
  const contFillPct = useContinuous && stage ? stageFill(stage, substep) : 0

  return (
    <div style={{ width: '100%' }}>

      {/* ── Label row above bar ─────────────────────────────────────── */}
      {showLabels && (
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'baseline',
          marginBottom: '4px',
        }}>
          <span style={{
            fontFamily: 'var(--mono-stack)',
            fontSize: '9px',
            fontVariantNumeric: 'tabular-nums',
            color: isBuilding ? 'var(--on-dark-mut)' : 'var(--on-dark-faint)',
            letterSpacing: '0.02em',
            lineHeight: 1,
          }}>
            {leftLabel}
          </span>
          {rightLabel && (
            <span style={{
              fontFamily: 'var(--mono-stack)',
              fontSize: '9px',
              color: 'var(--on-dark-faint)',
              letterSpacing: '0.04em',
              lineHeight: 1,
            }}>
              {rightLabel}
            </span>
          )}
        </div>
      )}

      {/* ── Bar ──────────────────────────────────────────────────────── */}
      {useContinuous ? (
        // Continuous animated fill — building with no substep info yet
        <div style={{
          position: 'relative',
          height: '6px',
          borderRadius: '3px',
          background: 'rgba(10,8,6,0.65)',
          border: `1px solid ${c.trackBorder}`,
          overflow: 'hidden',
        }}>
          <motion.div
            style={{
              position: 'absolute', top: 0, left: 0, bottom: 0,
              borderRadius: '3px',
              background: c.continuousFill,
              overflow: 'hidden',
            }}
            animate={{ width: `${Math.max(3, contFillPct)}%` }}
            transition={prefersReducedMotion
              ? { duration: 0.1 }
              : { type: 'spring', stiffness: 90, damping: 22 }}
          >
            {!prefersReducedMotion && (
              <>
                <div style={{
                  position: 'absolute', inset: 0, pointerEvents: 'none',
                  background: 'linear-gradient(90deg, transparent 0%, rgba(236,197,106,0.28) 50%, transparent 100%)',
                  animation: 'shimmer 2s linear infinite',
                }} />
                {contFillPct > 4 && (
                  <div style={{
                    position: 'absolute', top: 0, right: 0, bottom: 0,
                    width: '2px',
                    background: '#ECC56A',
                    boxShadow: '0 0 5px rgba(236,197,106,0.85)',
                  }} />
                )}
              </>
            )}
          </motion.div>
        </div>
      ) : (
        // Segmented milestone bar
        <div style={{ display: 'flex', gap: '2px', height: '6px' }}>
          {segStates.map((seg, i) => {
            const bg     = seg === 'filled' ? c.filledBg   : seg === 'active' ? c.activeBg   : c.emptyBg
            const border = seg === 'filled' ? c.filledBorder : seg === 'active' ? c.activeBorder : c.emptyBorder
            return (
              <div
                key={i}
                style={{
                  flex: 1,
                  height: '6px',
                  borderRadius: '2px',
                  position: 'relative',
                  overflow: 'hidden',
                  background: bg,
                  border: `1px solid ${border}`,
                  transition: prefersReducedMotion ? 'none' : 'background 0.45s ease, border-color 0.45s ease',
                }}
              >
                {seg === 'active' && !prefersReducedMotion && (
                  <div style={{
                    position: 'absolute', inset: 0, pointerEvents: 'none',
                    background: 'linear-gradient(90deg, transparent 0%, rgba(236,197,106,0.55) 50%, transparent 100%)',
                    animation: 'shimmer 1.8s linear infinite',
                  }} />
                )}
              </div>
            )
          })}
        </div>
      )}

    </div>
  )
}
