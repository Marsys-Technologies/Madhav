/**
 * SAMĪKṢĀ detector — unit tests (pure, no DB) — PB-3 lane L-2.
 *
 * Exercises the REAL two-stage detector: Stage 1 (the shipped regex detector,
 * reused) + Stage 2 deterministic enrichment into the §14.2 structured candidate,
 * plus the window-parser and grounding-from-citations wiring. No mocks of the
 * detector's own logic.
 */
import { describe, it, expect } from 'vitest'
import {
  detectStructuredCandidatesSync,
  detectStructuredCandidates,
  parseWindow,
  parseStatedConfidence,
  enrichCandidate,
} from '@/lib/pariprashna/samiksha/detector'

const NOW = '2026-02-05'

describe('parseWindow', () => {
  it('mid/early/late-YYYY resolve to seasonal thirds', () => {
    expect(parseWindow('around mid-2027', NOW)).toEqual({ start: '2027-05-01', end: '2027-09-01' })
    expect(parseWindow('early 2027', NOW)).toEqual({ start: '2027-01-01', end: '2027-05-01' })
    expect(parseWindow('late-2027', NOW)).toEqual({ start: '2027-09-01', end: '2028-01-01' })
  })
  it('Qn YYYY resolves to the quarter', () => {
    expect(parseWindow('Q3 2027', NOW)).toEqual({ start: '2027-07-01', end: '2027-10-01' })
    expect(parseWindow('Q1 2026', NOW)).toEqual({ start: '2026-01-01', end: '2026-04-01' })
  })
  it('relative horizons anchor at nowDate', () => {
    expect(parseWindow('in 2 years', NOW)).toEqual({ start: '2026-02-05', end: '2028-02-01' })
    expect(parseWindow('within 6 months', NOW)).toEqual({ start: '2026-02-05', end: '2026-08-01' })
  })
  it('by/bare year and this/next year', () => {
    expect(parseWindow('by 2027', NOW)).toEqual({ start: '2026-02-05', end: '2028-01-01' })
    expect(parseWindow('in 2027', NOW)).toEqual({ start: '2027-01-01', end: '2028-01-01' })
    expect(parseWindow('this year', NOW)).toEqual({ start: '2026-01-01', end: '2027-01-01' })
    expect(parseWindow('next year', NOW)).toEqual({ start: '2027-01-01', end: '2028-01-01' })
  })
  it('returns null for an unresolvable / absent horizon', () => {
    expect(parseWindow(null, NOW)).toBeNull()
    expect(parseWindow('someday soon', NOW)).toBeNull()
  })
})

describe('parseStatedConfidence', () => {
  it('parses percentages and decimals only; never invents from verbal hedges', () => {
    expect(parseStatedConfidence('there is a 70% chance of this')).toBe(0.7)
    expect(parseStatedConfidence('an 80 percent probability')).toBe(0.8)
    expect(parseStatedConfidence('confidence of 0.65 here')).toBe(0.65)
    expect(parseStatedConfidence('this is highly likely')).toBeNull() // verbal ≠ number
    expect(parseStatedConfidence('no probability stated')).toBeNull()
  })
})

describe('enrichCandidate — structured shape + grounding', () => {
  it('maps citation signal_ids into grounding_fact_ids (grounding comes free)', () => {
    const c = enrichCandidate(
      { text: 'A promotion is likely by mid-2027.', offset: 0, score: 0.85, horizon: 'mid-2027' },
      { citations: [{ signal_id: 'SIG.MSR.042', layer: 'L2' }, { signal_id: 'SIG.DASHA.007', layer: 'L3' }], nowDate: NOW },
    )
    expect(c.grounding_fact_ids).toEqual(['SIG.MSR.042', 'SIG.DASHA.007'])
    expect(c.domain).toBe('career')
    expect(c.direction).toBe('positive') // "promotion" is a positive keyword
    expect(c.window_start).toBe('2027-05-01')
    expect(c.window_end).toBe('2027-09-01')
    expect(c.technique_refs).toContain('vimshottari_dasha') // from the SIG.DASHA citation id
  })
  it('honest nulls: unknown domain/direction are null, not a plausible default', () => {
    const c = enrichCandidate(
      { text: 'Something noteworthy will occur around 2028.', offset: 0, score: 0.85, horizon: '2028' },
      { citations: [], nowDate: NOW },
    )
    expect(c.domain).toBeNull()
    expect(c.direction).toBeNull()
    expect(c.grounding_fact_ids).toEqual([])
    expect(c.confidence_stated).toBeUndefined()
  })
})

describe('detectStructuredCandidates(Sync)', () => {
  const TURN =
    'Your chart is strong. An occupational shift, self-initiated, is likely around mid-2027, ' +
    'with a 70% chance during the Saturn dasha. The weather today is fine.'

  it('extracts the time-indexed claim as a structured candidate (sync path)', () => {
    const out = detectStructuredCandidatesSync({
      text: TURN,
      citations: [{ signal_id: 'SIG.DASHA.SAT', layer: 'L3' }],
      nowDate: NOW,
    })
    expect(out.length).toBeGreaterThanOrEqual(1)
    const top = out[0]
    expect(top.claim_text).toMatch(/occupational shift/)
    expect(top.domain).toBe('career')
    expect(top.window_start).toBe('2027-05-01')
    expect(top.window_end).toBe('2027-09-01')
    expect(top.confidence_stated).toBe(0.7)
    expect(top.grounding_fact_ids).toEqual(['SIG.DASHA.SAT'])
    expect(top.technique_refs).toContain('vimshottari_dasha')
  })

  it('async path (default classifier) agrees with the sync path', async () => {
    const asyncOut = await detectStructuredCandidates({ text: TURN, nowDate: NOW })
    const syncOut = detectStructuredCandidatesSync({ text: TURN, nowDate: NOW })
    expect(asyncOut.map((c) => c.claim_text)).toEqual(syncOut.map((c) => c.claim_text))
  })

  it('Stage-2 classifier can DROP a false positive (returns null)', async () => {
    const out = await detectStructuredCandidates(
      { text: TURN, nowDate: NOW },
      () => null, // reject everything
    )
    expect(out).toEqual([])
  })

  it('respects the minScore filter (mirrors the route 0.5 gate)', () => {
    // A bare-year-only sentence with no prediction verb scores 0.45 (< 0.5).
    const out = detectStructuredCandidatesSync({ text: 'He was born in 1984 in Bhubaneswar.', nowDate: NOW })
    expect(out).toEqual([])
  })
})
