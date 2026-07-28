/**
 * kala_now_get.test.ts — ṢAḌ-DARŚANA W0.4 (SHAD_DARSHANA_BRIEF_v2_0.md §0.4/§3 W0.4)
 *
 * Tests tools/kala_views/now.ts — `kala_now_get`, VIEW 1: NOW. Mirrors
 * kala_temporal_retrieval.test.ts's mock-fetch pattern: mocks /api/retrieval/capability,
 * dispatching by URI, matching the real double-wrapped `{ ok, content: { content, is_error } }`
 * contract (see kala_temporal_retrieval.test.ts's doc-comment for why the mock must match
 * this shape exactly — a single-wrapped mock lets an unwrap bug ship undetected).
 *
 * Contract gates:
 *   ✓ computeKalaNow re-presents EXISTING window_families / kala_darshana rows — no new field
 *   ✓ unreachable registry → honest_empty coverage, never fabricated data
 *   ✓ live registry → reading/evidence/verdict/tri_plane populated from real rows
 *   ✓ tri_plane: interpretation_ref null (NOW IS the interpretation plane), prediction_ref →
 *     kala_ahead_get, intervention_ref → kala_elect_get
 *   ✓ registerKalaNowGetTool(server, principal) registers exactly 'kala_now_get'
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { Principal } from '../types.js'
import { computeKalaNow, registerKalaNowGetTool } from '../tools/kala_views/now.js'
import { isNoLever } from '../lib/kala_envelope.js'

const TEST_CHART_ID = '00000000-0000-0000-0000-000000000001'
const TEST_PRINCIPAL: Principal = { user_uid: 'test-uid', key_id: 'test-key', role: 'guest' }
const AS_OF = '2026-07-29'

const WINDOW_FAMILY = {
  window_start: '2026-07-01',
  window_end: '2026-08-15',
  window_peak: '2026-07-20',
  member_count: 3,
  member_signal_ids: ['sig-1', 'sig-2', 'sig-3'],
  signature_classes: ['dasha_transit_conjunction'],
  domains: ['career'],
  max_orb_strength: 0.82,
}

const DARSHANA_ROW = {
  effective_score: 61.4,
  net_label: 'favorable',
  window_start: AS_OF,
  window_end: AS_OF,
  obstruction_summary: null,
  narrative: { text: 'ok' },
}

function mockRegistryFetch(opts: { reachable: boolean }) {
  return vi.fn(async (_url: string, init?: RequestInit) => {
    if (!opts.reachable) throw new Error('registry unreachable in test')
    const body = JSON.parse(String(init?.body ?? '{}')) as { uri: string }
    let inner: Record<string, unknown> = {}
    if (body.uri === 'marsys://tool/L3/query_temporal_activation') {
      inner = { window_families: [WINDOW_FAMILY], forward_windows: [] }
    } else if (body.uri === 'marsys://tool/L3/query_temporal_view') {
      inner = { rows: [DARSHANA_ROW] }
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

describe('kala_now_get — thin-facade re-presentation (no new computation)', () => {
  it('windows array carries the EXACT window_families row the registry returned — no re-derived fields added', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: true }))
    const result = await computeKalaNow(TEST_CHART_ID, { as_of: AS_OF }, TEST_PRINCIPAL)
    expect(result.windows).toEqual([WINDOW_FAMILY])
  })

  it('darshana carries the EXACT kala_darshana row the registry returned', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: true }))
    const result = await computeKalaNow(TEST_CHART_ID, { as_of: AS_OF }, TEST_PRINCIPAL)
    expect(result.darshana).toEqual(DARSHANA_ROW)
  })

  it('evidence fact_ids trace verbatim to member_signal_ids (§N.5 — never restates, only references)', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: true }))
    const result = await computeKalaNow(TEST_CHART_ID, { as_of: AS_OF }, TEST_PRINCIPAL)
    expect(result.reading.evidence[0]?.fact_ids).toEqual(WINDOW_FAMILY.member_signal_ids)
  })
})

describe('kala_now_get — honest-empty on unreachable registry', () => {
  it('windows/darshana are empty/null and coverage marks both honest_empty', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: false }))
    const result = await computeKalaNow(TEST_CHART_ID, { as_of: AS_OF }, TEST_PRINCIPAL)
    expect(result.windows).toEqual([])
    expect(result.darshana).toBeNull()
    const byConcept = Object.fromEntries(result.coverage.map((c) => [c.concept, c]))
    expect(byConcept['temporal_activation_windows']?.state).toBe('honest_empty')
    expect(byConcept['kala_darshana_confluence']?.state).toBe('honest_empty')
  })

  it('never fabricates a verdict when unreachable — verdict states honest absence', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: false }))
    const result = await computeKalaNow(TEST_CHART_ID, { as_of: AS_OF }, TEST_PRINCIPAL)
    expect(result.reading.verdict.tier).toBe('structural_prior')
    expect(result.reading.verdict.statement).toMatch(/No structural activation/)
  })
})

describe('kala_now_get — coverage honesty (not-yet-built concepts disclosed, never dropped)', () => {
  it('discloses dasha_sandhi_bands / transit_moorti / dual_reference_gochara as not_in_corpus', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: true }))
    const result = await computeKalaNow(TEST_CHART_ID, { as_of: AS_OF }, TEST_PRINCIPAL)
    const byConcept = Object.fromEntries(result.coverage.map((c) => [c.concept, c]))
    expect(byConcept['dasha_sandhi_bands']?.state).toBe('not_in_corpus')
    expect(byConcept['transit_moorti']?.state).toBe('not_in_corpus')
    expect(byConcept['dual_reference_gochara']?.state).toBe('not_in_corpus')
    for (const key of ['dasha_sandhi_bands', 'transit_moorti', 'dual_reference_gochara']) {
      expect(byConcept[key]?.reason?.length).toBeGreaterThan(0)
    }
  })
})

describe('kala_now_get — envelope contract (E3/E4/E5, item 43, §7 Living-LEL)', () => {
  it('tri_plane: interpretation_ref is null (NOW IS the interpretation plane)', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: true }))
    const result = await computeKalaNow(TEST_CHART_ID, { as_of: AS_OF }, TEST_PRINCIPAL)
    expect(result.tri_plane.interpretation_ref).toBeNull()
  })

  it('tri_plane: prediction_ref points at kala_ahead_get, intervention_ref at kala_elect_get', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: true }))
    const result = await computeKalaNow(TEST_CHART_ID, { as_of: AS_OF }, TEST_PRINCIPAL)
    const pred = result.tri_plane.prediction_ref
    const interv = result.tri_plane.intervention_ref
    expect(pred && !isNoLever(pred) ? pred.instrument : null).toBe('kala_ahead_get')
    expect(interv && !isNoLever(interv) ? interv.instrument : null).toBe('kala_elect_get')
  })

  it('drill_pointers is derived from tri_plane and excludes no_lever entries', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: true }))
    const result = await computeKalaNow(TEST_CHART_ID, { as_of: AS_OF }, TEST_PRINCIPAL)
    expect(result.drill_pointers.map((p) => p.instrument).sort()).toEqual(['kala_ahead_get', 'kala_elect_get'])
  })

  it('question_frame is echoed verbatim when supplied (E4 W0: accepted, not yet conditioning)', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: true }))
    const qf = { domain: 'career', intent_verb: 'should_i' }
    const result = await computeKalaNow(TEST_CHART_ID, { as_of: AS_OF, question_frame: qf }, TEST_PRINCIPAL)
    expect(result.question_frame).toEqual(qf)
  })

  it('question_frame defaults to null when omitted', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: true }))
    const result = await computeKalaNow(TEST_CHART_ID, { as_of: AS_OF }, TEST_PRINCIPAL)
    expect(result.question_frame).toBeNull()
  })

  it('calibration_maturity is the honest LEL-absent zero (no LEL join at W0)', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: true }))
    const result = await computeKalaNow(TEST_CHART_ID, { as_of: AS_OF }, TEST_PRINCIPAL)
    expect(result.calibration_maturity).toEqual({
      n_events: 0,
      prospective_resolutions: 0,
      event_class_coverage: 0,
      weights_version: null,
      skill_score: null,
    })
  })

  it('field_snapshot_id is a stable stub, non-empty', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: true }))
    const result = await computeKalaNow(TEST_CHART_ID, { as_of: AS_OF }, TEST_PRINCIPAL)
    expect(typeof result.field_snapshot_id).toBe('string')
    expect(result.field_snapshot_id.length).toBeGreaterThan(0)
  })

  it('reading_prose is composed via the shared argument_composer (non-empty, includes thesis)', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: true }))
    const result = await computeKalaNow(TEST_CHART_ID, { as_of: AS_OF }, TEST_PRINCIPAL)
    expect(result.reading_prose.length).toBeGreaterThan(0)
    expect(result.reading_prose).toContain(result.reading.thesis.trim())
  })
})

describe('kala_now_get — tool registration', () => {
  it('registerKalaNowGetTool(server, principal) registers exactly kala_now_get', () => {
    let registeredName: string | null = null
    const mockServer = {
      tool: (name: string) => { registeredName = name },
    } as unknown as McpServer
    registerKalaNowGetTool(mockServer, TEST_PRINCIPAL)
    expect(registeredName).toBe('kala_now_get')
  })

  it('registers with (name, description, schema, handler) — 4 args', () => {
    let callArgs: unknown[] = []
    const mockServer = { tool: (...args: unknown[]) => { callArgs = args } } as unknown as McpServer
    registerKalaNowGetTool(mockServer, TEST_PRINCIPAL)
    expect(callArgs).toHaveLength(4)
    expect(typeof callArgs[0]).toBe('string')
    expect(typeof callArgs[1]).toBe('string')
    expect(typeof callArgs[2]).toBe('object')
    expect(typeof callArgs[3]).toBe('function')
  })

  it('calls server.tool exactly once (no accidental double-registration)', () => {
    let callCount = 0
    const mockServer = { tool: () => { callCount++ } } as unknown as McpServer
    registerKalaNowGetTool(mockServer, TEST_PRINCIPAL)
    expect(callCount).toBe(1)
  })
})
