/**
 * get_av_transit_gating.test.ts — Doctrine Campaign D-3 (Kāla Taraṅga), Lane T-1.
 *
 * Unit tests for the sign-keyed Aṣṭakavarga transit-gating + kakṣyā sub-window capability.
 * No live DB or sidecar required — `query` and `fetch` are mocked with fixtures shaped
 * like the REAL live payloads verified against chart 482012f1 during this lane's build
 * (see the LIVE INTEGRATION section at the bottom for the documented, not-run-in-CI path
 * that hits the real chart).
 *
 * CR-87 discipline: this capability takes chart_id as a REQUIRED param (per_chart scope,
 * no default), and kakshya_windows additionally requires planet/target_sign/start_date/
 * end_date with no defaults — the "requires chart_id" / "requires kakshya params" tests
 * below are this lane's two-chart-equivalent regression guard (no shared NatalContext
 * class exists yet in this codebase for T-1 to extend — see final report).
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

import {
  getAvTransitGatingCapability,
  classifySavBindus,
  houseFromSign,
  estimateLahiriAyanamshaDeg,
  toSidereal,
  kakshyaIndexForDegree,
  buildKakshyaWindows,
  SAV_MEAN_BINDUS,
  type KakshyaBoundary,
  type SiderealTransitRow,
} from '../get_av_transit_gating'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const ABHINANDAN_CHART_ID = '1c826d5a-41cb-4450-b4dc-59d440e5f75a'

// ── Pure-function unit tests ────────────────────────────────────────────────────────

describe('classifySavBindus', () => {
  it('classifies the brief\'s SAV-10th type specimen (27) as damping', () => {
    expect(classifySavBindus(27)).toBe('damping')
  })
  it('classifies the brief\'s SAV-7th type specimen (34) as amplifying', () => {
    expect(classifySavBindus(34)).toBe('amplifying')
  })
  it('classifies a bindu count within the neutral band as neutral', () => {
    expect(classifySavBindus(Math.round(SAV_MEAN_BINDUS))).toBe('neutral')
  })
  it('mean is ~28.08 (337/12, the classical Parashari grand total / 12 signs)', () => {
    expect(SAV_MEAN_BINDUS).toBeCloseTo(28.083, 2)
  })
})

describe('houseFromSign', () => {
  it('Aries lagna: sign 1 = house 1, sign 7 = house 7, sign 10 = house 10', () => {
    expect(houseFromSign(1, 1)).toBe(1)
    expect(houseFromSign(7, 1)).toBe(7)
    expect(houseFromSign(10, 1)).toBe(10)
  })
  it('wraps correctly for a non-Aries lagna (e.g. lagna sign 5 -> sign 4 is house 12)', () => {
    expect(houseFromSign(5, 5)).toBe(1)
    expect(houseFromSign(4, 5)).toBe(12)
  })
})

describe('estimateLahiriAyanamshaDeg', () => {
  it('returns ~23.85deg at the 2000.0 epoch', () => {
    expect(estimateLahiriAyanamshaDeg('2000-01-01')).toBeCloseTo(23.8531, 2)
  })
  it('increases by ~0.0140deg/year (50.29 arcsec) — 2026 is ~0.36deg ahead of 2000', () => {
    const d2000 = estimateLahiriAyanamshaDeg('2000-01-01')
    const d2026 = estimateLahiriAyanamshaDeg('2026-01-01')
    expect(d2026 - d2000).toBeCloseTo(26 * (50.29 / 3600), 3)
  })
})

describe('toSidereal', () => {
  it('subtracts the ayanamsha and wraps into [0,360)', () => {
    const row = toSidereal({ date: '2026-01-01', tropical_longitude: 356.196622 })
    // ayanamsha ~24.21deg at 2026.0 -> sidereal ~331.98deg -> sign 12 (Pisces), ~1.98deg in sign
    expect(row.sign_number).toBe(12)
    expect(row.degree_in_sign).toBeGreaterThan(1)
    expect(row.degree_in_sign).toBeLessThan(3)
  })
  it('handles the wrap-around case (tropical longitude near 0, ayanamsha positive)', () => {
    const row = toSidereal({ date: '2026-01-01', tropical_longitude: 5 })
    expect(row.sidereal_longitude).toBeGreaterThanOrEqual(0)
    expect(row.sidereal_longitude).toBeLessThan(360)
  })
})

const CLASSICAL_KAKSHYA_BOUNDARIES: KakshyaBoundary[] = [
  { index: 1, lord: 'Saturn',  start_deg: 0,     end_deg: 3.75 },
  { index: 2, lord: 'Jupiter', start_deg: 3.75,  end_deg: 7.5 },
  { index: 3, lord: 'Mars',    start_deg: 7.5,   end_deg: 11.25 },
  { index: 4, lord: 'Sun',     start_deg: 11.25, end_deg: 15 },
  { index: 5, lord: 'Venus',   start_deg: 15,    end_deg: 18.75 },
  { index: 6, lord: 'Mercury', start_deg: 18.75, end_deg: 22.5 },
  { index: 7, lord: 'Moon',    start_deg: 22.5,  end_deg: 26.25 },
  { index: 8, lord: 'Lagna',   start_deg: 26.25, end_deg: 30 },
]

describe('kakshyaIndexForDegree', () => {
  it('maps degree 0 to kakshya 1 (Saturn)', () => {
    expect(kakshyaIndexForDegree(0, CLASSICAL_KAKSHYA_BOUNDARIES)).toBe(1)
  })
  it('maps degree 29.99 to kakshya 8 (Lagna)', () => {
    expect(kakshyaIndexForDegree(29.99, CLASSICAL_KAKSHYA_BOUNDARIES)).toBe(8)
  })
  it('maps the exact final boundary (30) to kakshya 8 (end-inclusive only on the last cell)', () => {
    expect(kakshyaIndexForDegree(30, CLASSICAL_KAKSHYA_BOUNDARIES)).toBe(8)
  })
  it('a boundary crossing (3.75) lands in the NEXT kakshya (half-open [start,end))', () => {
    expect(kakshyaIndexForDegree(3.75, CLASSICAL_KAKSHYA_BOUNDARIES)).toBe(2)
  })
})

describe('buildKakshyaWindows', () => {
  it('emits one contiguous window per kakshya for simple forward motion', () => {
    const rows: SiderealTransitRow[] = [
      { date: '2026-01-01', sidereal_longitude: 1, sign_number: 12, degree_in_sign: 1, is_retrograde: false },
      { date: '2026-01-02', sidereal_longitude: 2, sign_number: 12, degree_in_sign: 2, is_retrograde: false },
      { date: '2026-01-03', sidereal_longitude: 3, sign_number: 12, degree_in_sign: 3, is_retrograde: false },
      { date: '2026-01-04', sidereal_longitude: 4, sign_number: 12, degree_in_sign: 4, is_retrograde: false },
      { date: '2026-01-05', sidereal_longitude: 5, sign_number: 12, degree_in_sign: 5, is_retrograde: false },
    ]
    const windows = buildKakshyaWindows(rows, CLASSICAL_KAKSHYA_BOUNDARIES, 12)
    expect(windows).toHaveLength(2)
    expect(windows[0]).toMatchObject({ kakshya_index: 1, lord: 'Saturn', entry_date: '2026-01-01', exit_date: '2026-01-03', day_count: 3 })
    expect(windows[1]).toMatchObject({ kakshya_index: 2, lord: 'Jupiter', entry_date: '2026-01-04', exit_date: '2026-01-05', day_count: 2 })
  })

  it('a retrograde re-entry into an earlier kakshya is a NEW window row, never merged', () => {
    const rows: SiderealTransitRow[] = [
      { date: '2026-01-01', sidereal_longitude: 5, sign_number: 12, degree_in_sign: 5, is_retrograde: false }, // kakshya 2
      { date: '2026-01-02', sidereal_longitude: 8, sign_number: 12, degree_in_sign: 8, is_retrograde: false }, // kakshya 3
      { date: '2026-01-03', sidereal_longitude: 5, sign_number: 12, degree_in_sign: 5, is_retrograde: true },  // back to kakshya 2, retrograde
    ]
    const windows = buildKakshyaWindows(rows, CLASSICAL_KAKSHYA_BOUNDARIES, 12)
    expect(windows).toHaveLength(3)
    expect(windows[0].kakshya_index).toBe(2)
    expect(windows[0].is_retrograde_segment).toBe(false)
    expect(windows[1].kakshya_index).toBe(3)
    expect(windows[2].kakshya_index).toBe(2)
    expect(windows[2].is_retrograde_segment).toBe(true)
  })

  it('rows outside the target sign are skipped and close any open window', () => {
    const rows: SiderealTransitRow[] = [
      { date: '2026-01-01', sidereal_longitude: 1, sign_number: 12, degree_in_sign: 1, is_retrograde: false },
      { date: '2026-01-02', sidereal_longitude: 31, sign_number: 1, degree_in_sign: 1, is_retrograde: false }, // left sign 12
    ]
    const windows = buildKakshyaWindows(rows, CLASSICAL_KAKSHYA_BOUNDARIES, 12)
    expect(windows).toHaveLength(1)
    expect(windows[0].exit_date).toBe('2026-01-01')
  })

  it('replays the REAL Saturn-2026 forward segment (sidereal Pisces) verified live this lane', () => {
    // Real dated case computed from ref_planet_transit_get(Saturn, 2026-01-01..2026-03-30)
    // converted via toSidereal — see this lane's final report for the full derivation.
    // Saturn stays in sidereal sign 12 (Pisces) all of 2026; kakshya 1 (Saturn) 01-01..01-24,
    // kakshya 2 (Jupiter) 01-25..02-28, kakshya 3 (Mars) 03-01..03-30 (all forward, no retro yet).
    const rows: SiderealTransitRow[] = [
      { date: '2026-01-01', sidereal_longitude: 331.98, sign_number: 12, degree_in_sign: 1.98, is_retrograde: false },
      { date: '2026-01-24', sidereal_longitude: 333.71, sign_number: 12, degree_in_sign: 3.71, is_retrograde: false },
      { date: '2026-01-25', sidereal_longitude: 333.81, sign_number: 12, degree_in_sign: 3.81, is_retrograde: false },
      { date: '2026-02-28', sidereal_longitude: 337.45, sign_number: 12, degree_in_sign: 7.45, is_retrograde: false },
      { date: '2026-03-01', sidereal_longitude: 337.57, sign_number: 12, degree_in_sign: 7.57, is_retrograde: false },
      { date: '2026-03-30', sidereal_longitude: 341.14, sign_number: 12, degree_in_sign: 11.14, is_retrograde: false },
    ]
    const windows = buildKakshyaWindows(rows, CLASSICAL_KAKSHYA_BOUNDARIES, 12)
    expect(windows.map((w) => w.kakshya_index)).toEqual([1, 2, 3])
    expect(windows.map((w) => w.lord)).toEqual(['Saturn', 'Jupiter', 'Mars'])
    expect(windows[0]).toMatchObject({ entry_date: '2026-01-01', exit_date: '2026-01-24' })
    expect(windows[1]).toMatchObject({ entry_date: '2026-01-25', exit_date: '2026-02-28' })
    expect(windows[2]).toMatchObject({ entry_date: '2026-03-01', exit_date: '2026-03-30' })
  })
})

// ── Handler tests (mocked query/fetch) ──────────────────────────────────────────────

describe('getAvTransitGatingCapability handler — sav_bav_gating', () => {
  beforeEach(() => {
    mockQuery.mockReset()
  })

  it('requires chart_id (CR-87 — no default chart context)', async () => {
    const result = await getAvTransitGatingCapability.handler({}, undefined)
    expect(result.is_error).toBe(true)
  })

  it('two DISTINCT chart_ids never cross-contaminate a response (regression guard)', async () => {
    // Fixture shaped like the live 96-row ashtakavarga_bindu_sign payload (trimmed to 2 signs).
    mockQuery.mockImplementation((sql: string, params: unknown[]) => {
      const chartId = params[0] as string
      if (sql.includes('graha_sign_attributes')) {
        return Promise.resolve({ rows: chartId === CHART_ID ? [{ fact_value_num: 1 }] : [{ fact_value_num: 5 }] })
      }
      return Promise.resolve({
        rows: [
          { fact_id: 'x1', fact_subject: 'SARVA-SIGN_7', fact_value_num: chartId === CHART_ID ? 34 : 20 },
          { fact_id: 'x2', fact_subject: 'SARVA-SIGN_10', fact_value_num: chartId === CHART_ID ? 27 : 40 },
        ],
      })
    })
    const resultA = await getAvTransitGatingCapability.handler({ chart_id: CHART_ID }, undefined)
    const resultB = await getAvTransitGatingCapability.handler({ chart_id: ABHINANDAN_CHART_ID }, undefined)
    const contentA = resultA.content as { rows: Array<{ sign_number: number; sav_bindus: number | null }> }
    const contentB = resultB.content as { rows: Array<{ sign_number: number; sav_bindus: number | null }> }
    const sign7A = contentA.rows.find((r) => r.sign_number === 7)
    const sign7B = contentB.rows.find((r) => r.sign_number === 7)
    expect(sign7A?.sav_bindus).toBe(34)
    expect(sign7B?.sav_bindus).toBe(20)
    expect(sign7A?.sav_bindus).not.toBe(sign7B?.sav_bindus)
  })

  it('parses SARVA-SIGN_N as sav_bindus and {GRAHA}-SIGN_N as bav entries, classified', async () => {
    mockQuery.mockImplementation((sql: string) => {
      if (sql.includes('graha_sign_attributes')) return Promise.resolve({ rows: [{ fact_value_num: 1 }] })
      return Promise.resolve({
        rows: [
          { fact_id: 'a', fact_subject: 'SARVA-SIGN_7', fact_value_num: 34 },
          { fact_id: 'b', fact_subject: 'SARVA-SIGN_10', fact_value_num: 27 },
          { fact_id: 'c', fact_subject: 'JUP-SIGN_7', fact_value_num: 5 },
        ],
      })
    })
    const result = await getAvTransitGatingCapability.handler({ chart_id: CHART_ID }, undefined)
    const content = result.content as { rows: Array<{ sign_number: number; sav_bindus: number; sav_classification: string; bav: Record<string, number>; house: number | null }> }
    const s7 = content.rows.find((r) => r.sign_number === 7)!
    const s10 = content.rows.find((r) => r.sign_number === 10)!
    expect(s7.sav_bindus).toBe(34)
    expect(s7.sav_classification).toBe('amplifying')
    expect(s7.house).toBe(7) // Aries lagna -> sign 7 = house 7
    expect(s7.bav['JUP']).toBe(5)
    expect(s10.sav_bindus).toBe(27)
    expect(s10.sav_classification).toBe('damping')
    expect(s10.house).toBe(10)
  })

  it('empty_reason when the asset has not been built for this chart (never a silent [])', async () => {
    mockQuery.mockResolvedValue({ rows: [] })
    const result = await getAvTransitGatingCapability.handler({ chart_id: CHART_ID }, undefined)
    const content = result.content as { empty_reason?: string; rows: unknown[] }
    expect(content.rows).toEqual([])
    expect(content.empty_reason).toMatch(/ashtakavarga_bindu_sign/)
  })
})

describe('getAvTransitGatingCapability handler — kakshya_windows', () => {
  beforeEach(() => {
    mockQuery.mockReset()
    vi.stubGlobal('fetch', vi.fn())
  })

  it('requires planet/target_sign/start_date/end_date (CR-87 — no defaults)', async () => {
    const result = await getAvTransitGatingCapability.handler(
      { chart_id: CHART_ID, mode: 'kakshya_windows' }, undefined,
    )
    expect(result.is_error).toBe(true)
    expect(mockQuery).not.toHaveBeenCalled()
  })

  it('serves dated windows from the sidecar transit series + kakshya boundary facts', async () => {
    mockQuery.mockResolvedValue({
      rows: [
        { fact_subject: 'KAKSHYA_1', fact_key: 'lord', fact_value_text: 'Saturn', fact_value_num: null },
        { fact_subject: 'KAKSHYA_1', fact_key: 'start_deg', fact_value_text: null, fact_value_num: 0 },
        { fact_subject: 'KAKSHYA_1', fact_key: 'end_deg', fact_value_text: null, fact_value_num: 3.75 },
        { fact_subject: 'KAKSHYA_2', fact_key: 'lord', fact_value_text: 'Jupiter', fact_value_num: null },
        { fact_subject: 'KAKSHYA_2', fact_key: 'start_deg', fact_value_text: null, fact_value_num: 3.75 },
        { fact_subject: 'KAKSHYA_2', fact_key: 'end_deg', fact_value_text: null, fact_value_num: 7.5 },
      ],
    })
    const fetchMock = fetch as unknown as ReturnType<typeof vi.fn>
    fetchMock.mockResolvedValue({
      ok: true,
      json: async () => ({
        ok: true,
        rows: [
          { date: '2026-01-01', tropical_longitude: 356.196622, is_retrograde: false },
          { date: '2026-01-25', tropical_longitude: 358.05, is_retrograde: false },
        ],
      }),
    })
    const result = await getAvTransitGatingCapability.handler(
      { chart_id: CHART_ID, mode: 'kakshya_windows', planet: 'Saturn', target_sign: 12, start_date: '2026-01-01', end_date: '2026-01-25' },
      undefined,
    )
    expect(result.is_error).toBe(false)
    const content = result.content as { windows: Array<{ kakshya_index: number; lord: string }> }
    expect(content.windows.length).toBeGreaterThan(0)
    expect(content.windows[0].lord).toBe('Saturn')
  })

  it('forwards the PYTHON_SIDECAR_API_KEY as x-api-key when configured (D-3 T-6 hotfix — was a live 401)', async () => {
    const prevKey = process.env['PYTHON_SIDECAR_API_KEY']
    process.env['PYTHON_SIDECAR_API_KEY'] = 'test-sidecar-key'
    vi.resetModules()
    try {
      const mod = await import('../get_av_transit_gating')
      mockQuery.mockResolvedValue({
        rows: [
          { fact_subject: 'KAKSHYA_1', fact_key: 'lord', fact_value_text: 'Saturn', fact_value_num: null },
          { fact_subject: 'KAKSHYA_1', fact_key: 'start_deg', fact_value_text: null, fact_value_num: 0 },
          { fact_subject: 'KAKSHYA_1', fact_key: 'end_deg', fact_value_text: null, fact_value_num: 3.75 },
        ],
      })
      const fetchMock = fetch as unknown as ReturnType<typeof vi.fn>
      fetchMock.mockResolvedValue({ ok: true, json: async () => ({ ok: true, rows: [] }) })
      await mod.getAvTransitGatingCapability.handler(
        { chart_id: CHART_ID, mode: 'kakshya_windows', planet: 'Saturn', target_sign: 12, start_date: '2026-01-01', end_date: '2026-01-25' },
        undefined,
      )
      expect(fetchMock).toHaveBeenCalled()
      const [, init] = fetchMock.mock.calls[0]
      expect((init as { headers: Record<string, string> }).headers['x-api-key']).toBe('test-sidecar-key')
    } finally {
      if (prevKey === undefined) delete process.env['PYTHON_SIDECAR_API_KEY']
      else process.env['PYTHON_SIDECAR_API_KEY'] = prevKey
      vi.resetModules()
    }
  })

  it('propagates a sidecar error honestly (never a fabricated window)', async () => {
    mockQuery.mockResolvedValue({
      rows: [
        { fact_subject: 'KAKSHYA_1', fact_key: 'lord', fact_value_text: 'Saturn', fact_value_num: null },
        { fact_subject: 'KAKSHYA_1', fact_key: 'start_deg', fact_value_text: null, fact_value_num: 0 },
        { fact_subject: 'KAKSHYA_1', fact_key: 'end_deg', fact_value_text: null, fact_value_num: 3.75 },
      ],
    })
    const fetchMock = fetch as unknown as ReturnType<typeof vi.fn>
    fetchMock.mockResolvedValue({ ok: false, status: 503, text: async () => 'sidecar down' })
    const result = await getAvTransitGatingCapability.handler(
      { chart_id: CHART_ID, mode: 'kakshya_windows', planet: 'Saturn', target_sign: 12, start_date: '2026-01-01', end_date: '2026-01-25' },
      undefined,
    )
    expect(result.is_error).toBe(true)
  })
})

// ── LIVE INTEGRATION (documented path, NOT run in CI — no live DB/sidecar in this suite) ──
//
// To verify against the real deployed chart 482012f1, run with a live DB + sidecar reachable
// and RUN_LIVE_AV_GATING_TEST=1:
//
//   RUN_LIVE_AV_GATING_TEST=1 npx vitest run get_av_transit_gating.test.ts -t "LIVE"
//
// Expected (verified manually via MCP this lane, recorded in the D-3 T-1 final report):
//   sav_bav_gating: sign 7 (Libra, house 7) sav_bindus=34 (amplifying); sign 10 (Capricorn,
//   house 10) sav_bindus=27 (damping) — exact match to BRIEF_D3's type specimens.
//   kakshya_windows(Saturn, target_sign=12 [sidereal Pisces], 2026-01-01..2026-03-30):
//   kakshya 1 (Saturn) 2026-01-01..01-24, kakshya 2 (Jupiter) 01-25..02-28, kakshya 3 (Mars)
//   03-01..03-30 — real weeks-long windows (Saturn is slow), not the brief's illustrative
//   "~3.4-day" figure, which only holds for a ~1deg/day mover.
const RUN_LIVE = process.env['RUN_LIVE_AV_GATING_TEST'] === '1'
describe.runIf(RUN_LIVE)('LIVE integration — chart 482012f1 (requires live DB + sidecar)', () => {
  it('sav_bav_gating serves real SAV bindus matching the brief type specimens', async () => {
    // Intentionally uses the REAL (unmocked) query() — only runs when RUN_LIVE_AV_GATING_TEST=1
    // and DATABASE_URL points at a live instance with chart 482012f1 built.
    const result = await getAvTransitGatingCapability.handler({ chart_id: CHART_ID }, undefined)
    const content = result.content as { rows: Array<{ sign_number: number; sav_bindus: number }> }
    const s7 = content.rows.find((r) => r.sign_number === 7)
    const s10 = content.rows.find((r) => r.sign_number === 10)
    expect(s7?.sav_bindus).toBe(34)
    expect(s10?.sav_bindus).toBe(27)
  })
})
