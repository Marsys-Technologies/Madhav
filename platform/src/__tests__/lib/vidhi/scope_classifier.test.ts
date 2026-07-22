/**
 * scope_classifier.test.ts — W4 "One Planner" core step 1.
 *
 * Covers the WEB-SIDE port of the deterministic scope-tuple classifier
 * (platform/src/lib/vidhi/scope_classifier.ts, ported faithfully from
 * platform-mcp/src/tools/intent_scope_classifier.ts).
 *
 * Asserts:
 *   - output SHAPE (ScopeClassification + ScopeTuple, schema-valid)
 *   - determinism (identical input → identical output)
 *   - the low-confidence `fallback_recommended` signal that drives the
 *     ClarificationRequest planner outcome
 */

import { describe, it, expect } from 'vitest'
import {
  classifyScope,
  ScopeTupleSchema,
  INTENTS,
  DOMAINS,
} from '@/lib/vidhi/scope_classifier'

describe('classifyScope — output shape', () => {
  it('returns a schema-valid ScopeTuple + the full ScopeClassification envelope', () => {
    const c = classifyScope('What is my current Vimshottari dasha period?')

    // Envelope fields present and correctly typed.
    expect(c.method).toBe('deterministic_rules')
    expect(typeof c.confidence).toBe('number')
    expect(c.confidence).toBeGreaterThanOrEqual(0)
    expect(c.confidence).toBeLessThanOrEqual(1)
    expect(Array.isArray(c.matched_rules)).toBe(true)
    expect(typeof c.fallback_prompt).toBe('string')
    expect(typeof c.fallback_recommended).toBe('boolean')
    expect(typeof c.usage).toBe('string')

    // The tuple validates against the exported Zod schema (the same schema
    // PipelinePlanSchema.scope_tuple uses).
    const parsed = ScopeTupleSchema.safeParse(c.scope_tuple)
    expect(parsed.success).toBe(true)

    // Vocabulary membership.
    expect(INTENTS).toContain(c.scope_tuple.intent)
    for (const d of c.scope_tuple.domains) expect(DOMAINS).toContain(d)
    expect(c.scope_tuple.domains.length).toBeGreaterThanOrEqual(1)
  })

  it('classifies a dasha-timing query into intent=dasha_timing with high confidence', () => {
    const c = classifyScope('What is my current dasha period?')
    expect(c.scope_tuple.intent).toBe('dasha_timing')
    expect(c.confidence).toBeGreaterThanOrEqual(0.5)
    expect(c.fallback_recommended).toBe(false)
    // dasha/transit/calibration intents default horizon → present.
    expect(c.scope_tuple.horizon).toBe('present')
  })

  it('detects domains (multi-value) and a remedy intervention', () => {
    const c = classifyScope('What gemstone remedy should I wear for my career and marriage?')
    expect(c.scope_tuple.intent).toBe('remedy_lookup')
    expect(c.scope_tuple.domains).toEqual(expect.arrayContaining(['career', 'marriage']))
    expect(c.scope_tuple.intervention).toBe('remedy')
  })

  it('is deterministic — identical input yields byte-identical output', () => {
    const q = 'Assess my career prospects in depth for the coming year.'
    expect(JSON.stringify(classifyScope(q))).toBe(JSON.stringify(classifyScope(q)))
  })
})

describe('classifyScope — fallback_recommended (drives ClarificationRequest)', () => {
  it('flags fallback_recommended for an empty query', () => {
    const c = classifyScope('   ')
    expect(c.confidence).toBe(0)
    expect(c.fallback_recommended).toBe(true)
    expect(c.scope_tuple.intent).toBe('unknown')
  })

  it('flags fallback_recommended for a genuinely ambiguous query (no intent match)', () => {
    const c = classifyScope('hey there, can you help me out with something?')
    expect(c.scope_tuple.intent).toBe('unknown')
    expect(c.fallback_recommended).toBe(true)
  })

  it('does NOT flag fallback_recommended for a clearly-classified query', () => {
    const c = classifyScope('Identify the raja yogas in my chart.')
    expect(c.scope_tuple.intent).toBe('yoga_identification')
    expect(c.fallback_recommended).toBe(false)
  })
})

describe('classifyScope — domain-inferred intent fallback (W6.1 fix-cycle)', () => {
  // Live E2E defect (native-directed, trace 6d1eb827-8c9c-4e98-b77e-7f5b5d689fbc,
  // the unscoped prashna_ask call): this exact phrase named 'career' but matched
  // no INTENT_RULES entry verbatim, so intent fell through to 'unknown' and
  // triggered an unnecessary clarification_needed.
  it('resolves a real domain-naming query to domain_assessment instead of unknown', () => {
    const c = classifyScope('What is my career direction and its timing over the next few years?')
    expect(c.scope_tuple.intent).toBe('domain_assessment')
    expect(c.scope_tuple.domains).toContain('career')
    expect(c.fallback_recommended).toBe(false)
    expect(c.matched_rules).toContain('intent:domain_assessment<-domain_inferred')
  })

  it('still resolves to unknown when no domain matches either (genuinely ambiguous)', () => {
    const c = classifyScope('hey there, can you help me out with something?')
    expect(c.scope_tuple.intent).toBe('unknown')
    expect(c.scope_tuple.domains).toEqual(['general'])
    expect(c.fallback_recommended).toBe(true)
  })

  it('never overrides an intent a specific rule already resolved', () => {
    // 'career' domain matches, but 'dasha' intent rule fires first and must win —
    // the domain-inferred fallback only applies when intent is still 'unknown'.
    const c = classifyScope('What does my current dasha period mean for my career?')
    expect(c.scope_tuple.intent).toBe('dasha_timing')
    expect(c.matched_rules).not.toContain('intent:domain_assessment<-domain_inferred')
  })
})
