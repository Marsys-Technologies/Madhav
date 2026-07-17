import { describe, it, expect } from 'vitest'
import { parseDate, toIsoDate, addDays, daysBetween, isWithinDays, clampDate } from '../dates'

describe('dates', () => {
  it('parseDate/toIsoDate round-trip', () => {
    const d = parseDate('2025-05-15')
    expect(toIsoDate(d)).toBe('2025-05-15')
  })

  it('addDays', () => {
    expect(toIsoDate(addDays(parseDate('2025-01-01'), 30))).toBe('2025-01-31')
    expect(toIsoDate(addDays(parseDate('2025-01-01'), -1))).toBe('2024-12-31')
  })

  it('daysBetween is signed', () => {
    expect(daysBetween(parseDate('2025-01-01'), parseDate('2025-01-31'))).toBe(30)
    expect(daysBetween(parseDate('2025-01-31'), parseDate('2025-01-01'))).toBe(-30)
  })

  it('isWithinDays respects the window inclusively both directions', () => {
    const center = parseDate('2025-05-15')
    expect(isWithinDays(center, parseDate('2025-06-29'), 45)).toBe(true) // exactly 45
    expect(isWithinDays(center, parseDate('2025-06-30'), 45)).toBe(false) // 46
    expect(isWithinDays(center, parseDate('2025-04-01'), 45)).toBe(true) // 44 days prior
  })

  it('clampDate', () => {
    const min = parseDate('2000-01-01')
    const max = parseDate('2030-01-01')
    expect(toIsoDate(clampDate(parseDate('1990-01-01'), min, max))).toBe('2000-01-01')
    expect(toIsoDate(clampDate(parseDate('2040-01-01'), min, max))).toBe('2030-01-01')
    expect(toIsoDate(clampDate(parseDate('2010-01-01'), min, max))).toBe('2010-01-01')
  })
})
