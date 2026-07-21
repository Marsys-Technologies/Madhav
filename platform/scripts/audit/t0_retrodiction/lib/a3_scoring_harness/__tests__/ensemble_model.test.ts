/**
 * ensemble_model.test.ts — D-4b permission-bridge lane. SYNTHETIC fixtures
 * only, no network, no LEL data — same discipline as model_interface.test.ts.
 */
import { describe, it, expect } from 'vitest'
import { hierarchicalEnsembleModel, EnsembleGridMismatchError } from '../ensemble_model'
import { pratyantarLordModel } from '../model_interface'
import type { ChartContext, TemporalCurveModel } from '../model_interface'
import type { CurvePoint } from '../../curve'

const RANGE: [Date, Date] = [new Date('2000-01-01T00:00:00Z'), new Date('2000-01-11T00:00:00Z')]
const CHART: ChartContext = { chartId: 'synthetic-chart-ensemble', substrate: {} }

function fixedCurveModel(modelId: string, points: CurvePoint[]): TemporalCurveModel {
  return { modelId, curve: () => points }
}

describe('hierarchicalEnsembleModel', () => {
  it('rejects an empty contender list rather than producing a silent zero-curve', () => {
    expect(() => hierarchicalEnsembleModel([])).toThrow(/non-empty/)
  })

  it('sums point-wise across contenders on an identical grid', () => {
    const a = fixedCurveModel('a', [
      { date: new Date('2000-01-01'), intensity: 1 },
      { date: new Date('2000-01-02'), intensity: 0 },
    ])
    const b = fixedCurveModel('b', [
      { date: new Date('2000-01-01'), intensity: 0.5 },
      { date: new Date('2000-01-02'), intensity: 2 },
    ])
    const ensemble = hierarchicalEnsembleModel([a, b])
    expect(ensemble.modelId).toBe('hierarchical_ensemble')
    const curve = ensemble.curve(CHART, 'marriage', RANGE)
    expect(curve).toEqual([
      { date: new Date('2000-01-01'), intensity: 1.5 },
      { date: new Date('2000-01-02'), intensity: 2 },
    ])
  })

  it('throws EnsembleGridMismatchError (never silently truncates/pads) when constituent curves have different lengths', () => {
    const a = fixedCurveModel('a', [{ date: new Date('2000-01-01'), intensity: 1 }])
    const b = fixedCurveModel('b', [
      { date: new Date('2000-01-01'), intensity: 1 },
      { date: new Date('2000-01-02'), intensity: 1 },
    ])
    const ensemble = hierarchicalEnsembleModel([a, b])
    expect(() => ensemble.curve(CHART, 'marriage', RANGE)).toThrow(EnsembleGridMismatchError)
  })

  it('bind() chains to every constituent that declares one, no-ops for those that do not', async () => {
    let bound = false
    const withBind: TemporalCurveModel = {
      modelId: 'has-bind',
      curve: () => [{ date: new Date('2000-01-01'), intensity: 1 }],
      bind: async () => {
        bound = true
      },
    }
    const withoutBind = fixedCurveModel('no-bind', [{ date: new Date('2000-01-01'), intensity: 1 }])
    const ensemble = hierarchicalEnsembleModel([withBind, withoutBind])
    await ensemble.bind!(CHART, 'marriage', RANGE)
    expect(bound).toBe(true)
  })

  it('composes with the real pratyantar_lord model (genuinely swappable per TemporalCurveModel)', () => {
    const pl = pratyantarLordModel({ marriage: { Venus: 1.0 } })
    const chart: ChartContext = {
      chartId: 'synthetic-chart-ensemble-2',
      substrate: { periods: [{ level: 1, lord: 'Venus', start: new Date('1999-01-01'), end: new Date('2001-01-01') }] },
    }
    const flat = fixedCurveModel('flat', pl.curve(chart, 'marriage', RANGE).map((p) => ({ date: p.date, intensity: 5 })))
    const ensemble = hierarchicalEnsembleModel([pl, flat])
    const curve = ensemble.curve(chart, 'marriage', RANGE)
    // pratyantar_lord alone would be 1 (depth-weight 1 * significator 1.0) throughout; +5 flat = 6.
    expect(curve.every((c) => c.intensity === 6)).toBe(true)
  })
})
