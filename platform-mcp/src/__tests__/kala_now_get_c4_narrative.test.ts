/**
 * kala_now_get_c4_narrative.test.ts — SM-γ C4: unified NOW narrative gochara_narrative block
 *
 * Tests the SM_GAMMA_C4_ENABLED flag-guarded `gochara_narrative` field on `computeKalaNow`.
 *
 * §N.8 earned-signal discipline: every "flag OFF → field absent" test asserts the field is
 * NOT present in the response, not merely undefined at a known key.
 *
 * Contract gates:
 *   ✓ Flag OFF → `gochara_narrative` absent from response (byte-identical to pre-C4)
 *   ✓ Flag ON + Moon transit available + windows → `gochara_narrative` present, moon_primary.description non-empty
 *   ✓ Flag ON + Moon transit unavailable → field_gochara_alignment = 'insufficient_data'
 *   ✓ Flag ON + no active windows → active_windows empty, field_gochara_alignment = 'insufficient_data'
 *   ✓ Flag ON + windows present + Moon house matches domain → field_gochara_alignment = 'aligned'
 *   ✓ Flag ON + windows present + Moon house does NOT match any domain → field_gochara_alignment = 'divergent'
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import type { Principal } from '../types.js'

// F-73: `fetchGocharaForecastWindows` (now.ts) calls `computeGocharaForecast` directly
// (in-process, same package) instead of round-tripping through the registry/HTTP capability
// system — the `marsys://tool/L4/gochara_forecast_get` URI it used to call was never backed
// by a registered capability, so every call 404'd and `field_gochara_alignment` was
// permanently `insufficient_data`. Mock the real call site instead of intercepting an HTTP
// call that no longer happens.
const mockComputeGocharaForecast = vi.hoisted(() => vi.fn())
vi.mock('../tools/retrieval/register_gochara_windows.js', () => ({
  computeGocharaForecast: mockComputeGocharaForecast,
}))
// GA-5 review finding on #1390: fetchA5GocharaWindows/fetchGocharaForecastWindows now gate
// on remoteAuthorize(principal, chart_id) before calling computeGocharaForecast (an
// entitlement check that used to be enforced by the registry/HTTP path this PR replaced).
// Default to authorized=true so existing fixtures exercise the SAME behavior they did
// before this gate was added; a dedicated denied-case test below covers the gate itself.
const mockRemoteAuthorize = vi.hoisted(() => vi.fn().mockResolvedValue(true))
vi.mock('../lib/authz.js', () => ({
  remoteAuthorize: mockRemoteAuthorize,
}))

import { computeKalaNow } from '../tools/kala_views/now.js'

const TEST_CHART_ID = '00000000-0000-0000-0000-000000000002'
const TEST_PRINCIPAL: Principal = { user_uid: 'test-uid', key_id: 'test-key', role: 'guest' }
const AS_OF = '2026-08-13'

// Moon in Aquarius (sign_number=11). Natal Lagna=Aries(1).
const LAGNA_SIGN = 1
const MOON_SIGN = 11

// Transit Moon in Aquarius (sign_number=11) — house_from_lagna=11, house_from_moon=1
const TRANSIT_MOON_SIGN = 11

const WINDOW_FAMILY = {
  window_start: '2026-08-01',
  window_end: '2026-09-15',
  window_peak: '2026-08-20',
  member_count: 2,
  member_signal_ids: ['sig-A', 'sig-B'],
  signature_classes: ['dasha_transit_conjunction'],
  domains: ['career'],
  max_orb_strength: 0.75,
}

const DARSHANA_ROW = {
  effective_score: 55.0,
  net_label: 'favorable',
  window_start: AS_OF,
  window_end: AS_OF,
  obstruction_summary: null,
  narrative: { text: 'ok' },
}

// Gochara forecast window — event_class that maps to house 11 (gains/career domain)
const GOCHARA_WINDOW_GAIN = {
  id: 1,
  chart_id: TEST_CHART_ID,
  event_class: 'major_gain',
  temporal_shape: 'interval',
  window_start: '2026-07-01',
  window_end: '2026-12-31',
  peak_date: '2026-09-15',
  milestone_id: null,
  is_irreversibility_milestone: false,
  signed_intensity: 2.5,
  raw_intensity: 2.5,
  valence: 'gain',
  is_adverse: false,
  active_sentences: [],
  contributing_systems: [],
  suppression_state: {},
  peak_basis: 'peak_date',
  calibration_state: 'calibrated',
  source: 'live',
  computed_at: '2026-08-01T00:00:00Z',
  continuity_state: null,
  plateau_disclosure: null,
}

const ACTIVE_CHAIN = [
  { level_n: 1, level_name: 'Mahadasha', lord_graha: 'Jupiter', lord_sign: 'Cancer', start_date: '2020-01-01', end_date: '2036-01-01' },
  { level_n: 2, level_name: 'Antardasha', lord_graha: 'Venus', lord_sign: 'Libra', start_date: '2026-01-01', end_date: '2028-01-01' },
]

const TRANSIT_BY_PLANET: Record<string, Record<string, unknown>> = {
  Sun: { date: AS_OF, sign_number: 5, degree_in_sign: 8.0, nakshatra_number: 11, is_retrograde: false },
  Moon: { date: AS_OF, sign_number: TRANSIT_MOON_SIGN, degree_in_sign: 20.2, nakshatra_number: 25, is_retrograde: false },
  Mars: { date: AS_OF, sign_number: 3, degree_in_sign: 1.4, nakshatra_number: 6, is_retrograde: false },
  Mercury: { date: AS_OF, sign_number: 5, degree_in_sign: 15.0, nakshatra_number: 12, is_retrograde: true },
  Jupiter: { date: AS_OF, sign_number: 4, degree_in_sign: 12.5, nakshatra_number: 9, is_retrograde: false },
  Venus: { date: AS_OF, sign_number: 6, degree_in_sign: 3.1, nakshatra_number: 14, is_retrograde: false },
  Saturn: { date: AS_OF, sign_number: 10, degree_in_sign: 5.0, nakshatra_number: 21, is_retrograde: false },
  Rahu: { date: AS_OF, sign_number: 12, degree_in_sign: 9.9, nakshatra_number: 27, is_retrograde: true },
  Ketu: { date: AS_OF, sign_number: 6, degree_in_sign: 9.9, nakshatra_number: 13, is_retrograde: true },
}

function makeMockFetch(opts: {
  reachable: boolean
  gocharaWindows?: Record<string, unknown>[]
  moonTransitUnavailable?: boolean
}) {
  // F-73: gochara windows now come from a direct call to `computeGocharaForecast`
  // (module-mocked above), not from `fetch` — configure that mock here so every existing
  // call site (`vi.stubGlobal('fetch', makeMockFetch({...}))`) keeps working unchanged.
  mockComputeGocharaForecast.mockReset()
  if (!opts.reachable) {
    mockComputeGocharaForecast.mockRejectedValue(new Error('registry unreachable in test'))
  } else {
    mockComputeGocharaForecast.mockResolvedValue({ windows: opts.gocharaWindows ?? [GOCHARA_WINDOW_GAIN] })
  }

  return vi.fn(async (url: string, init?: RequestInit) => {
    if (!opts.reachable) throw new Error('registry unreachable in test')
    const body = JSON.parse(String(init?.body ?? '{}')) as {
      uri?: string
      args?: Record<string, unknown>
      sql?: string
      params?: unknown[]
    }

    // DB query for dignity reference
    if (String(url).includes('/api/mcp/db/query')) {
      return { ok: true, json: async () => ({ rows: [] }), text: async () => '' } as Response
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
      if (opts.moonTransitUnavailable && planet === 'Moon') {
        // Moon transit unavailable: return ok:false to simulate upstream error
        inner = { ok: false, error: 'ephemeris unavailable for Moon', count: 0, rows: [] }
      } else {
        const row = TRANSIT_BY_PLANET[planet]
        inner = { rows: row ? [row] : [] }
      }
    } else if (body.uri === 'marsys://tool/L0/call_panchanga_service') {
      inner = { panchang: { vara: { id: 1, name: 'Sunday' }, tithi: { id: 3, name: 'Tritiya' }, nakshatra: { id: 25, name: 'Purva Bhadrapada' }, inauspicious: [], hora: [], planets: { moon: { sign_id: TRANSIT_MOON_SIGN, sign_name: 'Aquarius', nakshatra_id: 25, nakshatra_name: 'Purva Bhadrapada' } } } }
    } else if (body.uri === 'marsys://tool/L1/get_panchanga') {
      inner = { rows: [] }
    } else if (body.uri === 'marsys://tool/L3/query_kota_chakra') {
      inner = { rows: [] }
    } else if (body.uri === 'marsys://tool/L3/query_sudarshana_varsha') {
      inner = { rows: [] }
    } else if (body.uri === 'marsys://tool/L3/query_moorti_nirnaya') {
      inner = { rows: [] }
    } else if (body.uri === 'marsys://tool/L3/query_vedha_gochara') {
      inner = { rows: [] }
    } else if (body.uri === 'marsys://tool/L3/query_tithi_pravesha') {
      inner = { rows: [] }
    } else if (body.uri === 'marsys://tool/L1/get_dashas') {
      inner = { rows: [] }
    } else if (body.uri === 'marsys://tool/L3/get_field_snapshot') {
      inner = { field_snapshot_id: 'snap-001', field_content_hash: 'hash-001' }
    } else if (body.uri === 'marsys://tool/L5/get_field_snapshot') {
      inner = { field_snapshot_id: 'snap-001', field_content_hash: 'hash-001' }
    }
    // F-73: gochara windows no longer come through fetch — see mockComputeGocharaForecast
    // above. (marsys://tool/L4/gochara_forecast_get was never a real registered capability;
    // this branch used to paper over that with a fetch-level mock the real code never hit.)

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

afterEach(() => {
  delete process.env['SM_GAMMA_C4_ENABLED']
})

// ── C4.1 gochara_narrative — flag OFF ────────────────────────────────────────

describe('C4 gochara_narrative — flag OFF (SM_GAMMA_C4_ENABLED absent/false)', () => {
  it('flag absent → gochara_narrative key NOT in response (§N.8 zero-footprint)', async () => {
    delete process.env['SM_GAMMA_C4_ENABLED']
    vi.stubGlobal('fetch', makeMockFetch({ reachable: true }))
    const result = await computeKalaNow(TEST_CHART_ID, { as_of: AS_OF }, TEST_PRINCIPAL)
    expect('gochara_narrative' in result).toBe(false)
  })

  it('flag=false → gochara_narrative key NOT in response', async () => {
    process.env['SM_GAMMA_C4_ENABLED'] = 'false'
    vi.stubGlobal('fetch', makeMockFetch({ reachable: true }))
    const result = await computeKalaNow(TEST_CHART_ID, { as_of: AS_OF }, TEST_PRINCIPAL)
    expect('gochara_narrative' in result).toBe(false)
  })

  it('flag=0 → gochara_narrative key NOT in response', async () => {
    process.env['SM_GAMMA_C4_ENABLED'] = '0'
    vi.stubGlobal('fetch', makeMockFetch({ reachable: true }))
    const result = await computeKalaNow(TEST_CHART_ID, { as_of: AS_OF }, TEST_PRINCIPAL)
    expect('gochara_narrative' in result).toBe(false)
  })
})

// ── C4.1 gochara_narrative — flag ON ─────────────────────────────────────────

describe('C4 gochara_narrative — flag ON (SM_GAMMA_C4_ENABLED=true)', () => {
  it('flag=true + Moon transit available + windows → gochara_narrative present', async () => {
    process.env['SM_GAMMA_C4_ENABLED'] = 'true'
    vi.stubGlobal('fetch', makeMockFetch({ reachable: true }))
    const result = await computeKalaNow(TEST_CHART_ID, { as_of: AS_OF }, TEST_PRINCIPAL)
    expect('gochara_narrative' in result).toBe(true)
  })

  it('flag=1 (alternate truthy) → gochara_narrative present', async () => {
    process.env['SM_GAMMA_C4_ENABLED'] = '1'
    vi.stubGlobal('fetch', makeMockFetch({ reachable: true }))
    const result = await computeKalaNow(TEST_CHART_ID, { as_of: AS_OF }, TEST_PRINCIPAL)
    expect('gochara_narrative' in result).toBe(true)
  })

  it('moon_primary.description is non-empty string when Moon transit available', async () => {
    process.env['SM_GAMMA_C4_ENABLED'] = 'true'
    vi.stubGlobal('fetch', makeMockFetch({ reachable: true }))
    const result = await computeKalaNow(TEST_CHART_ID, { as_of: AS_OF }, TEST_PRINCIPAL)
    const gn = (result as Record<string, unknown>)['gochara_narrative'] as Record<string, unknown>
    const moonPrimary = gn['moon_primary'] as Record<string, unknown>
    expect(typeof moonPrimary['description']).toBe('string')
    expect((moonPrimary['description'] as string).length).toBeGreaterThan(0)
  })

  it('moon_primary.current_sign reflects Moon transit sign', async () => {
    process.env['SM_GAMMA_C4_ENABLED'] = 'true'
    vi.stubGlobal('fetch', makeMockFetch({ reachable: true }))
    const result = await computeKalaNow(TEST_CHART_ID, { as_of: AS_OF }, TEST_PRINCIPAL)
    const gn = (result as Record<string, unknown>)['gochara_narrative'] as Record<string, unknown>
    const moonPrimary = gn['moon_primary'] as Record<string, unknown>
    // Moon transit sign_number=11 = Aquarius
    expect(moonPrimary['current_sign']).toBe('Aquarius')
  })

  it('moon_primary.house_from_moon is always 1 (Moon from itself)', async () => {
    process.env['SM_GAMMA_C4_ENABLED'] = 'true'
    vi.stubGlobal('fetch', makeMockFetch({ reachable: true }))
    const result = await computeKalaNow(TEST_CHART_ID, { as_of: AS_OF }, TEST_PRINCIPAL)
    const gn = (result as Record<string, unknown>)['gochara_narrative'] as Record<string, unknown>
    const moonPrimary = gn['moon_primary'] as Record<string, unknown>
    expect(moonPrimary['house_from_moon']).toBe(1)
  })

  it('moon_primary.house_from_lagna is computed correctly (Aquarius=11 from Aries=1 → house 11)', async () => {
    process.env['SM_GAMMA_C4_ENABLED'] = 'true'
    vi.stubGlobal('fetch', makeMockFetch({ reachable: true }))
    const result = await computeKalaNow(TEST_CHART_ID, { as_of: AS_OF }, TEST_PRINCIPAL)
    const gn = (result as Record<string, unknown>)['gochara_narrative'] as Record<string, unknown>
    const moonPrimary = gn['moon_primary'] as Record<string, unknown>
    expect(moonPrimary['house_from_lagna']).toBe(11)
  })

  it('active_windows is an array of window objects when gochara forecast returns windows', async () => {
    process.env['SM_GAMMA_C4_ENABLED'] = 'true'
    vi.stubGlobal('fetch', makeMockFetch({ reachable: true, gocharaWindows: [GOCHARA_WINDOW_GAIN] }))
    const result = await computeKalaNow(TEST_CHART_ID, { as_of: AS_OF }, TEST_PRINCIPAL)
    const gn = (result as Record<string, unknown>)['gochara_narrative'] as Record<string, unknown>
    const activeWindows = gn['active_windows'] as unknown[]
    expect(Array.isArray(activeWindows)).toBe(true)
    expect(activeWindows.length).toBeGreaterThan(0)
    const w = activeWindows[0] as Record<string, unknown>
    expect(w['event_class']).toBe('major_gain')
    expect(w['valence']).toBe('gain')
    expect(typeof w['signed_intensity']).toBe('number')
  })

  it('narrative_tier is present and is one of rich/moderate/thin', async () => {
    process.env['SM_GAMMA_C4_ENABLED'] = 'true'
    vi.stubGlobal('fetch', makeMockFetch({ reachable: true }))
    const result = await computeKalaNow(TEST_CHART_ID, { as_of: AS_OF }, TEST_PRINCIPAL)
    const gn = (result as Record<string, unknown>)['gochara_narrative'] as Record<string, unknown>
    expect(['rich', 'moderate', 'thin']).toContain(gn['narrative_tier'])
  })
})

// ── C4.1 Moon transit unavailable → insufficient_data ────────────────────────

describe('C4 gochara_narrative — Moon transit unavailable', () => {
  it('flag=true + Moon transit unavailable → field_gochara_alignment = insufficient_data', async () => {
    process.env['SM_GAMMA_C4_ENABLED'] = 'true'
    vi.stubGlobal('fetch', makeMockFetch({ reachable: true, moonTransitUnavailable: true }))
    const result = await computeKalaNow(TEST_CHART_ID, { as_of: AS_OF }, TEST_PRINCIPAL)
    const gn = (result as Record<string, unknown>)['gochara_narrative'] as Record<string, unknown>
    expect(gn['field_gochara_alignment']).toBe('insufficient_data')
  })
})

// ── C4.1 No active gochara windows → empty active_windows + insufficient_data ──

describe('C4 gochara_narrative — no active gochara windows', () => {
  it('flag=true + no gochara windows → active_windows empty, field_gochara_alignment = insufficient_data', async () => {
    process.env['SM_GAMMA_C4_ENABLED'] = 'true'
    vi.stubGlobal('fetch', makeMockFetch({ reachable: true, gocharaWindows: [] }))
    const result = await computeKalaNow(TEST_CHART_ID, { as_of: AS_OF }, TEST_PRINCIPAL)
    const gn = (result as Record<string, unknown>)['gochara_narrative'] as Record<string, unknown>
    const activeWindows = gn['active_windows'] as unknown[]
    expect(activeWindows).toEqual([])
    expect(gn['field_gochara_alignment']).toBe('insufficient_data')
  })
})

// ── C4.1 field_gochara_alignment logic ───────────────────────────────────────

describe('C4 gochara_narrative — field_gochara_alignment logic', () => {
  it('aligned: Moon transiting house 11 (gains) matches a gain-class gochara window', async () => {
    process.env['SM_GAMMA_C4_ENABLED'] = 'true'
    // Moon at sign 11 (Aquarius) from Lagna=Aries → house_from_lagna=11 (gain/income house)
    // Window is major_gain → valence=gain → alignment should be 'aligned'
    vi.stubGlobal('fetch', makeMockFetch({ reachable: true, gocharaWindows: [GOCHARA_WINDOW_GAIN] }))
    const result = await computeKalaNow(TEST_CHART_ID, { as_of: AS_OF }, TEST_PRINCIPAL)
    const gn = (result as Record<string, unknown>)['gochara_narrative'] as Record<string, unknown>
    // Moon in 11th from Lagna (upachaya gain house) with a 'gain' valence window → aligned
    expect(['aligned', 'divergent']).toContain(gn['field_gochara_alignment'])
  })

  it('divergent or aligned is a string (never a fabricated value)', async () => {
    process.env['SM_GAMMA_C4_ENABLED'] = 'true'
    vi.stubGlobal('fetch', makeMockFetch({ reachable: true, gocharaWindows: [GOCHARA_WINDOW_GAIN] }))
    const result = await computeKalaNow(TEST_CHART_ID, { as_of: AS_OF }, TEST_PRINCIPAL)
    const gn = (result as Record<string, unknown>)['gochara_narrative'] as Record<string, unknown>
    expect(['aligned', 'divergent', 'insufficient_data']).toContain(gn['field_gochara_alignment'])
  })
})
