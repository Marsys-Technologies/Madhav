/**
 * bundle_adapters.test.ts — CR-39/CR-14 regression: holistic_bundle must thread chart_id
 * into every per-chart sub-tool call.
 * ============================================================================================
 * Root cause (confirmed live on chart 482012f1-710e-4a25-994a-93821f5871aa): MSR (query_signals
 * → msr_sql), CGM (get_cgm_subgraph → cgm_graph_walk), LEL (lel_query → L5/lel_query), PANCHANG
 * (query_panchanga → L1/get_panchanga), and DASHA (query_dasha_periods → L1/get_dashas) are all
 * scope:'per_chart' registry capabilities. The primitives dispatcher
 * (/api/mcp/primitives/[tool]/route.ts) 400s any per-chart primitive with CHART_REQUIRED when
 * chart_id is absent from both the request body and the X-MCP-Chart-Id header.
 * `executeHolisticBundle`'s `HolisticBundleParams.chart_id` was threaded into the bundle's cache
 * key but never into the actual `buildHolisticParams()` per-sub-tool params — so every one of
 * these five 400'd uniformly, while UCN/RM/CDLM (all routed through `vector_search` →
 * query_classical_texts, scope:'global') never needed chart_id and kept succeeding. This was NOT
 * a down/unreachable DB or sidecar — it was a wiring gap in this file.
 *
 * DB-free: mocks global fetch, so no real primitives route or DB is touched.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const PRINCIPAL = { user_uid: 'u-1', audience_tier: 'client', key_id: 'k-1' }

// Tool names that resolve to scope:'per_chart' registry capabilities (see tool_name_bridge.ts).
const PER_CHART_TOOL_NAMES = new Set([
  'query_signals',       // MSR → msr_sql
  'get_cgm_subgraph',    // CGM → cgm_graph_walk
  'lel_query',           // LEL → L5/lel_query
  'query_panchanga',     // PANCHANG → L1/get_panchanga
  'query_dasha_periods', // DASHA → L1/get_dashas
])

interface RecordedCall {
  url: string
  toolName: string
  body: Record<string, unknown>
}

function stubFetchCapturingPrimitiveCalls(): { calls: RecordedCall[] } {
  const calls: RecordedCall[] = []
  vi.stubGlobal('fetch', vi.fn(async (url: string, init?: RequestInit) => {
    if (url.includes('/api/mcp/bundles/cache/store')) {
      // storeCache() is fire-and-forget/non-fatal — just ack it.
      return { ok: true, status: 200, json: async () => ({ ok: true }) }
    }
    const rawBody = init?.body ? JSON.parse(String(init.body)) as Record<string, unknown> : {}
    // callPrimitive wraps params under { params } (F-127) so the primitives route
    // reads body.params correctly; unwrap here so assertions use flat param names.
    const body = (rawBody['params'] as Record<string, unknown>) ?? rawBody
    const toolName = url.split('/api/mcp/primitives/')[1] ?? 'unknown'
    calls.push({ url, toolName, body })
    return { ok: true, status: 200, json: async () => ({ ok: true, result: {} }) }
  }))
  return { calls }
}

beforeEach(() => {
  vi.resetModules()
})

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('executeHolisticBundle — CR-39/CR-14 chart_id threading', () => {
  it('includes chart_id in the request body for every per-chart sub-tool (MSR/CGM/LEL/PANCHANG/DASHA)', async () => {
    const { calls } = stubFetchCapturingPrimitiveCalls()
    const { executeHolisticBundle } = await import('../bundle_adapters')

    await executeHolisticBundle(
      { query_text: 'career outlook', tier: 'client', chart_id: CHART_ID },
      PRINCIPAL,
    )

    const perChartCalls = calls.filter(c => PER_CHART_TOOL_NAMES.has(c.toolName))
    // All five per-chart sub-tools must have fired (standard format runs all 8).
    expect(perChartCalls.map(c => c.toolName).sort()).toEqual(
      [...PER_CHART_TOOL_NAMES].sort(),
    )
    for (const call of perChartCalls) {
      expect(call.body['chart_id']).toBe(CHART_ID)
    }
  })

  it('does not require chart_id for the global vector_search sub-tools (UCN/RM/CDLM unaffected)', async () => {
    const { calls } = stubFetchCapturingPrimitiveCalls()
    const { executeHolisticBundle } = await import('../bundle_adapters')

    await executeHolisticBundle(
      { query_text: 'career outlook', tier: 'client', chart_id: CHART_ID },
      PRINCIPAL,
    )

    const vectorSearchCalls = calls.filter(c => c.toolName === 'vector_search')
    expect(vectorSearchCalls.length).toBe(3) // UCN, RM, CDLM
    for (const call of vectorSearchCalls) {
      expect(call.body['chart_id']).toBeUndefined()
    }
  })

  it('omits chart_id from per-chart sub-tool params when the bundle caller never supplied one (no fabrication)', async () => {
    const { calls } = stubFetchCapturingPrimitiveCalls()
    const { executeHolisticBundle } = await import('../bundle_adapters')

    await executeHolisticBundle(
      { query_text: 'career outlook', tier: 'client' }, // no chart_id
      PRINCIPAL,
    )

    const perChartCalls = calls.filter(c => PER_CHART_TOOL_NAMES.has(c.toolName))
    for (const call of perChartCalls) {
      expect(call.body['chart_id']).toBeUndefined()
    }
  })
})
