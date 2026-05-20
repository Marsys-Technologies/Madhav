/**
 * DMS formatter unit tests — edge cases required by AC.4C4S2.4
 * Phase: 4C-4-S2 (Item 4)
 */
import { describe, it, expect } from 'vitest'
import { formatDMS, formatDMSShort, decimalToDMS, lonWithinSign } from '@/lib/format/dms'

describe('decimalToDMS', () => {
  it('converts a typical sidereal longitude correctly', () => {
    // 4.389° → 04°23'20"
    const { degrees, minutes, seconds } = decimalToDMS(4.389)
    expect(degrees).toBe(4)
    expect(minutes).toBe(23)
    expect(seconds).toBe(20)
  })

  it('handles 0 degrees', () => {
    const { degrees, minutes, seconds } = decimalToDMS(0)
    expect(degrees).toBe(0)
    expect(minutes).toBe(0)
    expect(seconds).toBe(0)
  })

  it('wraps 360 degrees to 0', () => {
    const { degrees, minutes, seconds } = decimalToDMS(360)
    expect(degrees).toBe(0)
    expect(minutes).toBe(0)
    expect(seconds).toBe(0)
  })

  it('wraps negative degrees to positive', () => {
    // -5 → 355
    const { degrees } = decimalToDMS(-5)
    expect(degrees).toBe(355)
  })

  it('wraps values > 360', () => {
    // 365 → 5
    const { degrees } = decimalToDMS(365)
    expect(degrees).toBe(5)
  })
})

describe('formatDMS', () => {
  it('formats a typical longitude as DD°MM\'SS"', () => {
    // 18.85° → 18°51'00"
    expect(formatDMS(18.85)).toBe('18°51\'00"')
  })

  it('pads single-digit values with leading zeros', () => {
    expect(formatDMS(4.0)).toBe('04°00\'00"')
  })

  it('handles 0 correctly', () => {
    expect(formatDMS(0)).toBe('00°00\'00"')
  })

  it('handles 360 (wraps to 0)', () => {
    expect(formatDMS(360)).toBe('00°00\'00"')
  })
})

describe('formatDMSShort', () => {
  it('formats as DD°MM\' (no seconds)', () => {
    expect(formatDMSShort(4.389)).toBe('04°23\'')
  })

  it('handles 0', () => {
    expect(formatDMSShort(0)).toBe('00°00\'')
  })
})

describe('lonWithinSign', () => {
  it('returns within-sign portion for Mesha (0–30°)', () => {
    expect(lonWithinSign(4.389)).toBeCloseTo(4.389, 3)
  })

  it('returns within-sign for Vrishabha (30–60°)', () => {
    expect(lonWithinSign(32.0)).toBeCloseTo(2.0, 3)
  })

  it('returns within-sign for Kanya (150–180°)', () => {
    expect(lonWithinSign(177.0)).toBeCloseTo(27.0, 3)
  })

  it('handles 0', () => {
    expect(lonWithinSign(0)).toBe(0)
  })

  it('handles exactly on sign boundary', () => {
    // 30.0 = start of Vrishabha → within sign = 0
    expect(lonWithinSign(30)).toBeCloseTo(0, 3)
  })

  it('handles 360 (wraps correctly)', () => {
    expect(lonWithinSign(360)).toBe(0)
  })
})
