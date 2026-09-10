import { describe, expect, it } from 'vitest'
import {
  ANCHOR_MAGNITUDE_ORDER,
  ANOMALY_SEVERITY_ORDER,
  CLEANLINESS_ATTENTION_ORDER,
  OBSTRUCTION_SEVERITY_ORDER,
  WINDOW_STATUS_ACTIONABILITY_ORDER,
  MUHURTA_VERDICT_ORDER,
  salienceRank,
} from '../salience_order'

/** The vocabulary each DB CHECK constraint permits, as membership sets. */
const CHECK_VOCABULARIES: Record<string, readonly string[]> = {
  ANCHOR_MAGNITUDE_ORDER: ['minor', 'moderate', 'major', 'pivotal'],
  ANOMALY_SEVERITY_ORDER: ['critical', 'major', 'minor', 'informational'],
  CLEANLINESS_ATTENTION_ORDER: ['clean', 'flagged', 'staged_revision'],
  WINDOW_STATUS_ACTIONABILITY_ORDER: ['pending', 'open', 'past_window'],
  MUHURTA_VERDICT_ORDER: ['strong', 'adequate', 'mediocre', 'none_genuine'],
}

const ORDERS: Record<string, readonly string[]> = {
  ANCHOR_MAGNITUDE_ORDER,
  ANOMALY_SEVERITY_ORDER,
  CLEANLINESS_ATTENTION_ORDER,
  OBSTRUCTION_SEVERITY_ORDER,
  WINDOW_STATUS_ACTIONABILITY_ORDER,
  MUHURTA_VERDICT_ORDER,
}

describe('L4 salience orderings are total and duplicate-free', () => {
  it.each(Object.keys(ORDERS))('%s has no duplicate', (name) => {
    const order = ORDERS[name]!
    expect(new Set(order).size).toBe(order.length)
  })

  it.each(Object.keys(CHECK_VOCABULARIES))('%s ranks every value its CHECK permits', (name) => {
    // A value the constraint allows but the ranking omits would sort LAST via NULLS LAST --
    // i.e. a newly-added severity would silently become the least salient value there is.
    expect([...ORDERS[name]!].sort()).toEqual([...CHECK_VOCABULARIES[name]!].sort())
  })
})

describe('the orderings encode salience, not the alphabet', () => {
  it('ranks the most consequential anchor magnitude first, unlike a TEXT sort', () => {
    expect(ANCHOR_MAGNITUDE_ORDER[0]).toBe('pivotal')
    expect(ANCHOR_MAGNITUDE_ORDER.indexOf('major')).toBeLessThan(ANCHOR_MAGNITUDE_ORDER.indexOf('minor'))
    // The defect this replaces: `ORDER BY magnitude DESC` sorted major LAST.
    const alphabeticalDesc = [...ANCHOR_MAGNITUDE_ORDER].sort().reverse()
    expect(alphabeticalDesc.indexOf('major')).toBeGreaterThan(alphabeticalDesc.indexOf('minor'))
  })

  it('ranks critical anomalies first, unlike a TEXT sort', () => {
    expect(ANOMALY_SEVERITY_ORDER[0]).toBe('critical')
    const alphabeticalDesc = [...ANOMALY_SEVERITY_ORDER].sort().reverse()
    expect(alphabeticalDesc[alphabeticalDesc.length - 1]).toBe('critical')
  })

  it('ranks the rows needing attention first for cleanliness and obstruction', () => {
    expect(CLEANLINESS_ATTENTION_ORDER[0]).toBe('staged_revision')
    expect(OBSTRUCTION_SEVERITY_ORDER[0]).toBe('high')
  })
})

describe('salienceRank emits a NULL-safe ordering expression', () => {
  it('places the most salient value first and unknown values last', () => {
    const sql = salienceRank('magnitude', ANCHOR_MAGNITUDE_ORDER)
    expect(sql).toBe("array_position(ARRAY['pivotal', 'major', 'moderate', 'minor']::text[], magnitude) NULLS LAST")
  })

  it('escapes a quote in a vocabulary value rather than breaking the statement', () => {
    expect(salienceRank('c', ["it's"])).toContain("'it''s'")
  })
})
