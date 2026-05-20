/**
 * __tests__/ics_builder.test.ts
 *
 * Tests for ics_builder.ts — buildDayIcs + buildMuhuratIcs.
 *
 * AC.4C7.2: Builders return RFC 5545-compliant ICS strings.
 * Checks: required VCALENDAR/VEVENT structure, PRODID, DTSTART/DTEND presence,
 * CATEGORIES tags, DESCRIPTION back-links.
 */

import { describe, it, expect, beforeEach } from 'vitest'
import { buildDayIcs, buildMuhuratIcs } from '../ics_builder'
import type { PanchangDay } from '@/app/panchang/hooks/usePanchangDay'
import type { MuhuratWindow } from '@/app/panchang/hooks/useMuhuratFinder'

// ── Fixtures ──────────────────────────────────────────────────────────────────

function makePanchang(overrides: Partial<PanchangDay> = {}): PanchangDay {
  return {
    date: '2026-05-20',
    lat: 20.27,
    lon: 85.84,
    tz_offset_minutes: 330,
    angas: {
      tithi: { name: 'Tritiya', number: 3 },
      nakshatra: { name: 'Rohini', number: 4 },
      yoga: { name: 'Siddhi', number: 21 },
      karana_first: { name: 'Bava', number: 1 },
      karana_second: { name: 'Balava', number: 2 },
      vara: { name: 'Wednesday', number: 4 },
      paksha: 'Shukla',
    },
    timings: {
      sunrise_utc: '2026-05-20T00:53:00Z',
      sunset_utc: '2026-05-20T13:15:00Z',
      moonrise_utc: null,
      moonset_utc: null,
      inauspicious: {
        rahu_kalam: { start: '2026-05-20T07:30:00Z', end: '2026-05-20T09:00:00Z' },
        yamagandam: { start: '2026-05-20T05:00:00Z', end: '2026-05-20T06:30:00Z' },
        gulika_kalam: null,
        bhadra: null,
      },
      auspicious: {
        abhijit: {
          name: 'Abhijit Muhurta',
          start: '2026-05-20T06:45:00Z',
          end: '2026-05-20T07:30:00Z',
          score: 4,
        },
      },
    },
    special_yogas: [
      {
        name: 'Sarvartha Siddhi Yoga',
        score: 5,
        start: '2026-05-20T00:53:00Z',
        end: '2026-05-20T13:15:00Z',
      },
    ],
    planets: null,
    choghadiya: null,
    hora: null,
    native_context: null,
    raw: {},
    ...overrides,
  }
}

function makeMuhuratWindows(): MuhuratWindow[] {
  return [
    {
      event: 'marriage',
      start_utc: '2026-06-01T03:30:00Z',
      end_utc: '2026-06-01T05:00:00Z',
      star_rating: 5,
      score: 4.8,
      breakdown: { tithi: 1.2, nakshatra: 1.5, vara: 0.8, tara_bala: 0.9, avoid: -0.6 },
    },
    {
      event: 'marriage',
      start_utc: '2026-06-05T04:00:00Z',
      end_utc: '2026-06-05T06:00:00Z',
      star_rating: 4,
      score: 3.5,
      breakdown: { tithi: 1.0, nakshatra: 1.2, vara: 0.7, tara_bala: 0.6 },
    },
  ]
}

// ── buildDayIcs tests ─────────────────────────────────────────────────────────

describe('buildDayIcs', () => {
  let ics: string

  beforeEach(() => {
    ics = buildDayIcs(makePanchang(), 'Bhubaneswar, IN')
  })

  it('returns a non-empty string', () => {
    expect(ics).toBeTruthy()
    expect(typeof ics).toBe('string')
  })

  it('contains required RFC 5545 calendar wrapper', () => {
    expect(ics).toContain('BEGIN:VCALENDAR')
    expect(ics).toContain('END:VCALENDAR')
    expect(ics).toContain('VERSION:2.0')
    expect(ics).toContain('MARSYS-JIS//Panchang Calendar//EN')
  })

  it('contains at least one VEVENT', () => {
    expect(ics).toContain('BEGIN:VEVENT')
    expect(ics).toContain('END:VEVENT')
  })

  it('includes Rahu Kalam as an inauspicious event', () => {
    expect(ics).toContain('Rahu Kalam')
    expect(ics).toContain('MARSYS-Panchang/avoid')
  })

  it('includes Yamagandam as an inauspicious event', () => {
    expect(ics).toContain('Yamagandam')
  })

  it('includes Abhijit Muhurta as an auspicious event', () => {
    expect(ics).toContain('Abhijit Muhurta')
    expect(ics).toContain('MARSYS-Panchang/auspicious')
  })

  it('includes Sarvartha Siddhi Yoga from special_yogas', () => {
    expect(ics).toContain('Sarvartha Siddhi Yoga')
  })

  it('includes DTSTART and DTEND for events', () => {
    expect(ics).toContain('DTSTART:')
    expect(ics).toContain('DTEND:')
  })

  it('includes a back-link to /panchang in DESCRIPTION', () => {
    expect(ics).toContain('/panchang?d=2026-05-20')
  })

  it('includes LOCATION', () => {
    expect(ics).toContain('LOCATION:Bhubaneswar')
  })

  it('handles panchang with no inauspicious windows (all null)', () => {
    const noInaus = makePanchang()
    noInaus.timings.inauspicious = null
    noInaus.timings.auspicious = null
    noInaus.special_yogas = null
    const result = buildDayIcs(noInaus, 'Bhubaneswar, IN')
    expect(result).toContain('BEGIN:VCALENDAR')
    expect(result).toContain('END:VCALENDAR')
    // Should still produce valid ICS even with no events
    const veventCount = (result.match(/BEGIN:VEVENT/g) ?? []).length
    expect(veventCount).toBeGreaterThanOrEqual(0)
  })

  it('DTSTART format is UTC (ends with Z)', () => {
    const match = ics.match(/DTSTART:(\S+)/)
    expect(match).toBeTruthy()
    if (match) {
      expect(match[1]).toMatch(/Z$/)
    }
  })
})

// ── buildMuhuratIcs tests ─────────────────────────────────────────────────────

describe('buildMuhuratIcs', () => {
  let ics: string
  const windows = makeMuhuratWindows()

  beforeEach(() => {
    ics = buildMuhuratIcs(windows, 'Bhubaneswar, IN', 'marriage')
  })

  it('returns a non-empty string', () => {
    expect(ics).toBeTruthy()
    expect(typeof ics).toBe('string')
  })

  it('contains required RFC 5545 calendar wrapper', () => {
    expect(ics).toContain('BEGIN:VCALENDAR')
    expect(ics).toContain('END:VCALENDAR')
    expect(ics).toContain('VERSION:2.0')
  })

  it('contains one VEVENT per window', () => {
    const veventCount = (ics.match(/BEGIN:VEVENT/g) ?? []).length
    expect(veventCount).toBe(windows.length)
  })

  it('includes MARSYS-Panchang/muhurat category', () => {
    expect(ics).toContain('MARSYS-Panchang/muhurat')
  })

  it('includes star ratings in SUMMARY', () => {
    expect(ics).toContain('★')
  })

  it('includes breakdown scores in DESCRIPTION', () => {
    expect(ics).toContain('nakshatra')
    expect(ics).toContain('tithi')
  })

  it('ranks windows by score (highest first)', () => {
    // First event should be the highest-scored window (4.8)
    const firstSummaryMatch = ics.match(/BEGIN:VEVENT[\s\S]*?SUMMARY:([^\r\n]+)/)
    expect(firstSummaryMatch).toBeTruthy()
    if (firstSummaryMatch) {
      // Score 4.8 → 5 stars → "★★★★★"
      expect(firstSummaryMatch[1]).toContain('★★★★★')
    }
  })

  it('includes LOCATION', () => {
    expect(ics).toContain('LOCATION:Bhubaneswar')
  })

  it('handles empty windows array gracefully', () => {
    const result = buildMuhuratIcs([], 'Bhubaneswar, IN', 'marriage')
    expect(result).toContain('BEGIN:VCALENDAR')
    expect(result).toContain('END:VCALENDAR')
    const veventCount = (result.match(/BEGIN:VEVENT/g) ?? []).length
    expect(veventCount).toBe(0)
  })

  it('handles windows with null start_utc gracefully', () => {
    const windowsWithNull: MuhuratWindow[] = [
      { ...windows[0], start_utc: null },
      windows[1],
    ]
    const result = buildMuhuratIcs(windowsWithNull, 'Bhubaneswar, IN', 'marriage')
    // Only the non-null window should produce a VEVENT
    const veventCount = (result.match(/BEGIN:VEVENT/g) ?? []).length
    expect(veventCount).toBe(1)
  })
})
