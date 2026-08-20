import { describe, expect, it } from 'vitest'

import { CORPUS_FIXTURES } from '../../fixtures'
import { QUERY_CLASSES } from '../../types'
import {
  QUERY_CLASS_WORK_CLASS_MAP,
  WORK_CLASSES,
  getFixturesForWorkClass,
  getWorkClassForQueryClass,
} from '../work_classes'

describe('QUERY_CLASS_WORK_CLASS_MAP', () => {
  it('declares exactly one mapping entry per one of the 12 G3-F query classes', () => {
    expect(QUERY_CLASS_WORK_CLASS_MAP).toHaveLength(QUERY_CLASSES.length)
    const mappedClasses = QUERY_CLASS_WORK_CLASS_MAP.map((m) => m.queryClass).sort()
    expect(mappedClasses).toEqual([...QUERY_CLASSES].sort())
  })

  it('every mapping entry is either one of the 4 named work classes or explicitly null with a stated reason', () => {
    for (const mapping of QUERY_CLASS_WORK_CLASS_MAP) {
      expect(mapping.reason.length).toBeGreaterThan(20)
      if (mapping.workClass !== null) {
        expect(WORK_CLASSES).toContain(mapping.workClass)
      }
    }
  })

  it('maps the two obvious cases directly (factual→factual, sensitive→sensitive)', () => {
    expect(getWorkClassForQueryClass('factual')).toBe('factual')
    expect(getWorkClassForQueryClass('sensitive')).toBe('sensitive')
  })

  it('maps prediction_capture_outcome and timing to predictive', () => {
    expect(getWorkClassForQueryClass('prediction_capture_outcome')).toBe('predictive')
    expect(getWorkClassForQueryClass('timing')).toBe('predictive')
  })

  it('excludes ambiguous_clarification and door_parity from every work class, with a reason', () => {
    expect(getWorkClassForQueryClass('ambiguous_clarification')).toBeNull()
    expect(getWorkClassForQueryClass('door_parity')).toBeNull()
    const ambiguous = QUERY_CLASS_WORK_CLASS_MAP.find((m) => m.queryClass === 'ambiguous_clarification')!
    const doorParity = QUERY_CLASS_WORK_CLASS_MAP.find((m) => m.queryClass === 'door_parity')!
    expect(ambiguous.reason).toMatch(/scope|clarif/i)
    expect(doorParity.reason).toMatch(/parity|infrastructure/i)
  })

  it('throws for an unmapped/unknown query class rather than silently returning a default', () => {
    // @ts-expect-error deliberately passing an invalid query class to prove the guard
    expect(() => getWorkClassForQueryClass('not_a_real_class')).toThrow(/no work-class mapping/)
  })
})

describe('getFixturesForWorkClass', () => {
  it('never returns a fixture from an excluded query class', () => {
    for (const workClass of WORK_CLASSES) {
      const fixtures = getFixturesForWorkClass(workClass)
      for (const f of fixtures) {
        expect(['ambiguous_clarification', 'door_parity']).not.toContain(f.queryClass)
      }
    }
  })

  it('partitions all non-excluded fixtures across the 4 work classes with no overlap and no loss', () => {
    const seen = new Set<string>()
    let total = 0
    for (const workClass of WORK_CLASSES) {
      const fixtures = getFixturesForWorkClass(workClass)
      for (const f of fixtures) {
        expect(seen.has(f.fixtureId)).toBe(false)
        seen.add(f.fixtureId)
        total += 1
      }
    }
    const excludedCount = CORPUS_FIXTURES.filter((f) => getWorkClassForQueryClass(f.queryClass) === null).length
    expect(total).toBe(CORPUS_FIXTURES.length - excludedCount)
    expect(excludedCount).toBe(2) // ambiguous_clarification + door_parity
  })

  it('factual work class contains exactly the factual-001 fixture', () => {
    const fixtures = getFixturesForWorkClass('factual')
    expect(fixtures.map((f) => f.fixtureId)).toEqual(['factual-001-moon-nakshatra-lagna'])
  })

  it('sensitive work class contains exactly the sensitive-001 fixture', () => {
    const fixtures = getFixturesForWorkClass('sensitive')
    expect(fixtures.map((f) => f.fixtureId)).toEqual(['sensitive-001-ayurdaya-longevity'])
  })

  it('predictive work class contains exactly the timing and outcome fixtures', () => {
    const fixtures = getFixturesForWorkClass('predictive')
    expect(fixtures.map((f) => f.fixtureId).sort()).toEqual(
      ['timing-001-mercury-md-saturn-ad', 'outcome-001-saturn-ad-2026-authority-transition'].sort(),
    )
  })

  it('interpretive work class contains the remaining 6 fixtures', () => {
    const fixtures = getFixturesForWorkClass('interpretive')
    expect(fixtures).toHaveLength(6)
    expect(fixtures.map((f) => f.queryClass).sort()).toEqual(
      [
        'interpretive_whole_chart',
        'cross_domain_contradiction',
        'remedial',
        'incomplete_evidence',
        'returning_conversation_drift',
        'disagreement',
      ].sort(),
    )
  })
})
