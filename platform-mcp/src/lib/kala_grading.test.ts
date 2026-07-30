/**
 * kala_grading.test.ts — ṢAḌ-DARŚANA W1 item 38-lite + ELECT frontier v0. Unit tests for the
 * pure grading/frontier helpers (`kala_grading.ts`). No network — exercises the documented
 * lite-v0 conventions directly.
 */
import { describe, it, expect } from 'vitest'
import { gradeCandidate, buildFrontierStatement } from './kala_grading.js'

describe('gradeCandidate — item 38-lite tiering', () => {
  it('grades a disqualified candidate as disqualified regardless of score', () => {
    const grade = gradeCandidate({ score: 0.95, disqualified: true })
    expect(grade.tier).toBe('disqualified')
  })

  it('tiers gold at/above 0.75', () => {
    expect(gradeCandidate({ score: 0.75, disqualified: false }).tier).toBe('gold')
    expect(gradeCandidate({ score: 0.9, disqualified: false }).tier).toBe('gold')
  })

  it('tiers silver in [0.55, 0.75)', () => {
    expect(gradeCandidate({ score: 0.55, disqualified: false }).tier).toBe('silver')
    expect(gradeCandidate({ score: 0.74, disqualified: false }).tier).toBe('silver')
  })

  it('tiers bronze in [0.35, 0.55)', () => {
    expect(gradeCandidate({ score: 0.35, disqualified: false }).tier).toBe('bronze')
    expect(gradeCandidate({ score: 0.54, disqualified: false }).tier).toBe('bronze')
  })

  it('tiers marginal below 0.35', () => {
    expect(gradeCandidate({ score: 0.1, disqualified: false }).tier).toBe('marginal')
    expect(gradeCandidate({ score: 0, disqualified: false }).tier).toBe('marginal')
  })

  it('clamps an out-of-range score rather than crashing or fabricating a tier', () => {
    expect(gradeCandidate({ score: 1.5, disqualified: false }).tier).toBe('gold')
    expect(gradeCandidate({ score: -0.5, disqualified: false }).tier).toBe('marginal')
    expect(gradeCandidate({ score: NaN, disqualified: false }).tier).toBe('marginal')
  })

  it('names its convention_id and basis so callers/tests can trace WHY a tier was assigned', () => {
    const grade = gradeCandidate({ score: 0.8, disqualified: false })
    expect(grade.convention_id).toBe('lite_v0_score_threshold')
    expect(grade.basis).toContain('0.80')
  })
})

describe('buildFrontierStatement — ELECT frontier v0', () => {
  const RANGE = { start: '2026-08-01', end: '2026-10-30' }

  it('reports an honest empty frontier when no live candidates exist (absence-of-expected discipline)', () => {
    const frontier = buildFrontierStatement([], 'business', RANGE, 'date_range outside populated panchanga horizon')
    expect(frontier.candidate_count).toBe(0)
    expect(frontier.best).toBeNull()
    expect(frontier.statement).toContain('No candidates')
    expect(frontier.statement).toContain('date_range outside populated panchanga horizon')
    // Never fabricates a specific next-occurrence date it did not compute.
    expect(frontier.statement).not.toMatch(/next occurrence is \d{4}-\d{2}-\d{2}/)
  })

  it('treats every candidate as disqualified as an honest empty (no live candidates), not a crash', () => {
    const frontier = buildFrontierStatement(
      [{ start: '2026-08-05T00:00:00Z', end: '2026-08-07T00:00:00Z', score: 0.9, disqualified: true }],
      'business', RANGE, null,
    )
    expect(frontier.candidate_count).toBe(0)
    expect(frontier.best).toBeNull()
  })

  it('names the best candidate and flags gold-tier presence when one exists', () => {
    const frontier = buildFrontierStatement(
      [
        { start: '2026-08-05T00:00:00Z', end: '2026-08-07T00:00:00Z', score: 0.82, disqualified: false },
        { start: '2026-08-12T00:00:00Z', end: '2026-08-14T00:00:00Z', score: 0.4, disqualified: false },
      ],
      'business', RANGE, null,
    )
    expect(frontier.candidate_count).toBe(2)
    expect(frontier.gold_tier_present).toBe(true)
    expect(frontier.best_tier).toBe('gold')
    expect(frontier.best?.start).toBe('2026-08-05T00:00:00Z')
    expect(frontier.statement).toContain('gold')
  })

  it('honestly notes the absence of a gold-tier candidate and points at the W3 gap-report engine, without inventing a next-occurrence date', () => {
    const frontier = buildFrontierStatement(
      [{ start: '2026-08-12T00:00:00Z', end: '2026-08-14T00:00:00Z', score: 0.4, disqualified: false }],
      'business', RANGE, null,
    )
    expect(frontier.gold_tier_present).toBe(false)
    expect(frontier.best_tier).toBe('bronze')
    expect(frontier.statement).toContain('none reaching gold tier')
    expect(frontier.statement).toContain('W3, item 36')
    expect(frontier.statement).not.toMatch(/\d{4}-\d{2}-\d{2}.*occurs/)
  })

  it('picks the highest-score candidate as best even when it is not first in the input order', () => {
    const frontier = buildFrontierStatement(
      [
        { start: '2026-08-12T00:00:00Z', end: '2026-08-14T00:00:00Z', score: 0.4, disqualified: false },
        { start: '2026-09-01T00:00:00Z', end: '2026-09-03T00:00:00Z', score: 0.6, disqualified: false },
      ],
      'business', RANGE, null,
    )
    expect(frontier.best?.start).toBe('2026-09-01T00:00:00Z')
  })
})
