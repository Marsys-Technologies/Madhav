import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const queryMock = vi.fn()
vi.mock('@/lib/db/client', () => ({ query: (...args: unknown[]) => queryMock(...args) }))

import { queryInsightsCapability } from '../query_insights'

const NATIVE_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

function row(overrides: Record<string, unknown>) {
  return {
    insight_id: 'ins-test', insight_type: 'verdict_object', domain: 'career',
    statement: 'test statement', rank_consequence: 0.88, confidence_band: '[0.68,0.98)',
    n_support: 3, is_negative_knowledge: false,
    provenance_chain: { grade: 8.8, ranked_evidence: [{ salience: 0.9, fact_id: 'f1' }] },
    ...overrides,
  }
}

describe('query_insights — P3-b tier-suppression (F-69)', () => {
  beforeEach(() => queryMock.mockReset())
  afterEach(() => vi.restoreAllMocks())

  it('evidence_grade=structural → rank_consequence/confidence_band/provenance_chain.grade suppressed, tag + other provenance_chain keys preserved', async () => {
    queryMock.mockResolvedValueOnce({ rows: [row({ evidence_grade: 'structural' })] })
    queryMock.mockResolvedValueOnce({ rows: [{}] }) // calibration_summary query
    const result = await queryInsightsCapability.handler({ chart_id: NATIVE_CHART_ID }, undefined) as {
      content: { insight_units: Array<Record<string, unknown>> }
    }
    const unit = result.content.insight_units[0]
    expect(unit.rank_consequence).toBeNull()
    expect(unit.confidence_band).toBeNull()
    expect((unit.provenance_chain as Record<string, unknown>).grade).toBeNull()
    // Non-numeric provenance_chain content survives — unrelated to this suppression.
    expect((unit.provenance_chain as Record<string, unknown>).ranked_evidence).toBeDefined()
    expect(String(unit.tier_suppression_note)).toMatch(/suppressed at serve time/i)
    expect(unit.evidence_grade).toBe('structural')
  })

  it('evidence_grade=prior_only (retrodiction, n_support<5) → also suppressed', async () => {
    queryMock.mockResolvedValueOnce({ rows: [row({ insight_type: 'emergent_law', evidence_grade: 'prior_only' })] })
    queryMock.mockResolvedValueOnce({ rows: [{}] })
    const result = await queryInsightsCapability.handler({ chart_id: NATIVE_CHART_ID }, undefined) as {
      content: { insight_units: Array<Record<string, unknown>> }
    }
    expect(result.content.insight_units[0].rank_consequence).toBeNull()
  })

  it('evidence_grade=empirical → numeric fields pass through unchanged (honest-conditional C3 case preserved)', async () => {
    queryMock.mockResolvedValueOnce({ rows: [row({ insight_type: 'emergent_law', evidence_grade: 'empirical', n_support: 7 })] })
    queryMock.mockResolvedValueOnce({ rows: [{}] })
    const result = await queryInsightsCapability.handler({ chart_id: NATIVE_CHART_ID }, undefined) as {
      content: { insight_units: Array<Record<string, unknown>> }
    }
    const unit = result.content.insight_units[0]
    expect(unit.rank_consequence).toBe(0.88)
    expect((unit.provenance_chain as Record<string, unknown>).grade).toBe(8.8)
    expect(unit.tier_suppression_note).toBeUndefined()
  })
})
