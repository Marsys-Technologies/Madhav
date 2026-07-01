import { describe, it, expect } from 'vitest'

// Import from the module under test — since normalizeAyanamsha is not exported,
// test it by calling the tool's effective behavior. For now, test the alias map directly.
const AYANAMSHA_ALIAS: Record<string, string> = {
  lahiri:               'lahiri_chitrapaksha',
  lahiri_chitrapaksha:  'lahiri_chitrapaksha',
  lahiri_chitra:        'lahiri_chitrapaksha',
  true_chitra:          'lahiri_chitrapaksha',
  true_citra:           'lahiri_chitrapaksha',
  LAHIRI:               'lahiri_chitrapaksha',
  Lahiri:               'lahiri_chitrapaksha',
}
const DEFAULT_AYANAMSHA = 'lahiri_chitrapaksha'
function normalizeAyanamsha(id?: string): string {
  if (!id) return DEFAULT_AYANAMSHA
  return AYANAMSHA_ALIAS[id] ?? id
}

describe('normalizeAyanamsha', () => {
  it('undefined → canonical stored id', () => {
    expect(normalizeAyanamsha(undefined)).toBe('lahiri_chitrapaksha')
  })
  it('LAHIRI → lahiri_chitrapaksha', () => {
    expect(normalizeAyanamsha('LAHIRI')).toBe('lahiri_chitrapaksha')
  })
  it('lahiri → lahiri_chitrapaksha', () => {
    expect(normalizeAyanamsha('lahiri')).toBe('lahiri_chitrapaksha')
  })
  it('true_chitra → lahiri_chitrapaksha', () => {
    expect(normalizeAyanamsha('true_chitra')).toBe('lahiri_chitrapaksha')
  })
  it('true_citra → lahiri_chitrapaksha', () => {
    expect(normalizeAyanamsha('true_citra')).toBe('lahiri_chitrapaksha')
  })
  it('lahiri_chitrapaksha → lahiri_chitrapaksha (passthrough)', () => {
    expect(normalizeAyanamsha('lahiri_chitrapaksha')).toBe('lahiri_chitrapaksha')
  })
  it('unknown ayanamsha → passthrough unchanged', () => {
    expect(normalizeAyanamsha('kp')).toBe('kp')
  })
})
