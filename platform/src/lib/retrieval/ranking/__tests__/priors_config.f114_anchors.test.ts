/**
 * priors_config.f114_anchors.test.ts — PARIŚEṢA F-114 (CL-10).
 * ============================================================
 * `domainAnchorActors` names the grahas and bhāvas a domain's OWN affinity tables already
 * rate above neutral, so a bounded candidate set can be guaranteed to CONTAIN the domain's
 * significators before the composite ranker is asked to rank them. It must stay a pure
 * projection of GRAHA_DOMAIN_AFFINITY + DOMAIN_BHAVA_AFFINITY — the moment it becomes a
 * second hand-maintained list it can disagree with the weights that score it (GA.1 class).
 */
import { describe, it, expect } from 'vitest'
import {
  domainAnchorActors, grahaAffinity, bhavaAffinity, DOMAIN_BHAVA_AFFINITY,
} from '../priors_config'

describe('domainAnchorActors (F-114)', () => {
  it('names the classical marriage significators for the relationship domain', () => {
    const a = domainAnchorActors('relationship')
    // Venus = kalatra-kāraka (affinity 1.50) — the graha F-114 says the marriage lens never named.
    expect(a.grahas).toContain('venus')
    // 7 = kalatra-bhāva (2.20) — the house F-114 says the marriage lens never named.
    expect(a.houses).toContain(7)
    expect(a.houses).toEqual([...a.houses].sort((x, y) => x - y))
    // Saturn is NOT an anchor for relationship (0.90, below neutral) — the exact graha whose
    // ga_sensitive rows monopolised the degenerate top-10.
    expect(a.grahas).not.toContain('saturn')
    // The DB's own spellings are covered so a SQL predicate needs no second alias list.
    for (const alias of ['ven', 'venus', 've']) expect(a.graha_aliases).toContain(alias)
    expect(a.graha_aliases).not.toContain('sat')
  })

  it('is a pure projection of the two affinity tables (no independent list to drift)', () => {
    for (const domain of Object.keys(DOMAIN_BHAVA_AFFINITY)) {
      const a = domainAnchorActors(domain)
      // Every anchor graha is rated strictly above neutral for that domain…
      for (const g of a.grahas) expect(grahaAffinity(g, domain)).toBeGreaterThan(1.0)
      // …and every anchor bhāva likewise.
      for (const h of a.houses) expect(bhavaAffinity(h, domain)).toBeGreaterThan(1.0)
      // …and nothing above neutral is missing from the anchor set.
      const bhavaRow = DOMAIN_BHAVA_AFFINITY[domain]!
      const expectedHouses = Object.entries(bhavaRow)
        .filter(([, w]) => w > 1.0).map(([h]) => Number(h)).sort((x, y) => x - y)
      expect(a.houses).toEqual(expectedHouses)
    }
  })

  it('keeps domains genuinely distinct (a wealth anchor set is not a marriage anchor set)', () => {
    const rel = domainAnchorActors('relationship')
    const wealth = domainAnchorActors('wealth')
    const career = domainAnchorActors('career')
    // 7 (kalatra) belongs to relationship, not to wealth's 2/11 dhana-lābha set.
    expect(rel.houses).toContain(7)
    expect(wealth.houses).not.toContain(7)
    // 10 (karma) belongs to career, not to relationship.
    expect(career.houses).toContain(10)
    expect(rel.houses).not.toContain(10)
  })

  it('returns an empty, harmless set for an unknown or absent domain', () => {
    expect(domainAnchorActors(null)).toEqual({ grahas: [], graha_aliases: [], houses: [] })
    const unknown = domainAnchorActors('not_a_domain')
    expect(unknown.houses).toEqual([])
    expect(unknown.grahas).toEqual([])
  })
})
