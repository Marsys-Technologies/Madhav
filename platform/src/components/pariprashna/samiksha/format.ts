/**
 * SAMĪKṢĀ display helpers — PB-3 (SAMĪKṢĀ) lane L-3.
 *
 * Client-side, isomorphic parsing of the raw Postgres range literals the DAL returns as text
 * (`window`: "[2026-07-01,2027-01-01)", `confidence`: "[0.55,0.7)") into values a component can
 * render. Pure functions, no I/O — unit-testable and safe in a client bundle.
 */

export interface ParsedDateWindow {
  start: string // ISO yyyy-mm-dd
  end: string // ISO yyyy-mm-dd (exclusive upper)
}

export interface ParsedConfidence {
  low: number
  high: number
}

/** Parse a Postgres daterange literal `[lo,hi)` → {start,end}. Null on empty/malformed. */
export function parseDaterange(literal: string | null | undefined): ParsedDateWindow | null {
  if (!literal) return null
  const m = literal.match(/^[[(]\s*("?)(\d{4}-\d{2}-\d{2})\1\s*,\s*("?)(\d{4}-\d{2}-\d{2})\3\s*[\])]$/)
  if (!m) return null
  return { start: m[2], end: m[4] }
}

/** Parse a Postgres numrange literal `[lo,hi)` → {low,high}. Null on empty/malformed. */
export function parseNumrange(literal: string | null | undefined): ParsedConfidence | null {
  if (!literal) return null
  const m = literal.match(/^[[(]\s*([0-9.]+)\s*,\s*([0-9.]+)\s*[\])]$/)
  if (!m) return null
  return { low: Number(m[1]), high: Number(m[2]) }
}

/** A neutral, non-numeric confidence phrase (mirrors the dock card's `confidencePhrase`). */
export function confidencePhrase(c: ParsedConfidence | null): string {
  if (!c) return 'confidence not yet set'
  const mid = (c.low + c.high) / 2
  const pct = Math.round(mid * 100)
  return `~${pct}% confidence`
}

/** Short human window label, e.g. "Jul 2026 – Jan 2027". */
export function windowLabel(w: ParsedDateWindow | null): string {
  if (!w) return 'no window'
  const fmt = (iso: string) => {
    const d = new Date(iso + 'T00:00:00Z')
    if (Number.isNaN(d.getTime())) return iso
    return d.toLocaleDateString('en-GB', { month: 'short', year: 'numeric', timeZone: 'UTC' })
  }
  return `${fmt(w.start)} – ${fmt(w.end)}`
}

/**
 * kāla-rekhā geometry: given a window and "now", compute the today-dot fraction across a span
 * that pads the window on both sides so the dot has room to travel. Returns fractions in [0,1].
 * Deterministic given `nowIso` (injected, never `Date.now()` inside — so tests are stable).
 */
export function kalaRekhaGeometry(
  w: ParsedDateWindow | null,
  nowIso: string,
): { windowStartFraction: number; windowEndFraction: number; todayFraction: number } | null {
  if (!w) return null
  const start = Date.parse(w.start + 'T00:00:00Z')
  const end = Date.parse(w.end + 'T00:00:00Z')
  const now = Date.parse(nowIso.slice(0, 10) + 'T00:00:00Z')
  if (Number.isNaN(start) || Number.isNaN(end) || end <= start) return null
  const dur = end - start
  const spanStart = start - dur * 0.5
  const spanEnd = end + dur * 0.5
  const span = spanEnd - spanStart
  const clamp = (v: number) => Math.max(0, Math.min(1, v))
  return {
    windowStartFraction: clamp((start - spanStart) / span),
    windowEndFraction: clamp((end - spanStart) / span),
    todayFraction: clamp((now - spanStart) / span),
  }
}
