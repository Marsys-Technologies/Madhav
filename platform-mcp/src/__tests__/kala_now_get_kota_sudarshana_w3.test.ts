/**
 * kala_now_get_kota_sudarshana_w3.test.ts — ṢAḌ-DARŚANA W3 (SHAD_DARSHANA_BRIEF_v2_0.md §3
 * W3, Lane w3-kota-sudarshana), items 16 (Kota-Chakra) + 17 (Sudarśana-Chakra year-wheel).
 *
 * A separate file from kala_now_get.test.ts / kala_now_get_w1_joins.test.ts (not an edit to
 * either) — same low-merge-conflict-risk convention those files already established.
 *
 * Mirrors kala_now_get_w1_joins.test.ts's mock-fetch pattern: the double-wrapped
 * `{ ok, content: { content, is_error } }` contract dispatched by URI.
 *
 * Contract gates:
 *   ✓ §N.5: this facade only READS rows already computed by ka_kota_chakra/
 *     ka_sudarshana_varsha — these tests assert the served fields trace verbatim to the
 *     mocked capability rows, never re-derived here.
 *   ✓ B.10 honest-empty: unreachable capability / no current row -> coverage honest_empty,
 *     never a fabricated value.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { Principal } from '../types.js'
import { computeKalaNow } from '../tools/kala_views/now.js'

const TEST_CHART_ID = '00000000-0000-0000-0000-000000000001'
const TEST_PRINCIPAL: Principal = { user_uid: 'test-uid', key_id: 'test-key', role: 'guest' }

const KOTA_CHAKRA_ROWS = [
  {
    graha: 'Saturn', nakshatra_name: 'PurvaBhadrapada', count_from_janma: 1, kota_ring: 'bahya',
    is_natural_malefic: true, posture: 'attacking', severity: 'watch',
    window_start: '2026-07-20', window_end: '2026-08-15', start_truncated: true, end_truncated: false,
    ring_table_citation: 'tier-(iii) secondary-source transcription', uncited_extension: true,
    is_current: true,
  },
  {
    graha: 'Jupiter', nakshatra_name: 'Chitra', count_from_janma: 14, kota_ring: 'durgantara',
    is_natural_malefic: false, posture: 'settled_in_the_middle_ward', severity: 'supportive',
    window_start: '2026-01-01', window_end: '2026-02-01', start_truncated: true, end_truncated: true,
    ring_table_citation: 'tier-(iii) secondary-source transcription', uncited_extension: true,
    is_current: false, // NOT the current window — must be filtered out of kala_now_get
  },
]

const SUDARSHANA_ROWS = [
  {
    varsha_year: 42, window_start: '2025-02-05', window_end: '2026-02-05',
    jl_active_sign_name: 'Aquarius', cl_active_sign_name: 'Sagittarius', sl_active_sign_name: 'Libra',
    tri_lagna_convergence: false, is_current: true,
  },
  {
    varsha_year: 43, window_start: '2026-02-05', window_end: '2027-02-05',
    jl_active_sign_name: 'Pisces', cl_active_sign_name: 'Capricorn', sl_active_sign_name: 'Scorpio',
    tri_lagna_convergence: false, is_current: false,
  },
]

function mockRegistryFetch(opts: {
  reachable?: boolean
  kotaReachable?: boolean
  sudarshanaReachable?: boolean
  kotaRows?: typeof KOTA_CHAKRA_ROWS
  sudarshanaRows?: typeof SUDARSHANA_ROWS
}) {
  const reachable = opts.reachable ?? true
  return vi.fn(async (_url: string, init?: RequestInit) => {
    if (!reachable) throw new Error('registry unreachable in test')
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
    } else if (body.uri === 'marsys://tool/L1/get_dignity') {
      inner = { rows: [] }
    } else if (body.uri === 'marsys://tool/L3/query_kota_chakra') {
      if (opts.kotaReachable === false) throw new Error('query_kota_chakra unreachable in test')
      inner = { rows: opts.kotaRows ?? KOTA_CHAKRA_ROWS }
    } else if (body.uri === 'marsys://tool/L3/query_sudarshana_varsha') {
      if (opts.sudarshanaReachable === false) throw new Error('query_sudarshana_varsha unreachable in test')
      inner = { rows: opts.sudarshanaRows ?? SUDARSHANA_ROWS }
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

describe('kala_now_get item 16 — kota_chakra', () => {
  it('serves only the current ring-run per graha, verbatim from the writer row', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({}))
    const result = await computeKalaNow(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    expect(result.kota_chakra).toHaveLength(1)
    expect(result.kota_chakra[0]).toMatchObject({
      graha: 'Saturn',
      kota_ring: 'bahya',
      is_natural_malefic: true,
      posture: 'attacking',
      severity: 'watch',
      window_start: '2026-07-20',
      window_end: '2026-08-15',
      start_truncated: true,
      end_truncated: false,
    })
    const cov = result.coverage.find((c) => c.concept === 'kota_chakra')
    expect(cov?.state).toBe('computed')
  })

  it('is honest-empty (not fabricated) when the capability is unreachable', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ kotaReachable: false }))
    const result = await computeKalaNow(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    expect(result.kota_chakra).toEqual([])
    const cov = result.coverage.find((c) => c.concept === 'kota_chakra')
    expect(cov?.state).toBe('honest_empty')
    expect(result.provenance_envelope.kota_chakra_reachable).toBe(false)
  })

  it('is honest-empty when the writer has no row containing as_of (no current run)', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ kotaRows: [] }))
    const result = await computeKalaNow(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    expect(result.kota_chakra).toEqual([])
    const cov = result.coverage.find((c) => c.concept === 'kota_chakra')
    expect(cov?.state).toBe('honest_empty')
    expect(result.provenance_envelope.kota_chakra_reachable).toBe(true) // reached, genuinely empty
  })
})

describe('kala_now_get item 17 — sudarshana_varsha', () => {
  it('serves only the current varsha year, verbatim from the writer row', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({}))
    const result = await computeKalaNow(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    expect(result.sudarshana_varsha).toMatchObject({
      varsha_year: 42,
      jl_active_sign_name: 'Aquarius',
      cl_active_sign_name: 'Sagittarius',
      sl_active_sign_name: 'Libra',
      tri_lagna_convergence: false,
    })
    const cov = result.coverage.find((c) => c.concept === 'sudarshana_varsha')
    expect(cov?.state).toBe('computed')
  })

  it('is honest-empty when the capability is unreachable', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ sudarshanaReachable: false }))
    const result = await computeKalaNow(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    expect(result.sudarshana_varsha).toBeNull()
    const cov = result.coverage.find((c) => c.concept === 'sudarshana_varsha')
    expect(cov?.state).toBe('honest_empty')
    expect(result.provenance_envelope.sudarshana_varsha_reachable).toBe(false)
  })

  it('flags tri_lagna_convergence honestly when true', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({
      sudarshanaRows: [{ ...SUDARSHANA_ROWS[0]!, tri_lagna_convergence: true, jl_active_sign_name: 'Aries', cl_active_sign_name: 'Aries', sl_active_sign_name: 'Aries' }],
    }))
    const result = await computeKalaNow(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    expect(result.sudarshana_varsha?.tri_lagna_convergence).toBe(true)
  })
})
