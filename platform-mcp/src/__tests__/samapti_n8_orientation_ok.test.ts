/**
 * samapti_n8_orientation_ok.test.ts — SAMĀPTI · lane B-N8-TS-SERVE · finding F-22.
 *
 * F-22 (A7-N8-AUDIT register §2.3): `orientation_ok` is named as THE B.11 Whole-Chart-Read
 * enforcement signal in registry_bridge.ts's own header prose ("B.11 enforcement: all
 * per_chart domain tools call fetchOrientationContext() before executing their domain
 * query"), but it was set to the literal `true` on the sole basis that the L2 `query_ucd`
 * call did not THROW. No assertion on contents.
 *
 * Three concrete false-green paths the old boolean could not distinguish from success —
 * each one is a test below:
 *
 *   1. `query_ucd`'s handler catches its own errors and RETURNS `{ content: { error },
 *      is_error: true }`. It does not throw. So the ordinary failure path never reached
 *      `fetchOrientationContext`'s catch, and an ERROR PAYLOAD read `orientation_ok: true`.
 *   2. An unbuilt / partially-built chart returns HTTP 200 with an empty digest, zero
 *      entity_profiles and zero convergence_domains — no holistic context whatsoever —
 *      and read `orientation_ok: true`.
 *   3. A payload echoing a DIFFERENT chart_id read `orientation_ok: true`.
 *
 * These tests exercise the extracted predicate `assessOrientationPayload` directly, which
 * is the whole of the decision `fetchOrientationContext` now delegates to it. Testing the
 * predicate rather than the network wrapper is deliberate: it is the same seam
 * `resolveOrientationFetchParams` was extracted for in SAMAPANA Track B ("pure helper so
 * the decision is unit-testable without mocking network I/O").
 */
import { describe, it, expect } from 'vitest'
import { assessOrientationPayload } from '../tools/registry_bridge.js'

const CHART = '482012f1-710e-4a25-994a-93821f5871aa'

/** The shape `callRegistryCapability` actually returns: the double-wrapped ToolResult. */
function wrap(inner: Record<string, unknown>, is_error = false) {
  return { content: inner, is_error }
}

/** A genuinely built chart's digest-format orientation payload. Note `top_signals: []` —
 *  `response_format: 'digest'` returns no atomic signals BY DESIGN, so substance must be
 *  read from entity_profiles / convergence_domains / digest counts, never from top_signals. */
const BUILT = wrap({
  chart_id: CHART,
  ayanamsha_id: 'lahiri_chitrapaksha',
  response_format: 'digest',
  digest: { msr_signal_count: 573, contradiction_count: 4 },
  entity_profiles: [{ entity: 'Saturn', entity_type: 'graha', fact_ids: ['f1'] }],
  top_signals: [],
  convergence_domains: [{ domain: 'career', convergence_score: 0.8 }],
})

describe('F-22 · assessOrientationPayload — the B.11 signal asserts its own claim', () => {
  it('ok for a genuinely built chart (digest format, top_signals legitimately empty)', () => {
    expect(assessOrientationPayload(BUILT, CHART)).toEqual({ ok: true, reason: null })
  })

  it('NOT ok for an in-band error payload — query_ucd returns errors, it does not throw', () => {
    const errorPayload = wrap({ error: 'relation "vw_chart_digest" does not exist', chart_id: CHART }, true)
    const a = assessOrientationPayload(errorPayload, CHART)
    expect(a.ok).toBe(false)
    expect(a.reason).toContain('error payload')
  })

  it('NOT ok for an error reported inside content even when is_error stayed false', () => {
    const a = assessOrientationPayload(wrap({ error: 'boom', chart_id: CHART }, false), CHART)
    expect(a.ok).toBe(false)
    expect(a.reason).toContain('reported an error')
  })

  it('NOT ok for an unbuilt chart: 200 + empty digest + zero profiles + zero convergence', () => {
    const unbuilt = wrap({
      chart_id: CHART,
      ayanamsha_id: 'lahiri_chitrapaksha',
      response_format: 'digest',
      digest: {},
      entity_profiles: [],
      top_signals: [],
      convergence_domains: [],
    })
    const a = assessOrientationPayload(unbuilt, CHART)
    expect(a.ok).toBe(false)
    expect(a.reason).toContain('unbuilt or only partially built')
  })

  it('NOT ok for a zero-count digest (msr_signal_count: 0 is absence, not context)', () => {
    const zeroed = wrap({
      chart_id: CHART,
      digest: { msr_signal_count: 0 },
      entity_profiles: [],
      convergence_domains: [],
    })
    expect(assessOrientationPayload(zeroed, CHART).ok).toBe(false)
  })

  it('NOT ok when the payload echoes a different chart_id', () => {
    const other = wrap({ ...(BUILT.content as Record<string, unknown>), chart_id: 'ffffffff-0000-0000-0000-000000000000' })
    const a = assessOrientationPayload(other, CHART)
    expect(a.ok).toBe(false)
    expect(a.reason).toContain('echoed chart_id')
  })

  it('NOT ok for a null / non-object payload', () => {
    expect(assessOrientationPayload(null, CHART).ok).toBe(false)
    expect(assessOrientationPayload(undefined, CHART).ok).toBe(false)
    expect(assessOrientationPayload('nope', CHART).ok).toBe(false)
  })

  it('ok is reached via ANY one substance surface — partial builds are not punished', () => {
    // convergence rows present, profiles empty
    expect(assessOrientationPayload(
      wrap({ chart_id: CHART, digest: {}, entity_profiles: [], convergence_domains: [{ domain: 'career' }] }),
      CHART,
    ).ok).toBe(true)
    // digest count present, everything else empty
    expect(assessOrientationPayload(
      wrap({ chart_id: CHART, digest: { msr_signal_count: 12 }, entity_profiles: [], convergence_domains: [] }),
      CHART,
    ).ok).toBe(true)
  })

  it('every not-ok verdict names a reason — never a silent false', () => {
    const notOk = [
      assessOrientationPayload(null, CHART),
      assessOrientationPayload(wrap({ error: 'x' }, true), CHART),
      assessOrientationPayload(wrap({ chart_id: CHART, digest: {}, entity_profiles: [], convergence_domains: [] }), CHART),
    ]
    for (const a of notOk) {
      expect(a.ok).toBe(false)
      expect(typeof a.reason).toBe('string')
      expect((a.reason ?? '').length).toBeGreaterThan(10)
    }
  })
})
