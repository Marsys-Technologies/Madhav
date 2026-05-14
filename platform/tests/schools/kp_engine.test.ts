import { describe, it, expect } from 'vitest'
import { KPEngine } from '@/lib/schools/kp_engine'
import { ABHISEK_CHART } from '@/lib/schools/types'
import type { Domain } from '@/lib/schools/types'

const engine = new KPEngine()

describe('KPEngine', () => {
  it('school is kp and chartType is natal', () => {
    expect(engine.school).toBe('kp')
    expect(engine.chartType).toBe('natal')
  })

  it('CAREER analysis shows positive direction for Abhisek (Saturn 10H exalted)', async () => {
    const result = await engine.analyze(ABHISEK_CHART, 'CAREER')
    expect(result.direction).toBe('positive')
    expect(result.domainScore).toBeGreaterThan(3.0)
  })

  it('verdict mentions sub-lord activation percentage', async () => {
    const result = await engine.analyze(ABHISEK_CHART, 'CAREER')
    expect(result.schoolVerdict).toMatch(/\d+%/)
  })

  it('signalCoverage is primary', async () => {
    const result = await engine.analyze(ABHISEK_CHART, 'CAREER')
    expect(result.signalCoverage).toBe('primary')
  })

  it('domainScore is in [0, 5] for all domains', async () => {
    const domains: Domain[] = ['CAREER', 'HEALTH', 'RELATIONSHIP', 'SPIRITUAL', 'PSYCHOLOGICAL']
    for (const domain of domains) {
      const result = await engine.analyze(ABHISEK_CHART, domain)
      expect(result.domainScore).toBeGreaterThanOrEqual(0)
      expect(result.domainScore).toBeLessThanOrEqual(5)
    }
  })

  it('topSignals are sorted by score×weight descending', async () => {
    const result = await engine.analyze(ABHISEK_CHART, 'CAREER')
    const sigs = result.topSignals
    for (let i = 0; i < sigs.length - 1; i++) {
      const current = sigs[i].score * sigs[i].weight
      const next = sigs[i + 1].score * sigs[i + 1].weight
      expect(current).toBeGreaterThanOrEqual(next)
    }
  })

  it('no pendingFlags on KP engine result', async () => {
    const result = await engine.analyze(ABHISEK_CHART, 'CAREER')
    expect(result.pendingFlags?.length ?? 0).toBe(0)
  })
})
