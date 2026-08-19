/**
 * P1 G1-B — minor exclusion (§3.5.F). Edge cases are the whole point: an
 * off-by-one here is the difference between serving a 17-year-old and refusing
 * an adult, so the boundary is pinned from BOTH sides at every case.
 */

import { describe, expect, it } from 'vitest'

import {
  MINOR_AGE_THRESHOLD_YEARS,
  computeAgeYears,
  isMinorSubject,
  parseBirthDate,
  utcCalendarDate,
} from '../minor_exclusion'

const at = (iso: string) => new Date(`${iso}T12:00:00.000Z`)

describe('MINOR_AGE_THRESHOLD_YEARS', () => {
  it('is 18, per §3.5.F', () => {
    expect(MINOR_AGE_THRESHOLD_YEARS).toBe(18)
  })
})

describe('parseBirthDate', () => {
  it('parses a bare Postgres DATE string', () => {
    expect(parseBirthDate('1984-02-05')).toEqual({ year: 1984, month: 2, day: 5 })
  })

  it('parses a timestamp-shaped string by its date prefix', () => {
    expect(parseBirthDate('1984-02-05T10:43:00.000Z')).toEqual({ year: 1984, month: 2, day: 5 })
    expect(parseBirthDate('1984-02-05 10:43:00')).toEqual({ year: 1984, month: 2, day: 5 })
  })

  it('parses a Date by its UTC components', () => {
    expect(parseBirthDate(new Date(Date.UTC(2008, 1, 29)))).toEqual({
      year: 2008,
      month: 2,
      day: 29,
    })
  })

  it('returns null — not a default — for absent or malformed input', () => {
    expect(parseBirthDate(null)).toBeNull()
    expect(parseBirthDate(undefined)).toBeNull()
    expect(parseBirthDate('')).toBeNull()
    expect(parseBirthDate('05/02/1984')).toBeNull()
    expect(parseBirthDate('1984-2-5')).toBeNull()
    expect(parseBirthDate(new Date('nope'))).toBeNull()
  })

  it('rejects dates that look well-formed but are not real', () => {
    expect(parseBirthDate('2026-02-30')).toBeNull()
    expect(parseBirthDate('2025-02-29')).toBeNull() // 2025 is not a leap year
    expect(parseBirthDate('2026-04-31')).toBeNull()
    expect(parseBirthDate('2026-13-01')).toBeNull()
    expect(parseBirthDate('2026-00-10')).toBeNull()
    expect(parseBirthDate('2024-02-29')).toEqual({ year: 2024, month: 2, day: 29 }) // leap: real
  })
})

describe('computeAgeYears — the boundary', () => {
  it('EXACTLY 18 on the 18th birthday → 18, not a minor', () => {
    expect(computeAgeYears('2008-06-15', at('2026-06-15'))).toBe(18)
    expect(isMinorSubject('2008-06-15', at('2026-06-15'))).toBe(false)
  })

  it('the DAY BEFORE the 18th birthday → 17, a minor', () => {
    expect(computeAgeYears('2008-06-15', at('2026-06-14'))).toBe(17)
    expect(isMinorSubject('2008-06-15', at('2026-06-14'))).toBe(true)
  })

  it('the day AFTER the 18th birthday → 18, not a minor', () => {
    expect(computeAgeYears('2008-06-15', at('2026-06-16'))).toBe(18)
    expect(isMinorSubject('2008-06-15', at('2026-06-16'))).toBe(false)
  })

  it('handles the month boundary (birthday next month, same day number)', () => {
    expect(computeAgeYears('2008-07-15', at('2026-06-15'))).toBe(17)
    expect(computeAgeYears('2008-05-15', at('2026-06-15'))).toBe(18)
  })

  it('handles a Feb-29 birthday across a non-leap year', () => {
    // Born 2008-02-29. In 2026 (non-leap) the 18th birthday effectively lands
    // on Mar 1: Feb 28 is still 17, Mar 1 is 18.
    expect(computeAgeYears('2008-02-29', at('2026-02-28'))).toBe(17)
    expect(isMinorSubject('2008-02-29', at('2026-02-28'))).toBe(true)
    expect(computeAgeYears('2008-02-29', at('2026-03-01'))).toBe(18)
    expect(isMinorSubject('2008-02-29', at('2026-03-01'))).toBe(false)
  })

  it('handles a Dec-31 / Jan-1 year boundary', () => {
    expect(computeAgeYears('2007-12-31', at('2025-12-30'))).toBe(17)
    expect(computeAgeYears('2007-12-31', at('2025-12-31'))).toBe(18)
    expect(computeAgeYears('2008-01-01', at('2025-12-31'))).toBe(17)
    expect(computeAgeYears('2008-01-01', at('2026-01-01'))).toBe(18)
  })

  it('a newborn is 0 and a minor', () => {
    expect(computeAgeYears('2026-08-19', at('2026-08-19'))).toBe(0)
    expect(isMinorSubject('2026-08-19', at('2026-08-19'))).toBe(true)
  })

  it('a FUTURE birth date is negative (honest), and fails closed as a minor', () => {
    expect(computeAgeYears('2030-01-01', at('2026-08-19'))).toBe(-4)
    expect(isMinorSubject('2030-01-01', at('2026-08-19'))).toBe(true)
  })

  it('the canonical native (1984-02-05) is an adult', () => {
    expect(isMinorSubject('1984-02-05', at('2026-08-19'))).toBe(false)
    expect(computeAgeYears('1984-02-05', at('2026-08-19'))).toBe(42)
  })

  it('returns null — NOT false — when the age cannot be computed', () => {
    expect(computeAgeYears(null)).toBeNull()
    expect(isMinorSubject(null)).toBeNull()
    expect(isMinorSubject('not-a-date')).toBeNull()
    // The distinction that matters: null is not falsy-equivalent to "adult".
    expect(isMinorSubject(null)).not.toBe(false)
  })
})

describe('utcCalendarDate', () => {
  it('reads the UTC calendar date, not the local one', () => {
    // 2026-06-15T23:30Z is still June 15 in UTC regardless of the host TZ.
    expect(utcCalendarDate(new Date('2026-06-15T23:30:00.000Z'))).toEqual({
      year: 2026,
      month: 6,
      day: 15,
    })
    expect(utcCalendarDate(new Date('2026-06-16T00:30:00.000Z'))).toEqual({
      year: 2026,
      month: 6,
      day: 16,
    })
  })
})
