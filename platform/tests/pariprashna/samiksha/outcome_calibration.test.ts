/**
 * SAMĪKṢĀ outcome calibration — PURE unit tests — PB-3 lane L-5.
 *
 * Exercises the SHIPPED functions (outcome_calibration.ts), not a test-local reimplementation
 * (the PB-2 false-confidence lesson). No DB; the Brier arithmetic + numrange parsing + intent
 * assembly are all pure. The real-DB round-trip lives in the integration test.
 */

import { describe, it, expect } from 'vitest'
import {
  computeBrier,
  outcomeToValue,
  confidencePoint,
  parseNumrangeLiteral,
  buildCalibrationIntent,
  DEFAULT_PARTIAL_VALUE,
  type BrierResult,
} from '@/lib/pariprashna/samiksha/outcome_calibration'
import type { LedgerRow } from '@/lib/pariprashna/samiksha/schema'

describe('outcomeToValue', () => {
  it('maps happened→1, did_not_happen→0, partial→0.5 (default), unverifiable→null', () => {
    expect(outcomeToValue('happened')).toBe(1.0)
    expect(outcomeToValue('did_not_happen')).toBe(0.0)
    expect(outcomeToValue('partial')).toBe(DEFAULT_PARTIAL_VALUE)
    expect(outcomeToValue('unverifiable')).toBeNull()
  })
  it('honors an explicit partial value override', () => {
    expect(outcomeToValue('partial', 0.3)).toBe(0.3)
  })
})

describe('parseNumrangeLiteral', () => {
  it('parses inclusive/exclusive bracket forms to {low,high}', () => {
    expect(parseNumrangeLiteral('[0.55,0.7)')).toEqual({ low: 0.55, high: 0.7 })
    expect(parseNumrangeLiteral('(0.5,0.8]')).toEqual({ low: 0.5, high: 0.8 })
    expect(parseNumrangeLiteral('[0.6,0.8)')).toEqual({ low: 0.6, high: 0.8 })
  })
  it('returns null for empty / absent / unbounded-side ranges (honest null, no fabricated default)', () => {
    expect(parseNumrangeLiteral(null)).toBeNull()
    expect(parseNumrangeLiteral(undefined)).toBeNull()
    expect(parseNumrangeLiteral('')).toBeNull()
    expect(parseNumrangeLiteral('empty')).toBeNull()
    expect(parseNumrangeLiteral('[,0.5)')).toBeNull() // unbounded lower
    expect(parseNumrangeLiteral('[0.5,)')).toBeNull() // unbounded upper
    expect(parseNumrangeLiteral('garbage')).toBeNull()
  })
})

describe('confidencePoint', () => {
  it('is the band midpoint, clamped to [0,1]', () => {
    expect(confidencePoint({ low: 0.55, high: 0.7 })).toBeCloseTo(0.625, 10)
    expect(confidencePoint({ low: 0.5, high: 0.5 })).toBe(0.5)
    expect(confidencePoint(null)).toBeNull()
  })
})

describe('computeBrier — (confidence − outcome)²', () => {
  const cases: Array<[string, { low: number; high: number } | null, Parameters<typeof computeBrier>[1], number | null]> = [
    ['perfect confident hit', { low: 1, high: 1 }, 'happened', 0],
    ['perfect confident correct-negative', { low: 0, high: 0 }, 'did_not_happen', 0],
    ['maximally wrong (sure it happens, it did not)', { low: 1, high: 1 }, 'did_not_happen', 1],
    ['maximally wrong (sure it does not, it did)', { low: 0, high: 0 }, 'happened', 1],
    ['coin-flip confidence, happened', { low: 0.5, high: 0.5 }, 'happened', 0.25],
    ['coin-flip confidence, did not', { low: 0.5, high: 0.5 }, 'did_not_happen', 0.25],
    ['band midpoint 0.625, happened', { low: 0.55, high: 0.7 }, 'happened', (1 - 0.625) ** 2],
    ['no confidence band → null brier', null, 'happened', null],
  ]
  it.each(cases)('%s', (_label, band, outcome, expected) => {
    const r = computeBrier(band, outcome)
    if (expected === null) expect(r.brier).toBeNull()
    else expect(r.brier).toBeCloseTo(expected as number, 12)
  })

  it('unverifiable is Brier-EXCLUDED: outcome_value null AND brier null', () => {
    const r = computeBrier({ low: 0.6, high: 0.8 }, 'unverifiable')
    expect(r.outcome_value).toBeNull()
    expect(r.brier).toBeNull()
  })

  it('partial uses the override value in the Brier', () => {
    const r = computeBrier({ low: 0.6, high: 0.6 }, 'partial', 0.3)
    expect(r.outcome_value).toBe(0.3)
    expect(r.brier).toBeCloseTo((0.6 - 0.3) ** 2, 12) // 0.09
  })

  it('every non-excluded Brier lands in [0,1]', () => {
    for (const p of [0, 0.1, 0.5, 0.9, 1]) {
      for (const o of ['happened', 'did_not_happen'] as const) {
        const r = computeBrier({ low: p, high: p }, o)
        expect(r.brier).toBeGreaterThanOrEqual(0)
        expect(r.brier).toBeLessThanOrEqual(1)
      }
    }
  })
})

describe('buildCalibrationIntent — the ledger IS the citation (§14.5)', () => {
  const baseRow: Pick<LedgerRow, 'id' | 'chart_id' | 'domain' | 'outcome' | 'technique_refs' | 'grounding_fact_ids'> = {
    id: '9f1b2c3d-0000-0000-0000-000000000abc',
    chart_id: '482012f1-710e-4a25-994a-93821f5871aa',
    domain: 'career',
    outcome: 'happened',
    technique_refs: ['vimshottari_dasha'],
    grounding_fact_ids: ['PLN.SAT', 'HSE.10'],
  }

  it('sets source_citation === the ledger row id (not mimamsa_predictions, not phala_anchors)', () => {
    const brier: BrierResult = { confidence_point: 0.625, outcome_value: 1, brier: 0.140625 }
    const intent = buildCalibrationIntent(baseRow, brier, '2026-07-28T00:00:00.000Z')
    expect(intent.source_citation).toBe(baseRow.id)
    expect(intent.prediction_ledger_row_id).toBe(baseRow.id)
    expect(intent.chart_id).toBe(baseRow.chart_id)
    expect(intent.brier).toBe(0.140625)
    expect(intent.brier_excluded).toBe(false)
    expect(intent.scored_at).toBe('2026-07-28T00:00:00.000Z')
  })

  it('marks brier_excluded when the Brier is null (unverifiable)', () => {
    const brier: BrierResult = { confidence_point: 0.7, outcome_value: null, brier: null }
    const intent = buildCalibrationIntent({ ...baseRow, outcome: 'unverifiable' }, brier)
    expect(intent.brier).toBeNull()
    expect(intent.brier_excluded).toBe(true)
  })
})
