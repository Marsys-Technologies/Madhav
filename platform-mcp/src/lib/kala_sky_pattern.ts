/**
 * kala_sky_pattern.ts — ṢAḌ-DARŚANA W4 Lane R (YAJÑA-SETU), registry item 40.
 * ==========================================================================
 * TWO things live in this file, and the ordering between them is BINDING:
 *
 *   1. §5.4 — the INDIVIDUALIZED-MORTALITY-WINDOW HARD EXCLUSION (ADJUDICATION-13).
 *      Pure, synchronous, evaluated FIRST on every W4 entry point, before any
 *      computation. See the block comment above `detectMortalityExclusion`.
 *   2. The Mode-2 `sky_pattern_spec v1` constraint compiler + coarse-to-fine
 *      searcher over the muhūrta lattice (KALA_W4_UPAYA_DESIGN_v1_0.md §3.4).
 *
 * WHY THE RAIL LIVES HERE rather than in a third new library: Lane R's declared
 * file ownership (design §0.1) is exactly two new libs. The rail is a
 * REQUEST-SHAPE + SUBSTRATE gate, so it belongs with the spec compiler that
 * parses request shapes. `ritual.ts` and `elect.ts` both import it from here.
 *
 * ══════════════════════════════════════════════════════════════════════════════
 * THE ONE-ENGINE RULE (brief §7; design §0.2 — a RAIL, not a convenience)
 *
 * ELECT and YAJÑA-SETU share the SINGLE lattice/adjudication/grading engine in
 * `kala_lattice_query.ts`. This file **calls** `fetchLatticeSubstrate` and
 * `adjudicateCandidates`; it never forks, re-implements or copies them. It
 * defines NO second `adjudicateCandidates`, NO second `buildLedger`, and NO
 * second Pareto `dominates` — the `D-ONE-ENGINE` source assertion (design §6.3)
 * checks exactly that, and this file is written to satisfy it by construction.
 *
 * What this file IS allowed to build beside the engine, and why that is not a
 * second engine (design §3.4): `SkyPatternGapReport` answers a question only the
 * Mode-2 searcher CAN answer — "which constraint eliminated this horizon, and
 * when does the declared pattern next occur?" — because only it holds the spec.
 * The frozen engine's `LatticeGapReport` answers a different question ("which
 * factor families did the census not cover?") and its `next_occurrence` is
 * hard-`null` by deliberate design. So this report **composes** the frozen one
 * (embedding it verbatim under `census`) rather than reimplementing any of it.
 * That composition is required by fixture PASS condition 1, which is otherwise
 * structurally undischargeable on an empty result.
 *
 * ══════════════════════════════════════════════════════════════════════════════
 * COMPLETENESS BY CONSTRUCTION (Elevation §9 Stage 1 — the reason this is a
 * lattice search and not a per-candidate panchāṅga sampler)
 *
 * Every constraint kind this compiler supports maps 1:1 onto a lattice factor
 * family, and every factor is piecewise-constant on the lattice atoms. The
 * search therefore intersects/subtracts ATOM INTERVALS — exact set arithmetic
 * over the substrate's own boundary events. There is no sampling interval inside
 * which a satisfying window could hide. A spec naming a factor the census marks
 * `not_in_corpus` triggers the design §6.2 drop-and-report precedence rule
 * (dropped from the conjunction, reported by name), never a silent skip.
 */

import { callPlatformPrimitive } from '../client.js'
import { unwrapPrimitiveResult, unwrapFailureReason } from './primitive_unwrap.js'
import type { Principal } from '../types.js'
import {
  adjudicateCandidates,
  fetchLatticeSubstrate,
  type CandidateInterval,
  type FactorCensusRow,
  type LatticeAdjudication,
  type LatticeFactorRow,
  type LatticeGapReport,
  type LatticeSubstrate,
} from './kala_lattice_query.js'
import {
  computeAgnivasaConventionBVoice,
  type AgnivasaConventionBVoice,
} from './agnivasa_convention_b_voice.js'

// ══════════════════════════════════════════════════════════════════════════════
// §5.4 — INDIVIDUALIZED-MORTALITY-WINDOW HARD EXCLUSION (ADJUDICATION-13)
// ══════════════════════════════════════════════════════════════════════════════
//
// BINDING, and the only rule in W4 that withholds THE OUTPUT ITSELF — native
// included. §5.3 governs filing; this governs computation.
//
//   "§3.5.C's no-date-of-death clause is ABSOLUTE across every audience tier,
//    and the live L1 span-of-life tool is the named exposure (deliberately NOT
//    spelled here — the gate's own source scan treats a literal reference as a
//    violation, and it is right to: the tool name is exactly what must never
//    appear in a W4 code path. The design doc §5.4 names it):
//    a W4 surface that read such a fact into a window bound would
//    produce an individualized mortality window BY COMPOSITION, without any
//    surface ever *claiming* to serve one. No W4 surface may read āyurdāya or
//    longevity facts into any window bound, under any tier, filed or unfiled."
//
// Two properties a future edit must not weaken:
//   - It is NOT a disclosure tier. `native_self` does not unlock it.
//   - It is NOT conditioned on filing. An unfiled individualized mortality
//     window is still an individualized mortality window.
//
// Shape deliberately mirrors `isMode3ShapedRequest` (proven in production, and
// it already has the properties this needs):
//   - PURE and SYNCHRONOUS — structurally incapable of awaiting I/O, so it
//     cannot be reordered after a fetch by a later refactor.
//   - Evaluated FIRST, before any computation, on every W4 entry point.
//   - SHORT-CIRCUITS COMPLETELY — the refusal envelope carries no candidates, no
//     window, no diagnosis, because none was attempted.
//
// ENTRY-POINT ORDER (design §3.4, binding): mortality FIRST, then the Mode-3
// detector. Mortality withholds the output under every tier, whereas the Mode-3
// detector merely redirects to a surface that would have to run this check
// anyway.

/**
 * The forbidden-substrate identifier set (§5.4 test 1). This is a SUBSTRATE ban,
 * not a topic ban — deliberately. A topic ban alone would let a longevity fact
 * reach a window bound through an intermediate computation that never says
 * "mortality" anywhere (§5.4 test 3, the subtle case).
 *
 * Exported so the source-level scan (gate G16 part b) and the runtime detector
 * assert against ONE list rather than two that can drift apart.
 */
export const MORTALITY_FORBIDDEN_IDENTIFIERS: readonly string[] = [
  'ayurdaya',
  'longevity',
  'maraka',
  'ayus',
] as const

/**
 * Word-boundary matcher for the forbidden set. `\bayus\b` specifically, because
 * `ayus` is a substring of ordinary words ("ayusmati") and of `ayurdaya` itself;
 * an unbounded match would be noisy without being stronger.
 *
 * NOTE the deliberate exception the regex must tolerate: this file NAMES the
 * forbidden identifiers in order to ban them. The source-level gate scans for
 * matches OUTSIDE this module's own declaration block — see
 * `yajna_mode2_fixture_gate.ts`'s D-MORTALITY-SOURCE detector, which excludes
 * this file's own definition site by design and would otherwise be a rail that
 * fires on itself.
 */
export const MORTALITY_EXCLUSION_PATTERN = /ayurdaya|longevity|maraka|\bayus\b/i

/** Additional request-shape vocabulary (§5.4 test 2 — an `event_class` or
 *  `question_frame` naming a mortality/longevity subject). Kept separate from
 *  the substrate set above because the two tests are genuinely different: this
 *  one is about what the CALLER asked for, that one is about what the CODE may
 *  read. Both must fire. */
const MORTALITY_REQUEST_SHAPE_PATTERN =
  /\b(death|dying|die|died|mortality|lifespan|life[- ]span|how long (will|do) i live|when (will|do) i die|end of life|terminal|fatal|demise|survive)\b/i

export type MortalityExclusionTest = 'substrate' | 'request_shape' | 'composition'

export interface MortalityExclusionDecision {
  excluded: boolean
  /** Which of §5.4's three tests fired. `null` iff `excluded === false`. */
  test: MortalityExclusionTest | null
  /** The exact token/field that fired. `null` iff `excluded === false`. */
  matched_on: string | null
  /** The clause this refusal names, verbatim, so a caller can look it up. */
  clause: '§3.5.C (MACRO_PLAN_v2_0.md Ethical Framework) via KALA_W4_UPAYA_DESIGN_v1_0.md §5.4 / ADJUDICATION-13'
  statement: string
}

const MORTALITY_REFUSAL_STATEMENT =
  'This request is withheld under the individualized-mortality-window HARD EXCLUSION. ' +
  'MACRO_PLAN_v2_0.md §3.5.C\'s no-date-of-death clause is ABSOLUTE across every audience ' +
  'tier — it is not a disclosure tier and it is not conditioned on filing, so no audience ' +
  'setting and no consent state unlocks it. No candidate window, no ranked slate, no ' +
  'diagnosis and no partial computation is served with this response, because none was ' +
  'attempted: the check runs before any computation. If the underlying question is about ' +
  'timing a rite, a remedy or an undertaking, re-ask it in those terms and it will be ' +
  'served in full.'

const NOT_EXCLUDED: MortalityExclusionDecision = {
  excluded: false,
  test: null,
  matched_on: null,
  clause: '§3.5.C (MACRO_PLAN_v2_0.md Ethical Framework) via KALA_W4_UPAYA_DESIGN_v1_0.md §5.4 / ADJUDICATION-13',
  statement: '',
}

/** Every string a request can carry that a mortality subject could hide in.
 *  Collected exhaustively rather than spot-checked, because §5.4 test 3's whole
 *  point is that the subtle case does not announce itself. */
function collectRequestStrings(request: unknown, depth = 0): string[] {
  if (depth > 6 || request == null) return []
  if (typeof request === 'string') return [request]
  if (typeof request === 'number' || typeof request === 'boolean') return []
  if (Array.isArray(request)) return request.flatMap((v) => collectRequestStrings(v, depth + 1))
  if (typeof request === 'object') {
    return Object.entries(request as Record<string, unknown>).flatMap(([key, value]) => [
      // The KEY matters as much as the value: `{ ayurdaya_window: true }` names
      // the substrate without ever putting the word in a value position.
      key,
      ...collectRequestStrings(value, depth + 1),
    ])
  }
  return []
}

/**
 * §5.4's detector. **PURE and SYNCHRONOUS — never make this async.** If a future
 * refactor needs a fetch to decide, that refactor is wrong: the guarantee this
 * rail provides is that it CANNOT have been reordered after a fetch, and an
 * async signature silently retires that guarantee.
 *
 * @param request the full, unmodified tool input (every field, including
 *        `question_frame`, `sky_pattern_spec`, `event_class`, `undertaking`).
 */
export function detectMortalityExclusion(request: unknown): MortalityExclusionDecision {
  const strings = collectRequestStrings(request)

  // Test 1 — SUBSTRATE. Any reference to āyurdāya/longevity/māraka/āyus in the
  // request, in a key or a value. This is the test that catches a caller
  // steering a W4 surface at longevity substrate without naming mortality.
  for (const s of strings) {
    const m = MORTALITY_EXCLUSION_PATTERN.exec(s)
    if (m) {
      return {
        excluded: true,
        test: 'substrate',
        matched_on: m[0],
        clause: NOT_EXCLUDED.clause,
        statement: MORTALITY_REFUSAL_STATEMENT,
      }
    }
  }

  // Test 2 — REQUEST SHAPE. An event_class / question_frame / undertaking naming
  // a mortality or longevity subject in ordinary language.
  for (const s of strings) {
    const m = MORTALITY_REQUEST_SHAPE_PATTERN.exec(s)
    if (m) {
      return {
        excluded: true,
        test: 'request_shape',
        matched_on: m[0],
        clause: NOT_EXCLUDED.clause,
        statement: MORTALITY_REFUSAL_STATEMENT,
      }
    }
  }

  // Test 3 — COMPOSITION is enforced structurally rather than at this call site:
  // no W4 code path imports or calls the L1 span-of-life capability (its name is
  // deliberately not written here — see the header), asserted by the
  // source-level scan (gate G16 part b). That is why
  // test 1 is a SUBSTRATE ban: it makes the composition case unreachable rather
  // than trying to detect it after the fact.
  return NOT_EXCLUDED
}

/** The refusal envelope. Deliberately NOT a `KalaEnvelope` — it carries no
 *  reading, no coverage, no candidate data of any kind, exactly the
 *  `buildMode3WrongViewResponse` pattern: a response that carries no content
 *  because none was attempted. */
export interface MortalityExclusionRefusal {
  withheld: true
  withheld_reason: 'individualized_mortality_window_hard_exclusion'
  clause: MortalityExclusionDecision['clause']
  statement: string
  detector: { test: MortalityExclusionTest; matched_on: string }
  /** Stated explicitly so a caller cannot read the refusal as tier-dependent. */
  audience_tier_independent: true
  filing_state_independent: true
}

export function buildMortalityExclusionRefusal(
  decision: MortalityExclusionDecision,
): MortalityExclusionRefusal {
  if (!decision.excluded || decision.test === null || decision.matched_on === null) {
    throw new Error(
      'buildMortalityExclusionRefusal called on a non-excluded decision — this would emit a ' +
        'refusal with no detector behind it (§N.8: a signal without a real detector is null, not green)',
    )
  }
  return {
    withheld: true,
    withheld_reason: 'individualized_mortality_window_hard_exclusion',
    clause: decision.clause,
    statement: decision.statement,
    detector: { test: decision.test, matched_on: decision.matched_on },
    audience_tier_independent: true,
    filing_state_independent: true,
  }
}

// ══════════════════════════════════════════════════════════════════════════════
// sky_pattern_spec v1 — the constraint vocabulary (FROZEN per design §3.4)
// ══════════════════════════════════════════════════════════════════════════════

export type SkyPatternConstraintKind =
  | 'planet_state'
  | 'mutual_configuration'
  | 'chart_relative'
  | 'panchanga'
  | 'panchanga_not'
  | 'residence'
  | 'kalam_not'
  | 'transit_contact'
  | 'natal_yoga_activation'

export const SKY_PATTERN_CONSTRAINT_KINDS: readonly SkyPatternConstraintKind[] = [
  'planet_state',
  'mutual_configuration',
  'chart_relative',
  'panchanga',
  'panchanga_not',
  'residence',
  'kalam_not',
  'transit_contact',
  'natal_yoga_activation',
] as const

/** One constraint, as it appears in the fixture JSON: a single-key object whose
 *  key is the kind. Kept loose at the boundary and narrowed by the compiler, so
 *  an unknown kind is REPORTED rather than throwing. */
export type SkyPatternConstraint = Record<string, unknown>

export interface SkyPatternSpec {
  spec_version?: string
  all?: SkyPatternConstraint[]
  any?: SkyPatternConstraint[]
  horizon?: { months?: number }
}

export type ConstraintDispositionState =
  | 'computed'
  | 'computed_chart_relative'
  | 'not_in_corpus'
  | 'not_computed'
  | 'unknown_kind'

export interface SkyPatternConstraintDisposition {
  kind: string
  /** Human-stable identity for this constraint within the spec, e.g. `panchanga:vara`. */
  key: string
  state: ConstraintDispositionState
  /** Which lattice factor family this constraint resolved onto. `null` when it
   *  did not resolve (and then `reason` says why). */
  factor_family: string | null
  /** Required whenever state !== 'computed'. */
  reason: string | null
  /** Set only for chart-relative constraints: the `chart_facts.fact_id` whose
   *  value was read (§N.5 — referenced, never recomputed). */
  chart_fact_id?: string | null
  /** True when the constraint was DROPPED from the conjunction per the design
   *  §6.2 precedence rule. Dropping is reported, never silent. */
  dropped_from_conjunction: boolean
  /** Number of lattice atoms this constraint matched in the searched horizon.
   *  `0` with `state: 'computed'` is a legal, meaningful answer (the family is
   *  materialized; nothing in this horizon satisfies the constraint). */
  matched_atom_count: number
  /** ADJUDICATION-17: set ONLY on `kind: 'residence'` (agnivāsa) dispositions —
   *  one Convention (B) voice per matched atom (same shape as `kp_school_voice.ts`'s
   *  concurrence/dissent precedent), reporting what the `agnivasa_muhurta_chintamani_
   *  arithmetic` convention would say about the SAME date Convention (A) already
   *  resolved. Informational only — this array is NEVER consulted by the match logic
   *  above (`favourableElements`), which stays hardcoded to Convention (A) by design.
   *  `undefined` on every other constraint kind; `[]` when Convention (B) is not yet
   *  `convention_status='computed'` for this chart (an honest absence, not a gap in
   *  this array). */
  agnivasa_convention_b_voices?: AgnivasaConventionBVoice[]
}

export type PrecisionRegime = 'intra_day' | 'day_grade'

export interface SkyPatternCandidate {
  id: string
  start_utc: string
  end_utc: string
  /** §3.4: `intra_day` iff EVERY binding constraint is pāñcāṅgika or day-part
   *  (both intrinsically sub-day astronomical instants). The moment a
   *  `transit_contact` or `mutual_configuration` constraint binds, the candidate
   *  degrades to `day_grade` AND says which constraint did it. Conservatively
   *  labelling a purely-pāñcāṅgika candidate `day_grade` applies the honesty
   *  BACKWARDS and is an explicit FAIL of fixture PASS condition 2. */
  precision_regime: PrecisionRegime
  /** Names the COARSEST binding factor family — the reason the label is what it
   *  is, not just the label (§N.8). */
  precision_basis: string
  /** The lattice families that bound this candidate, in the order they were
   *  intersected. */
  binding_families: string[]
  /** Single reference location for the whole lattice — carried on every
   *  candidate because sunrise-derived boundaries (horā, vāra, every kālam) are
   *  location-dependent (design §3.1's honesty disclosure). */
  reference_location_key: string
  location_divergence_note: string | null
  /** item 44 — every W4 surface making a temporal claim emits `authority_basis`
   *  naming the id it INHERITED, and computes no window of its own. Here that is
   *  the set of lattice atom keys whose intersection IS this window. */
  authority_basis: string[]
}

export interface SkyPatternGapReport {
  statement: string
  eliminating_constraint: { kind: string; key: string; detail: string } | null
  constraints_evaluated: SkyPatternConstraintDisposition[]
  next_occurrence: { start_utc: string; end_utc: string } | null
  next_occurrence_state: 'found' | 'not_within_scan_ceiling' | 'not_searched'
  scan_ceiling_utc: string | null
  /** Embedded VERBATIM from the frozen engine — composed, never reimplemented. */
  census: LatticeGapReport
}

export interface SkyPatternCoverageEntry {
  concept: string
  state: 'computed' | 'honest_empty' | 'not_in_corpus'
  reason: string | null
  chart_fact_id?: string | null
}

export interface SkyPatternSearchResult {
  candidates: SkyPatternCandidate[]
  gap_report: SkyPatternGapReport
  coverage: SkyPatternCoverageEntry[]
  precision: {
    regime: PrecisionRegime
    basis: string
    /** True when NO constraint in the spec is of a kind that could legitimately
     *  degrade the label — the *reason* the label is right (fixture PASS 2's
     *  second assertion). */
    no_degrading_constraint_kinds_present: boolean
  }
  /** The frozen engine's adjudication over the produced candidates. `null` only
   *  when there were no candidates to adjudicate. */
  adjudication: LatticeAdjudication | null
  /** The paddhati convention set that resolved `residence` constraints. */
  paddhati: PaddhatiResolution | null
}

// ══════════════════════════════════════════════════════════════════════════════
// Interval arithmetic (exact set ops over lattice atoms — no sampling)
// ══════════════════════════════════════════════════════════════════════════════

export interface Interval {
  start: number
  end: number
  /** The lattice atom keys that contributed this interval — carried into
   *  `authority_basis`. */
  basis: string[]
}

function normalize(intervals: Interval[]): Interval[] {
  const sorted = intervals
    .filter((i) => i.end > i.start)
    .sort((a, b) => a.start - b.start || a.end - b.end)
  const out: Interval[] = []
  for (const iv of sorted) {
    const last = out[out.length - 1]
    if (last && iv.start <= last.end) {
      if (iv.end > last.end) last.end = iv.end
      for (const b of iv.basis) if (!last.basis.includes(b)) last.basis.push(b)
    } else {
      out.push({ start: iv.start, end: iv.end, basis: [...iv.basis] })
    }
  }
  return out
}

export function intersectIntervals(a: Interval[], b: Interval[]): Interval[] {
  const out: Interval[] = []
  let i = 0
  let j = 0
  const A = normalize(a)
  const B = normalize(b)
  while (i < A.length && j < B.length) {
    const start = Math.max(A[i]!.start, B[j]!.start)
    const end = Math.min(A[i]!.end, B[j]!.end)
    if (end > start) {
      out.push({ start, end, basis: [...A[i]!.basis, ...B[j]!.basis] })
    }
    if (A[i]!.end < B[j]!.end) i++
    else j++
  }
  return out
}

export function subtractIntervals(a: Interval[], b: Interval[]): Interval[] {
  const B = normalize(b)
  let cur = normalize(a)
  for (const cut of B) {
    const next: Interval[] = []
    for (const iv of cur) {
      if (cut.end <= iv.start || cut.start >= iv.end) {
        next.push(iv)
        continue
      }
      if (cut.start > iv.start) next.push({ start: iv.start, end: cut.start, basis: [...iv.basis] })
      if (cut.end < iv.end) next.push({ start: cut.end, end: iv.end, basis: [...iv.basis] })
    }
    cur = next
  }
  return cur
}

function rowInterval(row: LatticeFactorRow): Interval | null {
  const start = Date.parse(row.start_utc)
  const end = Date.parse(row.end_utc)
  if (Number.isNaN(start) || Number.isNaN(end) || end <= start) return null
  return { start, end, basis: [`${row.factor_family}/${row.factor_key}@${row.start_utc}`] }
}

// ══════════════════════════════════════════════════════════════════════════════
// The paddhati convention reader (R-2's consumer side)
// ══════════════════════════════════════════════════════════════════════════════

export interface PaddhatiConventionRow {
  factor_family: string
  convention_id: string
  school_tag: string
  constraint_role: 'hard' | 'soft' | 'informational'
  convention_status: 'computed' | 'declared_not_computed'
  provenance: string
  corpus_gap_ref: string | null
  native_confirmed: boolean
  awaiting_native_confirmation: boolean
  version: string
  /** Set iff native_confirmed=TRUE (migration 534): where the native's
   *  confirmation is recorded, so this reader cites a document section rather
   *  than a chat transcript. Optional on the wire — a primitive predating 534
   *  may not serve the column. */
  confirmation_provenance?: string | null
}

export interface PaddhatiResolution {
  version: string | null
  /** ONLY `convention_status='computed'` rows. A `declared_not_computed`
   *  convention that silently participated in grading is the exact failure the
   *  status exists to prevent (ADJUDICATION-8 rail 2). */
  operative: PaddhatiConventionRow[]
  /** Served so the divergence surface is real rather than decorative — but
   *  NEVER evaluated. */
  declared_not_computed: PaddhatiConventionRow[]
  /** Per ADJUDICATION-8's own arithmetic, the honest value today. */
  divergence: {
    state: 'none_computed' | 'diverges' | 'agrees'
    reason: string
  }
  /** ADJUDICATION-8 rail 1 — DERIVED from the fetched profile rows by
   *  `paddhatiCensusStatement`, never a wrapper-local constant (§N.7 item 3):
   *  migration 534 flips `native_confirmed` TRUE with a
   *  `confirmation_provenance`, and a static "not on record" claim would
   *  silently shadow that data. */
  census_statement: string
  available: boolean
  unavailable_reason: string | null
}

export const PADDHATI_DIVERGENCE_STATES = ['none_computed', 'diverges', 'agrees'] as const

/** The convention-content clause every census statement opens with. The
 *  CONTENT did not change in migration 534 — only its attestation did — so
 *  this clause is common to all three states below. */
export const PADDHATI_CENSUS_BASE =
  'agnivāsa convention = corpus default (tithi-element, pṛthvī-favourable); '

/** ADJUDICATION-8 rail 1's original coverage statement — the honest text
 *  WHILE no native confirmation row exists. Exported (as the old
 *  PADDHATI_CENSUS_STATEMENT was) so a gate/test asserts the exact string
 *  rather than re-spelling it. */
export const PADDHATI_CENSUS_UNCONFIRMED =
  PADDHATI_CENSUS_BASE + 'the native\'s lineage convention is not on record.'

/**
 * ADJUDICATION-8 rail 1's coverage statement, DERIVED from the fetched profile
 * rows rather than pinned as a static claim. Migration 534 (PR #1036) seeds
 * `native_confirmed=TRUE` with a `confirmation_provenance` for the Agnivāsa
 * convention on both canonical charts — a hardcoded "not on record" becomes
 * FALSE the moment that migration applies (§N.7 item 3: no wrapper-local
 * constant may shadow cited data; §N.8: a claim needs a detector — here, the
 * detector is reading the row the claim is about).
 *
 * Three states, each honest:
 *   confirmed   — an operative agnivāsa row carries native_confirmed=TRUE:
 *                 the statement cites the row's own confirmation_provenance.
 *   unconfirmed — the profile was read and carries no confirmed agnivāsa row:
 *                 the original "not on record" text (verbatim), plus an
 *                 awaiting-confirmation note when the row says so itself.
 *   unreachable — the profile could NOT be read: reported as unreachable with
 *                 the fetch-failure reason. An unreadable record is never
 *                 restated as "not on record" — absence of evidence vs.
 *                 evidence of absence.
 */
export function paddhatiCensusStatement(
  profile: Pick<PaddhatiResolution, 'available' | 'unavailable_reason' | 'operative'>,
): string {
  if (!profile.available) {
    return (
      PADDHATI_CENSUS_BASE +
      'whether the native\'s lineage convention is on record could NOT be determined for this ' +
      'call (' +
      (profile.unavailable_reason ?? 'kala_paddhati_profile unreachable') +
      ') — an unreachable profile is reported as unreachable, never restated as "not on record".'
    )
  }
  const confirmed = profile.operative.find(
    (r) => r.factor_family === 'agnivasa' && r.native_confirmed === true,
  )
  if (confirmed) {
    return (
      PADDHATI_CENSUS_BASE +
      `natively CONFIRMED as the native's lineage convention (${confirmed.convention_id}` +
      (confirmed.school_tag ? `, ${confirmed.school_tag}` : '') +
      '); ' +
      (confirmed.confirmation_provenance && confirmed.confirmation_provenance.trim()
        ? `confirmation recorded: ${confirmed.confirmation_provenance.trim()}`
        : 'the row carries native_confirmed=TRUE but no confirmation_provenance — a data gap ' +
          'to raise upstream (migration 534 prescribes the column be set iff confirmed)') +
      '.'
    )
  }
  const awaiting = profile.operative.some(
    (r) => r.factor_family === 'agnivasa' && r.awaiting_native_confirmation === true,
  )
  return awaiting
    ? PADDHATI_CENSUS_UNCONFIRMED + ' (awaiting native confirmation.)'
    : PADDHATI_CENSUS_UNCONFIRMED
}

/**
 * ADJUDICATION-17: a REAL divergence detector (§N.8 — replaces the previous hardcoded
 * `'none_computed'` literal). This is a CHART-LEVEL signal (`fetchPaddhatiProfile` has no date
 * parameter), so it cannot report a specific date's agree/diverge verdict — that real,
 * per-date comparison is `computeAgnivasaConventionBVoice` (`agnivasa_convention_b_voice.ts`),
 * called from the `residence` branch where a date IS available.
 *
 * What this CAN honestly say at chart level: whether the two conventions are even STRUCTURALLY
 * comparable (`'none_computed'` when Convention B isn't `computed`), and — when both are
 * computed — that they provably diverge on at least some real (tithi_id, vara_id) pairs. This
 * is not asserted from vibes: Convention A partitions by tithi_id alone (1-7=Prithvi favourable,
 * 8-30=other); Convention B is `(tithi_id + 1 + vara_id) mod 4`. A concrete, checkable
 * counter-example: tithi_id=1, vara_id=3 (Tuesday) — Convention A reads Prithvi (favourable,
 * tithi 1-7 band); Convention B reads `(1+1+3) mod 4 = 1` → Ākāśa (unfavourable). Both
 * `tithi_id=1` and `vara_id=3` are valid, real panchāṅga values — this is a genuine structural
 * divergence, not a hypothetical.
 */
function computePaddhatiDivergence(
  operative: PaddhatiConventionRow[],
): PaddhatiResolution['divergence'] {
  const conventionBOperative = operative.some(
    (r) => r.factor_family === 'agnivasa' && r.convention_id === 'agnivasa_muhurta_chintamani_arithmetic',
  )
  if (!conventionBOperative) {
    return {
      state: 'none_computed',
      reason:
        'one convention computable; agnivasa_muhurta_chintamani_arithmetic is ' +
        'declared_not_computed pending muhurta_chintamani translation',
    }
  }
  return {
    state: 'diverges',
    reason:
      'both agnivāsa conventions are computed. Structural divergence (not a per-instant claim ' +
      '— this call carries no date): Convention (A) partitions by tithi_id alone (1-7=Prithvi ' +
      'favourable); Convention (B) is (tithi_id+1+vara_id) mod 4. Checkable counter-example: ' +
      'tithi_id=1, vara_id=3 (Tuesday) — (A) reads Prithvi/favourable, (B) reads ' +
      '(1+1+3) mod 4=1 -> Akasha/unfavourable. For a SPECIFIC candidate date\'s comparison, ' +
      'see the muhurta_chintamani school voice on that date\'s residence disposition, not this ' +
      'chart-level field.',
  }
}

/**
 * ADJUDICATION-17, the per-date half of the ruling this file's `residence` branch
 * implements: for the EXACT atoms Convention (A) already matched (`matched`, computed by
 * the hardcoded `favourableElements` filter below — this function receives that result, it
 * never recomputes or influences it), build Convention (B)'s live voice from the SAME
 * atom's `detail`. Purely additive and read-only — no atom is dropped, reordered, or
 * reclassified by this function; it only ever APPENDS a second opinion alongside the one
 * Convention (A) already reached.
 *
 * Returns `[]` (not one `honest_empty` entry per atom) when Convention (B) itself is not
 * `convention_status='computed'` for this chart — the chart-level gap is already carried by
 * `PaddhatiResolution.divergence` (`computePaddhatiDivergence` above); repeating it once per
 * matched atom here would be noise, not honesty.
 */
export function buildAgnivasaConventionBVoices(
  matchedRows: Pick<LatticeFactorRow, 'detail'>[],
  paddhatiOperative: PaddhatiConventionRow[],
): AgnivasaConventionBVoice[] {
  const conventionBOperative = paddhatiOperative.some(
    (r) => r.factor_family === 'agnivasa' && r.convention_id === 'agnivasa_muhurta_chintamani_arithmetic',
  )
  if (!conventionBOperative) return []
  return matchedRows.map((r) => computeAgnivasaConventionBVoice(r.detail, true))
}

export async function fetchPaddhatiProfile(
  chartId: string,
  principal: Principal,
): Promise<PaddhatiResolution> {
  let rows: PaddhatiConventionRow[] = []
  let available = false
  let unavailable_reason: string | null = null
  try {
    const { status, envelope } = await callPlatformPrimitive(
      'query_kala_paddhati_profile',
      { chart_id: chartId },
      principal,
    )
    if (status === 200 && envelope.ok) {
      // ToolBundle unwrap (primitive_unwrap.ts) + real availability detector on the
      // parsed payload (§N.8) — never `available = true` on bare HTTP 200.
      const { payload, failure } = unwrapPrimitiveResult(envelope.result)
      if (failure !== null) {
        unavailable_reason = unwrapFailureReason('query_kala_paddhati_profile', failure)
      } else if (!Array.isArray(payload?.['rows'])) {
        unavailable_reason = 'query_kala_paddhati_profile payload carried no rows section'
      } else {
        rows = payload['rows'] as PaddhatiConventionRow[]
        available = true
      }
    } else {
      unavailable_reason = `query_kala_paddhati_profile returned status ${status}`
    }
  } catch (err) {
    unavailable_reason = `query_kala_paddhati_profile threw: ${String(err)}`
  }

  // Version selection is `ORDER BY version DESC LIMIT 1` — a STRING sort, which
  // is why the seed zero-pads (`paddhati_v01`). `paddhati_v10` would otherwise
  // sort below `paddhati_v2`. Same trap ADJUDICATION-2 called out for `ne_v01`;
  // repeated here because it bites per-table.
  const versions = Array.from(new Set(rows.map((r) => r.version))).sort()
  const version = versions.length > 0 ? versions[versions.length - 1]! : null
  const scoped = version ? rows.filter((r) => r.version === version) : []

  const operative = scoped.filter((r) => r.convention_status === 'computed')
  const declared = scoped.filter((r) => r.convention_status === 'declared_not_computed')

  return {
    version,
    operative,
    declared_not_computed: declared,
    divergence: computePaddhatiDivergence(operative),
    census_statement: paddhatiCensusStatement({ available, unavailable_reason, operative }),
    available,
    unavailable_reason,
  }
}

// ══════════════════════════════════════════════════════════════════════════════
// Chart-relative substrate (R-4) — read by fact_id, never recomputed (§N.5)
// ══════════════════════════════════════════════════════════════════════════════

export interface ChartRelativeSubstrate {
  /** The chart's janma nakṣatra NAME as L1 computed it. */
  janma_nakshatra: string | null
  /** The `chart_facts.fact_id` that value was read from. Carried into the
   *  response so a caller can resolve it (§N.5 / B.3). */
  janma_nakshatra_fact_id: string | null
  available: boolean
  unavailable_reason: string | null
}

/**
 * Reads the chart's own janma nakṣatra from L1.
 *
 * §N.7 item 2 discipline: the selection pins `fact_key` (not just a category)
 * AND carries a total order, because `chart_facts` holds one row per ayanamsha
 * for this key and a category-only `.find()` would pick an arbitrary one.
 */
export async function fetchChartRelativeSubstrate(
  chartId: string,
  principal: Principal,
): Promise<ChartRelativeSubstrate> {
  try {
    const { status, envelope } = await callPlatformPrimitive(
      'query_chart_facts',
      {
        chart_id: chartId,
        ayanamsha_id: 'lahiri_chitrapaksha',
        category: 'graha_position',
        planet: 'MOON',
        shape: 'rows',
        limit: 200,
      },
      principal,
    )
    if (status !== 200 || !envelope.ok) {
      return {
        janma_nakshatra: null,
        janma_nakshatra_fact_id: null,
        available: false,
        unavailable_reason: `query_chart_facts returned status ${status}`,
      }
    }
    // ToolBundle unwrap (primitive_unwrap.ts): the chart_facts payload's `rows`
    // live inside results[0].content, never at envelope.result.rows.
    const { payload, failure } = unwrapPrimitiveResult(envelope.result)
    if (failure !== null) {
      return {
        janma_nakshatra: null,
        janma_nakshatra_fact_id: null,
        available: false,
        unavailable_reason: unwrapFailureReason('query_chart_facts', failure),
      }
    }
    const rows = (Array.isArray(payload?.['rows']) ? payload['rows'] : []) as {
      fact_id?: string
      fact_key?: string
      fact_subject?: string
      fact_value_text?: string
    }[]
    const matches = rows
      .filter(
        (r) =>
          r.fact_key === 'nakshatra' &&
          (r.fact_subject ?? '').toUpperCase() === 'MOON' &&
          typeof r.fact_value_text === 'string' &&
          r.fact_value_text.length > 0,
      )
      // TOTAL order on fact_id — deterministic across calls, never `[0]` of an
      // unordered set (§N.7 item 2).
      .sort((a, b) => (a.fact_id ?? '').localeCompare(b.fact_id ?? ''))
    const picked = matches[0]
    if (!picked) {
      return {
        janma_nakshatra: null,
        janma_nakshatra_fact_id: null,
        available: false,
        unavailable_reason:
          'no MOON/nakshatra fact resolved for this chart at ayanamsha lahiri_chitrapaksha — ' +
          'the chart-relative constraint cannot be evaluated and is reported, not guessed',
      }
    }
    return {
      janma_nakshatra: picked.fact_value_text ?? null,
      janma_nakshatra_fact_id: picked.fact_id ?? null,
      available: true,
      unavailable_reason: null,
    }
  } catch (err) {
    return {
      janma_nakshatra: null,
      janma_nakshatra_fact_id: null,
      available: false,
      unavailable_reason: `query_chart_facts threw: ${String(err)}`,
    }
  }
}

/**
 * The nine tārā names in cycle order, and the classical count arithmetic.
 *
 * Source: `panchang_engine/tara_bala.py`'s own `_TARA_QUALITY` table, which the
 * production per-chart tārā-bala path already uses — REFERENCED here as the
 * naming convention, not re-derived as new astrological content. The arithmetic
 * (`((current - janma + 27) mod 27) mod 9`) is the same counted-from-janma rule
 * that module implements.
 *
 * §N.5 note on why this is a mirror rather than a call: `tara_bala.py` is a
 * Python sidecar module with no primitive route exposed for a *hypothetical*
 * transit nakṣatra, and the value needed here is the tārā of a LATTICE ATOM's
 * nakṣatra relative to the chart's janma nakṣatra — a query-time composition of
 * two already-computed values, not a new astrological constant. The nakṣatra
 * ORDER itself comes from the lattice atoms' own `detail.factor_id`, read from
 * panchang_engine, so the only thing stated here is the 9-fold cycle's names.
 */
export const TARA_CYCLE = [
  'janma',
  'sampat',
  'vipat',
  'kshema',
  'pratyak',
  'sadhaka',
  'vadha',
  'mitra',
  'ati_mitra',
] as const

export type TaraName = (typeof TARA_CYCLE)[number]

/** 1-based nakṣatra ids in, tārā name out. Pure. */
export function taraFor(janmaNakshatraId: number, currentNakshatraId: number): TaraName {
  const count = ((currentNakshatraId - janmaNakshatraId + 27) % 27) % 9
  return TARA_CYCLE[count]!
}

// ══════════════════════════════════════════════════════════════════════════════
// The compiler
// ══════════════════════════════════════════════════════════════════════════════

/** Which lattice family each constraint kind resolves onto. Every kind maps 1:1
 *  (design §3.4) — kinds with `null` have no chart-independent lattice family at
 *  this build tier and trigger drop-and-report. */
const KIND_TO_FAMILY: Record<SkyPatternConstraintKind, string | null> = {
  planet_state: 'hora',
  panchanga: 'panchangika',
  panchanga_not: 'panchangika',
  residence: 'agnivasa',
  kalam_not: 'kalam',
  chart_relative: null, // evaluated at query time as a post-filter (R-4)
  mutual_configuration: null,
  transit_contact: null,
  natal_yoga_activation: null,
}

/** The kinds that, when BINDING, legitimately degrade a candidate to
 *  `day_grade`. Pāñcāṅgika and day-part limbs are intrinsically sub-day
 *  astronomical instants and do NOT degrade (Elevation §8). */
const DEGRADING_KINDS: readonly SkyPatternConstraintKind[] = [
  'transit_contact',
  'mutual_configuration',
] as const

function constraintKindOf(c: SkyPatternConstraint): string {
  const keys = Object.keys(c)
  return keys[0] ?? 'unknown'
}

/** Resolve a graha name (Sanskrit or English) to its canonical English name via
 *  `brahma_ontology` — the cited L0 authority (BPHS), never a hardcoded alias
 *  map in this file (§N.5: reference the authority, do not restate it). */
export async function resolveGrahaName(
  name: string,
  principal: Principal,
): Promise<{ canonical: string | null; reason: string | null }> {
  try {
    const { status, envelope } = await callPlatformPrimitive('resolve_entity', { name }, principal)
    if (status !== 200 || !envelope.ok) {
      return { canonical: null, reason: `resolve_entity returned status ${status}` }
    }
    // ToolBundle unwrap (primitive_unwrap.ts): the resolve_entity capability returns
    // the entity row as its content — read it off the parsed payload, not envelope.result.
    const { payload, failure } = unwrapPrimitiveResult(envelope.result)
    if (failure !== null) {
      return { canonical: null, reason: unwrapFailureReason('resolve_entity', failure) }
    }
    const r = payload as { canonical_name_en?: string; entity?: { canonical_name_en?: string } } | null
    const canonical = r?.canonical_name_en ?? r?.entity?.canonical_name_en ?? null
    return canonical
      ? { canonical, reason: null }
      : { canonical: null, reason: `resolve_entity returned no canonical_name_en for '${name}'` }
  } catch (err) {
    return { canonical: null, reason: `resolve_entity threw: ${String(err)}` }
  }
}

function censusDisposition(census: FactorCensusRow[], factorName: string): FactorCensusRow | null {
  return census.find((r) => r.factor_name === factorName) ?? null
}

export interface SkyPatternSearchParams {
  spec: SkyPatternSpec
  chartId: string
  horizonStartUtc: string
  horizonEndUtc: string
  /** How far past the horizon `next_occurrence` may scan before giving up. */
  scanCeilingUtc: string
  subjectLabel?: string
}

/**
 * The Mode-2 search. Calls the FROZEN engine for substrate and adjudication;
 * everything between is exact interval arithmetic over that substrate's atoms.
 */
export async function searchSkyPattern(
  params: SkyPatternSearchParams,
  principal: Principal,
): Promise<SkyPatternSearchResult> {
  const substrate: LatticeSubstrate = await fetchLatticeSubstrate(
    { start_utc: params.horizonStartUtc, end_utc: params.scanCeilingUtc },
    principal,
  )
  const [paddhati, chartRel] = await Promise.all([
    fetchPaddhatiProfile(params.chartId, principal),
    fetchChartRelativeSubstrate(params.chartId, principal),
  ])

  const constraints = params.spec.all ?? []
  const dispositions: SkyPatternConstraintDisposition[] = []
  const horizonStart = Date.parse(params.horizonStartUtc)
  const horizonEnd = Date.parse(params.horizonEndUtc)
  const ceiling = Date.parse(params.scanCeilingUtc)

  const rowsByFamily = new Map<string, LatticeFactorRow[]>()
  for (const row of substrate.lattice_rows) {
    const list = rowsByFamily.get(row.factor_family) ?? []
    list.push(row)
    rowsByFamily.set(row.factor_family, list)
  }

  // Whole-scan-window seed: the search starts as "all of it" and every
  // constraint narrows. An empty result is therefore always attributable.
  let surviving: Interval[] = [{ start: horizonStart, end: ceiling, basis: [] }]
  let eliminating: SkyPatternGapReport['eliminating_constraint'] = null
  const bindingFamilies: string[] = []
  let anyDegradingKindPresent = false

  for (const c of constraints) {
    const kind = constraintKindOf(c)
    const body = c[kind]
    const kindTyped = SKY_PATTERN_CONSTRAINT_KINDS.includes(kind as SkyPatternConstraintKind)
      ? (kind as SkyPatternConstraintKind)
      : null

    if (kindTyped === null) {
      dispositions.push({
        kind,
        key: `${kind}:unknown`,
        state: 'unknown_kind',
        factor_family: null,
        reason:
          `'${kind}' is not one of sky_pattern_spec v1's nine frozen constraint kinds ` +
          `(${SKY_PATTERN_CONSTRAINT_KINDS.join(', ')}). It is DROPPED from the conjunction and ` +
          'reported here rather than silently skipped.',
        dropped_from_conjunction: true,
        matched_atom_count: 0,
      })
      continue
    }

    if (DEGRADING_KINDS.includes(kindTyped)) anyDegradingKindPresent = true

    const compiled = await compileConstraint({
      kind: kindTyped,
      body,
      rowsByFamily,
      census: substrate.census_rows,
      paddhati,
      chartRel,
      principal,
    })
    dispositions.push(compiled.disposition)

    if (compiled.disposition.dropped_from_conjunction) continue

    const before = surviving
    surviving =
      compiled.mode === 'exclude'
        ? subtractIntervals(surviving, compiled.intervals)
        : intersectIntervals(surviving, compiled.intervals)
    if (compiled.disposition.factor_family) bindingFamilies.push(compiled.disposition.factor_family)

    // First constraint to empty the HORIZON (not the scan ceiling) is the
    // eliminating one — recorded once, never overwritten by a later constraint
    // that merely also fails.
    const inHorizonBefore = before.some((i) => i.start < horizonEnd && i.end > horizonStart)
    const inHorizonAfter = surviving.some((i) => i.start < horizonEnd && i.end > horizonStart)
    if (eliminating === null && inHorizonBefore && !inHorizonAfter) {
      eliminating = {
        kind: compiled.disposition.kind,
        key: compiled.disposition.key,
        detail:
          `this constraint eliminated every remaining interval inside the searched horizon ` +
          `(${params.horizonStartUtc} .. ${params.horizonEndUtc}); ` +
          `${compiled.disposition.matched_atom_count} lattice atom(s) matched it across the full scan window`,
      }
    }
  }

  // Split into in-horizon candidates and beyond-horizon next-occurrence.
  const inHorizon = surviving.filter((i) => i.start < horizonEnd && i.end > horizonStart)
    .map((i) => ({ ...i, start: Math.max(i.start, horizonStart), end: Math.min(i.end, horizonEnd) }))
    .filter((i) => i.end > i.start)
  const beyondHorizon = surviving.filter((i) => i.end > horizonEnd)
    .map((i) => ({ ...i, start: Math.max(i.start, horizonEnd) }))
    .filter((i) => i.end > i.start)
    .sort((a, b) => a.start - b.start)

  // ── Precision regime (§3.4) ──
  const uniqueBinding = Array.from(new Set(bindingFamilies))
  const regime: PrecisionRegime = anyDegradingKindPresent ? 'day_grade' : 'intra_day'
  const coarsest = pickCoarsestFamily(uniqueBinding)
  const basis = anyDegradingKindPresent
    ? `degraded to day_grade by a ${DEGRADING_KINDS.filter((k) => dispositions.some((d) => d.kind === k)).join('/')} constraint — ` +
      'transit and mutual-configuration edges are day_grade at this build tier (brief §4: no W4 lane may ' +
      'require sub-day transit precision)'
    : uniqueBinding.length === 0
      ? 'no constraint bound this search — the horizon is unconstrained, so no precision claim is made from a binding factor'
      : `every binding constraint is pāñcāṅgika or day-part (${uniqueBinding.join(', ')}); coarsest binding family = ${coarsest}`

  const candidates: SkyPatternCandidate[] = inHorizon.map((iv, i) => ({
    id: `sp${i}`,
    start_utc: new Date(iv.start).toISOString(),
    end_utc: new Date(iv.end).toISOString(),
    precision_regime: regime,
    precision_basis: basis,
    binding_families: uniqueBinding,
    reference_location_key: 'bhubaneswar',
    location_divergence_note:
      'bg_muhurta_lattice is computed at ONE fixed reference location (bhubaneswar, ' +
      'lat 20.27 / lon 85.84 / UTC+05:30). Sunrise-derived boundaries — horā, vāra, every ' +
      'kālam — are location-dependent. A querent elsewhere must re-derive these boundaries ' +
      'for their own location; this divergence is served as data, never silently reconciled.',
    // item 44: the ids this window INHERITED. No window is computed here that is
    // not the intersection of already-computed atoms.
    authority_basis: iv.basis,
  }))

  // ── The frozen engine adjudicates the candidates we produced ──
  // This shared terminal call IS the one-engine rule made concrete (design §3.4).
  const intervals: CandidateInterval[] = candidates.map((c) => ({
    id: c.id,
    start: c.start_utc,
    end: c.end_utc,
    // Mode 2 has no upstream auspiciousness scalar (that is muhurta_finder's, and
    // it belongs to ELECT's act-time slate). 0 is the honest neutral here — it is
    // the SAME value for every candidate, so it can never silently order them.
    score: 0,
    disqualified: false,
  }))
  const adjudication =
    intervals.length > 0
      ? adjudicateCandidates(intervals, substrate, {
          subject_label: params.subjectLabel ?? 'declared sky pattern (YAJÑA-SETU Mode 2)',
        })
      : null

  // ── The gap report ──
  const censusReport: LatticeGapReport =
    adjudication?.gap_report ??
    adjudicateCandidates([], substrate, { subject_label: params.subjectLabel }).gap_report

  const next = beyondHorizon[0] ?? null
  const gap_report: SkyPatternGapReport = {
    statement: buildGapStatement(candidates.length, eliminating, dispositions, params),
    eliminating_constraint:
      candidates.length === 0
        ? eliminating ?? {
            kind: 'conjunction',
            key: 'all',
            detail:
              'no single constraint emptied the horizon on its own — the conjunction of the ' +
              'surviving constraints has no common interval inside it. Each constraint\'s own ' +
              'matched-atom count is in constraints_evaluated.',
          }
        : null,
    constraints_evaluated: dispositions,
    next_occurrence: next
      ? { start_utc: new Date(next.start).toISOString(), end_utc: new Date(next.end).toISOString() }
      : null,
    // `not_searched` is reserved for the case where the scan window genuinely did
    // not extend past the horizon — otherwise an absent date means "we looked and
    // found nothing", which is a different claim (§N.8 applied to a nullable field).
    next_occurrence_state: next
      ? 'found'
      : ceiling > horizonEnd
        ? 'not_within_scan_ceiling'
        : 'not_searched',
    scan_ceiling_utc: ceiling > horizonEnd ? params.scanCeilingUtc : null,
    census: censusReport,
  }

  return {
    candidates,
    gap_report,
    coverage: buildSkyPatternCoverage(dispositions, chartRel, paddhati, substrate),
    precision: {
      regime,
      basis,
      no_degrading_constraint_kinds_present: !anyDegradingKindPresent,
    },
    adjudication,
    paddhati,
  }
}

/** Coarsest = the family with the longest typical atom. Ordering is a property of
 *  the substrate's own construction (a vāra atom spans a whole Hindu day; a horā
 *  atom is 1/24 of one), not an astrological judgment. */
const FAMILY_COARSENESS: Record<string, number> = {
  vara: 100,
  tithi: 95,
  nakshatra: 95,
  agnivasa: 90,
  lagna: 40,
  hora: 30,
  combination_yoga: 25,
  kalam: 20,
  ghati_muhurta: 10,
}

function pickCoarsestFamily(families: string[]): string {
  if (families.length === 0) return 'none'
  return [...families].sort((a, b) => (FAMILY_COARSENESS[b] ?? 0) - (FAMILY_COARSENESS[a] ?? 0))[0]!
}

function buildGapStatement(
  candidateCount: number,
  eliminating: SkyPatternGapReport['eliminating_constraint'],
  dispositions: SkyPatternConstraintDisposition[],
  params: SkyPatternSearchParams,
): string {
  const dropped = dispositions.filter((d) => d.dropped_from_conjunction)
  const droppedNote =
    dropped.length > 0
      ? ` ${dropped.length} constraint(s) were DROPPED from the conjunction and the search ran on the ` +
        `remainder: ${dropped.map((d) => `${d.key} (${d.state})`).join(', ')}. The result is therefore ` +
        'PARKED-HONEST on those gaps, not a clean satisfaction of the declared pattern.'
      : ''
  if (candidateCount > 0) {
    return (
      `${candidateCount} interval(s) inside ${params.horizonStartUtc} .. ${params.horizonEndUtc} satisfy ` +
      `every evaluable constraint of the declared sky pattern.${droppedNote}`
    )
  }
  const why = eliminating
    ? `The eliminating constraint is ${eliminating.key}: ${eliminating.detail}.`
    : 'No constraint could be named as the eliminating one.'
  return (
    `No interval inside ${params.horizonStartUtc} .. ${params.horizonEndUtc} satisfies the declared ` +
    `sky pattern. ${why}${droppedNote}`
  )
}

function buildSkyPatternCoverage(
  dispositions: SkyPatternConstraintDisposition[],
  chartRel: ChartRelativeSubstrate,
  paddhati: PaddhatiResolution,
  substrate: LatticeSubstrate,
): SkyPatternCoverageEntry[] {
  // One entry per spec constraint, no more and no fewer (fixture PASS 4).
  const entries: SkyPatternCoverageEntry[] = dispositions.map((d) => ({
    concept: d.key,
    state:
      d.state === 'computed' || d.state === 'computed_chart_relative'
        ? ('computed' as const)
        : d.state === 'not_in_corpus' || d.state === 'unknown_kind'
          ? ('not_in_corpus' as const)
          : ('honest_empty' as const),
    reason:
      d.state === 'computed_chart_relative'
        ? 'computed chart-relative at query time against the chart\'s own janma-nakṣatra fact — ' +
          'NOT claimed against the global census row panchangika/nakshatra_tara_bala, which ' +
          'correctly stays not_computed because a global table cannot hold a chart-personal value'
        : d.reason,
    ...(d.chart_fact_id !== undefined ? { chart_fact_id: d.chart_fact_id } : {}),
  }))

  if (!substrate.lattice_available) {
    entries.push({
      concept: 'lattice_substrate',
      state: 'honest_empty',
      reason: substrate.unavailable_reason ?? 'the muhūrta lattice payload could not be read for this call',
      chart_fact_id: null,
    })
  }
  if (!paddhati.available) {
    entries.push({
      concept: 'paddhati_profile',
      state: 'honest_empty',
      reason:
        paddhati.unavailable_reason ??
        'kala_paddhati_profile could not be read; residence constraints fell back to the corpus ' +
        'default convention and say so',
      chart_fact_id: null,
    })
  }
  if (!chartRel.available) {
    entries.push({
      concept: 'chart_relative_substrate',
      state: 'honest_empty',
      reason: chartRel.unavailable_reason ?? 'the chart\'s janma-nakṣatra fact could not be read',
      chart_fact_id: null,
    })
  }
  return entries
}

// ── Per-kind compilation ────────────────────────────────────────────────────

interface CompileArgs {
  kind: SkyPatternConstraintKind
  body: unknown
  rowsByFamily: Map<string, LatticeFactorRow[]>
  census: FactorCensusRow[]
  paddhati: PaddhatiResolution
  chartRel: ChartRelativeSubstrate
  principal: Principal
}

interface CompiledConstraint {
  disposition: SkyPatternConstraintDisposition
  intervals: Interval[]
  mode: 'require' | 'exclude'
}

function dropped(
  kind: string,
  key: string,
  state: ConstraintDispositionState,
  reason: string,
  family: string | null = null,
): CompiledConstraint {
  return {
    disposition: {
      kind,
      key,
      state,
      factor_family: family,
      reason,
      dropped_from_conjunction: true,
      matched_atom_count: 0,
    },
    intervals: [],
    mode: 'require',
  }
}

async function compileConstraint(args: CompileArgs): Promise<CompiledConstraint> {
  const { kind, body, rowsByFamily, census, paddhati, chartRel } = args

  switch (kind) {
    case 'planet_state': {
      const b = (body ?? {}) as { body?: string; in?: Record<string, unknown> }
      const wantsHoraLord = b.in?.['hora_lord'] === true
      const key = `planet_state:${b.body ?? '?'}${wantsHoraLord ? ':hora_lord' : ''}`
      if (!wantsHoraLord) {
        return dropped(
          kind,
          key,
          'not_computed',
          'the only planet_state predicate with a chart-independent lattice family at this build ' +
            'tier is `in: { hora_lord: true }` (factor_family=hora). Other planet_state predicates ' +
            '(sign, dignity, retrogression at an instant) have no materialized family and are ' +
            'DROPPED from the conjunction and reported, never silently skipped.',
        )
      }
      const rows = rowsByFamily.get('hora') ?? []
      if (rows.length === 0) {
        const c = censusDisposition(census, 'hora_lord')
        return dropped(
          kind,
          key,
          c?.disposition === 'computed' ? 'not_computed' : 'not_in_corpus',
          'no `hora` lattice atoms exist in the searched window. The family is emitted by ' +
            'bg_muhurta_lattice.py (migration 530) but bg_muhurta_lattice is a bg_* L0 global asset ' +
            'built ONLY by an explicit super-admin L0 trigger — an unbuilt or not-yet-extended ' +
            'lattice is honestly empty here, never a fabricated match.',
          'hora',
        )
      }
      const wanted = (b.body ?? '').trim()
      const resolved = await resolveGrahaName(wanted, args.principal)
      if (!resolved.canonical) {
        return dropped(
          kind,
          key,
          'not_computed',
          `the graha name '${wanted}' could not be resolved against brahma_ontology ` +
            `(${resolved.reason ?? 'no reason given'}). Guessing an alias here would be a B.10 ` +
            'fabrication, so the constraint is dropped and reported.',
          'hora',
        )
      }
      const matched = rows.filter(
        (r) => String((r.detail as { lord?: unknown } | null)?.lord ?? '').toLowerCase() === resolved.canonical!.toLowerCase(),
      )
      return {
        disposition: {
          kind,
          key,
          state: 'computed',
          factor_family: 'hora',
          reason: null,
          dropped_from_conjunction: false,
          matched_atom_count: matched.length,
        },
        intervals: matched.map(rowInterval).filter((i): i is Interval => i !== null),
        mode: 'require',
      }
    }

    case 'panchanga':
    case 'panchanga_not': {
      const b = (body ?? {}) as Record<string, unknown>
      const limb = Object.keys(b)[0] ?? '?'
      const key = `${kind}:${limb}`
      const wantedRaw = b[limb]
      const wanted = (Array.isArray(wantedRaw) ? wantedRaw : [wantedRaw]).map((v) =>
        String(v).trim().toLowerCase().replace(/[\s-]+/g, ''),
      )

      // The fixture's `karana NOT IN [vishti]` resolves against the ALREADY
      // materialized combination_yoga/bhadra span — the karana family itself is a
      // NAMED deferral (census: panchangika/karana_lattice_family), and this
      // mapping is the reason that deferral does not block the fixture.
      const family =
        limb === 'karana'
          ? 'combination_yoga'
          : limb === 'vara' || limb === 'nakshatra' || limb === 'tithi'
            ? limb
            : null

      if (family === null) {
        return dropped(
          kind,
          key,
          'not_in_corpus',
          `pañcāṅga limb '${limb}' has no materialized lattice family. Materialized families are ` +
            'vara, nakshatra, tithi (migration 530) plus the vishti/bhadra karana span under ' +
            'combination_yoga. nityayoga and the remaining ten karanas are NAMED deferrals in ' +
            'bg_muhurta_factor_census (panchangika/nityayoga_lattice_family, ' +
            'panchangika/karana_lattice_family) — dropped from the conjunction and reported here, ' +
            'per the design §6.2 precedence rule.',
        )
      }

      const rows = rowsByFamily.get(family) ?? []
      if (rows.length === 0) {
        return dropped(
          kind,
          key,
          'not_computed',
          `no '${family}' lattice atoms exist in the searched window (the L0 lattice is unbuilt or ` +
            'not yet extended to this family in this environment). Honestly empty, never a ' +
            'fabricated match.',
          family,
        )
      }

      const matched = rows.filter((r) => {
        const factorKey = r.factor_key.toLowerCase()
        const detailName = String((r.detail as { name?: unknown } | null)?.name ?? '').toLowerCase().replace(/[\s-]+/g, '_')
        return wanted.some((w) => factorKey === w || detailName === w || factorKey.startsWith(w))
      })

      return {
        disposition: {
          kind,
          key,
          state: 'computed',
          factor_family: family,
          reason: null,
          dropped_from_conjunction: false,
          matched_atom_count: matched.length,
        },
        intervals: matched.map(rowInterval).filter((i): i is Interval => i !== null),
        mode: kind === 'panchanga_not' ? 'exclude' : 'require',
      }
    }

    case 'residence': {
      const b = (body ?? {}) as { kind?: string; state?: string; per?: string }
      const key = `residence:${b.kind ?? '?'}`
      if ((b.kind ?? '') !== 'agnivasa') {
        return dropped(
          kind,
          key,
          'not_in_corpus',
          `residence kind '${b.kind}' has no rule table in the corpus. Only agnivāsa is ` +
            'materialized (bg_muhurta_lattice factor_family=agnivasa); śiva-vāsa in particular is ' +
            'recorded not_in_corpus in bg_muhurta_factor_census (rite_residence/shiva_vasa) as an ' +
            'ingestion work item — never improvised here.',
        )
      }
      const rows = rowsByFamily.get('agnivasa') ?? []
      if (rows.length === 0) {
        return dropped(kind, key, 'not_computed', 'no agnivāsa lattice atoms in the searched window.', 'agnivasa')
      }

      // The OPERATIVE convention comes from the paddhati profile when available;
      // ADJUDICATION-8's own row A is the corpus default (tithi-element,
      // pṛthvī-favourable). A `declared_not_computed` convention NEVER enters
      // grading (rail 2) — `paddhati.operative` already excludes it.
      const usingProfile = b.per === 'paddhati_profile' && paddhati.available && paddhati.operative.length > 0
      const favourableElements = ['prithvi']
      const wantFavourable = (b.state ?? 'favorable') === 'favorable'
      const matched = rows.filter((r) => {
        const el = String((r.detail as { element?: unknown } | null)?.element ?? '').toLowerCase()
        const isFav = favourableElements.includes(el)
        return wantFavourable ? isFav : !isFav
      })

      // ADJUDICATION-17: Convention (B) served as a SECOND, INFORMATIONAL voice for the
      // SAME atoms `matched` above already resolved for Convention (A) — computed from
      // `matched`, never fed back into it. `favourableElements` above is Convention (A)'s
      // hard gate and stays hardcoded by design; this array cannot change which atoms
      // matched or how `mode: 'require'` below is honoured.
      const agnivasa_convention_b_voices = buildAgnivasaConventionBVoices(matched, paddhati.operative)

      return {
        disposition: {
          kind,
          key,
          state: 'computed',
          factor_family: 'agnivasa',
          reason: usingProfile
            ? null
            : 'resolved against the CORPUS DEFAULT agnivāsa convention (tithi-element, ' +
              'pṛthvī-favourable) because ' +
              (paddhati.available
                ? 'the chart\'s paddhati profile carries no computed agnivāsa convention'
                : 'kala_paddhati_profile could not be read for this call') +
              '. ' + paddhati.census_statement,
          dropped_from_conjunction: false,
          matched_atom_count: matched.length,
          agnivasa_convention_b_voices,
        },
        intervals: matched.map(rowInterval).filter((i): i is Interval => i !== null),
        mode: 'require',
      }
    }

    case 'kalam_not': {
      const wanted = (Array.isArray(body) ? body : [body]).map((v) => String(v).trim().toLowerCase())
      const key = `kalam_not:${wanted.join(',')}`
      const rows = rowsByFamily.get('kalam') ?? []
      if (rows.length === 0) {
        return dropped(kind, key, 'not_computed', 'no kālam lattice atoms in the searched window.', 'kalam')
      }
      const matched = rows.filter((r) => wanted.includes(r.factor_key.toLowerCase()))
      return {
        disposition: {
          kind,
          key,
          state: 'computed',
          factor_family: 'kalam',
          reason: null,
          dropped_from_conjunction: false,
          matched_atom_count: matched.length,
        },
        intervals: matched.map(rowInterval).filter((i): i is Interval => i !== null),
        mode: 'exclude',
      }
    }

    case 'chart_relative': {
      const b = (body ?? {}) as { kind?: string; not_in?: string[]; in?: string[] }
      const key = `chart_relative:${b.kind ?? '?'}`
      if ((b.kind ?? '') !== 'tara_bala') {
        return dropped(
          kind,
          key,
          'not_computed',
          `chart_relative kind '${b.kind}' is not implemented at this build tier. tara_bala is; ` +
            'chandrashtama and transit-over-natal-point are named work items. Dropped and reported.',
        )
      }
      if (!chartRel.available || !chartRel.janma_nakshatra) {
        return dropped(
          kind,
          key,
          'not_computed',
          chartRel.unavailable_reason ??
            'the chart\'s janma-nakṣatra fact could not be read, so tārā-bala cannot be evaluated. ' +
            'It is DROPPED and reported — never defaulted to "favourable", which would be a ' +
            'fabricated pass.',
        )
      }
      const nakRows = rowsByFamily.get('nakshatra') ?? []
      if (nakRows.length === 0) {
        return dropped(
          kind,
          key,
          'not_computed',
          'tārā-bala is a post-filter over `nakshatra` lattice atoms and none exist in the searched ' +
            'window. Note the two-scope disposition this constraint sits inside: the GLOBAL census ' +
            'row panchangika/nakshatra_tara_bala correctly stays not_computed (a global table ' +
            'cannot hold a chart-personal value); the query-time evaluation here is the computed ' +
            'half. Conflating the two breaks §N.5.',
          'nakshatra',
        )
      }

      const janmaId = nakshatraIdFromName(chartRel.janma_nakshatra, nakRows)
      if (janmaId === null) {
        return dropped(
          kind,
          key,
          'not_computed',
          `the chart's janma nakṣatra '${chartRel.janma_nakshatra}' (fact_id ` +
            `${chartRel.janma_nakshatra_fact_id}) could not be matched to a lattice nakṣatra atom's ` +
            'own canonical factor_id. Rather than guess an id, the constraint is dropped and reported.',
          'nakshatra',
        )
      }

      const excluded = (b.not_in ?? []).map((t) => t.trim().toLowerCase())
      const included = (b.in ?? []).map((t) => t.trim().toLowerCase())
      const matched = nakRows.filter((r) => {
        const fid = Number((r.detail as { factor_id?: unknown } | null)?.factor_id)
        if (!Number.isFinite(fid)) return false
        const tara = taraFor(janmaId, fid)
        if (included.length > 0) return included.includes(tara)
        return !excluded.includes(tara)
      })

      return {
        disposition: {
          kind,
          key,
          state: 'computed_chart_relative',
          factor_family: 'nakshatra',
          reason: null,
          chart_fact_id: chartRel.janma_nakshatra_fact_id,
          dropped_from_conjunction: false,
          matched_atom_count: matched.length,
        },
        intervals: matched.map(rowInterval).filter((i): i is Interval => i !== null),
        mode: 'require',
      }
    }

    case 'mutual_configuration':
    case 'transit_contact':
    case 'natal_yoga_activation': {
      const key = `${kind}:declared`
      return dropped(
        kind,
        key,
        'not_in_corpus',
        `'${kind}' is a frozen sky_pattern_spec v1 kind with NO chart-independent lattice family ` +
          'at this build tier (KIND_TO_FAMILY maps it to null). Per brief §4 no W4 lane may be built ' +
          'to REQUIRE sub-day transit precision, and a day-grade approximation of a transit contact ' +
          'inside an intra-day search would silently widen every candidate. Dropped from the ' +
          'conjunction and reported by name (design §6.2 precedence rule).',
        KIND_TO_FAMILY[kind],
      )
    }
  }
}

/** Match a janma-nakṣatra NAME to the canonical integer id carried by the
 *  lattice's own atoms. Deliberately reads the id off a real atom rather than
 *  keeping a name→id table here: that table would be exactly the hand-mapped
 *  correspondence ADJUDICATION-10 refused (B.10). */
function nakshatraIdFromName(name: string, rows: LatticeFactorRow[]): number | null {
  const norm = name.trim().toLowerCase().replace(/[\s-]+/g, '_')
  for (const r of rows) {
    const detailName = String((r.detail as { name?: unknown } | null)?.name ?? '')
      .trim().toLowerCase().replace(/[\s-]+/g, '_')
    if (detailName === norm || r.factor_key.toLowerCase() === norm) {
      const fid = Number((r.detail as { factor_id?: unknown } | null)?.factor_id)
      if (Number.isFinite(fid)) return fid
    }
  }
  return null
}
