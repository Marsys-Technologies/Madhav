import { describe, it, expect } from 'vitest'
import { ParashariEngine } from '@/lib/schools/parashari_engine'
import { ABHISEK_CHART } from '@/lib/schools/types'
import type { SignalScore, Domain } from '@/lib/schools/types'

const engine = new ParashariEngine()

const mockSignals = (score: number): SignalScore[] => [
  { signalId: 'SIG.MSR.001', signalName: 'Test signal A', score, weight: 0.9 },
  { signalId: 'SIG.MSR.002', signalName: 'Test signal B', score: score - 0.5, weight: 0.7 },
  { signalId: 'SIG.MSR.003', signalName: 'Test signal C', score: score + 0.3, weight: 0.6 },
]

describe('ParashariEngine', () => {
  it('school and chartType are set correctly', () => {
    expect(engine.school).toBe('parashari')
    expect(engine.chartType).toBe('natal')
  })

  it('analyze CAREER with default signals returns valid result', async () => {
    const result = await engine.analyze(ABHISEK_CHART, 'CAREER')
    expect(result.school).toBe('parashari')
    expect(result.domain).toBe('CAREER')
    expect(result.domainScore).toBeGreaterThanOrEqual(0)
    expect(result.domainScore).toBeLessThanOrEqual(5)
    expect(['positive', 'negative', 'neutral']).toContain(result.direction)
    expect(result.schoolVerdict.length).toBeGreaterThan(20)
    expect(result.topSignals.length).toBeGreaterThan(0)
  })

  it('analyze with injected high-score signals returns positive direction', async () => {
    const result = await engine.analyze(ABHISEK_CHART, 'CAREER', mockSignals(4.5))
    expect(result.direction).toBe('positive')
    expect(result.domainScore).toBeGreaterThan(3.2)
  })

  it('analyze with injected low-score signals returns negative direction', async () => {
    const lowSignals: SignalScore[] = [
      { signalId: 'SIG.MSR.001', signalName: 'Weak signal', score: 1.0, weight: 0.9 },
      { signalId: 'SIG.MSR.002', signalName: 'Weak signal 2', score: 1.2, weight: 0.8 },
    ]
    const result = await engine.analyze(ABHISEK_CHART, 'CAREER', lowSignals)
    expect(result.direction).toBe('negative')
    expect(result.domainScore).toBeLessThan(1.8)
  })

  it('domainScore is rounded to 3 decimal places', async () => {
    const result = await engine.analyze(ABHISEK_CHART, 'HEALTH')
    const decimals = result.domainScore.toString().split('.')[1]?.length ?? 0
    expect(decimals).toBeLessThanOrEqual(3)
  })

  const domains: Domain[] = ['CAREER', 'HEALTH', 'RELATIONSHIP', 'SPIRITUAL', 'PSYCHOLOGICAL']
  for (const domain of domains) {
    it(`analyze ${domain} produces non-empty verdict`, async () => {
      const result = await engine.analyze(ABHISEK_CHART, domain)
      expect(result.schoolVerdict.length).toBeGreaterThan(0)
      expect(result.domain).toBe(domain)
    })
  }
})
