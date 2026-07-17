import { describe, it, expect } from 'vitest'
import { scoreEvent, checkCurveNotDegenerate, runBlindBattery, runShuffledControls, PROXIMITY_DAYS } from '../checks'
import { buildCurve, type DashaPeriod } from '../curve'
import { parseDate, addDays } from '../dates'

// A richer, more Vimśottarī-shaped fixture for the anti-gaming test: a
// constant MD, then a sequence of ~200-day AD blocks each subdivided into
// 8 ~25-day PD blocks cycling through all 9 grahas — mimics the real
// chart's nested cadence closely enough that "top-decile is <15% of days"
// is a meaningful, non-trivial check rather than an artifact of a tiny
// hand-built fixture.
function realisticPeriods(): DashaPeriod[] {
  const lords = ['Mars', 'Venus', 'Saturn', 'Mercury', 'Sun', 'Moon', 'Jupiter', 'Rahu', 'Ketu']
  const periods: DashaPeriod[] = [{ level: 1, lord: 'Jupiter', start: parseDate('2020-01-01'), end: parseDate('2030-01-01') }]
  const rangeEnd = parseDate('2028-01-01')
  let cursor = parseDate('2023-01-01')
  let adIdx = 0
  while (cursor.getTime() < rangeEnd.getTime()) {
    const adLord = lords[adIdx % lords.length]
    const adEnd = addDays(cursor, 200)
    periods.push({ level: 2, lord: adLord, start: cursor, end: adEnd })
    let pdCursor = cursor
    for (let i = 0; i < 8; i++) {
      const pdLord = lords[(adIdx + i) % lords.length]
      const pdEnd = i === 7 ? adEnd : addDays(pdCursor, 25)
      periods.push({ level: 3, lord: pdLord, start: pdCursor, end: pdEnd })
      pdCursor = pdEnd
    }
    cursor = adEnd
    adIdx++
  }
  return periods
}

const BOUNDS_START = parseDate('1984-02-05')
const BOUNDS_END = parseDate('2034-12-31')

// A chart-shaped fixture: Jupiter MD, then a Mars sub-period confluence
// right around the loss-anchor date, and a Venus+Jupiter confluence right
// around the windfall-anchor date — mirrors the mechanism this harness
// looks for on the real chart without needing a live call.
function fixturePeriods(): DashaPeriod[] {
  return [
    { level: 1, lord: 'Jupiter', start: parseDate('1975-08-18'), end: parseDate('1991-08-18') },
    { level: 1, lord: 'Saturn', start: parseDate('1991-08-18'), end: parseDate('2010-08-18') },
    { level: 1, lord: 'Mercury', start: parseDate('2010-08-18'), end: parseDate('2027-08-18') },
    // windfall confluence: Venus AD + Jupiter PD around 2010-07-01 (just inside the Saturn MD)
    { level: 2, lord: 'Venus', start: parseDate('2010-01-01'), end: parseDate('2010-10-01') },
    { level: 3, lord: 'Jupiter', start: parseDate('2010-05-01'), end: parseDate('2010-08-01') },
    // loss confluence: Mars AD + Mars PD around 2025-05-15 (inside Mercury MD)
    { level: 2, lord: 'Mars', start: parseDate('2025-01-01'), end: parseDate('2025-12-31') },
    { level: 3, lord: 'Mars', start: parseDate('2025-04-01'), end: parseDate('2025-07-01') },
    // filler elsewhere so the 5yr windows aren't trivially all-zero except at the anchor
    { level: 3, lord: 'Venus', start: parseDate('2025-07-01'), end: parseDate('2025-09-01') },
    { level: 3, lord: 'Saturn', start: parseDate('2025-09-01'), end: parseDate('2025-12-31') },
  ]
}

describe('scoreEvent', () => {
  it('passes when a matching confluence sits within the proximity window at top-decile', () => {
    const periods = fixturePeriods()
    const score = scoreEvent(periods, { Mars: 1.0 }, 'loss', parseDate('2025-05-15'), BOUNDS_START, BOUNDS_END, 0.9)
    expect(score.within_proximity).toBe(true)
    expect(score.pass).toBe(true)
    expect(Math.abs(score.peak_lag_days as number)).toBeLessThanOrEqual(PROXIMITY_DAYS)
  })

  it('fails when the significator never runs near the event', () => {
    const periods = fixturePeriods()
    const score = scoreEvent(periods, { Ketu: 1.0 }, 'nomatch', parseDate('2025-05-15'), BOUNDS_START, BOUNDS_END, 0.9)
    expect(score.pass).toBe(false)
  })

  it('tags every score with the documented peak_basis', () => {
    const periods = fixturePeriods()
    const score = scoreEvent(periods, { Mars: 1.0 }, 'loss', parseDate('2025-05-15'), BOUNDS_START, BOUNDS_END, 0.9)
    expect(score.peak_basis).toBe('dasha_lord_confluence_v1')
  })
})

describe('checkCurveNotDegenerate', () => {
  it('fails variance_ok for a flat curve', () => {
    const flat = Array.from({ length: 20 }, () => ({ date: parseDate('2025-01-01'), intensity: 3 }))
    const result = checkCurveNotDegenerate(flat)
    expect(result.variance_ok).toBe(false)
    expect(result.pass).toBe(false)
  })

  it('passes both sub-checks for a chart-realistic curve', () => {
    const periods = realisticPeriods()
    const curve = buildCurve(periods, { Mars: 1.0 }, parseDate('2023-01-01'), parseDate('2028-01-01'), 5)
    const result = checkCurveNotDegenerate(curve)
    expect(result.variance).toBeGreaterThan(0)
    expect(result.top_decile_fraction).toBeLessThan(0.15)
    expect(result.pass).toBe(true)
  })
})

describe('runBlindBattery + runShuffledControls', () => {
  it('scores multiple events and reports hit rate + lead/lag distribution', () => {
    const periods = fixturePeriods()
    const events = [
      { event_id: 'loss', date: parseDate('2025-05-15'), significators: { Mars: 1.0 } },
      { event_id: 'windfall', date: parseDate('2010-07-01'), significators: { Venus: 1.0, Jupiter: 1.0 } },
      { event_id: 'nomatch', date: parseDate('1999-01-01'), significators: { Ketu: 1.0 } },
    ]
    const result = runBlindBattery(periods, events, BOUNDS_START, BOUNDS_END)
    expect(result.scored_count).toBe(3)
    expect(result.hit_count).toBeGreaterThanOrEqual(1)
    expect(result.hit_rate).toBeCloseTo(result.hit_count / 3, 5)
  })

  it('shuffled controls return one hit_rate per requested shift, deterministically spaced', () => {
    const periods = fixturePeriods()
    const events = [{ event_id: 'loss', date: parseDate('2025-05-15'), significators: { Mars: 1.0 } }]
    const shifts = runShuffledControls(periods, events, BOUNDS_START, BOUNDS_END, 4)
    expect(shifts).toHaveLength(4)
    // shift magnitudes must be strictly increasing and distinct (deterministic spacing, not random overlap)
    const mags = shifts.map((s) => s.shift_days)
    expect(new Set(mags).size).toBe(4)
    expect(mags[0]).toBeLessThan(mags[1])
  })
})
