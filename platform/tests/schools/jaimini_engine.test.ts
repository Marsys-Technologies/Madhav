import { describe, it, expect } from 'vitest'
import { JaiminiEngine } from '@/lib/schools/jaimini_engine'
import { ABHISEK_CHART } from '@/lib/schools/types'
import type { SignalScore, Domain } from '@/lib/schools/types'

const engine = new JaiminiEngine()

describe('JaiminiEngine', () => {
  it('school and chartType are set correctly', () => {
    expect(engine.school).toBe('jaimini')
    expect(engine.chartType).toBe('natal')
  })

  it('analyze CAREER returns valid result shape', async () => {
    const result = await engine.analyze(ABHISEK_CHART, 'CAREER')
    expect(result.school).toBe('jaimini')
    expect(result.domainScore).toBeGreaterThanOrEqual(0)
    expect(result.domainScore).toBeLessThanOrEqual(5)
    expect(['positive', 'negative', 'neutral']).toContain(result.direction)
    expect(result.schoolVerdict).toContain('Jaimini')
  })

  it('Chara Karaka hierarchy modulates CAREER positively for Abhisek', async () => {
    const result = await engine.analyze(ABHISEK_CHART, 'CAREER')
    // AmK Saturn exalted → career should score positive
    expect(result.direction).toBe('positive')
    expect(result.domainScore).toBeGreaterThan(3.0)
  })

  it('injected signals override defaults', async () => {
    const signals: SignalScore[] = [
      { signalId: 'SIG.MSR.055', signalName: 'Override signal', score: 1.0, weight: 0.9 },
    ]
    const result = await engine.analyze(ABHISEK_CHART, 'CAREER', signals)
    // Low score signal → should be negative or neutral, not positive
    expect(result.domainScore).toBeLessThan(3.0)
  })

  it('SPIRITUAL verdict mentions atmakaraka', async () => {
    const result = await engine.analyze(ABHISEK_CHART, 'SPIRITUAL')
    expect(result.schoolVerdict.toUpperCase()).toContain('MOON')
  })

  const domains: Domain[] = ['CAREER', 'HEALTH', 'RELATIONSHIP', 'SPIRITUAL', 'PSYCHOLOGICAL']
  for (const domain of domains) {
    it(`analyze ${domain} produces score in [0, 5]`, async () => {
      const result = await engine.analyze(ABHISEK_CHART, domain)
      expect(result.domainScore).toBeGreaterThanOrEqual(0)
      expect(result.domainScore).toBeLessThanOrEqual(5)
    })
  }
})
