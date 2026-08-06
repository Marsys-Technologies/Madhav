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

// ── ADJUDICATION-10 — the real seeded Abhijit sarva-doṣaghna row ───────────
//
// SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md ADJUDICATION-10 Part 1 ruled the
// W3 gate criterion ("the Abhijit-override case demonstrably rescues a
// candidate") MET by extracting the ONE muhūrta-scope, universal-cancellation
// rule genuinely present in the corpus: bphs_jaimini PG213, chunk
// bphs_jaimini_pg0213_c01 — "...Abhijit Sarva Doshaghnam or that noon time
// which cuts and cures all evil influences." Verified read-only against
// production `classical_text_chunks` before this test was written (see PR
// body for the verification query + returned content_en).
//
// The fixture below is the ACTUAL row seeded by migration 524 +
// bg_parihara_rules.py's MUHURTA_PARIHARA_ROWS constant — every field is
// transcribed from that source, not invented for this test. This is
// deliberately a DIFFERENT fixture from the "applies a muhūrta-scope rule
// when one genuinely exists" test above (which is a synthetic, hypothetical
// muhurta_chintamani rule illustrating the mechanism in the abstract) — this
// one proves the mechanism against the real, in-corpus row.
const ABHIJIT_PARIHARA_ROW: PariharaRuleRow = {
  dosha_canonical_id: 'rahu_kalam',
  dosha_name_en: 'Rahu Kalam',
  dosha_category: 'muhurta_kalam',
  cancellation_index: 1,
  cancellation_condition_text:
    '...the time goes under the special name of Abhijin Moohurta, and Abhijit Sarva ' +
    'Doshaghnam or that noon time which cuts and cures all evil influences.',
  net_standing: 'cancelled',
  scope: 'muhurta',
  source_text_id: 'bphs_jaimini',
  source_chapter: 213,
  source_citation:
    'Jaimini Sutras (bphs_jaimini), trans. B. Suryanarain Rao, 1949, PG213 [chunk bphs_jaimini_pg0213_c01]',
  extraction_context: 'translator_gloss_in_narrative',
}

describe('ADJUDICATION-10 — the real seeded Abhijit sarva-doṣaghna row rescues a real doṣa', () => {
  it('rescues a rahu_kalam candidate via the real seeded row, with the full judgment ledger', () => {
    const out = adjudicateCandidates([CANDIDATE_A], substrate({
      lattice_rows: [latticeRow()],  // real, cited rahu_kalam dosha overlapping CANDIDATE_A
      parihara_rules: [ABHIJIT_PARIHARA_ROW],
    }))
    const ledger = out.ledgers[0]!

    // doṣas_present → parihāras_applied (citations) → residual → net standing
    expect(ledger.dosas_present.map((d) => d.factor_key)).toEqual(['rahu_kalam'])
    expect(ledger.pariharas_applied).toHaveLength(1)
    expect(ledger.pariharas_applied[0]).toMatchObject({
      dosha_key: 'rahu_kalam',
      dosha_name_en: 'Rahu Kalam',
      net_standing: 'cancelled',
      extraction_context: 'translator_gloss_in_narrative',
    })
    expect(ledger.pariharas_applied[0]!.cancellation_condition_text).toContain('Abhijit Sarva Doshaghnam')
    expect(ledger.pariharas_applied[0]!.source_citation).toContain('bphs_jaimini_pg0213_c01')
    expect(ledger.residual_dosas).toHaveLength(0)
    expect(ledger.net_standing).toBe('fully_cancelled')
    expect(ledger.adjudication_note).toMatch(/cancelled by a cited muhūrta-scope parihāra rule/i)
  })

  it('leaves a DIFFERENT doṣa (not rahu_kalam) residual — the row does not silently rescue everything', () => {
    // Same real seeded row, but the overlapping doṣa is yamaganda, not rahu_kalam.
    // The schema has no wildcard/all-doṣa convention, so this row's reach is
    // exactly and only what its dosha_canonical_id key-matches — proving the
    // engine does NOT over-apply the "sarva" (all) claim beyond what the
    // schema can honestly encode.
    const out = adjudicateCandidates([CANDIDATE_A], substrate({
      lattice_rows: [latticeRow({
        factor_key: 'yamaganda',
        source_citation: 'Drik Panchang published index tables (YAMAGANDAM_INDEX)',
      })],
      parihara_rules: [ABHIJIT_PARIHARA_ROW],
    }))
    const ledger = out.ledgers[0]!
    expect(ledger.dosas_present.map((d) => d.factor_key)).toEqual(['yamaganda'])
    expect(ledger.pariharas_applied).toHaveLength(0)
    expect(ledger.residual_dosas.map((d) => d.factor_key)).toEqual(['yamaganda'])
    expect(ledger.net_standing).toBe('residual_dosas_present')
    // Honest wording: a muhūrta rule exists, it just doesn't key-match this doṣa.
    expect(ledger.adjudication_note).toMatch(/no muhūrta-scope parihāra rule in the corpus matches this specific residual doṣa/i)
  })

  it('a clean (doṣa-free) candidate no longer claims "no muhūrta-scope parihāra rule exists in the corpus"', () => {
    // Regression guard: once ANY muhurta-scope row is present, the engine must
    // not attach the blanket "no muhūrta-scope parihāra rule exists in the
    // corpus" disclaimer to an unrelated clean candidate — that claim would
    // now be false.
    const out = adjudicateCandidates([CANDIDATE_A], substrate({
      lattice_rows: [latticeRow({ factor_key: 'abhijit', detail: { category: 'auspicious' } })],
      parihara_rules: [ABHIJIT_PARIHARA_ROW],
    }))
    expect(out.ledgers[0]!.net_standing).toBe('clean')
    expect(out.ledgers[0]!.adjudication_note).not.toMatch(/no muhūrta-scope parihāra rule exists in the corpus/i)
  })

  it('gap_report reports no parihāra corpus gap once the real row is present', () => {
    const out = adjudicateCandidates([CANDIDATE_A], substrate({
      lattice_rows: [latticeRow()],
      parihara_rules: [ABHIJIT_PARIHARA_ROW],
    }))
    expect(out.gap_report.parihara_corpus_gap).toBeNull()
    expect(out.density.parihara_rules_muhurta_scope).toBe(1)
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

// ── ADVERSARIAL DOMINATED-CONTENDER TEST (item 36 required gate) ────────────
//
// The Pareto filter must correctly eliminate a candidate that is dominated on
// EVERY available axis by another candidate — even when a third "unrelated"
// candidate is present. This is the adversarial test required by the W3-ENG
// lane spec: "Create a fixture with 3 candidates where candidate B dominates
// candidate A on all axes. Assert that after the Pareto filter, candidate A
// does NOT appear in the output."
//
// Axis definitions (AXES_USED in the engine):
//   panchangika_quality       — MAXIMIZE (the caller's auspiciousness score)
//   residual_dosha_burden     — MINIMIZE (count of residual doṣas)
//   cited_auspicious_support  — MAXIMIZE (count of cited auspicious factor spans)
//
// Fixture:
//   CANDIDATE_DOM_A (score=0.40, 1 doṣa, 0 support)  ← dominated by DOM_B
//   CANDIDATE_DOM_B (score=0.80, 0 doṣas, 1 support) ← dominates A on all axes
//   CANDIDATE_DOM_C (score=0.60, 1 doṣa, 1 support)  ← Pareto-incomparable
//
// Dominance check (B over A):
//   panchangika_quality: 0.80 ≥ 0.40 AND 0.80 > 0.40 ✓
//   residual_dosha_burden: 0 ≤ 1 AND 0 < 1 ✓
//   cited_auspicious_support: 1 ≥ 0 AND 1 > 0 ✓
//   → B strictly dominates A on all three axes.
//
// C vs A: A.residual_dosha_burden==1, C.residual_dosha_burden==1 (tied),
//         A.cited_auspicious_support==0 < C==1 so C is not at-least-as-good
//         on all axes as A (A.panchangika_quality==0.40 < C==0.60 — A is worse
//         on that axis). C does not dominate A (C is better on two axes,
//         worse on none, but for dominance we need "at least as good on ALL"
//         + "strictly better on at least one" — C.panchangika_quality=0.60
//         vs A=0.40: C is strictly better; C.residual_dosha_burden=1 vs A=1:
//         tied (satisfied); C.cited_auspicious_support=1 vs A=0: C strictly
//         better → YES, C also dominates A).
// Expected frontier: {DOM_B, DOM_C}. Expected dominated: {DOM_A}.

describe('ADVERSARIAL dominated-contender test — item 36 required gate', () => {
  // Fixed time windows (non-overlapping so no cross-contamination of lattice rows).
  const CAND_DOM_A: CandidateInterval = {
    id: 'dom_a', start: '2026-09-01T00:00:00Z', end: '2026-09-01T12:00:00Z',
    score: 0.40, disqualified: false,
  }
  const CAND_DOM_B: CandidateInterval = {
    id: 'dom_b', start: '2026-09-02T00:00:00Z', end: '2026-09-02T12:00:00Z',
    score: 0.80, disqualified: false,
  }
  const CAND_DOM_C: CandidateInterval = {
    id: 'dom_c', start: '2026-09-03T00:00:00Z', end: '2026-09-03T12:00:00Z',
    score: 0.60, disqualified: false,
  }

  // Lattice rows: one doṣa overlapping DOM_A only; one support overlapping
  // DOM_B AND DOM_C; nothing on DOM_A's support axis.
  const DOSA_ON_A = latticeRow({
    factor_key: 'rahu_kalam',
    start_utc: '2026-09-01T02:00:00Z', end_utc: '2026-09-01T03:30:00Z',
    detail: { category: 'inauspicious' },
    corpus_status: 'computed_cited',
  })
  const SUPPORT_ON_B = latticeRow({
    factor_key: 'abhijit',
    start_utc: '2026-09-02T05:00:00Z', end_utc: '2026-09-02T06:00:00Z',
    detail: { category: 'auspicious' },
    corpus_status: 'computed_cited',
  })
  const DOSA_ON_C = latticeRow({
    factor_key: 'yamaganda',
    start_utc: '2026-09-03T01:00:00Z', end_utc: '2026-09-03T02:30:00Z',
    detail: { category: 'inauspicious' },
    corpus_status: 'computed_cited',
  })
  const SUPPORT_ON_C = latticeRow({
    factor_key: 'abhijit',
    start_utc: '2026-09-03T05:00:00Z', end_utc: '2026-09-03T06:00:00Z',
    detail: { category: 'auspicious' },
    corpus_status: 'computed_cited',
  })

  it('the dominated candidate (A) does NOT appear in the Pareto frontier', () => {
    // Core gate criterion: candidate DOM_A — dominated on all axes by DOM_B —
    // must be pruned from the frontier.
    const s = substrate({
      lattice_rows: [DOSA_ON_A, SUPPORT_ON_B, DOSA_ON_C, SUPPORT_ON_C],
    })
    const out = adjudicateCandidates([CAND_DOM_A, CAND_DOM_B, CAND_DOM_C], s)

    // DOM_A is in the dominated set.
    expect(out.pareto.dominated_candidate_ids).toContain('dom_a')
    // DOM_A is NOT in the frontier.
    expect(out.pareto.frontier_candidate_ids).not.toContain('dom_a')
  })

  it('DOM_B (the dominator) survives the frontier', () => {
    const s = substrate({
      lattice_rows: [DOSA_ON_A, SUPPORT_ON_B, DOSA_ON_C, SUPPORT_ON_C],
    })
    const out = adjudicateCandidates([CAND_DOM_A, CAND_DOM_B, CAND_DOM_C], s)
    expect(out.pareto.frontier_candidate_ids).toContain('dom_b')
  })

  it('confirms DOM_B dominates DOM_A on all three axes (audit trace)', () => {
    // Verify the fixture actually encodes the intended dominance by checking
    // each candidate's ledger directly — the test is its own domain-logic proof.
    const s = substrate({
      lattice_rows: [DOSA_ON_A, SUPPORT_ON_B, DOSA_ON_C, SUPPORT_ON_C],
    })
    const out = adjudicateCandidates([CAND_DOM_A, CAND_DOM_B, CAND_DOM_C], s)

    const ledgerA = out.ledgers.find((l) => l.candidate_id === 'dom_a')!
    const ledgerB = out.ledgers.find((l) => l.candidate_id === 'dom_b')!

    // panchangika_quality: B (0.80) > A (0.40)
    expect(CAND_DOM_B.score).toBeGreaterThan(CAND_DOM_A.score)
    // residual_dosha_burden: B (0) < A (≥1 because no muhurta-scope parihāra rescues it)
    expect(ledgerB.residual_dosas.length).toBeLessThan(ledgerA.residual_dosas.length)
    // cited_auspicious_support: B (1 abhijit span) > A (0)
    expect(ledgerB.supporting_factors.length).toBeGreaterThan(ledgerA.supporting_factors.length)
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

// ── ACCURACY STANDARDS — DETERMINISM / REPLAY TEST ───────────────────────────
//
// W3-ENG spec accuracy requirement: "The adjudication engine's outputs must be
// deterministic (same inputs → same outputs) — write a replay test."
//
// A non-deterministic engine would make it impossible to audit a historical
// adjudication result: re-running on the same substrate could yield a different
// Pareto frontier. This test catches any inadvertent statefulness or random
// ordering in `adjudicateCandidates`.
//
// We run a moderately complex case (2 candidates, 3 lattice rows including one
// doṣa, one support, one convention) twice with structurally identical
// substrate objects and assert deep equality of the entire adjudication result.

describe('ACCURACY STANDARDS — determinism replay test', () => {
  const CAND_R1: CandidateInterval = {
    id: 'replay_1', start: '2026-10-01T00:00:00Z', end: '2026-10-01T12:00:00Z',
    score: 0.65, disqualified: false,
  }
  const CAND_R2: CandidateInterval = {
    id: 'replay_2', start: '2026-10-02T00:00:00Z', end: '2026-10-02T12:00:00Z',
    score: 0.45, disqualified: false,
  }
  const DOSA_ROW = latticeRow({
    factor_key: 'rahu_kalam',
    start_utc: '2026-10-01T02:00:00Z', end_utc: '2026-10-01T03:30:00Z',
    detail: { category: 'inauspicious' }, corpus_status: 'computed_cited',
  })
  const SUPPORT_ROW = latticeRow({
    factor_key: 'abhijit',
    start_utc: '2026-10-01T05:00:00Z', end_utc: '2026-10-01T06:00:00Z',
    detail: { category: 'auspicious' }, corpus_status: 'computed_cited',
  })
  const CONVENTION_ROW = latticeRow({
    factor_key: 'visha_ghati',
    start_utc: '2026-10-01T04:00:00Z', end_utc: '2026-10-01T04:24:00Z',
    corpus_status: 'computed_uncited_convention',
  })

  it('produces byte-identical results on two sequential calls with the same inputs (replay gate)', () => {
    const buildSubstrate = () => substrate({
      lattice_rows: [DOSA_ROW, SUPPORT_ROW, CONVENTION_ROW],
    })
    const run1 = adjudicateCandidates([CAND_R1, CAND_R2], buildSubstrate())
    const run2 = adjudicateCandidates([CAND_R1, CAND_R2], buildSubstrate())
    // Deep-equal covers all nested arrays and objects.
    expect(run1).toEqual(run2)
  })

  it('the coverage_state and pareto frontier are stable across replays', () => {
    const buildSubstrate = () => substrate({
      lattice_rows: [DOSA_ROW, SUPPORT_ROW, CONVENTION_ROW],
    })
    const run1 = adjudicateCandidates([CAND_R1, CAND_R2], buildSubstrate())
    const run2 = adjudicateCandidates([CAND_R1, CAND_R2], buildSubstrate())
    expect(run1.coverage_state).toBe(run2.coverage_state)
    expect(run1.pareto.frontier_candidate_ids).toEqual(run2.pareto.frontier_candidate_ids)
    expect(run1.pareto.dominated_candidate_ids).toEqual(run2.pareto.dominated_candidate_ids)
  })
})
