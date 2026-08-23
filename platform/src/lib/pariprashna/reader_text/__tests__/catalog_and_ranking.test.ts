/**
 * catalog_and_ranking.test.ts — lane P4-J.
 *
 * Confirms the reader-facing catalog loads correctly on top of the existing,
 * tested `parseMsrSignals` (no re-parsing bug reintroduced — see catalog.ts's
 * header comment on why an earlier draft of this lane's OWN parser silently
 * dropped 4 blocks), and that the citation ranking is deterministic and
 * matches the real, manually-verified top signals.
 */
import { describe, expect, it } from 'vitest'

import { loadFullMsrCatalog, loadReaderFacingCatalog, isMetaStatisticsEntry } from '../catalog'
import {
  buildCitationFrequencyMap,
  normalizeEntityCode,
  rankMsrSignals,
  splitCompoundRef,
} from '../citation_ranking'

describe('catalog', () => {
  it('loads all 573 catalog signals via the existing, tested parser', () => {
    expect(loadFullMsrCatalog()).toHaveLength(573)
  })

  it('excludes exactly the 5 known internal meta-statistics entries from the reader-facing pool', () => {
    const full = loadFullMsrCatalog()
    const readerFacing = loadReaderFacingCatalog()
    const excluded = full.filter((s) => isMetaStatisticsEntry(s))
    expect(excluded.map((s) => s.signal_id).sort()).toEqual([
      'SIG.MSR.416',
      'SIG.MSR.417',
      'SIG.MSR.418',
      'SIG.MSR.419',
      'SIG.MSR.420',
    ])
    expect(readerFacing).toHaveLength(full.length - 5)
  })
})

describe('citation_ranking — normalization', () => {
  it('splits a compound comma-joined ref into individual entity codes', () => {
    expect(splitCompoundRef('YGA.BUDH_ADITYA, HSE.10')).toEqual(['YGA.BUDH_ADITYA', 'HSE.10'])
    expect(splitCompoundRef('PLN.SATURN')).toEqual(['PLN.SATURN'])
  })

  it('aliases the live YGA. citation namespace onto MSR\'s own YOG. entity namespace', () => {
    expect(normalizeEntityCode('YGA.SASHA_MPY')).toBe('YOG.SASHA_MPY')
    expect(normalizeEntityCode('PLN.SATURN')).toBe('PLN.SATURN') // unaffected
  })

  it('builds a frequency map that sums compound-ref counts per normalized entity', () => {
    const freq = buildCitationFrequencyMap([
      { ref: 'YGA.FOO, HSE.10', cite_count: 2 },
      { ref: 'YGA.FOO', cite_count: 3 },
    ])
    expect(freq.get('YOG.FOO')).toBe(5)
    expect(freq.get('HSE.10')).toBe(2)
  })
})

describe('citation_ranking — rankMsrSignals against the real catalog + real snapshot', () => {
  const ranked = rankMsrSignals(loadReaderFacingCatalog())

  it('produces a fully deterministic, descending-weight order', () => {
    for (let i = 1; i < ranked.length; i++) {
      expect(ranked[i - 1].citation_weight).toBeGreaterThanOrEqual(ranked[i].citation_weight)
    }
  })

  it('ranks SIG.MSR.198 (Tara Bala, 8 planets each individually cited) at #1, tie-broken over SIG.MSR.500', () => {
    // Both carry citation_weight 28 (verified by hand against the real snapshot,
    // see citation_ranking.ts header comment); "SIG.MSR.198" < "SIG.MSR.500"
    // lexicographically, so 198 must win the tie-break deterministically.
    expect(ranked[0].signal.signal_id).toBe('SIG.MSR.198')
    expect(ranked[0].citation_weight).toBe(28)
    expect(ranked[1].signal.signal_id).toBe('SIG.MSR.500')
    expect(ranked[1].citation_weight).toBe(28)
  })

  it('sorts every zero-weight (uncited) signal after every nonzero-weight one', () => {
    const firstZeroIdx = ranked.findIndex((r) => r.citation_weight === 0)
    expect(firstZeroIdx).toBeGreaterThan(0)
    for (let i = firstZeroIdx; i < ranked.length; i++) {
      expect(ranked[i].citation_weight).toBe(0)
    }
  })
})
