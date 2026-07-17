import { describe, it, expect } from 'vitest'
import {
  intensityAt,
  buildCurve,
  percentileThreshold,
  topDecileThreshold,
  topTercileThreshold,
  localMax,
  fractionAtOrAbove,
  variance,
  circularShiftPeriods,
  type DashaPeriod,
} from '../curve'
import { parseDate } from '../dates'

// A small fixture timeline: one Jupiter MD (level 1) covering the whole
// range, with a Mars AD (level 2) and, inside it, a Mars PD (level 3)
// centered on 2025-05-15 — this is meant to look like a genuine dasha
// confluence around the loss-anchor date.
function fixturePeriods(): DashaPeriod[] {
  return [
    { level: 1, lord: 'Jupiter', start: parseDate('2020-01-01'), end: parseDate('2030-01-01') },
    { level: 2, lord: 'Mars', start: parseDate('2025-01-01'), end: parseDate('2025-12-31') },
    { level: 3, lord: 'Venus', start: parseDate('2025-01-01'), end: parseDate('2025-04-01') },
    { level: 3, lord: 'Mars', start: parseDate('2025-04-01'), end: parseDate('2025-07-01') }, // confluence window
    { level: 3, lord: 'Saturn', start: parseDate('2025-07-01'), end: parseDate('2025-12-31') },
  ]
}

describe('intensityAt', () => {
  it('sums depth-weighted contributions for matching significators only', () => {
    const periods = fixturePeriods()
    const sig = { Mars: 1.0 }
    // 2025-05-15 is inside Mars AD (level 2, weight 2) and Mars PD (level 3, weight 4) => 2+4=6
    expect(intensityAt(periods, sig, parseDate('2025-05-15'))).toBe(6)
    // 2025-02-15 is inside Mars AD (level 2) but Venus PD (level 3, no match) => 2
    expect(intensityAt(periods, sig, parseDate('2025-02-15'))).toBe(2)
    // A date entirely outside the fixture (2040) has no matches at any level => 0
    expect(intensityAt(periods, sig, parseDate('2040-01-01'))).toBe(0)
  })

  it('is zero when no configured significator matches anything', () => {
    const periods = fixturePeriods()
    expect(intensityAt(periods, { Ketu: 1.0 }, parseDate('2025-05-15'))).toBe(0)
  })
})

describe('buildCurve + localMax', () => {
  it('finds the true peak within the proximity window at the confluence date', () => {
    const periods = fixturePeriods()
    const curve = buildCurve(periods, { Mars: 1.0 }, parseDate('2025-01-01'), parseDate('2025-12-31'), 2)
    const peak = localMax(curve, parseDate('2025-05-15'), 45)
    expect(peak).toBeDefined()
    expect(peak!.intensity).toBe(6)
  })

  it('returns undefined when the curve has no points in the window', () => {
    const periods = fixturePeriods()
    const curve = buildCurve(periods, { Mars: 1.0 }, parseDate('2025-01-01'), parseDate('2025-02-01'), 2)
    expect(localMax(curve, parseDate('2026-06-01'), 45)).toBeUndefined()
  })
})

describe('percentile thresholds', () => {
  it('topDecileThreshold >= topTercileThreshold for a spread distribution', () => {
    const curve = Array.from({ length: 100 }, (_, i) => ({ date: parseDate('2025-01-01'), intensity: i }))
    expect(topDecileThreshold(curve)).toBeGreaterThanOrEqual(topTercileThreshold(curve))
    expect(percentileThreshold(curve, 0.9)).toBe(89) // nearest-rank of the 90th percentile over 0..99
  })

  it('handles an empty curve without throwing', () => {
    expect(percentileThreshold([], 0.9)).toBe(0)
  })
})

describe('fractionAtOrAbove / variance', () => {
  it('reports 0 variance for a flat (degenerate) curve', () => {
    const flat = Array.from({ length: 10 }, () => ({ date: parseDate('2025-01-01'), intensity: 5 }))
    expect(variance(flat)).toBe(0)
  })

  it('fractionAtOrAbove(threshold=max) is small for a spread distribution', () => {
    const curve = Array.from({ length: 100 }, (_, i) => ({ date: parseDate('2025-01-01'), intensity: i }))
    const threshold = topDecileThreshold(curve)
    const frac = fractionAtOrAbove(curve, threshold)
    expect(frac).toBeGreaterThan(0)
    expect(frac).toBeLessThan(0.15)
  })
})

describe('circularShiftPeriods', () => {
  it('preserves each period duration for a non-wrapping shift', () => {
    const periods: DashaPeriod[] = [{ level: 1, lord: 'Mars', start: parseDate('2020-01-01'), end: parseDate('2020-02-01') }]
    const bounds = { start: parseDate('2000-01-01'), end: parseDate('2040-01-01') }
    const shifted = circularShiftPeriods(periods, 100, bounds.start, bounds.end)
    expect(shifted).toHaveLength(1)
    const durationMs = shifted[0].end.getTime() - shifted[0].start.getTime()
    expect(durationMs).toBe(parseDate('2020-02-01').getTime() - parseDate('2020-01-01').getTime())
  })

  it('splits a period that straddles the boundary after shifting into two pieces', () => {
    // 30-day bounds [day0, day30). Period spans [day24, day29) — a 5-day
    // period. Shift +5 days: start wraps to day29 (still inside bounds),
    // end wraps to day4 (having crossed past day30 back to day0) — the
    // shifted period straddles the boundary and must be split.
    const boundsStart = parseDate('2020-01-01')
    const boundsEnd = parseDate('2020-01-31')
    const periods: DashaPeriod[] = [{ level: 1, lord: 'Mars', start: parseDate('2020-01-25'), end: parseDate('2020-01-30') }]
    const shifted = circularShiftPeriods(periods, 5, boundsStart, boundsEnd)
    expect(shifted.length).toBe(2)
    // combined duration should still equal the original 5 days
    const total = shifted.reduce((s, p) => s + (p.end.getTime() - p.start.getTime()), 0)
    expect(total).toBe(5 * 86_400_000)
  })

  it('is a no-op when bounds are degenerate (end <= start)', () => {
    const periods: DashaPeriod[] = [{ level: 1, lord: 'Mars', start: parseDate('2020-01-01'), end: parseDate('2020-02-01') }]
    const shifted = circularShiftPeriods(periods, 10, parseDate('2020-01-01'), parseDate('2020-01-01'))
    expect(shifted).toBe(periods)
  })
})
