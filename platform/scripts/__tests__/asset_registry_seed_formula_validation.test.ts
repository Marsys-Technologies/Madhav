import { readFileSync } from 'node:fs'

import { describe, expect, it } from 'vitest'

import { ASSETS, validateFormulas } from '../seed/asset_registry_seed'

describe('asset_registry_seed formula validation', () => {
  const kpSublordDivision = ASSETS.find(
    (asset) => asset.asset_id === 'bg_kp_sublord_division',
  )!

  it('accepts the governed 27*9+6=249 KP sub-lord derivation', () => {
    expect(kpSublordDivision.expected_volume_formula).toBe(
      'NAKSHATRAS * VIMSHOTTARI_LORDS + RASHI_BOUNDARY_SPLITS',
    )
    expect(27 * 9 + 6).toBe(249)
    expect(() => validateFormulas([kpSublordDivision], [])).not.toThrow()
  })

  it('declares both named factors and their governed values', () => {
    const source = readFileSync(
      new URL('../seed/asset_registry_seed.ts', import.meta.url),
      'utf8',
    )

    expect(source).toMatch(/'VIMSHOTTARI_LORDS'/)
    expect(source).toMatch(/VIMSHOTTARI_LORDS:\s*9/)
    expect(source).toMatch(/'RASHI_BOUNDARY_SPLITS'/)
    expect(source).toMatch(/RASHI_BOUNDARY_SPLITS:\s*6/)
  })

  it('refuses unknown, unsafe, and nonpositive formula mutations', () => {
    expect(() => validateFormulas([{
      ...kpSublordDivision,
      expected_volume_formula: 'NAKSHATRAS * UNKNOWN_LORDS + RASHI_BOUNDARY_SPLITS',
    }], [])).toThrow(/Unknown variables|undeclared coefficient/)
    expect(() => validateFormulas([{
      ...kpSublordDivision,
      expected_volume_formula: 'NAKSHATRAS; process.exit(1)',
    }], [])).toThrow(/disallowed characters/)
    expect(() => validateFormulas([{
      ...kpSublordDivision,
      expected_volume_formula: 'RASHI_BOUNDARY_SPLITS - RASHI_BOUNDARY_SPLITS',
    }], [])).toThrow(/non-positive/)
  })
})
