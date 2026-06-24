'use client'

import { motion, AnimatePresence } from 'framer-motion'
import type { BuildStage, SubstepInfo } from './buildStage'
import { stageFill } from './buildStage'

interface AssetProgressBarProps {
  state: string                     // polled asset state
  sseState?: string                 // live SSE state override
  actualRows?: number | null        // for display when lit
  targetVolume?: number | null      // for display when lit (unused in fill; kept for API compat)
  stage?: BuildStage                // derived stage (passed from AssetRow)
  substep?: SubstepInfo             // substep data (passed from AssetRow)
  isQueued?: boolean                // true if in run plan but not yet started
}

const STATE_COLORS: Record<string, {
  fill: string; stroke: string; pill: string; pillColor: string
}> = {
  dormant:      { fill: 'rgba(122,86,24,0.0)',    stroke: 'rgba(122,86,24,0.4)',    pill: 'NOT BUILT',     pillColor: 'rgba(155,131,80,0.8)' },
  building:     { fill: 'rgba(168,124,48,0.7)',    stroke: 'rgba(200,154,70,0.75)',  pill: 'BUILDING',      pillColor: 'rgba(236,197,106,0.95)' },
  lit:          { fill: 'rgba(176,137,58,0.92)',   stroke: 'rgba(212,166,72,0.9)',   pill: 'LIVE',          pillColor: 'rgba(140,210,140,0.95)' },
  stale:        { fill: 'rgba(166,108,52,0.7)',    stroke: 'rgba(196,128,64,0.75)',  pill: 'OUT OF SYNC',   pillColor: 'rgba(232,180,108,0.95)' },
  error:        { fill: 'rgba(232,108,108,0.55)',  stroke: 'rgba(232,108,108,0.85)', pill: 'FAILED',        pillColor: 'rgba(232,108,108,1)' },
  not_migrated: { fill: 'rgba(80,70,50,0.0)',      stroke: 'rgba(80,70,50,0.3)',     pill: 'NOT MIGRATED',  pillColor: 'rgba(120,110,90,0.7)' },
  reconnecting: { fill: 'rgba(236,197,106,0.1)',   stroke: 'rgba(236,197,106,0.4)', pill: 'RECONNECTING',  pillColor: 'rgba(236,197,106,0.9)' },
  retired:      { fill: 'rgba(80,80,80,0.0)',       stroke: 'rgba(110,110,110,0.3)', pill: 'RETIRED',       pillColor: 'rgba(150,150,150,0.65)' },
}

function stageLabel(stage: BuildStage, substep?: SubstepInfo, actualRows?: number | null): string {
  switch (stage) {
    case 'queued':     return 'Queued'
    case 'running':    return 'Starting…'
    case 'substeps':   return substep ? `Step ${substep.index} / ${substep.total}` : 'Running…'
    case 'committing': return 'Committing…'
    case 'lit':        return actualRows != null ? `${actualRows.toLocaleString()} rows` : ''
    default:           return ''
  }
}

export function AssetProgressBar({ state, sseState, actualRows, stage, substep, isQueued }: AssetProgressBarProps) {
  // Prefer-reduced-motion check (safe for SSR — only evaluated client-side)
  const prefersReducedMotion = typeof window !== 'undefined'
    && typeof window.matchMedia === 'function'
    && window.matchMedia('(prefers-reduced-motion: reduce)').matches

  const effectiveState = sseState ?? state
  const isBuilding = effectiveState === 'building'
  const isLit = effectiveState === 'lit' || stage === 'lit'
  const isError = effectiveState === 'error'
  const colors = STATE_COLORS[state] ?? STATE_COLORS.dormant

  // Stage-based fill during building; row-count-independent
  let fillPct: number
  if (isBuilding && stage) {
    fillPct = stageFill(stage, substep)
  } else if (isLit) {
    fillPct = 100
  } else if (isError) {
    fillPct = 100
  } else {
    fillPct = 0
  }

  // Spring animation — disabled for prefers-reduced-motion
  const springTransition = prefersReducedMotion
    ? { duration: 0.1 }
    : { type: 'spring' as const, stiffness: 80, damping: 20 }

  // Stage label — only shown when building
  const currentStage: BuildStage = stage ?? (isLit ? 'lit' : 'idle')
  const label = stageLabel(currentStage, substep, actualRows)
  const showLabel = isBuilding && label !== ''

  // Fill color: amber while building, green for lit, red for error
  const fillColor = isError
    ? 'rgba(232,108,108,0.55)'
    : isLit
      ? 'rgba(83,180,95,0.55)'
      : colors.fill

  return (
    <div className="relative h-[22px] w-full">
      {/* Track */}
      <div
        className="absolute inset-0 rounded-[3px] border"
        style={{ borderColor: colors.stroke, background: 'rgba(15,12,8,0.6)' }}
      />

      {/* Fill — spring-animated width for stage-based progress */}
      <div className="absolute top-0 bottom-0 left-0 rounded-l-[3px] overflow-hidden" style={{ width: '100%' }}>
        <motion.div
          className="h-full rounded-l-[3px] origin-left relative"
          style={{ background: fillColor }}
          animate={{ width: `${fillPct}%` }}
          transition={springTransition}
        >
          {/* Shimmer overlay — CSS keyframe animation on the fill div, only during active building stages */}
          {isBuilding && (currentStage === 'running' || currentStage === 'substeps') && (
            <div
              className="absolute inset-0 pointer-events-none"
              style={{
                background: 'linear-gradient(90deg, transparent 0%, rgba(236,197,106,0.22) 50%, transparent 100%)',
                animation: 'shimmer 2s linear infinite',
              }}
            />
          )}
        </motion.div>
      </div>

      {/* Stage label — cross-fades between stages using AnimatePresence */}
      {showLabel && (
        <div
          className="absolute inset-0 flex items-center pl-2 pr-[68px] font-mono text-[9px] overflow-hidden"
          style={{ textShadow: '0 1px 2px rgba(0,0,0,0.6)' }}
        >
          <AnimatePresence mode="wait" initial={false}>
            <motion.span
              key={label}
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -4 }}
              transition={{ duration: 0.15 }}
              style={{ color: 'rgba(255,255,255,0.75)', display: 'block', whiteSpace: 'nowrap' }}
            >
              {label}
            </motion.span>
          </AnimatePresence>
        </div>
      )}

      {/* Rows count — shown in lit state (non-building) */}
      {!isBuilding && isLit && actualRows != null && (
        <div
          className="absolute inset-0 flex items-center justify-center pl-2 pr-[60px] font-mono text-[10px] text-white"
          style={{ textShadow: '0 1px 2px rgba(0,0,0,0.6)' }}
        >
          {actualRows.toLocaleString()}
        </div>
      )}

      {/* State pill — right edge inside the bar; label cross-fades on state change */}
      <div
        className="absolute top-[2px] right-[2px] bottom-[2px] flex items-center px-1.5 rounded-[2px] font-mono text-[8px] uppercase overflow-hidden"
        style={{ background: 'rgba(10,8,6,0.85)', letterSpacing: '0.06em' }}
      >
        <AnimatePresence mode="wait" initial={false}>
          <motion.span
            key={colors.pill}
            initial={{ opacity: 0, y: 3 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -3 }}
            transition={{ duration: 0.18, ease: [0.16, 1, 0.3, 1] }}
            style={{ color: colors.pillColor, display: 'block' }}
          >
            {colors.pill}
          </motion.span>
        </AnimatePresence>
      </div>

      {/* Shimmer keyframe — injected once via a style tag */}
      <style>{`
        @keyframes shimmer {
          from { transform: translateX(-100%); }
          to   { transform: translateX(200%); }
        }
      `}</style>
    </div>
  )
}
