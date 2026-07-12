/**
 * chart_facts_ayanamsha.test.ts — WP-1.3(f) / LCA-3 (ayanamsha reachability).
 *
 * The query_chart_facts-scoped resolver must make all SIX stored ayanamsha_id values reachable.
 * The pre-existing shared `normalizeAyanamsha` COLLAPSES true_chitra/true_citra -> lahiri, which
 * hid true_chitra's dataset. This resolver must NOT collapse any two distinct stored ayanamshas.
 */
import { describe, it, expect } from 'vitest'
import { resolveChartFactsAyanamsha } from '../tools/registry_bridge.js'

// The six ayanamsha_id values that actually exist in chart_facts (verified against prod).
const STORED = [
  'lahiri_chitrapaksha',
  'krishnamurti',
  'raman',
  'surya_siddhanta_classical',
  'true_chitra',
  'INVARIANT',
]

describe('resolveChartFactsAyanamsha — all 6 ayanamshas reachable', () => {
  it('defaults to lahiri_chitrapaksha when omitted', () => {
    expect(resolveChartFactsAyanamsha(undefined)).toBe('lahiri_chitrapaksha')
  })

  it('every stored ayanamsha_id resolves to ITSELF (no collapse)', () => {
    for (const id of STORED) {
      expect(resolveChartFactsAyanamsha(id)).toBe(id)
    }
  })

  it('true_chitra is NOT collapsed to lahiri (the LCA-3 bug)', () => {
    expect(resolveChartFactsAyanamsha('true_chitra')).toBe('true_chitra')
    expect(resolveChartFactsAyanamsha('true_citra')).toBe('true_chitra')
  })

  it('the six stored values map to six DISTINCT canonical targets (nothing merges)', () => {
    const resolved = new Set(STORED.map(resolveChartFactsAyanamsha))
    expect(resolved.size).toBe(STORED.length)
  })

  it('convenience aliases map without collapsing distinct ayanamshas', () => {
    expect(resolveChartFactsAyanamsha('lahiri')).toBe('lahiri_chitrapaksha')
    expect(resolveChartFactsAyanamsha('kp')).toBe('krishnamurti')
    expect(resolveChartFactsAyanamsha('surya_siddhanta')).toBe('surya_siddhanta_classical')
  })

  it('unknown id passes through unchanged (handler then returns honest-empty, not lahiri)', () => {
    expect(resolveChartFactsAyanamsha('not_a_real_ayanamsha')).toBe('not_a_real_ayanamsha')
  })
})
