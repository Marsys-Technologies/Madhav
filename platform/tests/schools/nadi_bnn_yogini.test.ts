import { describe, it, expect } from 'vitest'
import { NadiEngine } from '@/lib/schools/nadi_engine'
import { BNNEngine } from '@/lib/schools/bnn_engine'
import { YoginiEngine } from '@/lib/schools/yogini_engine'
import { ABHISEK_CHART } from '@/lib/schools/types'
import type { Domain } from '@/lib/schools/types'

const nadiEngine = new NadiEngine()
const bnnEngine = new BNNEngine()
const yoginiEngine = new YoginiEngine()

describe('NadiEngine', () => {
  it('school is nadi', () => { expect(nadiEngine.school).toBe('nadi') })

  it('analyze CAREER returns valid result', async () => {
    const result = await nadiEngine.analyze(ABHISEK_CHART, 'CAREER')
    expect(result.domainScore).toBeGreaterThanOrEqual(0)
    expect(result.domainScore).toBeLessThanOrEqual(5)
    expect(result.schoolVerdict).toContain('Nadi')
  })

  it('SPIRITUAL is Nadi strongest domain for Abhisek', async () => {
    const spiritual = await nadiEngine.analyze(ABHISEK_CHART, 'SPIRITUAL')
    const career = await nadiEngine.analyze(ABHISEK_CHART, 'CAREER')
    expect(spiritual.domainScore).toBeGreaterThanOrEqual(career.domainScore)
  })

  it('all domains produce valid directions', async () => {
    const domains: Domain[] = ['CAREER', 'HEALTH', 'RELATIONSHIP', 'SPIRITUAL', 'PSYCHOLOGICAL']
    for (const d of domains) {
      const r = await nadiEngine.analyze(ABHISEK_CHART, d)
      expect(['positive', 'negative', 'neutral']).toContain(r.direction)
    }
  })

  it('topSignals are non-empty', async () => {
    const result = await nadiEngine.analyze(ABHISEK_CHART, 'CAREER')
    expect(result.topSignals.length).toBeGreaterThan(0)
  })

  it('signalCoverage is primary', async () => {
    const result = await nadiEngine.analyze(ABHISEK_CHART, 'CAREER')
    expect(result.signalCoverage).toBe('primary')
  })
})

describe('BNNEngine', () => {
  it('school is bnn', () => { expect(bnnEngine.school).toBe('bnn') })

  it('analyze returns TRANSIT_DATA_PENDING flag', async () => {
    const result = await bnnEngine.analyze(ABHISEK_CHART, 'CAREER')
    expect(result.pendingFlags).toContain('[TRANSIT_DATA_PENDING]')
  })

  it('verdict mentions transit when pending', async () => {
    const result = await bnnEngine.analyze(ABHISEK_CHART, 'CAREER')
    expect(result.schoolVerdict).toContain('[TRANSIT_DATA_PENDING]')
  })

  it('domainScore is in [0, 5]', async () => {
    const result = await bnnEngine.analyze(ABHISEK_CHART, 'SPIRITUAL')
    expect(result.domainScore).toBeGreaterThanOrEqual(0)
    expect(result.domainScore).toBeLessThanOrEqual(5)
  })

  it('SPIRITUAL is BNN strongest domain (Ketu contact)', async () => {
    const spiritual = await bnnEngine.analyze(ABHISEK_CHART, 'SPIRITUAL')
    const health = await bnnEngine.analyze(ABHISEK_CHART, 'HEALTH')
    expect(spiritual.domainScore).toBeGreaterThan(health.domainScore)
  })

  it('without pending flag, no pendingFlags in result', async () => {
    const chartNoPending = { ...ABHISEK_CHART, pendingFlags: [] }
    const result = await bnnEngine.analyze(chartNoPending, 'CAREER')
    expect(result.pendingFlags?.length ?? 0).toBe(0)
  })

  it('all domains return valid shapes', async () => {
    const domains: Domain[] = ['CAREER', 'HEALTH', 'RELATIONSHIP', 'SPIRITUAL', 'PSYCHOLOGICAL']
    for (const d of domains) {
      const r = await bnnEngine.analyze(ABHISEK_CHART, d)
      expect(r.school).toBe('bnn')
      expect(r.domain).toBe(d)
    }
  })
})

describe('YoginiEngine', () => {
  it('school is yogini', () => { expect(yoginiEngine.school).toBe('yogini') })

  it('analyze reads Bhramari/Mars for Abhisek at 2026-05-14', async () => {
    const result = await yoginiEngine.analyze(ABHISEK_CHART, 'CAREER')
    expect(result.schoolVerdict).toContain('Bhramari')
  })

  it('CAREER direction is positive for Bhramari period (modifier 1.1)', async () => {
    const result = await yoginiEngine.analyze(ABHISEK_CHART, 'CAREER')
    // Bhramari CAREER modifier = 1.1 × base 3.5 → should be positive
    expect(result.domainScore).toBeGreaterThan(3.0)
    expect(result.direction).toBe('positive')
  })

  it('no pending flags on yogini engine', async () => {
    const result = await yoginiEngine.analyze(ABHISEK_CHART, 'CAREER')
    expect(result.pendingFlags?.length ?? 0).toBe(0)
  })

  it('domainScore bounded by [0, 5] even with modifier > 1.0', async () => {
    const domains: Domain[] = ['CAREER', 'HEALTH', 'RELATIONSHIP', 'SPIRITUAL', 'PSYCHOLOGICAL']
    for (const d of domains) {
      const r = await yoginiEngine.analyze(ABHISEK_CHART, d)
      expect(r.domainScore).toBeGreaterThanOrEqual(0)
      expect(r.domainScore).toBeLessThanOrEqual(5)
    }
  })

  it('all domains produce non-empty verdicts', async () => {
    const domains: Domain[] = ['CAREER', 'HEALTH', 'RELATIONSHIP', 'SPIRITUAL', 'PSYCHOLOGICAL']
    for (const d of domains) {
      const r = await yoginiEngine.analyze(ABHISEK_CHART, d)
      expect(r.schoolVerdict.length).toBeGreaterThan(20)
    }
  })
})
