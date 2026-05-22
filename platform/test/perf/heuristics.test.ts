/**
 * heuristics.test.ts — Unit tests for all 6 perf heuristics.
 * MCPT v3.1.0-S4 AC.S4.1–AC.S4.6
 *
 * CRITICAL: These heuristics must not call LLM APIs.
 * Verification: grep -rn "openai\|anthropic\|gemini" platform/src/lib/perf/heuristics/ must return nothing.
 */

import { describe, it, expect } from 'vitest'

// Import heuristics directly (no mocking needed — pure functions)
import { extractCitations, countCitations, hasCitation } from '../../src/lib/perf/heuristics/extract_citations'
import { extractNumericalClaims, hasNumericalClaims } from '../../src/lib/perf/heuristics/extract_numerical_claims'
import { isForwardLooking, extractForwardLookingPhrases } from '../../src/lib/perf/heuristics/forward_looking'
import { checkSanskritGlossing, isSanskritCompliant } from '../../src/lib/perf/heuristics/sanskrit_glossing'
import { detectLayerMixing, hasProperLayerAttribution } from '../../src/lib/perf/heuristics/layer_attribution'
import { isNonFactualResponse, meetsNonFactualShape } from '../../src/lib/perf/heuristics/is_non_factual'

// ── 1. extract_citations ──────────────────────────────────────────────────────

describe('extractCitations', () => {
  it('extracts SIG.MSR.NNN references', () => {
    const text = 'This is grounded in SIG.MSR.034 and SIG.MSR.123 from the corpus.'
    const citations = extractCitations(text)
    expect(citations).toContain('SIG.MSR.034')
    expect(citations).toContain('SIG.MSR.123')
  })

  it('extracts GFM footnote references [^N]', () => {
    const text = 'The moon is in Aquarius [^1], which indicates themes of detachment [^2].'
    const citations = extractCitations(text)
    expect(citations).toContain('[^1]')
    expect(citations).toContain('[^2]')
  })

  it('extracts LEL.E.NNN references', () => {
    const text = 'This pattern correlates with LEL.E.012 (career transition 2018).'
    const citations = extractCitations(text)
    expect(citations).toContain('LEL.E.012')
  })

  it('extracts FORENSIC.§N.N references', () => {
    const text = 'Per FORENSIC.§3.1 and FORENSIC.§12, the Sun is at 21°47′43″.'
    const citations = extractCitations(text)
    expect(citations.some(c => c.startsWith('FORENSIC'))).toBe(true)
  })

  it('extracts arrow citations → SIG.MSR.NNN', () => {
    const text = 'The pattern → SIG.MSR.234 indicates career stress.'
    const citations = extractCitations(text)
    expect(citations).toContain('SIG.MSR.234')
  })

  it('returns empty array for plain text without citations', () => {
    const text = 'This is a plain response with no citations.'
    expect(extractCitations(text)).toEqual([])
  })

  it('hasCitation returns true for text with SIG.MSR reference', () => {
    expect(hasCitation('Per SIG.MSR.001, the career signal is activated.')).toBe(true)
  })

  it('hasCitation returns false for plain text', () => {
    expect(hasCitation('No citations here.')).toBe(false)
  })

  it('countCitations returns deduplicated count', () => {
    const text = 'SIG.MSR.001 and SIG.MSR.001 and SIG.MSR.002'
    expect(countCitations(text)).toBe(2) // deduplicated
  })
})

// ── 2. extract_numerical_claims ───────────────────────────────────────────────

describe('extractNumericalClaims', () => {
  it('extracts degree values', () => {
    const text = 'Saturn is at 18°02′10″ and Sun is at 21.47°.'
    const claims = extractNumericalClaims(text)
    expect(claims.some(c => c.type === 'degree')).toBe(true)
  })

  it('extracts virupa values', () => {
    const text = 'Saturn has 235 virupas of shadbala.'
    const claims = extractNumericalClaims(text)
    expect(claims.some(c => c.type === 'virupa')).toBe(true)
  })

  it('extracts score/confidence values', () => {
    const text = 'Confidence: 0.87 for this prediction.'
    const claims = extractNumericalClaims(text)
    expect(claims.some(c => c.type === 'score')).toBe(true)
  })

  it('returns empty for plain text', () => {
    expect(extractNumericalClaims('The career is strong.')).toEqual([])
  })

  it('hasNumericalClaims returns true for degree text', () => {
    expect(hasNumericalClaims('Moon is at 27° in Aquarius.')).toBe(true)
  })
})

// ── 3. forward_looking ────────────────────────────────────────────────────────

describe('isForwardLooking', () => {
  it('detects "will" as forward-looking', () => {
    expect(isForwardLooking('This will bring changes in career.')).toBe(true)
  })

  it('detects "upcoming dasha" as forward-looking', () => {
    expect(isForwardLooking('The upcoming dasha of Saturn will intensify themes.')).toBe(true)
  })

  it('detects time horizon patterns', () => {
    expect(isForwardLooking('Within the next 90 days, Jupiter transits will be significant.')).toBe(true)
  })

  it('detects "predict" keyword', () => {
    expect(isForwardLooking('I predict a career shift in 2027.')).toBe(true)
  })

  it('returns false for purely historical text', () => {
    expect(isForwardLooking('In 2018, the career shifted dramatically.')).toBe(false)
  })

  it('returns false for empty string', () => {
    expect(isForwardLooking('')).toBe(false)
  })

  it('extractForwardLookingPhrases returns match context', () => {
    const phrases = extractForwardLookingPhrases('The upcoming dasha will bring changes.')
    expect(phrases.length).toBeGreaterThan(0)
  })
})

// ── 4. sanskrit_glossing ──────────────────────────────────────────────────────

describe('checkSanskritGlossing', () => {
  it('marks client-tier as non-compliant when Lagna appears without gloss', () => {
    const result = checkSanskritGlossing('Your Lagna is in Aries.', 'client')
    expect(result.compliant).toBe(false)
    expect(result.violations).toContain('Lagna')
  })

  it('marks client-tier as compliant when Lagna has English gloss', () => {
    const result = checkSanskritGlossing('Your Lagna (Ascendant) is in Aries.', 'client')
    // Lagna (Ascendant) has a gloss
    expect(result.glossed.includes('Lagna') || result.compliant).toBe(true)
  })

  it('always returns compliant for super_admin tier', () => {
    const result = checkSanskritGlossing('Lagna Dasha Nakshatra — no glosses needed.', 'super_admin')
    expect(result.compliant).toBe(true)
  })

  it('always returns compliant for acharya tier', () => {
    const result = checkSanskritGlossing('Atmakaraka Dasha — technical terms only.', 'acharya')
    expect(result.compliant).toBe(true)
  })

  it('isSanskritCompliant is true for non-client tier regardless of Sanskrit', () => {
    expect(isSanskritCompliant('Dasha Nakshatra Yoga', 'super_admin')).toBe(true)
  })
})

// ── 5. layer_attribution ─────────────────────────────────────────────────────

describe('detectLayerMixing', () => {
  it('detects interpretive claim without citation', () => {
    const text = 'This indicates a strong pattern of career challenges.'
    const mixing = detectLayerMixing(text)
    expect(mixing.length).toBeGreaterThan(0)
  })

  it('does not flag interpretive claim with nearby citation', () => {
    const text = 'This indicates a strong pattern per SIG.MSR.234 of career challenges.'
    const mixing = detectLayerMixing(text)
    expect(mixing.length).toBe(0)
  })

  it('returns empty for factual data text', () => {
    const text = 'Saturn is at 18° in Virgo, house 6.'
    const mixing = detectLayerMixing(text)
    expect(mixing.length).toBe(0)
  })

  it('hasProperLayerAttribution is false for uncited interpretive text', () => {
    expect(hasProperLayerAttribution('This suggests a career crisis tendency.')).toBe(false)
  })

  it('hasProperLayerAttribution is true when citation is present', () => {
    expect(hasProperLayerAttribution('This suggests per SIG.MSR.001 a career crisis tendency.')).toBe(true)
  })
})

// ── 6. is_non_factual ─────────────────────────────────────────────────────────

describe('isNonFactualResponse', () => {
  it('returns false for JSON-like responses (factual)', () => {
    expect(isNonFactualResponse('{ "signals": [], "count": 0 }')).toBe(false)
  })

  it('returns false for query_chart_facts tool (inherently factual)', () => {
    const text = 'This indicates a career pattern. The native tends to focus.'
    expect(isNonFactualResponse(text, 'query_chart_facts')).toBe(false)
  })

  it('returns true for interpretive text with "this indicates"', () => {
    expect(isNonFactualResponse('This indicates a strong career drive based on Saturn.')).toBe(true)
  })

  it('returns true for long text with 3+ sentences', () => {
    const text = [
      'The Moon in Aquarius at house 11 is significant.',
      'This placement indicates detachment from emotional ties.',
      'The native tends to find community over family.',
    ].join(' ')
    expect(isNonFactualResponse(text)).toBe(true)
  })

  it('returns false for markdown table responses (data-heavy)', () => {
    const text = '| Planet | House | Sign |\n|---|---|---|\n| Sun | 10 | Capricorn |\n| Moon | 11 | Aquarius |'
    expect(isNonFactualResponse(text)).toBe(false)
  })

  it('meetsNonFactualShape requires 3+ sentences AND citation', () => {
    const withCitation = 'This indicates SIG.MSR.001. The pattern is clear. Career challenges persist.'
    expect(meetsNonFactualShape(withCitation)).toBe(true)

    const withoutCitation = 'This indicates something. The pattern is clear. Career challenges persist.'
    expect(meetsNonFactualShape(withoutCitation)).toBe(false)
  })
})
