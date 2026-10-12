import { describe, it, expect } from 'vitest'
import { NadiEngine } from '@/lib/schools/nadi_engine'
import { BNNEngine } from '@/lib/schools/bnn_engine'
import { YoginiEngine } from '@/lib/schools/yogini_engine'
import { SYNTHETIC_CHART, SYNTHETIC_CHART_B } from '@/lib/schools/__fixtures__/synthetic_chart'
import { ALL_DOMAINS, liveSignals } from './_support'

const nadiEngine = new NadiEngine()
const bnnEngine = new BNNEngine()
const yoginiEngine = new YoginiEngine()

describe('NadiEngine', () => {
  it('school is nadi', () => { expect(nadiEngine.school).toBe('nadi') })

  it('no live signals => not available', async () => {
    const result = await nadiEngine.analyze(SYNTHETIC_CHART, 'CAREER')
    expect(result.available).toBe(false)
    expect(result.domainScore).toBeNull()
    expect(result.schoolVerdict).toContain('not available')
  })

  it('analyze CAREER returns valid result from live signals', async () => {
    const result = await nadiEngine.analyze(SYNTHETIC_CHART, 'CAREER', liveSignals(3.2))
    expect(result.domainScore as number).toBeGreaterThanOrEqual(0)
    expect(result.domainScore as number).toBeLessThanOrEqual(5)
    expect(result.schoolVerdict).toContain('Nadi')
  })

  it('all domains produce valid directions', async () => {
    for (const d of ALL_DOMAINS) {
      const r = await nadiEngine.analyze(SYNTHETIC_CHART, d, liveSignals(3.5))
      expect(['positive', 'negative', 'neutral']).toContain(r.direction)
    }
  })

  it('topSignals are the live signals; coverage is primary', async () => {
    const result = await nadiEngine.analyze(SYNTHETIC_CHART, 'CAREER', liveSignals(3))
    expect(result.topSignals.length).toBeGreaterThan(0)
    expect(result.signalCoverage).toBe('primary')
  })
})

describe('BNNEngine', () => {
  it('school is bnn', () => { expect(bnnEngine.school).toBe('bnn') })

  it('no live signals => not available, TRANSIT_DATA_PENDING still reported', async () => {
    const result = await bnnEngine.analyze(SYNTHETIC_CHART_B, 'CAREER')
    expect(result.available).toBe(false)
    expect(result.domainScore).toBeNull()
    expect(result.pendingFlags).toContain('[TRANSIT_DATA_PENDING]')
  })

  it('analyze returns TRANSIT_DATA_PENDING flag', async () => {
    const result = await bnnEngine.analyze(SYNTHETIC_CHART_B, 'CAREER', liveSignals(3))
    expect(result.pendingFlags).toContain('[TRANSIT_DATA_PENDING]')
  })

  it('verdict mentions transit when pending', async () => {
    const result = await bnnEngine.analyze(SYNTHETIC_CHART_B, 'CAREER', liveSignals(3))
    expect(result.schoolVerdict).toContain('[TRANSIT_DATA_PENDING]')
  })

  it('domainScore is in [0, 5]', async () => {
    const result = await bnnEngine.analyze(SYNTHETIC_CHART_B, 'SPIRITUAL', liveSignals(3))
    expect(result.domainScore as number).toBeGreaterThanOrEqual(0)
    expect(result.domainScore as number).toBeLessThanOrEqual(5)
  })

  it('without pending flag, no pendingFlags in result', async () => {
    const chartNoPending = { ...SYNTHETIC_CHART_B, pendingFlags: [] }
    const result = await bnnEngine.analyze(chartNoPending, 'CAREER', liveSignals(3))
    expect(result.pendingFlags?.length ?? 0).toBe(0)
  })

  it('all domains return valid shapes', async () => {
    for (const d of ALL_DOMAINS) {
      const r = await bnnEngine.analyze(SYNTHETIC_CHART_B, d, liveSignals(3))
      expect(r.school).toBe('bnn')
      expect(r.domain).toBe(d)
    }
  })
})

describe('YoginiEngine', () => {
  it('school is yogini', () => { expect(yoginiEngine.school).toBe('yogini') })

  it('no live signals => not available', async () => {
    const result = await yoginiEngine.analyze(SYNTHETIC_CHART, 'CAREER')
    expect(result.available).toBe(false)
    expect(result.domainScore).toBeNull()
  })

  it('names the running Yogini only from the ChartData passed in', async () => {
    const a = await yoginiEngine.analyze(SYNTHETIC_CHART, 'CAREER', liveSignals(3.5))
    const b = await yoginiEngine.analyze(SYNTHETIC_CHART_B, 'CAREER', liveSignals(3.5))
    expect(a.schoolVerdict).toContain('mangala')
    expect(a.schoolVerdict).toContain('1.50 years elapsed')
    expect(b.schoolVerdict).toContain('dhanya')
    expect(b.schoolVerdict).toContain('2.00 years elapsed')
  })

  it('without a Yogini state in the chart data, the period is reported not available (no embedded dasha)', async () => {
    const r = await yoginiEngine.analyze({ ...SYNTHETIC_CHART, yoginiDasha: undefined }, 'CAREER', liveSignals(3.5))
    expect(r.available).toBe(true)
    expect(r.schoolVerdict).toContain('running Yogini is not available')
    for (const name of ['mangala', 'pingala', 'dhanya', 'bhramari', 'bhadrika', 'ulka', 'siddha', 'sankata']) {
      expect(r.schoolVerdict.toLowerCase()).not.toContain(name)
    }
  })

  it('no pending flags on yogini engine', async () => {
    const result = await yoginiEngine.analyze(SYNTHETIC_CHART, 'CAREER', liveSignals(3))
    expect(result.pendingFlags?.length ?? 0).toBe(0)
  })

  it('domainScore bounded by [0, 5]', async () => {
    for (const d of ALL_DOMAINS) {
      const r = await yoginiEngine.analyze(SYNTHETIC_CHART, d, liveSignals(8))
      expect(r.domainScore as number).toBeGreaterThanOrEqual(0)
      expect(r.domainScore as number).toBeLessThanOrEqual(5)
    }
  })

  it('all domains produce non-empty verdicts', async () => {
    for (const d of ALL_DOMAINS) {
      const r = await yoginiEngine.analyze(SYNTHETIC_CHART, d, liveSignals(3))
      expect(r.schoolVerdict.length).toBeGreaterThan(20)
    }
  })
})
