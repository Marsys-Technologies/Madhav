/**
 * R5.1 C2 item 4 (posterior cardinality + base_rate_source stamping) — regression test.
 *
 * Fixture row is VERBATIM a real phala_anchors row read live from prod (Cloud SQL Auth Proxy,
 * 2026-07-09) for the native chart (482012f1-…): posterior=0.322, lift_vector_jsonb
 * {base_rate:0.2, promise_lift:1.75, trigger_lift:1, activation_lift:1,
 * ayanamsha_robustness_modifier:0.92}.
 *
 * Updated by F-68 (P3-b tier-suppression): the real prod row always carries
 * confidence_basis='structural_not_yet_empirical', so the original test now asserts
 * suppression (not pass-through). A CALIBRATED_ANCHOR_ROW fixture is added to preserve
 * the original canonical-or-floor assertion for future calibrated rows.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const queryMock = vi.fn()

vi.mock('@/lib/db/client', () => ({ query: (...args: unknown[]) => queryMock(...args) }))

import { queryPredictiveAnchorsCapability } from '../query_predictive_anchors'

const NATIVE_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

// The real prod row carries confidence_basis='structural_not_yet_empirical' — post-F-68
// this row is correctly suppressed at serve time (numeric fields nulled, tag preserved).
const REAL_ANCHOR_ROW = {
  anchor_id: '2710e082-1c36-4d60-bd54-dce0195a9ba6',
  domain: 'career',
  confidence_basis: 'structural_not_yet_empirical',
  posterior: 0.322,
  confidence_low: 0.20,
  confidence_high: 0.45,
  lift_vector_jsonb: {
    base_rate: 0.2,
    posterior: 0.322,
    promise_lift: 1.75,
    trigger_lift: 1,
    activation_lift: 1,
    ayanamsha_robustness_modifier: 0.92,
  },
}

// Same numeric values, calibrated tag — preserves the original canonical-or-floor intent
// for future rows that have undergone empirical calibration (none in prod today).
const CALIBRATED_ANCHOR_ROW = {
  ...REAL_ANCHOR_ROW,
  confidence_basis: 'some_future_calibrated_value',
}

describe('query_predictive_anchors — posterior_provenance (R5.1 C2 item 4)', () => {
  beforeEach(() => {
    queryMock.mockReset()
  })
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('real prod row (confidence_basis=structural_not_yet_empirical) → numeric fields suppressed, tag preserved, suppression note emitted', async () => {
    queryMock.mockResolvedValueOnce({ rows: [REAL_ANCHOR_ROW] })

    const result = await queryPredictiveAnchorsCapability.handler({ chart_id: NATIVE_CHART_ID }, undefined) as {
      content: { anchors: Array<Record<string, unknown>> }
      is_error: boolean
    }

    expect(result.is_error).toBe(false)
    const anchor = result.content.anchors[0]

    // P3-b suppression: numeric fields nulled, confidence_basis tag survives.
    expect(anchor.posterior).toBeNull()
    expect(anchor.confidence_low).toBeNull()
    expect(anchor.lift_vector_jsonb).toBeNull()
    expect(anchor.posterior_provenance).toBeNull()
    expect(String(anchor.posterior_provenance_note)).toMatch(/suppressed at serve time/i)
    expect(anchor.confidence_basis).toBe('structural_not_yet_empirical')
  })

  it('calibrated row → stamps base_rate_source + explicit-null cardinality WITHOUT altering stored posterior/lift values (canonical-or-floor)', async () => {
    queryMock.mockResolvedValueOnce({ rows: [CALIBRATED_ANCHOR_ROW] })

    const result = await queryPredictiveAnchorsCapability.handler({ chart_id: NATIVE_CHART_ID }, undefined) as {
      content: { anchors: Array<Record<string, unknown>> }
      is_error: boolean
    }

    expect(result.is_error).toBe(false)
    const anchor = result.content.anchors[0]

    // Canonical-or-floor: calibrated row's computed values are untouched.
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

// ── T-5 fix (A-6/B-1): §N.6 empty-reason discipline — no silent empties ─────────
describe('query_predictive_anchors — empty_reason / known_gap (T-5, A-6/B-1)', () => {
  beforeEach(() => queryMock.mockReset())
  afterEach(() => vi.restoreAllMocks())

  it('empty backing set for the chart → empty_reason + known_gap CR-66 (never a silent empty)', async () => {
    // 1st call: main anchor query → empty. 2nd call: chart-total count → 0.
    queryMock.mockResolvedValueOnce({ rows: [] })
    queryMock.mockResolvedValueOnce({ rows: [{ n: 0 }] })

    const result = await queryPredictiveAnchorsCapability.handler({ chart_id: NATIVE_CHART_ID }, undefined) as {
      content: { anchors: unknown[]; anchor_count: number; empty_reason: string | null; known_gap: string | null; provenance: { backing_data_reachable: boolean } }
      is_error: boolean
    }

    expect(result.is_error).toBe(false)
    expect(result.content.anchor_count).toBe(0)
    expect(result.content.empty_reason).toBeTruthy()
    expect(result.content.known_gap).toBe('CR-66')
    expect(result.content.provenance.backing_data_reachable).toBe(true)
  })

  it('filter miss (chart HAS anchors, none match filter) → distinct empty_reason + CR-66, not silent', async () => {
    queryMock.mockResolvedValueOnce({ rows: [] })          // filtered main query
    queryMock.mockResolvedValueOnce({ rows: [{ n: 42 }] }) // chart total > 0

    const result = await queryPredictiveAnchorsCapability.handler({ chart_id: NATIVE_CHART_ID, domain: 'wealth' }, undefined) as {
      content: { empty_reason: string | null; known_gap: string | null }
      is_error: boolean
    }

    expect(result.content.empty_reason).toContain('42 anchor')
    expect(String(result.content.empty_reason)).toMatch(/filter/i)
    expect(result.content.known_gap).toBe('CR-66')
  })

  it('unreachable count → backing_data_reachable false + honest empty_reason (not a confirmed zero)', async () => {
    queryMock.mockResolvedValueOnce({ rows: [] })                 // main query empty
    queryMock.mockRejectedValueOnce(new Error('DATABASE_URL not set')) // count throws

    const result = await queryPredictiveAnchorsCapability.handler({ chart_id: NATIVE_CHART_ID }, undefined) as {
      content: { empty_reason: string | null; provenance: { backing_data_reachable: boolean } }
      is_error: boolean
    }

    expect(result.is_error).toBe(false)
    expect(result.content.provenance.backing_data_reachable).toBe(false)
    expect(String(result.content.empty_reason)).toMatch(/unreachable|could not be read/i)
  })

  it('non-empty result carries empty_reason=null / known_gap=null', async () => {
    queryMock.mockResolvedValueOnce({ rows: [REAL_ANCHOR_ROW] })

    const result = await queryPredictiveAnchorsCapability.handler({ chart_id: NATIVE_CHART_ID }, undefined) as {
      content: { empty_reason: string | null; known_gap: string | null; anchor_count: number }
    }

    expect(result.content.anchor_count).toBe(1)
    expect(result.content.empty_reason).toBeNull()
    expect(result.content.known_gap).toBeNull()
  })
})
