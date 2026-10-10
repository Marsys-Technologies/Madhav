import { describe, it, expect } from 'vitest'
import { ParashariEngine } from '@/lib/schools/parashari_engine'
import { SYNTHETIC_CHART } from '@/lib/schools/__fixtures__/synthetic_chart'
import type { SignalScore } from '@/lib/schools/types'
import { ALL_DOMAINS } from './_support'

const engine = new ParashariEngine()

const mockSignals = (score: number): SignalScore[] => [
  { signalId: 'SIG.TEST.001', signalName: 'Test signal A', score, weight: 0.9 },
  { signalId: 'SIG.TEST.002', signalName: 'Test signal B', score: score - 0.5, weight: 0.7 },
  { signalId: 'SIG.TEST.003', signalName: 'Test signal C', score: score + 0.3, weight: 0.6 },
]

describe('ParashariEngine', () => {
  it('school and chartType are set correctly', () => {
    expect(engine.school).toBe('parashari')
    expect(engine.chartType).toBe('natal')
  })

  it('no live signals => not available (no default signal set)', async () => {
    const result = await engine.analyze(SYNTHETIC_CHART, 'CAREER')
    expect(result.school).toBe('parashari')
    expect(result.domain).toBe('CAREER')
    expect(result.available).toBe(false)
    expect(result.unavailableReason).toBe('no_live_signals')
    expect(result.domainScore).toBeNull()
    expect(result.direction).toBeNull()
    expect(result.schoolVerdict).toContain('not available')
  })

  it('analyze with injected high-score signals returns positive direction', async () => {
    const result = await engine.analyze(SYNTHETIC_CHART, 'CAREER', mockSignals(4.5))
    expect(result.available).toBe(true)
    expect(result.direction).toBe('positive')
    expect(result.domainScore as number).toBeGreaterThan(3.2)
    expect(result.schoolVerdict.length).toBeGreaterThan(20)
    expect(result.topSignals.length).toBeGreaterThan(0)
  })

  it('analyze with injected low-score signals returns negative direction', async () => {
    const lowSignals: SignalScore[] = [
      { signalId: 'SIG.TEST.001', signalName: 'Weak signal', score: 1.0, weight: 0.9 },
      { signalId: 'SIG.TEST.002', signalName: 'Weak signal 2', score: 1.2, weight: 0.8 },
    ]
    const result = await engine.analyze(SYNTHETIC_CHART, 'CAREER', lowSignals)
    expect(result.direction).toBe('negative')
    expect(result.domainScore as number).toBeLessThan(1.8)
  })

  it('domainScore is rounded to 3 decimal places', async () => {
    const result = await engine.analyze(SYNTHETIC_CHART, 'HEALTH', [
      { signalId: 'SIG.TEST.001', signalName: 'x', score: 3.14159, weight: 0.3 },
      { signalId: 'SIG.TEST.002', signalName: 'y', score: 2.71828, weight: 0.7 },
    ])
    const decimals = (result.domainScore as number).toString().split('.')[1]?.length ?? 0
    expect(decimals).toBeLessThanOrEqual(3)
  })

  for (const domain of ALL_DOMAINS) {
    it(`analyze ${domain} produces a non-empty verdict from live signals`, async () => {
      const result = await engine.analyze(SYNTHETIC_CHART, domain, mockSignals(3.5))
      expect(result.schoolVerdict.length).toBeGreaterThan(0)
      expect(result.domain).toBe(domain)
    })
  }
})
