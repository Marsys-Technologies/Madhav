'use client'

// BuildWaveAnimation — Framer Motion animated progress sweep for the natal wheel
// Shows a wave of light progressing around the 12-house wheel as builds complete
// H-04: Initial implementation with 5-ayanamsha arc, phase-based opacity, completion ring

import { useEffect, useRef, useState } from 'react'
import { motion, AnimatePresence, useAnimationFrame } from 'framer-motion'

// ── Types ──────────────────────────────────────────────────────────────────────

export type WavePhase =
  | 'idle'           // no build active
  | 'initializing'   // build queued, setting up
  | 'wave_1'         // first sweep (A1-A5, engine + early assets)
  | 'wave_2'         // second sweep (A6-A10, structural + synthesis prep)
  | 'wave_3'         // third sweep (A11-A14, synthesis outputs)
  | 'complete'       // all done — celebration pulse
  | 'failed'         // error state

export interface AyanamshaWaveState {
  ayanamsha_id: string
  display_name: string
  progress_pct: number    // 0–100
  phase: WavePhase
  color?: string          // optional override; falls back to AYANAMSHA_COLORS
}

interface BuildWaveAnimationProps {
  ayanamshaStates: AyanamshaWaveState[]
  size?: number
  className?: string
}

// ── Constants ─────────────────────────────────────────────────────────────────

const AYANAMSHA_COLORS: Record<string, string> = {
  lahiri:          '#3B82F6',  // blue-500
  true_chitra:     '#8B5CF6',  // violet-500
  kp:              '#F59E0B',  // amber-500
  raman:           '#10B981',  // emerald-500
  surya_siddhanta: '#EF4444',  // red-500
}

/** Fractional opacity per phase */
const PHASE_OPACITY: Record<WavePhase, number> = {
  idle:         0,
  initializing: 0.20,
  wave_1:       0.50,
  wave_2:       0.70,
  wave_3:       0.85,
  complete:     1.00,
  failed:       0.30,
}

/** Stroke width per phase */
const PHASE_STROKE_WIDTH: Record<WavePhase, number> = {
  idle:         0,
  initializing: 1.5,
  wave_1:       2.0,
  wave_2:       2.5,
  wave_3:       3.0,
  complete:     4.0,
  failed:       1.5,
}

/** Radial offsets (fraction of size/2) for the 5 ayanamsha rings */
const RING_RADII_FRACTIONS = [0.38, 0.35, 0.32, 0.29, 0.26] as const

// ── Helpers ────────────────────────────────────────────────────────────────────

function toRad(deg: number) {
  return (deg * Math.PI) / 180
}

/**
 * Build an SVG arc path starting at the 12-o'clock position and sweeping
 * clockwise for `sweepDeg` degrees along a circle of radius `r` centred at
 * (cx, cy).
 */
function arcPath(cx: number, cy: number, r: number, sweepDeg: number): string {
  const start = -90  // 12-o'clock
  const end = start + sweepDeg
  const sx = cx + r * Math.cos(toRad(start))
  const sy = cy + r * Math.sin(toRad(start))
  const ex = cx + r * Math.cos(toRad(end))
  const ey = cy + r * Math.sin(toRad(end))
  const large = sweepDeg > 180 ? 1 : 0
  return `M ${sx} ${sy} A ${r} ${r} 0 ${large} 1 ${ex} ${ey}`
}

/** Leading-dot coordinates at the arc tip */
function arcTip(cx: number, cy: number, r: number, sweepDeg: number) {
  const angle = -90 + sweepDeg
  return {
    x: cx + r * Math.cos(toRad(angle)),
    y: cy + r * Math.sin(toRad(angle)),
  }
}

// ── Component ─────────────────────────────────────────────────────────────────

export default function BuildWaveAnimation({
  ayanamshaStates,
  size = 400,
  className = '',
}: BuildWaveAnimationProps) {
  const cx = size / 2
  const cy = size / 2

  // Pulse oscillator — drives the leading-dot + completion-ring throb
  const pulseRef = useRef(0)
  const [pulse, setPulse] = useState(0)

  useAnimationFrame((t) => {
    pulseRef.current = t
    setPulse(t)
  })

  // Derived state
  const active = ayanamshaStates.filter((s) => s.phase !== 'idle')
  const allComplete =
    active.length > 0 && active.every((s) => s.phase === 'complete')
  const anyActive = active.some((s) =>
    ['initializing', 'wave_1', 'wave_2', 'wave_3'].includes(s.phase),
  )

  // Nothing to show — return sentinel div so tests can assert idle state
  if (ayanamshaStates.length === 0 || active.length === 0) {
    return (
      <div
        data-testid="build-wave-idle"
        className={className}
        aria-hidden="true"
      />
    )
  }

  return (
    <svg
      viewBox={`0 0 ${size} ${size}`}
      className={`pointer-events-none select-none ${className}`}
      data-testid="build-wave-animation"
      aria-hidden="true"
    >
      {/* ── Per-ayanamsha arcs ─────────────────────────────────────────────── */}
      {ayanamshaStates.map((state, i) => {
        if (state.phase === 'idle') return null

        const r = (RING_RADII_FRACTIONS[i] ?? 0.38) * size
        const opacity = PHASE_OPACITY[state.phase] ?? 0
        const strokeWidth = PHASE_STROKE_WIDTH[state.phase] ?? 2
        const color =
          state.color ??
          AYANAMSHA_COLORS[state.ayanamsha_id] ??
          '#64748B'

        const sweepDeg = Math.min(
          Math.max((state.progress_pct / 100) * 360, 0),
          359.99, // avoid degenerate full-circle arc
        )

        const isActive = ['initializing', 'wave_1', 'wave_2', 'wave_3'].includes(
          state.phase,
        )

        // Sinusoidal throb: amplitude ±15% of base opacity, period ~2 s
        const throb = isActive
          ? opacity * (0.85 + 0.15 * Math.sin((pulse / 1000) * Math.PI + i))
          : opacity

        const tip = arcTip(cx, cy, r, sweepDeg)
        const path = arcPath(cx, cy, r, sweepDeg)

        return (
          <g
            key={state.ayanamsha_id}
            data-testid={`wave-${state.ayanamsha_id}`}
          >
            {/* Progress arc */}
            <motion.path
              d={path}
              fill="none"
              stroke={color}
              strokeWidth={strokeWidth}
              strokeLinecap="round"
              strokeOpacity={throb}
              initial={{ pathLength: 0, opacity: 0 }}
              animate={{
                pathLength: state.progress_pct / 100,
                opacity: throb,
              }}
              transition={{ duration: 0.6, ease: 'easeOut' }}
            />

            {/* Leading dot — visible only while actively progressing */}
            <AnimatePresence>
              {isActive && state.progress_pct > 0 && (
                <motion.circle
                  key={`tip-${state.ayanamsha_id}`}
                  cx={tip.x}
                  cy={tip.y}
                  r={4}
                  fill={color}
                  fillOpacity={throb}
                  initial={{ scale: 0, opacity: 0 }}
                  animate={{ scale: 1, opacity: throb }}
                  exit={{ scale: 0, opacity: 0 }}
                  transition={{ duration: 0.3 }}
                  data-testid={`tip-${state.ayanamsha_id}`}
                />
              )}
            </AnimatePresence>

            {/* Failed state: short dashed segment at current position */}
            {state.phase === 'failed' && (
              <circle
                cx={tip.x}
                cy={tip.y}
                r={5}
                fill="none"
                stroke={color}
                strokeWidth={1.5}
                strokeOpacity={0.4}
                data-testid={`failed-marker-${state.ayanamsha_id}`}
              />
            )}
          </g>
        )
      })}

      {/* ── Completion celebration ring ────────────────────────────────────── */}
      <AnimatePresence>
        {allComplete && (
          <motion.circle
            key="complete-ring"
            cx={cx}
            cy={cy}
            r={(RING_RADII_FRACTIONS[0] ?? 0.38) * size + 10}
            fill="none"
            stroke="#16A34A"  // green-700
            strokeWidth={2}
            strokeOpacity={0.5 + 0.5 * Math.sin((pulse / 1000) * Math.PI)}
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 1.1, opacity: 0 }}
            transition={{ duration: 0.5, ease: 'easeOut' }}
            data-testid="complete-ring"
          />
        )}
      </AnimatePresence>

      {/* ── Global activity ring — subtle outer glow while any build runs ──── */}
      <AnimatePresence>
        {anyActive && !allComplete && (
          <motion.circle
            key="activity-ring"
            cx={cx}
            cy={cy}
            r={(RING_RADII_FRACTIONS[0] ?? 0.38) * size + 18}
            fill="none"
            stroke="#3B82F6"
            strokeWidth={1}
            strokeOpacity={0.15 + 0.1 * Math.sin((pulse / 800) * Math.PI)}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            data-testid="activity-ring"
          />
        )}
      </AnimatePresence>
    </svg>
  )
}
