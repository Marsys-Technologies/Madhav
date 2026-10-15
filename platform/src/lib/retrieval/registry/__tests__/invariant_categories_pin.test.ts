/**
 * Pins the PROVISIONAL list of fact categories stored under ayanamsha_id='INVARIANT'.
 * The list is derived from writer code, not from a live read (see the PROVISIONAL note in
 * constants.ts). Changing it must be a deliberate edit of this test, ideally with the result of:
 *   SELECT DISTINCT fact_category FROM chart_facts WHERE ayanamsha_id = 'INVARIANT' ORDER BY 1;
 */
import { describe, it, expect } from 'vitest'
import {
  INVARIANT_AYANAMSHA,
  INVARIANT_BEARING_CAPABILITY_URIS,
  INVARIANT_STORED_FACT_CATEGORIES,
  INVARIANT_STORED_FACT_CATEGORY_PREFIXES,
} from '../constants'

describe('INVARIANT category list (PROVISIONAL, writer-derived, not verified against the database)', () => {
  it('pins the exact category set', () => {
    expect([...INVARIANT_STORED_FACT_CATEGORIES].sort()).toEqual([
      'graha_combustion_state',
      'graha_retrogression_state',
      'graha_shadbala_naisargika',
      'graha_shadbala_total',
      'graha_speed_state',
      'nakshatra_cross_ayanamsha',
    ])
  })

  it('pins the prefix set', () => {
    expect([...INVARIANT_STORED_FACT_CATEGORY_PREFIXES]).toEqual(['panchanga_'])
  })

  it('INVARIANT is a sentinel, not a sixth ayanamsha', () => {
    expect(INVARIANT_AYANAMSHA).toBe('INVARIANT')
  })

  it('no capability is left on the old "do not inject" list: every INVARIANT-bearing handler reads IN ($n,INVARIANT) now', () => {
    expect([...INVARIANT_BEARING_CAPABILITY_URIS]).toEqual([])
  })
})
