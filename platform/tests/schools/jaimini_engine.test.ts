import { describe, it, expect } from 'vitest'
import { JaiminiEngine } from '@/lib/schools/jaimini_engine'
import { SYNTHETIC_CHART, SYNTHETIC_CHART_B } from '@/lib/schools/__fixtures__/synthetic_chart'
import type { SignalScore } from '@/lib/schools/types'
import { ALL_DOMAINS, liveSignals } from './_support'

const engine = new JaiminiEngine()

describe('JaiminiEngine', () => {
  it('school and chartType are set correctly', () => {
    expect(engine.school).toBe('jaimini')
    expect(engine.chartType).toBe('natal')
  })

  it('no live signals => not available', async () => {
    const result = await engine.analyze(SYNTHETIC_CHART, 'CAREER')
    expect(result.available).toBe(false)
    expect(result.unavailableReason).toBe('no_live_signals')
    expect(result.domainScore).toBeNull()
    expect(result.schoolVerdict).toContain('Jaimini')
  })

  it('analyze CAREER with live signals returns valid result shape', async () => {
    const result = await engine.analyze(SYNTHETIC_CHART, 'CAREER', liveSignals(4.0))
    expect(result.school).toBe('jaimini')
    expect(result.domainScore as number).toBeGreaterThanOrEqual(0)
    expect(result.domainScore as number).toBeLessThanOrEqual(5)
    expect(['positive', 'negative', 'neutral']).toContain(result.direction)
    expect(result.schoolVerdict).toContain('Jaimini')
  })

  it('injected low-score signals are not positive', async () => {
    const signals: SignalScore[] = [
      { signalId: 'SIG.TEST.001', signalName: 'Override signal', score: 1.0, weight: 0.9 },
    ]
    const result = await engine.analyze(SYNTHETIC_CHART, 'CAREER', signals)
    expect(result.domainScore as number).toBeLessThan(3.0)
  })

  it('verdict names Chara Karakas only from the ChartData passed in', async () => {
    const a = await engine.analyze(SYNTHETIC_CHART, 'SPIRITUAL', liveSignals(3.5))
    const b = await engine.analyze(SYNTHETIC_CHART_B, 'SPIRITUAL', liveSignals(3.5))
    expect(a.schoolVerdict).toContain('atmakaraka jupiter')
    expect(b.schoolVerdict).toContain('atmakaraka saturn')
    const bare = await engine.analyze({ ...SYNTHETIC_CHART, charaPadas: undefined }, 'SPIRITUAL', liveSignals(3.5))
    expect(bare.schoolVerdict).not.toContain('atmakaraka')
  })

  for (const domain of ALL_DOMAINS) {
    it(`analyze ${domain} produces score in [0, 5]`, async () => {
      const result = await engine.analyze(SYNTHETIC_CHART, domain, liveSignals(3.5))
      expect(result.domainScore as number).toBeGreaterThanOrEqual(0)
      expect(result.domainScore as number).toBeLessThanOrEqual(5)
    })
  }
})
