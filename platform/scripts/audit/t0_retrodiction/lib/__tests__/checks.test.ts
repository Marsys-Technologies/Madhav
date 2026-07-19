import { describe, it, expect } from 'vitest'
import {
  scoreEvent,
  checkCurveNotDegenerate,
  runBlindBattery,
  runShuffledControls,
  PROXIMITY_DAYS,
  scoreShapeAwareEvent,
  scorePointEvent,
  scoreIntervalEvent,
  scoreChainEvent,
  toleranceDaysFor,
  isSecondaryBattery,
  type ShapeAwareEvent,
} from '../checks'
import { buildCurve, circularShiftPeriods, type DashaPeriod } from '../curve'
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

// ---------------------------------------------------------------------------
// Shape-aware matcher (CR-47, DR-13/DIS.026, D-4a Lane A-1). Uses the same
// `fixturePeriods()` chart-shaped fixture as the point-only tests above —
// 'loss' (Mars confluence ~2025-05-15) and 'windfall' (Venus+Jupiter
// confluence ~2010-07) are the two named specimens carried from D-3's §G
// (score_g.py check_a/check_b) and BRIEF_D4A's gate item 2.
// ---------------------------------------------------------------------------

describe('toleranceDaysFor / isSecondaryBattery (DR-13(d))', () => {
  it('exact confidence keeps DR-11s ±45d figure unchanged', () => {
    expect(toleranceDaysFor('exact')).toBe(45)
  })
  it('month_known widens to ±75d', () => {
    expect(toleranceDaysFor('month_known')).toBe(75)
  })
  it('year_only routes to the secondary battery, never the primary hit-rate', () => {
    expect(isSecondaryBattery('year_only')).toBe(true)
    expect(isSecondaryBattery('exact')).toBe(false)
    expect(isSecondaryBattery('month_known')).toBe(false)
  })
})

describe('scorePointEvent (DR-13(a)/(d))', () => {
  it('named specimen: loss event scores nonzero fit at exact confidence (±45d)', () => {
    const periods = fixturePeriods()
    const event: ShapeAwareEvent = { event_id: 'loss', shape: 'point', date_confidence: 'exact', event_date: parseDate('2025-05-15') }
    const score = scorePointEvent(periods, { Mars: 1.0 }, event, BOUNDS_START, BOUNDS_END, 0.9)
    expect(score.shape).toBe('point')
    expect(score.pass).toBe(true)
    expect(score.peak?.intensity).toBeGreaterThan(0)
    expect(score.secondary_battery).toBe(false)
  })

  it('month_known confidence widens the proximity window so a peak just outside ±45d but inside ±75d still hits', () => {
    // Shift the fixture's Mars confluence slightly later so it lands outside ±45d
    // of the anchor date but inside ±75d, isolating the tolerance-scaling behavior.
    const periods: DashaPeriod[] = [
      { level: 1, lord: 'Mercury', start: parseDate('2010-08-18'), end: parseDate('2027-08-18') },
      { level: 2, lord: 'Mars', start: parseDate('2025-07-15'), end: parseDate('2025-09-15') },
      { level: 3, lord: 'Mars', start: parseDate('2025-07-20'), end: parseDate('2025-08-10') },
    ]
    const anchor = parseDate('2025-05-15')
    const exactEvent: ShapeAwareEvent = { event_id: 'delayed', shape: 'point', date_confidence: 'exact', event_date: anchor }
    const monthEvent: ShapeAwareEvent = { event_id: 'delayed', shape: 'point', date_confidence: 'month_known', event_date: anchor }
    const exactScore = scorePointEvent(periods, { Mars: 1.0 }, exactEvent, BOUNDS_START, BOUNDS_END, 0.9)
    const monthScore = scorePointEvent(periods, { Mars: 1.0 }, monthEvent, BOUNDS_START, BOUNDS_END, 0.9)
    // The confluence sits ~61 days out: outside ±45d (exact) so no in-window curve point has
    // nonzero intensity -> at_or_above_threshold/pass false; inside ±75d (month_known) so the
    // widened window DOES catch the nonzero peak -> pass true. (within_proximity alone is not
    // the discriminating signal here — see localMax: it is true whenever the window has ANY
    // curve coverage, zero-intensity or not; at_or_above_threshold/pass is the real hit test.)
    expect(exactScore.pass).toBe(false)
    expect(exactScore.peak?.intensity ?? 0).toBe(0)
    expect(monthScore.pass).toBe(true)
    expect(monthScore.peak?.intensity).toBeGreaterThan(0)
  })
})

describe('scoreIntervalEvent (DR-13(b) — overlap, not distance-to-a-point)', () => {
  it('named specimen: windfall scores as INTERVAL over the native-ratified [2010-07 -> 2011-03] window with nonzero overlap', () => {
    const periods = fixturePeriods()
    const event: ShapeAwareEvent = {
      event_id: 'windfall',
      shape: 'interval',
      date_confidence: 'month_known',
      interval_start: parseDate('2010-07-01'),
      interval_end: parseDate('2011-03-31'),
    }
    const score = scoreShapeAwareEvent(periods, { Venus: 1.0, Jupiter: 1.0 }, event, BOUNDS_START, BOUNDS_END, 0.9)
    expect(score.shape).toBe('interval')
    expect(score.pass).toBe(true)
    expect(score.overlap_fraction).toBeGreaterThan(0)
    expect(score.peak?.intensity).toBeGreaterThan(0)
  })

  it('a non-overlapping interval scores zero overlap and fails, not a false hit', () => {
    const periods = fixturePeriods()
    const event: ShapeAwareEvent = {
      event_id: 'no-overlap',
      shape: 'interval',
      date_confidence: 'month_known',
      interval_start: parseDate('1999-01-01'),
      interval_end: parseDate('1999-06-01'),
    }
    const score = scoreIntervalEvent(periods, { Venus: 1.0, Jupiter: 1.0 }, event, BOUNDS_START, BOUNDS_END, 0.9)
    expect(score.overlap_fraction).toBe(0)
    expect(score.pass).toBe(false)
  })
})

describe('scoreChainEvent (DR-13(c) — per-milestone scoring)', () => {
  it('a synthetic chain event scores each milestone independently, with a chain-level pass if any milestone hits', () => {
    const periods = fixturePeriods()
    const chain: ShapeAwareEvent = {
      event_id: 'synthetic-chain',
      shape: 'chain',
      date_confidence: 'year_only',
      milestones: [
        // milestone 1: no confluence anywhere near it — expected to fail
        { event_id: 'synthetic-chain-m1', shape: 'point', date_confidence: 'exact', event_date: parseDate('1999-01-01') },
        // milestone 2: sits on the windfall confluence — expected to hit
        {
          event_id: 'synthetic-chain-m2',
          shape: 'interval',
          date_confidence: 'month_known',
          interval_start: parseDate('2010-07-01'),
          interval_end: parseDate('2010-10-01'),
        },
        // milestone 3: sits on the loss confluence — expected to hit
        { event_id: 'synthetic-chain-m3', shape: 'point', date_confidence: 'exact', event_date: parseDate('2025-05-15') },
      ],
    }
    const significators = { Mars: 1.0, Venus: 1.0, Jupiter: 1.0 }
    const score = scoreChainEvent(periods, significators, chain, BOUNDS_START, BOUNDS_END, 0.9)
    expect(score.shape).toBe('chain')
    expect(score.milestone_scores).toHaveLength(3)
    expect(score.milestone_scores?.[0].pass).toBe(false)
    expect(score.milestone_scores?.[1].pass).toBe(true)
    expect(score.milestone_scores?.[2].pass).toBe(true)
    expect(score.pass).toBe(true) // chain-level pass: at least one milestone hit
  })
})

describe('scoreShapeAwareEvent control-mirroring (DR-13(e))', () => {
  it('applies the identical shape/tolerance treatment to a shuffled-control curve as to the real one', () => {
    const periods = fixturePeriods()
    const shifted = circularShiftPeriods(periods, 1000, BOUNDS_START, BOUNDS_END)
    const event: ShapeAwareEvent = {
      event_id: 'windfall',
      shape: 'interval',
      date_confidence: 'month_known',
      interval_start: parseDate('2010-07-01'),
      interval_end: parseDate('2011-03-31'),
    }
    // Same function, same event, only the periods argument differs (real vs shuffled) —
    // no branch in scoreShapeAwareEvent/scoreIntervalEvent inspects "is this a control".
    const real = scoreShapeAwareEvent(periods, { Venus: 1.0, Jupiter: 1.0 }, event, BOUNDS_START, BOUNDS_END, 0.9)
    const control = scoreShapeAwareEvent(shifted, { Venus: 1.0, Jupiter: 1.0 }, event, BOUNDS_START, BOUNDS_END, 0.9)
    expect(real.shape).toBe(control.shape)
    expect(real.date_confidence).toBe(control.date_confidence)
    // Not asserting on pass/overlap equality (the whole point of the shift is to change them) —
    // asserting the SCORING RULE APPLIED is identical, i.e. both went through scoreIntervalEvent.
    expect(typeof real.overlap_fraction).toBe('number')
    expect(typeof control.overlap_fraction).toBe('number')
  })
})
