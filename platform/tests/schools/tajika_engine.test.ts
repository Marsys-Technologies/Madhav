import { describe, it, expect } from 'vitest'
import { TajikaEngine } from '@/lib/schools/tajika_engine'
import { ABHISEK_CHART } from '@/lib/schools/types'
import type { Domain } from '@/lib/schools/types'

const engine = new TajikaEngine()

describe('TajikaEngine', () => {
  it('school is tajika and chartType is varsha_kundali', () => {
    expect(engine.school).toBe('tajika')
    expect(engine.chartType).toBe('varsha_kundali')
  })

  it('analyze returns VARSHA_KUNDALI_PENDING flag when chart has pending flag', async () => {
    const result = await engine.analyze(ABHISEK_CHART, 'CAREER')
    expect(result.pendingFlags).toContain('[VARSHA_KUNDALI_PENDING]')
  })

  it('verdict mentions VARSHA_KUNDALI_PENDING when pending', async () => {
    const result = await engine.analyze(ABHISEK_CHART, 'CAREER')
    expect(result.schoolVerdict).toContain('[VARSHA_KUNDALI_PENDING]')
  })

  it('analyze without pending flag clears pendingFlags array', async () => {
    const chartNoPending = { ...ABHISEK_CHART, pendingFlags: [] }
    const result = await engine.analyze(chartNoPending, 'CAREER')
    expect(result.pendingFlags?.length ?? 0).toBe(0)
    expect(result.schoolVerdict).not.toContain('[VARSHA_KUNDALI_PENDING]')
  })

  it('domainScore is in valid range 0–5', async () => {
    const result = await engine.analyze(ABHISEK_CHART, 'HEALTH')
    expect(result.domainScore).toBeGreaterThanOrEqual(0)
    expect(result.domainScore).toBeLessThanOrEqual(5)
  })

  const domains: Domain[] = ['CAREER', 'HEALTH', 'RELATIONSHIP', 'SPIRITUAL', 'PSYCHOLOGICAL']
  for (const domain of domains) {
    it(`${domain}: returns valid SchoolResult shape`, async () => {
      const result = await engine.analyze(ABHISEK_CHART, domain)
      expect(result.school).toBe('tajika')
      expect(result.domain).toBe(domain)
      expect(result.topSignals.length).toBeGreaterThan(0)
    })
  }
})
