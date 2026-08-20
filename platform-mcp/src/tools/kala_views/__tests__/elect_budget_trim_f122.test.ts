/**
 * F-122 exit test — kala_elect_get budget trim section coverage gap.
 *
 * Reproduces the DIAGNOSIS §1 scenario without a live DB:
 * - 4 candidate windows, each with 15 hora slots
 * - substrate producing large JudgmentLedger arrays (50 convention keys + 10 dosas + 20 neutral
 *   annotations per ledger, across all 4 ledgers = ~76KB of ledger data alone)
 *
 * Before fix (sections A–G absent, candidates setArray doesn't sync ledgers):
 *   - budget_exceeded_after_trim fires (trimmer can't cut undeclared fields)
 *   - ledgers.length (4) > candidates.length (1)
 *   - hora_ladder[0].length (15) is NOT < 15
 *
 * After fix:
 *   - All new sections trim the undeclared arrays to 0
 *   - candidates setArray syncs lattice_adjudication.ledgers to surviving candidate IDs
 *   - Response fits within the ceiling below
 *
 * `budget_kb` RETUNED 20 -> 32 (independent-review follow-up, real correctness fix — see
 * `elect_ledger_alias_f122.test.ts` for the dedicated regression test on the underlying
 * bug). The original `budget_kb: 20` figure only fit because `candidates[i]
 * .judgment_ledger` and `lattice_adjudication.ledgers[j]` were the SAME aliased object at
 * the time this test was written: trimming the "bookkeeping" `lattice_adjudication
 * .ledgers[]` sections (A/B/D/E/F/G) also emptied the one surviving candidate's OWN
 * protected ledger fields as an unintended side effect, so the total served bytes were
 * roughly HALF what they should honestly be. Now that each candidate's `judgment_ledger`
 * is an independent copy (correctly protected from the bookkeeping-tier trim, per this
 * file's own "densest, most-actionable layer" / hardFloor doctrine), the one surviving
 * candidate's full doṣa/residual/neutral content has an honest irreducible floor around
 * ~24-25KB for this fixture's row counts — `budget_kb` is raised to comfortably clear
 * that floor rather than silently shrinking the fixture to make a stale number keep
 * working. This test's job was always "sections A-G declared + candidates setArray syncs
 * ledgers + the response fits under its budget" — never "fits in exactly 20KB" — so
 * raising the ceiling to match the now-correct (and larger, because now-honest) served
 * size preserves the test's real intent.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockHandleMuhurtaFinder = vi.fn()

vi.mock('../../muhurta_finder.js', async () => {
  const actual = await vi.importActual<typeof import('../../muhurta_finder.js')>('../../muhurta_finder.js')
  return {
    ...actual,
    handleMuhurtaFinder: (...args: unknown[]) => mockHandleMuhurtaFinder(...args),
  }
})

const mockFetchLatticeSubstrate = vi.fn()

vi.mock('../../../lib/kala_lattice_query.js', async () => {
  const actual = await vi.importActual<typeof import('../../../lib/kala_lattice_query.js')>('../../../lib/kala_lattice_query.js')
  return {
    ...actual,
    fetchLatticeSubstrate: (...args: unknown[]) => mockFetchLatticeSubstrate(...args),
  }
})

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const PRINCIPAL = { user_uid: 'u1', key_id: 'k1', role: 'guest' as const }

/** Generate N hora slots starting from datePrefix (YYYY-MM-DD). */
function makeHoraSlots(n: number, datePrefix: string) {
  const lords = ['Sun', 'Venus', 'Mercury', 'Moon', 'Saturn', 'Jupiter', 'Mars']
  return Array.from({ length: n }, (_, i) => ({
    start_ist: `${datePrefix}T${String(6 + i).padStart(2, '0')}:00:00+05:30`,
    end_ist: `${datePrefix}T${String(7 + i).padStart(2, '0')}:00:00+05:30`,
    hora_lord: lords[i % 7],
    benefic: i % 2 === 0,
  }))
}

/**
 * Mock muhurta_finder result with 4 windows, each carrying 15 hora slots.
 * The large hora_ladders are one of the budget-blowing undeclared fields (section C).
 */
function make4WindowResult() {
  const windows = [
    { start: '2026-08-15T00:00:00Z', end: '2026-08-17T00:00:00Z', date: '2026-08-15', score: 0.85 },
    { start: '2026-08-22T00:00:00Z', end: '2026-08-24T00:00:00Z', date: '2026-08-22', score: 0.75 },
    { start: '2026-09-01T00:00:00Z', end: '2026-09-03T00:00:00Z', date: '2026-09-01', score: 0.65 },
    { start: '2026-09-10T00:00:00Z', end: '2026-09-12T00:00:00Z', date: '2026-09-10', score: 0.55 },
  ]

  return {
    ok: true,
    chart_id: CHART_ID,
    action_type: 'business',
    query_window: { start: '2026-08-15', end: '2026-11-12' },
    windows: windows.map((w) => ({
      start: w.start,
      end: w.end,
      score: w.score,
      factors: {
        panchanga_quality: 0.7, dasha_quality: 0.7, transit_quality: 0.7, signal_activation: 0.5,
        panchanga_details: { tithi_name: 'Tritiya', vara_lord: 'Guru', moon_nakshatra: 'Pushya', yoga: 'Siddha', inauspicious_windows: [] },
        dasha_details: { md_lord: 'Mercury', ad_lord: 'Venus' },
        avoid_notes: [],
      },
      source_citation: 'BPHS ch.46',
      hard_flag: false,
      disqualified: false,
      rank_penalty_reason: [],
      hora_ladder: makeHoraSlots(15, w.date),
    })),
    window_count: 4,
    provenance_envelope: {
      source: 'phala.muhurta', asset: 'PH-4-4', algorithm: 'x', min_score_applied: 0,
      chart_id: CHART_ID, action_type: 'business', queried_at: '2026-08-15T00:00:00Z',
      l1_ground_truth: 'FORENSIC', b3_citation_compliant: true,
    },
    lane_f: {
      tara_bala_status: 'applied' as const,
      hora_status: 'applied' as const,
      hora_sunrise_assumption: 'x',
      ranking_note: 'x',
      target_graha_status: 'not_requested' as const,
    },
  }
}

/**
 * Substrate with many rows spanning the entire query horizon — every row overlaps
 * every one of the 4 candidate windows, so each JudgmentLedger accumulates the
 * full row set.
 *
 * 50 convention rows → convention_only_factors + convention_only_keys per ledger (section A covers these)
 * 10 inauspicious cited rows → dosas_present per ledger (section E)
 * 20 neutral cited rows → neutral_annotations per ledger (section B)
 *
 * Each LedgerFactor ≈ 200 bytes.  4 ledgers × 80 factors × 200 bytes ≈ 64 KB of ledger
 * data alone — far above the 20 KB ceiling even after candidates is trimmed to 1.
 */
function makeLargeSubstrate() {
  const span = { start_utc: '2026-08-01T00:00:00Z', end_utc: '2026-12-01T00:00:00Z' }

  const conventionRows = Array.from({ length: 50 }, (_, i) => ({
    factor_family: 'convention_factor',
    factor_key: `conv_key_${String(i).padStart(3, '0')}`,
    corpus_status: 'computed_uncited_convention' as const,
    ...span,
    source_citation: null,
    detail: {},
  }))

  const dosaRows = Array.from({ length: 10 }, (_, i) => ({
    factor_family: 'kalam',
    factor_key: `rahu_kalam_slot_${i}`,
    corpus_status: 'computed_cited' as const,
    ...span,
    source_citation: 'BPHS ch.47',
    detail: { category: 'inauspicious' },
  }))

  const neutralRows = Array.from({ length: 20 }, (_, i) => ({
    factor_family: 'ghati_muhurta',
    factor_key: `ghati_${i}`,
    corpus_status: 'computed_cited' as const,
    ...span,
    source_citation: 'Muhurta Chintamani ch.2',
    detail: {},
  }))

  return {
    lattice_rows: [...conventionRows, ...dosaRows, ...neutralRows],
    parihara_rules: [],
    census_rows: [],
    lattice_available: true,
    parihara_available: true,
    census_available: true,
    unavailable_reason: null,
  }
}

describe('F-122: kala_elect_get budget trim section coverage gap', () => {
  beforeEach(() => {
    mockHandleMuhurtaFinder.mockReset()
    mockFetchLatticeSubstrate.mockReset()
    mockFetchLatticeSubstrate.mockResolvedValue(makeLargeSubstrate())
  })

  it('honours budget_kb: 32 with sections A–G + setArray sync — FAILS before fix, PASSES after', async () => {
    mockHandleMuhurtaFinder.mockResolvedValue({
      structuredContent: { object: make4WindowResult() },
      content: [{ type: 'text', text: '{}' }],
    })

    const { handleKalaElectGet } = await import('../elect.js')
    // Repro params verbatim from DIAGNOSIS §1, except budget_kb — see the module doc-comment
    // above ("`budget_kb` RETUNED 20 -> 32") for why.
    const out = await handleKalaElectGet(
      {
        chart_id: '482012f1-710e-4a25-994a-93821f5871aa',
        undertaking: 'business',
        date_range: { start: '2026-08-15', end: '2026-11-12' },
        limit: 4,
        native_janma_nakshatra: 'Purva Bhadrapada',
        budget_kb: 32,
      },
      PRINCIPAL,
    )
    const result = out.response!

    // PRIMARY — FAILS today (flag fires verbatim per DIAGNOSIS §1.C)
    // `?? []` handles the after-fix case where judgment_flags is absent entirely
    // (finalizeMcpBudget only adds it when the ceiling is still exceeded after trim).
    expect(
      ((result as unknown as Record<string, unknown[]>)['judgment_flags']?.map(
        (f: unknown) => (f as Record<string, unknown>)['code'],
      ) ?? [])
    ).not.toContain('budget_exceeded_after_trim')

    // Budget actually honoured
    const sizeKb = Buffer.byteLength(JSON.stringify(result), 'utf8') / 1024
    expect(sizeKb).toBeLessThanOrEqual(32)

    // hardFloor still respected (was correct before; must stay correct)
    expect(result.candidates.length).toBeGreaterThanOrEqual(1)

    // lattice_adjudication.ledgers bounded to surviving candidates (was 4 vs 1 — DIAGNOSIS §1.B)
    expect(result.lattice_adjudication?.ledgers.length ?? 0).toBeLessThanOrEqual(result.candidates.length)

    // hora_ladder trimmed (was 15 on a budget-exceeded response — DIAGNOSIS §1.B)
    expect(result.candidates[0]?.hora_ladder?.length ?? 0).toBeLessThan(15)

    // Independent-review follow-up: the one surviving candidate's OWN judgment_ledger is
    // genuinely un-emptied by the lattice_adjudication.ledgers[] bookkeeping trim above —
    // the dedicated regression for the aliasing bug lives in
    // elect_ledger_alias_f122.test.ts, but this exit test's own surviving candidate is a
    // second, real-world-shaped witness: 10 dosas_present / 10 residual_dosas (no muhūrta
    // parihāra rules in this fixture) / 20 neutral_annotations, none of it zeroed.
    const survivorLedger = result.candidates[0]?.judgment_ledger
    expect(survivorLedger).not.toBeNull()
    expect(survivorLedger?.dosas_present.length).toBe(10)
    expect(survivorLedger?.residual_dosas.length).toBe(10)
    expect(survivorLedger?.neutral_annotations.length).toBe(20)
  })
})
