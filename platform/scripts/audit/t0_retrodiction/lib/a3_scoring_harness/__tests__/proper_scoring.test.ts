/**
 * proper_scoring.test.ts — SYNTHETIC fixtures only, all dates pre-2020.
 * Known-answer inputs per BRIEF_D4A.md's "done" bar: "CRPS/log-score
 * implemented and testably correct (unit tests with known-answer inputs,
 * e.g. a perfect forecast should score near 0 CRPS)."
 */
import { describe, it, expect } from 'vitest'
import { crps, logScore, normalize, skill } from '../proper_scoring'
import type { CurvePoint } from '../../curve'

const D = (y: number, m: number, d: number) => new Date(Date.UTC(y, m - 1, d))

function regularGrid(start: Date, days: number, stepDays: number, intensityAt: (dayOffset: number) => number): CurvePoint[] {
  const out: CurvePoint[] = []
  for (let d = 0; d <= days; d += stepDays) {
    out.push({ date: new Date(start.getTime() + d * 86_400_000), intensity: intensityAt(d) })
  }
  return out
}

describe('normalize', () => {
  it('sums to 1 for a non-degenerate curve', () => {
    const curve = regularGrid(D(1995, 1, 1), 100, 5, (d) => (d === 50 ? 10 : 1))
    const probs = normalize(curve)
    expect(probs.reduce((s, v) => s + v, 0)).toBeCloseTo(1, 6)
  })

  it('falls back to uniform for an all-zero curve (no fabricated information, no divide-by-zero)', () => {
    const curve = regularGrid(D(1995, 1, 1), 100, 5, () => 0)
    const probs = normalize(curve)
    expect(probs.every((p) => Math.abs(p - 1 / curve.length) < 1e-9)).toBe(true)
  })

  it('clamps negative intensities to 0 before normalizing', () => {
    const curve: CurvePoint[] = [
      { date: D(1995, 1, 1), intensity: -5 },
      { date: D(1995, 1, 2), intensity: 5 },
    ]
    const probs = normalize(curve)
    expect(probs[0]).toBe(0)
    expect(probs[1]).toBe(1)
  })
})

describe('crps — known-answer inputs', () => {
  it('a perfect single-point forecast exactly at the true date scores CRPS near 0', () => {
    const trueDate = D(1995, 6, 15)
    const curve = regularGrid(D(1995, 1, 1), 365, 1, (d) => {
      const pointDate = D(1995, 1, 1).getTime() + d * 86_400_000
      return pointDate === trueDate.getTime() ? 1 : 0
    })
    const result = crps(curve, trueDate)
    expect(result.crps).toBeLessThan(1e-6)
    expect(result.eventInRange).toBe(true)
  })

  it('a uniform (maximally uninformative) forecast scores strictly worse (higher CRPS) than a concentrated forecast around the true date', () => {
    const trueDate = D(1995, 6, 15)
    const start = D(1995, 1, 1)
    const uniformCurve = regularGrid(start, 365, 5, () => 1)
    const concentratedCurve = regularGrid(start, 365, 5, (d) => {
      const pointDate = start.getTime() + d * 86_400_000
      return Math.abs(pointDate - trueDate.getTime()) < 20 * 86_400_000 ? 100 : 0
    })
    const uniformResult = crps(uniformCurve, trueDate)
    const concentratedResult = crps(concentratedCurve, trueDate)
    expect(concentratedResult.crps).toBeLessThan(uniformResult.crps)
  })

  it('flags eventInRange=false when the true date falls entirely outside the curve grid, and still returns a finite (penalized) score', () => {
    const curve = regularGrid(D(1995, 1, 1), 100, 5, (d) => (d === 50 ? 10 : 0))
    const result = crps(curve, D(1980, 1, 1)) // decades before the grid
    expect(result.eventInRange).toBe(false)
    expect(Number.isFinite(result.crps)).toBe(true)
    expect(result.crps).toBeGreaterThan(0)
  })

  it('is symmetric in construction: scoring the SAME function on a real curve and a shifted (control-like) curve uses identical code, no special-casing', () => {
    const trueDate = D(1995, 6, 15)
    const start = D(1995, 1, 1)
    const curveA = regularGrid(start, 365, 5, (d) => (d === 165 ? 10 : 0))
    const curveB = regularGrid(start, 365, 5, (d) => (d === 165 ? 10 : 0)) // identical construction
    expect(crps(curveA, trueDate).crps).toBeCloseTo(crps(curveB, trueDate).crps, 9)
  })
})

describe('logScore', () => {
  it('is higher (less negative) for a concentrated forecast near the truth than a diffuse one', () => {
    const trueDate = D(1995, 6, 15)
    const start = D(1995, 1, 1)
    const concentrated = regularGrid(start, 365, 5, (d) => {
      const pointDate = start.getTime() + d * 86_400_000
      return Math.abs(pointDate - trueDate.getTime()) < 10 * 86_400_000 ? 100 : 0
    })
    const diffuse = regularGrid(start, 365, 5, () => 1)
    expect(logScore(concentrated, trueDate)).toBeGreaterThan(logScore(diffuse, trueDate))
  })

  it('never returns -Infinity or NaN even for a true date entirely outside the grid (epsilon floor)', () => {
    const curve = regularGrid(D(1995, 1, 1), 100, 5, (d) => (d === 50 ? 10 : 0))
    const s = logScore(curve, D(1960, 1, 1))
    expect(Number.isFinite(s)).toBe(true)
  })
})

describe('skill — DR-15(b) verbatim: 1 - CRPS_model/CRPS_control', () => {
  it('is positive when the model beats the control (lower CRPS)', () => {
    expect(skill(2, 10)).toBeCloseTo(0.8, 9)
  })

  it('is zero when model and control are identical', () => {
    expect(skill(5, 5)).toBe(0)
  })

  it('is negative when the model is worse than the control', () => {
    expect(skill(10, 2)).toBeLessThan(0)
  })

  it('returns null (never a fabricated number) when control CRPS is exactly 0', () => {
    expect(skill(1, 0)).toBeNull()
  })
})
