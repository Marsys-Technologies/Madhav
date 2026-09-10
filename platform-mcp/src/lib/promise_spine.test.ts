/**
 * A-08 promise_spine.ts — unit tests
 *
 * Test contract per EKV A-08 spec:
 *   - kala_ahead × kala_upaya one reconciled verdict (verified via pure function)
 *   - no_contradictions certification impossible in a denied domain (INV-1)
 *   - §N.8: interpretPactJoin returns null (not a fabricated join) for
 *     non-PACT responses
 */

import { describe, it, expect } from 'vitest'
import { interpretPactJoin, type SaraPromiseJoin } from './promise_spine.js'

// ── helpers ──────────────────────────────────────────────────────────────────

function makePact(
  pact_status: string,
  stages: Array<{ stage: string; status?: string }> = [],
  fact_id_refs: string[] = [],
): Record<string, unknown> {
  return { pact_status, stages, fact_id_refs }
}

// ── null / invalid inputs ─────────────────────────────────────────────────────

describe('interpretPactJoin — null / invalid inputs', () => {
  it('returns null for null input (§N.8)', () => {
    expect(interpretPactJoin(null)).toBeNull()
  })

  it('returns null for non-object input', () => {
    expect(interpretPactJoin('string')).toBeNull()
    expect(interpretPactJoin(42)).toBeNull()
    expect(interpretPactJoin([])).toBeNull()
  })

  it('returns null when pact_status absent (not a PACT response)', () => {
    expect(interpretPactJoin({})).toBeNull()
    expect(interpretPactJoin({ other_field: 'value' })).toBeNull()
    expect(interpretPactJoin({ content: {} })).toBeNull()
    expect(interpretPactJoin({ content: { other_field: 'value' } })).toBeNull()
  })
})

// ── chain_complete ────────────────────────────────────────────────────────────

describe('interpretPactJoin — chain_complete', () => {
  it('maps to projection:supported, stance:consistent', () => {
    const result = interpretPactJoin(
      makePact('chain_complete', [
        { stage: 'PROMISE' }, { stage: 'CONFIRMATION' },
        { stage: 'ACTIVATION' }, { stage: 'TRIGGER' },
      ], ['f1', 'f2', 'f3'])
    )
    expect(result).not.toBeNull()
    const r = result as SaraPromiseJoin
    expect(r.projection).toBe('supported')
    expect(r.stance).toBe('consistent')
    expect(r.shared_fact_ids).toEqual(['f1', 'f2', 'f3'])
    expect(r.promise_verdict).toContain('complete')
    expect(r.promise_verdict).toContain('4/4')
  })
})

// ── INV-1: no_contradictions certification impossible in a denied domain ──────

describe('INV-1 — denied domains must carry stance:contradicts', () => {
  const deniedStatuses = [
    'denied_at_promise',
    'denied_at_confirmation',
    'denied_at_activation',
  ]

  it.each(deniedStatuses)('%s → projection:contradicted, stance:contradicts', (status) => {
    const result = interpretPactJoin(makePact(status, [], []))
    expect(result).not.toBeNull()
    const r = result as SaraPromiseJoin
    // INV-1: stance MUST be 'contradicts' for any denial
    expect(r.stance).toBe('contradicts')
    expect(r.stance).not.toBe('consistent') // no_contradictions cert impossible
    expect(r.projection).toBe('contradicted')
  })

  it('denied_at_promise includes PROMISE in the verdict', () => {
    const result = interpretPactJoin(makePact('denied_at_promise', [{ stage: 'PROMISE' }])) as SaraPromiseJoin
    expect(result.promise_verdict).toContain('PROMISE')
  })

  it('denied_at_confirmation includes CONFIRMATION in the verdict', () => {
    const result = interpretPactJoin(
      makePact('denied_at_confirmation', [{ stage: 'PROMISE' }, { stage: 'CONFIRMATION' }])
    ) as SaraPromiseJoin
    expect(result.promise_verdict).toContain('CONFIRMATION')
  })

  it('denied_at_activation includes ACTIVATION in the verdict', () => {
    const result = interpretPactJoin(
      makePact('denied_at_activation', [{ stage: 'PROMISE' }, { stage: 'CONFIRMATION' }, { stage: 'ACTIVATION' }])
    ) as SaraPromiseJoin
    expect(result.promise_verdict).toContain('ACTIVATION')
  })
})

// ── pending / infra states ────────────────────────────────────────────────────

describe('interpretPactJoin — pending / infra states', () => {
  it('chain_pending_activation → neutral/pending', () => {
    const result = interpretPactJoin(
      makePact('chain_pending_activation', [{ stage: 'PROMISE' }, { stage: 'CONFIRMATION' }])
    ) as SaraPromiseJoin
    expect(result.projection).toBe('neutral')
    expect(result.stance).toBe('pending')
    expect(result.promise_verdict).toContain('pending')
  })

  it('chain_incomplete_infra → neutral/pending with infrastructure note', () => {
    const result = interpretPactJoin(
      makePact('chain_incomplete_infra', [
        { stage: 'PROMISE' }, { stage: 'CONFIRMATION' },
        { stage: 'ACTIVATION' }, { stage: 'TRIGGER' },
      ])
    ) as SaraPromiseJoin
    expect(result.projection).toBe('neutral')
    expect(result.stance).toBe('pending')
    expect(result.promise_verdict).toContain('infrastructure')
    expect(result.promise_verdict).not.toContain('denied') // infra gap ≠ classical denial
  })
})

// ── content-wrapper envelope unwrapping ───────────────────────────────────────

describe('interpretPactJoin — content-wrapper unwrapping', () => {
  it('unwraps MCP content envelope', () => {
    const raw = {
      content: makePact('chain_complete', [{ stage: 'PROMISE' }], ['fa1', 'fa2']),
    }
    const result = interpretPactJoin(raw) as SaraPromiseJoin
    expect(result.projection).toBe('supported')
    expect(result.shared_fact_ids).toContain('fa1')
  })

  it('handles flat response (no content wrapper)', () => {
    const raw = makePact('denied_at_promise', [], [])
    const result = interpretPactJoin(raw) as SaraPromiseJoin
    expect(result.projection).toBe('contradicted')
  })

  it('prefers content wrapper when present and has pact_status', () => {
    const raw = {
      pact_status: 'chain_complete',       // outer — would be used without wrapper
      content: makePact('denied_at_promise', []), // inner takes precedence
    }
    const result = interpretPactJoin(raw) as SaraPromiseJoin
    // content wrapper takes precedence → denied_at_promise
    expect(result.projection).toBe('contradicted')
  })
})

// ── shared_fact_ids cap ───────────────────────────────────────────────────────

describe('interpretPactJoin — shared_fact_ids budget cap', () => {
  it('caps shared_fact_ids at 25 (full set in grounding envelope)', () => {
    const ids = Array.from({ length: 40 }, (_, i) => `fact_${i}`)
    const result = interpretPactJoin(makePact('chain_complete', [], ids)) as SaraPromiseJoin
    expect(result.shared_fact_ids).toHaveLength(25)
    expect(result.shared_fact_ids[0]).toBe('fact_0') // preserves order
  })

  it('returns all ids when fewer than 25', () => {
    const ids = ['a', 'b', 'c']
    const result = interpretPactJoin(makePact('chain_complete', [], ids)) as SaraPromiseJoin
    expect(result.shared_fact_ids).toEqual(['a', 'b', 'c'])
  })

  it('returns empty array when fact_id_refs absent', () => {
    const result = interpretPactJoin({ pact_status: 'chain_complete', stages: [] }) as SaraPromiseJoin
    expect(result.shared_fact_ids).toEqual([])
  })
})

// ── one reconciled verdict: kala_ahead × kala_upaya (EKV A-08 test contract) ─

describe('One reconciled verdict: kala_ahead × kala_upaya story', () => {
  /**
   * Both kala_ahead (what windows are opening?) and kala_upaya (what remedies
   * apply?) ask the same pact_query for the same (chart_id, domain). This test
   * verifies that a single interpretPactJoin call on that shared pact result
   * produces ONE reconciled verdict both views can embed as kernel.promise —
   * the "one voice" invariant.
   */
  it('same pact result → same SaraPromiseJoin for both callers (one voice)', () => {
    const sharedPactResult = makePact(
      'chain_complete',
      [{ stage: 'PROMISE' }, { stage: 'CONFIRMATION' },
       { stage: 'ACTIVATION' }, { stage: 'TRIGGER' }],
      ['f1', 'f2'],
    )
    // Both kala_ahead and kala_upaya interpret the SAME pact result
    const forAhead = interpretPactJoin(sharedPactResult) as SaraPromiseJoin
    const forUpaya = interpretPactJoin(sharedPactResult) as SaraPromiseJoin

    // One voice: same projection, same stance, same fact IDs
    expect(forAhead.projection).toBe(forUpaya.projection)
    expect(forAhead.stance).toBe(forUpaya.stance)
    expect(forAhead.shared_fact_ids).toEqual(forUpaya.shared_fact_ids)
    expect(forAhead.promise_verdict).toBe(forUpaya.promise_verdict)
  })

  it('denied domain: kala_upaya cannot certify no_contradictions (INV-1)', () => {
    const deniedPact = makePact('denied_at_promise', [{ stage: 'PROMISE' }])
    const forUpaya = interpretPactJoin(deniedPact) as SaraPromiseJoin
    // kala_upaya must not certify "no contradictions" — INV-1
    expect(forUpaya.stance).not.toBe('consistent')
    expect(forUpaya.projection).toBe('contradicted')
  })
})
