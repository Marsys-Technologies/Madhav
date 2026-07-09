/**
 * R5.1 C2 item 4 (posterior cardinality + base_rate_source stamping) — regression test.
 *
 * Fixture row is VERBATIM a real phala_anchors row read live from prod (Cloud SQL Auth Proxy,
 * 2026-07-09) for the native chart (482012f1-…): posterior=0.322, lift_vector_jsonb
 * {base_rate:0.2, promise_lift:1.75, trigger_lift:1, activation_lift:1,
 * ayanamsha_robustness_modifier:0.92}.
 *
 * Asserts query_predictive_anchors never re-derives or changes the stored posterior/lift
 * values (canonical-or-floor discipline) while stamping honest provenance: the real
 * base_rate_source description, and an explicit (never fabricated) cardinality=null since
 * this is a deterministic product model with no sample-size analog.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const queryMock = vi.fn()

vi.mock('@/lib/db/client', () => ({ query: (...args: unknown[]) => queryMock(...args) }))

import { queryPredictiveAnchorsCapability } from '../query_predictive_anchors'

const NATIVE_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

const REAL_ANCHOR_ROW = {
  anchor_id: '2710e082-1c36-4d60-bd54-dce0195a9ba6',
  domain: 'career',
  posterior: 0.322,
  lift_vector_jsonb: {
    base_rate: 0.2,
    posterior: 0.322,
    promise_lift: 1.75,
    trigger_lift: 1,
    activation_lift: 1,
    ayanamsha_robustness_modifier: 0.92,
  },
}

describe('query_predictive_anchors — posterior_provenance (R5.1 C2 item 4)', () => {
  beforeEach(() => {
    queryMock.mockReset()
  })
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('stamps base_rate_source + explicit-null cardinality WITHOUT altering the stored posterior/lift_vector_jsonb values', async () => {
    queryMock.mockResolvedValueOnce({ rows: [REAL_ANCHOR_ROW] })

    const result = await queryPredictiveAnchorsCapability.handler({ chart_id: NATIVE_CHART_ID }, undefined) as {
      content: { anchors: Array<Record<string, unknown>> }
      is_error: boolean
    }

    expect(result.is_error).toBe(false)
    const anchor = result.content.anchors[0]

    // Canonical-or-floor: the underlying computed values are untouched.
    expect(anchor.posterior).toBe(0.322)
    expect(anchor.lift_vector_jsonb).toEqual(REAL_ANCHOR_ROW.lift_vector_jsonb)

    const prov = anchor.posterior_provenance as Record<string, unknown>
    expect(prov).toBeDefined()
    expect(prov.model).toBe('deterministic_product_lift')
    // Never fabricates a sample size for a model that has none.
    expect(prov.cardinality).toBeNull()
    expect(String(prov.cardinality_note)).toMatch(/not a sample-fit/i)
    expect(String(prov.base_rate_source)).toContain('brahma_event_ontology')
    expect(prov.base_rate_value).toBe(0.2)
  })

  it('anchors written before BA-P5B (posterior/lift_vector_jsonb null) get an honest null provenance block, never a backfilled guess', async () => {
    queryMock.mockResolvedValueOnce({
      rows: [{ anchor_id: 'legacy-anchor', domain: 'career', posterior: null, lift_vector_jsonb: null }],
    })

    const result = await queryPredictiveAnchorsCapability.handler({ chart_id: NATIVE_CHART_ID }, undefined) as {
      content: { anchors: Array<Record<string, unknown>> }
      is_error: boolean
    }

    const anchor = result.content.anchors[0]
    expect(anchor.posterior_provenance).toBeNull()
    expect(String(anchor.posterior_provenance_note)).toMatch(/not computed/i)
  })
})
