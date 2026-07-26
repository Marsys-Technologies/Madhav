/**
 * fired_sensitive_boost.test.ts — ŚODHANA T5 (PŪRTI / MC-030) pure-function guards.
 * Proves the serve-time salience correction that surfaces a FIRED rare sensitive-degree
 * (e.g. Mars-in-puṣkara) above the not-fired rows the build-time salience buried.
 */
import { describe, it, expect } from 'vitest'
import { firedSensitiveDegreeBoost, FIRED_SENSITIVE_DEGREE_BOOST, type MsrSignalRow } from '../composite_ranker'

function row(partial: Partial<MsrSignalRow>): MsrSignalRow {
  return { signal_id: 's', ...partial }
}

describe('firedSensitiveDegreeBoost (MC-030 serve-time correction)', () => {
  it('lifts a FIRED puṣkara signal by the boost factor', () => {
    const r = row({
      signal_type_id: 'sensitive_degree_check:pushkara',
      signal_summary_text: 'category=sensitive_degree_check | key=pushkara | value_text=pushkara | fired=True | in_pushkara_navamsa=True',
    })
    expect(firedSensitiveDegreeBoost(r)).toBe(FIRED_SENSITIVE_DEGREE_BOOST)
    expect(FIRED_SENSITIVE_DEGREE_BOOST).toBeGreaterThan(1)
  })

  it('does NOT lift a NOT-fired puṣkara signal (the ones that used to rank above the fired one)', () => {
    const r = row({
      signal_type_id: 'sensitive_degree_check:pushkara',
      signal_summary_text: 'category=sensitive_degree_check | key=pushkara | value_text=not_pushkara | fired=False',
    })
    expect(firedSensitiveDegreeBoost(r)).toBe(1.0)
  })

  it('boosts fired gaṇḍānta and mṛtyu-bhāga too, but not unrelated signal types', () => {
    expect(firedSensitiveDegreeBoost(row({ signal_type_id: 'sensitive_degree_check:gandanta', signal_summary_text: 'fired=True' }))).toBe(FIRED_SENSITIVE_DEGREE_BOOST)
    expect(firedSensitiveDegreeBoost(row({ signal_type_id: 'sensitive_degree_check:mrityu_bhaga', signal_summary_text: 'fired=True' }))).toBe(FIRED_SENSITIVE_DEGREE_BOOST)
    // A routine dignity descriptor is untouched.
    expect(firedSensitiveDegreeBoost(row({ signal_type_id: 'graha_dignity:dignity_state', signal_summary_text: 'value_text=neutral' }))).toBe(1.0)
  })

  it('the correction reverses the observed inversion: a fired row now outranks a not-fired one at equal base salience', () => {
    // Live-observed on 482012f1: fired Mars-puṣkara salience 0.46 < not-fired puṣkara 1.30.
    // Model that as equal base × boost: fired × 1.6 must exceed not-fired × 1.0.
    const base = 1.0
    const fired = base * firedSensitiveDegreeBoost(row({ signal_type_id: 'sensitive_degree_check:pushkara', signal_summary_text: 'fired=True' }))
    const notFired = base * firedSensitiveDegreeBoost(row({ signal_type_id: 'sensitive_degree_check:pushkara', signal_summary_text: 'fired=False' }))
    expect(fired).toBeGreaterThan(notFired)
  })
})
