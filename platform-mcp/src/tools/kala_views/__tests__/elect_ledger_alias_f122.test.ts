/**
 * F-122 follow-up regression test — judgment_ledger aliasing (independent-review fix).
 *
 * PROVES: `candidates[i].judgment_ledger` and `lattice_adjudication.ledgers[j]` are
 * INDEPENDENT objects for the same candidate — not the same aliased reference.
 *
 * Before the fix: `ledgerById` (elect.ts) mapped `candidate_id -> l` directly from
 * `adjudication.ledgers`, so `candidates[i].judgment_ledger === lattice_adjudication
 * .ledgers[j]` for matching ids. The budget-trim sections declared in
 * `buildElectSections()` (D/E/G: `lattice_adjudication.ledgers[].dosas_present` /
 * `.residual_dosas` / `.pariharas_applied`) are `minKeep: 0`, NOT `hardFloor`, and are
 * deliberately meant to be eaten BEFORE the `candidates` section (the sole `hardFloor:
 * true` section) is ever touched. With the alias, trimming those "bookkeeping" arrays
 * through `lattice_adjudication.ledgers[]` silently emptied the SAME fields on a
 * SURVIVING candidate's own `judgment_ledger` too — the exact "densest, most-actionable
 * layer" `hardFloor` exists to protect, emptied by a section that was never supposed to
 * touch it.
 *
 * This test builds a response with 2 surviving candidates and a large enough
 * `dosas_present`/`residual_dosas`/`pariharas_applied` payload that the trimmer must cut
 * the bookkeeping-tier `lattice_adjudication.ledgers[]` sections to close the budget gap,
 * while `budget_kb` is generous enough that the `candidates` array itself is never
 * shortened (2 candidates survive throughout). It then asserts BOTH surviving candidates'
 * `judgment_ledger.dosas_present` / `.residual_dosas` / `.pariharas_applied` still carry
 * their full, un-emptied content — i.e. the bookkeeping-tier trim did NOT reach through to
 * the candidate's own protected copy.
 *
 * Before the fix (aliased objects): this test FAILS — the surviving candidates'
 * judgment_ledger fields come back empty once `lattice_adjudication.ledgers[]` is trimmed.
 * After the fix (independent clones): this test PASSES.
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

/** 2 candidate windows — small hora_ladder each, so the ladder isn't what forces the trim. */
function make2WindowResult() {
  const windows = [
    { start: '2026-08-15T00:00:00Z', end: '2026-08-17T00:00:00Z', date: '2026-08-15', score: 0.85 },
    { start: '2026-08-22T00:00:00Z', end: '2026-08-24T00:00:00Z', date: '2026-08-22', score: 0.75 },
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
      hora_ladder: Array.from({ length: 3 }, (_, i) => ({
        start_ist: `${w.date}T${String(6 + i).padStart(2, '0')}:00:00+05:30`,
        end_ist: `${w.date}T${String(7 + i).padStart(2, '0')}:00:00+05:30`,
        hora_lord: ['Sun', 'Venus', 'Mercury'][i % 3],
        benefic: i % 2 === 0,
      })),
    })),
    window_count: 2,
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
 * Substrate whose rows overlap BOTH candidate windows and carry enough doṣa/residual/
 * parihāra content to force the bookkeeping-tier `lattice_adjudication.ledgers[]`
 * sections to trim — without forcing the `candidates` array itself to shrink.
 *
 * 25 dosa rows (inauspicious, no matching parihāra rule) -> dosas_present + residual_dosas
 * per ledger (sections D/E). 5 muhūrta-scope parihāra rules matching a subset of dosha
 * keys -> pariharas_applied per ledger (section G) genuinely non-empty too.
 */
function makeLargeSubstrate() {
  const span = { start_utc: '2026-08-01T00:00:00Z', end_utc: '2026-12-01T00:00:00Z' }

  const dosaRows = Array.from({ length: 25 }, (_, i) => ({
    factor_family: 'kalam',
    factor_key: `dosha_key_${i}`,
    corpus_status: 'computed_cited' as const,
    ...span,
    source_citation: 'BPHS ch.47',
    detail: { category: 'inauspicious' },
  }))

  // Muhūrta-scope parihāra rules for the first 5 dosha keys — genuinely exercises
  // pariharas_applied (section G) rather than leaving it permanently empty.
  const pariharaRules = Array.from({ length: 5 }, (_, i) => ({
    scope: 'muhurta' as const,
    dosha_canonical_id: `dosha_key_${i}`,
    dosha_name_en: `Test Doṣa ${i}`,
    cancellation_condition_text: 'test cancellation condition',
    net_standing: 'cancelled',
    source_citation: 'Test Parihara Corpus',
    extraction_context: null,
  }))

  return {
    lattice_rows: dosaRows,
    parihara_rules: pariharaRules,
    census_rows: [],
    lattice_available: true,
    parihara_available: true,
    census_available: true,
    unavailable_reason: null,
  }
}

describe('F-122 follow-up: judgment_ledger aliasing fix (independent-review finding)', () => {
  beforeEach(() => {
    mockHandleMuhurtaFinder.mockReset()
    mockFetchLatticeSubstrate.mockReset()
    mockFetchLatticeSubstrate.mockResolvedValue(makeLargeSubstrate())
  })

  it('a budget trim that empties lattice_adjudication.ledgers[] bookkeeping arrays does NOT empty a surviving candidate\'s own judgment_ledger', async () => {
    mockHandleMuhurtaFinder.mockResolvedValue({
      structuredContent: { object: make2WindowResult() },
      content: [{ type: 'text', text: '{}' }],
    })

    const { handleKalaElectGet } = await import('../elect.js')
    const out = await handleKalaElectGet(
      {
        chart_id: CHART_ID,
        undertaking: 'business',
        date_range: { start: '2026-08-15', end: '2026-11-12' },
        limit: 2,
        native_janma_nakshatra: 'Purva Bhadrapada',
        budget_kb: 34,
      },
      PRINCIPAL,
    )
    const result = out.response!

    // Sanity: both candidates survived (this test is about a SURVIVING candidate's ledger,
    // not about the candidates-array hardFloor mechanism itself — that's covered by
    // elect_budget_trim_f122.test.ts). If this assertion ever starts failing because the
    // fixture's sizing no longer forces this shape, the fixture — not the assertion below
    // — needs retuning; the aliasing property below is only meaningful for a genuine
    // survivor whose ledger has real content pre-trim.
    expect(result.candidates.length).toBe(2)

    // Sanity: a trim actually happened, and it actually reached lattice_adjudication's
    // bookkeeping ledgers — checked by the ledgers' OWN post-trim total, not by scraping
    // `trim_report` entries (which `finalizeMcpBudget` may itself collapse to a one-line
    // placeholder under extra budget pressure — an orthogonal, legitimate degrade path
    // this test must not depend on the absence/presence of). 25 dosas per candidate x 2
    // candidates = 50 pre-trim; a genuine bookkeeping-tier trim must reduce that total.
    const totalAdjDosas = (result.lattice_adjudication?.ledgers ?? []).reduce(
      (n, l) => n + l.dosas_present.length,
      0,
    )
    expect(totalAdjDosas, 'lattice_adjudication.ledgers[].dosas_present must actually have been trimmed for this test to be meaningful').toBeLessThan(50)

    // THE CORE ASSERTION: every surviving candidate's OWN judgment_ledger still carries
    // its full pre-trim content. Pre-fix (aliased objects), these arrays come back EMPTY
    // (or reduced) here — the exact defect an independent Opus review caught: the PR's own
    // budget-trim sections silently emptied the surviving candidate's protected ledger
    // through the aliased lattice_adjudication.ledgers[] reference.
    for (const candidate of result.candidates) {
      const ledger = candidate.judgment_ledger
      expect(ledger, `candidate ${candidate.start} must carry a judgment_ledger`).not.toBeNull()
      expect(
        ledger!.dosas_present.length,
        `candidate ${candidate.start} judgment_ledger.dosas_present must not be emptied by the lattice_adjudication.ledgers[] bookkeeping trim`,
      ).toBe(25)
      expect(
        ledger!.residual_dosas.length,
        `candidate ${candidate.start} judgment_ledger.residual_dosas must not be emptied by the lattice_adjudication.ledgers[] bookkeeping trim`,
      ).toBe(20) // 25 dosas - 5 with a matching parihara rule = 20 residual
      expect(
        ledger!.pariharas_applied.length,
        `candidate ${candidate.start} judgment_ledger.pariharas_applied must not be emptied by the lattice_adjudication.ledgers[] bookkeeping trim`,
      ).toBe(5)
    }

    // And the object identity itself must be independent — never the same reference as
    // the (now bookkeeping-trimmed) lattice_adjudication.ledgers[] entry for that
    // candidate. This is the direct, structural proof of the fix (not just an
    // array-length proxy for it). Deliberately UNCONDITIONAL (independent-review nit):
    // an earlier version of this test wrapped these two assertions in
    // `if (adjLedger) { ... }`, which would silently SKIP the identity proof (rather than
    // fail) if a future change ever dropped a surviving candidate's ledger from
    // `lattice_adjudication.ledgers[]` — exactly the kind of quietly-vanishing assertion
    // this whole test exists to avoid. `toBeDefined()` below makes that condition a loud
    // failure instead.
    for (const candidate of result.candidates) {
      const adjLedger = result.lattice_adjudication?.ledgers.find(
        (l) => l.candidate_id === candidate.judgment_ledger?.candidate_id,
      )
      expect(adjLedger, `candidate ${candidate.start} must have a corresponding lattice_adjudication.ledgers[] entry for this identity check to be meaningful`).toBeDefined()
      expect(candidate.judgment_ledger).not.toBe(adjLedger)
      expect(candidate.judgment_ledger?.dosas_present).not.toBe(adjLedger!.dosas_present)
    }
  })
})
