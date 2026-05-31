/**
 * Tests for NewClientForm schema helpers — parseBirthDateUi + derivePreferredName
 */

import { describe, it, expect } from 'vitest'
import {
  parseBirthDateUi,
  derivePreferredName,
} from '../form_schema'

// ─── parseBirthDateUi ─────────────────────────────────────────────────────────

describe('parseBirthDateUi', () => {
  it('accepts "05 02 1984" (DD MM YYYY) and returns "1984-02-05"', () => {
    expect(parseBirthDateUi('05 02 1984')).toBe('1984-02-05')
  })

  it('accepts "5 2 1984" (D M YYYY) and returns "1984-02-05"', () => {
    expect(parseBirthDateUi('5 2 1984')).toBe('1984-02-05')
  })

  it('accepts "31 12 2000" and returns "2000-12-31"', () => {
    expect(parseBirthDateUi('31 12 2000')).toBe('2000-12-31')
  })

  it('accepts "01 01 1900" and returns "1900-01-01"', () => {
    expect(parseBirthDateUi('01 01 1900')).toBe('1900-01-01')
  })

  it('rejects empty string — returns null', () => {
    expect(parseBirthDateUi('')).toBeNull()
  })

  it('rejects ISO format "1984-02-05" — returns null (wrong separator)', () => {
    expect(parseBirthDateUi('1984-02-05')).toBeNull()
  })

  it('rejects "32 01 2000" — day out of range', () => {
    expect(parseBirthDateUi('32 01 2000')).toBeNull()
  })

  it('rejects "01 13 2000" — month out of range', () => {
    expect(parseBirthDateUi('01 13 2000')).toBeNull()
  })

  it('rejects "abc def ghi"', () => {
    expect(parseBirthDateUi('abc def ghi')).toBeNull()
  })

  it('rejects "05-02-1984" (dash separator)', () => {
    expect(parseBirthDateUi('05-02-1984')).toBeNull()
  })

  it('rejects "05/02/1984" (slash separator)', () => {
    expect(parseBirthDateUi('05/02/1984')).toBeNull()
  })
})

// ─── derivePreferredName ──────────────────────────────────────────────────────

describe('derivePreferredName', () => {
  it('returns first word of full_name when preferred_name is blank', () => {
    expect(derivePreferredName('Abhisek Mohanty', '')).toBe('Abhisek')
  })

  it('returns first word when preferred_name is whitespace only', () => {
    expect(derivePreferredName('Abhisek Mohanty', '   ')).toBe('Abhisek')
  })

  it('returns preferred_name as-is when provided', () => {
    expect(derivePreferredName('Abhisek Mohanty', 'Abhi')).toBe('Abhi')
  })

  it('returns full_name verbatim if it is one word and preferred_name is blank', () => {
    expect(derivePreferredName('Abhisek', '')).toBe('Abhisek')
  })

  it('returns empty string when both are empty', () => {
    expect(derivePreferredName('', '')).toBe('')
  })
})

