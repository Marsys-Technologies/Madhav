/**
 * ics_client.ts — Browser-safe RFC 5545 ICS formatter for client components.
 *
 * Does NOT use ical-generator (Node-only due to crypto dep) — instead
 * hand-rolls the minimal RFC 5545 format for single-event / small-batch exports.
 *
 * Used by MuhuratResultsList for inline "Export to Calendar" downloads.
 *
 * RFC 5545 reference: https://tools.ietf.org/html/rfc5545
 *
 * Phase: 4C-7 (Item 9 support)
 */

// ── Helpers ───────────────────────────────────────────────────────────────────

/** Format a Date as RFC 5545 UTC datetime: 20261231T120000Z */
function formatIcsDate(d: Date): string {
  const pad = (n: number) => String(n).padStart(2, '0')
  return [
    d.getUTCFullYear(),
    pad(d.getUTCMonth() + 1),
    pad(d.getUTCDate()),
    'T',
    pad(d.getUTCHours()),
    pad(d.getUTCMinutes()),
    pad(d.getUTCSeconds()),
    'Z',
  ].join('')
}

/** Fold long lines per RFC 5545 §3.1 (max 75 octets, fold with CRLF + SPACE) */
function foldLine(line: string): string {
  const MAX = 75
  if (line.length <= MAX) return line
  const parts: string[] = []
  let pos = 0
  while (pos < line.length) {
    if (pos === 0) {
      parts.push(line.slice(0, MAX))
      pos = MAX
    } else {
      parts.push(' ' + line.slice(pos, pos + MAX - 1))
      pos += MAX - 1
    }
  }
  return parts.join('\r\n')
}

/** Escape special chars in ICS text values per RFC 5545 §3.3.11 */
function escapeText(str: string): string {
  return str
    .replace(/\\/g, '\\\\')
    .replace(/;/g, '\\;')
    .replace(/,/g, '\\,')
    .replace(/\n/g, '\\n')
    .replace(/\r/g, '')
}

/** Generate a UUID-like DTSTAMP + UID */
function makeUid(): string {
  const rand = Math.random().toString(36).slice(2, 10)
  const ts = Date.now()
  return `marsys-${ts}-${rand}@amjis-web`
}

// ── ICS event data ────────────────────────────────────────────────────────────

export interface IcsEventData {
  start: Date
  end: Date
  summary: string
  description?: string
  location?: string
  categories?: string[]
  url?: string
}

// ── buildSingleEventIcs ───────────────────────────────────────────────────────

/**
 * Build a minimal RFC 5545 ICS string for a single event.
 * Safe to run in browser (no Node crypto required).
 */
export function buildSingleEventIcs(event: IcsEventData, calName: string): string {
  const now = formatIcsDate(new Date())
  const start = formatIcsDate(event.start)
  const end = formatIcsDate(event.end)
  const uid = makeUid()

  const lines: string[] = [
    'BEGIN:VCALENDAR',
    'VERSION:2.0',
    `PRODID:-//MARSYS-JIS//Panchang Calendar//EN`,
    'METHOD:PUBLISH',
    foldLine(`X-WR-CALNAME:${escapeText(calName)}`),
    'BEGIN:VEVENT',
    foldLine(`UID:${uid}`),
    `DTSTAMP:${now}`,
    `DTSTART:${start}`,
    `DTEND:${end}`,
    foldLine(`SUMMARY:${escapeText(event.summary)}`),
  ]

  if (event.description) {
    lines.push(foldLine(`DESCRIPTION:${escapeText(event.description)}`))
  }
  if (event.location) {
    lines.push(foldLine(`LOCATION:${escapeText(event.location)}`))
  }
  if (event.categories && event.categories.length > 0) {
    lines.push(foldLine(`CATEGORIES:${event.categories.map(escapeText).join(',')}`))
  }
  if (event.url) {
    lines.push(foldLine(`URL:${event.url}`))
  }

  lines.push('END:VEVENT', 'END:VCALENDAR')
  return lines.join('\r\n') + '\r\n'
}

// ── buildMuhuratWindowIcs ─────────────────────────────────────────────────────

/**
 * Build ICS for a single Muhurat Finder window (browser-safe).
 * Triggers a file download when called client-side.
 */
export interface MuhuratWindowExportData {
  start_utc: string | null
  end_utc: string | null
  star_rating: number
  score: number
  breakdown: Record<string, number>
  event?: string
}

export function buildMuhuratWindowIcs(
  window: MuhuratWindowExportData,
  location: string,
  eventKey?: string,
): string | null {
  if (!window.start_utc) return null
  const start = new Date(window.start_utc)
  if (isNaN(start.getTime())) return null
  const end = window.end_utc
    ? new Date(window.end_utc)
    : new Date(start.getTime() + 90 * 60 * 1000)

  const stars = '★'.repeat(Math.round(Math.max(1, Math.min(5, window.star_rating)))) +
    '☆'.repeat(5 - Math.round(Math.max(1, Math.min(5, window.star_rating))))

  const label = eventKey ? eventKey.replace(/_/g, ' ') : 'muhurat'

  const breakdownLines = Object.entries(window.breakdown)
    .filter(([, v]) => v !== 0)
    .sort(([, a], [, b]) => b - a)
    .map(([k, v]) => `  • ${k}: ${v >= 0 ? '+' : ''}${v.toFixed(2)}`)
    .join('\n')

  const description = [
    `Auspicious window for ${label}.`,
    `Score: ${window.score.toFixed(2)} (${stars})`,
    '',
    'Score breakdown:',
    breakdownLines || '  (no breakdown)',
    '',
    'View on MARSYS Panchang: https://amjis-web.run.app/panchang',
  ].join('\n')

  return buildSingleEventIcs(
    {
      start,
      end,
      summary: `${stars} ${label} Muhurat`,
      description,
      location,
      categories: ['MARSYS-Panchang/muhurat'],
      url: 'https://amjis-web.run.app/panchang',
    },
    `MARSYS Muhurat — ${label}`,
  )
}

// ── downloadIcs (browser helper) ──────────────────────────────────────────────

/**
 * Trigger a browser download of an ICS string.
 */
export function downloadIcs(icsContent: string, filename: string): void {
  const blob = new Blob([icsContent], { type: 'text/calendar;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}
