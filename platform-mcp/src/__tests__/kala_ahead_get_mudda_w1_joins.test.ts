/**
 * kala_ahead_get_mudda_w1_joins.test.ts — ṢAḌ-DARŚANA W1 (SHAD_DARSHANA_BRIEF_v2_0.md §3 W1,
 * item 30: "Mudda daśā joined to the varsha (annual/Tājika) plane").
 *
 * Tests the new kala_ahead_get join field added on top of tools/kala_views/ahead.ts's existing
 * thin facade: mudda_dasha_varsha. A separate file from kala_ahead_get.test.ts /
 * kala_ahead_get_w1_joins.test.ts (not an edit to either) — this lane shares ahead.ts with
 * several already-merged/in-flight sibling lanes, and a new file carries far lower
 * merge-conflict risk than editing an existing suite.
 *
 * Design authority: KALA_SIX_VIEWS_DESIGN_v2_0.md §E ("AHEAD — add: ... Mudda daśā inside
 * each varsha (the Tājika micro-clock, already computed as one of the 8 systems, never
 * joined)"). Pure [J] JOIN over two already-computed substrates:
 *   - marsys://tool/L1/get_tajik (l1_tajik_varsha_year_lords — varsha_year, year_lord,
 *     muntha_sign/house, varsha window) — the SAME substrate ganita_tajaka_get already serves.
 *   - marsys://tool/L3/query_active_dashas (system_id='mudda', already one of the 9 systems
 *     chart_dashas carries — the SAME substrate query_active_dashas already serves for
 *     vimshottari elsewhere in this facade/now.ts).
 * No new astrological computation (§N.5 / B.10) — every field traces verbatim to one of these
 * two existing capabilities' own output.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { Principal } from '../types.js'
import { computeKalaAhead } from '../tools/kala_views/ahead.js'

const TEST_CHART_ID = '00000000-0000-0000-0000-000000000001'
const TEST_PRINCIPAL: Principal = { user_uid: 'test-uid', key_id: 'test-key', role: 'guest' }

const VARSHA_ROW = {
  varsha_id: 'varsha-uuid-1',
  chart_id: TEST_CHART_ID,
  varsha_year: 42,
  varsha_start_iso: '2026-02-05T00:00:00Z',
  varsha_end_iso: '2027-02-05T00:00:00Z',
  year_lord: 'Saturn',
  muntha_sign: 'Aquarius',
  muntha_house: 11,
}

const MUDDA_CHAIN = [
  { level_n: 1, level_name: 'Mahadasha', lord_graha: 'Saturn', lord_sign: 'Aquarius', start_date: '2026-02-05', end_date: '2027-02-05', start_iso: null, end_iso: null },
  { level_n: 2, level_name: 'Antardasha', lord_graha: 'Mercury', lord_sign: 'Aquarius', start_date: '2026-06-01', end_date: '2026-08-01', start_iso: null, end_iso: null },
]

function mockRegistryFetch(opts: {
  reachable: boolean
  tajikReachable?: boolean
  muddaReachable?: boolean
  varshaRows?: Array<Record<string, unknown>>
  muddaChain?: typeof MUDDA_CHAIN
}) {
  return vi.fn(async (_url: string, init?: RequestInit) => {
    if (!opts.reachable) throw new Error('registry unreachable in test')
    const body = JSON.parse(String(init?.body ?? '{}')) as { uri: string }
    let inner: Record<string, unknown> = {}
    if (body.uri === 'marsys://tool/L3/query_temporal_activation') {
      inner = { window_families: [], forward_windows: [] }
    } else if (body.uri === 'marsys://tool/L3/query_projections') {
      inner = { projection_families: [] }
    } else if (body.uri === 'marsys://tool/L1/get_dignity') {
      inner = { rows: [] }
    } else if (body.uri === 'marsys://tool/L1/get_tajik') {
      if (opts.tajikReachable === false) throw new Error('tajik registry unreachable in test')
      inner = { varsha_year_lords: { rows: opts.varshaRows ?? [VARSHA_ROW] } }
    } else if (body.uri === 'marsys://tool/L3/query_active_dashas') {
      if (opts.muddaReachable === false) throw new Error('mudda active-dasha registry unreachable in test')
      inner = { systems: [{ system_id: 'mudda', active_chain: opts.muddaChain ?? MUDDA_CHAIN }] }
    } else if (body.uri === 'marsys://tool/L0/query_planet_transit') {
      inner = { rows: [] }
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

describe('kala_ahead_get W1 join — mudda_dasha_varsha (item 30)', () => {
  it('joins the current varsha context (year_lord, muntha) with the active Mudda daśā chain, verbatim', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: true }))
    const result = await computeKalaAhead(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    expect(result.mudda_dasha_varsha).toEqual({
      varsha_year: 42,
      varsha_start_iso: '2026-02-05T00:00:00Z',
      varsha_end_iso: '2027-02-05T00:00:00Z',
      year_lord: 'Saturn',
      muntha_sign: 'Aquarius',
      muntha_house: 11,
      as_of_date: expect.any(String),
      mudda_chain: [
        { level_n: 1, level_name: 'Mahadasha', lord_graha: 'Saturn', lord_sign: 'Aquarius', start_date: '2026-02-05', end_date: '2027-02-05' },
        { level_n: 2, level_name: 'Antardasha', lord_graha: 'Mercury', lord_sign: 'Aquarius', start_date: '2026-06-01', end_date: '2026-08-01' },
      ],
    })
  })

  it('coverage marks mudda_dasha_varsha computed when both sources resolve', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: true }))
    const result = await computeKalaAhead(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    const byConcept = Object.fromEntries(result.coverage.map((c) => [c.concept, c]))
    expect(byConcept['mudda_dasha_varsha']?.state).toBe('computed')
  })

  it('honest_empty (never fabricated) when the Tajaka varsha registry is unreachable', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: true, tajikReachable: false }))
    const result = await computeKalaAhead(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    expect(result.mudda_dasha_varsha).toBeNull()
    const byConcept = Object.fromEntries(result.coverage.map((c) => [c.concept, c]))
    expect(byConcept['mudda_dasha_varsha']?.state).toBe('honest_empty')
    expect(byConcept['mudda_dasha_varsha']?.reason?.length).toBeGreaterThan(0)
  })

  it('honest_empty when no varsha_year_lords row resolves for the current date', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: true, varshaRows: [] }))
    const result = await computeKalaAhead(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    expect(result.mudda_dasha_varsha).toBeNull()
    const byConcept = Object.fromEntries(result.coverage.map((c) => [c.concept, c]))
    expect(byConcept['mudda_dasha_varsha']?.state).toBe('honest_empty')
  })

  it('honest_empty when the Mudda active-dasha chain is unreachable, even if varsha context resolved', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: true, muddaReachable: false }))
    const result = await computeKalaAhead(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    expect(result.mudda_dasha_varsha).toBeNull()
    const byConcept = Object.fromEntries(result.coverage.map((c) => [c.concept, c]))
    expect(byConcept['mudda_dasha_varsha']?.state).toBe('honest_empty')
  })

  it('honest_empty when the Mudda chain resolves but is empty (no active row for this date)', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: true, muddaChain: [] }))
    const result = await computeKalaAhead(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    expect(result.mudda_dasha_varsha).toBeNull()
    const byConcept = Object.fromEntries(result.coverage.map((c) => [c.concept, c]))
    expect(byConcept['mudda_dasha_varsha']?.state).toBe('honest_empty')
  })
})
