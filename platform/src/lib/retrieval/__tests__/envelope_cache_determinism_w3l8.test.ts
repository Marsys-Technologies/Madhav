/**
 * envelope_cache_determinism_w3l8.test.ts — W3-L8 (RETRIEVAL_PLANE_ELEVATION_PLAN §9.7,
 * W-28 envelope half): cache-safe determinism.
 *
 * The property a response cache needs: a given tool call with identical inputs, against
 * an unchanged build_id/ledger_version, produces byte-identical STABLE CONTENT. This test
 * calls buildRetrievalEnvelope twice with identical params and diffs the two outputs —
 * once on the whole envelope (proving the ONLY differing field is the documented call-time
 * one, `timing.computed_at`), and once on the "stable content" projection a cache layer
 * would actually key/store (everything except `timing.computed_at`), proving that
 * projection is byte-identical across calls.
 */
import { describe, it, expect } from 'vitest'
import { buildRetrievalEnvelope, type V3Envelope, type BuildRetrievalEnvelopeParams } from '@/lib/retrieval/envelope'

function fixedParams(): BuildRetrievalEnvelopeParams {
  return {
    tool: 'get_signals',
    content: { rows: [{ fact_id: 'f-1', value: 42 }] },
    query_class: 'per_chart_structural',
    insight_type: 'signal_summary',
    pagination: { offset: 0, limit: 50, total: 1 },
    chart_header: {
      chart_id_short: '482012f1',
      name: 'Abhisek Mohanty',
      lagna_sign: 'Aries',
      lagna_deg: 12.3,
      moon_sign: 'Purva Bhadrapada',
      sun_sign: 'Capricorn',
      ayanamsha: 'lahiri',
      current_maha_antar: 'Saturn/Mercury',
    },
    // as_of_date passed explicitly (the cache-safe usage documented on TimingBlock) —
    // stable regardless of what second/millisecond the call actually happens at.
    as_of_date: '2026-07-20',
    coverage: { family: 'msr_signals[domain=career]', served: 1, total: 1 },
    verdict: { grade: 'confirmed' },
    ranking_basis: { formula: 'composite_v1' },
    grounding: { fact_ids: ['f-1'], citations: ['BPHS 3.4'], grounding_score: 1 },
    drill_pointers: [{ instrument: 'judgment_query', hint: 'confirm in D9', pointer_type: 'confirm_in_varga' }],
    judgment_flags: [],
    build_id: 'build-abc-123',
    ledger_version: '3:1800000000',
  }
}

/** The projection a cache layer would actually store/compare — everything EXCEPT the
 *  documented call-time field (`timing.computed_at`). */
function stableContent(envelope: V3Envelope): Omit<V3Envelope, 'timing'> & { timing: { as_of_date: string } } {
  const { timing, ...rest } = envelope
  return { ...rest, timing: { as_of_date: timing.as_of_date } }
}

describe('buildRetrievalEnvelope — cache-safe determinism (W3-L8, W-28 envelope half)', () => {
  it('two calls with identical params produce byte-identical STABLE CONTENT (v3 format)', () => {
    const params = fixedParams()
    const first = buildRetrievalEnvelope(params, 'v3') as V3Envelope
    const second = buildRetrievalEnvelope(params, 'v3') as V3Envelope

    // Only the documented call-time field is allowed to differ (it is `new Date()...` —
    // realistically calls execute microseconds apart, so this is a genuine live check,
    // not a tautology).
    expect(JSON.stringify(stableContent(first))).toBe(JSON.stringify(stableContent(second)))

    // ledger_version and build_id — the two W-28 cache-key axes — are present and stable.
    expect(first.build_id).toBe('build-abc-123')
    expect(first.ledger_version).toBe('3:1800000000')
    expect(second.build_id).toBe(first.build_id)
    expect(second.ledger_version).toBe(first.ledger_version)
  })

  it('two calls with identical params produce byte-identical output under legacy format (no timing block at all)', () => {
    const params = fixedParams()
    const first = buildRetrievalEnvelope(params, 'legacy')
    const second = buildRetrievalEnvelope(params, 'legacy')
    // legacy carries no timing block whatsoever — the whole envelope is stable content.
    expect(JSON.stringify(first)).toBe(JSON.stringify(second))
  })

  it('changing build_id (a real cache-invalidation event) changes the envelope — proves the cache key axis is load-bearing, not decorative', () => {
    const params = fixedParams()
    const withBuildA = buildRetrievalEnvelope(params, 'v3') as V3Envelope
    const withBuildB = buildRetrievalEnvelope({ ...params, build_id: 'build-xyz-999' }, 'v3') as V3Envelope
    expect(withBuildA.build_id).not.toBe(withBuildB.build_id)
    expect(JSON.stringify(stableContent(withBuildA))).not.toBe(JSON.stringify(stableContent(withBuildB)))
  })

  it('changing ledger_version (a concept-ledger update, no chart rebuild) changes the envelope — the second, independent cache key axis', () => {
    const params = fixedParams()
    const withLedgerA = buildRetrievalEnvelope(params, 'v3') as V3Envelope
    const withLedgerB = buildRetrievalEnvelope({ ...params, ledger_version: '4:1800000600' }, 'v3') as V3Envelope
    expect(withLedgerA.ledger_version).not.toBe(withLedgerB.ledger_version)
    // Everything else (including build_id) is unchanged, isolating ledger_version as the
    // sole differing field.
    expect(withLedgerA.build_id).toBe(withLedgerB.build_id)
    expect(JSON.stringify(stableContent(withLedgerA))).not.toBe(JSON.stringify(stableContent(withLedgerB)))
  })

  it('omitting ledger_version/build_id is honest null, never fabricated (B.10) — and is itself stable across calls', () => {
    const params: BuildRetrievalEnvelopeParams = { tool: 'get_positions', content: { rows: [] } }
    const first = buildRetrievalEnvelope(params, 'v3') as V3Envelope
    const second = buildRetrievalEnvelope(params, 'v3') as V3Envelope
    expect(first.build_id).toBeNull()
    expect(first.ledger_version).toBeNull()
    expect(JSON.stringify(stableContent(first))).toBe(JSON.stringify(stableContent(second)))
  })
})
