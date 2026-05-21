/**
 * sade_sati_cycles.test.ts
 *
 * COV-S10 unit tests for sade_sati_cycles migration + types.
 * Tests the TypeScript type contracts and phase classification logic.
 * No DB connection required.
 *
 * Audit reference: §G.10 of CAPABILITY_COVERAGE_AND_PERFORMANCE_AUDIT_v1_0.md (v1.2)
 */

import { describe, it, expect } from 'vitest'
import type { SadeSatiCycle, SadeSatiCycleInsert, SadeSatiPhase } from '@/lib/types/sade_sati_cycles'
import { SADE_SATI_PHASE_MAP } from '@/lib/types/sade_sati_cycles'

describe('COV-S10 — sade_sati_cycles: type contracts and phase classification', () => {
  it('SADE_SATI_PHASE_MAP covers Capricorn/Aquarius/Pisces for Aquarius natal Moon', () => {
    expect(SADE_SATI_PHASE_MAP['Capricorn']).toBeDefined()
    expect(SADE_SATI_PHASE_MAP['Aquarius']).toBeDefined()
    expect(SADE_SATI_PHASE_MAP['Pisces']).toBeDefined()
  })

  it('phase map assigns correct severity weights (peak=1.0, rising/setting=0.7)', () => {
    expect(SADE_SATI_PHASE_MAP['Capricorn']?.severity_weight).toBe(0.7)
    expect(SADE_SATI_PHASE_MAP['Aquarius']?.severity_weight).toBe(1.0)
    expect(SADE_SATI_PHASE_MAP['Pisces']?.severity_weight).toBe(0.7)
  })

  it('phase map assigns correct phase labels', () => {
    expect(SADE_SATI_PHASE_MAP['Capricorn']?.phase).toBe('rising')
    expect(SADE_SATI_PHASE_MAP['Aquarius']?.phase).toBe('peak')
    expect(SADE_SATI_PHASE_MAP['Pisces']?.phase).toBe('setting')
  })

  it('SadeSatiCycleInsert type is satisfied by a valid fixture row', () => {
    const fixture: SadeSatiCycleInsert = {
      native_id: 'abhisek_mohanty',
      start_date: '2017-06-21',
      end_date: '2020-01-24',
      phase: 'peak',
      moon_sign: 'Aquarius',
      saturn_sign: 'Aquarius',
      severity_weight: 1.0,
      computation_source: 'ephemeris_daily',
    }
    expect(fixture.native_id).toBe('abhisek_mohanty')
    expect(fixture.moon_sign).toBe('Aquarius')
    expect(fixture.severity_weight).toBe(1.0)
  })

  it('SadeSatiPhase union covers all three phases', () => {
    const validPhases: SadeSatiPhase[] = ['rising', 'peak', 'setting']
    expect(validPhases).toHaveLength(3)
    expect(validPhases).toContain('rising')
    expect(validPhases).toContain('peak')
    expect(validPhases).toContain('setting')
  })

  it('SADE_SATI_PHASE_MAP has no entries for non-Sade-Sati signs', () => {
    const nonSadeSatiSigns = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra', 'Scorpio', 'Sagittarius']
    for (const sign of nonSadeSatiSigns) {
      expect(SADE_SATI_PHASE_MAP[sign]).toBeUndefined()
    }
  })
})
