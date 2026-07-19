/**
 * shape_scoring.test.ts — SYNTHETIC fixtures only, all dates pre-2020.
 * See model_interface.test.ts header for the sealed-test-split discipline.
 */
import { describe, it, expect } from 'vitest'
import { scoreCurveEvent, runBlindBattery, toleranceDaysFor, isSecondaryBattery, type CurveEvent } from '../shape_scoring'
import type { CurvePoint } from '../../curve'

const D = (y: number, m: number, d: number) => new Date(Date.UTC(y, m - 1, d))

/**
 * A curve with a clear spike centered on 1995-06-15, ZERO (not a nonzero
 * baseline) elsewhere over a 1990-2000 span. Background must be exactly 0,
 * not a low nonzero value: `scoreCurveEvent`'s point/interval logic (like
 * production `scoreEvent`/`scoreIntervalEvent` in checks.ts) requires
 * `peak.intensity > 0` for a pass — a nonzero background would make the
 * curve degenerate (>15% of days "at or above" a near-zero top-decile
 * threshold) and every window trivially pass regardless of the spike,
 * defeating what these tests are checking.
 */
function spikeCurve(): CurvePoint[] {
  const out: CurvePoint[] = []
  const start = D(1990, 1, 1).getTime()
  const end = D(2000, 1, 1).getTime()
  const spike = D(1995, 6, 15).getTime()
  for (let t = start; t <= end; t += 5 * 86_400_000) {
    const daysFromSpike = Math.abs(t - spike) / 86_400_000
    out.push({ date: new Date(t), intensity: daysFromSpike < 10 ? 10 : 0 })
  }
  return out
}

describe('scoreCurveEvent — point shape', () => {
  it('passes when the true date sits inside the spike and within tolerance', () => {
    const curve = spikeCurve()
    const event: CurveEvent = { eventId: 'p1', shape: 'point', dateConfidence: 'exact', eventDate: D(1995, 6, 20) }
    const score = scoreCurveEvent(curve, event, 0.9)
    expect(score.pass).toBe(true)
    expect(score.withinProximity).toBe(true)
  })

  it('fails when the true date is far from any high-intensity region', () => {
    const curve = spikeCurve()
    const event: CurveEvent = { eventId: 'p2', shape: 'point', dateConfidence: 'exact', eventDate: D(1991, 1, 1) }
    const score = scoreCurveEvent(curve, event, 0.9)
    expect(score.pass).toBe(false)
  })

  it('month_known tolerance (±75d) can pass where exact (±45d) would fail, for the same off-center date', () => {
    // A sparse (gapped) curve so a ±45d window can genuinely contain zero
    // points while a ±75d window reaches into the high-intensity cluster —
    // the dense spikeCurve() above always has SOME point in any window on
    // its 10-year span, which would make withinProximity trivially true
    // regardless of tolerance and defeat the point of this test.
    const spike = D(1995, 6, 15).getTime()
    // Narrow cluster (±5d around the spike center) and background elsewhere.
    // farDate is 60d after the cluster center: exact's ±45d window is
    // [15,105]d and never reaches the cluster's [-5,5]d span; month_known's
    // ±75d window is [-15,135]d and does.
    const cluster: CurvePoint[] = [-5, 0, 5].map((d) => ({ date: new Date(spike + d * 86_400_000), intensity: 10 }))
    const background: CurvePoint[] = [-900, -500, 500, 900].map((d) => ({ date: new Date(spike + d * 86_400_000), intensity: 1 }))
    const curve = [...background, ...cluster].sort((a, b) => a.date.getTime() - b.date.getTime())
    const farDate = new Date(spike + 60 * 86_400_000) // 60 days after the cluster center
    const exactEvent: CurveEvent = { eventId: 'p3', shape: 'point', dateConfidence: 'exact', eventDate: farDate }
    const monthEvent: CurveEvent = { eventId: 'p3', shape: 'point', dateConfidence: 'month_known', eventDate: farDate }
    const exactScore = scoreCurveEvent(curve, exactEvent, 0.9)
    const monthScore = scoreCurveEvent(curve, monthEvent, 0.9)
    expect(exactScore.withinProximity).toBe(false) // ±45d window [15,105]d never reaches the cluster's [-5,5]d span
    expect(monthScore.withinProximity).toBe(true) // ±75d window [-15,135]d overlaps the cluster
    expect(monthScore.pass).toBe(true)
  })

  it('year_only is flagged secondaryBattery=true', () => {
    const curve = spikeCurve()
    const event: CurveEvent = { eventId: 'p4', shape: 'point', dateConfidence: 'year_only', eventDate: D(1995, 6, 15) }
    const score = scoreCurveEvent(curve, event, 0.9)
    expect(score.secondaryBattery).toBe(true)
  })
})

describe('scoreCurveEvent — interval shape (DR-13(b): overlap, not distance)', () => {
  it('passes when part of the interval overlaps the top-decile region', () => {
    const curve = spikeCurve()
    const event: CurveEvent = { eventId: 'i1', shape: 'interval', dateConfidence: 'exact', intervalStart: D(1995, 6, 1), intervalEnd: D(1995, 7, 1) }
    const score = scoreCurveEvent(curve, event, 0.9)
    expect(score.pass).toBe(true)
    expect(score.overlapFraction).toBeGreaterThan(0)
  })

  it('fails when the interval never touches the top-decile region', () => {
    const curve = spikeCurve()
    const event: CurveEvent = { eventId: 'i2', shape: 'interval', dateConfidence: 'exact', intervalStart: D(1991, 1, 1), intervalEnd: D(1991, 3, 1) }
    const score = scoreCurveEvent(curve, event, 0.9)
    expect(score.pass).toBe(false)
    expect(score.overlapFraction).toBe(0)
  })
})

describe('scoreCurveEvent — chain shape (DR-13(c): any milestone hits -> chain hits)', () => {
  it('passes if any one milestone passes, even if others fail', () => {
    const curve = spikeCurve()
    const event: CurveEvent = {
      eventId: 'c1',
      shape: 'chain',
      dateConfidence: 'exact',
      milestones: [
        { eventId: 'c1_m1', shape: 'point', dateConfidence: 'exact', eventDate: D(1991, 1, 1) }, // far, fails
        { eventId: 'c1_m2', shape: 'point', dateConfidence: 'exact', eventDate: D(1995, 6, 15) }, // hits
      ],
    }
    const score = scoreCurveEvent(curve, event, 0.9)
    expect(score.pass).toBe(true)
    expect(score.milestoneScores).toHaveLength(2)
    expect(score.milestoneScores!.filter((m) => m.pass)).toHaveLength(1)
  })

  it('fails only if every milestone fails', () => {
    const curve = spikeCurve()
    const event: CurveEvent = {
      eventId: 'c2',
      shape: 'chain',
      dateConfidence: 'exact',
      milestones: [
        { eventId: 'c2_m1', shape: 'point', dateConfidence: 'exact', eventDate: D(1991, 1, 1) },
        { eventId: 'c2_m2', shape: 'point', dateConfidence: 'exact', eventDate: D(1992, 1, 1) },
      ],
    }
    const score = scoreCurveEvent(curve, event, 0.9)
    expect(score.pass).toBe(false)
  })

  it('throws for a chain with zero milestones (a recording error, per DR-13(c))', () => {
    const curve = spikeCurve()
    const event: CurveEvent = { eventId: 'c3', shape: 'chain', dateConfidence: 'exact', milestones: [] }
    expect(() => scoreCurveEvent(curve, event, 0.9)).toThrow(/no milestones/)
  })
})

describe('tolerance + secondary-battery helpers', () => {
  it('toleranceDaysFor matches DR-13(d) exactly', () => {
    expect(toleranceDaysFor('exact')).toBe(45)
    expect(toleranceDaysFor('month_known')).toBe(75)
  })
  it('isSecondaryBattery is true only for year_only', () => {
    expect(isSecondaryBattery('exact')).toBe(false)
    expect(isSecondaryBattery('month_known')).toBe(false)
    expect(isSecondaryBattery('year_only')).toBe(true)
  })
})

describe('runBlindBattery', () => {
  it('excludes year_only events from the primary battery by default', () => {
    const curve = spikeCurve()
    const events: CurveEvent[] = [
      { eventId: 'a', shape: 'point', dateConfidence: 'exact', eventDate: D(1995, 6, 15) },
      { eventId: 'b', shape: 'point', dateConfidence: 'year_only', eventDate: D(1996, 1, 1) },
    ]
    const result = runBlindBattery(() => curve, events, 2 / 3, false)
    expect(result.scoredCount).toBe(1)
  })

  it('includes year_only events when includeSecondary=true', () => {
    const curve = spikeCurve()
    const events: CurveEvent[] = [
      { eventId: 'a', shape: 'point', dateConfidence: 'exact', eventDate: D(1995, 6, 15) },
      { eventId: 'b', shape: 'point', dateConfidence: 'year_only', eventDate: D(1996, 1, 1) },
    ]
    const result = runBlindBattery(() => curve, events, 2 / 3, true)
    expect(result.scoredCount).toBe(2)
  })
})
