import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('server-only', () => ({}))

const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

import { computeKpis } from '../kpi_aggregator'

beforeEach(() => mockQuery.mockReset())

function rows<T>(r: T[]) {
  return { rows: r }
}

function mockBySql(map: (sql: string) => { rows: unknown[] } | null) {
  mockQuery.mockImplementation((...args: unknown[]) => {
    const sql = typeof args[0] === 'string' ? (args[0] as string) : ''
    const hit = map(sql)
    return Promise.resolve(hit ?? { rows: [] })
  })
}

describe('computeKpis', () => {
  it('computes plan_accuracy_recall/precision from mixed correct/wrong rows', async () => {
    mockBySql((sql) => {
      if (sql.includes('plan_unjudged_consume')) {
        return rows([{
          plan_correct: '8', plan_wrong: '2', plan_unjudged_consume: '5',
          citation_yes: '9', citation_total: '10',
        }])
      }
      if (sql.includes('b10_clean') && sql.includes('b11_clean')) {
        return rows([{ total: '10', b10_clean: '10', b11_clean: '9' }])
      }
      if (sql.includes('AVG(pl.brier_score)')) {
        return rows([{ avg_brier: 0.18, n: '5' }])
      }
      if (sql.includes('percentile_cont') && sql.includes('query_class')) {
        return rows([
          { query_class: 'factual', p50: 900, p95: 2100 },
          { query_class: 'interpretive', p50: 2300, p95: 6100 },
        ])
      }
      if (sql.includes('percentile_cont')) {
        return rows([{ p50: 1800, p95: 5400, pass: '99', n: '100' }])
      }
      if (sql.includes('retrieval_hit = true') && sql.includes('AS hit')) {
        return rows([{ hit: '93', n: '100' }])
      }
      return rows([
        { bucket: '2026-05-01T00:00:00Z', n: '10', correct: '8', wrong: '2', b10_clean: '10', pass: '10', hit: '9' },
      ])
    })

    const out = await computeKpis({ start: '2026-05-01T00:00:00Z', end: '2026-05-08T00:00:00Z', source: 'all' })
    expect(out.bundles.pipeline_correctness.plan_accuracy_recall).toBeCloseTo(0.8)
    expect(out.bundles.pipeline_correctness.plan_accuracy_precision).toBeCloseTo(0.8)
    expect(out.bundles.pipeline_correctness.plan_accuracy_n).toBe(10)
    expect(out.bundles.pipeline_correctness.plan_accuracy_consume_unjudged_n).toBe(5)
    expect(out.bundles.pipeline_correctness.citation_rate).toBeCloseTo(0.9)
  })

  it('returns null (not NaN) when no rows match', async () => {
    mockBySql((sql) => {
      if (sql.includes('plan_unjudged_consume')) return rows([{ plan_correct: '0', plan_wrong: '0', plan_unjudged_consume: '0', citation_yes: '0', citation_total: '0' }])
      if (sql.includes('b10_clean')) return rows([{ total: '0', b10_clean: '0', b11_clean: '0' }])
      if (sql.includes('AVG(pl.brier_score)')) return rows([{ avg_brier: null, n: '0' }])
      if (sql.includes('percentile_cont') && sql.includes('query_class')) return rows([])
      if (sql.includes('percentile_cont')) return rows([{ p50: null, p95: null, pass: '0', n: '0' }])
      if (sql.includes('AS hit')) return rows([{ hit: '0', n: '0' }])
      return rows([])
    })
    const out = await computeKpis({ start: '2026-05-01T00:00:00Z', end: '2026-05-08T00:00:00Z', source: 'all' })
    expect(out.bundles.pipeline_correctness.plan_accuracy_recall).toBeNull()
    expect(out.bundles.pipeline_correctness.citation_rate).toBeNull()
    expect(out.bundles.answer_quality.calibration_brier).toBeNull()
    expect(out.bundles.answer_quality.b10_compliance_rate).toBeNull()
    expect(out.bundles.performance_health.latency_p50_ms).toBeNull()
    expect(out.bundles.retrieval_health.retrieval_hit_rate).toBeNull()
  })

  it('surfaces calibration_brier=null when no observed outcomes', async () => {
    mockBySql((sql) => {
      if (sql.includes('plan_unjudged_consume')) return rows([{ plan_correct: '5', plan_wrong: '0', plan_unjudged_consume: '0', citation_yes: '5', citation_total: '5' }])
      if (sql.includes('b10_clean')) return rows([{ total: '5', b10_clean: '5', b11_clean: '5' }])
      if (sql.includes('AVG(pl.brier_score)')) return rows([{ avg_brier: null, n: '0' }])
      if (sql.includes('percentile_cont') && sql.includes('query_class')) return rows([])
      if (sql.includes('percentile_cont')) return rows([{ p50: 1000, p95: 1500, pass: '5', n: '5' }])
      if (sql.includes('AS hit')) return rows([{ hit: '5', n: '5' }])
      return rows([])
    })
    const out = await computeKpis({ start: '2026-05-01T00:00:00Z', end: '2026-05-08T00:00:00Z', source: 'all' })
    expect(out.bundles.answer_quality.calibration_brier).toBeNull()
    expect(out.bundles.answer_quality.calibration_n).toBe(0)
  })

  it('rounds latency percentiles to integers', async () => {
    mockBySql((sql) => {
      if (sql.includes('plan_unjudged_consume')) return rows([{ plan_correct: '0', plan_wrong: '0', plan_unjudged_consume: '0', citation_yes: '0', citation_total: '0' }])
      if (sql.includes('b10_clean')) return rows([{ total: '0', b10_clean: '0', b11_clean: '0' }])
      if (sql.includes('AVG(pl.brier_score)')) return rows([{ avg_brier: null, n: '0' }])
      if (sql.includes('percentile_cont') && sql.includes('query_class')) return rows([])
      if (sql.includes('percentile_cont')) return rows([{ p50: 1799.6, p95: 5399.4, pass: '0', n: '10' }])
      if (sql.includes('AS hit')) return rows([{ hit: '0', n: '0' }])
      return rows([])
    })
    const out = await computeKpis({ start: '2026-05-01T00:00:00Z', end: '2026-05-08T00:00:00Z', source: 'all' })
    expect(out.bundles.performance_health.latency_p50_ms).toBe(1800)
    expect(out.bundles.performance_health.latency_p95_ms).toBe(5399)
  })

  it('respects source filter (consume vs all) in SQL params', async () => {
    const seenSql: string[] = []
    mockQuery.mockImplementation((...args: unknown[]) => {
      const sql = typeof args[0] === 'string' ? (args[0] as string) : ''
      seenSql.push(sql)
      if (sql.includes('plan_unjudged_consume')) return Promise.resolve(rows([{ plan_correct: '0', plan_wrong: '0', plan_unjudged_consume: '0', citation_yes: '0', citation_total: '0' }]))
      if (sql.includes('b10_clean')) return Promise.resolve(rows([{ total: '0', b10_clean: '0', b11_clean: '0' }]))
      if (sql.includes('AVG(pl.brier_score)')) return Promise.resolve(rows([{ avg_brier: null, n: '0' }]))
      if (sql.includes('percentile_cont') && sql.includes('query_class')) return Promise.resolve(rows([]))
      if (sql.includes('percentile_cont')) return Promise.resolve(rows([{ p50: null, p95: null, pass: '0', n: '0' }]))
      if (sql.includes('AS hit')) return Promise.resolve(rows([{ hit: '0', n: '0' }]))
      return Promise.resolve(rows([]))
    })

    await computeKpis({ start: '2026-05-01T00:00:00Z', end: '2026-05-08T00:00:00Z', source: 'consume' })
    expect(seenSql.some((s) => s.includes('AND source = $3'))).toBe(true)
  })

  it('produces sparkline arrays for every bundle (even empty)', async () => {
    mockBySql((sql) => {
      if (sql.includes('plan_unjudged_consume')) return rows([{ plan_correct: '0', plan_wrong: '0', plan_unjudged_consume: '0', citation_yes: '0', citation_total: '0' }])
      if (sql.includes('b10_clean')) return rows([{ total: '0', b10_clean: '0', b11_clean: '0' }])
      if (sql.includes('AVG(pl.brier_score)')) return rows([{ avg_brier: null, n: '0' }])
      if (sql.includes('percentile_cont') && sql.includes('query_class')) return rows([])
      if (sql.includes('percentile_cont')) return rows([{ p50: null, p95: null, pass: '0', n: '0' }])
      if (sql.includes('AS hit')) return rows([{ hit: '0', n: '0' }])
      return rows([])
    })
    const out = await computeKpis({ start: '2026-05-01T00:00:00Z', end: '2026-05-08T00:00:00Z', source: 'all' })
    expect(out.sparklines).toHaveProperty('pipeline_correctness')
    expect(out.sparklines).toHaveProperty('answer_quality')
    expect(out.sparklines).toHaveProperty('performance_health')
    expect(out.sparklines).toHaveProperty('retrieval_health')
    expect(Array.isArray(out.sparklines.pipeline_correctness)).toBe(true)
  })
})
