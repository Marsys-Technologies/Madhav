/**
 * kala_now_get_sandhi_w1_joins.test.ts — ṢAḌ-DARŚANA W1 (SHAD_DARSHANA_BRIEF_v2_0.md §3 W1,
 * item 1-lite: "sandhi bands from existing period spans; full calendar W3").
 *
 * Tests the new kala_now_get join field added on top of tools/kala_views/now.ts's existing
 * thin facade: dasha_sandhi. A separate file from kala_now_get.test.ts / kala_now_get_w1_joins.test.ts
 * (not an edit to either) — this lane shares now.ts with several already-merged/in-flight
 * sibling lanes, and a new file carries far lower merge-conflict risk than editing an existing
 * suite.
 *
 * Contract gates:
 *   ✓ Gate W1 objectivity: dasha_sandhi is a raw computed interval + boolean membership flag —
 *     no favorable/unfavorable grading.
 *   ✓ Gate W1 acceptance: present-and-non-empty when the active MD/AD chain resolves,
 *     honest-empty (via `coverage`) when it doesn't.
 *   ✓ §N.5 / B.10 (JOIN, not new computation): band_start/band_end are pure arithmetic over
 *     the EXISTING start_date/end_date already returned by query_active_dashas — never a new
 *     astrological derivation.
 *   ✓ band_convention is served explicitly (documented default, not a silent/fabricated rule) —
 *     per KALA_SIX_VIEWS_DESIGN_v1_0.md §1.2's "configurable orb (last/first ~3% of period
 *     span)", with the lite simplification (each boundary uses ITS OWN period's span on both
 *     sides, rather than the full asymmetric outgoing/incoming two-period convention — that is
 *     item 1-full, wave W3) spelled out on the field itself.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { Principal } from '../types.js'
import { computeKalaNow } from '../tools/kala_views/now.js'

const TEST_CHART_ID = '00000000-0000-0000-0000-000000000001'
const TEST_PRINCIPAL: Principal = { user_uid: 'test-uid', key_id: 'test-key', role: 'guest' }

// MD span: 2020-01-01 .. 2036-01-01 (5844 days) -> 3% ~= 175 days.
// AD span: 2026-01-01 .. 2028-01-01 (730 days)  -> 3% ~= 22 days.
const ACTIVE_CHAIN = [
  { level_n: 1, level_name: 'Mahadasha', lord_graha: 'Jupiter', lord_sign: 'Cancer', start_date: '2020-01-01', end_date: '2036-01-01', start_iso: null, end_iso: null },
  { level_n: 2, level_name: 'Antardasha', lord_graha: 'Venus', lord_sign: 'Libra', start_date: '2026-01-01', end_date: '2028-01-01', start_iso: null, end_iso: null },
]

// Level 3/4 chain fixture — mirrors live-observed dates from DIAGNOSIS.md (F-121):
// chart 482012f1-…, as_of=2026-08-16, sandhi_flag=true at level_n=4 for 2026-08-13..2026-08-25.
const ACTIVE_CHAIN_WITH_SUKSHMA = [
  { level_n: 1, level_name: 'Mahadasha', lord_graha: 'Jupiter', lord_sign: 'Cancer', start_date: '2020-01-01', end_date: '2036-01-01', start_iso: null, end_iso: null },
  { level_n: 2, level_name: 'Antardasha', lord_graha: 'Venus', lord_sign: 'Libra', start_date: '2026-01-01', end_date: '2028-01-01', start_iso: null, end_iso: null },
  { level_n: 3, level_name: 'Pratyantardasha', lord_graha: 'Sun', lord_sign: 'Leo', start_date: '2026-07-01', end_date: '2026-09-15', start_iso: null, end_iso: null },
  // span=100d → 3% bandWidth=3d → period_start band Aug 10-16 includes as_of 2026-08-16
  { level_n: 4, level_name: 'Sukshma', lord_graha: 'Moon', lord_sign: 'Cancer', start_date: '2026-08-13', end_date: '2026-11-21', start_iso: null, end_iso: null },
]

function mockRegistryFetch(opts: { reachable: boolean; chainReachable?: boolean; chain?: typeof ACTIVE_CHAIN | [] }) {
  return vi.fn(async (_url: string, init?: RequestInit) => {
    if (!opts.reachable) throw new Error('registry unreachable in test')
    const body = JSON.parse(String(init?.body ?? '{}')) as { uri: string }
    let inner: Record<string, unknown> = {}
    if (body.uri === 'marsys://tool/L3/query_temporal_activation') {
      inner = { window_families: [], forward_windows: [] }
    } else if (body.uri === 'marsys://tool/L3/query_temporal_view') {
      inner = { rows: [] }
    } else if (body.uri === 'marsys://tool/L0/call_panchanga_service') {
      inner = { panchang: null, native_context: null }
    } else if (body.uri === 'marsys://tool/L1/get_panchanga') {
      inner = { rows: [] }
    } else if (body.uri === 'marsys://tool/L3/query_active_dashas') {
      if (opts.chainReachable === false) throw new Error('active-dasha registry unreachable in test')
      inner = { systems: [{ system_id: 'vimshottari', active_chain: opts.chain ?? ACTIVE_CHAIN }] }
    } else if (body.uri === 'marsys://tool/L1/get_dignity') {
      inner = { rows: [] }
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

describe('kala_now_get W1 join — dasha_sandhi (item 1-lite)', () => {
  it('reports a band around every MD/AD boundary, derived from existing period spans', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: true }))
    const result = await computeKalaNow(TEST_CHART_ID, { as_of: '2026-01-05' }, TEST_PRINCIPAL)
    expect(result.dasha_sandhi).not.toBeNull()
    expect(result.dasha_sandhi?.bands.length).toBe(4) // MD start, MD end, AD start, AD end
    const byBoundary = Object.fromEntries(
      (result.dasha_sandhi?.bands ?? []).map((b) => [`${b.level_name}:${b.boundary_kind}`, b]),
    )
    expect(byBoundary['Mahadasha:period_start']?.boundary_date).toBe('2020-01-01')
    expect(byBoundary['Mahadasha:period_end']?.boundary_date).toBe('2036-01-01')
    expect(byBoundary['Antardasha:period_start']?.boundary_date).toBe('2026-01-01')
    expect(byBoundary['Antardasha:period_end']?.boundary_date).toBe('2028-01-01')
  })

  it('band_width_days is ~3% of the boundary\'s own period span (documented lite convention)', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: true }))
    const result = await computeKalaNow(TEST_CHART_ID, { as_of: '2026-01-05' }, TEST_PRINCIPAL)
    const byBoundary = Object.fromEntries(
      (result.dasha_sandhi?.bands ?? []).map((b) => [`${b.level_name}:${b.boundary_kind}`, b]),
    )
    // AD span = 730 days; 3% = 21.9 -> round to 22
    expect(byBoundary['Antardasha:period_start']?.band_width_days).toBe(22)
    expect(byBoundary['Antardasha:period_end']?.band_width_days).toBe(22)
    // MD span = 5844 days; 3% = 175.32 -> round to 175
    expect(byBoundary['Mahadasha:period_start']?.band_width_days).toBe(175)
  })

  it('is_now_within_band=true when as_of falls inside the boundary\'s band', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: true }))
    // AD starts 2026-01-01, band is ±22 days -> 2026-01-05 is inside.
    const result = await computeKalaNow(TEST_CHART_ID, { as_of: '2026-01-05' }, TEST_PRINCIPAL)
    const byBoundary = Object.fromEntries(
      (result.dasha_sandhi?.bands ?? []).map((b) => [`${b.level_name}:${b.boundary_kind}`, b]),
    )
    expect(byBoundary['Antardasha:period_start']?.is_now_within_band).toBe(true)
  })

  it('is_now_within_band=false when as_of is nowhere near any boundary', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: true }))
    // 2027-06-15 is far from AD start (2026-01-01) and AD end (2028-01-01) bands (±22d),
    // and far from MD start/end bands (±175d around 2020-01-01 / 2036-01-01).
    const result = await computeKalaNow(TEST_CHART_ID, { as_of: '2027-06-15' }, TEST_PRINCIPAL)
    expect((result.dasha_sandhi?.bands ?? []).every((b) => b.is_now_within_band === false)).toBe(true)
  })

  it('serves an explicit, documented band_convention string (never a silent/unstated rule)', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: true }))
    const result = await computeKalaNow(TEST_CHART_ID, { as_of: '2026-01-05' }, TEST_PRINCIPAL)
    expect(result.dasha_sandhi?.band_convention).toEqual(expect.stringContaining('3%'))
    expect(result.dasha_sandhi?.band_convention).toEqual(expect.stringContaining('lite'))
    // F-121: band_convention now names the level scope (levels 1-4) and states level 5 is never computed
    expect(result.dasha_sandhi?.band_convention).toEqual(expect.stringContaining('Sūkṣma'))
    expect(result.dasha_sandhi?.band_convention).toEqual(expect.stringContaining('Prāṇa'))
  })

  it('coverage marks dasha_sandhi computed when the active chain resolves', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: true }))
    const result = await computeKalaNow(TEST_CHART_ID, { as_of: '2026-01-05' }, TEST_PRINCIPAL)
    const byConcept = Object.fromEntries(result.coverage.map((c) => [c.concept, c]))
    expect(byConcept['dasha_sandhi']?.state).toBe('computed')
  })

  it('honest_empty (never fabricated) when the active-dasha registry is unreachable', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: true, chainReachable: false }))
    const result = await computeKalaNow(TEST_CHART_ID, { as_of: '2026-01-05' }, TEST_PRINCIPAL)
    expect(result.dasha_sandhi).toBeNull()
    const byConcept = Object.fromEntries(result.coverage.map((c) => [c.concept, c]))
    expect(byConcept['dasha_sandhi']?.state).toBe('honest_empty')
    expect(byConcept['dasha_sandhi']?.reason?.length).toBeGreaterThan(0)
  })

  it('honest_empty when no active Vimśottarī MD/AD chain resolves for the chart/date', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: true, chain: [] }))
    const result = await computeKalaNow(TEST_CHART_ID, { as_of: '2026-01-05' }, TEST_PRINCIPAL)
    expect(result.dasha_sandhi).toBeNull()
    const byConcept = Object.fromEntries(result.coverage.map((c) => [c.concept, c]))
    expect(byConcept['dasha_sandhi']?.state).toBe('honest_empty')
  })

  it('requests max_level: 4 for fetchVimshottariMdAdBoundaries — regression guard against silent revert to 2', async () => {
    const mockFn = mockRegistryFetch({ reachable: true })
    vi.stubGlobal('fetch', mockFn)
    await computeKalaNow(TEST_CHART_ID, { as_of: '2026-08-16' }, TEST_PRINCIPAL)
    // computeKalaNow calls query_active_dashas twice: fetchActiveVimshottariChain (max_level:2) and
    // fetchVimshottariMdAdBoundaries (max_level:4). Assert the boundary-fetch call uses max_level:4.
    const qadBodies = mockFn.mock.calls
      .map(([, init]) => JSON.parse(String(init?.body ?? '{}')) as { uri: string; args?: Record<string, unknown> })
      .filter((b) => b.uri === 'marsys://tool/L3/query_active_dashas')
    const maxLevels = qadBodies.map((b) => b.args?.max_level)
    expect(maxLevels).toContain(4)
  })

  it('level-4 (Sūkṣma) band present with is_now_within_band: true when as_of falls inside active Sūkṣma period (F-121 regression guard)', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: true, chain: ACTIVE_CHAIN_WITH_SUKSHMA as typeof ACTIVE_CHAIN }))
    // as_of=2026-08-16 is inside Sukshma boundary 2026-08-13..2026-08-25 (DIAGNOSIS.md live observation)
    const result = await computeKalaNow(TEST_CHART_ID, { as_of: '2026-08-16' }, TEST_PRINCIPAL)
    const level4Bands = (result.dasha_sandhi?.bands ?? []).filter((b) => b.level_n === 4)
    expect(level4Bands.length).toBeGreaterThan(0)
    expect(level4Bands.some((b) => b.is_now_within_band === true)).toBe(true)
  })
})
