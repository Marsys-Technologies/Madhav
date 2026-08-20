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

  // GA-5 review finding on #1386: the numeric fields being nulled means nothing if the
  // exact same grade is still readable in plain text in `statement`, served in the same
  // row. Live-confirmed: mi_darshana.py embeds every row's statement as
  // "{name}: {status} (grade {grade:.1f}/10). {note}" -- including suppressed rows.
  it('evidence_grade=structural → the grade embedded in statement text is ALSO redacted, not just the structured fields', async () => {
    queryMock.mockResolvedValueOnce({
      rows: [row({ evidence_grade: 'structural', statement: 'Career Setback: promised (grade 8.8/10). Strong evidence, corroborated across traditions.' })],
    })
    queryMock.mockResolvedValueOnce({ rows: [{}] })
    const result = await queryInsightsCapability.handler({ chart_id: NATIVE_CHART_ID }, undefined) as {
      content: { insight_units: Array<Record<string, unknown>> }
    }
    const unit = result.content.insight_units[0]
    expect(unit.rank_consequence).toBeNull()
    // the recoverable number must be gone from the served statement text
    expect(String(unit.statement)).not.toMatch(/8\.8/)
    expect(String(unit.statement)).not.toMatch(/\(grade\s+[\d.]+\/10\)/i)
    // the rest of the statement (name, status, non-numeric prose) survives unredacted
    expect(String(unit.statement)).toContain('Career Setback')
    expect(String(unit.statement)).toContain('promised')
    expect(String(unit.statement)).toContain('Strong evidence, corroborated across traditions.')
  })

  it('evidence_grade=assignment_only (an unrecognized/not-allowlisted value) → also suppressed, fail-closed', async () => {
    queryMock.mockResolvedValueOnce({ rows: [row({ evidence_grade: 'assignment_only' })] })
    queryMock.mockResolvedValueOnce({ rows: [{}] })
    const result = await queryInsightsCapability.handler({ chart_id: NATIVE_CHART_ID }, undefined) as {
      content: { insight_units: Array<Record<string, unknown>> }
    }
    expect(result.content.insight_units[0].rank_consequence).toBeNull()
  })

  // GA-5 review finding on #1386 round 2: the round-1 fix redacted only the 'verdict_object'
  // template's "(grade N.N/10)" shape -- mi_darshana.py has (at least) 3 more templates that
  // embed the same suppressed value differently. Live-confirmed 6 of 84 non-empirical rows
  // (load_bearing + calibrated_outlook) leaked through round 1's fix untouched.
  it('evidence_grade=structural, load_bearing template → the embedded sensitivity value is ALSO redacted', async () => {
    queryMock.mockResolvedValueOnce({
      rows: [row({
        insight_type: 'load_bearing', evidence_grade: 'structural',
        statement: 'Career Setback is load-bearing for this reading (sensitivity=0.60). Removing this signal would materially alter the reading.',
      })],
    })
    queryMock.mockResolvedValueOnce({ rows: [{}] })
    const result = await queryInsightsCapability.handler({ chart_id: NATIVE_CHART_ID }, undefined) as {
      content: { insight_units: Array<Record<string, unknown>> }
    }
    const unit = result.content.insight_units[0]
    expect(String(unit.statement)).not.toMatch(/0\.60/)
    expect(String(unit.statement)).not.toMatch(/\(sensitivity=[\d.]+\)/i)
    expect(String(unit.statement)).toContain('load-bearing for this reading')
    expect(String(unit.statement)).toContain('Removing this signal would materially alter the reading.')
  })

  it('evidence_grade=prior_only, calibrated_outlook template → the embedded outcome-rate value is ALSO redacted', async () => {
    queryMock.mockResolvedValueOnce({
      rows: [row({
        insight_type: 'calibrated_outlook', evidence_grade: 'prior_only',
        statement: 'Across similar charts, the observed outcome rate is 0.0% across 12 events matching this pattern.',
      })],
    })
    queryMock.mockResolvedValueOnce({ rows: [{}] })
    const result = await queryInsightsCapability.handler({ chart_id: NATIVE_CHART_ID }, undefined) as {
      content: { insight_units: Array<Record<string, unknown>> }
    }
    const unit = result.content.insight_units[0]
    expect(String(unit.statement)).not.toMatch(/0\.0%/)
    expect(String(unit.statement)).not.toMatch(/outcome rate is [\d.]+%/i)
    expect(String(unit.statement)).toContain('across 12 events matching this pattern.')
  })

  // GA-5 review finding on #1386 round 3: manifestation_grammar's non-empirical branch
  // (mi_darshana.py line 179) embeds "(prior-based estimate: N%)" -- latent on the canonical
  // chart today (all 7 manifestation_grammar rows are currently evidence_grade=empirical)
  // but the branch is reachable and would leak identically to the other 3 shapes.
  it('evidence_grade=assignment_only, manifestation_grammar template → the embedded prior-based estimate is ALSO redacted', async () => {
    queryMock.mockResolvedValueOnce({
      rows: [row({
        insight_type: 'manifestation_grammar', evidence_grade: 'assignment_only',
        statement: 'Channel propensity for this configuration: insufficient evidence for an empirical grade (prior-based estimate: 42%).',
      })],
    })
    queryMock.mockResolvedValueOnce({ rows: [{}] })
    const result = await queryInsightsCapability.handler({ chart_id: NATIVE_CHART_ID }, undefined) as {
      content: { insight_units: Array<Record<string, unknown>> }
    }
    const unit = result.content.insight_units[0]
    expect(String(unit.statement)).not.toMatch(/42%/)
    expect(String(unit.statement)).not.toMatch(/prior-based estimate: [\d.]+%/i)
    expect(String(unit.statement)).toContain('insufficient evidence for an empirical grade')
  })
})
