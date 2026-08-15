/**
 * query_prospective_ledger — SARVA-SIDDHI W-2 P-1 tests.
 *
 * Proves the repointed E-2 `standing_predictions_read` serving surface: the LIVE prospective
 * ledger (brahma_prospective_ledger) read, domain-layered per §N.6, with an explicit
 * empty_reason on an empty result (the B-1/A-6 silent-empty this lane must not repeat).
 *
 * The three real filed predictions this lane exists to surface (all filed 2026-07-19,
 * D-4a Lane A-4, provenance intact in the ledger) are used as the fixture rows:
 *   - Sat–Jupiter pratyantar 2027-04-09..2027-08-18   (major_gain,          wealth)
 *   - Ketu-MD consolidation shape 2027-08-17..2034    (major_gain,          wealth)
 *   - Venus-MD onset 2034-08-17                        (property_acquisition, residence)
 * On a wealth plan, all THREE must surface — the residence-domain Venus-MD prediction via
 * the documented wealth ⊇ {wealth, residence} material/asset cluster.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockQuery = vi.fn()
vi.mock('@/lib/db/client', () => ({ query: (sql: string, params: unknown[]) => mockQuery(sql, params) }))

import { queryProspectiveLedgerCapability } from '../query_prospective_ledger'
import { checkCapability } from '../../../chart_agnostic_gate'

const NATIVE_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

/** Minimal ledger-row shape the handler reads (+ ontology_domain from the join). */
function row(overrides: Record<string, unknown>): Record<string, unknown> {
  return {
    prediction_id: 'p', chart_id: NATIVE_CHART_ID, claim: 'c', event_class: 'major_gain',
    claim_shape: 'interval', observation_window: '[2027-04-09,2027-08-19)', milestone_set: null,
    model: 'm', formula_version: 'f', confidence: 0.6, falsifier: 'x', as_of: '2026-07-19T00:00:00Z',
    generator_class: 'reading_synthesis', configuration_signature: null, lifecycle_status: 'open',
    matched_event_id: null, matched_at: null, match_note: null, filed_by: 'native', filing_method: 'explicit_filing_tool',
    source_citation: 's', created_at: '2026-07-19T00:00:00Z', ontology_domain: 'wealth',
    ...overrides,
  }
}

const THREE_WEALTH_ARC = [
  row({ prediction_id: 'sat-jup', claim: 'Saturn-Jupiter pratyantar dasha convergence', event_class: 'major_gain', ontology_domain: 'wealth', observation_window: '[2027-04-09,2027-08-19)' }),
  row({ prediction_id: 'ketu-md', claim: 'Ketu Mahadasha consolidation shape', event_class: 'major_gain', ontology_domain: 'wealth', observation_window: '[2027-08-17,2034-08-18)' }),
  row({ prediction_id: 'venus-md', claim: 'Venus Mahadasha onset', event_class: 'property_acquisition', ontology_domain: 'residence', claim_shape: 'point', observation_window: '[2034-08-17,2034-08-18)' }),
]

describe('query_prospective_ledger — descriptor + gate', () => {
  beforeEach(() => mockQuery.mockReset())

  it('passes the chart-agnostic gate (0 violations)', () => {
    expect(checkCapability(queryProspectiveLedgerCapability)).toHaveLength(0)
  })

  it('declares an empty_reason density_contract (§N.6 — no silent empties)', () => {
    expect(queryProspectiveLedgerCapability.density_contract?.empty_reason).toBe(true)
  })

  it('description carries no native chart UUID', () => {
    expect(queryProspectiveLedgerCapability.description).not.toContain(NATIVE_CHART_ID)
  })
})

describe('query_prospective_ledger — domain layering (§N.6 / B.10)', () => {
  beforeEach(() => mockQuery.mockReset())

  it('surfaces ALL THREE wealth-arc predictions on a wealth plan (residence via the asset cluster)', async () => {
    mockQuery.mockResolvedValueOnce({ rows: THREE_WEALTH_ARC })
    const res = await queryProspectiveLedgerCapability.handler(
      { chart_id: NATIVE_CHART_ID, domain: 'wealth' }, undefined,
    ) as { content: Record<string, unknown> }
    const preds = res.content['predictions'] as Array<{ prediction_id: string }>
    const ids = preds.map((p) => p.prediction_id)
    expect(ids).toContain('sat-jup')
    expect(ids).toContain('ketu-md')
    expect(ids).toContain('venus-md') // residence-domain, surfaced via wealth ⊇ {wealth, residence}
    expect(res.content['prediction_count']).toBe(3)
    expect(res.content['empty_reason']).toBeNull()
    expect(res.content['filters']).toMatchObject({ domain_cluster: ['wealth', 'residence'] })
  })

  it('never drops non-matching open predictions — they go to other_domain_predictions (B.10)', async () => {
    const rows = [
      ...THREE_WEALTH_ARC,
      row({ prediction_id: 'spiritual', event_class: 'spiritual_turn', ontology_domain: 'spirituality', claim_shape: 'interval' }),
    ]
    mockQuery.mockResolvedValueOnce({ rows })
    const res = await queryProspectiveLedgerCapability.handler(
      { chart_id: NATIVE_CHART_ID, domain: 'wealth' }, undefined,
    ) as { content: Record<string, unknown> }
    expect(res.content['prediction_count']).toBe(3)
    const other = res.content['other_domain_predictions'] as Array<{ prediction_id: string }>
    expect(other.map((p) => p.prediction_id)).toEqual(['spiritual'])
    expect(res.content['total_open_count']).toBe(4)
  })

  it('emits an explicit empty_reason when no filed predictions exist (no bare silent empty)', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    const res = await queryProspectiveLedgerCapability.handler(
      { chart_id: NATIVE_CHART_ID, domain: 'wealth' }, undefined,
    ) as { content: Record<string, unknown> }
    expect(res.content['prediction_count']).toBe(0)
    expect(typeof res.content['empty_reason']).toBe('string')
    expect(res.content['empty_reason']).toMatch(/explicit filing/i)
  })

  it('emits an empty_reason pointing to other_domain_predictions when open rows exist but none match the domain', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [row({ prediction_id: 'spiritual', event_class: 'spiritual_turn', ontology_domain: 'spirituality' })] })
    const res = await queryProspectiveLedgerCapability.handler(
      { chart_id: NATIVE_CHART_ID, domain: 'wealth' }, undefined,
    ) as { content: Record<string, unknown> }
    expect(res.content['prediction_count']).toBe(0)
    expect(res.content['other_domain_count']).toBe(1)
    expect(res.content['empty_reason']).toMatch(/other_domain_predictions/)
  })

  it('with no domain arg returns every open prediction in predictions (no clustering)', async () => {
    mockQuery.mockResolvedValueOnce({ rows: THREE_WEALTH_ARC })
    const res = await queryProspectiveLedgerCapability.handler(
      { chart_id: NATIVE_CHART_ID }, undefined,
    ) as { content: Record<string, unknown> }
    expect(res.content['prediction_count']).toBe(3)
    expect(res.content['other_domain_count']).toBe(0)
    expect(res.content['empty_reason']).toBeNull()
  })
})

describe('query_prospective_ledger — empty-window guard (EKV C-03)', () => {
  beforeEach(() => mockQuery.mockReset())

  it('toServed does not throw for observation_window="empty" — returns null dates (covers C-03 second read path)', async () => {
    // 6 brahma_prospective_ledger rows were filed with observation_window='empty' on 2026-08-11
    // by w45_post_fit_rebuild. Before PR #1287, deriveWindowFields -> parseDaterange threw on
    // 'empty', crashing the entire standing_predictions_read call. This test ensures the
    // query_prospective_ledger handler's toServed path (which calls deriveWindowFields) is
    // covered by the same null-passthrough guard.
    const emptyWindowRow = row({
      prediction_id: 'empty-win',
      claim: 'Gochara forecast: window 2068-09-04–2068-09-04',
      event_class: 'psychological_arc',
      observation_window: 'empty',
      filed_by: 'w45_post_fit_rebuild',
      generator_class: 'engine',
      lifecycle_status: 'open',
    })
    mockQuery.mockResolvedValueOnce({ rows: [emptyWindowRow] })
    // Must not throw:
    const res = await queryProspectiveLedgerCapability.handler(
      { chart_id: NATIVE_CHART_ID }, undefined,
    ) as { content: Record<string, unknown> }
    const preds = res.content['predictions'] as Array<Record<string, unknown>>
    const served = preds.find((p) => p['prediction_id'] === 'empty-win')
    expect(served).toBeDefined()
    // Empty window => null derived dates (same as missing window — not a crash)
    expect(served!['window_start']).toBeNull()
    expect(served!['window_end']).toBeNull()
    expect(served!['point_date']).toBeNull()
  })
})
