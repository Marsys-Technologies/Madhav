/**
 * envelope_timing_prediction_w3.test.ts
 * ======================================
 * W3 Lane L7 (Retrieval Plane Elevation, plan §8 R-2 items 6 + 7):
 *   - TimingBlock extension (timing_anchored / applies_window / valid_until)
 *     round-trips through the real `buildRetrievalEnvelope` builder for a
 *     time-sensitive tool, and stays ADDITIVE (a non-time-sensitive response
 *     keeps the minimal 2-field TimingBlock).
 *   - The standardized PredictionClaim shape validates against the L5 Mīmāṃsā
 *     prospective ledger contract (`mimamsa_predictions`, migration
 *     `brahma_mimamsa_prediction_ledger.sql`, tool `log_prediction`) — its
 *     CHECK constraints are mirrored by `validatePredictionClaim`, and
 *     `predictionClaimToLedgerRow` maps onto the exact insert column set.
 */
import { describe, it, expect } from 'vitest'
import {
  buildRetrievalEnvelope,
  validatePredictionClaim,
  isPredictionClaimLedgerReady,
  predictionClaimToLedgerRow,
  type V3Envelope,
  type PredictionClaim,
} from '../envelope'

// A concrete time-sensitive judgment/prediction, modeled on what judgment_query
// (register_d9_judgment.ts Step 9) computes: an as_of_date anchor, a current-dasha
// applies-window, and an honest timing_anchored flag.
const AS_OF = '2026-07-20'

describe('W3 L7 — TimingBlock extension round-trips through the builder', () => {
  it('populates timing_anchored / applies_window / valid_until when the caller supplies them (v3)', () => {
    const env = buildRetrievalEnvelope(
      {
        tool: 'judgment_query',
        content: { verdict: 'promising' },
        as_of_date: AS_OF,
        timing_anchored: true,
        applies_window: { start: '2024-11-01', end: '2027-03-15' },
        valid_until: '2027-03-15',
      },
      'v3',
    ) as V3Envelope

    expect(env.response_format).toBe('v3')
    expect(env.timing.as_of_date).toBe(AS_OF)
    expect(typeof env.timing.computed_at).toBe('string')
    expect(env.timing.timing_anchored).toBe(true)
    expect(env.timing.applies_window).toEqual({ start: '2024-11-01', end: '2027-03-15' })
    expect(env.timing.valid_until).toBe('2027-03-15')
  })

  it('preserves an honest timing_anchored:false (never silently dropped)', () => {
    const env = buildRetrievalEnvelope(
      { tool: 'judgment_query', content: {}, as_of_date: AS_OF, timing_anchored: false },
      'v3',
    ) as V3Envelope
    expect(env.timing.timing_anchored).toBe(false)
  })

  it('stays additive: a non-time-sensitive response keeps only as_of_date + computed_at', () => {
    const env = buildRetrievalEnvelope(
      { tool: 'chart_facts_query', content: {}, as_of_date: AS_OF },
      'v3',
    ) as V3Envelope
    expect(env.timing.as_of_date).toBe(AS_OF)
    expect(env.timing.timing_anchored).toBeUndefined()
    expect(env.timing.applies_window).toBeUndefined()
    expect(env.timing.valid_until).toBeUndefined()
  })

  it('legacy format carries no timing block at all (byte-shape unchanged)', () => {
    const env = buildRetrievalEnvelope(
      { tool: 'judgment_query', content: {}, timing_anchored: true },
      'legacy',
    )
    expect('timing' in env).toBe(false)
  })
})

describe('W3 L7 — PredictionClaim shape aligns with the Mīmāṃsā ledger contract', () => {
  const validClaim: PredictionClaim = {
    claim: 'A significant career elevation (new role or title) manifests.',
    domain: 'career',
    horizon_date: '2027-03-15',
    applies_window: { start: '2024-11-01', end: '2027-03-15' },
    mechanism: 'Vimshottari Jupiter maha-dasha activating the 10th-lord promise; confirmed in D-10.',
    confidence: 0.62,
    falsifier: 'If no documented role/title change occurs by 2027-03-15, this prediction is false.',
    calibration_lineage: {
      source_citation: 'Brahma L4 phala.anchors / anchor_career_10L_jupiter',
      technique: 'vimshottari',
      ayanamsha_id: 'lahiri',
    },
  }

  it('a well-formed claim is ledger-ready (no problems)', () => {
    expect(validatePredictionClaim(validClaim)).toEqual([])
    expect(isPredictionClaimLedgerReady(validClaim)).toBe(true)
  })

  it('rejects confidence at the closed bounds — mirrors the ledger CHECK (confidence > 0 AND < 1)', () => {
    expect(validatePredictionClaim({ ...validClaim, confidence: 0 }).length).toBeGreaterThan(0)
    expect(validatePredictionClaim({ ...validClaim, confidence: 1 }).length).toBeGreaterThan(0)
    expect(isPredictionClaimLedgerReady({ ...validClaim, confidence: 1.4 })).toBe(false)
  })

  it('requires a non-empty falsifier (Learning Layer rule #4) and source_citation (B.3)', () => {
    expect(validatePredictionClaim({ ...validClaim, falsifier: '' }).some((m) => m.includes('falsifier'))).toBe(true)
    expect(
      validatePredictionClaim({
        ...validClaim,
        calibration_lineage: { source_citation: '' },
      }).some((m) => m.includes('source_citation')),
    ).toBe(true)
  })

  it('requires an ISO horizon_date and a stated mechanism (plan §8 R-2)', () => {
    expect(validatePredictionClaim({ ...validClaim, horizon_date: 'March 2027' }).some((m) => m.includes('horizon_date'))).toBe(true)
    expect(validatePredictionClaim({ ...validClaim, mechanism: '' }).some((m) => m.includes('mechanism'))).toBe(true)
  })

  it('enforces horizon_date >= applies_window.start (ledger horizon_after_log analogue)', () => {
    const bad = { ...validClaim, applies_window: { start: '2028-01-01', end: null } }
    expect(validatePredictionClaim(bad).some((m) => m.includes('precedes applies_window.start'))).toBe(true)
  })

  it('predictionClaimToLedgerRow maps onto the exact mimamsa_predictions insert column set', () => {
    const row = predictionClaimToLedgerRow(validClaim, '482012f1-710e-4a25-994a-93821f5871aa')
    expect(row).toEqual({
      chart_id: '482012f1-710e-4a25-994a-93821f5871aa',
      domain: 'career',
      prediction_text: validClaim.claim,
      horizon_date: '2027-03-15',
      confidence: 0.62,
      falsifier: validClaim.falsifier,
      source_citation: 'Brahma L4 phala.anchors / anchor_career_10L_jupiter',
    })
    // The additive wire-only fields (mechanism, applies_window) are intentionally NOT ledger columns.
    expect('mechanism' in row).toBe(false)
    expect('applies_window' in row).toBe(false)
  })

  it('carries the prediction on the v3 envelope, null when absent (never fabricated)', () => {
    const withPred = buildRetrievalEnvelope(
      { tool: 'judgment_query', content: {}, prediction: validClaim },
      'v3',
    ) as V3Envelope
    expect(withPred.prediction).toEqual(validClaim)

    const without = buildRetrievalEnvelope({ tool: 'judgment_query', content: {} }, 'v3') as V3Envelope
    expect(without.prediction).toBeNull()
  })
})
