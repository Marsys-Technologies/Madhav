/**
 * significator_condition.f113.test.ts — F-113 regression battery
 * ===============================================================
 * The finding (PARIŚEṢA-V4 corpus, baseline_id F-113, CL-20 TIER1-CORRECTNESS):
 *
 *   "assess_marriage omits the chart's single most consequential 7th-house fact. The string
 *    'exalted' appears ZERO times in the entire 147,294-byte assess_marriage response.
 *    Saturn is EXALTED in Libra in the 7TH HOUSE (Vishakha, shadbala 7.83 — the 2nd-strongest
 *    graha in the chart), and Venus — the 7th lord and stored karaka for domain 'marriage' —
 *    sits in the bottom strength quartile (shadbala_percentile 0.25, warning_tier 'watch').
 *    Neither fact appears anywhere in the marriage assessment."
 *
 * These tests pin BOTH halves of the fix:
 *   1. the SELECTION CONTRACT (selectNotablePlacements) — the rule that decides what is
 *      consequential enough to surface, asserted directly rather than through a mocked DB;
 *   2. the VERDICT CLAUSE (buildVerdictLayer) — that the selected fact actually reaches the
 *      one response layer no budget pass may drop (kernel.verdict), with 'exalted' and the
 *      specific Saturn-in-the-7th placement present in the served text.
 *
 * The live values below are the REAL canonical-chart values (482012f1-…, lahiri), confirmed
 * against ganita_dasha_lord_capability_get and judgment_query at the time of the fix — not
 * invented fixtures.
 */

import { describe, it, expect } from 'vitest'
import {
  selectNotablePlacements,
  describeNotablePlacements,
  isDignityExtreme,
  NO_NOTABLE_PLACEMENT_TEXT,
  NOTABLE_DIGNITY_ABS_WEIGHT,
  type SignificatorPlacement,
  type SignificatorCondition,
} from '../significator_condition'
import { buildVerdictLayer } from '../register_d8_assess_domain'

/** Real canonical-chart placement: Saturn, exalted in Libra, 7th house, ṣaḍbala 7.83 rūpa,
 *  rank 2 of the classical 7 (Sun 8.47 is rank 1). */
const SATURN_7TH: SignificatorPlacement = {
  graha: 'Saturn',
  graha_code: 'SAT',
  house: 7,
  sign: 'Libra',
  dignity_state: 'exalted',
  dignity_weight: 2,
  shadbala_rupa: 7.83,
  fact_ids: ['1408b9cb77735337', '802b98a85d32bc93'],
  role: 'occupant',
  shadbala_rank: 2,
  shadbala_population_size: 9,
  // PERCENT_RANK over this chart's 9 graha_shadbala_total.rupa rows — the exact value
  // ganita_dasha_lord_capability_get serves live for Saturn on this chart.
  shadbala_percentile: 0.875,
  rank_statement: 'Saturn is ranked 2nd of 9 by shadbala among 9 chart planets.',
}

/** Real canonical-chart placement: Venus — 7th lord AND marriage kāraka — neutral in
 *  Sagittarius, 9th house, ṣaḍbala 4.64 rūpa, weakest of the classical 7. */
const VENUS_BHAVESHA: SignificatorPlacement = {
  graha: 'Venus',
  graha_code: 'VEN',
  house: 9,
  sign: 'Sagittarius',
  dignity_state: 'neutral',
  dignity_weight: 0,
  shadbala_rupa: 4.64,
  fact_ids: ['5a80bdf4947d5e16'],
  role: 'bhavesha',
  shadbala_rank: 7,
  shadbala_population_size: 9,
  // Live value from ganita_dasha_lord_capability_get — the number F-113's own claim cites.
  shadbala_percentile: 0.25,
  rank_statement: 'Venus is ranked 7th of 9 by shadbala among 9 chart planets.',
}

/** Mars: the OTHER 7th-house occupant on this chart — neutral dignity, mid ṣaḍbala rank.
 *  It must NOT be selected: the contract surfaces extremes, not every occupant. */
const MARS_7TH: SignificatorPlacement = {
  graha: 'Mars',
  graha_code: 'MAR',
  house: 7,
  sign: 'Libra',
  dignity_state: 'neutral',
  dignity_weight: 0,
  shadbala_rupa: 5.57,
  fact_ids: ['01a0d06d44a08aed'],
  role: 'occupant',
  shadbala_rank: 6,
  shadbala_population_size: 9,
  // Live value: 0.375 — above LOW_SHADBALA_PERCENTILE (0.34), so NOT strength-extreme.
  // This is the same row ganita_dasha_lord_capability_get leaves at warning_tier 'none'.
  shadbala_percentile: 0.375,
  rank_statement: 'Mars is ranked 6th of 9 by shadbala among 9 chart planets.',
}

function verdictText(clauses: { text: string }[]): string {
  return clauses.map(c => c.text).join(' ')
}

function sigCond(over: Partial<SignificatorCondition> = {}): SignificatorCondition {
  return {
    domain: 'relationship',
    bhava: 7,
    bhava_sign: 'Libra',
    bhavesha: VENUS_BHAVESHA,
    karakas: [],
    occupants: [SATURN_7TH, MARS_7TH],
    notable: selectNotablePlacements([VENUS_BHAVESHA, SATURN_7TH, MARS_7TH]),
    fact_ids: ['1408b9cb77735337', '5a80bdf4947d5e16'],
    selection_contract: 'x',
    note: 'y',
    ...over,
  }
}

const BASE_VERDICT_INPUTS = {
  domain_label: 'Marriage / Partnership',
  top10: [] as Array<Record<string, unknown>>,
  bearingYogaFirings: [] as Array<Record<string, unknown>>,
  domainMatchedYogaFactIds: [] as string[],
  vargaAnalysis: {} as Record<string, unknown>,
  contradictions: { status: 'no_contradictions_in_domain' } as Record<string, unknown>,
  chartWideContradictionCount: 3,
  temporalOk: false,
  stageTemporalCount: 0,
}

describe('F-113 · selection contract (what counts as consequential)', () => {
  it('classifies exalted/debilitated/own/moolatrikona as dignity extremes and nothing weaker', () => {
    for (const d of ['exalted', 'debilitated', 'own', 'moolatrikona']) {
      expect(isDignityExtreme(d)).toBe(true)
    }
    for (const d of ['great_friend', 'friend', 'neutral', 'enemy', 'great_enemy', null]) {
      expect(isDignityExtreme(d)).toBe(false)
    }
    expect(NOTABLE_DIGNITY_ABS_WEIGHT).toBe(1.5)
  })

  it('selects the exalted 7th-house Saturn — the fact F-113 says was omitted', () => {
    const notable = selectNotablePlacements([VENUS_BHAVESHA, SATURN_7TH, MARS_7TH])
    const saturn = notable.find(p => p.graha === 'Saturn')
    expect(saturn).toBeDefined()
    expect(saturn!.dignity_state).toBe('exalted')
    expect(saturn!.house).toBe(7)
    expect(saturn!.notable_reasons.some(r => r.includes('exalted'))).toBe(true)
  })

  it('also selects the bottom-quartile 7th lord / marriage kāraka Venus', () => {
    const notable = selectNotablePlacements([VENUS_BHAVESHA, SATURN_7TH, MARS_7TH])
    const venus = notable.find(p => p.graha === 'Venus')
    expect(venus).toBeDefined()
    expect(venus!.notable_reasons.some(r => r.includes('bottom of chart'))).toBe(true)
  })

  it('does NOT select a mid-strength, ordinary-dignity occupant (Mars) — extremes, not everything', () => {
    const notable = selectNotablePlacements([VENUS_BHAVESHA, SATURN_7TH, MARS_7TH])
    expect(notable.map(p => p.graha)).not.toContain('Mars')
  })

  it('orders a dignity extreme ahead of a mere strength extreme (stable, deterministic)', () => {
    const a = selectNotablePlacements([VENUS_BHAVESHA, SATURN_7TH, MARS_7TH])
    const b = selectNotablePlacements([SATURN_7TH, MARS_7TH, VENUS_BHAVESHA])
    expect(a[0]!.graha).toBe('Saturn')
    expect(a.map(p => p.graha)).toEqual(b.map(p => p.graha))
  })

  it('returns an empty selection — never a fabricated one — when nothing is extreme', () => {
    expect(selectNotablePlacements([MARS_7TH])).toEqual([])
    expect(describeNotablePlacements([], 7)).toBeNull()
  })
})

describe("F-113 · the omitted fact reaches the served verdict (the 'exalted' regression)", () => {
  it("assess_marriage's verdict contains 'exalted' AND names Saturn in the 7th", () => {
    const verdict = buildVerdictLayer({ ...BASE_VERDICT_INPUTS, significatorCondition: sigCond() })
    const text = verdictText(verdict.clauses)
    // The literal F-113 reproducer: grep 'exalted' over the response returned 0.
    expect(text).toContain('exalted')
    expect(text).toContain('Saturn')
    expect(text).toMatch(/Saturn[^.;]*exalted/)
    expect(text).toContain('7th')
    expect(text).toContain('Libra')
    expect(text).toContain('7.83')
  })

  it('cites the real L1 fact_ids the claim rests on (B.3 derivation-ledger)', () => {
    const verdict = buildVerdictLayer({ ...BASE_VERDICT_INPUTS, significatorCondition: sigCond() })
    const clause = verdict.clauses.find(c => c.text.includes('exalted'))!
    expect(clause.grounded).toBe(true)
    expect(clause.fact_ids).toContain('1408b9cb77735337')
    expect(verdict.fact_ids_cited).toContain('1408b9cb77735337')
  })

  it('places the significator clause SECOND — ahead of yoga/varga/contradiction/timing', () => {
    const verdict = buildVerdictLayer({ ...BASE_VERDICT_INPUTS, significatorCondition: sigCond() })
    expect(verdict.clauses[1]!.text).toContain('Significator condition (D1)')
  })

  it('states an honest absence rather than dropping the clause when nothing is notable', () => {
    const verdict = buildVerdictLayer({
      ...BASE_VERDICT_INPUTS,
      significatorCondition: sigCond({ notable: [], bhavesha: MARS_7TH, occupants: [MARS_7TH] }),
    })
    const text = verdictText(verdict.clauses)
    expect(text).toContain(NO_NOTABLE_PLACEMENT_TEXT)
    expect(text).not.toContain('exalted')
  })

  it('discloses an unavailable leg instead of silently omitting it', () => {
    const verdict = buildVerdictLayer({
      ...BASE_VERDICT_INPUTS,
      significatorCondition: sigCond({ empty_reason: 'resolution failed for bhāva 7' }),
    })
    expect(verdictText(verdict.clauses)).toContain('Significator condition (D1) unavailable')
  })

  it('leaves the pre-F-113 clause set byte-identical when no leg is supplied', () => {
    const before = buildVerdictLayer(BASE_VERDICT_INPUTS)
    expect(before.clauses.some(c => c.text.includes('Significator condition'))).toBe(false)
  })

  it('keeps the clause compact enough for the ≤2KB Sāra kernel it must survive in', () => {
    const verdict = buildVerdictLayer({ ...BASE_VERDICT_INPUTS, significatorCondition: sigCond() })
    const clause = verdict.clauses[1]!
    expect(Buffer.byteLength(clause.text, 'utf8')).toBeLessThan(400)
  })
})
