/**
 * model_interface.test.ts — SYNTHETIC fixtures only. No LEL data is read
 * anywhere in this file; all dates below are hand-authored, pre-2020, and
 * do not correspond to any real chart-482012f1 LEL event. See the module
 * header for why: BRIEF_D4A.md Lane A-3 forbids sealed-test-split
 * (LEL events >= 2020-01-01) contact while building/testing this harness.
 */
import { describe, it, expect } from 'vitest'
import { pratyantarLordModel, midpointTriangleModel, transitKernelModel, NotImplementedModelError, type ChartContext } from '../model_interface'
import type { DashaPeriod } from '../../curve'

const BOUNDS_START = new Date(Date.UTC(1990, 0, 1))
const BOUNDS_END = new Date(Date.UTC(2015, 0, 1))

function syntheticPeriods(): DashaPeriod[] {
  return [
    { level: 1, lord: 'Jupiter', start: new Date(Date.UTC(1990, 0, 1)), end: new Date(Date.UTC(2000, 0, 1)) },
    { level: 2, lord: 'Venus', start: new Date(Date.UTC(1995, 0, 1)), end: new Date(Date.UTC(1996, 0, 1)) },
  ]
}

describe('pratyantarLordModel — the one real, servable model', () => {
  it('implements TemporalCurveModel and produces a non-empty curve for a known event class', () => {
    const model = pratyantarLordModel({ synthetic_wealth: { Venus: 1.0 } })
    const chart: ChartContext = { chartId: 'synthetic-chart-1', substrate: { periods: syntheticPeriods() } }
    const curve = model.curve(chart, 'synthetic_wealth', [BOUNDS_START, BOUNDS_END])
    expect(model.modelId).toBe('pratyantar_lord')
    expect(curve.length).toBeGreaterThan(0)
    expect(curve.some((c) => c.intensity > 0)).toBe(true)
  })

  it('returns an honest zero curve (not an error) for an event class with no significator entry', () => {
    const model = pratyantarLordModel({ synthetic_wealth: { Venus: 1.0 } })
    const chart: ChartContext = { chartId: 'synthetic-chart-1', substrate: { periods: syntheticPeriods() } }
    const curve = model.curve(chart, 'unmapped_class', [BOUNDS_START, BOUNDS_END])
    expect(curve.length).toBeGreaterThan(0)
    expect(curve.every((c) => c.intensity === 0)).toBe(true)
  })

  it('throws a clear error (not a silent empty curve) when substrate.periods is missing', () => {
    const model = pratyantarLordModel({ synthetic_wealth: { Venus: 1.0 } })
    const chart: ChartContext = { chartId: 'synthetic-chart-2', substrate: {} }
    expect(() => model.curve(chart, 'synthetic_wealth', [BOUNDS_START, BOUNDS_END])).toThrow(/substrate\.periods missing/)
  })
})

describe('stub models — never fabricate a curve', () => {
  it('midpoint_triangle throws NotImplementedModelError', () => {
    const model = midpointTriangleModel()
    const chart: ChartContext = { chartId: 'synthetic-chart-1', substrate: {} }
    expect(() => model.curve(chart, 'synthetic_wealth', [BOUNDS_START, BOUNDS_END])).toThrow(NotImplementedModelError)
  })

  it('transit_kernel throws NotImplementedModelError', () => {
    const model = transitKernelModel()
    const chart: ChartContext = { chartId: 'synthetic-chart-1', substrate: {} }
    expect(() => model.curve(chart, 'synthetic_wealth', [BOUNDS_START, BOUNDS_END])).toThrow(NotImplementedModelError)
  })

  it('all three models share the identical TemporalCurveModel shape (genuinely swappable)', () => {
    const models = [pratyantarLordModel({}), midpointTriangleModel(), transitKernelModel()]
    for (const m of models) {
      expect(typeof m.modelId).toBe('string')
      expect(typeof m.curve).toBe('function')
    }
  })
})
