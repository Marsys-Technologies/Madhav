/**
 * F-135 exit test — buildRankedThemes: weaknesses_empty_reason + open_questions grade sort
 *
 * Fixture shaped like chart 482012f1: 13 promised / 14 conditional / 0 denied.
 * Inserted out of order to verify sort; does NOT test string equality — only substrings.
 */

import { describe, it, expect } from 'vitest'
import { _buildRankedThemesForTest as buildRankedThemes } from '../register_p1_synthesis.js'

function makeVerdict(statement: string): Record<string, unknown> {
  return { statement }
}

function makeVerdictWithSupport(statement: string, n_support: number): Record<string, unknown> {
  return { statement, n_support }
}

// 14 conditional (grades 3.8..5.9) + 13 promised (grades 6.0..9.0) = 27, 0 denied.
// Intentionally scrambled: highest conditional (5.9) is first so sort is actually tested.
const fixture27: Record<string, unknown>[] = [
  makeVerdict('Social Standing: conditional (grade 5.9/10).'),      // ← highest conditional
  makeVerdict('Property Acquisition: conditional (grade 3.8/10).'), // ← lowest conditional
  makeVerdict('Financial Stability: conditional (grade 4.0/10).'),
  makeVerdict('Sibling Relations: conditional (grade 4.2/10).'),
  makeVerdict('Early Education: conditional (grade 4.3/10).'),
  makeVerdict('Communication Skills: conditional (grade 4.5/10).'),
  makeVerdict('Land Holdings: conditional (grade 4.6/10).'),
  makeVerdict('Creative Expression: conditional (grade 4.7/10).'),
  makeVerdict('Health Resilience: conditional (grade 4.8/10).'),
  makeVerdict('Foreign Travel: conditional (grade 5.0/10).'),
  makeVerdict('Partnership Quality: conditional (grade 5.1/10).'),
  makeVerdict('Spiritual Growth: conditional (grade 5.2/10).'),
  makeVerdict('Career Recognition: conditional (grade 5.4/10).'),
  makeVerdict('Inheritance Prospects: conditional (grade 5.6/10).'),
  // 13 promised
  makeVerdict('Longevity: promised (grade 6.0/10).'),
  makeVerdict('Intelligence: promised (grade 6.2/10).'),
  makeVerdict('Wealth Accumulation: promised (grade 6.4/10).'),
  makeVerdict('Marital Harmony: promised (grade 6.6/10).'),
  makeVerdict('Leadership: promised (grade 6.8/10).'),
  makeVerdict('Professional Success: promised (grade 7.0/10).'),
  makeVerdict('Creativity: promised (grade 7.2/10).'),
  makeVerdict('Spiritual Merit: promised (grade 7.4/10).'),
  makeVerdict('Social Influence: promised (grade 7.6/10).'),
  makeVerdict('Academic Excellence: promised (grade 7.8/10).'),
  makeVerdict('Family Bonds: promised (grade 8.0/10).'),
  makeVerdict('Moral Strength: promised (grade 8.5/10).'),
  makeVerdict('Divine Grace: promised (grade 9.0/10).'),
]

describe('F-135 — buildRankedThemes weaknesses_empty_reason + grade sort', () => {
  it('weaknesses is empty for 13-promised/14-conditional/0-denied chart', () => {
    const result = buildRankedThemes(fixture27, 'native')
    expect(result.weaknesses).toEqual([])
  })

  it('weaknesses_empty_reason contains conditional count "14" and min grade "3.8"', () => {
    const result = buildRankedThemes(fixture27, 'native')
    expect(result.weaknesses_empty_reason).not.toBeNull()
    expect(result.weaknesses_empty_reason).toContain('14')
    expect(result.weaknesses_empty_reason).toContain('3.8')
  })

  it('open_questions[0] is lowest-graded domain (Property Acquisition, grade 3.8)', () => {
    const result = buildRankedThemes(fixture27, 'native')
    expect(result.open_questions[0]).toContain('Property Acquisition')
  })

  it('open_questions[1] is second-lowest (Financial Stability, grade 4.0) — not just first pair', () => {
    const result = buildRankedThemes(fixture27, 'native')
    expect(result.open_questions[1]).toContain('Financial Stability')
  })

  it('open_questions last element is highest-graded conditional (Social Standing, grade 5.9)', () => {
    const result = buildRankedThemes(fixture27, 'native')
    const last = result.open_questions[result.open_questions.length - 1]
    expect(last).toContain('Social Standing')
  })

  it('weaknesses_empty_reason is null when weaknesses is non-empty (second fixture)', () => {
    const fixtureWithDenied: Record<string, unknown>[] = [
      makeVerdict('Acute Illness: denied (grade 1.5/10).'),
      makeVerdict('Career Success: promised (grade 7.0/10).'),
    ]
    const result = buildRankedThemes(fixtureWithDenied, 'native')
    expect(result.weaknesses.length).toBeGreaterThan(0)
    expect(result.weaknesses_empty_reason).toBeNull()
  })

  // GA-5 review finding on #1385: the original weaknesses_empty_reason hardcoded a claim
  // ('no event class scored below the denied ceiling, grade < 2.0/10') that is FALSE for
  // exactly this case -- a denied row with a real grade above that ceiling, suppressed only
  // because n_support=0. The reason must name this cause honestly instead.
  it('a denied-but-zero-support row is excluded from weaknesses, and the reason names it (not a fabricated grade-ceiling claim)', () => {
    const fixture: Record<string, unknown>[] = [
      makeVerdictWithSupport('Career Setback: denied (grade 5.0/10).', 0),
      makeVerdict('Longevity: promised (grade 6.0/10).'),
    ]
    const result = buildRankedThemes(fixture, 'native')
    expect(result.weaknesses).toEqual([])
    expect(result.weaknesses_empty_reason).not.toBeNull()
    expect(result.weaknesses_empty_reason).toContain('1 event class')
    expect(result.weaknesses_empty_reason).toContain('n_support=0')
    // the old fabricated claim must NOT be present
    expect(result.weaknesses_empty_reason).not.toContain('below the denied ceiling')
    expect(result.weaknesses_empty_reason).not.toContain('2.0/10')
    // the zero-support row still surfaces its own honest flag
    expect(result.verdict_quality_flags.some(f => f.includes('n_support=0'))).toBe(true)
  })

  it('a no_evidence row is counted in the reason and sorts LAST in open_questions (null-grade branch coverage)', () => {
    const fixture: Record<string, unknown>[] = [
      makeVerdict('Property Acquisition: conditional (grade 3.8/10).'),
      makeVerdict('Foreign Litigation: no evidence available for this event class — cannot assess.'),
      makeVerdict('Longevity: promised (grade 6.0/10).'),
    ]
    const result = buildRankedThemes(fixture, 'native')
    // the null-graded (no_evidence) entry must sort after the graded conditional one
    expect(result.open_questions.length).toBe(2)
    expect(result.open_questions[0]).toContain('Property Acquisition')
    expect(result.open_questions[1]).toContain('Foreign Litigation')
    expect(result.weaknesses_empty_reason).toContain('1 class(es) have no evidence available')
  })
})
