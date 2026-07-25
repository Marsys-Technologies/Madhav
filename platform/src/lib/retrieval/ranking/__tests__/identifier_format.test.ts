/**
 * identifier_format.test.ts — EL-32 + EL-44 shared humanizer/canonicalizer
 * ============================================================================
 */

import { describe, it, expect } from 'vitest'
import {
  canonicalGraha,
  displayGraha,
  displayVarga,
  ordinalHouse,
  humanizeMachineKey,
  humanizeSnakeLabel,
} from '../identifier_format'

describe('canonicalGraha (EL-32 canonical-output pass)', () => {
  it('resolves every alias variant to the SAME full-uppercase canonical form', () => {
    expect(canonicalGraha('SA')).toBe('SATURN')
    expect(canonicalGraha('SAT')).toBe('SATURN')
    expect(canonicalGraha('saturn')).toBe('SATURN')
    expect(canonicalGraha('SATURN')).toBe('SATURN')
  })

  it('returns null rather than inventing a graha for an unrecognized token', () => {
    expect(canonicalGraha('NOT_A_GRAHA')).toBeNull()
    expect(canonicalGraha(null)).toBeNull()
  })
})

describe('displayGraha', () => {
  it('renders Title-case prose form regardless of input alias', () => {
    expect(displayGraha('SA')).toBe('Saturn')
    expect(displayGraha('SAT')).toBe('Saturn')
    expect(displayGraha('SATURN')).toBe('Saturn')
  })
})

describe('displayVarga', () => {
  it('names the classical Sanskrit term alongside the D-code', () => {
    expect(displayVarga('D2')).toMatch(/Horā/)
    expect(displayVarga('D2')).toMatch(/D2/)
    expect(displayVarga('D9')).toMatch(/Navāṃśa/)
  })

  it('falls back to the bare code for an unrecognized varga rather than fabricating a name', () => {
    expect(displayVarga('D999')).toBe('D999')
  })
})

describe('ordinalHouse', () => {
  it('formats the charter\'s own worked example: house 7 -> "7th house"', () => {
    expect(ordinalHouse(7)).toBe('7th house')
  })
  it('handles the 1st/2nd/3rd/11th/12th special-cases correctly', () => {
    expect(ordinalHouse(1)).toBe('1st house')
    expect(ordinalHouse(2)).toBe('2nd house')
    expect(ordinalHouse(3)).toBe('3rd house')
    expect(ordinalHouse(11)).toBe('11th house')
    expect(ordinalHouse(12)).toBe('12th house')
  })
})

describe('humanizeMachineKey — the charter\'s own worked example', () => {
  it('"Saturn_in_H7" -> "Saturn in the 7th house"', () => {
    expect(humanizeMachineKey('Saturn_in_H7')).toBe('Saturn in the 7th house')
  })

  it('"D2_SUN" (L1 fact_subject shape) -> "Sun in Horā (D2)"', () => {
    expect(humanizeMachineKey('D2_SUN')).toBe('Sun in Horā (D2)')
  })

  it('a bare graha alias resolves to its display name', () => {
    expect(humanizeMachineKey('SAT')).toBe('Saturn')
  })

  it('never fabricates a gloss for an unrecognized shape — returns it unchanged', () => {
    expect(humanizeMachineKey('totally_unknown_key_123')).toBe('totally_unknown_key_123')
  })
})

describe('humanizeSnakeLabel', () => {
  it('de-snake-cases without reinterpreting the content', () => {
    expect(humanizeSnakeLabel('GAJAKESARI_YOGA')).toBe('Gajakesari Yoga')
    expect(humanizeSnakeLabel('nabhasa_akrti')).toBe('Nabhasa Akrti')
  })
})
