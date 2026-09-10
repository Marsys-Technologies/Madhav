/**
 * kala_ritual_resonance.m8_no_false_emptiness.test.ts — NIRMĀṆA L3-W3, finding M8.
 * ==========================================================================
 * REGRESSION GUARD for a §N.8 defect: `TEMPORAL_INTENSITY_UNAVAILABLE_REASON` asserted
 * "field empty — ka_kshetra has written no rows" as the cause of a not_computed factor.
 *
 * The claim was FALSE — measured live at the time of the fix, `kala_field_windows` held
 * **31,350 rows for the canonical chart** and 7,650 for the second — and, worse, it was
 * *unfalsifiable*: `scoreTemporalIntensity()` takes no arguments, so no execution path
 * consults the field. A reason that no code path could ever contradict is precisely the
 * defect class §N.8 names, and §N.7 item 6's "an honest null beats an invented judgment"
 * applies to the *justification* as much as to the value.
 *
 * The verdict itself (`not_computed`, factor dropped and the product renormalised) was and
 * remains correct. Only the stated cause was wrong. The true blocker is one layer over:
 * no registry capability exists over any `kala_field*` table, so λ is unreachable from the
 * serving plane whether or not the field is populated.
 *
 * This test fails against the pre-fix string.
 */
import { describe, it, expect } from 'vitest'
import {
  TEMPORAL_INTENSITY_UNAVAILABLE_REASON,
  scoreTemporalIntensity,
} from './kala_ritual_resonance'

describe('M8 — the temporal-intensity reason states a true cause (§N.8)', () => {
  it('does not claim ka_kshetra has written no rows', () => {
    // The specific false empirical assertion, in the forms it appeared in.
    expect(TEMPORAL_INTENSITY_UNAVAILABLE_REASON).not.toMatch(/written no rows/i)
    expect(TEMPORAL_INTENSITY_UNAVAILABLE_REASON).not.toMatch(/field empty/i)
  })

  it('names the real blocker — the missing serving path — rather than a data absence', () => {
    expect(TEMPORAL_INTENSITY_UNAVAILABLE_REASON).toMatch(/no registry capability exists/i)
    expect(TEMPORAL_INTENSITY_UNAVAILABLE_REASON).toMatch(/kala_field\*/)
  })

  it('still refuses to invent a value — the verdict was never the defect', () => {
    const factor = scoreTemporalIntensity()
    expect(factor.value).toBeNull()
    expect(factor.state).toBe('not_computed')
    // The prohibition on substitution must survive the rewording.
    expect(TEMPORAL_INTENSITY_UNAVAILABLE_REASON).toMatch(/invented intensity/i)
    expect(TEMPORAL_INTENSITY_UNAVAILABLE_REASON).toMatch(/never zero-filled/i)
  })
})
