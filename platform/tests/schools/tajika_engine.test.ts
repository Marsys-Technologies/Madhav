import { describe, it, expect } from 'vitest'
import { TajikaEngine } from '@/lib/schools/tajika_engine'
import { SYNTHETIC_CHART } from '@/lib/schools/__fixtures__/synthetic_chart'
import { ALL_DOMAINS, liveSignals } from './_support'

const engine = new TajikaEngine()
const pendingChart = { ...SYNTHETIC_CHART, pendingFlags: ['VARSHA_KUNDALI_PENDING'] }

describe('TajikaEngine', () => {
  it('school is tajika and chartType is varsha_kundali', () => {
    expect(engine.school).toBe('tajika')
    expect(engine.chartType).toBe('varsha_kundali')
  })

  it('no live signals => not available, pending flag still reported', async () => {
    const result = await engine.analyze(pendingChart, 'CAREER')
    expect(result.available).toBe(false)
    expect(result.unavailableReason).toBe('no_live_signals')
    expect(result.domainScore).toBeNull()
    expect(result.pendingFlags).toContain('[VARSHA_KUNDALI_PENDING]')
  })

  it('analyze returns VARSHA_KUNDALI_PENDING flag when chart has pending flag', async () => {
    const result = await engine.analyze(pendingChart, 'CAREER', liveSignals(3))
    expect(result.pendingFlags).toContain('[VARSHA_KUNDALI_PENDING]')
  })

  it('verdict mentions VARSHA_KUNDALI_PENDING when pending', async () => {
    const result = await engine.analyze(pendingChart, 'CAREER', liveSignals(3))
    expect(result.schoolVerdict).toContain('[VARSHA_KUNDALI_PENDING]')
  })

  it('analyze without pending flag clears pendingFlags array', async () => {
    const chartNoPending = { ...SYNTHETIC_CHART, pendingFlags: [] }
    const result = await engine.analyze(chartNoPending, 'CAREER', liveSignals(3))
    expect(result.pendingFlags?.length ?? 0).toBe(0)
    expect(result.schoolVerdict).not.toContain('[VARSHA_KUNDALI_PENDING]')
  })

  it('domainScore is in valid range 0–5', async () => {
    const result = await engine.analyze(SYNTHETIC_CHART, 'HEALTH', liveSignals(3.3))
    expect(result.domainScore as number).toBeGreaterThanOrEqual(0)
    expect(result.domainScore as number).toBeLessThanOrEqual(5)
  })

  for (const domain of ALL_DOMAINS) {
    it(`${domain}: returns valid SchoolResult shape from live signals`, async () => {
      const result = await engine.analyze(SYNTHETIC_CHART, domain, liveSignals(3))
      expect(result.school).toBe('tajika')
      expect(result.domain).toBe(domain)
      expect(result.topSignals.length).toBeGreaterThan(0)
    })
  }
})
