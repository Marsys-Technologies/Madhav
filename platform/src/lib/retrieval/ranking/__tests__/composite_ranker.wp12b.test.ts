/**
 * composite_ranker.wp12b.test.ts — WP-1.2β pure-function unit gate (no DB).
 *
 * Covers the domain-discrimination + attribution primitives added in WP-1.2β:
 *   - extractPrimaryBhava: reads target_house / house / signal_type_id `house_N`.
 *   - bhavaFromFactSubject: HOUSE_N / BHAVA_N in an L1 fact_subject.
 *   - deriveSignalEntity: bhāva-fallback + sade_sati→Saturn attribution (drains UNATTRIBUTED).
 *   - topic-relevance discrimination: a house-2 signal outscores a house-7 signal for wealth
 *     and the reverse for relationship (the wealth∩relationship separation lever).
 *   - buildHierarchicalProfiles: bhāva entities are typed 'bhava' and outrank UNATTRIBUTED.
 */
import { describe, it, expect } from 'vitest'
import {
  extractPrimaryBhava, bhavaFromFactSubject, deriveSignalEntity,
  applyCompositeRanking, buildHierarchicalProfiles,
  type MsrSignalRow, type L1ChartContext,
} from '../composite_ranker'
import { bhavaAffinity } from '../priors_config'

const EMPTY_CTX: L1ChartContext = {
  graha_map: {}, current_md_lord: null, current_ad_lord: null, as_of_date: '2026-07-12',
}

function houseSignal(house: number, id: string): MsrSignalRow {
  return {
    signal_id: id,
    signal_type_id: `aspect_parashari_per_varga:house_${house}`,
    signal_type_class: 'composite_state',
    source_subsystem: 'structural',
    signal_tradition: 'parashari',
    computed_salience: 2.3,
    domains_affected_array: ['career', 'relationship', 'wealth'],
    configuration_jsonb: { varga: 'D1', target_house: house, source_house: 1 },
    constituent_facts_array: [`f_${id}`],
  }
}

describe('WP-1.2β — extractPrimaryBhava', () => {
  it('reads target_house from configuration_jsonb', () => {
    expect(extractPrimaryBhava(houseSignal(2, 'a'))).toBe(2)
  })
  it('falls back to signal_type_id house_N when config has no house', () => {
    expect(extractPrimaryBhava({
      signal_id: 'b', signal_type_id: 'aspect_parashari_per_varga:house_11', configuration_jsonb: null,
    })).toBe(11)
  })
  it('returns null when no house is present', () => {
    expect(extractPrimaryBhava({
      signal_id: 'c', signal_type_id: 'yoga_label:yoga_name', configuration_jsonb: { graha: 'JUPITER' },
    })).toBeNull()
  })
  it('rejects out-of-range houses', () => {
    expect(extractPrimaryBhava({ signal_id: 'd', configuration_jsonb: { target_house: 13 } })).toBeNull()
  })
})

describe('WP-1.2β — bhavaFromFactSubject', () => {
  it('parses HOUSE_7 and D1_HOUSE_10 and BHAVA_2', () => {
    expect(bhavaFromFactSubject('HOUSE_7')).toBe(7)
    expect(bhavaFromFactSubject('D1_HOUSE_10')).toBe(10)
    expect(bhavaFromFactSubject('BHAVA_2')).toBe(2)
  })
  it('returns null for graha subjects', () => {
    expect(bhavaFromFactSubject('D108_SAT')).toBeNull()
  })
})

describe('WP-1.2β — deriveSignalEntity attribution drains UNATTRIBUTED', () => {
  it('attributes a graha-less house signal to its BHAVA_N', () => {
    expect(deriveSignalEntity(houseSignal(5, 'x'))).toBe('BHAVA_5')
  })
  it('attributes a sade_sati signal to SATURN', () => {
    expect(deriveSignalEntity({
      signal_id: 'ss', signal_type_id: 'anumukha_shani_period:saturn_dignity',
      signal_type_class: 'sade_sati', configuration_jsonb: { fact_key: 'saturn_dignity' },
    })).toBe('SATURN')
  })
  it('still prefers a real graha when present', () => {
    expect(deriveSignalEntity({
      signal_id: 'g', configuration_jsonb: { graha: 'VENUS', target_house: 7 },
    })).toBe('VENUS')
  })
  it('uses fact_subject HOUSE_N when config has neither graha nor house', () => {
    const m = new Map<string, string>([['f1', 'HOUSE_9']])
    expect(deriveSignalEntity({
      signal_id: 'fs', signal_type_id: 'x:y', configuration_jsonb: { fact_key: 'k' }, constituent_facts_array: ['f1'],
    }, m)).toBe('BHAVA_9')
  })
  it('only returns UNATTRIBUTED with no graha and no house anywhere', () => {
    expect(deriveSignalEntity({
      signal_id: 'u', signal_type_id: 'panchanga_abhijit_muhurta:duration_minutes',
      signal_type_class: 'panchanga', configuration_jsonb: { fact_key: 'duration_minutes' },
    })).toBe('UNATTRIBUTED')
  })
})

describe('WP-1.2β — bhavaAffinity discriminates wealth vs relationship', () => {
  it('house 2 favours wealth over relationship; house 7 the reverse', () => {
    expect(bhavaAffinity(2, 'wealth')).toBeGreaterThan(bhavaAffinity(2, 'relationship'))
    expect(bhavaAffinity(7, 'relationship')).toBeGreaterThan(bhavaAffinity(7, 'wealth'))
  })
  it('moksha favours the 4-8-12 trikoṇa, not the 9th (dharma)', () => {
    expect(bhavaAffinity(12, 'moksha')).toBeGreaterThan(bhavaAffinity(9, 'moksha'))
    expect(bhavaAffinity(8, 'moksha')).toBeGreaterThan(1.0)
    expect(bhavaAffinity(4, 'moksha')).toBeGreaterThan(1.0)
  })
})

describe('WP-1.2β — composite ranking reorders per domain', () => {
  it('wealth ranks the house-2 signal top; relationship ranks the house-7 signal top', () => {
    const pool: MsrSignalRow[] = [houseSignal(2, 'h2'), houseSignal(7, 'h7'), houseSignal(11, 'h11'), houseSignal(6, 'h6')]
    const wealth = applyCompositeRanking(pool, EMPTY_CTX, 'wealth')
    const rel = applyCompositeRanking(pool, EMPTY_CTX, 'relationship')
    // wealth top is a wealth-primary house (2 or 11); relationship top is house 7.
    expect(['h2', 'h11']).toContain(wealth[0].signal_id)
    expect(rel[0].signal_id).toBe('h7')
    // The two domains do NOT produce the same #1.
    expect(wealth[0].signal_id).not.toBe(rel[0].signal_id)
  })
})

describe('WP-1.2β — buildHierarchicalProfiles types + orders bhāva entities', () => {
  it('bhāva entities are typed bhava and outrank UNATTRIBUTED', () => {
    const pool: MsrSignalRow[] = [
      houseSignal(2, 'a'), houseSignal(2, 'b'), houseSignal(11, 'c'),
      { signal_id: 'un', signal_type_id: 'panchanga_x:y', signal_type_class: 'panchanga', configuration_jsonb: { fact_key: 'y' } },
    ]
    const scored = applyCompositeRanking(pool, EMPTY_CTX, null)
    const profiles = buildHierarchicalProfiles(scored, 10, 3, {})
    const unattr = profiles.find(p => p.entity === 'UNATTRIBUTED')
    const bhava = profiles.find(p => p.entity_type === 'bhava')
    expect(bhava).toBeDefined()
    if (unattr) {
      // UNATTRIBUTED, if present, is last.
      expect(profiles[profiles.length - 1].entity).toBe('UNATTRIBUTED')
    }
  })
})
