/**
 * confidence/__tests__/activation_gate.test.ts — lane G3-C (PPR-03).
 *
 * The single most important test in this lane: proves the
 * `empirically_calibrated` activation gate correctly refuses to fire under
 * today's REAL L5 STRUCTURAL-mode conditions (CLAUDE.md §E — "L5 is sealed
 * in STRUCTURAL mode; empirical calibration values fill in as
 * prediction→outcome data accrues"). Fixtures below are shaped exactly like
 * the REAL `query_calibration.ts` / `query_insights.ts` response payloads
 * (verified against those files' own SQL — see `activation_gate.ts`'s
 * module docblock for the citation) in their realistic near-empty state.
 */
import { describe, it, expect } from 'vitest'

import {
  evaluateEmpiricalCalibrationGate,
  extractCalibrationSampleSize,
  MIN_SAMPLE_SIZE_FOR_EMPIRICAL_CALIBRATION,
} from '../activation_gate'

describe('evaluateEmpiricalCalibrationGate — RED-conditions proof: closed under today\'s real STRUCTURAL-mode data', () => {
  it('gate is CLOSED when no real sample size could be determined (null) — the honest default', () => {
    const result = evaluateEmpiricalCalibrationGate({ sampleSize: null })
    expect(result.gate_open).toBe(false)
    expect(result.sample_size).toBeNull()
    expect(result.gate_note).toContain('STRUCTURAL mode')
  })

  it('gate is CLOSED when the real extracted sample size is 0 — a chart with zero mimamsa_calibration rows (the realistic case for most charts today)', () => {
    const result = evaluateEmpiricalCalibrationGate({ sampleSize: 0 })
    expect(result.gate_open).toBe(false)
  })

  it('gate is CLOSED when the real sample size is positive but below the (honestly disclosed placeholder) minimum', () => {
    const result = evaluateEmpiricalCalibrationGate({ sampleSize: 3 })
    expect(result.gate_open).toBe(false)
    expect(result.min_sample_size_required).toBe(MIN_SAMPLE_SIZE_FOR_EMPIRICAL_CALIBRATION)
    expect(result.threshold_is_placeholder).toBe(true)
  })

  it('gate OPENS only once a real sample size clears the minimum — proves the gate is not permanently closed, just correctly closed today', () => {
    const result = evaluateEmpiricalCalibrationGate({ sampleSize: MIN_SAMPLE_SIZE_FOR_EMPIRICAL_CALIBRATION })
    expect(result.gate_open).toBe(true)
    expect(result.gate_note).toContain('Gate OPEN')
  })

  it('gate is CLOSED one below the minimum (boundary check)', () => {
    const result = evaluateEmpiricalCalibrationGate({ sampleSize: MIN_SAMPLE_SIZE_FOR_EMPIRICAL_CALIBRATION - 1 })
    expect(result.gate_open).toBe(false)
  })
})

describe('extractCalibrationSampleSize — real payload shapes', () => {
  it('extracts total_matches from a realistic query_insights calibration_summary payload', () => {
    const payload = {
      chart_id: 'chart-1',
      insight_units: [],
      calibration_summary: {
        total_matches: 0,
        confirmed: 0,
        partial: 0,
        refuted: 0,
        unresolved: 0,
        mean_composite_score: null,
      },
      evidence_grade_counts: {},
    }
    expect(extractCalibrationSampleSize(payload)).toBe(0)
  })

  it('extracts a positive total_matches once real prediction→outcome data exists', () => {
    const payload = { calibration_summary: { total_matches: 42 } }
    expect(extractCalibrationSampleSize(payload)).toBe(42)
  })

  it('extracts and sums verdict_distribution[].n from a realistic query_calibration payload', () => {
    const payload = {
      chart_id: 'chart-1',
      verdict_distribution: [
        { composite_verdict: 'confirmed', n: 5, mean_score: 0.8 },
        { composite_verdict: 'partial', n: 2, mean_score: 0.5 },
      ],
      reliability_curve: [],
      multipliers: [],
      qa_results: [],
    }
    expect(extractCalibrationSampleSize(payload)).toBe(7)
  })

  it('returns null on an empty verdict_distribution array (the realistic zero-data case)', () => {
    const payload = { verdict_distribution: [] }
    expect(extractCalibrationSampleSize(payload)).toBeNull()
  })

  it('returns null (never guesses) on a malformed/unrelated payload shape', () => {
    expect(extractCalibrationSampleSize({ some_other_field: 1 })).toBeNull()
    expect(extractCalibrationSampleSize(null)).toBeNull()
    expect(extractCalibrationSampleSize('not an object')).toBeNull()
    expect(extractCalibrationSampleSize(42)).toBeNull()
  })

  it('accepts a clean numeric-string total_matches (defensive against bigint-as-string pg drivers) but rejects a non-numeric string', () => {
    expect(extractCalibrationSampleSize({ calibration_summary: { total_matches: '17' } })).toBe(17)
    expect(extractCalibrationSampleSize({ calibration_summary: { total_matches: 'not-a-number' } })).toBeNull()
  })
})

describe('end-to-end: the gate correctly stays closed composing extraction + evaluation on realistic empty-state payloads', () => {
  it('a turn that consulted query_insights on a chart with zero calibration matches never opens the gate', () => {
    const payload = { calibration_summary: { total_matches: 0 } }
    const sampleSize = extractCalibrationSampleSize(payload)
    const gate = evaluateEmpiricalCalibrationGate({ sampleSize })
    expect(gate.gate_open).toBe(false)
  })
})
