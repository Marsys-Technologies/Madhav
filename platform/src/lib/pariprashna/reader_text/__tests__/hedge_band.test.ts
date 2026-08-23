/**
 * hedge_band.test.ts — lane P4-J, §N.8 red-then-green proof for the hedge-band
 * gate (`hedge_bands.ts`).
 *
 * This detector exists because the lane asserted a safety property in prose
 * with nothing behind it: "No entry below claims a stronger hedge than its own
 * catalog confidence licenses." Adversarial review machine-checked it and found
 * 9 of 25 entries mismatched, 4 of them overclaims. The assertion is now a
 * computed gate wired into `review.ts`; this file proves the gate can fail
 * before any of its greens count.
 */
import { describe, expect, it } from 'vitest'

import { loadReaderFacingCatalog } from '../catalog'
import { READER_TEXT_ENTRIES } from '../entries'
import {
  HEDGE_BAND_MARKERS,
  checkHedgeBand,
  detectHedgeBands,
  licensedHedgeBand,
} from '../hedge_bands'
import { reviewEntry } from '../review'
import type { MsrSignal, ReaderTextEntry } from '../types'

const catalog = loadReaderFacingCatalog()
const signalsById = new Map<string, MsrSignal>(catalog.map((s) => [s.signal_id, s]))

function realSignal(id: string): MsrSignal {
  const s = signalsById.get(id)
  if (!s) throw new Error(`fixture signal ${id} not found in catalog — test setup bug`)
  return s
}

describe('licensedHedgeBand — band boundaries and the honest-null case', () => {
  it('maps confidence onto exactly the published bands, at their boundaries', () => {
    expect(licensedHedgeBand(0.95)).toBe('well_established')
    expect(licensedHedgeBand(0.9)).toBe('well_established')
    expect(licensedHedgeBand(0.89)).toBe('solidly_supported')
    expect(licensedHedgeBand(0.8)).toBe('solidly_supported')
    expect(licensedHedgeBand(0.79)).toBe('reasonably_supported')
    expect(licensedHedgeBand(0.7)).toBe('reasonably_supported')
    expect(licensedHedgeBand(0.69)).toBe('provisional')
    expect(licensedHedgeBand(0.68)).toBe('provisional')
  })

  it('licenses NO band when the catalog records no usable confidence', () => {
    // msr_parser.ts defaults a missing `confidence:` to 0 — indistinguishable
    // from a real 0.00, so it licenses nothing rather than the weakest band.
    expect(licensedHedgeBand(0)).toBeNull()
    expect(licensedHedgeBand(null)).toBeNull()
    expect(licensedHedgeBand(undefined)).toBeNull()
    expect(licensedHedgeBand(Number.NaN)).toBeNull()
  })
})

describe('detectHedgeBands — markers are disjoint and decidable', () => {
  it('finds exactly the band claimed, and finds more than one when more than one is claimed', () => {
    expect(detectHedgeBands('This is well-established in the chart.')).toEqual(['well_established'])
    expect(detectHedgeBands('Treat it as genuinely provisional.')).toEqual(['provisional'])
    expect(detectHedgeBands('Solidly supported, and also reasonably supported.')).toEqual([
      'solidly_supported',
      'reasonably_supported',
    ])
    expect(detectHedgeBands('No hedge phrase at all here.')).toEqual([])
  })
})

describe('hedge-band gate — RED then GREEN (§N.8)', () => {
  // SIG.MSR.121 carries catalog confidence 0.72 -> licensed "reasonably supported".
  // The fixture text is synthetic and pinned rather than derived from the real
  // entry's current prose: these RED cases must keep proving the DETECTOR works
  // even while the authored text is being edited, and a fixture built by
  // string-replacing whatever band the real entry happens to carry today breaks
  // the moment that band legitimately changes. The real entries are covered by
  // the GREEN batch case at the bottom, which reads them directly.
  const fixture = (hedge: string): ReaderTextEntry => ({
    signal_id: 'SIG.MSR.121',
    reader_text: `Six of the seven classical planets sit in pairs across three signs. Confidence is ${hedge}.`,
    grade: 'supporting',
    grounding_note: 'Classical basis: "Phaladeepika Ch.12 (multi-planet sign concentrations)"',
    catalog_discrepancy_note: '',
  })
  const base = fixture(HEDGE_BAND_MARKERS.reasonably_supported)

  it('RED: an entry hedged STRONGER than its catalog confidence licenses fails the gate', () => {
    const overclaimed: ReaderTextEntry = {
      ...base,
      reader_text: fixture(HEDGE_BAND_MARKERS.well_established).reader_text,
    }
    expect(overclaimed.reader_text).not.toBe(base.reader_text)

    const result = checkHedgeBand(overclaimed, realSignal('SIG.MSR.121'))
    expect(result.passed).toBe(false)
    expect(result.flags[0].code).toBe('hedge_band_mismatch')
    expect(result.flags[0].detail).toContain('OVERCLAIM')

    // …and the gate is wired into review, so the overclaim cannot freeze.
    const reviewed = reviewEntry(overclaimed, realSignal('SIG.MSR.121'))
    expect(reviewed.passed).toBe(false)
    expect(reviewed.flags.some((f) => f.source === 'hedge_band')).toBe(true)
  })

  it('RED: an entry hedged WEAKER than licensed also fails (the band is exact, not a ceiling)', () => {
    const underclaimed: ReaderTextEntry = {
      ...base,
      reader_text: fixture(HEDGE_BAND_MARKERS.provisional).reader_text,
    }
    const result = checkHedgeBand(underclaimed, realSignal('SIG.MSR.121'))
    expect(result.passed).toBe(false)
    expect(result.flags[0].detail).toContain('underclaim')
  })

  it('RED: an entry claiming two bands at once is ambiguous and fails', () => {
    const ambiguous: ReaderTextEntry = {
      ...base,
      reader_text: `${base.reader_text} It is also well-established.`,
    }
    const result = checkHedgeBand(ambiguous, realSignal('SIG.MSR.121'))
    expect(result.passed).toBe(false)
    expect(result.flags[0].code).toBe('hedge_band_ambiguous')
  })

  it('RED: an entry stating no hedge at all fails when the catalog licenses one', () => {
    const silent: ReaderTextEntry = {
      ...base,
      reader_text: fixture('a direct count').reader_text,
    }
    const result = checkHedgeBand(silent, realSignal('SIG.MSR.121'))
    expect(result.passed).toBe(false)
    expect(result.flags[0].code).toBe('hedge_band_absent')
  })

  it('GREEN: the pinned fixture at its licensed band passes the gate', () => {
    const result = checkHedgeBand(base, realSignal('SIG.MSR.121'))
    expect(result.passed).toBe(true)
    expect(result.licensed).toBe('reasonably_supported')
    expect(result.claimed).toEqual(['reasonably_supported'])
  })

  it('GREEN: every authored entry claims exactly the band its own catalog confidence licenses', () => {
    const mismatches: string[] = []
    for (const entry of READER_TEXT_ENTRIES) {
      const signal = signalsById.get(entry.signal_id) ?? null
      const result = checkHedgeBand(entry, signal)
      if (!result.passed) mismatches.push(result.flags.map((f) => f.detail).join(' | '))
    }
    expect(mismatches).toEqual([])
  })
})
