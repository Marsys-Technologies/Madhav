/**
 * kala_ahead_get_period_echo_w3.test.ts — ṢAḌ-DARŚANA W3 (SHAD_DARSHANA_BRIEF_v2_0.md §3 W3,
 * item 31: "Period-echo mining (hypothesis-framed)").
 *
 * Tests the new kala_ahead_get join field added on top of tools/kala_views/ahead.ts's
 * existing thin facade: period_echo. A separate file from kala_ahead_get.test.ts (not an
 * edit to it) — this lane shares ahead.ts with several already-merged/in-flight sibling
 * lanes, and a new file carries far lower merge-conflict risk than editing the existing
 * suite (same convention kala_ahead_get_w1_joins.test.ts documents for item 32).
 *
 * Contract gates:
 *   ✓ Genuinely field-independent: no kala_field/ka_kshetra dispatch appears anywhere in
 *     this test's mock — every field is joined from get_dashas / query_life_arc / lel_query.
 *   ✓ LAW ZERO / hypothesis discipline: `hypothesis` is populated ONLY alongside
 *     `status: 'hypothesis_served'`; a level with zero qualifying prior occurrences reports
 *     `insufficient_data` with `hypothesis: null` — never an invented match.
 *   ✓ Pre-birth exclusion: a same-lord row that starts before the resolved birth-year floor
 *     is excluded from `same_lord_past_occurrence_count` and never appears in `candidates`.
 *   ✓ Birth-floor-unresolved is a hard withhold (insufficient_data), even when the lord-level
 *     query itself returned rows — never a silent risk of citing a pre-birth period.
 *   ✓ LEL corroboration is additive, never required: candidates are still served (structural
 *     echo) when LEL is empty/unreachable, with an honest zero/unavailable count, never
 *     fabricated.
 *   ✓ coverage: 'period_echo_mining' is `computed` only when ≥1 level actually served a
 *     hypothesis; every-level-insufficient_data is honest_empty, not silently upgraded.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { Principal } from '../types.js'
import { computeKalaAhead } from '../tools/kala_views/ahead.js'

const TEST_CHART_ID = '00000000-0000-0000-0000-000000000001'
const TEST_PRINCIPAL: Principal = { user_uid: 'test-uid', key_id: 'test-key', role: 'guest' }

// Currently running: Mercury Mahādaśā (2010-08-17..2027-08-17), Saturn Antardaśā
// (2024-12-07..2027-08-17) — shaped after the native's real canonical chain (482012f1).
const ACTIVE_CHAIN = [
  { level_n: 1, level_name: 'Mahadasha', lord_graha: 'Mercury', lord_sign: 'Virgo', start_date: '2010-08-17', end_date: '2027-08-17' },
  { level_n: 2, level_name: 'Antardasha', lord_graha: 'Saturn', lord_sign: 'Capricorn', start_date: '2024-12-07', end_date: '2027-08-17' },
]

// get_dashas rows for level=2 lord_graha=Saturn: one pre-birth row (must be excluded), one
// genuine lived past occurrence (1991-08-17..1994-08-20), and the currently-running row itself
// (must be excluded — not a completed PRIOR occurrence).
const SATURN_AD_ROWS = [
  { lord_graha: 'Saturn', level_n: 2, start_date: '1962-09-23', end_date: '1965-07-30' }, // pre-birth
  { lord_graha: 'Saturn', level_n: 2, start_date: '1991-08-17', end_date: '1994-08-20' }, // lived past occurrence
  { lord_graha: 'Saturn', level_n: 2, start_date: '2024-12-07', end_date: '2027-08-17' }, // currently running
]

// get_dashas rows for level=1 lord_graha=Mercury: only the currently-running MD — no prior
// occurrence (the structurally-expected Mahādaśā case).
const MERCURY_MD_ROWS = [
  { lord_graha: 'Mercury', level_n: 1, start_date: '2010-08-17', end_date: '2027-08-17' },
]

const LEL_EVENTS = [
  {
    event_id: 'lel-1', event_date: '1992-06-01', category: 'career', domain: 'career/first_job_joined',
    event_type: 'milestone', description: 'Started first job.', source_citation: 'LEL v1.7 #12',
  },
]

const BIRTH_YEAR_PARVA = [{ parva_index: 1, dasha_planet: 'Jupiter', start_year: 1984, end_year: 1991 }]

interface MockOpts {
  reachable?: boolean
  getDashasReachable?: boolean
  lifeArcReachable?: boolean
  lelReachable?: boolean
  lelEvents?: typeof LEL_EVENTS
  saturnAdRows?: typeof SATURN_AD_ROWS
}

function mockRegistryFetch(opts: MockOpts) {
  return vi.fn(async (url: string, init?: RequestInit) => {
    if (opts.reachable === false) throw new Error('registry unreachable in test')
    const body = JSON.parse(String(init?.body ?? '{}')) as { uri?: string; args?: Record<string, unknown> }

    if (String(url).includes('/api/mcp/db/query')) {
      return { ok: true, json: async () => ({ rows: [] }), text: async () => '' } as Response
    }

    let inner: Record<string, unknown> = {}
    if (body.uri === 'marsys://tool/L3/query_temporal_activation') {
      inner = { window_families: [], forward_windows: [] }
    } else if (body.uri === 'marsys://tool/L3/query_projections') {
      inner = { projection_families: [] }
    } else if (body.uri === 'marsys://tool/L1/get_dignity') {
      inner = { rows: [{ fact_subject: 'LAGNA', fact_key: 'sign_num', fact_value_num: 1, fact_id: 'fact-lagna' }] }
    } else if (body.uri === 'marsys://tool/L0/call_panchanga_service') {
      inner = { panchangs: [], count: 0 }
    } else if (body.uri === 'marsys://tool/L3/query_active_dashas') {
      const args = body.args as { systems?: string } | undefined
      if (args?.systems === 'mudda') {
        inner = { systems: [] }
      } else {
        inner = { systems: [{ system_id: 'vimshottari', active_chain: ACTIVE_CHAIN }] }
      }
    } else if (body.uri === 'marsys://tool/L0/query_planet_transit') {
      inner = { rows: [] }
    } else if (body.uri === 'marsys://tool/L1/get_tajik') {
      inner = { rows: [] }
    } else if (body.uri === 'marsys://tool/L1/get_dashas') {
      if (opts.getDashasReachable === false) throw new Error('get_dashas unreachable in test')
      const args = body.args as { level?: number; lord_graha?: string } | undefined
      if (args?.level === 2 && args?.lord_graha === 'Saturn') {
        inner = { rows: opts.saturnAdRows ?? SATURN_AD_ROWS, total: (opts.saturnAdRows ?? SATURN_AD_ROWS).length }
      } else if (args?.level === 1 && args?.lord_graha === 'Mercury') {
        inner = { rows: MERCURY_MD_ROWS, total: MERCURY_MD_ROWS.length }
      } else {
        inner = { rows: [], total: 0 }
      }
    } else if (body.uri === 'marsys://tool/L3/query_life_arc') {
      if (opts.lifeArcReachable === false) throw new Error('query_life_arc unreachable in test')
      inner = { parvas: BIRTH_YEAR_PARVA }
    } else if (body.uri === 'marsys://tool/L5/lel_query') {
      if (opts.lelReachable === false) throw new Error('lel_query unreachable in test')
      inner = { events: opts.lelEvents ?? LEL_EVENTS, has_more: false, total_matching: (opts.lelEvents ?? LEL_EVENTS).length }
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

describe('kala_ahead_get item 31 — period_echo (hypothesis-framed, field-independent)', () => {
  it('serves one period_echo entry per active-chain level (Mahadasha + Antardasha)', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({}))
    const result = await computeKalaAhead(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    expect(result.period_echo).toHaveLength(2)
    expect(result.period_echo.map((e) => e.level_name).sort()).toEqual(['Antardasha', 'Mahadasha'])
  })

  it('Antardasha (Saturn, has a lived past occurrence) serves a hypothesis, never a verdict/prediction', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({}))
    const result = await computeKalaAhead(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    const ad = result.period_echo.find((e) => e.level_n === 2)
    expect(ad?.status).toBe('hypothesis_served')
    expect(ad?.hypothesis).toMatch(/^Hypothesis:/)
    expect(ad?.hypothesis).toContain('not a prediction')
    expect(ad?.hypothesis).not.toMatch(/will happen|guaranteed|verified true/i)
  })

  it('excludes the pre-birth Saturn AD row (1962) — only the 1991 lived occurrence counts', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({}))
    const result = await computeKalaAhead(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    const ad = result.period_echo.find((e) => e.level_n === 2)
    expect(ad?.same_lord_past_occurrence_count).toBe(1)
    expect(ad?.candidates).toHaveLength(1)
    expect(ad?.candidates[0]?.start_date).toBe('1991-08-17')
    expect(ad?.candidates.some((c) => c.start_date === '1962-09-23')).toBe(false)
  })

  it('never cites the currently-running period as its own past occurrence', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({}))
    const result = await computeKalaAhead(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    const ad = result.period_echo.find((e) => e.level_n === 2)
    expect(ad?.candidates.some((c) => c.start_date === '2024-12-07')).toBe(false)
  })

  it('LEL-corroborates the 1991 occurrence from the real LEL event overlapping it', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({}))
    const result = await computeKalaAhead(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    const ad = result.period_echo.find((e) => e.level_n === 2)
    expect(ad?.lel_corroborated_occurrence_count).toBe(1)
    expect(ad?.candidates[0]?.lel_event_count).toBe(1)
    expect(ad?.candidates[0]?.lel_events_sample[0]?.event_id).toBe('lel-1')
  })

  it('Mahadasha (Mercury, no prior MD occurrence) honestly reports insufficient_data, hypothesis null', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({}))
    const result = await computeKalaAhead(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    const md = result.period_echo.find((e) => e.level_n === 1)
    expect(md?.status).toBe('insufficient_data')
    expect(md?.hypothesis).toBeNull()
    expect(md?.same_lord_past_occurrence_count).toBe(0)
    expect(md?.insufficient_data_reason).toMatch(/Vimśottarī|120-year/)
  })

  it('chart with NO LEL data at all (e.g. the second canonical chart) still serves the structural echo honestly', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ lelEvents: [] }))
    const result = await computeKalaAhead(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    const ad = result.period_echo.find((e) => e.level_n === 2)
    expect(ad?.status).toBe('hypothesis_served')
    expect(ad?.same_lord_past_occurrence_count).toBe(1)
    expect(ad?.lel_corroborated_occurrence_count).toBe(0)
    expect(ad?.candidates[0]?.lel_event_count).toBe(0)
    expect(ad?.hypothesis).toContain('no logged life events on file')
  })

  it('LEL fetch failure is disclosed, never silently treated as a confirmed zero', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ lelReachable: false }))
    const result = await computeKalaAhead(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    const ad = result.period_echo.find((e) => e.level_n === 2)
    expect(ad?.status).toBe('hypothesis_served')
    expect(ad?.confidence_basis).toMatch(/UNAVAILABLE, not a confirmed zero/)
  })

  it('birth-year floor unresolved (query_life_arc unreachable) withholds the hypothesis entirely, even though get_dashas returned rows', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ lifeArcReachable: false }))
    const result = await computeKalaAhead(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    const ad = result.period_echo.find((e) => e.level_n === 2)
    expect(ad?.status).toBe('insufficient_data')
    expect(ad?.hypothesis).toBeNull()
    expect(ad?.insufficient_data_reason).toMatch(/birth-year floor could not be resolved/)
  })

  it('get_dashas unreachable is an honest insufficient_data, not a thrown error', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ getDashasReachable: false }))
    const result = await computeKalaAhead(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    const ad = result.period_echo.find((e) => e.level_n === 2)
    expect(ad?.status).toBe('insufficient_data')
    expect(ad?.insufficient_data_reason).toMatch(/unreachable/)
  })

  it('coverage marks period_echo_mining computed when ≥1 level serves a hypothesis', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({}))
    const result = await computeKalaAhead(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    const byConcept = Object.fromEntries(result.coverage.map((c) => [c.concept, c]))
    expect(byConcept['period_echo_mining']?.state).toBe('computed')
    expect(result.provenance_envelope.period_echo_reachable).toBe(true)
  })

  it('coverage is honest_empty (never computed) when EVERY level reports insufficient_data', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ saturnAdRows: [SATURN_AD_ROWS[2]!] })) // only the currently-running row
    const result = await computeKalaAhead(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    const byConcept = Object.fromEntries(result.coverage.map((c) => [c.concept, c]))
    expect(byConcept['period_echo_mining']?.state).not.toBe('computed')
    expect(result.provenance_envelope.period_echo_reachable).toBe(false)
  })

  it('no kala_field / ka_kshetra dispatch is ever made — genuinely field-independent', async () => {
    const fetchMock = mockRegistryFetch({})
    vi.stubGlobal('fetch', fetchMock)
    await computeKalaAhead(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    const calledUris = fetchMock.mock.calls
      .map((call) => {
        try {
          return (JSON.parse(String((call[1] as RequestInit | undefined)?.body ?? '{}')) as { uri?: string }).uri
        } catch {
          return undefined
        }
      })
      .filter(Boolean)
    expect(calledUris.some((u) => /kala_field|ka_kshetra/i.test(String(u)))).toBe(false)
  })
})
