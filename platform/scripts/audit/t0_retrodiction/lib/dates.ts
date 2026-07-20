/**
 * dates.ts — date-math primitives for the T-0 retrodiction-gate harness
 * (BRIEF_D3.md §F1 Lane T-0). No network, no astrology — pure calendar math
 * so it is trivially unit-testable offline (CONDUCTOR_PROTOCOL §3.1(b)).
 */

const MS_PER_DAY = 86_400_000

/** Parses a 'YYYY-MM-DD' string as a UTC midnight Date (avoids TZ drift). */
export function parseDate(iso: string): Date {
  const [y, m, d] = iso.slice(0, 10).split('-').map(Number)
  return new Date(Date.UTC(y, m - 1, d))
}

export function toIsoDate(d: Date): string {
  return d.toISOString().slice(0, 10)
}

export function addDays(d: Date, days: number): Date {
  return new Date(d.getTime() + days * MS_PER_DAY)
}

/** Signed day difference b - a. */
export function daysBetween(a: Date, b: Date): number {
  return Math.round((b.getTime() - a.getTime()) / MS_PER_DAY)
}

export function isWithinDays(center: Date, candidate: Date, windowDays: number): boolean {
  return Math.abs(daysBetween(center, candidate)) <= windowDays
}

export function clampDate(d: Date, min: Date, max: Date): Date {
  if (d.getTime() < min.getTime()) return min
  if (d.getTime() > max.getTime()) return max
  return d
}
