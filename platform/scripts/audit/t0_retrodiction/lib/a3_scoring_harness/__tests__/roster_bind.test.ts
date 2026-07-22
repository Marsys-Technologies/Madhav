/**
 * roster_bind.test.ts — D-4b permission-bridge lane. The bind-time
 * assertion is the deliverable this file exists to prove, both directions:
 * (a) a genuinely working roster passes and reports every contender; (b) a
 * roster containing a stub/broken contender fails LOUDLY, naming exactly
 * which one, before any scoring call. SYNTHETIC fixtures only — this file
 * proves the mechanism, not a live sidecar round-trip (see
 * permission_model.test.ts's header for why the live proof lives in the
 * PR description instead of CI).
 */
import { describe, it, expect } from 'vitest'
import { assertRosterBindable, RosterBindFailureError } from '../roster_bind'
import { midpointTriangleModel, transitKernelModel, pratyantarLordModel } from '../model_interface'
import type { ChartContext, TemporalCurveModel } from '../model_interface'

const RANGE: [Date, Date] = [new Date('2000-01-01T00:00:00Z'), new Date('2000-01-06T00:00:00Z')]
const CHART: ChartContext = {
  chartId: 'synthetic-chart-roster-bind',
  substrate: { periods: [{ level: 1, lord: 'Venus', start: new Date('1999-01-01'), end: new Date('2001-01-01') }] },
}

function workingModel(modelId: string): TemporalCurveModel {
  return { modelId, curve: () => [{ date: new Date('2000-01-01'), intensity: 1 }] }
}

function asyncWorkingModel(modelId: string): TemporalCurveModel {
  let ready = false
  return {
    modelId,
    bind: async () => {
      ready = true
    },
    curve: () => {
      if (!ready) throw new Error(`${modelId}: not bound`)
      return [{ date: new Date('2000-01-01'), intensity: 1 }]
    },
  }
}

describe('assertRosterBindable — positive case', () => {
  it('passes for a roster of genuinely working models (sync + async bind) and reports each point count', async () => {
    const roster = [pratyantarLordModel({ marriage: { Venus: 1.0 } }), workingModel('m2'), asyncWorkingModel('m3')]
    const report = await assertRosterBindable(roster, CHART, 'marriage', RANGE)
    expect(report).toHaveLength(3)
    expect(report.map((r) => r.modelId).sort()).toEqual(['m2', 'm3', 'pratyantar_lord'])
    for (const r of report) expect(r.pointCount).toBeGreaterThan(0)
  })
})

describe('assertRosterBindable — negative case (the exact blocker class this module exists to catch)', () => {
  it('fails loudly with RosterBindFailureError naming a NotImplementedModelError stub in the roster', async () => {
    const roster = [pratyantarLordModel({ marriage: { Venus: 1.0 } }), midpointTriangleModel()]
    await expect(assertRosterBindable(roster, CHART, 'marriage', RANGE)).rejects.toThrow(RosterBindFailureError)
    try {
      await assertRosterBindable(roster, CHART, 'marriage', RANGE)
      expect.unreachable()
    } catch (err) {
      expect(err).toBeInstanceOf(RosterBindFailureError)
      const e = err as RosterBindFailureError
      expect(e.failures).toHaveLength(1)
      expect(e.failures[0].modelId).toBe('midpoint_triangle')
      expect(e.failures[0].reason).toMatch(/NotImplementedModelError/)
      expect(e.message).toContain('midpoint_triangle')
    }
  })

  it('reports EVERY failing contender, not just the first (transit_kernel AND midpoint_triangle together)', async () => {
    const roster = [pratyantarLordModel({ marriage: { Venus: 1.0 } }), midpointTriangleModel(), transitKernelModel()]
    try {
      await assertRosterBindable(roster, CHART, 'marriage', RANGE)
      expect.unreachable()
    } catch (err) {
      const e = err as RosterBindFailureError
      expect(e.failures.map((f) => f.modelId).sort()).toEqual(['midpoint_triangle', 'transit_kernel'])
    }
  })

  it('fails loudly when an async bind() rejects (e.g. a network/sidecar failure)', async () => {
    const broken: TemporalCurveModel = {
      modelId: 'broken_network_model',
      bind: async () => {
        throw new Error('ECONNREFUSED: sidecar unreachable')
      },
      curve: () => [{ date: new Date('2000-01-01'), intensity: 1 }],
    }
    const roster = [pratyantarLordModel({ marriage: { Venus: 1.0 } }), broken]
    try {
      await assertRosterBindable(roster, CHART, 'marriage', RANGE)
      expect.unreachable()
    } catch (err) {
      const e = err as RosterBindFailureError
      expect(e.failures).toHaveLength(1)
      expect(e.failures[0].modelId).toBe('broken_network_model')
      expect(e.failures[0].reason).toContain('ECONNREFUSED')
    }
  })

  it('treats an empty curve() result as a bind-time failure, not an honest pass-through', async () => {
    const emptyModel: TemporalCurveModel = { modelId: 'empty_model', curve: () => [] }
    const roster = [pratyantarLordModel({ marriage: { Venus: 1.0 } }), emptyModel]
    try {
      await assertRosterBindable(roster, CHART, 'marriage', RANGE)
      expect.unreachable()
    } catch (err) {
      const e = err as RosterBindFailureError
      expect(e.failures[0].modelId).toBe('empty_model')
    }
  })
})
