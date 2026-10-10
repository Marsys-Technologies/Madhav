import { describe, it, expect } from 'vitest'
import { runSchoolsForDomain, runFullTriangulation, summarizeConvergence } from '@/lib/schools/school_runner'
import { SYNTHETIC_CHART } from '@/lib/schools/__fixtures__/synthetic_chart'
import { liveSignalsForAll } from './_support'

const live = { liveSignals: liveSignalsForAll(4.0) }

describe('school_runner', () => {
  it('runSchoolsForDomain returns 7 school results for CAREER', async () => {
    const result = await runSchoolsForDomain(SYNTHETIC_CHART, 'CAREER', live)
    expect(result.schoolResults.length).toBe(7)
    expect(result.domain).toBe('CAREER')
    expect(result.chartId).toBe(SYNTHETIC_CHART.chartId)
  })

  it('convergence object has required fields', async () => {
    const result = await runSchoolsForDomain(SYNTHETIC_CHART, 'CAREER', live)
    expect(result.convergence).toHaveProperty('convergenceLevel')
    expect(result.convergence).toHaveProperty('schoolsAgreeing')
    expect(result.convergence).toHaveProperty('meanDomainScore')
    expect(['HIGH', 'MEDIUM', 'LOW']).toContain(result.convergence.convergenceLevel)
  })

  it('narrative is set when includeNarratives=true', async () => {
    const result = await runSchoolsForDomain(SYNTHETIC_CHART, 'CAREER', { ...live, includeNarratives: true })
    expect(result.convergence.convergenceNarrative).toBeTruthy()
    expect(result.convergence.convergenceNarrative!.length).toBeGreaterThan(10)
  })

  it('runDate is in ISO format YYYY-MM-DD', async () => {
    const result = await runSchoolsForDomain(SYNTHETIC_CHART, 'CAREER', live)
    expect(result.runDate).toMatch(/^\d{4}-\d{2}-\d{2}$/)
  })

  it('runFullTriangulation returns 5 domain results', async () => {
    const results = await runFullTriangulation(SYNTHETIC_CHART, live)
    expect(results.length).toBe(5)
    const domains = results.map(r => r.domain)
    expect(domains).toContain('CAREER')
    expect(domains).toContain('HEALTH')
    expect(domains).toContain('SPIRITUAL')
  })

  it('summarizeConvergence categorizes domains correctly', async () => {
    const results = await runFullTriangulation(SYNTHETIC_CHART, live)
    const summary = summarizeConvergence(results)
    const allDomains = [
      ...summary.highConvergenceDomains,
      ...summary.mediumConvergenceDomains,
      ...summary.lowConvergenceDomains,
    ]
    expect(allDomains.length).toBe(5)
    expect(summary.overallAgreementSignal.length).toBeGreaterThan(0)
  })
})
