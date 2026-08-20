import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const queryMock = vi.fn()
vi.mock('@/lib/db/client', () => ({ query: (...args: unknown[]) => queryMock(...args) }))

import { queryPredictiveAnchorsCapability } from '../query_predictive_anchors'

const NATIVE_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

const BASE_ROW = {
  anchor_id: 'p3b-test-anchor', domain: 'career',
  posterior: 0.322,
  confidence_low: 0.20, confidence_high: 0.45,
  lift_vector_jsonb: {
    base_rate: 0.2, posterior: 0.322, promise_lift: 1.75,
    trigger_lift: 1, activation_lift: 1, ayanamsha_robustness_modifier: 0.92,
  },
}

describe('query_predictive_anchors — P3-b tier-suppression (F-68)', () => {
  beforeEach(() => queryMock.mockReset())
  afterEach(() => vi.restoreAllMocks())

  it('confidence_basis=structural_not_yet_empirical → numeric fields suppressed to null, tag preserved', async () => {
    queryMock.mockResolvedValueOnce({ rows: [{ ...BASE_ROW, confidence_basis: 'structural_not_yet_empirical' }] })
    const result = await queryPredictiveAnchorsCapability.handler({ chart_id: NATIVE_CHART_ID }, undefined) as {
      content: { anchors: Array<Record<string, unknown>> }
    }
    const anchor = result.content.anchors[0]
    expect(anchor.posterior).toBeNull()
    expect(anchor.confidence_low).toBeNull()
    expect(anchor.confidence_high).toBeNull()
    expect(anchor.lift_vector_jsonb).toBeNull()
    expect(anchor.posterior_provenance).toBeNull()
    expect(String(anchor.posterior_provenance_note)).toMatch(/suppressed at serve time/i)
    // The tag itself is the disclosure and must survive unchanged.
    expect(anchor.confidence_basis).toBe('structural_not_yet_empirical')
  })

  it('missing/null confidence_basis → fail-closed, also suppressed', async () => {
    const { confidence_basis, ...rowWithoutBasis } = { ...BASE_ROW, confidence_basis: undefined }
    queryMock.mockResolvedValueOnce({ rows: [rowWithoutBasis] })
    const result = await queryPredictiveAnchorsCapability.handler({ chart_id: NATIVE_CHART_ID }, undefined) as {
      content: { anchors: Array<Record<string, unknown>> }
    }
    expect(result.content.anchors[0].posterior).toBeNull()
  })

  // GA-5 review finding on #1378: this used to assert pass-through for an arbitrary
  // string ('empirically_calibrated') and call it "a genuinely calibrated
  // confidence_basis" -- but that string is not, and has never been, anything the write
  // path (ph_sodhana's leakage firewall) permits into this column; asserting pass-through
  // for it exercised a state the schema forbids, under an allowlist that is empty BY
  // DESIGN today (L4 is NO-SCORING; calibration is L5's job). The correct fail-closed
  // behavior is that an UNRECOGNIZED confidence_basis value suppresses exactly like the
  // known NOT_YET_CALIBRATED one -- there is currently no string that legitimately serves
  // calibrated numbers through this path.
  it('an unrecognized confidence_basis value (not in the allowlist) → also suppressed, fail-closed', async () => {
    queryMock.mockResolvedValueOnce({ rows: [{ ...BASE_ROW, confidence_basis: 'some_unexpected_tag_not_in_allowlist' }] })
    const result = await queryPredictiveAnchorsCapability.handler({ chart_id: NATIVE_CHART_ID }, undefined) as {
      content: { anchors: Array<Record<string, unknown>> }
    }
    const anchor = result.content.anchors[0]
    expect(anchor.posterior).toBeNull()
    expect(anchor.lift_vector_jsonb).toBeNull()
    expect(anchor.posterior_provenance).toBeNull()
  })

  it('pre-BA-P5B legacy row (posterior=null in DB, no confidence_basis) → not-computed note, not suppression note', async () => {
    queryMock.mockResolvedValueOnce({ rows: [{ anchor_id: 'legacy-anc', domain: 'career', posterior: null, lift_vector_jsonb: null }] })
    const result = await queryPredictiveAnchorsCapability.handler({ chart_id: NATIVE_CHART_ID }, undefined) as {
      content: { anchors: Array<Record<string, unknown>> }
    }
    const anchor = result.content.anchors[0]
    expect(anchor.posterior).toBeNull()
    expect(anchor.posterior_provenance).toBeNull()
    // Must be 'not computed', not 'suppressed at serve time' — the posterior never existed.
    expect(String(anchor.posterior_provenance_note)).toMatch(/not computed/i)
    expect(String(anchor.posterior_provenance_note)).not.toMatch(/suppressed at serve time/i)
  })
})
