/**
 * Paripraśna consent — MINOR EXCLUSION (§3.5.F, PPR-14).
 *
 * "Minors (§3.5.F): trivially computable — `birth_date` is the chart's own
 * primary datum. A chart whose subject is <18 is servable ONLY to the native in
 * a parent/guardian capacity and NEVER enters the cohort; enforced at
 * entitlement resolution, not convention."
 *
 * This module is the "trivially computable" half — pure calendar arithmetic on
 * `charts.birth_date` (a Postgres `DATE`, which the app's pg client returns as a
 * 'YYYY-MM-DD' string). The enforcement half lives in `resolve.ts`.
 *
 * ── TIMEZONE, STATED HONESTLY (§N.7 item 6) ──────────────────────────────────
 * `charts.birth_date` is a bare calendar DATE with no offset (the chart's
 * `timezone_id` is nullable and is not part of this computation). The age is
 * therefore a calendar-to-calendar comparison, evaluated against the UTC
 * calendar date of `asOf`. On the subject's 18th birthday there is a window of
 * up to ~a day in which their local calendar and UTC disagree. We do NOT invent
 * a safety margin to paper over this: a margin would be a number chosen for how
 * it reads rather than derived from anything. The boundary is documented, the
 * arithmetic is exact, and the tests pin both sides of it.
 */

/** The threshold is 18 per §3.5.F. Named, never a bare literal at a call site. */
export const MINOR_AGE_THRESHOLD_YEARS = 18

export interface CalendarDate {
  year: number
  month: number // 1-12
  day: number // 1-31
}

const DATE_PREFIX_RE = /^(\d{4})-(\d{2})-(\d{2})(?:[T ].*)?$/

function isRealCalendarDate(y: number, m: number, d: number): boolean {
  if (m < 1 || m > 12 || d < 1 || d > 31) return false
  // Round-trip through UTC: rejects 2026-02-30, 2025-02-29, 2026-04-31, …
  const probe = new Date(Date.UTC(y, m - 1, d))
  return (
    probe.getUTCFullYear() === y && probe.getUTCMonth() === m - 1 && probe.getUTCDate() === d
  )
}

/**
 * Parse a `charts.birth_date` value into a calendar date.
 * Returns `null` — an honest "unknown", never a silently-defaulted date — when
 * the value is absent or is not a real calendar date.
 */
export function parseBirthDate(value: string | Date | null | undefined): CalendarDate | null {
  if (value == null) return null

  if (value instanceof Date) {
    if (Number.isNaN(value.getTime())) return null
    return { year: value.getUTCFullYear(), month: value.getUTCMonth() + 1, day: value.getUTCDate() }
  }

  const m = DATE_PREFIX_RE.exec(value.trim())
  if (!m) return null
  const year = Number(m[1])
  const month = Number(m[2])
  const day = Number(m[3])
  if (!isRealCalendarDate(year, month, day)) return null
  return { year, month, day }
}

/** The UTC calendar date of an instant. */
export function utcCalendarDate(instant: Date): CalendarDate {
  return {
    year: instant.getUTCFullYear(),
    month: instant.getUTCMonth() + 1,
    day: instant.getUTCDate(),
  }
}

/**
 * Completed years between `birthDate` and `asOf`, by calendar comparison.
 *
 * Returns `null` when the birth date cannot be parsed. Returns a NEGATIVE number
 * for a birth date in the future — also honest: a future-dated chart is not a
 * zero-year-old, and callers fail closed on it via `isMinorSubject`.
 */
export function computeAgeYears(
  birthDate: string | Date | null | undefined,
  asOf: Date = new Date(),
): number | null {
  const b = parseBirthDate(birthDate)
  if (!b) return null
  const now = utcCalendarDate(asOf)

  let age = now.year - b.year
  const beforeBirthdayThisYear =
    now.month < b.month || (now.month === b.month && now.day < b.day)
  if (beforeBirthdayThisYear) age -= 1
  return age
}

/**
 * Is this subject a minor (<18) as of `asOf`?
 *
 * Returns `null` when the age cannot be computed. `null` is NOT "no" — every
 * caller must fail closed on it (resolve.ts refuses with reason
 * `birth_date_unavailable`).
 */
export function isMinorSubject(
  birthDate: string | Date | null | undefined,
  asOf: Date = new Date(),
): boolean | null {
  const age = computeAgeYears(birthDate, asOf)
  if (age === null) return null
  return age < MINOR_AGE_THRESHOLD_YEARS
}
