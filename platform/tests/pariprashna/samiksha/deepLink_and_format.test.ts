/**
 * SAMĪKṢĀ deep-link builder + display helpers — PB-3 lane L-3 (pure unit, no DB).
 *
 * The deep link is READ-ONLY by construction: `buildTurnDeepLink` is a pure function returning
 * a URL string (a GET target). This test pins its exact shape and proves it has no side effect
 * (calling it does not mutate its input and returns a stable string) — the P1 "settled turns
 * stay byte-identical" guarantee holds because there is simply no write path here.
 */
import { describe, it, expect } from 'vitest'
import { buildTurnDeepLink } from '@/lib/pariprashna/samiksha/deepLink'
import {
  parseDaterange,
  parseNumrange,
  confidencePhrase,
  windowLabel,
  kalaRekhaGeometry,
} from '@/components/pariprashna/samiksha/format'

describe('buildTurnDeepLink (read-only)', () => {
  it('produces the documented thread route + turn anchor', () => {
    const url = buildTurnDeepLink({
      chartId: '482012f1-710e-4a25-994a-93821f5871aa',
      conversationId: 'c0ffee00-0000-4000-8000-000000000001',
      turnOrdinal: 7,
    })
    expect(url).toBe(
      '/clients/482012f1-710e-4a25-994a-93821f5871aa/pariprashna?thread=c0ffee00-0000-4000-8000-000000000001#turn-7',
    )
  })

  it('is pure — no side effect, stable output, input unmutated', () => {
    const input = { chartId: 'a', conversationId: 'b', turnOrdinal: 1 }
    const frozen = Object.freeze({ ...input })
    const a = buildTurnDeepLink(frozen)
    const b = buildTurnDeepLink(frozen)
    expect(a).toBe(b)
    expect(frozen).toEqual({ chartId: 'a', conversationId: 'b', turnOrdinal: 1 })
    expect(a.startsWith('/clients/')).toBe(true) // relative GET target, never an API/mutation URL
    expect(a).not.toContain('/api/')
  })
})

describe('display helpers', () => {
  it('parses Postgres range literals', () => {
    expect(parseDaterange('[2026-07-01,2027-01-01)')).toEqual({ start: '2026-07-01', end: '2027-01-01' })
    expect(parseNumrange('[0.55,0.7)')).toEqual({ low: 0.55, high: 0.7 })
    expect(parseDaterange(null)).toBeNull()
    expect(parseNumrange('garbage')).toBeNull()
  })

  it('confidencePhrase is non-numeric-band, neutral', () => {
    expect(confidencePhrase({ low: 0.55, high: 0.65 })).toBe('~60% confidence')
    expect(confidencePhrase(null)).toBe('confidence not yet set')
  })

  it('windowLabel renders a short month-year span', () => {
    expect(windowLabel({ start: '2026-07-01', end: '2027-01-01' })).toBe('Jul 2026 – Jan 2027')
  })

  it('kalaRekhaGeometry places the today-dot deterministically across [readingDate, windowEnd] (§6.9)', () => {
    // PB-6 (SAMĀPTI): domain is [readingDate, windowEnd] — the window's end is
    // always the domain's right edge (windowEndFraction === 1), and the
    // window's start floats wherever it genuinely falls relative to the
    // reading date (no longer padded 0.5x on either side).
    const geo = kalaRekhaGeometry({ start: '2026-01-01', end: '2026-12-31' }, '2026-07-01', '2025-10-01')
    expect(geo).not.toBeNull()
    expect(geo!.windowStartFraction).toBeGreaterThan(0)
    expect(geo!.windowEndFraction).toBe(1)
    expect(geo!.todayFraction).toBeGreaterThan(geo!.windowStartFraction)
    expect(geo!.todayFraction).toBeLessThan(geo!.windowEndFraction)
  })

  it('kalaRekhaGeometry returns null when the window ends at/before the reading date (degenerate domain)', () => {
    const geo = kalaRekhaGeometry({ start: '2025-01-01', end: '2025-06-01' }, '2025-03-01', '2025-06-01')
    expect(geo).toBeNull()
  })
})
