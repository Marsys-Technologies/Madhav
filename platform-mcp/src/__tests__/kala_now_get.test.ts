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

// item 8 (dual-reference gochara) + item 28 (daśā-lord transit condition) fixtures.
// Natal: Lagna=Aries(1), Moon=Aquarius(11). Currently-running: MD=Jupiter, AD=Venus.
const LAGNA_SIGN = 1
const MOON_SIGN = 11

const ACTIVE_CHAIN = [
  { level_n: 1, level_name: 'Mahadasha', lord_graha: 'Jupiter', lord_sign: 'Cancer', start_date: '2020-01-01', end_date: '2036-01-01' },
  { level_n: 2, level_name: 'Antardasha', lord_graha: 'Venus', lord_sign: 'Libra', start_date: '2026-01-01', end_date: '2028-01-01' },
]

const TRANSIT_BY_PLANET: Record<string, Record<string, unknown>> = {
  Sun: { date: AS_OF, sign_number: 5, degree_in_sign: 8.0, nakshatra_number: 11, is_retrograde: false },
  Moon: { date: AS_OF, sign_number: 11, degree_in_sign: 20.2, nakshatra_number: 25, is_retrograde: false },
  Mars: { date: AS_OF, sign_number: 3, degree_in_sign: 1.4, nakshatra_number: 6, is_retrograde: false },
  Mercury: { date: AS_OF, sign_number: 5, degree_in_sign: 15.0, nakshatra_number: 12, is_retrograde: true },
  Jupiter: { date: AS_OF, sign_number: 4, degree_in_sign: 12.5, nakshatra_number: 9, is_retrograde: false }, // Cancer -> exalted
  Venus: { date: AS_OF, sign_number: 6, degree_in_sign: 3.1, nakshatra_number: 14, is_retrograde: false }, // Virgo -> debilitated
  Saturn: { date: AS_OF, sign_number: 10, degree_in_sign: 5.0, nakshatra_number: 21, is_retrograde: false }, // Capricorn -> own sign
  Rahu: { date: AS_OF, sign_number: 12, degree_in_sign: 9.9, nakshatra_number: 27, is_retrograde: true },
  Ketu: { date: AS_OF, sign_number: 6, degree_in_sign: 9.9, nakshatra_number: 13, is_retrograde: true },
}

const DIGNITY_BY_GRAHA: Record<string, Record<string, unknown>> = {
  Jupiter: { graha: 'Jupiter', exaltation_sign: 'Cancer', debilitation_sign: 'Capricorn', own_signs: ['Sagittarius', 'Pisces'] },
  Venus: { graha: 'Venus', exaltation_sign: 'Pisces', debilitation_sign: 'Virgo', own_signs: ['Taurus', 'Libra'] },
}

function mockRegistryFetch(opts: { reachable: boolean }) {
  return vi.fn(async (url: string, init?: RequestInit) => {
    if (!opts.reachable) throw new Error('registry unreachable in test')
    const body = JSON.parse(String(init?.body ?? '{}')) as { uri?: string; args?: Record<string, unknown>; sql?: string; params?: unknown[] }

    if (String(url).includes('/api/mcp/db/query')) {
      const graha = String(body.params?.[0] ?? '')
      const row = Object.values(DIGNITY_BY_GRAHA).find((r) => String(r['graha']).toLowerCase() === graha.toLowerCase())
      return { ok: true, json: async () => ({ rows: row ? [row] : [] }), text: async () => '' } as Response
    }

    let inner: Record<string, unknown> = {}
    if (body.uri === 'marsys://tool/L3/query_temporal_activation') {
      inner = { window_families: [WINDOW_FAMILY], forward_windows: [] }
    } else if (body.uri === 'marsys://tool/L3/query_temporal_view') {
      inner = { rows: [DARSHANA_ROW] }
    } else if (body.uri === 'marsys://tool/L1/get_dignity') {
      inner = {
        rows: [
          { fact_subject: 'LAGNA', fact_key: 'sign_num', fact_value_num: LAGNA_SIGN, fact_id: 'fact-lagna' },
          { fact_subject: 'MOON', fact_key: 'sign_num', fact_value_num: MOON_SIGN, fact_id: 'fact-moon' },
        ],
      }
    } else if (body.uri === 'marsys://tool/L3/query_active_dashas') {
      inner = { systems: [{ system_id: 'vimshottari', active_chain: ACTIVE_CHAIN }] }
    } else if (body.uri === 'marsys://tool/L0/query_planet_transit') {
      const planet = String(body.args?.['planet'] ?? '')
      const row = TRANSIT_BY_PLANET[planet]
      inner = { rows: row ? [row] : [] }
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

  it('item 8/28: gochara_dual_reference rows are all-null (honest, one row per known graha) and dasha_lord_transit_condition is empty; coverage marks both honest_empty', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: false }))
    const result = await computeKalaNow(TEST_CHART_ID, { as_of: AS_OF }, TEST_PRINCIPAL)
    expect(result.gochara_dual_reference).toHaveLength(9)
    for (const row of result.gochara_dual_reference) {
      expect(row.transit_sign_number).toBeNull()
      expect(row.house_from_moon).toBeNull()
      expect(row.house_from_lagna).toBeNull()
    }
    expect(result.dasha_lord_transit_condition).toEqual([])
    const byConcept = Object.fromEntries(result.coverage.map((c) => [c.concept, c]))
    expect(byConcept['dual_reference_gochara']?.state).toBe('honest_empty')
    expect(byConcept['dasha_lord_current_transit_condition']?.state).toBe('honest_empty')
  })

  it('never fabricates a verdict when unreachable — verdict states honest absence', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: false }))
    const result = await computeKalaNow(TEST_CHART_ID, { as_of: AS_OF }, TEST_PRINCIPAL)
    expect(result.reading.verdict.tier).toBe('structural_prior')
    expect(result.reading.verdict.statement).toMatch(/No structural activation/)
  })
})

describe('kala_now_get — coverage honesty (not-yet-built concepts disclosed, never dropped)', () => {
  it('discloses transit_moorti as not_in_corpus', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: true }))
    const result = await computeKalaNow(TEST_CHART_ID, { as_of: AS_OF }, TEST_PRINCIPAL)
    const byConcept = Object.fromEntries(result.coverage.map((c) => [c.concept, c]))
    expect(byConcept['transit_moorti']?.state).toBe('not_in_corpus')
    expect(byConcept['transit_moorti']?.reason?.length).toBeGreaterThan(0)
  })

  // W1 item 1-lite: dasha_sandhi_bands graduated from not_in_corpus to a real [J] join
  // (see kala_now_get_sandhi_w1_joins.test.ts for the full contract) — this suite's default
  // mock ACTIVE_CHAIN resolves, so it is 'computed', not 'not_in_corpus', from here on.
  it('discloses dasha_sandhi as computed once the active MD/AD chain resolves', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: true }))
    const result = await computeKalaNow(TEST_CHART_ID, { as_of: AS_OF }, TEST_PRINCIPAL)
    const byConcept = Object.fromEntries(result.coverage.map((c) => [c.concept, c]))
    expect(byConcept['dasha_sandhi']?.state).toBe('computed')
  })
})

describe('kala_now_get — item 8 (dual-reference gochara, wave W1)', () => {
  it('reports all 9 grahas with house-from-moon AND house-from-lagna computed independently', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: true }))
    const result = await computeKalaNow(TEST_CHART_ID, { as_of: AS_OF }, TEST_PRINCIPAL)
    const rows = result.gochara_dual_reference
    expect(rows).toHaveLength(9)
    const jupiter = rows.find((r) => r.planet === 'Jupiter')
    // Jupiter transiting sign 4 (Cancer); lagna sign 1 -> house 4; moon sign 11 -> house 6.
    expect(jupiter?.transit_sign_number).toBe(4)
    expect(jupiter?.transit_sign_name).toBe('Cancer')
    expect(jupiter?.house_from_lagna).toBe(4)
    expect(jupiter?.house_from_moon).toBe(6)
    // The two references must be able to disagree — proves this is not a single silent default.
    expect(jupiter?.house_from_lagna).not.toBe(jupiter?.house_from_moon)
  })

  it('coverage marks dual_reference_gochara computed when both natal refs and transit are reachable', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: true }))
    const result = await computeKalaNow(TEST_CHART_ID, { as_of: AS_OF }, TEST_PRINCIPAL)
    const byConcept = Object.fromEntries(result.coverage.map((c) => [c.concept, c]))
    expect(byConcept['dual_reference_gochara']?.state).toBe('computed')
  })

  it('never grades favorable/unfavorable — objective house counts only (Gate W1: no judgment call)', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: true }))
    const result = await computeKalaNow(TEST_CHART_ID, { as_of: AS_OF }, TEST_PRINCIPAL)
    for (const row of result.gochara_dual_reference) {
      expect(Object.keys(row)).not.toContain('favorable')
      expect(Object.keys(row)).not.toContain('classification')
    }
  })
})

describe('kala_now_get — item 28 (daśā-lord current transit condition, wave W1)', () => {
  it('reports both MD and AD lords with their current transit sign/house/dignity', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: true }))
    const result = await computeKalaNow(TEST_CHART_ID, { as_of: AS_OF }, TEST_PRINCIPAL)
    const rows = result.dasha_lord_transit_condition
    expect(rows).toHaveLength(2)
    const md = rows.find((r) => r.level_name === 'Mahadasha')
    const ad = rows.find((r) => r.level_name === 'Antardasha')
    expect(md?.lord_graha).toBe('Jupiter')
    expect(md?.lord_natal_sign).toBe('Cancer')
    expect(md?.transit_sign_name).toBe('Cancer')
    expect(md?.dignity).toBe('exalted')
    expect(md?.as_of_date).toBe(AS_OF)
    expect(ad?.lord_graha).toBe('Venus')
    expect(ad?.transit_sign_name).toBe('Virgo')
    expect(ad?.dignity).toBe('debilitated')
  })

  it('coverage marks dasha_lord_current_transit_condition computed when the join resolves', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: true }))
    const result = await computeKalaNow(TEST_CHART_ID, { as_of: AS_OF }, TEST_PRINCIPAL)
    const byConcept = Object.fromEntries(result.coverage.map((c) => [c.concept, c]))
    expect(byConcept['dasha_lord_current_transit_condition']?.state).toBe('computed')
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
