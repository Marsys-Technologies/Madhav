/**
 * F-176 (PARISESA-V4) — promise_gate disclosure on kala_windows_get / kala_projections_get.
 *
 * VERIFICATION-FIRST FINDING, CONFIRMED for kala_projections_get. Live verification against
 * the canonical chart (482012f1-710e-4a25-994a-93821f5871aa, domain='relationship') found:
 *   - kala_projections_get served 2 tier_1_high projections with NO promise_gate key;
 *   - kala_ahead_get (F-110, same substrate) correctly served promise_gate.pact_status:
 *     'denied_at_promise', gating_scope:'horizon_invariant', contradicts_served_projections:true
 *     for the identical chart/domain;
 *   - pact_query independently confirmed pact_status:'denied_at_promise' (the refutation check
 *     did NOT refute the finding).
 *
 * kala_windows_get's exposure is narrower: its `forward_windows` fallback (query_temporal_
 * activation.ts:296-357) only fires when the primary `kala_activation` query returns zero rows.
 * Live testing across the canonical chart's entire kala_bhavishya-overlapping window found dated
 * activations densely cover that whole span for this chart/domain, so the fallback never actually
 * fired for the canonical chart — LATENT for that chart/domain, not exercised. This module gates
 * it anyway, defensively, using the SAME shared `computePromiseGate` (promise_gate.ts) — the tests
 * below exercise BOTH the "fallback fired" (gate attached) and "fallback did not fire" (no gate,
 * no extra pact_query call) paths.
 *
 * `fetch` is mocked globally, following the same pattern as
 * d1_6_s1_cr42_regressions.test.ts / kala_ahead_get_f110_promise_gate.test.ts.
 */
import { beforeAll, beforeEach, describe, expect, it, vi } from 'vitest'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { Principal } from '../types.js'

const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const principal: Principal = { user_uid: 'test-uid', key_id: 'mcp_test_key' }

const RELATIONSHIP_PROJECTION_FAMILY = {
  window_start: '2027-10-20',
  window_end: '2030-04-03',
  domain: 'relationship',
  member_count: 2,
  probability_tier: 'tier_1_high' as const,
  max_effective_score: 0.7,
  narrative: { headline: 'Relationship activation near 2027-10-20' },
  source_citation: 'ka_bhavishya_lekha:v1.0:rank=17',
}

const RELATIONSHIP_PROJECTIONS = [
  { id: '4346', domain: 'relationship', probability_tier: 'tier_1_high', effective_score: 0.7 },
  { id: '4368', domain: 'relationship', probability_tier: 'tier_1_high', effective_score: 0.7 },
]

const RELATIONSHIP_FORWARD_WINDOW = {
  id: '4346',
  signal_id: '2b9a44d4-b7f2-404a-9cda-05572c1b410d',
  domain: 'relationship',
  probability_tier: 'tier_1_high',
  effective_score: 0.7,
  window_start: '2027-10-20',
  window_end: '2030-04-03',
  peak_date: '2027-10-20',
}

/** Builds the fetch mock: routes by capability URI, exactly like the production proxy. */
function mockRegistryFetch(opts: {
  pact: string | 'unreachable' | 'no_status'
  windowsActivationsEmpty?: boolean
}) {
  return vi.fn(async (_url: string, init?: RequestInit) => {
    const body = JSON.parse(String(init?.body ?? '{}')) as { uri: string }
    if (body.uri === 'marsys://tool/L-PACT/pact_query') {
      if (opts.pact === 'unreachable') throw new Error('L-PACT unreachable in test')
      const inner = opts.pact === 'no_status'
        ? { about: { domain: 'relationship', bhava: 7 } }
        : { chart_id: CHART_ID, pact_status: opts.pact, stages: [{ stage: 'PROMISE', status: opts.pact === 'denied_at_promise' ? 'denied' : 'passed' }], fact_id_refs: ['d332fe1dbda74ea0'] }
      return { ok: true, json: async () => ({ ok: true, content: inner }), text: async () => '' } as unknown as Response
    }
    if (body.uri === 'marsys://tool/L3/query_projections') {
      return {
        ok: true,
        json: async () => ({
          ok: true,
          content: {
            content: {
              chart_id: CHART_ID,
              projections: RELATIONSHIP_PROJECTIONS,
              projection_count: RELATIONSHIP_PROJECTIONS.length,
              projection_families: [RELATIONSHIP_PROJECTION_FAMILY],
            },
            is_error: false,
          },
        }),
        text: async () => '',
      } as unknown as Response
    }
    if (body.uri === 'marsys://tool/L3/query_temporal_activation') {
      const activations = opts.windowsActivationsEmpty ? [] : [{ id: '1', signal_id: 'sig-1', activation_start: '2027-08-18', activation_end: '2028-01-15' }]
      const forward_windows = opts.windowsActivationsEmpty ? [RELATIONSHIP_FORWARD_WINDOW] : []
      return {
        ok: true,
        json: async () => ({
          ok: true,
          content: {
            content: { chart_id: CHART_ID, activations, forward_windows, window_families: [] },
            is_error: false,
          },
        }),
        text: async () => '',
      } as unknown as Response
    }
    throw new Error(`unexpected capability call in test: ${body.uri}`)
  })
}

describe('F-176 — kala_windows_get / kala_projections_get promise_gate', () => {
  const registeredHandlers = new Map<string, (params: Record<string, unknown>) => Promise<{ structuredContent: { object: Record<string, unknown> } }>>()

  beforeAll(async () => {
    const { registerP1AliasTools } = await import('../tools/register_p1_aliases.js')
    const mockServer = {
      tool: (name: string, _desc: string, _schema: Record<string, unknown>, handler: (params: Record<string, unknown>) => Promise<unknown>) => {
        registeredHandlers.set(name, handler as (params: Record<string, unknown>) => Promise<{ structuredContent: { object: Record<string, unknown> } }>)
      },
    } as unknown as McpServer
    registerP1AliasTools(mockServer, principal)
  })

  beforeEach(() => {
    mockFetch.mockReset()
  })

  describe('kala_projections_get', () => {
    it('denied_at_promise: emits promise_gate with contradicts_served_projections:true', async () => {
      mockFetch.mockImplementation(mockRegistryFetch({ pact: 'denied_at_promise' }))
      const handler = registeredHandlers.get('kala_projections_get')!
      const result = await handler({ chart_id: CHART_ID, domain: 'relationship' })
      const gate = result.structuredContent.object['promise_gate'] as Record<string, unknown>

      expect(gate).toBeDefined()
      expect(gate['state']).toBe('checked')
      expect(gate['pact_status']).toBe('denied_at_promise')
      expect(gate['gating_scope']).toBe('horizon_invariant')
      expect(gate['contradicts_served_projections']).toBe(true)
      // §N.5: the served rows themselves are untouched — never re-graded. Read from
      // `content.projections` (the primitive's real nesting), NOT the top-level
      // `projections` field this handler also sets — that field is always empty due to a
      // pre-existing, separate defect (it reads `projData['projections']`, but the
      // primitive nests the array under `projData['content']['projections']`) unrelated to
      // and out of scope for F-176; left untouched here.
      const content = result.structuredContent.object['content'] as Record<string, unknown>
      expect(content['projections']).toEqual(RELATIONSHIP_PROJECTIONS)
    })

    it('pact_query failure: state is unreachable, never smoothed to a clean/not_applicable result', async () => {
      mockFetch.mockImplementation(mockRegistryFetch({ pact: 'unreachable' }))
      const handler = registeredHandlers.get('kala_projections_get')!
      const result = await handler({ chart_id: CHART_ID, domain: 'relationship' })
      const gate = result.structuredContent.object['promise_gate'] as Record<string, unknown>

      expect(gate['state']).toBe('unreachable')
      expect(gate['join']).toBeNull()
      expect(gate['contradicts_served_projections']).toBe(false)
      expect(gate['reason']).toMatch(/not the same as checked-and-clear/)
    })

    it('chain_complete (no denial): gating_scope none, contradicts false', async () => {
      mockFetch.mockImplementation(mockRegistryFetch({ pact: 'chain_complete' }))
      const handler = registeredHandlers.get('kala_projections_get')!
      const result = await handler({ chart_id: CHART_ID, domain: 'relationship' })
      const gate = result.structuredContent.object['promise_gate'] as Record<string, unknown>

      expect(gate['gating_scope']).toBe('none')
      expect(gate['contradicts_served_projections']).toBe(false)
    })
  })

  describe('kala_windows_get', () => {
    it('forward_windows fallback fired (activations empty): emits promise_gate, contradicts true on denial', async () => {
      mockFetch.mockImplementation(mockRegistryFetch({ pact: 'denied_at_promise', windowsActivationsEmpty: true }))
      const handler = registeredHandlers.get('kala_windows_get')!
      const result = await handler({ chart_id: CHART_ID, domain: 'relationship', start_date: '2030-05-01', end_date: '2031-05-01' })
      const gate = result.structuredContent.object['promise_gate'] as Record<string, unknown>

      expect(gate).toBeDefined()
      expect(gate['state']).toBe('checked')
      expect(gate['pact_status']).toBe('denied_at_promise')
      expect(gate['contradicts_served_projections']).toBe(true)
      // The forward_windows rows themselves are untouched.
      const content = result.structuredContent.object['content'] as Record<string, unknown>
      expect(content['forward_windows']).toEqual([RELATIONSHIP_FORWARD_WINDOW])
    })

    it('forward_windows fallback NOT fired (activations non-empty, the canonical-chart-observed case): no promise_gate, no pact_query call', async () => {
      mockFetch.mockImplementation(mockRegistryFetch({ pact: 'denied_at_promise', windowsActivationsEmpty: false }))
      const handler = registeredHandlers.get('kala_windows_get')!
      const result = await handler({ chart_id: CHART_ID, domain: 'relationship', start_date: '2028-01-01', end_date: '2029-01-01' })

      expect(result.structuredContent.object['promise_gate']).toBeUndefined()
      // Nothing to gate ⇒ pact_query must not even be called (cost discipline, §5.3).
      const pactCalls = mockFetch.mock.calls.filter((c) => {
        const b = JSON.parse(String((c[1] as RequestInit).body)) as { uri: string }
        return b.uri === 'marsys://tool/L-PACT/pact_query'
      })
      expect(pactCalls.length).toBe(0)
    })

    it('pact_query failure on a fired fallback: state is unreachable, never smoothed', async () => {
      mockFetch.mockImplementation(mockRegistryFetch({ pact: 'unreachable', windowsActivationsEmpty: true }))
      const handler = registeredHandlers.get('kala_windows_get')!
      const result = await handler({ chart_id: CHART_ID, domain: 'relationship', start_date: '2030-05-01', end_date: '2031-05-01' })
      const gate = result.structuredContent.object['promise_gate'] as Record<string, unknown>

      expect(gate['state']).toBe('unreachable')
      expect(gate['join']).toBeNull()
      expect(gate['contradicts_served_projections']).toBe(false)
    })
  })
})
