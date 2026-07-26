/**
 * envelope_verdict_receipt_dedup_mc023.test.ts — ŚODHANA T3 (MC-023 regression check).
 *
 * judgment_query (design §28.6) builds its top-level `verdict` v3-envelope extra by
 * SPREADING its own capability's `content.verdict` block plus a `receipt` field:
 * `{ ...verdictBlock, receipt, note }` — see registry_bridge.ts's judgment_query handler.
 * Nothing deletes the original `content.verdict` (nor `content.receipt`, frequently the SAME
 * object reference as `verdict.receipt`), so every v3 envelope shipped the verdict — and its
 * completeness receipt — TWICE: once at the top level, once nested under `content`.
 * `buildRetrievalEnvelope` now collapses a genuine duplicate down to a short pointer,
 * conservatively (only when every key of the nested copy deep-equals the top-level one) so a
 * `content.verdict` that legitimately differs from the top-level `verdict` is never touched.
 */
import { describe, it, expect } from 'vitest'
import { buildRetrievalEnvelope, type V3Envelope } from '../envelope'

describe('buildRetrievalEnvelope — MC-023 verdict/receipt de-duplication', () => {
  it('collapses content.verdict when it is a byte-identical duplicate (subset) of the top-level verdict', () => {
    const verdictBlock = { bhava: true, bhavesha: true, karaka: true }
    const receipt = { varga_confirmed: 'D9✓', timing_anchored: true }
    const topVerdict = { ...verdictBlock, receipt, note: 'deterministic verdict note' }

    const env = buildRetrievalEnvelope(
      {
        tool: 'judgment_query',
        content: { verdict: verdictBlock, receipt, checklist: { bearing_yogas: [] } },
        verdict: topVerdict,
      },
      'v3',
    ) as V3Envelope

    expect(env.verdict).toEqual(topVerdict) // top-level copy is untouched, still the canonical one
    const content = env.content as Record<string, unknown>
    expect(content['verdict']).not.toEqual(verdictBlock) // nested duplicate collapsed
    expect((content['verdict'] as Record<string, unknown>)['deduplicated']).toBe(true)
    expect(content['receipt']).not.toEqual(receipt) // nested receipt duplicate collapsed too
    expect((content['receipt'] as Record<string, unknown>)['deduplicated']).toBe(true)
    // The real checklist data (unrelated to verdict/receipt) is completely untouched.
    expect((content['checklist'] as Record<string, unknown>)['bearing_yogas']).toEqual([])
  })

  it('never touches a content.verdict that genuinely differs from the top-level verdict', () => {
    const differentNestedVerdict = { some_other_field: 'not a duplicate at all' }
    const topVerdict = { bhava: true, note: 'x' }

    const env = buildRetrievalEnvelope(
      { tool: 'some_other_tool', content: { verdict: differentNestedVerdict }, verdict: topVerdict },
      'v3',
    ) as V3Envelope

    const content = env.content as Record<string, unknown>
    expect(content['verdict']).toEqual(differentNestedVerdict) // untouched — not a duplicate
  })

  it('is a no-op when content has no verdict/receipt key at all', () => {
    const env = buildRetrievalEnvelope(
      { tool: 'get_signals', content: { rows: [1, 2, 3] }, verdict: { some: 'verdict' } },
      'v3',
    ) as V3Envelope
    expect(env.content).toEqual({ rows: [1, 2, 3] })
  })

  it('is a no-op under legacy format (top-level verdict is always null under legacy)', () => {
    const env = buildRetrievalEnvelope(
      { tool: 'judgment_query', content: { verdict: { a: 1 }, receipt: { b: 2 } } },
      'legacy',
    )
    expect(env.verdict).toBeNull()
    expect((env.content as Record<string, unknown>)['verdict']).toEqual({ a: 1 })
    expect((env.content as Record<string, unknown>)['receipt']).toEqual({ b: 2 })
  })
})
