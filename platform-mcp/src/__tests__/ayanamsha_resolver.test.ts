import { describe, expect, it } from 'vitest'
import { resolveChartFactsAyanamsha } from '../lib/ayanamsha.js'

describe('resolveChartFactsAyanamsha', () => {
  it('keeps distinct stored schools reachable', () => {
    expect(resolveChartFactsAyanamsha('true_chitra')).toBe('true_chitra')
    expect(resolveChartFactsAyanamsha('true_citra')).toBe('true_chitra')
    expect(resolveChartFactsAyanamsha('krishnamurti')).toBe('krishnamurti')
    expect(resolveChartFactsAyanamsha('raman')).toBe('raman')
  })

  it('normalizes only convenience aliases and preserves unknown values', () => {
    expect(resolveChartFactsAyanamsha('LAHIRI')).toBe('lahiri_chitrapaksha')
    expect(resolveChartFactsAyanamsha('kp')).toBe('krishnamurti')
    expect(resolveChartFactsAyanamsha('unrecognized_school')).toBe('unrecognized_school')
  })
})
