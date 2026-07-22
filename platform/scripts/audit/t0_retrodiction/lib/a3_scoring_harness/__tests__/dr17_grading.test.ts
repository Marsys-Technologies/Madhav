import { describe, it, expect } from 'vitest'
import {
  DR17_GRADE_WEIGHTS,
  DR17_ANTI_HIT_WEIGHT,
  TIE_BAND_WIDTHS_DAYS,
  DR13D_SUBSTITUTE_TIE_BAND_WIDTHS_DAYS,
  tierForDateConfidence,
  computeControlBaseline,
  findLocalMaxima,
  dedupeByTieBand,
  gradeCurveEvent,
  type GradingEvent,
} from '../dr17_grading'
import type { CurvePoint } from '../../curve'

function mkCurve(startIso: string, values: number[], stepDays = 5): CurvePoint[] {
  const start = new Date(startIso + 'T00:00:00Z')
  return values.map((v, i) => ({ date: new Date(start.getTime() + i * stepDays * 86_400_000), intensity: v }))
}

describe('dr17_grading: NP-D4B-001 committed weights', () => {
  it('matches the packet-committed six-value vector verbatim', () => {
    expect(DR17_GRADE_WEIGHTS).toEqual({ peak: 1.0, sub_peak: 0.75, elevated: 0.5, neutral: 0.0, contra: -0.5 })
    expect(DR17_ANTI_HIT_WEIGHT).toBe(-1.0)
  })
  it('is frozen (cannot be mutated by a caller)', () => {
    expect(Object.isFrozen(DR17_GRADE_WEIGHTS)).toBe(true)
  })
})

describe('dr17_grading: NP-D4B-003 tie-band tables', () => {
  it('adopted table matches packet §4 verbatim', () => {
    expect(TIE_BAND_WIDTHS_DAYS).toEqual({ day: 3, week: 7, month: 45, year: 180 })
  })
  it('DR-13(d) substitute table replaces only day/month per condition (d)', () => {
    expect(DR13D_SUBSTITUTE_TIE_BAND_WIDTHS_DAYS).toEqual({ day: 45, week: 7, month: 75, year: 180 })
  })
  it('tierForDateConfidence maps the existing shape_scoring vocabulary', () => {
    expect(tierForDateConfidence('exact')).toBe('day')
    expect(tierForDateConfidence('month_known')).toBe('month')
    expect(tierForDateConfidence('year_only')).toBe('year')
  })
})

describe('findLocalMaxima', () => {
  it('finds a single interior peak', () => {
    const curve = mkCurve('2020-01-01', [0, 1, 3, 1, 0])
    const maxima = findLocalMaxima(curve)
    expect(maxima).toHaveLength(1)
    expect(maxima[0].index).toBe(2)
    expect(maxima[0].intensity).toBe(3)
  })
  it('finds multiple local maxima (multi-modal density, DR-15(a))', () => {
    const curve = mkCurve('2020-01-01', [0, 2, 0, 5, 0, 1, 0])
    const maxima = findLocalMaxima(curve)
    expect(maxima.map((m) => m.index)).toEqual([1, 3, 5])
  })
  it('collapses a plateau to one maximum at its onset', () => {
    const curve = mkCurve('2020-01-01', [0, 1, 4, 4, 4, 1, 0])
    const maxima = findLocalMaxima(curve)
    expect(maxima).toHaveLength(1)
    expect(maxima[0].index).toBe(2)
  })
  it('treats monotonically increasing then flat-to-end as a trailing maximum', () => {
    const curve = mkCurve('2020-01-01', [0, 1, 2, 3])
    const maxima = findLocalMaxima(curve)
    expect(maxima.map((m) => m.index)).toEqual([3])
  })
  it('an all-zero (degenerate) curve is one flat maximum at index 0, not many', () => {
    const curve = mkCurve('2020-01-01', [0, 0, 0, 0])
    const maxima = findLocalMaxima(curve)
    expect(maxima).toHaveLength(1)
    expect(maxima[0].index).toBe(0)
  })
})

describe('dedupeByTieBand', () => {
  it('drops a lower-ranked maximum within the tie-band of a kept higher one', () => {
    const maxima = [
      { index: 0, date: new Date('2020-01-01T00:00:00Z'), intensity: 5 },
      { index: 1, date: new Date('2020-01-03T00:00:00Z'), intensity: 4 }, // 2 days from the kept peak
      { index: 2, date: new Date('2020-06-01T00:00:00Z'), intensity: 3 }, // far away, kept
    ]
    const deduped = dedupeByTieBand(maxima, 3)
    expect(deduped).toHaveLength(2)
    expect(deduped.map((m) => m.intensity)).toEqual([5, 3])
  })
  it('a wider tie-band merges more aggressively (monotone in width)', () => {
    const maxima = [
      { index: 0, date: new Date('2020-01-01T00:00:00Z'), intensity: 5 },
      { index: 1, date: new Date('2020-02-10T00:00:00Z'), intensity: 4 }, // 40 days away
    ]
    expect(dedupeByTieBand(maxima, 3)).toHaveLength(2) // day tie-band: not merged
    expect(dedupeByTieBand(maxima, 45)).toHaveLength(1) // DR-13(d) substitute month width: merged
  })
})

describe('computeControlBaseline', () => {
  it('computes per-index mean/stddev across control curves', () => {
    const controls = [mkCurve('2020-01-01', [0, 0, 0]), mkCurve('2020-01-01', [2, 2, 2])]
    const baseline = computeControlBaseline(controls)
    expect(baseline.meanByIndex).toEqual([1, 1, 1])
    expect(baseline.stdByIndex[0]).toBeCloseTo(1, 6)
  })
  it('throws on grid-length mismatch (mirrors ensemble_model.ts EnsembleGridMismatchError discipline)', () => {
    const controls = [mkCurve('2020-01-01', [0, 0, 0]), mkCurve('2020-01-01', [1, 1])]
    expect(() => computeControlBaseline(controls)).toThrow(/grid-length mismatch/)
  })
})

describe('gradeCurveEvent — the grade ladder', () => {
  const point: GradingEvent = {
    eventId: 'EVT.TEST.POINT',
    shape: 'point',
    dateConfidenceTier: 'day',
    matchToleranceDays: 45,
    eventDate: new Date('2020-03-01T00:00:00Z'),
  }

  it('grades peak: rank-1 live-active local max matches the true date', () => {
    // grid at 5-day steps from 2020-01-01; index for 2020-03-01 is day 60 -> index 12
    const values = new Array(30).fill(0)
    values[12] = 10 // exactly at the true date
    const curve = mkCurve('2020-01-01', values)
    const controls = [mkCurve('2020-01-01', new Array(30).fill(0)), mkCurve('2020-01-01', new Array(30).fill(0))]
    const baseline = computeControlBaseline(controls)
    const result = gradeCurveEvent(curve, point, baseline, 'test_model')
    expect(result.grade).toBe('peak')
    expect(result.weight).toBe(1.0)
    expect(result.antiHitApplied).toBe(false)
    expect(result.matchedPeakRank).toBe(1)
  })

  it('grades sub_peak: a non-rank-1 local max matches, rank-1 sits elsewhere', () => {
    const values = new Array(30).fill(0)
    values[12] = 5 // true-date peak (rank 2)
    values[25] = 10 // dominant peak elsewhere (rank 1)
    const curve = mkCurve('2020-01-01', values)
    const controls = [mkCurve('2020-01-01', new Array(30).fill(0))]
    const baseline = computeControlBaseline(controls)
    const result = gradeCurveEvent(curve, point, baseline, 'test_model')
    expect(result.grade).toBe('sub_peak')
    expect(result.weight).toBe(0.75)
    expect(result.matchedPeakRank).toBe(2)
  })

  it('grades elevated: true-date window sits on a wide above-baseline plateau that tapers into a genuine (far-away, out-of-tolerance) peak, so the plateau itself is never counted as its own local maximum', () => {
    // index 0..24 held at intensity 1 (an elevated but non-peaking plateau covering the true
    // date at index 12); index 25 spikes to 10 -- the plateau's rising edge, so [0..24] fails
    // findLocalMaxima's own local-max test (next-neighbor 10 > 1) and is correctly NOT registered
    // as a local maximum in its own right, only the index-25 spike is. That spike (day 125) is
    // 65 days from the true date (day 60) -- outside the ±45d point tolerance -- so it cannot
    // itself supply a peak/sub_peak match either. The true date's own window peak (intensity 1,
    // still above the all-zero control baseline) is what should land 'elevated'.
    const values = new Array(30).fill(1)
    values[25] = 10
    const curve = mkCurve('2020-01-01', values)
    const controls = [mkCurve('2020-01-01', new Array(30).fill(0))]
    const baseline = computeControlBaseline(controls)
    const result = gradeCurveEvent(curve, point, baseline, 'test_model')
    expect(result.grade).toBe('elevated')
    expect(result.weight).toBe(0.5)
  })

  it('grades neutral: curve indistinguishable from control everywhere', () => {
    const curve = mkCurve('2020-01-01', new Array(30).fill(1))
    const controls = [mkCurve('2020-01-01', new Array(30).fill(1)), mkCurve('2020-01-01', new Array(30).fill(1))]
    const baseline = computeControlBaseline(controls)
    const result = gradeCurveEvent(curve, point, baseline, 'test_model')
    expect(result.grade).toBe('neutral')
    expect(result.weight).toBe(0.0)
  })

  it('grades contra: model quiet at true date, live-active elsewhere, non-overlapping — anti-hit NOT applied (structurally inert)', () => {
    const values = new Array(30).fill(0)
    values[25] = 10 // active far from the true date (index 12), well outside ±45d tolerance at 5-day steps
    const curve = mkCurve('2020-01-01', values)
    const controls = [mkCurve('2020-01-01', new Array(30).fill(0))]
    const baseline = computeControlBaseline(controls)
    const result = gradeCurveEvent(curve, point, baseline, 'test_model')
    expect(result.grade).toBe('contra')
    expect(result.weight).toBe(-0.5)
    expect(result.antiHitApplied).toBe(false)
    expect(result.antiHitInertReason).toMatch(/valence/)
  })

  it('grades neutral (not contra) when quiet at the true date AND quiet everywhere else (honest non-finding, no elsewhere-wrong call)', () => {
    const curve = mkCurve('2020-01-01', new Array(30).fill(0))
    const controls = [mkCurve('2020-01-01', new Array(30).fill(0))]
    const baseline = computeControlBaseline(controls)
    const result = gradeCurveEvent(curve, point, baseline, 'test_model')
    expect(result.grade).toBe('neutral')
  })

  it('interval-shaped event: overlap-based matching (DR-13(b))', () => {
    const interval: GradingEvent = {
      eventId: 'EVT.TEST.INTERVAL',
      shape: 'interval',
      dateConfidenceTier: 'month',
      matchToleranceDays: 0,
      intervalStart: new Date('2020-02-01T00:00:00Z'),
      intervalEnd: new Date('2020-04-01T00:00:00Z'),
    }
    const values = new Array(30).fill(0)
    values[12] = 10 // 2020-03-01, inside [Feb 1, Apr 1]
    const curve = mkCurve('2020-01-01', values)
    const controls = [mkCurve('2020-01-01', new Array(30).fill(0))]
    const baseline = computeControlBaseline(controls)
    const result = gradeCurveEvent(curve, interval, baseline, 'test_model')
    expect(result.grade).toBe('peak')
  })

  it('throws on grid misalignment between curve and baseline (never silently mis-scores)', () => {
    const curve = mkCurve('2020-01-01', new Array(10).fill(1))
    const controls = [mkCurve('2020-01-01', new Array(30).fill(0))]
    const baseline = computeControlBaseline(controls)
    expect(() => gradeCurveEvent(curve, point, baseline, 'test_model')).toThrow(/grid misalignment/)
  })

  it('a wider (DR-13(d) substitute) tie-band can only merge MORE, never split a kept peak into two', () => {
    const values = new Array(30).fill(0)
    values[9] = 10 // true date is index 12 (day-tier ±45d tolerance covers this either way)
    values[12] = 9
    const curve = mkCurve('2020-01-01', values)
    const controls = [mkCurve('2020-01-01', new Array(30).fill(0))]
    const baseline = computeControlBaseline(controls)
    const adopted = gradeCurveEvent(curve, point, baseline, 'test_model', 'adopted')
    const sensitivity = gradeCurveEvent(curve, point, baseline, 'test_model', 'dr13d_sensitivity')
    // index 9 (day 45, intensity 10) and index 12 (day 60, intensity 9, the true date) are 15
    // days apart. Under the narrow ±3d adopted day-tier tie-band they are NOT merged (2 distinct
    // deduped maxima); under the wide ±45d DR-13(d)-substitute day-tier tie-band they ARE merged
    // into 1 (the higher-intensity one, index 9, kept). Both index 9 and index 12 independently
    // fall within the point-match tolerance (±45d, a SEPARATE, always-wider mechanism per
    // NP-D4B-003(e) "no role leakage") of the true date, so this specimen resolves 'peak' either
    // way here -- the tie-band's effect on THIS specimen's grade is a no-op, but its effect on the
    // DEDUPED COUNT (which feeds the aggregate census, not this single grade) is real and asserted
    // below. A grade-level flip is a real but rarer possibility the sensitivity recompute (driver
    // level, not this unit test) checks for across the full event/contender battery, per
    // NP-D4B-003(d)'s own framing ("may make a result look WORSE... never better").
    // (A third, trivial, intensity-0 "maximum" also always registers at the curve's flat trailing
    // tail, index 14 onward -- a boundary artifact of a monotonically-non-increasing tail always
    // being locally-maximal at its own start with nothing after it to compare to; see
    // findLocalMaxima's own doc comment. It never satisfies isAboveBaseline against a real
    // (non-negative-mean) control baseline, so it never affects a grade outcome, only the raw
    // deduped count -- disclosed here, not silently ignored.)
    expect(adopted.grade).toBe('peak')
    expect(adopted.dedupedMaximaCount).toBe(3)
    expect(sensitivity.grade).toBe('peak')
    expect(sensitivity.dedupedMaximaCount).toBe(1)
  })
})
