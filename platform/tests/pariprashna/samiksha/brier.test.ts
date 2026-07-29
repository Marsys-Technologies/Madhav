/**
 * SAMĪKṢĀ Brier-eligibility predicate — PB-3 lane L-3 (pure unit, no DB).
 *
 * The can't-tell → unverifiable → Brier-EXCLUDED guarantee at the query/read layer. These are
 * demonstrate-can-fail assertions: a `happened` row IS eligible (so the predicate isn't
 * blanket-excluding), an `unverifiable` row is NOT (the exclusion is real), and a not-yet-
 * resolved row is neither eligible nor "excluded" (it is simply unresolved).
 */
import { describe, it, expect } from 'vitest'
import {
  isBrierEligible,
  isBrierExcluded,
  partitionForBrier,
  BRIER_ELIGIBLE_SQL,
  BRIER_SCORABLE_OUTCOMES,
  BRIER_EXCLUDED_OUTCOME,
} from '@/lib/pariprashna/samiksha/brier'

describe('Brier eligibility (can’t-tell exclusion)', () => {
  it('a scorable, valued outcome IS eligible (not blanket-excluding)', () => {
    expect(isBrierEligible({ outcome: 'happened', outcome_value: 1 })).toBe(true)
    expect(isBrierEligible({ outcome: 'did_not_happen', outcome_value: 0 })).toBe(true)
    expect(isBrierEligible({ outcome: 'partial', outcome_value: 0.5 })).toBe(true)
  })

  it('an unverifiable outcome is Brier-EXCLUDED and never eligible', () => {
    const row = { outcome: 'unverifiable' as const, outcome_value: null }
    expect(isBrierEligible(row)).toBe(false)
    expect(isBrierExcluded(row)).toBe(true)
  })

  it('a not-yet-resolved row is neither eligible nor "excluded" (just unresolved)', () => {
    const row = { outcome: null, outcome_value: null }
    expect(isBrierEligible(row)).toBe(false)
    expect(isBrierExcluded(row)).toBe(false)
  })

  it('a scorable outcome with a null value is not eligible (value required)', () => {
    expect(isBrierEligible({ outcome: 'happened', outcome_value: null })).toBe(false)
  })

  it('partitionForBrier splits eligible vs excluded, counting can’t-tell separately', () => {
    const rows = [
      { outcome: 'happened' as const, outcome_value: 1 },
      { outcome: 'unverifiable' as const, outcome_value: null },
      { outcome: 'partial' as const, outcome_value: 0.5 },
      { outcome: 'unverifiable' as const, outcome_value: null },
      { outcome: null, outcome_value: null },
    ]
    const { eligible, excluded } = partitionForBrier(rows)
    expect(eligible).toHaveLength(2)
    expect(excluded).toHaveLength(2) // the two can’t-tells, counted separately (honesty metric)
  })

  it('the SQL predicate twin excludes unverifiable by construction', () => {
    expect(BRIER_ELIGIBLE_SQL).toContain("outcome IN ('happened','did_not_happen','partial')")
    expect(BRIER_ELIGIBLE_SQL).toContain('outcome_value IS NOT NULL')
    expect(BRIER_ELIGIBLE_SQL).not.toContain('unverifiable')
    expect(BRIER_SCORABLE_OUTCOMES).not.toContain(BRIER_EXCLUDED_OUTCOME)
  })
})
