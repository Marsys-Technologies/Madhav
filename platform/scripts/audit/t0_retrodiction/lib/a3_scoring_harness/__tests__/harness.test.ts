/**
 * harness.test.ts — SYNTHETIC fixtures only, all dates pre-2020. See
 * model_interface.test.ts header for the sealed-test-split discipline.
 *
 * This file's `runComparativeHarness` tests ARE the "acceptance proof is
 * demonstrating this refusal live" deliverable from BRIEF_D4A.md Lane A-3
 * deliverable 4 — a one-sided config attempt actually gets rejected, run
 * via `npx vitest run` (not asserted in prose).
 */
import { describe, it, expect } from 'vitest'
import { runMirroredScoringHarness, runComparativeHarness, assertMirrored, ControlMirroringViolationError, type MirroredScoringParams } from '../harness'
import { pratyantarLordModel } from '../model_interface'
import type { ChartContext } from '../model_interface'
import type { CurveEvent } from '../shape_scoring'
import type { DashaPeriod } from '../../curve'

const D = (y: number, m: number, d: number) => new Date(Date.UTC(y, m - 1, d))
const BOUNDS_START = D(1990, 1, 1)
const BOUNDS_END = D(2010, 1, 1)

function syntheticChart(): ChartContext {
  const periods: DashaPeriod[] = [
    { level: 1, lord: 'Jupiter', start: D(1990, 1, 1), end: D(2005, 1, 1) },
    { level: 2, lord: 'Venus', start: D(1995, 1, 1), end: D(1996, 1, 1) },
    { level: 3, lord: 'Venus', start: D(1995, 5, 1), end: D(1995, 8, 1) },
  ]
  return { chartId: 'synthetic-chart-harness', substrate: { periods } }
}

function syntheticEvents(): CurveEvent[] {
  return [
    { eventId: 'e1', shape: 'point', dateConfidence: 'exact', eventDate: D(1995, 6, 15) },
    { eventId: 'e2', shape: 'interval', dateConfidence: 'exact', intervalStart: D(1995, 5, 15), intervalEnd: D(1995, 7, 15) },
  ]
}

const BASE_PARAMS: MirroredScoringParams = { percentile: 0.9, shuffleCount: 3, includeSecondaryBattery: false }

describe('assertMirrored — the structural check', () => {
  it('is silent (no throw) for identical params', () => {
    expect(() => assertMirrored(BASE_PARAMS, { ...BASE_PARAMS })).not.toThrow()
  })

  it('throws ControlMirroringViolationError naming the differing field when percentile is loosened only for the real chart', () => {
    const looser = { ...BASE_PARAMS, percentile: 0.7 }
    expect(() => assertMirrored(looser, BASE_PARAMS)).toThrow(ControlMirroringViolationError)
    try {
      assertMirrored(looser, BASE_PARAMS)
      expect.unreachable()
    } catch (err) {
      expect((err as Error).message).toContain('percentile')
      expect((err as Error).message).toContain('0.7')
    }
  })

  it('throws when shuffleCount differs', () => {
    expect(() => assertMirrored(BASE_PARAMS, { ...BASE_PARAMS, shuffleCount: 1 })).toThrow(ControlMirroringViolationError)
  })

  it('throws when includeSecondaryBattery differs', () => {
    expect(() => assertMirrored(BASE_PARAMS, { ...BASE_PARAMS, includeSecondaryBattery: true })).toThrow(ControlMirroringViolationError)
  })

  it('reports every differing field, not just the first', () => {
    const allLoosened: MirroredScoringParams = { percentile: 0.5, shuffleCount: 1, includeSecondaryBattery: true }
    try {
      assertMirrored(allLoosened, BASE_PARAMS)
      expect.unreachable()
    } catch (err) {
      const msg = (err as Error).message
      expect(msg).toContain('percentile')
      expect(msg).toContain('shuffleCount')
      expect(msg).toContain('includeSecondaryBattery')
    }
  })
})

describe('runComparativeHarness — LIVE REFUSAL DEMONSTRATION (deliverable 4 acceptance proof)', () => {
  const model = pratyantarLordModel({ synthetic_event_class: { Venus: 1.0 } })
  const chart = syntheticChart()
  const events = syntheticEvents()

  it('REJECTS a one-sided config: real chart loosened to percentile=0.5 while control stays at 0.9', () => {
    const oneSidedReal: MirroredScoringParams = { ...BASE_PARAMS, percentile: 0.5 }
    const unloosenedControl: MirroredScoringParams = { ...BASE_PARAMS, percentile: 0.9 }
    expect(() =>
      runComparativeHarness({
        model,
        chart,
        eventClass: 'synthetic_event_class',
        events,
        boundsStart: BOUNDS_START,
        boundsEnd: BOUNDS_END,
        realParams: oneSidedReal,
        controlParams: unloosenedControl,
      })
    ).toThrow(ControlMirroringViolationError)
  })

  it('REJECTS a one-sided config: control given more shuffle shifts than the real run was configured with (asymmetric rigor, still a violation)', () => {
    expect(() =>
      runComparativeHarness({
        model,
        chart,
        eventClass: 'synthetic_event_class',
        events,
        boundsStart: BOUNDS_START,
        boundsEnd: BOUNDS_END,
        realParams: BASE_PARAMS,
        controlParams: { ...BASE_PARAMS, shuffleCount: 20 },
      })
    ).toThrow(/Control-mirroring violation/)
  })

  it('PROCEEDS and returns a full result when real and control params are identical', () => {
    const result = runComparativeHarness({
      model,
      chart,
      eventClass: 'synthetic_event_class',
      events,
      boundsStart: BOUNDS_START,
      boundsEnd: BOUNDS_END,
      realParams: BASE_PARAMS,
      controlParams: { ...BASE_PARAMS },
    })
    expect(result.modelId).toBe('pratyantar_lord')
    expect(result.primary.metric).toBe('CRPS/log-score')
    expect(result.secondary.metric).toContain('hit-rate')
  })
})

describe('runMirroredScoringHarness — single-params entry point, mirroring by construction', () => {
  it('produces primary CRPS/log-score results and secondary hit-rate results for both control types', () => {
    const model = pratyantarLordModel({ synthetic_event_class: { Venus: 1.0 } })
    const result = runMirroredScoringHarness({
      model,
      chart: syntheticChart(),
      eventClass: 'synthetic_event_class',
      events: syntheticEvents(),
      boundsStart: BOUNDS_START,
      boundsEnd: BOUNDS_END,
      params: BASE_PARAMS,
    })
    expect(result.primary.perEventReal).toHaveLength(2)
    expect(result.primary.perEventControlShuffled).toHaveLength(BASE_PARAMS.shuffleCount)
    expect(result.primary.perEventControlAntiphase).toHaveLength(2)
    expect(Number.isFinite(result.primary.meanCrpsReal)).toBe(true)
    expect(result.secondary.real.scoredCount).toBe(2)
    // skill is either a finite number or null (never NaN/undefined) — never a fabricated value.
    expect(result.primary.skillVsShuffled === null || Number.isFinite(result.primary.skillVsShuffled)).toBe(true)
    expect(result.primary.skillVsAntiphase === null || Number.isFinite(result.primary.skillVsAntiphase)).toBe(true)
  })

  it('the real curve genuinely differs from its own shuffled control (the model does not trivially "beat" a copy of itself)', () => {
    const model = pratyantarLordModel({ synthetic_event_class: { Venus: 1.0 } })
    const result = runMirroredScoringHarness({
      model,
      chart: syntheticChart(),
      eventClass: 'synthetic_event_class',
      events: syntheticEvents(),
      boundsStart: BOUNDS_START,
      boundsEnd: BOUNDS_END,
      params: BASE_PARAMS,
    })
    expect(result.primary.meanCrpsControlShuffled).not.toBeCloseTo(result.primary.meanCrpsReal, 9)
  })
})
