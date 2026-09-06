/**
 * register_d9_judgment.f_kala_1_activation_rank.test.ts — F-KALA-1
 * (L3_W1_ANALYSIS_BATCH_E.md, ka_kalasutra finding 1).
 *
 * THE DEFECT: judgment_query's `kala_activations` timing hook deduped/ranked
 * `kala_activation` rows by `convergence_score` (`?? -Infinity` / `?? 0`). That column is
 * 99.6% NULL (measured) — `ka_sangam` only ever produces windows for ≤260 of ~50,104
 * activation predicates. Once every candidate falls back to the same default, `curConv >
 * prevConv` is never true and the final sort's tiebreak silently decides everything, so
 * "best row per window" and "top 6 overall" were both effectively arbitrary for 99.6% of
 * rows — the product's headline verdict tool picking a "best" activation that isn't really
 * ranked by anything.
 *
 * THE FIX: rank by `dasha_activation_proximity_score` (0% NULL, [0,1], higher = stronger)
 * first, `convergence_score` then `orb_strength` as secondary tiebreaks (real signal for the
 * small fraction of rows ka_sangam does cover), `id` string-compare as the final total-order
 * tiebreak (§N.7 item 2).
 *
 * Pure module-level function tests — no DB required.
 */
import { describe, it, expect } from 'vitest'
import { compareKalaActivationRank, pickTopKalaActivations } from '../register_d9_judgment'

function row(overrides: Record<string, unknown>): Record<string, unknown> {
  return {
    id: 'id-default',
    signal_id: 'sig-default',
    signature_class: 'YOGA',
    activation_start: '2026-01-01',
    activation_peak_date: '2026-01-05',
    activation_end: '2026-01-10',
    convergence_score: null,
    dasha_activation_proximity_score: null,
    orb_strength: null,
    domains_affected_array: [],
    source_citation: 'src',
    ...overrides,
  }
}

describe('compareKalaActivationRank', () => {
  it('ranks by dasha_activation_proximity_score first (higher wins) when convergence_score/orb_strength are both NULL', () => {
    const strong = row({ id: 'a', dasha_activation_proximity_score: 0.8 })
    const weak = row({ id: 'b', dasha_activation_proximity_score: 0.2 })
    expect(compareKalaActivationRank(strong, weak)).toBeLessThan(0)
    expect(compareKalaActivationRank(weak, strong)).toBeGreaterThan(0)
  })

  it('falls back to convergence_score as a secondary tiebreak when proximity ties', () => {
    const higherConv = row({ id: 'a', dasha_activation_proximity_score: 0.5, convergence_score: 0.9 })
    const lowerConv = row({ id: 'b', dasha_activation_proximity_score: 0.5, convergence_score: 0.1 })
    expect(compareKalaActivationRank(higherConv, lowerConv)).toBeLessThan(0)
  })

  it('falls back to orb_strength as a tertiary tiebreak when proximity AND convergence tie', () => {
    const higherOrb = row({ id: 'a', dasha_activation_proximity_score: 0.5, convergence_score: 0.5, orb_strength: 0.9 })
    const lowerOrb = row({ id: 'b', dasha_activation_proximity_score: 0.5, convergence_score: 0.5, orb_strength: 0.1 })
    expect(compareKalaActivationRank(higherOrb, lowerOrb)).toBeLessThan(0)
  })

  it('falls back to id string-compare as the final total-order tiebreak when everything else ties', () => {
    const a = row({ id: 'aaa', dasha_activation_proximity_score: 0.5 })
    const b = row({ id: 'bbb', dasha_activation_proximity_score: 0.5 })
    expect(compareKalaActivationRank(a, b)).toBeLessThan(0)
    expect(compareKalaActivationRank(b, a)).toBeGreaterThan(0)
  })

  it('treats a NULL/undefined proximity score as -Infinity, never as a favorable default (§N.7 item 6)', () => {
    const withScore = row({ id: 'a', dasha_activation_proximity_score: 0.01 })
    const withoutScore = row({ id: 'b', dasha_activation_proximity_score: null })
    expect(compareKalaActivationRank(withScore, withoutScore)).toBeLessThan(0)
  })
})

describe('pickTopKalaActivations — the regression this replaces', () => {
  it('the 99.6%-NULL scenario: with proximity scores present, ranking is no longer arbitrary', () => {
    // All rows share NULL convergence_score/orb_strength (the measured 99.6% case) but
    // carry distinct, real dasha_activation_proximity_score values (0% NULL, measured) —
    // the fix must rank on THOSE, not silently degrade to id-only ordering.
    const rows = [
      row({ id: 'low', signature_class: 'YOGA', activation_start: 'w1', dasha_activation_proximity_score: 0.2 }),
      row({ id: 'high', signature_class: 'DOSHA', activation_start: 'w2', dasha_activation_proximity_score: 0.95 }),
      row({ id: 'mid', signature_class: 'DIGNITY', activation_start: 'w3', dasha_activation_proximity_score: 0.5 }),
    ]
    const top = pickTopKalaActivations(rows, 6)
    expect(top.map((r) => r['id'])).toEqual(['high', 'mid', 'low'])
  })

  it('dedupes by distinct window (start|peak|end|signature_class), keeping the higher-ranked row per window', () => {
    const sameWindow = { activation_start: 'w1', activation_peak_date: 'p1', activation_end: 'e1', signature_class: 'YOGA' }
    const rows = [
      row({ id: 'weaker', ...sameWindow, dasha_activation_proximity_score: 0.3 }),
      row({ id: 'stronger', ...sameWindow, dasha_activation_proximity_score: 0.9 }),
    ]
    const top = pickTopKalaActivations(rows, 6)
    expect(top).toHaveLength(1)
    expect(top[0]?.['id']).toBe('stronger')
  })

  it('distinct windows are never deduped against each other', () => {
    const rows = [
      row({ id: 'a', activation_start: 'w1', dasha_activation_proximity_score: 0.5 }),
      row({ id: 'b', activation_start: 'w2', dasha_activation_proximity_score: 0.5 }),
    ]
    const top = pickTopKalaActivations(rows, 6)
    expect(top).toHaveLength(2)
  })

  it('caps at the given limit after ranking (top 6 of the batch\'s named default)', () => {
    const rows = Array.from({ length: 10 }, (_, i) =>
      row({ id: `r${i}`, activation_start: `w${i}`, dasha_activation_proximity_score: i / 10 }))
    const top = pickTopKalaActivations(rows, 6)
    expect(top).toHaveLength(6)
    // Highest proximity scores (r9..r4) survive the cap.
    expect(top.map((r) => r['id'])).toEqual(['r9', 'r8', 'r7', 'r6', 'r5', 'r4'])
  })

  it('the compact row shape drops the verbose jsonb fields the caller already excludes (§N.6 budget)', () => {
    const rows = [row({ id: 'a', activation_predicted_dates_jsonb: [{ huge: 'blob' }], active_dasha_periods_jsonb: [{ huge: 'blob' }] })]
    const top = pickTopKalaActivations(rows, 6)
    expect(top[0]).not.toHaveProperty('activation_predicted_dates_jsonb')
    expect(top[0]).not.toHaveProperty('active_dasha_periods_jsonb')
  })

  it('returns [] for an empty input, never throws', () => {
    expect(pickTopKalaActivations([], 6)).toEqual([])
  })
})
