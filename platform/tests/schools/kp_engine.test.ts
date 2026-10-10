import { describe, it, expect } from 'vitest'
import { KPEngine } from '@/lib/schools/kp_engine'
import { SYNTHETIC_CHART } from '@/lib/schools/__fixtures__/synthetic_chart'
import { ALL_DOMAINS, liveSignals } from './_support'

const engine = new KPEngine()

describe('KPEngine', () => {
  it('school is kp and chartType is natal', () => {
    expect(engine.school).toBe('kp')
    expect(engine.chartType).toBe('natal')
  })

  it('no live signals (undefined) => honest not-available, no invented score', async () => {
    const result = await engine.analyze(SYNTHETIC_CHART, 'CAREER')
    expect(result.available).toBe(false)
    expect(result.unavailableReason).toBe('no_live_signals')
    expect(result.signalSupply).toBe('not_supplied')
    expect(result.domainScore).toBeNull()
    expect(result.direction).toBeNull()
    expect(result.topSignals).toEqual([])
    expect(result.signalCoverage).toBe('silent')
  })

  it('empty live signals ([]) => the same honest not-available (never a computed zero)', async () => {
    const result = await engine.analyze(SYNTHETIC_CHART, 'CAREER', [])
    expect(result.available).toBe(false)
    expect(result.unavailableReason).toBe('no_live_signals')
    expect(result.signalSupply).toBe('supplied_empty')
    expect(result.domainScore).toBeNull()
  })

  it('analyses only the signals passed in (high score => positive)', async () => {
    const result = await engine.analyze(SYNTHETIC_CHART, 'CAREER', liveSignals(4.5))
    expect(result.available).toBe(true)
    expect(result.direction).toBe('positive')
    expect(result.domainScore).toBeCloseTo(4.5, 3)
    expect(result.topSignals.every(s => s.signalId.startsWith('SIG.TEST.'))).toBe(true)
  })

  it('verdict is derived from the live signals and the domain cusps, not a stored chart', async () => {
    const result = await engine.analyze(SYNTHETIC_CHART, 'CAREER', liveSignals(2.5))
    expect(result.schoolVerdict).toContain('3 live signal(s)')
    expect(result.schoolVerdict).toContain('10H, 6H, 2H')
    expect(result.schoolVerdict).toContain('Test live signal')
  })

  it('signalCoverage is primary when analysed', async () => {
    const result = await engine.analyze(SYNTHETIC_CHART, 'CAREER', liveSignals(3))
    expect(result.signalCoverage).toBe('primary')
  })

  it('domainScore is in [0, 5] for all domains', async () => {
    for (const domain of ALL_DOMAINS) {
      const result = await engine.analyze(SYNTHETIC_CHART, domain, liveSignals(9))
      expect(result.domainScore).toBeGreaterThanOrEqual(0)
      expect(result.domainScore).toBeLessThanOrEqual(5)
    }
  })

  it('topSignals are sorted by score×weight descending', async () => {
    const sigs = [
      { signalId: 'SIG.TEST.A', signalName: 'a', score: 2, weight: 0.5 },
      { signalId: 'SIG.TEST.B', signalName: 'b', score: 4, weight: 0.9 },
      { signalId: 'SIG.TEST.C', signalName: 'c', score: 3, weight: 0.7 },
    ]
    const result = await engine.analyze(SYNTHETIC_CHART, 'CAREER', sigs)
    const top = result.topSignals
    for (let i = 0; i < top.length - 1; i++) {
      expect(top[i].score * top[i].weight).toBeGreaterThanOrEqual(top[i + 1].score * top[i + 1].weight)
    }
  })

  it('no pendingFlags on KP engine result', async () => {
    const result = await engine.analyze(SYNTHETIC_CHART, 'CAREER', liveSignals(3))
    expect(result.pendingFlags?.length ?? 0).toBe(0)
  })
})
