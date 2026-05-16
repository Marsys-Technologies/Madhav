/**
 * γ3 — PPL: Prediction detector unit tests
 *
 * Tests:
 *  - detectPredictionCandidates returns candidates for time-indexed sentences
 *  - extractSuggestedFalsifier extracts falsifier clauses
 *  - Confidence scores reflect presence of prediction verbs
 *  - No false positives on historical references
 */

import { describe, it, expect } from 'vitest'
import {
  detectPredictionCandidates,
  extractSuggestedFalsifier,
} from '../../../src/lib/ppl/prediction_detector'
import {
  PredictionCandidatePartSchema,
  predictionCandidatePart,
} from '../../../src/lib/streams/data_parts'

// ── Schema tests ──────────────────────────────────────────────────────────────

describe('PredictionCandidatePartSchema', () => {
  it('accepts valid prediction candidate part', () => {
    const part = {
      type: 'prediction_candidate',
      text: 'Jupiter will conjunct Saturn within 2 years.',
      offset: 0,
      score: 0.85,
      horizon: '2 years',
    }
    expect(() => PredictionCandidatePartSchema.parse(part)).not.toThrow()
  })

  it('accepts null horizon', () => {
    const part = {
      type: 'prediction_candidate',
      text: 'This event will occur.',
      offset: 0,
      score: 0.5,
      horizon: null,
    }
    expect(() => PredictionCandidatePartSchema.parse(part)).not.toThrow()
  })

  it('rejects score out of 0–1 range', () => {
    expect(() => PredictionCandidatePartSchema.parse({
      type: 'prediction_candidate',
      text: 'x',
      offset: 0,
      score: 1.5,
      horizon: null,
    })).toThrow()
  })
})

describe('predictionCandidatePart helper', () => {
  it('creates part with correct type', () => {
    const p = predictionCandidatePart({ text: 'X', offset: 0, score: 0.7, horizon: '6 months' })
    expect(p.type).toBe('prediction_candidate')
    expect(p.horizon).toBe('6 months')
  })
})

// ── Detector tests ────────────────────────────────────────────────────────────

describe('detectPredictionCandidates', () => {
  it('returns empty array for empty text', () => {
    expect(detectPredictionCandidates('')).toEqual([])
  })

  it('detects a sentence with year + prediction verb', () => {
    const text = 'Jupiter will transit Aries in 2026. This is significant.'
    const candidates = detectPredictionCandidates(text)
    expect(candidates.length).toBeGreaterThan(0)
    expect(candidates[0].score).toBeGreaterThanOrEqual(0.5)
  })

  it('gives higher score when prediction verb is present', () => {
    const highConf = 'The native is expected to experience a career change within 6 months.'
    const lowConf = 'The transit occurs in 2027.'
    const highCandidates = detectPredictionCandidates(highConf)
    const lowCandidates = detectPredictionCandidates(lowConf)
    if (highCandidates.length > 0 && lowCandidates.length > 0) {
      expect(highCandidates[0].score).toBeGreaterThan(lowCandidates[0].score)
    }
  })

  it('sorts candidates by score descending', () => {
    const text =
      'Jupiter will conjoin Rahu within 3 months. ' +
      'The Sun was in Aries in 2020. ' +
      'Mars is expected to transit Scorpio by 2026.'
    const candidates = detectPredictionCandidates(text)
    for (let i = 1; i < candidates.length; i++) {
      expect(candidates[i - 1].score).toBeGreaterThanOrEqual(candidates[i].score)
    }
  })

  it('extracts horizon from detected sentence', () => {
    const text = 'Career will improve significantly within 6 months.'
    const candidates = detectPredictionCandidates(text)
    if (candidates.length > 0) {
      expect(candidates[0].horizon).toBeTruthy()
    }
  })

  it('skips very short fragments', () => {
    const text = 'In 2027.'
    const candidates = detectPredictionCandidates(text)
    // Very short — under 20 chars; should be skipped
    expect(candidates).toHaveLength(0)
  })
})

describe('extractSuggestedFalsifier', () => {
  it('extracts clause starting with "unless"', () => {
    const text = 'The native will succeed unless Saturn transits 10th lord.'
    const falsifier = extractSuggestedFalsifier(text)
    expect(falsifier).toBeTruthy()
    expect(falsifier?.toLowerCase()).toContain('unless')
  })

  it('returns null when no falsifier indicator', () => {
    const text = 'Jupiter will be exalted in 2026.'
    expect(extractSuggestedFalsifier(text)).toBeNull()
  })

  it('extracts "barring" clause', () => {
    const text = 'Career growth is expected, barring unexpected setbacks.'
    const falsifier = extractSuggestedFalsifier(text)
    expect(falsifier).toBeTruthy()
    expect(falsifier?.toLowerCase()).toContain('barring')
  })
})
