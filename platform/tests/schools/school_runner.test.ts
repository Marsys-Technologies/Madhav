import { describe, it, expect } from 'vitest'
import { runSchoolsForDomain, runFullTriangulation, summarizeConvergence } from '@/lib/schools/school_runner'
import { ABHISEK_CHART } from '@/lib/schools/types'

describe('school_runner', () => {
  it('runSchoolsForDomain returns 7 school results for CAREER', async () => {
    const result = await runSchoolsForDomain(ABHISEK_CHART, 'CAREER')
    expect(result.schoolResults.length).toBe(7)
    expect(result.domain).toBe('CAREER')
    expect(result.chartId).toBe('abhisek_primary')
  })

  it('convergence object has required fields', async () => {
    const result = await runSchoolsForDomain(ABHISEK_CHART, 'CAREER')
    expect(result.convergence).toHaveProperty('convergenceLevel')
    expect(result.convergence).toHaveProperty('schoolsAgreeing')
    expect(result.convergence).toHaveProperty('meanDomainScore')
    expect(['HIGH', 'MEDIUM', 'LOW']).toContain(result.convergence.convergenceLevel)
  })

  it('narrative is set when includeNarratives=true', async () => {
    const result = await runSchoolsForDomain(ABHISEK_CHART, 'CAREER', { includeNarratives: true })
    expect(result.convergence.convergenceNarrative).toBeTruthy()
    expect(result.convergence.convergenceNarrative!.length).toBeGreaterThan(10)
  })

  it('runDate is in ISO format YYYY-MM-DD', async () => {
    const result = await runSchoolsForDomain(ABHISEK_CHART, 'CAREER')
    expect(result.runDate).toMatch(/^\d{4}-\d{2}-\d{2}$/)
  })

  it('runFullTriangulation returns 5 domain results', async () => {
    const results = await runFullTriangulation(ABHISEK_CHART)
    expect(results.length).toBe(5)
    const domains = results.map(r => r.domain)
    expect(domains).toContain('CAREER')
    expect(domains).toContain('HEALTH')
    expect(domains).toContain('SPIRITUAL')
  })

  it('summarizeConvergence categorizes domains correctly', async () => {
    const results = await runFullTriangulation(ABHISEK_CHART)
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
