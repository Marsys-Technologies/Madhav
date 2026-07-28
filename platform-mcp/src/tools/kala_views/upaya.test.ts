/**
 * upaya.test.ts — ṢAḌ-DARŚANA W0.4: `kala_upaya_get` facade shell.
 * Covers: honest not-computed reading/coverage, envelope well-formedness, tri-plane honesty
 * (no dangling pointer to an unregistered sibling tool), and calibration_maturity's honest
 * all-zero state (no computation ran, so no LEL-derived maturity claim is legal).
 */
import { describe, it, expect } from 'vitest'
import { isNoLever } from '../../lib/kala_envelope.js'
import { buildKalaUpayaReading, buildKalaUpayaResponse } from './upaya.js'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

describe('buildKalaUpayaReading', () => {
  it('is a well-formed argument reading with an honest unresolved verdict', () => {
    const reading = buildKalaUpayaReading(CHART_ID)
    expect(reading.thesis.trim().length).toBeGreaterThan(0)
    expect(reading.verdict.statement.trim().length).toBeGreaterThan(0)
    expect(reading.verdict.tier).toBe('unresolved')
    expect(reading.evidence).toEqual([])
    expect(reading.dissent).toEqual([])
    // No fabricated falsifier date — nothing has been claimed yet, so nothing to falsify.
    expect(reading.falsifier).toBeNull()
  })

  it('names the chart_id it was called for (never a chart-invariant constant)', () => {
    const a = buildKalaUpayaReading(CHART_ID)
    const b = buildKalaUpayaReading('1c826d5a-0000-0000-0000-000000000000')
    expect(a.thesis).toContain(CHART_ID)
    expect(b.thesis).not.toContain(CHART_ID)
  })
})

describe('buildKalaUpayaResponse', () => {
  const response = buildKalaUpayaResponse({ chart_id: CHART_ID })

  it('tags the tool name', () => {
    expect(response.tool).toBe('kala_upaya_get')
  })

  it('carries three honest not_in_corpus coverage rows, each with a reason', () => {
    expect(response.coverage.length).toBe(3)
    for (const entry of response.coverage) {
      expect(entry.state).toBe('not_in_corpus')
      expect(entry.reason).toBeTruthy()
    }
    const concepts = response.coverage.map((c) => c.concept).sort()
    expect(concepts).toEqual(['alternate_routing_search', 'efficacy_tiers', 'pact_link_diagnosis'])
  })

  it('serves an honest all-zero calibration_maturity (nothing computed, no LEL consulted)', () => {
    expect(response.calibration_maturity).toEqual({
      n_events: 0,
      prospective_resolutions: 0,
      event_class_coverage: 0,
      weights_version: null,
      skill_score: null,
    })
  })

  it('intervention_ref is null (this object IS the intervention plane already)', () => {
    expect(response.tri_plane.intervention_ref).toBeNull()
  })

  it('interpretation_ref/prediction_ref are honest no_lever placeholders, not dangling pointers', () => {
    expect(isNoLever(response.tri_plane.interpretation_ref)).toBe(true)
    expect(isNoLever(response.tri_plane.prediction_ref)).toBe(true)
  })

  it('composed_text is non-empty and deterministic for the same input', () => {
    const again = buildKalaUpayaResponse({ chart_id: CHART_ID })
    expect(response.composed_text.length).toBeGreaterThan(0)
    expect(again.composed_text).toBe(response.composed_text)
  })

  it('threads question_frame through when supplied, and is null when omitted', () => {
    const withFrame = buildKalaUpayaResponse({ chart_id: CHART_ID, question_frame: { domain: 'career' } })
    expect(withFrame.question_frame).toEqual({ domain: 'career' })
    expect(response.question_frame).toBeNull()
  })
})
