/**
 * confidence/__tests__/type_claim.test.ts — one test per PPR-03 confidence
 * type, proving correct assignment from a realistic real-shaped input (lane
 * G3-C).
 */
import { describe, it, expect } from 'vitest'

import { typeClaimConfidence, wasClassicalSourceConsulted, CLASSICAL_PRIOR_BEARING_TOOL_NAMES, TYPING_BASIS } from '../type_claim'
import { evaluateEmpiricalCalibrationGate } from '../activation_gate'

const CLOSED_GATE = evaluateEmpiricalCalibrationGate({ sampleSize: null })
const OPEN_GATE = evaluateEmpiricalCalibrationGate({ sampleSize: 100 })

describe('typeClaimConfidence — one real-shaped fixture per PPR-03 type', () => {
  it('deterministic_fact: an L1-layer citation (a direct chart_facts reference)', () => {
    const entry = typeClaimConfidence({
      ref: 'SIG.MSR.001',
      layer: 'L1',
      calibrationConsulted: false,
      calibrationGate: CLOSED_GATE,
      classicalConsulted: false,
    })
    expect(entry.confidence_type).toBe('deterministic_fact')
    expect(entry.basis).toBe(TYPING_BASIS.L1_FACT_LAYER)
  })

  it('structural_prior: an L2.5-layer citation (an MSR/Bodha structural signal) with no calibration or classical signal in play', () => {
    const entry = typeClaimConfidence({
      ref: 'SIG.MSR.042',
      layer: 'L2.5',
      calibrationConsulted: false,
      calibrationGate: CLOSED_GATE,
      classicalConsulted: false,
    })
    expect(entry.confidence_type).toBe('structural_prior')
    expect(entry.basis).toBe(TYPING_BASIS.L2_5_STRUCTURAL_SIGNAL)
  })

  it('classical_prior: a turn where a real classical-text capability (classical_attribution_lookup) was consulted', () => {
    expect(wasClassicalSourceConsulted(['classical_attribution_lookup'])).toBe(true)
    const entry = typeClaimConfidence({
      ref: 'SIG.MSR.011',
      layer: 'L2.5',
      calibrationConsulted: false,
      calibrationGate: CLOSED_GATE,
      classicalConsulted: true,
    })
    expect(entry.confidence_type).toBe('classical_prior')
    expect(entry.basis).toBe(TYPING_BASIS.CLASSICAL_SOURCE_CONSULTED)
  })

  // ── G3BC hardening defect 4 ──────────────────────────────────────────────
  // The emitted `basis` string itself (not just a symbolic reference to it)
  // must disclose the turn-scoping — a downstream reader of the PERSISTED
  // receipt only ever sees this literal value, never this module's own
  // header comment. Asserting the literal (not just `TYPING_BASIS.
  // CLASSICAL_SOURCE_CONSULTED`, which would pass even if the constant
  // regressed back to the un-scoped wording) is the actual defect-4 proof.
  it("defect 4 fix: classical_prior's basis literally says 'this_turn', not the old ambiguous 'classical_source_consulted'", () => {
    const entry = typeClaimConfidence({
      ref: 'SIG.MSR.011',
      layer: 'L2.5',
      calibrationConsulted: false,
      calibrationGate: CLOSED_GATE,
      classicalConsulted: true,
    })
    expect(entry.basis).toBe('classical_source_consulted_this_turn')
    expect(entry.basis).not.toBe('classical_source_consulted')
  })

  it('empirically_calibrated: calibration consulted AND the real activation gate is open', () => {
    const entry = typeClaimConfidence({
      ref: 'SIG.MSR.077',
      layer: 'L2.5',
      calibrationConsulted: true,
      calibrationGate: OPEN_GATE,
      classicalConsulted: false,
    })
    expect(entry.confidence_type).toBe('empirically_calibrated')
    expect(entry.basis).toBe(TYPING_BASIS.CALIBRATION_GATE_OPEN)
  })

  it('empirically_calibrated is NEVER assigned when calibration was consulted but the gate is closed (PPR-03\'s core rule) — falls through to structural_prior', () => {
    const entry = typeClaimConfidence({
      ref: 'SIG.MSR.077',
      layer: 'L2.5',
      calibrationConsulted: true,
      calibrationGate: CLOSED_GATE,
      classicalConsulted: false,
    })
    expect(entry.confidence_type).not.toBe('empirically_calibrated')
    expect(entry.confidence_type).toBe('structural_prior')
  })

  it('unresolved: no real detector fires (an unrecognized layer, no calibration or classical signal)', () => {
    const entry = typeClaimConfidence({
      ref: 'SIG.MSR.099',
      layer: 'unknown_layer',
      calibrationConsulted: false,
      calibrationGate: CLOSED_GATE,
      classicalConsulted: false,
    })
    expect(entry.confidence_type).toBe('unresolved')
    expect(entry.basis).toBe(TYPING_BASIS.UNRESOLVED_NO_DETECTOR)
  })
})

describe('typeClaimConfidence — priority ordering', () => {
  it('L1 layer wins over an open calibration gate (a direct fact citation is never demoted to a calibration claim)', () => {
    const entry = typeClaimConfidence({
      ref: 'SIG.MSR.001',
      layer: 'L1',
      calibrationConsulted: true,
      calibrationGate: OPEN_GATE,
      classicalConsulted: true,
    })
    expect(entry.confidence_type).toBe('deterministic_fact')
  })

  it('an open calibration gate wins over classical consultation', () => {
    const entry = typeClaimConfidence({
      ref: 'SIG.MSR.001',
      layer: 'L2.5',
      calibrationConsulted: true,
      calibrationGate: OPEN_GATE,
      classicalConsulted: true,
    })
    expect(entry.confidence_type).toBe('empirically_calibrated')
  })
})

describe('CLASSICAL_PRIOR_BEARING_TOOL_NAMES', () => {
  it('is a real, non-empty, deduplicated list', () => {
    expect(CLASSICAL_PRIOR_BEARING_TOOL_NAMES.length).toBeGreaterThan(0)
    expect(new Set(CLASSICAL_PRIOR_BEARING_TOOL_NAMES).size).toBe(CLASSICAL_PRIOR_BEARING_TOOL_NAMES.length)
  })

  it('wasClassicalSourceConsulted is false when no classical tool ran this turn', () => {
    expect(wasClassicalSourceConsulted(['query_planet', 'get_dashas'])).toBe(false)
  })
})
