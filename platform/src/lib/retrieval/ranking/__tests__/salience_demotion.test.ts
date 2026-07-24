/**
 * salience_demotion.test.ts — WP-1.2(d) (LCA-9b-2 serving cap) unit tests.
 * Pure functions over hand-built rows — no DB.
 */
import { describe, it, expect } from 'vitest'
import {
  isDescriptiveOrPerVarga,
  demoteSignatureTier,
  demoteSignatureTiers,
  DEMOTED_TIER,
} from '../salience_demotion'

describe('WP-1.2(d) salience demotion — descriptive/per-varga barred from major/chart_defining', () => {
  it('flags descriptive almanac fact_keys (pakshi, presiding_deity, akshara, yoni, symbol)', () => {
    for (const fk of ['pakshi', 'presiding_deity', 'akshara', 'yoni', 'symbol']) {
      expect(isDescriptiveOrPerVarga({ configuration_jsonb: { fact_key: fk } })).toBe(true)
    }
  })

  it('flags per-varga granular data (varga beyond D1)', () => {
    expect(isDescriptiveOrPerVarga({ configuration_jsonb: { varga: 'D108', fact_key: 'dignity_state' } })).toBe(true)
    expect(isDescriptiveOrPerVarga({ configuration_jsonb: { varga: 'D9', fact_key: 'dignity_state' } })).toBe(true)
  })

  it('does NOT flag D1 rasi-chart data or non-descriptive keys', () => {
    expect(isDescriptiveOrPerVarga({ configuration_jsonb: { varga: 'D1', fact_key: 'dignity_state' } })).toBe(false)
    expect(isDescriptiveOrPerVarga({ configuration_jsonb: { fact_key: 'raja_yoga' } })).toBe(false)
    expect(isDescriptiveOrPerVarga({ configuration_jsonb: null })).toBe(false)
  })

  it('flags per-varga / descriptive via signal_type_id token', () => {
    expect(isDescriptiveOrPerVarga({ signal_type_id: 'graha_dignity_per_varga:dignity_state' })).toBe(true)
    expect(isDescriptiveOrPerVarga({ signal_type_id: 'graha_nakshatra_join:pakshi' })).toBe(true)
  })

  it('caps a chart_defining per-varga signal down to supporting, disclosing the demotion', () => {
    const row = {
      signal_id: 'x', signature_tier: 'chart_defining',
      configuration_jsonb: { varga: 'D108', fact_key: 'dignity_state' },
    }
    const out = demoteSignatureTier(row)
    expect(out.signature_tier).toBe(DEMOTED_TIER)
    expect(out.signature_tier_demoted_from).toBe('chart_defining')
    expect(out.signature_tier_demotion_reason).toContain('not served at major/chart_defining tier')
    expect(out.signature_tier_demotion_reason).not.toContain('WP-1.2d')
  })

  it('caps a major descriptive signal (pakshi) but leaves a real major yoga untouched', () => {
    const pakshi = { signal_id: 'p', signature_tier: 'major', configuration_jsonb: { fact_key: 'pakshi' } }
    const yoga = { signal_id: 'y', signature_tier: 'major', configuration_jsonb: { fact_key: 'raja_yoga' } }
    const [dp, dy] = demoteSignatureTiers([pakshi, yoga])
    expect(dp.signature_tier).toBe(DEMOTED_TIER)
    expect(dy.signature_tier).toBe('major') // untouched
    expect(dy).toBe(yoga) // same reference — no needless copy
  })

  it('never touches supporting/background rows even if descriptive', () => {
    const row = { signal_id: 'b', signature_tier: 'supporting', configuration_jsonb: { fact_key: 'pakshi' } }
    expect(demoteSignatureTier(row).signature_tier).toBe('supporting')
  })
})
