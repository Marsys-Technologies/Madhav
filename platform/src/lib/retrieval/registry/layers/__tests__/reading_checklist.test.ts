/**
 * reading_checklist.test.ts — ŚODHANA T5 (PŪRTI) pure-function guards for the served
 * completeness receipt's exhaustiveness disclosure + the domain→KP-cusp map.
 */
import { describe, it, expect } from 'vitest'
import { checklistExhaustiveness, DOMAIN_KP_CUSPS, type ChecklistUnit } from '../reading_checklist'

describe('checklistExhaustiveness (the non_exhaustive self-disclosure)', () => {
  it('an all-served/empty checklist is exhaustive (no salience_sampled disclosure)', () => {
    const units: ChecklistUnit[] = [
      { unit: 'a', state: 'served' },
      { unit: 'b', state: 'empty_for_this_chart' },
    ]
    const r = checklistExhaustiveness(units)
    expect(r.exhaustive).toBe(true)
    expect(r.non_exhaustive).toBe(false)
    expect(r.units_unserved).toEqual([])
  })

  it('any not_joined / not_computed / salience_floored / not_yet_available unit forces non_exhaustive: salience_sampled', () => {
    const units: ChecklistUnit[] = [
      { unit: 'bhava', state: 'served' },
      { unit: 'tajaka', state: 'not_joined' },
      { unit: 'yogi_avayogi', state: 'not_yet_available' },
    ]
    const r = checklistExhaustiveness(units)
    expect(r.exhaustive).toBe(false)
    expect(r.non_exhaustive).toBe('salience_sampled')
    expect(r.units_unserved).toContain('tajaka')
    expect(r.units_unserved).toContain('yogi_avayogi')
    expect(r.units_served).toBe(1)
    expect(r.units_total).toBe(3)
  })
})

describe('DOMAIN_KP_CUSPS (MC-031 wealth/career chain)', () => {
  it('wealth maps to the 2nd + 11th cusps (accumulated wealth + gains)', () => {
    expect(DOMAIN_KP_CUSPS['wealth']).toEqual([2, 11])
  })
  it('career maps to the 10th + 6th cusps (karma + service/competition)', () => {
    expect(DOMAIN_KP_CUSPS['career']).toEqual([10, 6])
  })
})
