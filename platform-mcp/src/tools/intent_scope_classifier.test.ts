/**
 * intent_scope_classifier.test.ts — D-2 Lane V-3, CR-28 / DR-8 (DIS.021) contract test.
 *
 * Asserts the redesigned deterministic scope-tuple classifier honors the DR-8 ruling:
 * the common path returns a computed scope_tuple (not a rendered prompt), is deterministic,
 * is fully auditable via matched_rules, and retains the old prompt as a disclosed fallback.
 */
import { describe, it, expect } from 'vitest'
import { classifyScope, INTENT_CLASSIFY_TEMPLATE, renderFallbackPrompt } from './intent_scope_classifier.js'

describe('classifyScope — DR-8 contract shape', () => {
  it('returns the full DR-8 envelope (not a rendered prompt)', () => {
    const r = classifyScope('What is my current mahadasha?')
    expect(r).toHaveProperty('scope_tuple')
    expect(r).toHaveProperty('confidence')
    expect(r.method).toBe('deterministic_rules')
    expect(Array.isArray(r.matched_rules)).toBe(true)
    expect(typeof r.fallback_prompt).toBe('string')
    expect(typeof r.fallback_recommended).toBe('boolean')
    // scope_tuple carries all seven dimensions
    const t = r.scope_tuple
    for (const k of ['intent', 'domains', 'width', 'depth', 'horizon', 'intervention', 'entitlement']) {
      expect(t).toHaveProperty(k)
    }
    expect(Array.isArray(t.domains)).toBe(true)
  })

  it('is deterministic: identical query → identical tuple (compiler-safe)', () => {
    const q = 'Should I wear a gemstone remedy for my career prospects next year?'
    expect(classifyScope(q)).toEqual(classifyScope(q))
  })

  it('retains the exact pre-DR-8 prompt as fallback_prompt', () => {
    const r = classifyScope('anything')
    expect(r.fallback_prompt).toBe(renderFallbackPrompt('anything'))
    expect(INTENT_CLASSIFY_TEMPLATE).toContain('You are a Jyotish query classifier')
  })
})

describe('classifyScope — intent classification', () => {
  const cases: Array<[string, string]> = [
    ['What dasha am I running now?', 'dasha_timing'],
    ['Where is Saturn transiting currently?', 'transit_analysis'],
    ['Do I have a Gaja Kesari yoga?', 'yoga_identification'],
    ['What is the Shadbala of my Jupiter?', 'planet_strength'],
    ['Analyze my 10th house lord', 'house_analysis'],
    ['What remedy should I do for Saturn?', 'remedy_lookup'],
    ['What is my birth nakshatra and tithi?', 'panchanga'],
    ['What does BPHS say about the 8th lord?', 'classical_rule'],
    ['Give me a full reading of my chart', 'chart_overview'],
    ['Was my last prediction accurate?', 'prediction_calibration'],
    ['Assess my career prospects', 'domain_assessment'],
  ]
  for (const [q, expected] of cases) {
    it(`"${q}" → intent=${expected}`, () => {
      expect(classifyScope(q).scope_tuple.intent).toBe(expected)
    })
  }
})

describe('classifyScope — domains (multi-value)', () => {
  it('extracts a single domain', () => {
    expect(classifyScope('How is my wealth?').scope_tuple.domains).toContain('wealth')
  })
  it('extracts multiple domains', () => {
    const doms = classifyScope('Assess my career and marriage prospects').scope_tuple.domains
    expect(doms).toContain('career')
    expect(doms).toContain('marriage')
  })
  it('defaults to general when no domain matches', () => {
    expect(classifyScope('What dasha am I running?').scope_tuple.domains).toEqual(['general'])
  })
})

describe('classifyScope — width / depth / horizon / intervention', () => {
  it('detects broad width', () => {
    expect(classifyScope('Give me a comprehensive whole-chart reading').scope_tuple.width).toBe('broad')
  })
  it('multi-domain implies broad width', () => {
    expect(classifyScope('career wealth marriage health').scope_tuple.width).toBe('broad')
  })
  it('detects deep depth', () => {
    expect(classifyScope('I want a detailed in-depth acharya-grade analysis of my career').scope_tuple.depth).toBe('deep')
  })
  it('detects shallow depth', () => {
    expect(classifyScope('Quick summary of my chart').scope_tuple.depth).toBe('shallow')
  })
  it('detects present horizon', () => {
    expect(classifyScope('What is my current running dasha right now?').scope_tuple.horizon).toBe('present')
  })
  it('detects near horizon', () => {
    expect(classifyScope('What happens next year in my career?').scope_tuple.horizon).toBe('near')
  })
  it('detects muhurta intervention', () => {
    expect(classifyScope('What is an auspicious time to start my business?').scope_tuple.intervention).toBe('muhurta')
  })
  it('detects remedy intervention', () => {
    expect(classifyScope('What mantra should I chant for Saturn?').scope_tuple.intervention).toBe('remedy')
  })
})

describe('classifyScope — confidence and fallback', () => {
  it('recommends fallback for unmatched / gibberish', () => {
    const r = classifyScope('asdfqwer zxcv')
    expect(r.scope_tuple.intent).toBe('unknown')
    expect(r.fallback_recommended).toBe(true)
    expect(r.confidence).toBeLessThan(0.5)
  })
  it('does not recommend fallback for a clear query', () => {
    const r = classifyScope('What remedy for my wealth problems next year?')
    expect(r.fallback_recommended).toBe(false)
    expect(r.confidence).toBeGreaterThanOrEqual(0.5)
  })
  it('handles empty query gracefully', () => {
    const r = classifyScope('')
    expect(r.confidence).toBe(0)
    expect(r.fallback_recommended).toBe(true)
    expect(r.scope_tuple.intent).toBe('unknown')
  })
  it('matched_rules audits every classification decision', () => {
    const r = classifyScope('remedy for wealth now')
    expect(r.matched_rules.some((m) => m.startsWith('intent:'))).toBe(true)
    expect(r.matched_rules).toContain('domain:wealth')
    expect(r.matched_rules).toContain('intervention:remedy')
  })
})

describe('classifyScope — entitlement tier', () => {
  it('reference intents get reference entitlement', () => {
    expect(classifyScope('What does the BPHS say about Rahu?').scope_tuple.entitlement).toBe('reference')
  })
  it('chart-specific intents default to the least-privilege restricted entitlement ' +
    '(no session context is available to this deterministic classifier to justify native)', () => {
    expect(classifyScope('What is my wealth outlook?').scope_tuple.entitlement).toBe('restricted')
  })
})
