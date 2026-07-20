/**
 * curve_controls.test.ts — SYNTHETIC fixtures only, all dates pre-2020.
 * See model_interface.test.ts header for the sealed-test-split discipline
 * this file (and every file in this directory) follows.
 */
import { describe, it, expect } from 'vitest'
import { circularShiftCurve, shuffledBirthControlCurve, antiphaseControlCurve, antiphaseInvertPeakTrough } from '../curve_controls'
import type { CurvePoint } from '../../curve'

const BOUNDS_START = new Date(Date.UTC(1990, 0, 1))
const BOUNDS_END = new Date(Date.UTC(2000, 0, 1)) // exactly 10 years — clean half-period math

function makeCurve(): CurvePoint[] {
  // A spike at day 100 from BOUNDS_START, zero elsewhere across a 200-day sample.
  const out: CurvePoint[] = []
  for (let d = 0; d <= 200; d += 10) {
    out.push({ date: new Date(BOUNDS_START.getTime() + d * 86_400_000), intensity: d === 100 ? 10 : 0 })
  }
  return out
}

describe('circularShiftCurve', () => {
  it('preserves intensities, only moving dates', () => {
    const curve = makeCurve()
    const shifted = circularShiftCurve(curve, 500, BOUNDS_START, BOUNDS_END)
    const originalIntensities = curve.map((c) => c.intensity).sort()
    const shiftedIntensities = shifted.map((c) => c.intensity).sort()
    expect(shiftedIntensities).toEqual(originalIntensities)
  })

  it('wraps within [boundsStart, boundsEnd)', () => {
    const curve = makeCurve()
    const totalDays = Math.round((BOUNDS_END.getTime() - BOUNDS_START.getTime()) / 86_400_000)
    const shifted = circularShiftCurve(curve, totalDays - 50, BOUNDS_START, BOUNDS_END)
    for (const pt of shifted) {
      expect(pt.date.getTime()).toBeGreaterThanOrEqual(BOUNDS_START.getTime())
      expect(pt.date.getTime()).toBeLessThan(BOUNDS_END.getTime())
    }
  })

  it('is a no-op transform of dates for shiftDays=0 modulo the total span', () => {
    const curve = makeCurve()
    const shifted = circularShiftCurve(curve, 0, BOUNDS_START, BOUNDS_END)
    expect(shifted.map((c) => c.date.getTime())).toEqual(curve.map((c) => c.date.getTime()))
  })
})

describe('shuffledBirthControlCurve (deliverable 1 — real, not stub)', () => {
  it('is exactly circularShiftCurve at the caller-supplied shift', () => {
    const curve = makeCurve()
    const a = shuffledBirthControlCurve(curve, 333, BOUNDS_START, BOUNDS_END)
    const b = circularShiftCurve(curve, 333, BOUNDS_START, BOUNDS_END)
    expect(a).toEqual(b)
  })

  it('moves the real spike away from its original date (control curve is genuinely different from the real curve)', () => {
    const curve = makeCurve()
    const shifted = shuffledBirthControlCurve(curve, 500, BOUNDS_START, BOUNDS_END)
    const originalSpikeDate = curve.find((c) => c.intensity === 10)!.date.getTime()
    const shiftedSpikeDate = shifted.find((c) => c.intensity === 10)!.date.getTime()
    expect(shiftedSpikeDate).not.toBe(originalSpikeDate)
  })
})

describe('antiphaseControlCurve (deliverable 2 — primary reading: half-period shift)', () => {
  it('shifts by exactly half the bounds span', () => {
    const curve = makeCurve()
    const antiphase = antiphaseControlCurve(curve, BOUNDS_START, BOUNDS_END)
    const totalDays = Math.round((BOUNDS_END.getTime() - BOUNDS_START.getTime()) / 86_400_000)
    const manual = circularShiftCurve(curve, Math.round(totalDays / 2), BOUNDS_START, BOUNDS_END)
    expect(antiphase).toEqual(manual)
  })

  it('is deterministic and reproducible (same input -> same output, no randomness)', () => {
    const curve = makeCurve()
    const a = antiphaseControlCurve(curve, BOUNDS_START, BOUNDS_END)
    const b = antiphaseControlCurve(curve, BOUNDS_START, BOUNDS_END)
    expect(a).toEqual(b)
  })

  it('is a genuinely different permutation than the shuffled-birth control at an arbitrary shift', () => {
    const curve = makeCurve()
    const antiphase = antiphaseControlCurve(curve, BOUNDS_START, BOUNDS_END)
    const shuffled = shuffledBirthControlCurve(curve, 137, BOUNDS_START, BOUNDS_END)
    expect(antiphase).not.toEqual(shuffled)
  })
})

describe('antiphaseInvertPeakTrough (deliverable 2 — documented alternate reading)', () => {
  it('turns the former peak into the minimum (0) and leaves dates untouched', () => {
    const curve = makeCurve()
    const inverted = antiphaseInvertPeakTrough(curve)
    expect(inverted.map((c) => c.date.getTime())).toEqual(curve.map((c) => c.date.getTime()))
    const formerPeak = inverted.find((c, i) => curve[i].intensity === 10)!
    expect(formerPeak.intensity).toBe(0)
    // A former zero becomes the new peak (max - 0 = max).
    const formerZero = inverted.find((c, i) => curve[i].intensity === 0)!
    expect(formerZero.intensity).toBe(10)
  })

  it('never produces a negative intensity', () => {
    const curve: CurvePoint[] = [
      { date: new Date(0), intensity: 3 },
      { date: new Date(86_400_000), intensity: 7 },
      { date: new Date(2 * 86_400_000), intensity: -1 }, // pathological input, guarded regardless
    ]
    const inverted = antiphaseInvertPeakTrough(curve)
    expect(inverted.every((c) => c.intensity >= 0)).toBe(true)
  })
})
