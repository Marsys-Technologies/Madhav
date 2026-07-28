/**
 * SAMĪKṢĀ lifecycle eyebrow labels — unit — PB-3 lane L-2 (§6.9).
 */
import { describe, it, expect } from 'vitest'
import { lifecycleEyebrow, lifecycleSuffix } from '@/lib/pariprashna/samiksha/lifecycle_label'

describe('lifecycleSuffix / lifecycleEyebrow', () => {
  it('maps the §6.9 progression', () => {
    expect(lifecycleSuffix('detected')).toBe('AWAITING CONFIRMATION')
    expect(lifecycleSuffix('open')).toBe('WINDOW OPEN')
    expect(lifecycleSuffix('open', { closingSoon: true })).toBe('WINDOW CLOSING')
    expect(lifecycleSuffix('window_closed')).toBe('AWAITING OUTCOME')
  })
  it('resolves the outcome word (§6.9 CONFIRMED / MISSED / MIXED)', () => {
    expect(lifecycleSuffix('outcome_recorded', { outcome: 'happened' })).toBe('RESOLVED — CONFIRMED')
    expect(lifecycleSuffix('outcome_recorded', { outcome: 'did_not_happen' })).toBe('RESOLVED — MISSED')
    expect(lifecycleSuffix('outcome_recorded', { outcome: 'partial' })).toBe('RESOLVED — MIXED')
    expect(lifecycleSuffix('unverifiable')).toBe('RESOLVED — UNVERIFIABLE')
  })
  it('lapsed states are non-shameful, factual (W-2)', () => {
    expect(lifecycleSuffix('lapsed')).toBe('LAPSED')
    expect(lifecycleSuffix('lapsed_unconfirmed')).toBe('LAPSED — UNCONFIRMED')
  })
  it('full eyebrow carries the TIME-INDEXED READING prefix', () => {
    expect(lifecycleEyebrow('open')).toBe('TIME-INDEXED READING · WINDOW OPEN')
  })
})
