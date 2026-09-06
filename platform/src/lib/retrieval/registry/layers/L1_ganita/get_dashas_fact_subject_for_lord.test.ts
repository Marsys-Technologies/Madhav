/**
 * get_dashas_fact_subject_for_lord.test.ts — F-A11 (L1_W1_ANALYSIS_BATCH_A.md), MUST.
 *
 * `factSubjectForLord` was fixed (R-43) to resolve yogini deity lord names (Mangala/Pingala/…)
 * to their underlying graha's fact_subject code, so the serve-side natal re-derivation in
 * get_dashas.ts stops overwriting the writer's correctly-populated `lord_natal_*` columns with
 * NULL for yogini's 83,740 rows. The function was exported "for unit testing (no DB access
 * required)" but never had one — per §N.8 (a fix claimed without a detector is null, not
 * green), this pins it directly against ga_dashas_writer.py's own YOGINI_SEQUENCE mapping so a
 * future edit to either side can't silently drift out of sync again.
 */
import { describe, it, expect } from 'vitest'
import { factSubjectForLord } from './get_dashas'

// Mirrors ga_dashas_writer.py's YOGINI_SEQUENCE (name, graha, order) — kept in sync by
// inspection on both sides, per the R-43 comment in get_dashas.ts.
const YOGINI_DEITY_TO_GRAHA_NAME: Record<string, string> = {
  Mangala: 'Moon', Pingala: 'Sun', Dhanya: 'Jupiter', Bhramari: 'Mars',
  Bhadrika: 'Mercury', Ulka: 'Saturn', Siddha: 'Venus', Sankata: 'Rahu',
}

describe('factSubjectForLord (F-A11 resolver)', () => {
  for (const [deity, graha] of Object.entries(YOGINI_DEITY_TO_GRAHA_NAME)) {
    it(`resolves yogini deity "${deity}" to the same fact_subject as classical graha "${graha}"`, () => {
      expect(factSubjectForLord(deity)).toBe(factSubjectForLord(graha))
      expect(factSubjectForLord(deity)).toBeDefined()
    })
  }

  const CLASSICAL_GRAHAS = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']
  for (const graha of CLASSICAL_GRAHAS) {
    it(`resolves classical graha "${graha}" to a defined fact_subject (non-yogini systems unaffected)`, () => {
      expect(factSubjectForLord(graha)).toBeDefined()
    })
  }

  it('all 9 classical grahas resolve to 9 DISTINCT fact_subject codes', () => {
    const codes = CLASSICAL_GRAHAS.map(g => factSubjectForLord(g))
    expect(new Set(codes).size).toBe(9)
  })

  it('an unrecognized lord name resolves to undefined (honest gap, not a silent guess)', () => {
    expect(factSubjectForLord('NotARealLord')).toBeUndefined()
    expect(factSubjectForLord('')).toBeUndefined()
  })

  it('undefined input resolves to undefined', () => {
    expect(factSubjectForLord(undefined)).toBeUndefined()
  })
})
