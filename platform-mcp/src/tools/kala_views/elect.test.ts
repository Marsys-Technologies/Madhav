/**
 * elect.test.ts — ṢAḌ-DARŚANA v2 W0.4 kala_elect_get facade.
 * Covers: the argument-shaped reading composed from muhurta_finder windows, honest
 * coverage for the not-yet-built W3/W4 election-doctrine items, and the Mode-3 role
 * (ELECT answers an undertaking-shaped call — the routing redirect itself is a separate
 * lane's `kala_ritual_get`, not tested here).
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { isNoLever } from '../../lib/kala_envelope.js'

const mockHandleMuhurtaFinder = vi.fn()

vi.mock('../muhurta_finder.js', async () => {
  const actual = await vi.importActual<typeof import('../muhurta_finder.js')>('../muhurta_finder.js')
  return {
    ...actual,
    handleMuhurtaFinder: (...args: unknown[]) => mockHandleMuhurtaFinder(...args),
  }
})

// Item 36 (W3): the lattice ENGINE stays REAL in these tests — only its I/O adapter is
// mocked. That is deliberate: the adjudication, Pareto and gap-report logic under test here
// is the same code the engine's own unit suite exercises, so the facade tests prove the
// WIRING (ledger attachment, coverage derivation, density fields) against real engine output
// rather than against a hand-written stand-in that could drift from it.
const mockFetchLatticeSubstrate = vi.fn()

vi.mock('../../lib/kala_lattice_query.js', async () => {
  const actual = await vi.importActual<typeof import('../../lib/kala_lattice_query.js')>('../../lib/kala_lattice_query.js')
  return {
    ...actual,
    fetchLatticeSubstrate: (...args: unknown[]) => mockFetchLatticeSubstrate(...args),
  }
})

/** An empty-but-available substrate: the default for the pre-existing tests, which are not
 *  about the lattice and must not depend on a live platform primitive. */
function emptySubstrate() {
  return {
    lattice_rows: [], parihara_rules: [], census_rows: [],
    lattice_available: true, parihara_available: true, census_available: true,
    unavailable_reason: null,
  }
}

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const PRINCIPAL = { user_uid: 'u1', key_id: 'k1', role: 'guest' as const }

function muhurtaResult(overrides: Partial<Record<string, unknown>> = {}) {
  return {
    ok: true,
    chart_id: CHART_ID,
    action_type: 'business',
    query_window: { start: '2026-08-01', end: '2026-10-30' },
    windows: [
      {
        start: '2026-08-05T00:00:00Z',
        end: '2026-08-07T00:00:00Z',
        score: 0.82,
        factors: {
          panchanga_quality: 0.7, dasha_quality: 0.8, transit_quality: 0.6, signal_activation: 0.5,
          panchanga_details: { tithi_name: 'Tritiya', vara_lord: 'Guru', moon_nakshatra: 'Pushya', yoga: 'Siddha', inauspicious_windows: [] },
          dasha_details: { md_lord: 'Mercury', ad_lord: 'Venus' },
          avoid_notes: [],
        },
        source_citation: 'BPHS ch.46',
        hard_flag: false,
        disqualified: false,
        rank_penalty_reason: [],
        hora_ladder: [
          { start_ist: '2026-08-05T06:00:00+05:30', end_ist: '2026-08-05T07:00:00+05:30', hora_lord: 'Mercury', benefic: true },
          { start_ist: '2026-08-05T07:00:00+05:30', end_ist: '2026-08-05T08:00:00+05:30', hora_lord: 'Moon', benefic: true },
        ],
      },
      {
        start: '2026-08-12T00:00:00Z',
        end: '2026-08-14T00:00:00Z',
        score: 0.55,
        factors: {
          panchanga_quality: 0.4, dasha_quality: 0.5, transit_quality: 0.5, signal_activation: 0.4,
          panchanga_details: { tithi_name: 'Dashami', vara_lord: 'Shani', moon_nakshatra: 'Ashwini', yoga: 'Vyatipata', inauspicious_windows: [] },
          dasha_details: { md_lord: 'Mercury', ad_lord: 'Venus' },
          avoid_notes: [],
        },
        source_citation: 'BPHS ch.46',
        hard_flag: true,
        disqualified: true,
        rank_penalty_reason: ['Vadha-tara for native star'],
        tara_bala: {
          janma_nakshatra: 'Purva Bhadrapada', day_nakshatra: 'Ashwini', count_from_janma: 3, tara_index: 3,
          tara_name: 'Vipat', favorable: false, adverse: true, severity: 'severe', citation: 'Muhurta Chintamani',
        },
        hora_ladder: [
          { start_ist: '2026-08-12T06:00:00+05:30', end_ist: '2026-08-12T07:00:00+05:30', hora_lord: 'Saturn', benefic: false },
          { start_ist: '2026-08-12T07:00:00+05:30', end_ist: '2026-08-12T08:00:00+05:30', hora_lord: 'Jupiter', benefic: true },
        ],
      },
    ],
    window_count: 2,
    provenance_envelope: {
      source: 'phala.muhurta', asset: 'PH-4-4', algorithm: 'x', min_score_applied: 0,
      chart_id: CHART_ID, action_type: 'business', queried_at: '2026-07-29T00:00:00Z',
      l1_ground_truth: 'FORENSIC', b3_citation_compliant: true,
    },
    lane_f: {
      tara_bala_status: 'applied' as const,
      hora_status: 'applied' as const,
      hora_sunrise_assumption: 'x',
      ranking_note: 'x',
      target_graha_status: 'not_requested' as const,
    },
    ...overrides,
  }
}

describe('handleKalaElectGet', () => {
  beforeEach(() => {
    mockHandleMuhurtaFinder.mockReset()
    mockFetchLatticeSubstrate.mockReset()
    mockFetchLatticeSubstrate.mockResolvedValue(emptySubstrate())
  })

  it('composes an argument reading with a live top candidate and a hard-vetoed dissent row', async () => {
    mockHandleMuhurtaFinder.mockResolvedValue({
      structuredContent: { object: muhurtaResult() },
      content: [{ type: 'text', text: '{}' }],
    })

    const { handleKalaElectGet } = await import('./elect.js')
    const { response, error } = await handleKalaElectGet(
      { chart_id: CHART_ID, undertaking: 'business', limit: 5 },
      PRINCIPAL,
    )

    expect(error).toBeUndefined()
    expect(response).toBeDefined()
    expect(response!.tool).toBe('kala_elect_get')
    expect(response!.candidate_count).toBe(2)
    expect(response!.reading.thesis).toContain('2026-08-05')
    // The disqualified window surfaces as dissent, not silently dropped.
    expect(response!.reading.dissent.length).toBeGreaterThan(0)
    expect(response!.reading.dissent[0]!.source).toContain('tara_bala')
    expect(response!.reading.verdict.tier).toBe('structural_prior')
    expect(response!.reading.falsifier?.resolves_by).toBe('2026-08-07')
    // ELECT is itself the intervention plane — self-pointer is null, not omitted.
    // ND-1 (ṢAḌ-DARŚANA W1 verify-reopen, 2026-07-30): the bare-null contract this assertion
    // encoded is retired — every tri_plane slot is now either a real pointer or an honest,
    // self-describing `no_lever`. See tools/kala_views/ahead.ts's prediction_ref for the
    // rationale (the campaign's own tri_plane_no_dead_end_gate.ts grades a bare null WARN).
    expect(isNoLever(response!.tri_plane.intervention_ref!)).toBe(true)
    // Honest W0 gap coverage present.
    const conceptNames = response!.coverage.map((c) => c.concept)
    expect(conceptNames).toContain('contender_lattice_parihara_adjudication')
    expect(conceptNames).toContain('ritual_pairing')
    // Item 38-lite grading + frontier v0 coverage present.
    expect(conceptNames).toContain('candidate_grading_lite')
    expect(conceptNames).toContain('elect_frontier_v0')
  })

  describe('item 38-lite grading + ELECT frontier v0', () => {
    it('labels the live top candidate gold and the hard-vetoed candidate disqualified', async () => {
      mockHandleMuhurtaFinder.mockResolvedValue({
        structuredContent: { object: muhurtaResult() },
        content: [{ type: 'text', text: '{}' }],
      })

      const { handleKalaElectGet } = await import('./elect.js')
      const { response } = await handleKalaElectGet({ chart_id: CHART_ID, undertaking: 'business' }, PRINCIPAL)

      expect(response!.candidates[0]!.grading_tier).toBe('gold') // score 0.82, not disqualified
      expect(response!.candidates[1]!.grading_tier).toBe('disqualified') // hard-vetoed, regardless of its 0.55 score
      expect(response!.candidates[1]!.grading_tier_label).toContain('Disqualified')
    })

    it('reports a frontier statement naming the best live candidate and gold-tier presence', async () => {
      mockHandleMuhurtaFinder.mockResolvedValue({
        structuredContent: { object: muhurtaResult() },
        content: [{ type: 'text', text: '{}' }],
      })

      const { handleKalaElectGet } = await import('./elect.js')
      const { response } = await handleKalaElectGet({ chart_id: CHART_ID, undertaking: 'business' }, PRINCIPAL)

      expect(response!.frontier.candidate_count).toBe(1) // only the non-disqualified window counts as "live"
      expect(response!.frontier.gold_tier_present).toBe(true)
      expect(response!.frontier.best?.start).toBe('2026-08-05T00:00:00Z')
      expect(response!.frontier.statement).toContain('2026-08-05')
    })

    it('reports an honest empty frontier (never a fabricated next-occurrence date) when no windows are computed', async () => {
      mockHandleMuhurtaFinder.mockResolvedValue({
        structuredContent: { object: muhurtaResult({ windows: [], window_count: 0, empty_reason: 'date_range outside populated panchanga horizon' }) },
        content: [{ type: 'text', text: '{}' }],
      })

      const { handleKalaElectGet } = await import('./elect.js')
      const { response } = await handleKalaElectGet({ chart_id: CHART_ID, undertaking: 'business' }, PRINCIPAL)

      expect(response!.frontier.candidate_count).toBe(0)
      expect(response!.frontier.best).toBeNull()
      expect(response!.frontier.statement).toContain('date_range outside populated panchanga horizon')
    })

    it('reports an honest no-gold-tier frontier when every live candidate is below the gold threshold', async () => {
      const noGold = muhurtaResult()
      ;(noGold.windows as Record<string, unknown>[])[0]!['score'] = 0.6
      mockHandleMuhurtaFinder.mockResolvedValue({
        structuredContent: { object: noGold },
        content: [{ type: 'text', text: '{}' }],
      })

      const { handleKalaElectGet } = await import('./elect.js')
      const { response } = await handleKalaElectGet({ chart_id: CHART_ID, undertaking: 'business' }, PRINCIPAL)

      expect(response!.frontier.gold_tier_present).toBe(false)
      expect(response!.frontier.best_tier).toBe('silver')
      expect(response!.frontier.statement).toContain('none reaching gold tier')
    })
  })

  it('reports an honest gap when every candidate is disqualified', async () => {
    const allVetoed = muhurtaResult()
    ;(allVetoed.windows as Record<string, unknown>[])[0]!['disqualified'] = true
    mockHandleMuhurtaFinder.mockResolvedValue({
      structuredContent: { object: allVetoed },
      content: [{ type: 'text', text: '{}' }],
    })

    const { handleKalaElectGet } = await import('./elect.js')
    const { response } = await handleKalaElectGet({ chart_id: CHART_ID, undertaking: 'business' }, PRINCIPAL)

    expect(response!.gap_report).not.toBeNull()
    expect(response!.reading.thesis).toContain('hard veto')
  })

  it('reports an honest empty when no windows are computed', async () => {
    mockHandleMuhurtaFinder.mockResolvedValue({
      structuredContent: { object: muhurtaResult({ windows: [], window_count: 0, empty_reason: 'date_range outside populated panchanga horizon' }) },
      content: [{ type: 'text', text: '{}' }],
    })

    const { handleKalaElectGet } = await import('./elect.js')
    const { response } = await handleKalaElectGet({ chart_id: CHART_ID, undertaking: 'business' }, PRINCIPAL)

    expect(response!.candidate_count).toBe(0)
    expect(response!.gap_report).toContain('outside populated panchanga horizon')
    expect(response!.reading.falsifier).toBeNull()
  })

  it('propagates an honest error on AUTHZ_DENIED (no structuredContent on that branch)', async () => {
    mockHandleMuhurtaFinder.mockResolvedValue({
      content: [{ type: 'text', text: 'AUTHZ_DENIED: not authorized to access this chart' }],
      isError: true,
    })

    const { handleKalaElectGet } = await import('./elect.js')
    const { response, error } = await handleKalaElectGet({ chart_id: CHART_ID, undertaking: 'business' }, PRINCIPAL)

    expect(response).toBeUndefined()
    expect(error?.message).toContain('AUTHZ_DENIED')
  })

  describe('coverage honesty — hora_ladder (PARĪKṢAKA live-production regression, defect 1)', () => {
    // Reproduces the exact live-production defect: coverage claimed
    // { concept: 'hora_ladder', state: 'computed' } while no candidate object anywhere in the
    // response carried a `hora_ladder` field, even though muhurta_finder.ts's
    // enrichWindowsLaneF genuinely computes one per window (~line 776). Fails on pre-fix code
    // because `KalaElectCandidate` never projected the field.
    it('never claims hora_ladder computed while withholding it from every served candidate', async () => {
      mockHandleMuhurtaFinder.mockResolvedValue({
        structuredContent: { object: muhurtaResult() },
        content: [{ type: 'text', text: '{}' }],
      })

      const { handleKalaElectGet } = await import('./elect.js')
      const { response } = await handleKalaElectGet({ chart_id: CHART_ID, undertaking: 'business' }, PRINCIPAL)

      const horaCoverage = response!.coverage.find((c) => c.concept === 'hora_ladder')
      expect(horaCoverage?.state).toBe('computed')
      // The honesty invariant this regression protects: if coverage says `computed`, the
      // payload must actually exist somewhere in the response — not just upstream.
      expect(response!.candidates.length).toBeGreaterThan(0)
      for (const c of response!.candidates) {
        expect(Array.isArray(c.hora_ladder)).toBe(true)
        expect(c.hora_ladder.length).toBeGreaterThan(0)
      }
    })

    it('falls back to honest_empty (never a bare unbacked "computed") when no window carries a ladder', async () => {
      const noLadders = muhurtaResult()
      for (const w of noLadders.windows as Record<string, unknown>[]) {
        delete w['hora_ladder']
      }
      mockHandleMuhurtaFinder.mockResolvedValue({
        structuredContent: { object: noLadders },
        content: [{ type: 'text', text: '{}' }],
      })

      const { handleKalaElectGet } = await import('./elect.js')
      const { response } = await handleKalaElectGet({ chart_id: CHART_ID, undertaking: 'business' }, PRINCIPAL)

      const horaCoverage = response!.coverage.find((c) => c.concept === 'hora_ladder')
      expect(horaCoverage?.state).toBe('honest_empty')
      expect(horaCoverage?.reason?.length).toBeGreaterThan(0)
      for (const c of response!.candidates) {
        expect(c.hora_ladder).toEqual([])
      }
    })
  })

  // ── Item 36 (W3): contender lattice + parihāra adjudication wiring ──────────────
  describe('item 36 — contender lattice + parihāra adjudication', () => {
    const CITED_DOSA = {
      factor_family: 'kalam',
      factor_key: 'rahu_kalam',
      start_utc: '2026-08-05T03:00:00Z',
      end_utc: '2026-08-05T04:30:00Z',
      detail: { category: 'inauspicious' },
      source_citation: 'Drik Panchang published index tables (RAHU_KALAM_INDEX)',
      corpus_status: 'computed_cited' as const,
    }
    const CONVENTION_ROW = {
      ...CITED_DOSA,
      factor_key: 'yamakantaka',
      corpus_status: 'computed_uncited_convention' as const,
    }
    const CENSUS = [
      { factor_family: 'panchangika', factor_name: 'tithi', disposition: 'computed' as const,
        citation_or_gap_note: 'compute_tithi', evidence_pointer: 'angas.py', school_tag: null },
      { factor_family: 'combination_yoga', factor_name: 'mrityu_yoga', disposition: 'not_in_corpus' as const,
        citation_or_gap_note: 'no vara x nakshatra table in the ingested corpus', evidence_pointer: 'n/a', school_tag: null },
    ]

    async function electWith(substrate: Record<string, unknown>) {
      mockHandleMuhurtaFinder.mockResolvedValue({
        structuredContent: { object: muhurtaResult() },
        content: [{ type: 'text', text: '{}' }],
      })
      mockFetchLatticeSubstrate.mockResolvedValue(substrate)
      const { handleKalaElectGet } = await import('./elect.js')
      const { response } = await handleKalaElectGet({ chart_id: CHART_ID, undertaking: 'business' }, PRINCIPAL)
      return response!
    }

    it('attaches a judgment ledger to every candidate and reports residual doṣas uncancelled', async () => {
      const response = await electWith({ ...emptySubstrate(), lattice_rows: [CITED_DOSA], census_rows: CENSUS })

      const ledger = response.candidates[0]!.judgment_ledger
      expect(ledger).not.toBeNull()
      expect(ledger!.dosas_present.map((d) => d.factor_key)).toEqual(['rahu_kalam'])
      // The corpus carries no muhūrta-scope parihāra rule, so nothing is cancelled — and the
      // response says so rather than presenting a clean verdict.
      expect(ledger!.pariharas_applied).toHaveLength(0)
      expect(ledger!.residual_dosas.map((d) => d.factor_key)).toEqual(['rahu_kalam'])
      expect(ledger!.net_standing).toBe('residual_dosas_present')
      const conceptNames = response.coverage.map((c) => c.concept)
      expect(conceptNames).toContain('muhurta_scope_parihara_rules')
      expect(response.coverage.find((c) => c.concept === 'muhurta_scope_parihara_rules')?.state).toBe('not_in_corpus')
    })

    it('never lets an uncited-convention row become a doṣa, and counts it separately', async () => {
      const response = await electWith({
        ...emptySubstrate(), lattice_rows: [CITED_DOSA, CONVENTION_ROW], census_rows: CENSUS,
      })

      const ledger = response.candidates[0]!.judgment_ledger!
      expect(ledger.dosas_present.map((d) => d.factor_key)).toEqual(['rahu_kalam'])
      expect(ledger.convention_only_factor_count).toBe(1)
      expect(ledger.convention_only_keys).toEqual(['yamakantaka'])
      expect(ledger.convention_only_note).toBeTruthy()
      // The two density layers are counted separately at slate level too.
      expect(response.lattice_adjudication!.density.cited_rows_in_horizon).toBe(1)
      expect(response.lattice_adjudication!.density.convention_only_rows_in_horizon).toBe(1)
    })

    it('serves the factor census in coverage and names the corpus gaps in the gap report', async () => {
      const response = await electWith({ ...emptySubstrate(), lattice_rows: [CITED_DOSA], census_rows: CENSUS })

      expect(response.coverage.find((c) => c.concept === 'muhurta_factor_census')?.state).toBe('computed')
      expect(response.lattice_adjudication!.gap_report.factors_not_in_corpus.map((f) => f.factor_name))
        .toEqual(['mrityu_yoga'])
      expect(response.gap_report).toContain('Pareto')
      // The gap report never invents a next-occurrence date.
      expect(response.lattice_adjudication!.gap_report.next_occurrence).toBeNull()
    })

    it('reports honest_empty (never computed) when the lattice substrate cannot be read', async () => {
      const response = await electWith({
        ...emptySubstrate(), lattice_available: false, unavailable_reason: 'query_muhurta_lattice returned status 503',
      })

      const entry = response.coverage.find((c) => c.concept === 'contender_lattice_parihara_adjudication')
      expect(entry?.state).toBe('honest_empty')
      expect(entry?.reason).toContain('503')
      expect(response.candidates[0]!.judgment_ledger!.net_standing).toBe('clean')
    })

    it('claims computed only when cited rows genuinely annotated a candidate', async () => {
      const withRows = await electWith({ ...emptySubstrate(), lattice_rows: [CITED_DOSA], census_rows: CENSUS })
      expect(withRows.coverage.find((c) => c.concept === 'contender_lattice_parihara_adjudication')?.state)
        .toBe('computed')

      const conventionsOnly = await electWith({ ...emptySubstrate(), lattice_rows: [CONVENTION_ROW], census_rows: CENSUS })
      expect(conventionsOnly.coverage.find((c) => c.concept === 'contender_lattice_parihara_adjudication')?.state)
        .toBe('honest_empty')
    })

    it('surfaces the Pareto frontier with the axes it could not evaluate named, not zero-filled', async () => {
      const response = await electWith({ ...emptySubstrate(), lattice_rows: [CITED_DOSA], census_rows: CENSUS })

      const pareto = response.lattice_adjudication!.pareto
      expect(pareto.frontier_candidate_ids.length).toBeGreaterThan(0)
      expect(pareto.axes_excluded.map((a) => a.key)).toContain('personal_field_alignment')
      for (const axis of pareto.axes_excluded) expect(axis.reason.length).toBeGreaterThan(20)
    })

    it('degrades honestly (no throw, null adjudication) when the substrate fetch itself throws', async () => {
      mockHandleMuhurtaFinder.mockResolvedValue({
        structuredContent: { object: muhurtaResult() },
        content: [{ type: 'text', text: '{}' }],
      })
      mockFetchLatticeSubstrate.mockRejectedValue(new Error('network down'))

      const { handleKalaElectGet } = await import('./elect.js')
      const { response, error } = await handleKalaElectGet({ chart_id: CHART_ID, undertaking: 'business' }, PRINCIPAL)

      expect(error).toBeUndefined()
      expect(response!.lattice_adjudication).toBeNull()
      expect(response!.candidates[0]!.judgment_ledger).toBeNull()
      expect(response!.coverage.find((c) => c.concept === 'contender_lattice_parihara_adjudication')?.state)
        .toBe('honest_empty')
      expect(response!.coverage.find((c) => c.concept === 'muhurta_factor_census')?.state).toBe('not_in_corpus')
    })
  })
})
