/**
 * kala_lattice_query.test.ts — ṢAḌ-DARŚANA W3 item 36: the query-time contender
 * lattice + parihāra adjudication engine.
 *
 * These tests are the engine's SPEC. They encode, in order, the five stages of
 * KALA_SUPREME_ELEVATION_v1_0.md §9 that this lane owns at query time — lattice
 * annotation, census-aware density layering, parihāra adjudication, Pareto
 * survival, gap report — plus the three honesty rails the campaign holds this
 * engine to:
 *
 *   1. §N.6 density: `computed_uncited_convention` lattice rows are SERVED but
 *      counted/flagged separately and never become findings or doṣas.
 *   2. DATA-HONESTY: with zero muhūrta-scope parihāra rows in the corpus (the
 *      substrate's actual state), no doṣa is ever silently cancelled — the
 *      ledger reports residuals and names the corpus gap.
 *   3. 3-state coverage: a missing/empty substrate payload yields `honest_empty`
 *      (or `not_in_corpus`), NEVER `computed`.
 */
import { describe, it, expect } from 'vitest'
import {
  adjudicateCandidates,
  type CandidateInterval,
  type FactorCensusRow,
  type LatticeFactorRow,
  type LatticeSubstrate,
  type PariharaRuleRow,
} from './kala_lattice_query.js'

// ── Fixtures ────────────────────────────────────────────────────────────────
// Shapes mirror the real substrate columns (migration 484/485) exactly.

function latticeRow(over: Partial<LatticeFactorRow> = {}): LatticeFactorRow {
  return {
    factor_family: 'kalam',
    factor_key: 'rahu_kalam',
    start_utc: '2026-08-05T03:00:00Z',
    end_utc: '2026-08-05T04:30:00Z',
    detail: { category: 'inauspicious' },
    source_citation: 'Drik Panchang published index tables (RAHU_KALAM_INDEX)',
    corpus_status: 'computed_cited',
    ...over,
  }
}

function censusRow(over: Partial<FactorCensusRow> = {}): FactorCensusRow {
  return {
    factor_family: 'panchangika',
    factor_name: 'tithi',
    disposition: 'computed',
    citation_or_gap_note: 'panchang_engine.angas.compute_tithi',
    evidence_pointer: 'panchang_engine/angas.py:compute_tithi',
    school_tag: null,
    ...over,
  }
}

const CANDIDATE_A: CandidateInterval = {
  id: 'w1', start: '2026-08-05T00:00:00Z', end: '2026-08-06T00:00:00Z', score: 0.82, disqualified: false,
}
const CANDIDATE_B: CandidateInterval = {
  id: 'w2', start: '2026-08-12T00:00:00Z', end: '2026-08-13T00:00:00Z', score: 0.55, disqualified: false,
}

function substrate(over: Partial<LatticeSubstrate> = {}): LatticeSubstrate {
  return {
    lattice_available: true,
    parihara_available: true,
    census_available: true,
    lattice_rows: [],
    parihara_rules: [],
    census_rows: [censusRow()],
    unavailable_reason: null,
    ...over,
  }
}

// ── Stage 1: lattice annotation ─────────────────────────────────────────────

describe('stage 1 — lattice annotation (overlap is exact, not sampled)', () => {
  it('annotates a candidate with every cited lattice row overlapping its interval', () => {
    const out = adjudicateCandidates([CANDIDATE_A], substrate({
      lattice_rows: [
        latticeRow(),                                                       // inside A
        latticeRow({ factor_key: 'abhijit', detail: { category: 'auspicious' } }),
        latticeRow({ factor_key: 'rahu_kalam', start_utc: '2026-09-01T03:00:00Z', end_utc: '2026-09-01T04:30:00Z' }), // outside A
      ],
    }))
    const ledger = out.ledgers[0]!
    expect(ledger.candidate_id).toBe('w1')
    expect(ledger.dosas_present.map((d) => d.factor_key)).toEqual(['rahu_kalam'])
    expect(ledger.supporting_factors.map((s) => s.factor_key)).toEqual(['abhijit'])
  })

  it('treats a row that merely touches the boundary as non-overlapping (half-open interval)', () => {
    const out = adjudicateCandidates([CANDIDATE_A], substrate({
      lattice_rows: [latticeRow({ start_utc: '2026-08-06T00:00:00Z', end_utc: '2026-08-06T01:00:00Z' })],
    }))
    expect(out.ledgers[0]!.dosas_present).toHaveLength(0)
  })

  it('derives polarity ONLY from the row\'s own detail — a family with no polarity is a neutral annotation', () => {
    const out = adjudicateCandidates([CANDIDATE_A], substrate({
      lattice_rows: [
        latticeRow({ factor_family: 'agnivasa', factor_key: 'agni_vasa', detail: { element: 'Jala' } }),
        latticeRow({ factor_family: 'ghati_muhurta', factor_key: '1:Rudra', detail: { number: 1, period: 'day' } }),
      ],
    }))
    const ledger = out.ledgers[0]!
    expect(ledger.dosas_present).toHaveLength(0)
    expect(ledger.supporting_factors).toHaveLength(0)
    expect(ledger.neutral_annotations.map((n) => n.factor_key)).toEqual(['agni_vasa', '1:Rudra'])
  })
})

// ── §N.6 density layering ───────────────────────────────────────────────────

describe('§N.6 density — convention rows are served, counted separately, never findings', () => {
  it('never promotes a computed_uncited_convention row to a doṣa or a supporting factor', () => {
    const out = adjudicateCandidates([CANDIDATE_A], substrate({
      lattice_rows: [
        latticeRow({ factor_key: 'yamakantaka', corpus_status: 'computed_uncited_convention' }),
        latticeRow({ factor_key: 'visha_ghati', corpus_status: 'computed_uncited_convention' }),
        latticeRow(),  // the one genuinely cited row
      ],
    }))
    const ledger = out.ledgers[0]!
    expect(ledger.dosas_present.map((d) => d.factor_key)).toEqual(['rahu_kalam'])
    expect(ledger.convention_only_factor_count).toBe(2)
    expect(ledger.convention_only_keys).toEqual(['visha_ghati', 'yamakantaka'])
    expect(ledger.convention_only_note).toMatch(/not cited classical findings/i)
    // The rows are still SERVED — B.10 forbids silently dropping them.
    expect(ledger.convention_only_factors.map((f) => f.factor_key)).toEqual(['visha_ghati', 'yamakantaka'])
  })

  it('reports zero convention rows honestly (null note, not a fabricated caveat)', () => {
    const out = adjudicateCandidates([CANDIDATE_A], substrate({ lattice_rows: [latticeRow()] }))
    expect(out.ledgers[0]!.convention_only_factor_count).toBe(0)
    expect(out.ledgers[0]!.convention_only_note).toBeNull()
  })
})

// ── Stage 3: parihāra adjudication ──────────────────────────────────────────

describe('stage 3 — parihāra adjudication (juridical, never additive)', () => {
  it('leaves every doṣa residual when the corpus carries no muhūrta-scope cancellation rule', () => {
    const natalOnly: PariharaRuleRow[] = [{
      dosha_canonical_id: 'manglik_dosha',
      dosha_name_en: 'Manglik Dosha',
      dosha_category: 'relationship',
      cancellation_index: 1,
      cancellation_condition_text: 'Mars in own sign cancels',
      net_standing: 'cancellable_by_condition',
      scope: 'natal',
      source_text_id: 'bphs',
      source_chapter: 80,
      source_citation: 'Brihat Parasara Hora Sastra (bphs), ch.80',
    }]
    const out = adjudicateCandidates([CANDIDATE_A], substrate({
      lattice_rows: [latticeRow()],
      parihara_rules: natalOnly,
    }))
    const ledger = out.ledgers[0]!
    expect(ledger.pariharas_applied).toHaveLength(0)
    expect(ledger.residual_dosas.map((d) => d.factor_key)).toEqual(['rahu_kalam'])
    expect(ledger.net_standing).toBe('residual_dosas_present')
    expect(ledger.adjudication_note).toMatch(/no muhūrta-scope/i)
    expect(out.gap_report.parihara_corpus_gap).toMatch(/no muhūrta-scope/i)
  })

  it('applies a muhūrta-scope rule when one genuinely exists, and cites it', () => {
    const rescue: PariharaRuleRow[] = [{
      dosha_canonical_id: 'rahu_kalam',
      dosha_name_en: 'Rāhu-kālam',
      dosha_category: 'muhurta',
      cancellation_index: 1,
      cancellation_condition_text: 'Abhijit muhūrta overrides the day-part doṣa for a midday saṅkalpa',
      net_standing: 'cancellable_by_condition',
      scope: 'muhurta',
      source_text_id: 'muhurta_chintamani',
      source_chapter: 5,
      source_citation: 'Muhurta Chintamani (muhurta_chintamani), ch.5',
    }]
    const out = adjudicateCandidates([CANDIDATE_A], substrate({
      lattice_rows: [latticeRow()],
      parihara_rules: rescue,
    }))
    const ledger = out.ledgers[0]!
    expect(ledger.pariharas_applied).toHaveLength(1)
    expect(ledger.pariharas_applied[0]!.dosha_key).toBe('rahu_kalam')
    expect(ledger.pariharas_applied[0]!.source_citation).toContain('Muhurta Chintamani')
    expect(ledger.residual_dosas).toHaveLength(0)
    expect(ledger.net_standing).toBe('fully_cancelled')
  })

  it('marks a doṣa-free candidate clean', () => {
    const out = adjudicateCandidates([CANDIDATE_A], substrate({
      lattice_rows: [latticeRow({ factor_key: 'abhijit', detail: { category: 'auspicious' } })],
    }))
    expect(out.ledgers[0]!.net_standing).toBe('clean')
  })

  it('does not adjudicate at all when the parihāra payload is unavailable', () => {
    const out = adjudicateCandidates([CANDIDATE_A], substrate({
      lattice_rows: [latticeRow()],
      parihara_available: false,
    }))
    expect(out.ledgers[0]!.net_standing).toBe('not_adjudicated')
    expect(out.ledgers[0]!.residual_dosas).toHaveLength(0)
  })
})

// ── Stage 4: Pareto survival ────────────────────────────────────────────────

describe('stage 4 — Pareto survival across factor groups', () => {
  it('keeps a candidate that is weaker on score but carries no residual doṣa', () => {
    const out = adjudicateCandidates([CANDIDATE_A, CANDIDATE_B], substrate({
      lattice_rows: [
        latticeRow(),                                        // doṣa on A
        latticeRow({ factor_key: 'abhijit', detail: { category: 'auspicious' },
                     start_utc: '2026-08-12T06:00:00Z', end_utc: '2026-08-12T07:00:00Z' }), // support on B
      ],
    }))
    expect(out.pareto.frontier_candidate_ids.sort()).toEqual(['w1', 'w2'])
  })

  it('drops a candidate dominated on every available axis', () => {
    const worse: CandidateInterval = { ...CANDIDATE_B, score: 0.2 }
    const out = adjudicateCandidates([CANDIDATE_A, worse], substrate({ lattice_rows: [] }))
    expect(out.pareto.frontier_candidate_ids).toEqual(['w1'])
    expect(out.pareto.dominated_candidate_ids).toEqual(['w2'])
  })

  it('discloses the axes it could NOT evaluate rather than scoring them as zero', () => {
    const out = adjudicateCandidates([CANDIDATE_A], substrate())
    const excludedKeys = out.pareto.axes_excluded.map((a) => a.key)
    expect(excludedKeys).toContain('personal_field_alignment')
    expect(excludedKeys).toContain('rite_specific_resonance')
    expect(excludedKeys).toContain('practical_feasibility')
    for (const axis of out.pareto.axes_excluded) expect(axis.reason.length).toBeGreaterThan(20)
    expect(out.pareto.axes_used).toContain('residual_dosha_burden')
  })
})

// ── Stage 5: gap report + coverage honesty ──────────────────────────────────

describe('stage 5 — gap report and 3-state coverage honesty', () => {
  it('reports honest_empty (never computed) when the lattice horizon has no rows', () => {
    const out = adjudicateCandidates([CANDIDATE_A], substrate({ lattice_rows: [] }))
    expect(out.coverage_state).toBe('honest_empty')
    expect(out.coverage_reason).toMatch(/no lattice factor rows/i)
  })

  it('reports honest_empty when the substrate fetch itself failed', () => {
    const out = adjudicateCandidates([CANDIDATE_A], substrate({
      lattice_available: false, unavailable_reason: 'primitive call returned 503',
    }))
    expect(out.coverage_state).toBe('honest_empty')
    expect(out.coverage_reason).toContain('503')
  })

  it('reports computed only when cited rows actually annotated a candidate', () => {
    const out = adjudicateCandidates([CANDIDATE_A], substrate({ lattice_rows: [latticeRow()] }))
    expect(out.coverage_state).toBe('computed')
  })

  it('does NOT claim computed when the only overlapping rows are conventions', () => {
    const out = adjudicateCandidates([CANDIDATE_A], substrate({
      lattice_rows: [latticeRow({ factor_key: 'visha_ghati', corpus_status: 'computed_uncited_convention' })],
    }))
    expect(out.coverage_state).toBe('honest_empty')
    expect(out.coverage_reason).toMatch(/convention/i)
  })

  it('enumerates the census gaps in the gap report, with reasons', () => {
    const out = adjudicateCandidates([CANDIDATE_A], substrate({
      lattice_rows: [latticeRow()],
      census_rows: [
        censusRow(),
        censusRow({ factor_family: 'combination_yoga', factor_name: 'mrityu_yoga', disposition: 'not_in_corpus', citation_or_gap_note: 'no vara x nakshatra table in the ingested corpus' }),
        censusRow({ factor_family: 'degree_sensitive', factor_name: 'mrityu_bhaga', disposition: 'not_computed', citation_or_gap_note: 'table exists but no per-atom evaluation is built' }),
      ],
    }))
    expect(out.gap_report.factors_not_in_corpus.map((f) => f.factor_name)).toEqual(['mrityu_yoga'])
    expect(out.gap_report.factors_not_computed.map((f) => f.factor_name)).toEqual(['mrityu_bhaga'])
    expect(out.gap_report.census_disposition_counts).toEqual({ computed: 1, not_in_corpus: 1, not_computed: 1 })
  })

  it('never invents a next-occurrence date beyond the horizon', () => {
    const out = adjudicateCandidates([], substrate({ lattice_rows: [latticeRow()] }))
    expect(out.gap_report.statement).toMatch(/not computed at this build tier|no candidate/i)
    expect(out.gap_report.next_occurrence).toBeNull()
  })

  it('marks the census not_in_corpus when the census payload itself is unavailable', () => {
    const out = adjudicateCandidates([CANDIDATE_A], substrate({
      lattice_rows: [latticeRow()], census_available: false, census_rows: [],
    }))
    expect(out.gap_report.census_state).toBe('not_in_corpus')
    expect(out.gap_report.census_disposition_counts).toEqual({})
  })
})

// ── ONE-ENGINE RULE ─────────────────────────────────────────────────────────

describe('ONE-ENGINE RULE — the engine is rite-agnostic', () => {
  it('produces identical ledgers for the same interval regardless of the caller\'s label', () => {
    const s = substrate({ lattice_rows: [latticeRow()] })
    const elect = adjudicateCandidates([CANDIDATE_A], s, { subject_label: 'business (ELECT act-time)' })
    const yajna = adjudicateCandidates([CANDIDATE_A], s, { subject_label: 'graha-śānti yajña (YAJÑA-SETU)' })
    expect(elect.ledgers).toEqual(yajna.ledgers)
    expect(elect.pareto.frontier_candidate_ids).toEqual(yajna.pareto.frontier_candidate_ids)
  })
})
