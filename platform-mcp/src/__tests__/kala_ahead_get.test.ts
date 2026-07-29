/**
 * kala_ahead_get.test.ts — ṢAḌ-DARŚANA W0.4 (SHAD_DARSHANA_BRIEF_v2_0.md §0.4/§3 W0.4)
 *
 * Tests tools/kala_views/ahead.ts — `kala_ahead_get`, VIEW 2: AHEAD. Mirrors
 * kala_temporal_retrieval.test.ts's mock-fetch pattern (double-wrapped
 * `{ ok, content: { content, is_error } }` contract).
 *
 * Contract gates:
 *   ✓ computeKalaAhead re-presents EXISTING window_families/forward_windows and
 *     projection_families rows — no new field
 *   ✓ probability_tier → ArgumentEvidence.strength is a direct relabel of an EXISTING
 *     pre-computed field (never invented)
 *   ✓ unreachable registry → honest_empty coverage, never fabricated data
 *   ✓ forward_windows fallback used when window_families is empty
 *   ✓ tri_plane: interpretation_ref → kala_explain_get, prediction_ref null (AHEAD IS the
 *     prediction plane), intervention_ref → kala_elect_get
 *   ✓ falsifier derived from the leading projection's window_end (never fabricated)
 *   ✓ registerKalaAheadGetTool(server, principal) registers exactly 'kala_ahead_get'
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { Principal } from '../types.js'
import { computeKalaAhead, registerKalaAheadGetTool } from '../tools/kala_views/ahead.js'
import { isNoLever } from '../lib/kala_envelope.js'

const TEST_CHART_ID = '00000000-0000-0000-0000-000000000001'
const TEST_PRINCIPAL: Principal = { user_uid: 'test-uid', key_id: 'test-key', role: 'guest' }

const WINDOW_FAMILY = {
  window_start: '2027-01-01',
  window_end: '2027-03-01',
  window_peak: '2027-02-01',
  member_count: 2,
  member_signal_ids: ['sig-10', 'sig-11'],
  signature_classes: ['dasha_ingress'],
  domains: ['wealth'],
  max_orb_strength: 0.55,
}

const PROJECTION_FAMILY = {
  window_start: '2027-06-01',
  window_end: '2027-09-01',
  domain: 'career',
  member_count: 5,
  member_ids: ['proj-1', 'proj-2'],
  member_signal_ids: ['sig-20', 'sig-21'],
  probability_tier: 'tier_1_high' as const,
  max_effective_score: 71.2,
  narrative: { text: 'promotion window' },
  source_citation: 'x',
}

function mockRegistryFetch(opts: { reachable: boolean; emptyWindows?: boolean }) {
  return vi.fn(async (_url: string, init?: RequestInit) => {
    if (!opts.reachable) throw new Error('registry unreachable in test')
    const body = JSON.parse(String(init?.body ?? '{}')) as { uri: string }
    let inner: Record<string, unknown> = {}
    if (body.uri === 'marsys://tool/L3/query_temporal_activation') {
      inner = opts.emptyWindows
        ? { window_families: [], forward_windows: [WINDOW_FAMILY] }
        : { window_families: [WINDOW_FAMILY], forward_windows: [] }
    } else if (body.uri === 'marsys://tool/L3/query_projections') {
      inner = { projections: [], projection_families: [PROJECTION_FAMILY] }
    }
    return {
      ok: true,
      json: async () => ({ ok: true, content: { content: inner, is_error: false } }),
      text: async () => '',
    } as Response
  })
}

beforeEach(() => {
  vi.unstubAllGlobals()
})

describe('kala_ahead_get — thin-facade re-presentation (no new computation)', () => {
  it('projections array carries the EXACT projection_families row the registry returned', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: true }))
    const result = await computeKalaAhead(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    expect(result.projections).toEqual([PROJECTION_FAMILY])
  })

  it('windows array carries window_families verbatim when non-empty', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: true, emptyWindows: false }))
    const result = await computeKalaAhead(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    expect(result.windows).toEqual([WINDOW_FAMILY])
  })

  it('falls back to forward_windows when window_families is empty (the capability\'s own fallback, never re-derived)', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: true, emptyWindows: true }))
    const result = await computeKalaAhead(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    expect(result.windows).toEqual([WINDOW_FAMILY])
  })

  it('probability_tier tier_1_high maps to evidence strength "strong" — a direct relabel of an existing field', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: true }))
    const result = await computeKalaAhead(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    const projEvidence = result.reading.evidence.find((e) => e.claim.includes('career'))
    expect(projEvidence?.strength).toBe('strong')
  })

  it('evidence fact_ids trace verbatim to member_signal_ids/member_ids (§N.5)', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: true }))
    const result = await computeKalaAhead(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    const projEvidence = result.reading.evidence.find((e) => e.claim.includes('career'))
    expect(projEvidence?.fact_ids).toEqual([...PROJECTION_FAMILY.member_signal_ids, ...PROJECTION_FAMILY.member_ids])
  })
})

describe('kala_ahead_get — honest-empty on unreachable registry', () => {
  it('windows/projections are empty and coverage marks both honest_empty', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: false }))
    const result = await computeKalaAhead(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    expect(result.windows).toEqual([])
    expect(result.projections).toEqual([])
    const byConcept = Object.fromEntries(result.coverage.map((c) => [c.concept, c]))
    expect(byConcept['forward_temporal_windows']?.state).toBe('honest_empty')
    expect(byConcept['probabilistic_projections']?.state).toBe('honest_empty')
  })

  it('falsifier is null when no leading projection exists — never fabricated', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: false }))
    const result = await computeKalaAhead(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    expect(result.reading.falsifier).toBeNull()
  })
})

describe('kala_ahead_get — falsifier (derived from existing window bounds, never invented)', () => {
  it('falsifier resolves_by equals the leading projection\'s window_end', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: true }))
    const result = await computeKalaAhead(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    expect(result.reading.falsifier?.resolves_by).toBe(PROJECTION_FAMILY.window_end)
  })
})

describe('kala_ahead_get — coverage honesty (not-yet-built concepts disclosed, never dropped)', () => {
  it('discloses promise_gated_forecasting / dasha_lord_forward_transit_condition / sky_event_calendar / tithi_pravesa as not_in_corpus', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: true }))
    const result = await computeKalaAhead(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    const byConcept = Object.fromEntries(result.coverage.map((c) => [c.concept, c]))
    for (const key of [
      'promise_gated_forecasting',
      'dasha_lord_forward_transit_condition',
      'sky_event_calendar',
      'tithi_pravesa',
    ]) {
      expect(byConcept[key]?.state).toBe('not_in_corpus')
      expect(byConcept[key]?.reason?.length).toBeGreaterThan(0)
    }
  })
})

describe('kala_ahead_get — envelope contract (E3/E4/E5, item 43, §7 Living-LEL)', () => {
  it('tri_plane: prediction_ref is null (AHEAD IS the prediction plane)', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: true }))
    const result = await computeKalaAhead(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    expect(result.tri_plane.prediction_ref).toBeNull()
  })

  it('tri_plane: interpretation_ref points at kala_explain_get, intervention_ref at kala_elect_get', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: true }))
    const result = await computeKalaAhead(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    const interp = result.tri_plane.interpretation_ref
    const interv = result.tri_plane.intervention_ref
    expect(interp && !isNoLever(interp) ? interp.instrument : null).toBe('kala_explain_get')
    expect(interv && !isNoLever(interv) ? interv.instrument : null).toBe('kala_elect_get')
  })

  it('drill_pointers excludes no_lever entries and matches tri_plane', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: true }))
    const result = await computeKalaAhead(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    expect(result.drill_pointers.map((p) => p.instrument).sort()).toEqual(['kala_elect_get', 'kala_explain_get'])
  })

  it('horizon_years defaults to 5 and is echoed on the response', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: true }))
    const result = await computeKalaAhead(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    expect(result.horizon_years).toBe(5)
  })

  it('horizon_years is threaded through when supplied', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: true }))
    const result = await computeKalaAhead(TEST_CHART_ID, { horizon_years: 2 }, TEST_PRINCIPAL)
    expect(result.horizon_years).toBe(2)
  })

  it('calibration_maturity is the honest LEL-absent zero (no LEL join at W0)', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: true }))
    const result = await computeKalaAhead(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    expect(result.calibration_maturity.n_events).toBe(0)
    expect(result.calibration_maturity.event_class_coverage).toBe(0)
  })

  it('question_frame is echoed verbatim when supplied', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: true }))
    const qf = { domain: 'wealth', horizon: '90d' }
    const result = await computeKalaAhead(TEST_CHART_ID, { question_frame: qf }, TEST_PRINCIPAL)
    expect(result.question_frame).toEqual(qf)
  })

  it('reading_prose is composed via the shared argument_composer', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: true }))
    const result = await computeKalaAhead(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    expect(result.reading_prose.length).toBeGreaterThan(0)
    expect(result.reading_prose).toContain(result.reading.thesis.trim())
  })
})

describe('kala_ahead_get — tool registration', () => {
  it('registerKalaAheadGetTool(server, principal) registers exactly kala_ahead_get', () => {
    let registeredName: string | null = null
    const mockServer = {
      tool: (name: string) => { registeredName = name },
    } as unknown as McpServer
    registerKalaAheadGetTool(mockServer, TEST_PRINCIPAL)
    expect(registeredName).toBe('kala_ahead_get')
  })

  it('registers with (name, description, schema, handler) — 4 args', () => {
    let callArgs: unknown[] = []
    const mockServer = { tool: (...args: unknown[]) => { callArgs = args } } as unknown as McpServer
    registerKalaAheadGetTool(mockServer, TEST_PRINCIPAL)
    expect(callArgs).toHaveLength(4)
    expect(typeof callArgs[0]).toBe('string')
    expect(typeof callArgs[1]).toBe('string')
    expect(typeof callArgs[2]).toBe('object')
    expect(typeof callArgs[3]).toBe('function')
  })

  it('calls server.tool exactly once (no accidental double-registration)', () => {
    let callCount = 0
    const mockServer = { tool: () => { callCount++ } } as unknown as McpServer
    registerKalaAheadGetTool(mockServer, TEST_PRINCIPAL)
    expect(callCount).toBe(1)
  })
})
