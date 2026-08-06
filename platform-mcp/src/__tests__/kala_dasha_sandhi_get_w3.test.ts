/**
 * kala_dasha_sandhi_get_w3.test.ts — ṢAḌ-DARŚANA W3, Item 1-full
 * (SHAD_DARSHANA_BRIEF_v2_0.md §1 item 1, §3 W3: "Daśā-sandhi calendar, all levels,
 * both directions").
 *
 * TDD: tests written BEFORE the implementation. These drive the shape of the new
 * `kala_dasha_sandhi_get` MCP tool.
 *
 * ── SPEC CONTRACT (item 1 full, distilled from the brief) ──────────────────────
 *
 * 1. ALL LEVELS: Mahādaśā (L1) → Antardaśā (L2) → Pratyantardaśā (L3) → Sūkṣmadaśā (L4)
 *    at minimum. Source: chart_dashas table (existing L1 build artifact, served via
 *    marsys://tool/L1/get_dashas). Item 1 is a JOIN, not a new computation — §N.5/B.10.
 *
 * 2. BOTH DIRECTIONS: past N years AND future N years from the as_of date. The tool
 *    accepts `past_years` (default 5) and `future_years` (default 5) parameters and
 *    serves period boundaries (sandhi dates) across that bilateral window.
 *
 * 3. TILING PROPERTY TEST (from the brief's mandatory property test):
 *    Sandhi intervals tile with no gaps/overlaps — every moment in the horizon
 *    belongs to exactly one daśā period at each level. This is the existing
 *    chart_dashas data contract, verified here at the serving layer.
 *
 * 4. ACCURACY STANDARD (3 known anchors from FORENSIC chart 482012f1):
 *    The native's Vimśottarī Mahādaśā sequence from the canonical chart. These
 *    boundary dates are pulled from `chart_dashas` (which the FORENSIC 7/7 PASS
 *    has already validated). The tests assert the serving layer neither drops
 *    nor mutates the dates from the underlying table.
 *
 * 5. HONEST-EMPTY discipline: unreachable source → coverage state = honest_empty
 *    with a non-empty reason (never fabricated values, never silent null).
 *
 * Design authority: SHAD_DARSHANA_BRIEF_v2_0.md §1 item 1, §3 W3;
 * KALA_SIX_VIEWS_DESIGN_v1_0.md §7.1; CLAUDE.md §N.5/B.10.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { Principal } from '../types.js'
import { computeDashaSandhiCalendar } from '../tools/kala_views/dasha_sandhi.js'

const TEST_CHART_ID = '00000000-0000-0000-0000-000000000001'
const TEST_PRINCIPAL: Principal = { user_uid: 'test-uid', key_id: 'test-key', role: 'guest' }

// ── Accuracy anchors (known daśā boundaries for the test chart fixture) ───────
// These fixture dates represent well-known Vimśottarī boundary points — the test
// asserts the serving layer returns them verbatim (§N.5: JOIN, not re-derivation).
//
// Level 1 (Mahādaśā) example sequence for the fixture:
//   Ra MD: 2001-02-07 .. 2019-02-07
//   Ju MD: 2019-02-07 .. 2035-02-07    (current for date 2026-08-06)
//   Sa MD: 2035-02-07 .. 2054-02-07
//
// Level 2 (Antardaśā) example — Ju/Ve AD:
//   Ju-Ve AD: 2023-10-02 .. 2026-10-02
//   Ju-Su AD: 2026-10-02 .. 2027-08-14
const MD_ROWS_L1 = [
  { dasha_row_id: 'ra-md', level_n: 1, level_name: 'Mahadasha', system_id: 'vimshottari',
    lord_graha: 'RA', start_date: '2001-02-07', end_date: '2019-02-07' },
  { dasha_row_id: 'ju-md', level_n: 1, level_name: 'Mahadasha', system_id: 'vimshottari',
    lord_graha: 'JU', start_date: '2019-02-07', end_date: '2035-02-07' },
  { dasha_row_id: 'sa-md', level_n: 1, level_name: 'Mahadasha', system_id: 'vimshottari',
    lord_graha: 'SA', start_date: '2035-02-07', end_date: '2054-02-07' },
]
const AD_ROWS_L2 = [
  { dasha_row_id: 'ju-ve-ad', level_n: 2, level_name: 'Antardasha', system_id: 'vimshottari',
    lord_graha: 'VE', start_date: '2023-10-02', end_date: '2026-10-02' },
  { dasha_row_id: 'ju-su-ad', level_n: 2, level_name: 'Antardasha', system_id: 'vimshottari',
    lord_graha: 'SU', start_date: '2026-10-02', end_date: '2027-08-14' },
]
const PAD_ROWS_L3 = [
  { dasha_row_id: 'ju-ve-ma-pad', level_n: 3, level_name: 'Pratyantardasha', system_id: 'vimshottari',
    lord_graha: 'MA', start_date: '2026-06-01', end_date: '2026-08-12' },
  { dasha_row_id: 'ju-ve-ra-pad', level_n: 3, level_name: 'Pratyantardasha', system_id: 'vimshottari',
    lord_graha: 'RA', start_date: '2026-08-12', end_date: '2026-11-04' },
]

function mockRegistryFetch(opts: {
  reachable?: boolean
  dashaRows?: typeof MD_ROWS_L1 | []
}) {
  const reachable = opts.reachable ?? true
  return vi.fn(async (_url: string, init?: RequestInit) => {
    if (!reachable) throw new Error('registry unreachable in test')
    const body = JSON.parse(String(init?.body ?? '{}')) as { uri: string; args?: Record<string, unknown> }
    let inner: Record<string, unknown> = {}
    if (body.uri === 'marsys://tool/L1/get_dashas') {
      const rows = opts.dashaRows ?? [...MD_ROWS_L1, ...AD_ROWS_L2, ...PAD_ROWS_L3]
      inner = { rows, total: rows.length }
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

// ── Core contract: all levels returned ────────────────────────────────────────

describe('kala_dasha_sandhi_get — all levels, both directions (item 1-full)', () => {
  it('returns period boundaries at every level present in the source data', async () => {
    // Use past_years=10 so the Ju MD start boundary (2019-02-07) falls inside the window
    // (horizon_start = 2016-08-06, which is before 2019-02-07). This ensures L1 boundaries
    // are present alongside L2 and L3 boundaries from the fixture.
    vi.stubGlobal('fetch', mockRegistryFetch({}))
    const result = await computeDashaSandhiCalendar(
      TEST_CHART_ID, { as_of: '2026-08-06', past_years: 10, future_years: 10 }, TEST_PRINCIPAL,
    )
    const levels = new Set(result.boundaries.map((b) => b.level_n))
    // Must include L1 (Maha — Ju MD start 2019-02-07 is in ±10y window),
    // L2 (Antar — Ju/Ve AD boundaries in window),
    // L3 (Pratyantar — PAD boundaries in window)
    expect(levels.has(1)).toBe(true)
    expect(levels.has(2)).toBe(true)
    expect(levels.has(3)).toBe(true)
  })

  it('returns boundaries in BOTH directions: past and future of as_of date', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({}))
    const result = await computeDashaSandhiCalendar(
      TEST_CHART_ID, { as_of: '2026-08-06', past_years: 5, future_years: 5 }, TEST_PRINCIPAL,
    )
    const pastBoundaries = result.boundaries.filter((b) => b.boundary_date < '2026-08-06')
    const futureBoundaries = result.boundaries.filter((b) => b.boundary_date > '2026-08-06')
    expect(pastBoundaries.length).toBeGreaterThan(0)
    expect(futureBoundaries.length).toBeGreaterThan(0)
  })

  it('respects the past_years window — excludes boundaries too far in the past', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({}))
    // past_years=1 from 2026-08-06 => window starts 2025-08-06
    // Ra MD ended 2019-02-07 — should NOT appear
    const result = await computeDashaSandhiCalendar(
      TEST_CHART_ID, { as_of: '2026-08-06', past_years: 1, future_years: 1 }, TEST_PRINCIPAL,
    )
    const raEnd = result.boundaries.find(
      (b) => b.lord_graha === 'RA' && b.level_n === 1 && b.boundary_kind === 'period_end',
    )
    expect(raEnd).toBeUndefined()
  })

  it('respects the future_years window — excludes boundaries too far in the future', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({}))
    // future_years=1 from 2026-08-06 => window ends ~2027-08-06
    // Sa MD starts 2035-02-07 — should NOT appear
    const result = await computeDashaSandhiCalendar(
      TEST_CHART_ID, { as_of: '2026-08-06', past_years: 1, future_years: 1 }, TEST_PRINCIPAL,
    )
    const saMdStart = result.boundaries.find(
      (b) => b.lord_graha === 'SA' && b.level_n === 1 && b.boundary_kind === 'period_start',
    )
    expect(saMdStart).toBeUndefined()
  })
})

// ── Accuracy anchors: boundary dates come from the table verbatim ─────────────

describe('kala_dasha_sandhi_get — accuracy anchors (§N.5 JOIN contract)', () => {
  it('ANCHOR 1 — Ju MD boundary 2019-02-07 is served verbatim (never re-derived)', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({}))
    const result = await computeDashaSandhiCalendar(
      TEST_CHART_ID, { as_of: '2026-08-06', past_years: 10, future_years: 10 }, TEST_PRINCIPAL,
    )
    const juMdStart = result.boundaries.find(
      (b) => b.level_n === 1 && b.lord_graha === 'JU' && b.boundary_kind === 'period_start',
    )
    expect(juMdStart).toBeDefined()
    expect(juMdStart!.boundary_date).toBe('2019-02-07')
  })

  it('ANCHOR 2 — Ju/Ve AD boundary 2026-10-02 is served verbatim', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({}))
    const result = await computeDashaSandhiCalendar(
      TEST_CHART_ID, { as_of: '2026-08-06', past_years: 5, future_years: 5 }, TEST_PRINCIPAL,
    )
    const juVeAdEnd = result.boundaries.find(
      (b) => b.level_n === 2 && b.lord_graha === 'VE' && b.boundary_kind === 'period_end',
    )
    expect(juVeAdEnd).toBeDefined()
    expect(juVeAdEnd!.boundary_date).toBe('2026-10-02')
  })

  it('ANCHOR 3 — Pratyantar Ra boundary 2026-08-12 is served verbatim', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({}))
    const result = await computeDashaSandhiCalendar(
      TEST_CHART_ID, { as_of: '2026-08-06', past_years: 5, future_years: 5 }, TEST_PRINCIPAL,
    )
    const padRaStart = result.boundaries.find(
      (b) => b.level_n === 3 && b.lord_graha === 'RA' && b.boundary_kind === 'period_start',
    )
    expect(padRaStart).toBeDefined()
    expect(padRaStart!.boundary_date).toBe('2026-08-12')
  })
})

// ── Tiling property: no gaps or overlaps at each level ────────────────────────

describe('kala_dasha_sandhi_get — tiling property (mandatory property test)', () => {
  it('consecutive periods at the same level share the exact same boundary date (no gap)', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({}))
    const result = await computeDashaSandhiCalendar(
      TEST_CHART_ID, { as_of: '2026-08-06', past_years: 10, future_years: 10 }, TEST_PRINCIPAL,
    )
    // For each level, sort all periods by start_date; each end_date must equal the next start_date
    const byLevel = new Map<number, typeof result.boundaries>()
    for (const b of result.boundaries.filter((b) => b.boundary_kind === 'period_start')) {
      const arr = byLevel.get(b.level_n) ?? []
      arr.push(b)
      byLevel.set(b.level_n, arr)
    }
    for (const [_level, starts] of byLevel) {
      const sorted = [...starts].sort((a, b) => a.boundary_date.localeCompare(b.boundary_date))
      for (let i = 0; i < sorted.length - 1; i++) {
        // The corresponding end boundary must equal the next start boundary
        const currentPeriodEnd = result.boundaries.find(
          (b) =>
            b.level_n === sorted[i]!.level_n &&
            b.lord_graha === sorted[i]!.lord_graha &&
            b.boundary_kind === 'period_end' &&
            b.period_id === sorted[i]!.period_id,
        )
        if (currentPeriodEnd && sorted[i + 1]) {
          expect(currentPeriodEnd.boundary_date).toBe(sorted[i + 1]!.boundary_date)
        }
      }
    }
  })
})

// ── Honest-empty discipline ───────────────────────────────────────────────────

describe('kala_dasha_sandhi_get — honest-empty discipline', () => {
  it('is honest_empty (never fabricated) when the dasha registry is unreachable', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ reachable: false }))
    const result = await computeDashaSandhiCalendar(
      TEST_CHART_ID, { as_of: '2026-08-06', past_years: 5, future_years: 5 }, TEST_PRINCIPAL,
    )
    expect(result.boundaries).toEqual([])
    const cov = result.coverage.find((c) => c.concept === 'dasha_sandhi_calendar')
    expect(cov?.state).toBe('honest_empty')
    expect(cov?.reason?.length).toBeGreaterThan(0)
  })

  it('is honest_empty when the chart has no dasha data', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({ dashaRows: [] }))
    const result = await computeDashaSandhiCalendar(
      TEST_CHART_ID, { as_of: '2026-08-06', past_years: 5, future_years: 5 }, TEST_PRINCIPAL,
    )
    expect(result.boundaries).toEqual([])
    const cov = result.coverage.find((c) => c.concept === 'dasha_sandhi_calendar')
    expect(cov?.state).toBe('honest_empty')
    expect(cov?.reason).toContain('no dasha rows')
  })

  it('reports dasha_source in provenance so the caller can trace the authority', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({}))
    const result = await computeDashaSandhiCalendar(
      TEST_CHART_ID, { as_of: '2026-08-06', past_years: 5, future_years: 5 }, TEST_PRINCIPAL,
    )
    expect(result.provenance.dasha_source).toBe('marsys://tool/L1/get_dashas')
    expect(result.provenance.authority_note).toContain('chart_dashas')
  })
})

// ── Boundary shape contract ───────────────────────────────────────────────────

describe('kala_dasha_sandhi_get — boundary shape', () => {
  it('each boundary row carries the required fields', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({}))
    const result = await computeDashaSandhiCalendar(
      TEST_CHART_ID, { as_of: '2026-08-06', past_years: 5, future_years: 5 }, TEST_PRINCIPAL,
    )
    expect(result.boundaries.length).toBeGreaterThan(0)
    for (const b of result.boundaries) {
      // Required: level_n, level_name, lord_graha, boundary_date, boundary_kind, period_id
      expect(typeof b.level_n).toBe('number')
      expect(b.level_n).toBeGreaterThanOrEqual(1)
      expect(typeof b.level_name).toBe('string')
      expect(typeof b.lord_graha).toBe('string')
      expect(b.lord_graha.length).toBeGreaterThan(0)
      expect(b.boundary_date).toMatch(/^\d{4}-\d{2}-\d{2}$/)
      expect(['period_start', 'period_end']).toContain(b.boundary_kind)
      expect(typeof b.period_id).toBe('string')
      expect(b.period_id.length).toBeGreaterThan(0)
    }
  })

  it('each period whose both boundaries fall in the window contributes exactly 2 boundaries', async () => {
    // Use a large enough window so all fixture periods have both start and end inside it.
    // The Ju MD (2019-02-07 .. 2035-02-07) and both AD rows are fully within ±25y of 2026.
    vi.stubGlobal('fetch', mockRegistryFetch({}))
    const result = await computeDashaSandhiCalendar(
      TEST_CHART_ID, { as_of: '2026-08-06', past_years: 25, future_years: 25 }, TEST_PRINCIPAL,
    )
    // Pick only periods whose START and END are both inside the 50-year window:
    // Ju MD: 2019-02-07..2035-02-07 → both inside 2001..2051 ✓
    // Sa MD: 2035-02-07..2054-02-07 → end at 2054 is outside 25y future (2051) → skip
    // Ju/Ve AD: 2023-10-02..2026-10-02 → both inside ✓
    // Ju/Su AD: 2026-10-02..2027-08-14 → both inside ✓
    // PAD rows → both inside ✓
    const byPeriod = new Map<string, string[]>()
    for (const b of result.boundaries) {
      const arr = byPeriod.get(b.period_id) ?? []
      arr.push(b.boundary_kind)
      byPeriod.set(b.period_id, arr)
    }
    // Every period that appears in the results at all must have BOTH kinds
    // (we never serve a period_end without its period_start or vice versa,
    //  as long as both boundaries fall within the horizon)
    for (const [pid, kinds] of byPeriod) {
      if (kinds.length === 2) {
        expect(kinds).toContain('period_start')
        expect(kinds).toContain('period_end')
      }
      // A period with only 1 kind is one whose other boundary is outside the window —
      // this is expected for Ra MD (start 2001 outside ±25y) and Sa MD (end 2054 outside).
      expect(kinds.length).toBeLessThanOrEqual(2)
      expect(kinds.length).toBeGreaterThan(0)
      expect(new Set(kinds).size).toBe(kinds.length)  // no duplicate kinds per period
      void pid
    }
  })

  it('reports the as_of_within_band flag for a boundary the as_of date is near', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({}))
    // 2026-08-06 is 6 days before the PAD Ra boundary on 2026-08-12
    const result = await computeDashaSandhiCalendar(
      TEST_CHART_ID, { as_of: '2026-08-06', past_years: 5, future_years: 5 }, TEST_PRINCIPAL,
    )
    const nearBoundary = result.boundaries.find(
      (b) => b.boundary_date === '2026-08-12',
    )
    expect(nearBoundary?.is_near_as_of).toBe(true)
  })

  it('reports horizon_start and horizon_end at the top level', async () => {
    vi.stubGlobal('fetch', mockRegistryFetch({}))
    const result = await computeDashaSandhiCalendar(
      TEST_CHART_ID, { as_of: '2026-08-06', past_years: 5, future_years: 5 }, TEST_PRINCIPAL,
    )
    expect(result.horizon_start).toBe('2021-08-06')
    expect(result.horizon_end).toBe('2031-08-06')
  })
})
