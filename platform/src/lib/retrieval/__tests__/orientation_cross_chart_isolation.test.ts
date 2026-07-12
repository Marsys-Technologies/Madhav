/**
 * WP-0.1 — LCA-17 cross-chart substitution regression suite (findings F-0893,
 * F-0902, F-0905, F-0908).
 *
 * Defect: `get_chart_orientation` (retrieval tool `query_ucd`) intermittently
 * returned ANOTHER chart's digest. Root cause: the shared, module-level retrieval
 * result cache (`platform/src/lib/retrieval/cache.ts`) keyed entries with a weak
 * 32-bit rolling hash (`_hash`). Two DIFFERENT chart_ids whose argument objects
 * hash to the same 32-bit value collapse to the SAME cache key, so a concurrent
 * request for chart B reads chart A's cached, chart-A-stamped payload — a
 * cross-chart, entitlement-class data substitution. It is load-correlated
 * (collision probability rises with the number of co-resident keys) and never
 * appears in isolated single-chart probes (the colliding sibling is never
 * resident), exactly matching the audit's Lane-6 signature.
 *
 * These two chart_ids are REAL, distinct v4 UUIDs found by brute-force search
 * (~59k random UUIDs, matching the 32-bit birthday bound) to collide under the
 * pre-fix `_hash` for the exact argument object `query_ucd` builds for a
 * get_chart_orientation call. They model the class of concurrent different-chart
 * calls the deployed swarm hit. Under the fixed (SHA-256, full-width) key they no
 * longer collide.
 *
 * The suite exercises the REAL cacheKey / cacheGet / cacheSet on the REAL shared
 * cache, reproducing `query_ucd`'s exact read-through pattern (cache.ts callers:
 * query_ucd.ts:148-153,293 and query_signals.ts). It must show 0 substitutions
 * across N>=100 interleaved iterations.
 */

import { describe, it, expect, beforeEach } from 'vitest'
import { cacheKey, cacheGet, cacheSet, __clearRetrievalCache } from '../cache'

// Two DISTINCT real v4 UUIDs whose get_chart_orientation cache key collided under
// the pre-fix weak 32-bit hash (both mapped to `query_ucd::-aoxz7s`).
const COLLIDING_CHART_A = 'eaf4b85b-9549-4838-9439-3fab4b11572e'
const COLLIDING_CHART_B = '4b9bba4b-67ef-4c11-a4fe-05299f30780e'

// The two canonical charts the program uses (CLAUDE.md §B / L1_GANITA_CLOSURE).
const NATIVE_CHART = '482012f1-710e-4a25-994a-93821f5871aa' // Abhisek
const ABHINANDAN_CHART = '1c826d5a-41cb-4450-b4dc-59d440e5f75a' // verification

/** Exactly the argument object query_ucd.ts:148 builds for a default orientation call. */
function orientArgs(chart_id: string): Record<string, unknown> {
  return {
    chart_id,
    ayanamsha_id: 'lahiri_chitrapaksha',
    top_k_signals: 20,
    top_k_entities: 10,
    signal_class: undefined,
    min_salience: undefined,
    response_format: 'summary',
    priors_version: '1.0',
  }
}

/**
 * Faithful reproduction of query_ucd's cache read-through (cache.ts:152-153 +
 * 293): key the call, return any cached payload, else compute a chart-stamped
 * digest and cache it. The returned payload's `content.chart_id` is the identity
 * the LLM consumer reads — it MUST equal the requested chart_id.
 */
function orientationDigest(chart_id: string): { content: { chart_id: string; digest: string } } {
  const key = cacheKey('query_ucd', orientArgs(chart_id))
  const cached = cacheGet(key)
  if (cached !== undefined) return cached as { content: { chart_id: string; digest: string } }
  const result = { content: { chart_id, digest: `DIGEST_FOR_${chart_id}` } }
  cacheSet(key, result)
  return result
}

describe('WP-0.1 / LCA-17 — get_chart_orientation cross-chart isolation', () => {
  beforeEach(() => {
    __clearRetrievalCache()
  })

  it('cacheKey is chart-injective: two distinct chart_ids never share a key (F-0893)', () => {
    const keyA = cacheKey('query_ucd', orientArgs(COLLIDING_CHART_A))
    const keyB = cacheKey('query_ucd', orientArgs(COLLIDING_CHART_B))
    expect(COLLIDING_CHART_A).not.toBe(COLLIDING_CHART_B)
    expect(keyA).not.toBe(keyB)
  })

  it('no substitution across N>=100 interleaved calls for the known-colliding pair (F-0893/0902/0905/0908)', () => {
    const N = 120
    const substitutions: Array<{ i: number; requested: string; returned: string }> = []
    for (let i = 0; i < N; i++) {
      const requested = i % 2 === 0 ? COLLIDING_CHART_A : COLLIDING_CHART_B
      const returned = orientationDigest(requested).content.chart_id
      if (returned !== requested) substitutions.push({ i, requested, returned })
    }
    expect(substitutions).toEqual([])
  })

  it('no substitution across N>=100 interleaved calls for native + Abhinandan (F-0893)', () => {
    const N = 200
    const substitutions: Array<{ i: number; requested: string; returned: string }> = []
    for (let i = 0; i < N; i++) {
      const requested = i % 2 === 0 ? NATIVE_CHART : ABHINANDAN_CHART
      const returned = orientationDigest(requested).content.chart_id
      if (returned !== requested) substitutions.push({ i, requested, returned })
    }
    expect(substitutions).toEqual([])
  })

  it('concurrent (Promise.all) interleave of the colliding pair yields the requested chart every time', async () => {
    const N = 150
    const requests = Array.from({ length: N }, (_, i) =>
      i % 2 === 0 ? COLLIDING_CHART_A : COLLIDING_CHART_B,
    )
    const results = await Promise.all(
      requests.map(async (chart_id) => {
        // yield to the event loop so calls genuinely interleave
        await Promise.resolve()
        return { chart_id, returned: orientationDigest(chart_id).content.chart_id }
      }),
    )
    const bad = results.filter((r) => r.returned !== r.chart_id)
    expect(bad).toEqual([])
  })

  it('key sample: 5000 distinct random-shaped chart_ids produce 5000 distinct keys (collision-resistance)', () => {
    const keys = new Set<string>()
    for (let i = 0; i < 5000; i++) {
      // deterministic pseudo-UUIDs derived from a seed mixer (distinct inputs)
      const id = `${(i * 2654435761 >>> 0).toString(16).padStart(8, '0')}-0000-4000-8000-${i
        .toString(16)
        .padStart(12, '0')}`
      keys.add(cacheKey('query_ucd', orientArgs(id)))
    }
    expect(keys.size).toBe(5000)
  })
})
