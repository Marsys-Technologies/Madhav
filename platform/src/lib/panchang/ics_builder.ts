/**
 * ics_builder.ts — iCal (RFC 5545) builders for Panchang events.
 *
 * Exports:
 *   buildDayIcs(panchang, location)   → ICS string for a full Panchang day
 *   buildMuhuratIcs(windows, location) → ICS string for Muhurat Finder results
 *
 * Phase: 4C-7 (Item 2)
 */

import ical, { ICalCalendarMethod } from 'ical-generator'
import type { PanchangDay } from '@/app/panchang/hooks/usePanchangDay'
import type { MuhuratWindow } from '@/app/panchang/hooks/useMuhuratFinder'

// ── Constants ─────────────────────────────────────────────────────────────────

const PROD_ID = '-//MARSYS-JIS//Panchang Calendar//EN'
const APP_URL = process.env.NEXT_PUBLIC_APP_URL ?? 'https://amjis-web.run.app'

// Default event duration for auspicious yogas (90 minutes if no end time)
const DEFAULT_AUSPICIOUS_DURATION_MS = 90 * 60 * 1000

// Default event duration for inauspicious windows (90 minutes)
const DEFAULT_INAUSPICIOUS_DURATION_MS = 90 * 60 * 1000

// ── Helpers ───────────────────────────────────────────────────────────────────

/** Parse a UTC ISO string or null to a Date or null */
function parseUtc(iso: string | null | undefined): Date | null {
  if (!iso) return null
  const d = new Date(iso)
  return isNaN(d.getTime()) ? null : d
}

/** Star rating unicode for SUMMARY lines */
function starsFor(score: number): string {
  const stars = Math.round(Math.max(1, Math.min(5, score)))
  return '★'.repeat(stars) + '☆'.repeat(5 - stars)
}

/** Format a breakdown dict as a readable text block for ICS DESCRIPTION */
function formatBreakdown(breakdown: Record<string, number>): string {
  const lines = Object.entries(breakdown)
    .filter(([, v]) => v !== 0)
    .sort(([, a], [, b]) => b - a)
    .map(([k, v]) => `  • ${k}: ${v >= 0 ? '+' : ''}${v.toFixed(2)}`)
  return lines.length > 0 ? lines.join('\n') : '  (no breakdown available)'
}

// ── buildDayIcs ───────────────────────────────────────────────────────────────

/**
 * Build an ICS string for all significant events in a Panchang day.
 *
 * Adds:
 *   - Auspicious yogas (if any) with category MARSYS-Panchang/auspicious
 *   - Inauspicious windows (Rahu/Yama/Gulika/Bhadra) with category MARSYS-Panchang/avoid
 *
 * @param panchang  PanchangDay object (from usePanchangDay / SSR fetch)
 * @param location  Human-readable location string (e.g. "Bhubaneswar, IN")
 */
export function buildDayIcs(panchang: PanchangDay, location: string): string {
  const cal = ical({
    prodId: PROD_ID,
    name: `Panchang — ${panchang.date}`,
    method: ICalCalendarMethod.PUBLISH,
    description: `MARSYS-JIS Panchang for ${location} on ${panchang.date}`,
  })

  const dateLabel = panchang.date
  const deepLink = `${APP_URL}/panchang?d=${dateLabel}`

  // ── 1. Inauspicious windows ────────────────────────────────────────────────

  const inauspiciousKeys = ['rahu_kalam', 'yamagandam', 'gulika_kalam', 'bhadra'] as const

  if (panchang.timings.inauspicious) {
    const inaus = panchang.timings.inauspicious as Record<string, { start: string | null; end: string | null } | null>
    for (const key of inauspiciousKeys) {
      const window = inaus[key]
      if (!window) continue
      const start = parseUtc(window.start)
      if (!start) continue
      const end = parseUtc(window.end) ?? new Date(start.getTime() + DEFAULT_INAUSPICIOUS_DURATION_MS)

      const labels: Record<string, string> = {
        rahu_kalam: 'Rahu Kalam',
        yamagandam: 'Yamagandam',
        gulika_kalam: 'Gulika Kalam',
        bhadra: 'Bhadra',
      }
      const label = labels[key] ?? key

      cal.createEvent({
        start,
        end,
        summary: `⚠️ ${label} — Avoid`,
        description: `${label} is an inauspicious period. Avoid starting new ventures or important activities during this window.\n\nFull Panchang: ${deepLink}`,
        location,
        categories: [{ name: 'MARSYS-Panchang/avoid' }],
        url: deepLink,
        transparency: 'TRANSPARENT' as never,
      })
    }
  }

  // ── 2. Auspicious yogas ────────────────────────────────────────────────────

  if (panchang.timings.auspicious) {
    const aus = panchang.timings.auspicious as Record<string, { name?: string; start?: string | null; end?: string | null; score?: number } | null>

    for (const [key, yoga] of Object.entries(aus)) {
      if (!yoga) continue
      const yogaName = yoga.name ?? key
      const start = parseUtc(yoga.start)
      if (!start) continue
      const end = parseUtc(yoga.end) ?? new Date(start.getTime() + DEFAULT_AUSPICIOUS_DURATION_MS)
      const score = yoga.score ?? 3
      const stars = starsFor(score)

      cal.createEvent({
        start,
        end,
        summary: `✨ ${yogaName} ${stars}`,
        description: `${yogaName} is an auspicious yoga active on ${dateLabel}.\n\nRating: ${stars} (${score.toFixed ? score.toFixed(1) : score})\n\nFull Panchang: ${deepLink}`,
        location,
        categories: [{ name: 'MARSYS-Panchang/auspicious' }],
        url: deepLink,
      })
    }
  }

  // ── 3. Special yogas (special_yogas array) ─────────────────────────────────

  if (Array.isArray(panchang.special_yogas) && panchang.special_yogas.length > 0) {
    const sunrise = parseUtc(panchang.timings.sunrise_utc)
    const sunset = parseUtc(panchang.timings.sunset_utc)

    for (const yoga of panchang.special_yogas) {
      const y = yoga as { name?: string; score?: number; start?: string | null; end?: string | null }
      const yogaName = y.name ?? 'Special Yoga'
      const start = parseUtc(y.start) ?? sunrise
      if (!start) continue
      const end = parseUtc(y.end) ?? sunset ?? new Date(start.getTime() + DEFAULT_AUSPICIOUS_DURATION_MS)
      const score = y.score ?? 3
      const stars = starsFor(score)

      cal.createEvent({
        start,
        end,
        summary: `✨ ${yogaName} ${stars}`,
        description: `${yogaName} — auspicious yoga for ${dateLabel}.\n\nRating: ${stars}\n\nFull Panchang: ${deepLink}`,
        location,
        categories: [{ name: 'MARSYS-Panchang/auspicious' }],
        url: deepLink,
      })
    }
  }

  return cal.toString()
}

// ── buildMuhuratIcs ───────────────────────────────────────────────────────────

/**
 * Build an ICS string for a set of Muhurat Finder result windows.
 *
 * Each window becomes one VEVENT with category MARSYS-Panchang/muhurat.
 * DESCRIPTION includes star rating + breakdown scores.
 *
 * @param windows   Array of MuhuratWindow objects from the finder
 * @param location  Human-readable location string (e.g. "Bhubaneswar, IN")
 * @param eventKey  Event key (e.g. "marriage", "business_start") for context
 */
export function buildMuhuratIcs(
  windows: MuhuratWindow[],
  location: string,
  eventKey?: string,
): string {
  const eventLabel = eventKey ? eventKey.replace(/_/g, ' ') : 'muhurat'
  const cal = ical({
    prodId: PROD_ID,
    name: `Muhurat Finder — ${eventLabel}`,
    method: ICalCalendarMethod.PUBLISH,
    description: `MARSYS-JIS Muhurat windows for ${eventLabel} at ${location}`,
  })

  const sorted = [...windows].sort((a, b) => b.score - a.score)

  sorted.forEach((w, idx) => {
    const start = parseUtc(w.start_utc)
    if (!start) return
    const end = parseUtc(w.end_utc) ?? new Date(start.getTime() + DEFAULT_AUSPICIOUS_DURATION_MS)
    const stars = starsFor(w.star_rating)
    const rank = idx + 1

    const breakdownText = formatBreakdown(w.breakdown)
    const deepLink = `${APP_URL}/panchang`

    cal.createEvent({
      start,
      end,
      summary: `${stars} ${eventLabel} Muhurat #${rank}`,
      description: [
        `Rank #${rank} auspicious window for ${eventLabel}.`,
        `Score: ${w.score.toFixed(2)} (${stars})`,
        '',
        'Score breakdown:',
        breakdownText,
        '',
        `View on MARSYS Panchang: ${deepLink}`,
      ].join('\n'),
      location,
      categories: [{ name: 'MARSYS-Panchang/muhurat' }],
      url: deepLink,
    })
  })

  return cal.toString()
}
