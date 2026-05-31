/**
 * Tests for NewClientForm schema extensions — [BUILD-ORCH-D-S1]
 *
 * Acceptance criteria:
 *   - DD MM YYYY format accepted and converted to YYYY-MM-DD
 *   - Malformed date strings rejected
 *   - preferred_name defaults to first word of full_name when blank
 *   - timezone_id required; missing → validation error
 *   - birth_date_ui accepts single-digit day/month with space separator
 */

import { describe, it, expect } from 'vitest'
import {
  parseBirthDateUi,
  validateFormSchema,
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

// ─── validateFormSchema ───────────────────────────────────────────────────────

describe('validateFormSchema — timezone_id required', () => {
  const base = {
    full_name: 'Test Native',
    preferred_name: '',
    gender: 'male' as const,
    birth_date_ui: '05 02 1984',
    birth_time: '10:43',
    birth_place: 'Bhubaneswar, Odisha',
    latitude: '20.2961',
    longitude: '85.8245',
    timezone_id: 'Asia/Kolkata',
    ayanamshas: ['lahiri'],
  }

  it('passes with valid input including timezone_id', () => {
    const result = validateFormSchema(base)
    expect(result.ok).toBe(true)
    if (result.ok) {
      expect(result.birth_date).toBe('1984-02-05')
      expect(result.preferred_name).toBe('Test')
    }
  })

  it('fails when timezone_id is missing', () => {
    const result = validateFormSchema({ ...base, timezone_id: '' })
    expect(result.ok).toBe(false)
    if (!result.ok) {
      expect(result.errors).toContain('timezone_id')
    }
  })

  it('fails when birth_date_ui is malformed', () => {
    const result = validateFormSchema({ ...base, birth_date_ui: '1984-02-05' })
    expect(result.ok).toBe(false)
    if (!result.ok) {
      expect(result.errors).toContain('birth_date_ui')
    }
  })

  it('derives preferred_name from full_name when blank', () => {
    const result = validateFormSchema({ ...base, preferred_name: '' })
    expect(result.ok).toBe(true)
    if (result.ok) {
      expect(result.preferred_name).toBe('Test')
    }
  })

  it('uses provided preferred_name when non-blank', () => {
    const result = validateFormSchema({ ...base, preferred_name: 'Tester' })
    expect(result.ok).toBe(true)
    if (result.ok) {
      expect(result.preferred_name).toBe('Tester')
    }
  })
})
