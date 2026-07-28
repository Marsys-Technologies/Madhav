/**
 * ConfidenceSlider — elicits a Brier-ready confidence BAND — PB-3 lane L-2.
 *
 * Design authority: PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md §14.3 + BRIEF_PB-3 §F1 L-2.
 *
 * "Confirm elicits a probability if none stated (§14.3): slider → numrange."
 * The ledger's confidence column is a `numrange` (NEVER a point — the X-5 lesson
 * that made a text-enum confidence Brier-unusable). This control therefore
 * produces a BAND `{ low, high }` in [0,1], not a point estimate: two thumbs the
 * human sets to the low/high edges of their credible interval.
 *
 * If the detector already parsed a stated probability (`confidence_stated`), the
 * band is PRE-POSITIONED centred on it (the human may still widen/narrow it) —
 * the point only seeds the UI; the committed value is always the band the human
 * confirms, never a code-invented half-width on the server (B.10 spirit).
 */

'use client'

import { useState } from 'react'
import type { ConfidenceBand } from '@/lib/pariprashna/samiksha/schema'

/** Seed a band centred on a stated point (UI pre-fill only; ±0.1, clamped). */
export function bandFromStatedPoint(p: number): ConfidenceBand {
  const half = 0.1
  return { low: Math.max(0, Math.round((p - half) * 100) / 100), high: Math.min(1, Math.round((p + half) * 100) / 100) }
}

export interface ConfidenceSliderProps {
  /** Detector's stated point, if any — seeds the initial band. */
  statedPoint?: number
  value?: ConfidenceBand
  onChange: (band: ConfidenceBand) => void
}

export function ConfidenceSlider({ statedPoint, value, onChange }: ConfidenceSliderProps) {
  const seed: ConfidenceBand =
    value ?? (statedPoint !== undefined ? bandFromStatedPoint(statedPoint) : { low: 0.4, high: 0.6 })
  const [band, setBand] = useState<ConfidenceBand>(seed)

  function update(next: ConfidenceBand) {
    // Keep low <= high (the numrange invariant the DAL also enforces).
    const clamped: ConfidenceBand = { low: Math.min(next.low, next.high), high: Math.max(next.low, next.high) }
    setBand(clamped)
    onChange(clamped)
  }

  return (
    <div className="pp-conf-slider" data-testid="confidence-slider">
      <div className="pp-conf-slider__eyebrow">CONFIDENCE</div>
      <label className="pp-conf-slider__row">
        <span className="pp-conf-slider__lbl">low</span>
        <input
          type="range"
          min={0}
          max={1}
          step={0.01}
          value={band.low}
          data-testid="confidence-low"
          onChange={(e) => update({ ...band, low: Number(e.target.value) })}
        />
        <span className="pp-conf-slider__val">{Math.round(band.low * 100)}%</span>
      </label>
      <label className="pp-conf-slider__row">
        <span className="pp-conf-slider__lbl">high</span>
        <input
          type="range"
          min={0}
          max={1}
          step={0.01}
          value={band.high}
          data-testid="confidence-high"
          onChange={(e) => update({ ...band, high: Number(e.target.value) })}
        />
        <span className="pp-conf-slider__val">{Math.round(band.high * 100)}%</span>
      </label>
      <div className="pp-conf-slider__band">
        numrange [{band.low.toFixed(2)}, {band.high.toFixed(2)})
      </div>
    </div>
  )
}
