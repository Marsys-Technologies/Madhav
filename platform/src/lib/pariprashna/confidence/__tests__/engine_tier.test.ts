/**
 * confidence/__tests__/engine_tier.test.ts — "new engine layers surface at
 * their earned tier" (lane G3-C, PPR-03 / roadmap G3-C line 103).
 *
 * Generation literals below (`'v1'`, `'v2'`, `'v3'`, `'g3_utkarsha'`) are the
 * REAL values seen in `src/lib/lel/prospective_ledger_w51_lel_sig.test.ts`
 * and the kala_gochara_authority / kala_gochara_windows generation-authority
 * mechanism `reading_checklist.ts#fetchGocharaSweep` reads live — not
 * invented for this test.
 */
import { describe, it, expect } from 'vitest'

import { capConfidenceTypeForEngineGeneration, isNonAuthoritativeEngineGeneration } from '../engine_tier'

describe('isNonAuthoritativeEngineGeneration', () => {
  it('true when the source generation differs from the chart\'s authoritative generation', () => {
    expect(isNonAuthoritativeEngineGeneration({ sourceGeneration: 'g3_utkarsha', authoritativeGeneration: 'v1' })).toBe(true)
  })

  it('false when the source generation IS the authoritative one', () => {
    expect(isNonAuthoritativeEngineGeneration({ sourceGeneration: 'v1', authoritativeGeneration: 'v1' })).toBe(false)
  })

  it('false (never assumes) when either generation is unknown', () => {
    expect(isNonAuthoritativeEngineGeneration({ sourceGeneration: null, authoritativeGeneration: 'v1' })).toBe(false)
    expect(isNonAuthoritativeEngineGeneration({ sourceGeneration: 'v3', authoritativeGeneration: null })).toBe(false)
  })
})

describe('capConfidenceTypeForEngineGeneration — a v3/experimental layer never surfaces above structural_prior', () => {
  it('caps deterministic_fact down to structural_prior for a non-authoritative gochara generation (v3 ahead of the chart\'s promoted v1)', () => {
    const capped = capConfidenceTypeForEngineGeneration('deterministic_fact', {
      sourceGeneration: 'v3',
      authoritativeGeneration: 'v1',
    })
    expect(capped).toBe('structural_prior')
  })

  it('caps empirically_calibrated down to structural_prior for a non-authoritative generation', () => {
    const capped = capConfidenceTypeForEngineGeneration('empirically_calibrated', {
      sourceGeneration: 'g3_utkarsha',
      authoritativeGeneration: 'v1',
    })
    expect(capped).toBe('structural_prior')
  })

  it('does NOT cap a proposed structural_prior, classical_prior, or unresolved — those tiers are already earned by a merely-present engine generation', () => {
    expect(capConfidenceTypeForEngineGeneration('structural_prior', { sourceGeneration: 'v3', authoritativeGeneration: 'v1' })).toBe('structural_prior')
    expect(capConfidenceTypeForEngineGeneration('classical_prior', { sourceGeneration: 'v3', authoritativeGeneration: 'v1' })).toBe('classical_prior')
    expect(capConfidenceTypeForEngineGeneration('unresolved', { sourceGeneration: 'v3', authoritativeGeneration: 'v1' })).toBe('unresolved')
  })

  it('does NOT cap when the source generation IS the chart\'s promoted/authoritative one', () => {
    expect(capConfidenceTypeForEngineGeneration('deterministic_fact', { sourceGeneration: 'v1', authoritativeGeneration: 'v1' })).toBe('deterministic_fact')
  })

  it('does NOT cap when generation is unknown on either side — an honest "cannot determine" never silently suppresses an earned type', () => {
    expect(capConfidenceTypeForEngineGeneration('deterministic_fact', { sourceGeneration: null, authoritativeGeneration: null })).toBe('deterministic_fact')
  })
})
