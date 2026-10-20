/**
 * kala_lattice_query.ts — ṢAḌ-DARŚANA W3 item 36: the query-time contender lattice
 * + parihāra adjudication engine.
 * ==========================================================================
 * SHAD_DARSHANA_BRIEF_v2_0.md §2 file map names this exact path — "query-time
 * lattice annotation + parihāra adjudication + Pareto survival + gap report over
 * the `bg_muhurta_lattice`/`bg_parihara_rules` tables". The SUBSTRATE (those
 * tables, their writers, migrations 484/485) landed with PR #930 on Night 2 and
 * is NOT rebuilt here. This file is item 36's remaining half: the engine.
 *
 * THE ONE-ENGINE RULE (SHAD_DARSHANA_BRIEF_v2_0.md §7; KALA_SUPREME_ELEVATION
 * _v1_0.md §9): ELECT (`kala_elect_get`, Mode 3) and YAJÑA-SETU
 * (`kala_ritual_get`, Modes 1–2) share THIS single generation+adjudication
 * engine. The contract-signing case and the yajña case differ only in the rule
 * tables and deity layer loaded — never in algorithm. Every exported function
 * here is therefore rite-agnostic: `subject_label` is carried into prose and
 * nowhere else, and a test asserts two different labels produce byte-identical
 * ledgers.
 *
 * WHAT THIS ENGINE COMPUTES (the query-time slice of Elevation §9's five stages):
 *   Stage 1 · annotation   — every lattice factor row whose [start,end) span
 *                            overlaps a candidate interval is attached to it.
 *                            Overlap is exact set arithmetic over the substrate's
 *                            own boundary events; there is no sampling interval
 *                            inside which a factor could hide.
 *   Stage 2 · census       — the factor census (item 41) is read as the
 *                            completeness register and surfaced in the gap
 *                            report: computed / not_computed / not_in_corpus.
 *   Stage 3 · adjudication — per candidate, the judgment ledger
 *                            `doṣas_present → parihāras_applied (citations) →
 *                            residual_doṣas → net standing`.
 *   Stage 4 · Pareto       — survival across factor GROUPS, over the axes that
 *                            are genuinely available, with the unavailable axes
 *                            DISCLOSED rather than silently scored zero.
 *   Stage 5 · gap report   — the decision surface: frontier, residual burden,
 *                            named corpus gaps. Never a fabricated
 *                            "next occurrence is 14 Nov".
 *
 * ══════════════════════════════════════════════════════════════════════════════
 * WHAT THIS ENGINE REFUSES TO DO (the three rails it is built against)
 *
 * 1. §N.6 SERVING DENSITY. The substrate stamps each lattice row
 *    `computed_cited` or `computed_uncited_convention` — the latter being a live
 *    deterministic production convention whose source table carries NO per-row
 *    classical citation (the writer disclosed this instead of inventing one).
 *    Convention rows are SERVED (B.10 forbids dropping data) but are counted and
 *    flagged SEPARATELY and can never become a doṣa, a supporting factor, or a
 *    Pareto axis input. A caller must never be able to read the annotation count
 *    as "N cited classical factors".
 *
 * 2. DATA HONESTY / B.10. This engine introduces NO new astrological constants.
 *    A factor's polarity comes from the substrate row's own `detail`
 *    (`kalam.category`, `combination_yoga.strength`) — nowhere else. A family the
 *    substrate ships without polarity (`agnivasa`, `ghati_muhurta`) is a NEUTRAL
 *    ANNOTATION, not a silently-assigned doṣa. And NO cancellation is derived in
 *    TypeScript (KA-4b, U:25 item 4; ALGO 3.17 step 3): the old `dosha_canonical_id`
 *    key-match is removed, so a doṣa-bearing candidate reads `cancellation_unassessed`
 *    — never "uncancelled" — until the scoped evaluator (served per doṣa on the
 *    registry ELECT face as `scoped_cancellation`) has assessed it. The per-scope rule
 *    counts are disclosed in `density.parihara_rules_by_scope`; a count is not an
 *    assessment. The lattice also does not emit the vivāha chapter's doṣas
 *    (`vivaha_chapter_dosas: 'not_detected'`), so "no cited doṣa" is not a clearance.
 *
 * 3. 3-STATE COVERAGE HONESTY. A null or empty substrate payload yields
 *    `honest_empty` (or `not_in_corpus` for the census), never `computed`. An
 *    interval whose only overlapping rows are conventions is `honest_empty` too:
 *    conventions are data, not cited computation.
 *
 * Consumers: `tools/kala_views/elect.ts` (Mode 3). `tools/kala_views/ritual.ts`
 * (Modes 1–2) consumes the SAME exports when its real engine lands at W4 — it
 * must not fork a second copy.
 */

import { callPlatformPrimitive } from '../client.js'
import { unwrapPrimitiveResult, unwrapFailureReason } from './primitive_unwrap.js'
import type { Principal } from '../types.js'

// ── Substrate row shapes (mirror migrations 484/485 exactly) ─────────────────

export type LatticeCorpusStatus = 'computed_cited' | 'computed_uncited_convention'

/** One row of `bg_muhurta_lattice`. */
export interface LatticeFactorRow {
  factor_family: string
  factor_key: string
  start_utc: string
  end_utc: string
  detail: Record<string, unknown> | null
  source_citation: string
  corpus_status: LatticeCorpusStatus
}

/** One row of `bg_parihara_rules`. */
export interface PariharaRuleRow {
  dosha_canonical_id: string
  dosha_name_en: string
  dosha_category: string
  cancellation_index: number
  cancellation_condition_text: string
  net_standing: string
  scope: 'natal' | 'muhurta'
  source_text_id: string
  source_chapter: number | null
  source_citation: string
  /** ADJUDICATION-10 / migration 524: NULL on every row seeded before that
   *  migration (not retroactively classified). 'mula_sutra_citation' | 'translator_gloss_in_narrative'
   *  when set — carried through to `AppliedParihara` so a caller can never mistake a translator's
   *  narrative aside for a mūla-sūtra verse. */
  extraction_context?: string | null
}

/** One row of `bg_muhurta_factor_census`. */
export interface FactorCensusRow {
  factor_family: string
  factor_name: string
  disposition: 'computed' | 'not_computed' | 'not_in_corpus'
  citation_or_gap_note: string
  evidence_pointer: string
  school_tag: string | null
}

/** The three substrate payloads plus their availability, kept explicit so a
 *  failed fetch can never be mistaken for an honestly-empty horizon. */
export interface LatticeSubstrate {
  lattice_rows: LatticeFactorRow[]
  parihara_rules: PariharaRuleRow[]
  census_rows: FactorCensusRow[]
  lattice_available: boolean
  parihara_available: boolean
  census_available: boolean
  unavailable_reason: string | null
}

// ── Engine inputs/outputs ───────────────────────────────────────────────────

/** A candidate window to adjudicate. `score` is the caller's ALREADY-COMPUTED
 *  scalar (muhurta_finder's auspiciousness_score) — referenced as a Pareto axis,
 *  never recomputed here (§N.5: the upstream value is the authority). */
export interface CandidateInterval {
  id: string
  start: string
  end: string
  score: number
  disqualified: boolean
}

/** A lattice factor as it appears inside a judgment ledger. */
export interface LedgerFactor {
  factor_family: string
  factor_key: string
  start_utc: string
  end_utc: string
  source_citation: string
}

export interface AppliedParihara {
  dosha_key: string
  dosha_name_en: string
  cancellation_condition_text: string
  net_standing: string
  source_citation: string
  /** See `PariharaRuleRow.extraction_context` — carried through so a translator's gloss is never
   *  presented with a mūla-sūtra verse's evidentiary weight. */
  extraction_context?: string | null
}

/**
 * ALGO 3.17 step 3 / U:25 item 4: this engine never derives a cancellation, so a doṣa-bearing
 * candidate reads `cancellation_unassessed` — never "uncancelled". `no_cited_dosa_detected` is a
 * statement about what the lattice DETECTS (it does not emit the vivāha chapter's doṣas — see
 * `vivaha_chapter_dosas`), never "checked and clean". The scoped evaluator's per-doṣa
 * cancelled / cancellation_unassessed states are served on the registry ELECT face
 * (`scoped_cancellation`), not here.
 */
export type NetStanding = 'no_cited_dosa_detected' | 'cancellation_unassessed' | 'not_adjudicated'

/** Elevation §9 stage 3: `doṣas_present → parihāras_applied → residual_doṣas → net standing`. */
export interface JudgmentLedger {
  candidate_id: string
  dosas_present: LedgerFactor[]
  /** Always empty here: no cancellation is derived in TypeScript (U:25 item 4). */
  pariharas_applied: AppliedParihara[]
  /** Doṣas whose cancellation was NOT assessed by this engine (kept under the old field name for the
   *  budget/alias consumers); presence here is not a finding that they are "uncancelled". */
  residual_dosas: LedgerFactor[]
  supporting_factors: LedgerFactor[]
  neutral_annotations: LedgerFactor[]
  net_standing: NetStanding
  /** §N.6: convention rows are served here, but in their own field, with their own count. */
  convention_only_factors: LedgerFactor[]
  convention_only_factor_count: number
  convention_only_keys: string[]
  convention_only_note: string | null
  adjudication_note: string
}

export interface ParetoAxisExclusion {
  key: string
  reason: string
}

export interface ParetoResult {
  frontier_candidate_ids: string[]
  dominated_candidate_ids: string[]
  axes_used: string[]
  axes_excluded: ParetoAxisExclusion[]
  method_note: string
}

export interface CensusGapEntry {
  factor_family: string
  factor_name: string
  reason: string
  evidence_pointer: string
}

export interface LatticeGapReport {
  statement: string
  factor_families_evaluated: string[]
  factors_not_computed: CensusGapEntry[]
  factors_not_in_corpus: CensusGapEntry[]
  census_disposition_counts: Record<string, number>
  census_state: 'computed' | 'honest_empty' | 'not_in_corpus'
  parihara_corpus_gap: string | null
  /** Always null at this build tier — the next-occurrence search beyond the
   *  horizon is not built, and an invented date is worse than an absent one. */
  next_occurrence: null
}

export type LatticeCoverageState = 'computed' | 'honest_empty' | 'not_in_corpus'

export interface LatticeAdjudication {
  ledgers: JudgmentLedger[]
  pareto: ParetoResult
  gap_report: LatticeGapReport
  coverage_state: LatticeCoverageState
  coverage_reason: string | null
  density: {
    cited_rows_in_horizon: number
    convention_only_rows_in_horizon: number
    parihara_rules_total: number
    parihara_rules_muhurta_scope: number
    /** Live per-scope rule counts (natal / muhurta / marriage / upanayana / general, as present).
     *  A count of rules is not an assessment of any candidate. */
    parihara_rules_by_scope: Record<string, number>
  }
  /** The lattice emits kālams, yogas, ghaṭīs and tithi/nakṣatra/lagna spans — not the vivāha
   *  chapter's doṣas — so "no doṣa present" is never "checked and clean" (U:25 item 4). */
  vivaha_chapter_dosas: 'not_detected'
}

export interface AdjudicationOptions {
  /** Prose label only (the rite/undertaking). Carried into the gap-report
   *  statement and NOWHERE else — the ONE-ENGINE RULE forbids algorithm
   *  divergence between ELECT and YAJÑA. */
  subject_label?: string
}

// ── Stage 1: overlap + polarity (both derived from substrate data only) ──────

function overlaps(row: LatticeFactorRow, candidate: CandidateInterval): boolean {
  const rowStart = Date.parse(row.start_utc)
  const rowEnd = Date.parse(row.end_utc)
  const candStart = Date.parse(candidate.start)
  const candEnd = Date.parse(candidate.end)
  if ([rowStart, rowEnd, candStart, candEnd].some((n) => Number.isNaN(n))) return false
  // Half-open on both sides: touching endpoints do not overlap.
  return rowStart < candEnd && rowEnd > candStart
}

type Polarity = 'dosha' | 'support' | 'neutral'

/**
 * Polarity comes from the row's OWN `detail`, which the substrate writer sourced
 * from panchang_engine's cited tables. `kalam` rows carry `category`;
 * `combination_yoga` rows carry `strength`. `agnivasa` and `ghati_muhurta` carry
 * neither — the substrate ships no polarity for them, so this engine assigns
 * none (B.10: an unstated polarity is not a doṣa).
 */
function polarityOf(row: LatticeFactorRow): Polarity {
  const detail = row.detail ?? {}
  const raw = detail['category'] ?? detail['strength']
  if (raw === 'inauspicious') return 'dosha'
  if (raw === 'auspicious') return 'support'
  return 'neutral'
}

function toLedgerFactor(row: LatticeFactorRow): LedgerFactor {
  return {
    factor_family: row.factor_family,
    factor_key: row.factor_key,
    start_utc: row.start_utc,
    end_utc: row.end_utc,
    source_citation: row.source_citation,
  }
}

const CONVENTION_NOTE =
  'These factor spans are live deterministic conventions whose source table carries no ' +
  'per-row classical citation (corpus_status=computed_uncited_convention). They are served ' +
  'in full but are NOT cited classical findings, and are excluded from doṣa detection, ' +
  'parihāra adjudication and every Pareto axis. See the factor census for each gap.'

/** Live per-scope counts, in a stable order. */
function countByScope(rules: PariharaRuleRow[]): Record<string, number> {
  const counts: Record<string, number> = {}
  for (const r of rules) counts[r.scope] = (counts[r.scope] ?? 0) + 1
  return Object.fromEntries(Object.entries(counts).sort(([x], [y]) => x.localeCompare(y)))
}

function scopeCountText(counts: Record<string, number>): string {
  const parts = Object.entries(counts).map(([scope, n]) => `${scope}=${n}`)
  return parts.length > 0 ? parts.join(', ') : 'none'
}

/**
 * U:25 item 4 / ALGO 3.17 step 3: replaces the old "ZERO muhūrta-scope rules … reported
 * UNCANCELLED" narration. States what was NOT done (cancellation not assessed here) and gives the
 * live per-scope rule counts instead of asserting an outcome.
 */
function cancellationUnassessedNote(dosaCount: number, counts: Record<string, number>): string {
  return (
    `${dosaCount} doṣa(s) present; cancellation_unassessed — this lattice reading evaluates no ` +
    'parihāra predicate, so it asserts no cancellation outcome for any doṣa. The scoped ' +
    'evaluator states (cancelled with locator / cancellation_unassessed) are served per doṣa on ' +
    `the registry ELECT face. Parihāra rules by scope in the corpus: ${scopeCountText(counts)} ` +
    '(a rule count is not an assessment of this candidate).'
  )
}

// ── Stage 3: adjudication ───────────────────────────────────────────────────

function buildLedger(
  candidate: CandidateInterval,
  rows: LatticeFactorRow[],
  substrate: LatticeSubstrate,
): JudgmentLedger {
  const overlapping = rows.filter((r) => overlaps(r, candidate))
  const cited = overlapping.filter((r) => r.corpus_status === 'computed_cited')
  const convention = overlapping.filter((r) => r.corpus_status !== 'computed_cited')

  const dosaRows = cited.filter((r) => polarityOf(r) === 'dosha')
  const supportRows = cited.filter((r) => polarityOf(r) === 'support')
  const neutralRows = cited.filter((r) => polarityOf(r) === 'neutral')

  const dosas_present = dosaRows.map(toLedgerFactor)
  const supporting_factors = supportRows.map(toLedgerFactor)
  const neutral_annotations = neutralRows.map(toLedgerFactor)

  const conventionFactors = convention
    .map(toLedgerFactor)
    .sort((a, b) => a.factor_key.localeCompare(b.factor_key))
  const conventionKeys = Array.from(new Set(conventionFactors.map((f) => f.factor_key))).sort()

  // Adjudication proper. No cancellation is derived here (U:25 item 4): a candidate with doṣas
  // reads cancellation_unassessed; `not_adjudicated` covers an unreadable lattice or parihāra
  // payload (an empty row set from a failed fetch is not "no doṣa").
  const pariharas_applied: AppliedParihara[] = []
  const residual_dosas: LedgerFactor[] = []
  let net_standing: NetStanding
  let adjudication_note: string

  if (!substrate.lattice_available || !substrate.parihara_available) {
    net_standing = 'not_adjudicated'
    adjudication_note =
      'The muhūrta lattice or parihāra graph payload was unavailable for this call' +
      (substrate.unavailable_reason ? ` (${substrate.unavailable_reason})` : '') +
      ', so no doṣa detection or cancellation was assessed; nothing is read as clean.'
  } else if (dosas_present.length === 0) {
    net_standing = 'no_cited_dosa_detected'
    adjudication_note =
      'No cited doṣa overlaps this candidate; uncited convention spans are listed separately. ' +
      'The lattice does not detect the vivāha chapter\'s doṣas, so this is not a clearance.'
  } else {
    residual_dosas.push(...dosas_present)
    net_standing = 'cancellation_unassessed'
    adjudication_note = cancellationUnassessedNote(dosas_present.length, countByScope(substrate.parihara_rules))
  }

  return {
    candidate_id: candidate.id,
    dosas_present,
    pariharas_applied,
    residual_dosas,
    supporting_factors,
    neutral_annotations,
    net_standing,
    convention_only_factors: conventionFactors,
    convention_only_factor_count: conventionFactors.length,
    convention_only_keys: conventionKeys,
    convention_only_note: conventionFactors.length > 0 ? CONVENTION_NOTE : null,
    adjudication_note,
  }
}

// ── Stage 4: Pareto survival ────────────────────────────────────────────────

/**
 * The five factor GROUPS Elevation §9 names. Only the three that this build tier
 * can genuinely evaluate participate; the other two are DISCLOSED as excluded.
 * Scoring an unavailable axis as zero would silently make every candidate tie on
 * it — a fabricated comparison dressed as a computed one.
 */
const EXCLUDED_AXES: readonly ParetoAxisExclusion[] = [
  {
    key: 'personal_field_alignment',
    reason:
      "the field's λ for the rite's domain requires ka_kshetra field rows, which are not " +
      'populated at this build tier (the lifetime-count priors blocker, campaign item 39 / W2) — ' +
      'this axis is excluded from the frontier rather than scored as a tie for every candidate',
  },
  {
    key: 'rite_specific_resonance',
    reason:
      'the per-activity rule join (bg_muhurta_activity_rules, keyed on tithi/nakṣatra/vāra ids) ' +
      'cannot be resolved from the candidate shape this engine is handed, which carries ' +
      'panchāṅga limb NAMES and not their ids — resolving names to ids would require a mapping ' +
      'table this lane refuses to invent (B.10); wiring the id path is item 6/7 W3 work',
  },
  {
    key: 'practical_feasibility',
    reason:
      'no substrate anywhere in this estate models a querent\'s practical constraints ' +
      '(travel, availability, participants), so the axis has no honest input and is excluded ' +
      'rather than approximated',
  },
] as const

interface AxisVector {
  id: string
  /** Maximize: the caller's already-computed auspiciousness score. */
  panchangika_quality: number
  /** Minimize: count of residual doṣas after adjudication. */
  residual_dosha_burden: number
  /** Maximize: count of cited auspicious factor spans overlapping. */
  cited_auspicious_support: number
}

const AXES_USED = ['panchangika_quality', 'residual_dosha_burden', 'cited_auspicious_support'] as const

function dominates(a: AxisVector, b: AxisVector): boolean {
  const atLeastAsGood =
    a.panchangika_quality >= b.panchangika_quality &&
    a.residual_dosha_burden <= b.residual_dosha_burden &&
    a.cited_auspicious_support >= b.cited_auspicious_support
  const strictlyBetter =
    a.panchangika_quality > b.panchangika_quality ||
    a.residual_dosha_burden < b.residual_dosha_burden ||
    a.cited_auspicious_support > b.cited_auspicious_support
  return atLeastAsGood && strictlyBetter
}

function buildPareto(candidates: CandidateInterval[], ledgers: JudgmentLedger[]): ParetoResult {
  const byId = new Map(ledgers.map((l) => [l.candidate_id, l]))
  const vectors: AxisVector[] = candidates.map((c) => {
    const ledger = byId.get(c.id)
    return {
      id: c.id,
      panchangika_quality: Number.isFinite(c.score) ? c.score : 0,
      residual_dosha_burden: ledger?.residual_dosas.length ?? 0,
      cited_auspicious_support: ledger?.supporting_factors.length ?? 0,
    }
  })

  const frontier: string[] = []
  const dominated: string[] = []
  for (const v of vectors) {
    if (vectors.some((other) => other.id !== v.id && dominates(other, v))) dominated.push(v.id)
    else frontier.push(v.id)
  }

  return {
    frontier_candidate_ids: frontier,
    dominated_candidate_ids: dominated,
    axes_used: [...AXES_USED],
    axes_excluded: [...EXCLUDED_AXES],
    method_note:
      'Pareto survival across factor groups (Elevation §9 stage 4): a candidate survives unless ' +
      'another candidate is at least as good on EVERY available axis and strictly better on one. ' +
      'Pruning is structural, never on a scalar score — a candidate strong on three axes and weak ' +
      'on one reaches grading alive. Excluded axes are listed, not zero-filled.',
  }
}

// ── Stage 5: gap report ─────────────────────────────────────────────────────

function buildGapReport(
  candidates: CandidateInterval[],
  ledgers: JudgmentLedger[],
  pareto: ParetoResult,
  substrate: LatticeSubstrate,
  evaluatedFamilies: string[],
  subjectLabel: string | undefined,
): LatticeGapReport {
  const dispositionCounts: Record<string, number> = {}
  for (const row of substrate.census_rows) {
    dispositionCounts[row.disposition] = (dispositionCounts[row.disposition] ?? 0) + 1
  }

  const toEntry = (r: FactorCensusRow): CensusGapEntry => ({
    factor_family: r.factor_family,
    factor_name: r.factor_name,
    reason: r.citation_or_gap_note,
    evidence_pointer: r.evidence_pointer,
  })

  const censusState: LatticeGapReport['census_state'] = !substrate.census_available
    ? 'not_in_corpus'
    : substrate.census_rows.length > 0
      ? 'computed'
      : 'honest_empty'

  const ruleCounts = countByScope(substrate.parihara_rules)
  const pariharaGap = !substrate.parihara_available
    ? 'The parihāra graph payload was unavailable for this call, so no rule counts are available.'
    : (ruleCounts['muhurta'] ?? 0) === 0
      ? `No muhūrta-scope parihāra rule is present (rules by scope: ${scopeCountText(ruleCounts)}); ` +
        'cancellation is assessed per doṣa by the scoped evaluator, not by this lattice reading.'
      : null

  const subject = subjectLabel ? ` for ${subjectLabel}` : ''
  const residualTotal = ledgers.reduce((n, l) => n + l.residual_dosas.length, 0)

  const statement = candidates.length === 0
    ? `No candidate windows were supplied to the lattice engine${subject}, so no frontier exists. ` +
      'Whether a better configuration occurs beyond the searched horizon is not computed at this ' +
      'build tier — the next-occurrence search is not built, and no date is invented here.'
    : `${pareto.frontier_candidate_ids.length} of ${candidates.length} candidate window(s)${subject} survive ` +
      `Pareto adjudication across ${pareto.axes_used.length} available factor group(s); ` +
      `${residualTotal} doṣa annotation(s) across the slate have cancellation_unassessed. ` +
      `${pareto.axes_excluded.length} factor group(s) could not be evaluated at this build tier and are ` +
      'named in axes_excluded. Whether a textbook-perfect configuration occurs beyond this horizon is ' +
      'not computed at this build tier — no next-occurrence date is asserted.'

  return {
    statement,
    factor_families_evaluated: evaluatedFamilies,
    factors_not_computed: substrate.census_rows.filter((r) => r.disposition === 'not_computed').map(toEntry),
    factors_not_in_corpus: substrate.census_rows.filter((r) => r.disposition === 'not_in_corpus').map(toEntry),
    census_disposition_counts: dispositionCounts,
    census_state: censusState,
    parihara_corpus_gap: pariharaGap,
    next_occurrence: null,
  }
}

// ── The engine entry point ──────────────────────────────────────────────────

export function adjudicateCandidates(
  candidates: CandidateInterval[],
  substrate: LatticeSubstrate,
  options: AdjudicationOptions = {},
): LatticeAdjudication {
  const rows = substrate.lattice_available ? substrate.lattice_rows : []
  const ledgers = candidates.map((c) => buildLedger(c, rows, substrate))
  const pareto = buildPareto(candidates, ledgers)

  const citedRows = rows.filter((r) => r.corpus_status === 'computed_cited')
  const conventionRows = rows.filter((r) => r.corpus_status !== 'computed_cited')

  const evaluatedFamilies = Array.from(new Set(citedRows.map((r) => r.factor_family))).sort()

  const gap_report = buildGapReport(
    candidates, ledgers, pareto, substrate, evaluatedFamilies, options.subject_label,
  )

  // ── 3-state coverage honesty ──
  // `computed` is claimed ONLY when cited rows genuinely annotated something.
  let coverage_state: LatticeCoverageState
  let coverage_reason: string | null
  const annotatedCited = ledgers.some(
    (l) => l.dosas_present.length + l.supporting_factors.length + l.neutral_annotations.length > 0,
  )

  if (!substrate.lattice_available) {
    coverage_state = 'honest_empty'
    coverage_reason =
      'the muhūrta lattice payload could not be read for this call' +
      (substrate.unavailable_reason ? `: ${substrate.unavailable_reason}` : '')
  } else if (citedRows.length === 0 && conventionRows.length > 0) {
    coverage_state = 'honest_empty'
    coverage_reason =
      'the only lattice rows overlapping this horizon are uncited conventions ' +
      '(corpus_status=computed_uncited_convention); they are served in each ledger\'s ' +
      'convention_only_factors but do not constitute a cited computed annotation'
  } else if (citedRows.length === 0) {
    coverage_state = 'honest_empty'
    coverage_reason =
      'no lattice factor rows overlap the searched horizon — the lattice carries a rolling ' +
      'forward horizon built by an explicit super-admin L0 trigger, so an interval outside ' +
      'that built horizon is honestly empty rather than a computed clean verdict'
  } else if (!annotatedCited) {
    coverage_state = 'honest_empty'
    coverage_reason =
      'cited lattice rows exist in the fetched horizon but none overlaps any supplied ' +
      'candidate interval, so no candidate carries a computed annotation'
  } else {
    coverage_state = 'computed'
    coverage_reason = null
  }

  return {
    ledgers,
    pareto,
    gap_report,
    coverage_state,
    coverage_reason,
    density: {
      cited_rows_in_horizon: citedRows.length,
      convention_only_rows_in_horizon: conventionRows.length,
      parihara_rules_total: substrate.parihara_available ? substrate.parihara_rules.length : 0,
      parihara_rules_muhurta_scope: substrate.parihara_available
        ? substrate.parihara_rules.filter((r) => r.scope === 'muhurta').length
        : 0,
      parihara_rules_by_scope: substrate.parihara_available ? countByScope(substrate.parihara_rules) : {},
    },
    vivaha_chapter_dosas: 'not_detected',
  }
}

// ── Substrate fetch adapter ─────────────────────────────────────────────────
//
// The engine above is a PURE function of its substrate — that is what makes it
// unit-testable and what keeps ELECT and YAJÑA on one implementation. This
// adapter is the only I/O in the file: it reads the two L0 capabilities
// (`query_muhurta_lattice`, `query_parihara_graph`) through the platform's
// surgical-primitive route, exactly as every other platform-mcp data path does.
// A failed or malformed payload sets the corresponding `*_available` flag to
// false with a reason — it never yields a plausible-looking empty array.

function asRows<T>(section: unknown): T[] {
  if (!section || typeof section !== 'object') return []
  const rows = (section as { rows?: unknown }).rows
  return Array.isArray(rows) ? (rows as T[]) : []
}

export async function fetchLatticeSubstrate(
  params: { start_utc: string; end_utc: string; limit?: number },
  principal: Principal,
): Promise<LatticeSubstrate> {
  const reasons: string[] = []

  let lattice_rows: LatticeFactorRow[] = []
  let lattice_available = false
  try {
    const { status, envelope } = await callPlatformPrimitive(
      'query_muhurta_lattice',
      { start_utc: params.start_utc, end_utc: params.end_utc, ...(params.limit ? { limit: params.limit } : {}) },
      principal,
    )
    if (status === 200 && envelope.ok) {
      // The primitives route serves a legacy ToolBundle — the capability payload
      // lives at result.results[0].content as a JSON string, never at
      // result.<key> (see primitive_unwrap.ts). `lattice_available` is a REAL
      // detector on the parsed payload (§N.8): true only when the payload
      // actually carried a `rows` array. An empty `rows` array IS available
      // (an honestly-empty horizon) — distinct from wrapper-parse failure and
      // from a payload with no rows section.
      const { payload, failure } = unwrapPrimitiveResult(envelope.result)
      if (failure !== null) {
        reasons.push(unwrapFailureReason('query_muhurta_lattice', failure))
      } else if (!payload || !('rows' in payload)) {
        reasons.push('query_muhurta_lattice payload carried no rows section')
      } else if (!Array.isArray(payload['rows'])) {
        reasons.push('query_muhurta_lattice rows section is not an array')
      } else {
        lattice_rows = payload['rows'] as LatticeFactorRow[]
        lattice_available = true
      }
    } else {
      reasons.push(`query_muhurta_lattice returned status ${status}`)
    }
  } catch (err) {
    reasons.push(`query_muhurta_lattice threw: ${String(err)}`)
  }

  let parihara_rules: PariharaRuleRow[] = []
  let census_rows: FactorCensusRow[] = []
  let parihara_available = false
  let census_available = false
  try {
    const { status, envelope } = await callPlatformPrimitive('query_parihara_graph', {}, principal)
    if (status === 200 && envelope.ok) {
      // Same ToolBundle unwrap as above. `parihara_available` / `census_available`
      // are REAL detectors on the parsed payload: true only when the payload
      // actually carried that section (each section's rows may honestly be empty).
      // A wrapper-parse failure fails BOTH flags with the distinct unwrap reason —
      // never the misleading "returned no <x> section" that a live-populated
      // production DB would make a lie.
      const { payload, failure } = unwrapPrimitiveResult(envelope.result)
      if (failure !== null) {
        reasons.push(unwrapFailureReason('query_parihara_graph', failure))
      } else {
        parihara_rules = asRows<PariharaRuleRow>(payload?.['parihara_rules'])
        census_rows = asRows<FactorCensusRow>(payload?.['factor_census'])
        parihara_available = payload?.['parihara_rules'] !== undefined
        census_available = payload?.['factor_census'] !== undefined
        if (!parihara_available) reasons.push('query_parihara_graph payload carried no parihara_rules section')
        if (!census_available) reasons.push('query_parihara_graph payload carried no factor_census section')
      }
    } else {
      reasons.push(`query_parihara_graph returned status ${status}`)
    }
  } catch (err) {
    reasons.push(`query_parihara_graph threw: ${String(err)}`)
  }

  return {
    lattice_rows,
    parihara_rules,
    census_rows,
    lattice_available,
    parihara_available,
    census_available,
    unavailable_reason: reasons.length > 0 ? reasons.join('; ') : null,
  }
}
