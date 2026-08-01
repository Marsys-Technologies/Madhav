/**
 * kala_now_get_moorti_vedha_w3.test.ts — ṢAḌ-DARŚANA W3 (SHAD_DARSHANA_BRIEF_v2_0.md §3
 * W3, Lane w3-moorti-vedha), items 4 (Moorti-nirṇaya) + 5 (Vedha application +
 * Sarvatobhadra chakra grid — closes defect R-19).
 *
 * A separate file from kala_now_get.test.ts / kala_now_get_kota_sudarshana_w3.test.ts (not
 * an edit to either) — same low-merge-conflict-risk convention those files already
 * established.
 *
 * Mirrors kala_now_get_kota_sudarshana_w3.test.ts's mock-fetch pattern: the
 * double-wrapped `{ ok, content: { content, is_error } }` contract dispatched by URI.
 *
 * Contract gates:
 *   ✓ §N.5: this facade only READS rows already computed by ka_moorti_nirnaya/
 *     ka_vedha_gochara — these tests assert the served fields trace verbatim to the
 *     mocked capability rows, never re-derived here.
 *   ✓ B.10 honest-empty: unreachable capability / no current row -> coverage honest_empty,
 *     never a fabricated value.
 *   ✓ §N.6: house_vedha and sarvatobhadra rows are never conflated — vedha_kind and
 *     uncited_extension are asserted to round-trip verbatim, distinguishing the REAL cited
 *     mechanism from the disclosed R-19 approximation.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { Principal } from '../types.js'
import { computeKalaNow } from '../tools/kala_views/now.js'

const TEST_CHART_ID = '00000000-0000-0000-0000-000000000001'
const TEST_PRINCIPAL: Principal = { user_uid: 'test-uid', key_id: 'test-key', role: 'guest' }

const MOORTI_ROWS = [
  {
    graha: 'Jupiter', target_sign_idx: 4, target_sign_name: 'Leo',
    window_start: '2026-05-01', window_end: '2027-05-15',
    start_truncated: true, end_truncated: false, moorti_computed: false,
    moon_nakshatra_idx_at_ingress: null, moon_nakshatra_name_at_ingress: null,
    janma_nakshatra_idx: 24, janma_nakshatra_fact_id: 'fact-moon-1', nakshatra_offset: null,
    moorti_name: null, quality_tier: null, phala_brief: null, moorti_classical_citation: null,
    is_current: true,
  },
  {
    graha: 'Saturn', target_sign_idx: 10, target_sign_name: 'Aquarius',
    window_start: '2023-01-17', window_end: '2025-03-29',
    start_truncated: false, end_truncated: false, moorti_computed: true,
    moon_nakshatra_idx_at_ingress: 5, moon_nakshatra_name_at_ingress: 'Ardra',
    janma_nakshatra_idx: 24, janma_nakshatra_fact_id: 'fact-moon-1', nakshatra_offset: 8,
    moorti_name: 'tamra', quality_tier: 3, phala_brief: 'Mixed results; caution advised.',
    moorti_classical_citation: 'Phaladeepika Ch.26 §moorti-nirnaya; BPHS Ch.28',
    is_current: false, // NOT current — must be filtered out
  },
]

const VEDHA_ROWS = [
  {
    vedha_kind: 'house_vedha', graha: 'Sun',
    window_start: '2026-07-15', window_end: '2026-08-14',
    start_truncated: false, end_truncated: false,
    janma_reference_fact_id: 'fact-moon-1',
    classical_citation: 'BPHS Ch.29', uncited_extension: false,
    grid_basis: null, grid_school_tag: null,
    detail: {
      primary_house: 3, primary_sign_idx: 2, primary_sign_name: 'Gemini',
      vedha_house: 9, vedha_sign_idx: 8, vedha_sign_name: 'Sagittarius',
      phala: 'Courage, travel, gain from siblings',
      obstruction_active: true, obstructing_graha: 'Mars',
      obstruction_window_start: '2026-07-20', obstruction_window_end: '2026-07-25',
      malefic_obstructing_grahas: ['Mars'], malefic_count: 1,
      malefic_effect_grade: 'fear', malefic_effect_description: 'Vedha caused by one malefic: fear.',
      malefic_scale_citation: '[HIGH] Phaladeepika — Trans. V. Subrahmanya Sastri, 2nd Ed. 1950 | PG353',
      malefic_grade_uncited_extension: true,
    },
    is_current: true,
  },
  {
    vedha_kind: 'sarvatobhadra', graha: 'Mars',
    window_start: '2026-06-01', window_end: '2026-06-20',
    start_truncated: false, end_truncated: false,
    janma_reference_fact_id: 'fact-moon-1',
    classical_citation: 'Prasna Marga (Sarvatobhadra Chakra vedha geometry: rekha/kona/vithi vedha); cf. ga_sensitive_degree_writer.py sarvatobhadra_vedha evidence row',
    uncited_extension: true,
    grid_basis: 'algorithmic_approximation', grid_school_tag: null,
    detail: {
      target_nakshatra_idx: 24, target_nakshatra_name: 'Purva Bhadrapada',
      vedha_nakshatra_idx: 11, vedha_nakshatra_name: 'Uttara Phalguni',
      cancellation_effect: 'While Mars dwells in Uttara Phalguni ...',
      r19_disclosure: 'no SBC grid in the ingested corpus (8 term hits, all index/OCR/passing-mention); grid geometry varies by tradition; served value is an algorithmic approximation, not a transcribed grid.',
    },
    is_current: false, // NOT current — must be filtered out
  },
  {
    vedha_kind: 'latta', graha: 'Moon',
    window_start: '2026-04-01', window_end: '2026-04-10',
    start_truncated: false, end_truncated: false,
    janma_reference_fact_id: 'fact-moon-1',
    classical_citation: '[HIGH] Phaladeepika — Trans. V. Subrahmanya Sastri, 2nd Ed. 1950 | PG339',
    uncited_extension: false,
    grid_basis: null, grid_school_tag: null,
    detail: {
      count_from_graha: 22, direction: 'backward',
      latta_nakshatra_idx: 24, latta_nakshatra_name: 'Purva Bhadrapada',
      janma_nakshatra_idx: 24, janma_nakshatra_name: 'Purva Bhadrapada',
      effect_description: 'A great loss.',
      affliction_condition: 'If, when thus counting, the Janma-nakshatra (natal star) happens to come as the Latta star, there will be sickness and anguish.',
    },
    is_current: false, // NOT current — must be filtered out
  },
]

function mockRegistryFetch(opts: {
  moortiReachable?: boolean
  vedhaReachable?: boolean
  moortiRows?: typeof MOORTI_ROWS
  vedhaRows?: typeof VEDHA_ROWS
}) {
  return vi.fn(async (_url: string, init?: RequestInit) => {
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
      inner = { rows: [] }
    } else if (body.uri === 'marsys://tool/L3/query_sudarshana_varsha') {
      inner = { rows: [] }
    } else if (body.uri === 'marsys://tool/L3/query_moorti_nirnaya') {
      if (opts.moortiReachable === false) throw new Error('query_moorti_nirnaya unreachable in test')
      inner = { rows: opts.moortiRows ?? MOORTI_ROWS }
    } else if (body.uri === 'marsys://tool/L3/query_vedha_gochara') {
      if (opts.vedhaReachable === false) throw new Error('query_vedha_gochara unreachable in test')
      inner = { rows: opts.vedhaRows ?? VEDHA_ROWS }
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

describe('kala_now_get item 4 — moorti_nirnaya', () => {
  it('serves only the current sign-run per graha, verbatim from the writer row', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({}))
    const result = await computeKalaNow(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    expect(result.moorti_nirnaya).toHaveLength(1)
    expect(result.moorti_nirnaya[0]).toMatchObject({
      graha: 'Jupiter',
      target_sign_name: 'Leo',
      window_start: '2026-05-01',
      window_end: '2027-05-15',
      moorti_computed: false,
      moorti_name: null,
    })
    const cov = result.coverage.find((c) => c.concept === 'moorti_nirnaya')
    expect(cov?.state).toBe('computed')
  })

  it('honestly serves null moorti fields when moorti_computed is false (truncated ingress)', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({}))
    const result = await computeKalaNow(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    const row = result.moorti_nirnaya[0]
    expect(row?.moorti_computed).toBe(false)
    expect(row?.moorti_name).toBeNull()
    expect(row?.quality_tier).toBeNull()
    expect(row?.moorti_classical_citation).toBeNull()
  })

  it('serves a real cited moorti classification when moorti_computed is true', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({
      moortiRows: [{ ...MOORTI_ROWS[1]!, is_current: true }],
    }))
    const result = await computeKalaNow(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    expect(result.moorti_nirnaya[0]).toMatchObject({
      graha: 'Saturn',
      moorti_computed: true,
      moorti_name: 'tamra',
      quality_tier: 3,
      moorti_classical_citation: 'Phaladeepika Ch.26 §moorti-nirnaya; BPHS Ch.28',
    })
  })

  it('is honest-empty (not fabricated) when the capability is unreachable', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ moortiReachable: false }))
    const result = await computeKalaNow(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    expect(result.moorti_nirnaya).toEqual([])
    const cov = result.coverage.find((c) => c.concept === 'moorti_nirnaya')
    expect(cov?.state).toBe('honest_empty')
    expect(result.provenance_envelope.moorti_nirnaya_reachable).toBe(false)
  })

  it('is honest-empty when the writer has no row containing as_of (no current run)', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ moortiRows: [] }))
    const result = await computeKalaNow(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    expect(result.moorti_nirnaya).toEqual([])
    const cov = result.coverage.find((c) => c.concept === 'moorti_nirnaya')
    expect(cov?.state).toBe('honest_empty')
    expect(result.provenance_envelope.moorti_nirnaya_reachable).toBe(true) // reached, genuinely empty
  })
})

describe('kala_now_get item 5 — vedha_gochara (closes R-19)', () => {
  it('serves only the current vedha row(s), verbatim from the writer row', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({}))
    const result = await computeKalaNow(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    expect(result.vedha_gochara).toHaveLength(1)
    expect(result.vedha_gochara[0]).toMatchObject({
      vedha_kind: 'house_vedha',
      graha: 'Sun',
      classical_citation: 'BPHS Ch.29',
      uncited_extension: false,
    })
    const cov = result.coverage.find((c) => c.concept === 'vedha_gochara')
    expect(cov?.state).toBe('computed')
  })

  it('never conflates house_vedha (REAL cited) with sarvatobhadra (R-19, disclosed approximation)', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({
      vedhaRows: [
        { ...VEDHA_ROWS[0]!, is_current: true },
        { ...VEDHA_ROWS[1]!, is_current: true },
      ],
    }))
    const result = await computeKalaNow(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    expect(result.vedha_gochara).toHaveLength(2)
    const houseRow = result.vedha_gochara.find((r) => r.vedha_kind === 'house_vedha')
    const sbcRow = result.vedha_gochara.find((r) => r.vedha_kind === 'sarvatobhadra')
    expect(houseRow?.uncited_extension).toBe(false)
    expect(sbcRow?.uncited_extension).toBe(true)
    expect(sbcRow?.detail['r19_disclosure']).toBeDefined()
  })

  it('serves the obstruction detail verbatim for house_vedha rows', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({}))
    const result = await computeKalaNow(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    expect(result.vedha_gochara[0]?.detail).toMatchObject({
      primary_house: 3,
      vedha_house: 9,
      obstruction_active: true,
      obstructing_graha: 'Mars',
    })
  })

  it('is honest-empty (not fabricated) when the capability is unreachable', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ vedhaReachable: false }))
    const result = await computeKalaNow(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    expect(result.vedha_gochara).toEqual([])
    const cov = result.coverage.find((c) => c.concept === 'vedha_gochara')
    expect(cov?.state).toBe('honest_empty')
    expect(result.provenance_envelope.vedha_gochara_reachable).toBe(false)
  })

  it('is honest-empty (the classically normal state) when no vedha is currently active', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ vedhaRows: [] }))
    const result = await computeKalaNow(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    expect(result.vedha_gochara).toEqual([])
    const cov = result.coverage.find((c) => c.concept === 'vedha_gochara')
    expect(cov?.state).toBe('honest_empty')
    expect(result.provenance_envelope.vedha_gochara_reachable).toBe(true) // reached, genuinely empty
  })

  // ── ADJUDICATION-11 additions ──────────────────────────────────────────────
  it('serves grid_basis/grid_school_tag verbatim (machine-readable, not prose-only) on sarvatobhadra rows', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({
      vedhaRows: [{ ...VEDHA_ROWS[1]!, is_current: true }],
    }))
    const result = await computeKalaNow(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    const sbcRow = result.vedha_gochara.find((r) => r.vedha_kind === 'sarvatobhadra')
    expect(sbcRow?.grid_basis).toBe('algorithmic_approximation')
    expect(sbcRow?.grid_school_tag).toBeNull()
  })

  it('serves house_vedha rows carrying null grid_basis (not grid-based)', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({}))
    const result = await computeKalaNow(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    expect(result.vedha_gochara[0]?.grid_basis).toBeNull()
    expect(result.vedha_gochara[0]?.grid_school_tag).toBeNull()
  })

  it('serves the PG353 malefic-count grading verbatim in house_vedha detail', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({}))
    const result = await computeKalaNow(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    expect(result.vedha_gochara[0]?.detail).toMatchObject({
      malefic_count: 1,
      malefic_effect_grade: 'fear',
      malefic_grade_uncited_extension: true,
    })
  })

  it('serves vedha_kind=latta rows as REAL cited (uncited_extension=false), distinct from sarvatobhadra', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({
      vedhaRows: [{ ...VEDHA_ROWS[2]!, is_current: true }],
    }))
    const result = await computeKalaNow(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    const lattaRow = result.vedha_gochara.find((r) => r.vedha_kind === 'latta')
    expect(lattaRow).toBeDefined()
    expect(lattaRow?.uncited_extension).toBe(false)
    expect(lattaRow?.classical_citation).toContain('PG339')
    expect(lattaRow?.detail['effect_description']).toBe('A great loss.')
  })

  it('never conflates all three vedha_kind values when all are current simultaneously', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({
      vedhaRows: [
        { ...VEDHA_ROWS[0]!, is_current: true },
        { ...VEDHA_ROWS[1]!, is_current: true },
        { ...VEDHA_ROWS[2]!, is_current: true },
      ],
    }))
    const result = await computeKalaNow(TEST_CHART_ID, {}, TEST_PRINCIPAL)
    expect(result.vedha_gochara).toHaveLength(3)
    const kinds = result.vedha_gochara.map((r) => r.vedha_kind).sort()
    expect(kinds).toEqual(['house_vedha', 'latta', 'sarvatobhadra'])
  })
})
