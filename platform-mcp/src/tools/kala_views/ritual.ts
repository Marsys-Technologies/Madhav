/**
 * ritual.ts — ṢAḌ-DARŚANA W0.4: `kala_ritual_get`
 * (SHAD_DARSHANA_BRIEF_v2_0.md §0.4 / §2 file map / §3 W0.4 · items 38/40 · Elevation §8).
 * ==========================================================================================
 * THE CRITICAL RAIL THIS FILE IMPLEMENTS (quoted verbatim, binding):
 *
 *   "implements the Mode-3 routing rule (Elev §8) from day one: a Mode-3-shaped call returns
 *   `wrong_view` naming `kala_elect_get` plus the tri-plane pointer. No Mode-3 passthrough,
 *   proxy, or delegation to the muhūrta substrate ships in `kala_ritual_get` — at W0 or ever."
 *   — SHAD_DARSHANA_BRIEF_v2_0.md §0.4
 *
 * THE MODE-3 ROUTING RULE (KALA_SUPREME_ELEVATION_v1_0.md §8, binding, quoted in full):
 *   1. `kala_elect_get` is the sole server of Mode 3 (activity election: undertaking → act-time
 *      slate + paired preparatory rite, served as one answer).
 *   2. `kala_ritual_get` serves Modes 1–2 ONLY (opportunity scan / pattern search). It NEVER
 *      accepts an undertaking as its subject and NEVER emits an act-time slate. A Mode-3-shaped
 *      call arriving here returns an honest `wrong_view` state naming `kala_elect_get` as the
 *      correct surface, plus the tri-plane pointer to it — a redirect, never a passthrough,
 *      proxy, or internal delegation. No Mode-3 stub of any kind ships here, at W0 or ever.
 *   3. Planner routing follows the same split (a W5 concern — out of scope here).
 *   4. One engine underneath, regardless (§9 one-engine rule) — irrelevant to THIS file, which
 *      never calls that engine; it only detects and redirects.
 *
 * THE DETECTOR (this file's `isMode3ShapedRequest`): a request is Mode-3-shaped iff it carries
 * a non-blank `undertaking` field. `undertaking` is the literal word KALA_SUPREME_ELEVATION_v1_0
 * §8's mode table uses for Mode 3's "Given" column ("3 — ACTIVITY ELECTION | Given: undertaking
 * | Returns: ranked slate + the preparatory rite and ITS best time"). Modes 1 and 2's own
 * "Given" columns (`horizon`, a declared `sky_pattern_spec`) share NO field with Mode 3's
 * vocabulary — the input shape below has no field an undertaking could hide behind. The
 * detector runs FIRST, before any other branch, and short-circuits to the wrong_view response
 * with no other code path executed for that request (see `buildKalaRitualResponse`).
 *
 * W0 SCOPE for Modes 1–2 (this file also builds this facade shell): real Mode 1 (4-factor
 * opportunity scan) and Mode 2 (coarse-to-fine sky-pattern search) computation lands at W4
 * (brief §3 W4, item 40). At W0 this serves an honest `not_in_corpus` coverage row — never a
 * fabricated ritual-opportunity list (CLAUDE.md B.10).
 *
 * ══════════════════════════════════════════════════════════════════════════════
 * W4 (ṢAḌ-DARŚANA Lane R, item 40): MODES 1–2 ARE NOW REAL.
 *
 * ENTRY-POINT ORDER — BINDING, and this file now runs TWO detectors first, in a
 * FIXED order (KALA_W4_UPAYA_DESIGN_v1_0.md §3.4, ADJUDICATION-13):
 *
 *   (1) the §5.4 INDIVIDUALIZED-MORTALITY-WINDOW HARD EXCLUSION, then
 *   (2) the existing `isMode3ShapedRequest` Mode-3 detector.
 *
 * MORTALITY FIRST, because it withholds the OUTPUT ITSELF under every audience
 * tier, whereas the Mode-3 detector merely redirects to a surface that would
 * then have to run the mortality check anyway. Both are PURE and SYNCHRONOUS;
 * neither may be reordered after a fetch. `routeKalaRitualRequest` below is the
 * one function that encodes this order, and it is unit-tested directly.
 *
 * THE MODE-3 RULE GETS STRONGER AT W4, NOT WEAKER. ELECT gaining the rite half
 * (item 38's W4 half) is exactly what makes this redirect CORRECT rather than
 * merely disciplined — it now points at a surface that genuinely answers the
 * whole question.
 *
 * THE SOURCE-SCAN RAIL IN `ritual.test.ts` WAS NARROWED, NOT DELETED — see
 * DESIGN RULING R-2, recorded in that file's own header. The two patterns naming
 * the act-time-slate substrate (the muhūrta-finder tool, and the compute route)
 * are KEPT verbatim and permanently. They are deliberately NOT spelled out in
 * THIS file, because the rail scans this file's own source text — writing them
 * here, even inside a comment explaining the ban, would make the rail fire on
 * itself. The rule they encode is unchanged: this file naming either of them IS
 * the Mode-3 passthrough the routing rule forbids, at W4 or ever. Read the exact
 * patterns in `ritual.test.ts`. The generic I/O ban was replaced
 * by an ALLOWLIST — this file may reach the lattice ONLY through
 * `fetchLatticeSubstrate` (the frozen engine's own fetcher) and through Lane R's
 * two new libs. A direct `callPlatformPrimitive` call in THIS file remains a
 * FAIL; the allowed path is one hop through the shared engine, which is also
 * what enforces the ONE-ENGINE RULE at the import-graph level.
 *
 * Registration: `registerKalaRitualGet` is called from `registry_bridge.ts`'s
 * `registerRegistryBridgeTools` — ONE canonical registration for this tool, per brief §2.
 */
import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { Principal } from '../../types.js'
import {
  makeKalaEnvelope,
  noLelCalibrationMaturity,
  buildKalaFreshness,
  buildFieldSnapshotIdStub,
  computedCoverage,
  honestEmptyCoverage,
  notInCorpusCoverage,
  noLeverPointer,
  pointerTo,
  type KalaCoverageEntry,
  type KalaEnvelope,
  type ArgumentReading,
  type QuestionFrame,
  type TriPlanePointers,
} from '../../lib/kala_envelope.js'
import { composeArgument } from '../../lib/argument_composer.js'
// Lane R's two new libs + the frozen engine's own fetcher. These three imports
// ARE the allowlist DESIGN RULING R-2 narrowed the source-scan rail to.
import {
  buildMortalityExclusionRefusal,
  detectMortalityExclusion,
  searchSkyPattern,
  type MortalityExclusionRefusal,
  type SkyPatternSearchResult,
  type SkyPatternSpec,
} from '../../lib/kala_sky_pattern.js'
import {
  scoreMode1Opportunities,
  type ActivityClass,
  type Mode1Result,
} from '../../lib/kala_ritual_resonance.js'
import { fetchLatticeSubstrate, type LatticeSubstrate } from '../../lib/kala_lattice_query.js'

// ── Input shape ──────────────────────────────────────────────────────────────────────

// Identical shape to upaya.ts's copy — see that file's comment for why this is duplicated
// per-facade rather than added to kala_envelope.ts's zod surface (it has none by design).
const QuestionFrameShape = {
  domain: z.string().optional().describe("e.g. 'career', 'marriage', 'health', 'wealth'."),
  entity: z.string().optional().describe('The specific undertaking/entity named, if any (free text).'),
  horizon: z.string().optional().describe("Caller-stated horizon, e.g. '90d', 'next 24 months' — not yet resolved to a window."),
  intent_verb: z.string().optional().describe("e.g. 'should_i', 'when_should_i', 'what_is'."),
  stakes: z.string().optional().describe('Free-text statement of what is at stake, if supplied.'),
  comparison_target: z.string().optional().describe('For CONTRAST-shaped questions: what to diff against.'),
}

// Elevation §8 Mode-2 sky_pattern_spec schema sketch (v0). W0 accepts and echoes the shape;
// it does NOT compile or search it yet (that is the W4 build). Kept loose (z.record) because
// the constraint-kind enum (planet_state · mutual_configuration · chart_relative · panchanga ·
// panchanga_not · residence · kalam_not · transit_contact · natal_yoga_activation) is owned by
// the W4 designer, not this W0 facade — over-specifying it here would just have to be redone.
const SkyPatternConstraintShape = z.record(z.string(), z.unknown())
const SkyPatternSpecShape = z
  .object({
    all: z.array(SkyPatternConstraintShape).optional().describe('Conjunction of constraints.'),
    any: z.array(SkyPatternConstraintShape).optional().describe('Disjunction of constraints.'),
    horizon: z.object({ months: z.number().int().positive().optional() }).optional(),
  })
  .describe('Elevation §8 Mode-2 sky_pattern_spec v0 (schema sketch) — accepted/echoed at W0, compiled/searched at W4.')

const KalaRitualInputShape = {
  chart_id: z.string().uuid().describe('Chart UUID. Required — no default chart.'),
  // Mode 1 (OPPORTUNITY SCAN): "Given: horizon."
  horizon: z.string().optional().describe("Mode 1 (opportunity scan): the horizon to search, e.g. '90d', '24m'. Ignored if sky_pattern_spec or undertaking is also present."),
  // Mode 2 (PATTERN SEARCH): "Given: declared sky-combination."
  sky_pattern_spec: SkyPatternSpecShape.optional(),
  // Mode 3 marker — kala_ritual_get NEVER serves this; supplying it triggers the wrong_view
  // redirect to kala_elect_get. See the file header for why this exact field is the detector.
  undertaking: z
    .string()
    .optional()
    .describe(
      "DO NOT USE to request an act-time slate — kala_ritual_get never serves undertakings. Naming an undertaking here (e.g. 'sign the contract', 'get married') is Mode 3 (activity election), served EXCLUSIVELY by kala_elect_get; this field exists only so the router can detect a misrouted Mode-3 call and redirect honestly.",
    ),
  question_frame: z.object(QuestionFrameShape).optional().describe('Optional question_frame (Elevation §5 E4).'),
  activity_class: z
    .enum([
      'vivah', 'griha_pravesh', 'vyapara', 'yatra', 'property_purchase',
      'mantra_initiation', 'upaya_ritual', 'sadhana_initiation',
    ])
    .optional()
    .describe(
      "Mode 1 only: which bg_muhurta_activity_rules class to grade windows against. Default " +
      "'upaya_ritual'. Closed vocabulary — the same eight classes the rule table's own CHECK admits.",
    ),
  limit: z.number().int().min(1).max(50).optional().describe('Mode 1 only: max ranked (window, rite) pairs. Default 10.'),
}

export interface KalaRitualParams {
  chart_id: string
  horizon?: string | null
  sky_pattern_spec?: unknown
  undertaking?: string | null
  question_frame?: QuestionFrame | null
  /** Mode 1 (W4): which `bg_muhurta_activity_rules` class to grade against.
   *  Defaults to `upaya_ritual` — the class whose own name IS "remedial rite".
   *  Never inferred from free text (that would be a guess dressed as a rule). */
  activity_class?: string | null
  /** Mode 1 (W4): max ranked (window, rite) pairs to return. */
  limit?: number | null
}

export type KalaRitualMode = 'opportunity_scan' | 'pattern_search'

/** The honest Mode-3 redirect. Deliberately NOT a `KalaEnvelope` — it carries no reading, no
 *  coverage, no candidate data of any kind, because none was computed and none was attempted
 *  (the detector short-circuits before any Mode-1/2 logic runs). `wrong_view: true` plus
 *  `correct_surface`/`tri_plane.intervention_ref` both name `kala_elect_get`, satisfying the
 *  brief's "returns wrong_view naming kala_elect_get plus the tri-plane pointer" verbatim. */
export interface KalaRitualWrongView {
  tool: 'kala_ritual_get'
  wrong_view: true
  mode_detected: 'activity_election'
  reason: string
  correct_surface: 'kala_elect_get'
  tri_plane: TriPlanePointers
}

export interface KalaRitualResponse extends KalaEnvelope {
  tool: 'kala_ritual_get'
  wrong_view: false
  mode: KalaRitualMode
  composed_text: string
  /** Mode 2 only — the compiled search result. `null` in Mode 1. */
  pattern_search: SkyPatternSearchResult | null
  /** Mode 1 only — the ranked (window, rite) pairs. `null` in Mode 2. */
  opportunities: Mode1Result | null
  /** §N.6 serving density: the paddhati divergence block, served alongside the
   *  operative convention so a caller can never read "one convention computed"
   *  as "the native's lineage convention". */
  paddhati_divergence: { state: string; reason: string } | null
}

export type KalaRitualResult = KalaRitualWrongView | KalaRitualResponse | MortalityExclusionRefusal

// ── The detector-order router (PURE, SYNCHRONOUS, unit-tested directly) ────────

export type KalaRitualRoute =
  | { route: 'mortality_withheld'; refusal: MortalityExclusionRefusal }
  | { route: 'mode3_redirect'; response: KalaRitualWrongView }
  | { route: 'compute'; mode: KalaRitualMode }

/**
 * THE ENTRY-POINT ORDER, encoded once (design §3.4 / ADJUDICATION-13):
 *   (1) §5.4 mortality hard exclusion — withholds the OUTPUT, every tier.
 *   (2) Mode-3 detector — redirects to kala_elect_get.
 *   (3) otherwise compute.
 *
 * **PURE and SYNCHRONOUS by construction.** Both detectors it calls are pure and
 * synchronous, so this function is structurally incapable of awaiting I/O and
 * cannot be reordered after a fetch by a later refactor. A test asserts it is
 * not an AsyncFunction — that assertion is the guarantee, not a style check.
 */
export function routeKalaRitualRequest(params: KalaRitualParams): KalaRitualRoute {
  // (1) MORTALITY FIRST. Not a disclosure tier, not conditioned on filing.
  const mortality = detectMortalityExclusion(params)
  if (mortality.excluded) {
    return { route: 'mortality_withheld', refusal: buildMortalityExclusionRefusal(mortality) }
  }
  // (2) Mode-3 detector, unchanged from W0.
  if (isMode3ShapedRequest(params)) {
    return {
      route: 'mode3_redirect',
      response: buildMode3WrongViewResponse({
        chart_id: params.chart_id,
        undertaking: params.undertaking as string,
      }),
    }
  }
  // (3) compute.
  return { route: 'compute', mode: determineRitualMode(params) }
}

// ── The Mode-3 detector (unit-tested directly) ─────────────────────────────────────────

/**
 * True iff `params` is Mode-3-shaped: a non-blank `undertaking`. This is the ENTIRE detector —
 * deliberately a single, simple, exhaustively-testable condition rather than a heuristic, so
 * the CI Mode-3 single-route assertion (brief §2 CI list; Elevation §8 clause 4) and this
 * file's own routing logic can never disagree about what counts as Mode-3-shaped.
 */
export function isMode3ShapedRequest(params: { undertaking?: string | null }): boolean {
  return typeof params.undertaking === 'string' && params.undertaking.trim().length > 0
}

/**
 * Builds the wrong_view redirect. Pure, synchronous, no I/O — proof by construction that no
 * passthrough/proxy/delegation to the muhūrta substrate (or to kala_elect_get itself) happens:
 * this function never calls anything, it only describes where the caller should go.
 */
export function buildMode3WrongViewResponse(params: { chart_id: string; undertaking: string }): KalaRitualWrongView {
  return {
    tool: 'kala_ritual_get',
    wrong_view: true,
    mode_detected: 'activity_election',
    reason:
      `kala_ritual_get serves YAJÑA-SETU Modes 1–2 only (opportunity scan / pattern search). ` +
      `The supplied 'undertaking' field ("${params.undertaking}") names Mode 3 (activity ` +
      `election: undertaking → act-time slate + paired preparatory rite), which is served ` +
      `EXCLUSIVELY by kala_elect_get per the Mode-3 routing rule ` +
      `(KALA_SUPREME_ELEVATION_v1_0.md §8, clauses 1–2). No Mode-3 passthrough, proxy, or ` +
      `delegation is implemented in kala_ritual_get, by design, at W0 or ever — call ` +
      `kala_elect_get directly with this undertaking instead.`,
    correct_surface: 'kala_elect_get',
    tri_plane: {
      interpretation_ref: noLeverPointer('wrong_view redirect — no interpretive content is served by this response.'),
      prediction_ref: noLeverPointer('wrong_view redirect — no predictive content is served by this response.'),
      intervention_ref: pointerTo(
        'kala_elect_get',
        'Mode 3 (activity election): serves the act-time slate AND the paired preparatory rite with its own best time, as one answer.',
      ),
    },
  }
}

// ── Modes 1–2 (honest W0 stub; no wrong_view) ──────────────────────────────────────────

/** Mode is determined ONLY after Mode-3 is ruled out. A declared `sky_pattern_spec` selects
 *  Mode 2 (pattern search); its absence defaults to Mode 1 (opportunity scan) — the honest
 *  default for "Given: horizon" when no horizon was even supplied either (W0 has no live
 *  scan to run regardless of horizon presence). */
export function determineRitualMode(params: { sky_pattern_spec?: unknown }): KalaRitualMode {
  return params.sky_pattern_spec != null ? 'pattern_search' : 'opportunity_scan'
}


// ── Modes 1–2: REAL (W4, item 40) ─────────────────────────────────────────────────────

/** Resolve the Mode-1 activity class. `upaya_ritual` is the honest default for a
 *  YAJÑA-SETU opportunity scan: it is the `bg_muhurta_activity_rules` class whose
 *  own name IS "remedial rite". Never inferred from free text. */
function resolveActivityClass(params: KalaRitualParams): ActivityClass {
  const named = (params.activity_class ?? '').trim() as ActivityClass
  return named.length > 0 ? named : 'upaya_ritual'
}

/** Parse a caller horizon string into a UTC window. Deliberately conservative:
 *  an unparseable horizon falls back to 90 days and the response SAYS SO in
 *  coverage — never silently reinterpreted as something else. */
export function resolveHorizon(horizon: string | null | undefined, now: Date = new Date()): {
  start_utc: string
  end_utc: string
  months: number
  parsed: boolean
} {
  const raw = (horizon ?? '').trim().toLowerCase()
  let days = 90
  let parsed = false
  const m = /^(\d+)\s*(d|day|days|m|mo|month|months|y|yr|year|years)$/.exec(raw)
  if (m) {
    const n = Number(m[1])
    const unit = m[2]!
    days = unit.startsWith('d') ? n : unit.startsWith('y') ? n * 365 : n * 30
    parsed = true
  }
  const start = new Date(now.getTime())
  const end = new Date(now.getTime() + days * 86_400_000)
  return {
    start_utc: start.toISOString(),
    end_utc: end.toISOString(),
    months: Math.max(1, Math.round(days / 30)),
    parsed,
  }
}

function buildMode2Reading(chartId: string, result: SkyPatternSearchResult): ArgumentReading {
  const n = result.candidates.length
  const thesis =
    n > 0
      ? `The declared sky pattern occurs ${n} time(s) in the searched horizon for chart ${chartId}, ` +
        `at ${result.precision.regime} precision (${result.precision.basis}).`
      : `The declared sky pattern does not occur in the searched horizon for chart ${chartId}. ` +
        result.gap_report.statement
  return {
    thesis,
    evidence: result.candidates.slice(0, 3).map((c) => ({
      claim: `${c.start_utc} → ${c.end_utc} satisfies every evaluable constraint (${c.binding_families.join(', ') || 'no binding family'})`,
      // §N.5: these are LATTICE ATOM ids, inherited not recomputed. They are not
      // chart_facts fact_ids, so they go in the claim text and authority_basis
      // rather than being mislabelled as fact_ids.
      fact_ids: [],
      strength: 'strong' as const,
    })),
    dissent: result.gap_report.constraints_evaluated
      .filter((d) => d.dropped_from_conjunction)
      .slice(0, 3)
      .map((d) => ({
        claim: `${d.key} was DROPPED from the conjunction (${d.state}): ${d.reason ?? 'no reason recorded'}`,
        fact_ids: [],
        source: 'sky_pattern_spec constraint compiler (drop-and-report precedence rule)',
      })),
    verdict:
      n > 0
        ? { statement: `Elect within ${result.candidates[0]!.start_utc} → ${result.candidates[0]!.end_utc} for the declared pattern.`, tier: 'structural_prior' as const }
        : {
            statement:
              result.gap_report.next_occurrence_state === 'found'
                ? `The pattern next occurs at ${result.gap_report.next_occurrence!.start_utc}, beyond the searched horizon.`
                : `The pattern does not occur within the scan ceiling (${result.gap_report.next_occurrence_state}).`,
            tier: 'structural_prior' as const,
          },
    falsifier:
      n > 0
        ? {
            statement:
              'if any dropped constraint is later materialized and this window fails it, this candidate is withdrawn — ' +
              'the constraints that were dropped are named in gap_report.constraints_evaluated',
            resolves_by: result.candidates[0]!.end_utc.slice(0, 10),
          }
        : null,
  }
}

function buildMode1Reading(chartId: string, result: Mode1Result): ArgumentReading {
  const top = result.opportunities[0]
  return {
    thesis: top
      ? `${result.opportunities.length} ritual opportunity/ies are available for chart ${chartId} in the ` +
        `searched horizon; the strongest is ${top.window.start_utc} → ${top.window.end_utc} ` +
        `(composite ${top.score_vector.composite ?? 'not scored'} over ` +
        `${top.score_vector.factors_present.length} present factor(s): ${top.score_vector.factors_present.join(', ') || 'none'}).`
      : `No ritual opportunity could be scored for chart ${chartId} in the searched horizon.`,
    evidence: result.opportunities.slice(0, 3).map((o) => ({
      claim:
        `${o.window.start_utc} → ${o.window.end_utc}: ${o.rite.rite_class ?? 'rite'} for ` +
        `${o.rite.planet ?? 'unnamed graha'} (${o.rite.citation ?? 'uncited — not offered as a prescription'})`,
      fact_ids: [],
      strength: (o.score_vector.composite ?? 0) >= 0.7 ? ('strong' as const) : ('moderate' as const),
    })),
    dissent: [],
    verdict: top
      ? { statement: `Perform the paired rite within ${top.window.start_utc} → ${top.window.end_utc}.`, tier: 'structural_prior' as const }
      : {
          statement:
            'No opportunity is asserted. Every absent score factor is named with its reason in ' +
            'score_vector.factors_absent — none is imputed.',
          tier: 'unresolved' as const,
        },
    falsifier: null,
  }
}

function commonTriPlane(): TriPlanePointers {
  return {
    interpretation_ref: noLeverPointer(
      'kala_now_get (interpretation plane) is not yet wired to this facade — planner wiring lands at W5 (SHAD_DARSHANA_BRIEF_v2_0.md §3 W5).',
    ),
    prediction_ref: pointerTo(
      'kala_ahead_get',
      'Mode-1 ritual-opportunity rows join the AHEAD 90-day digest from W4 (Elevation §6 D4) — this is the predictive continuation of the rows served here.',
    ),
    intervention_ref: noLeverPointer(
      'kala_ritual_get IS the intervention plane (YAJÑA-SETU) — this response is itself the '
        + 'intervention surface, so there is no further lever to traverse to. Not a missing '
        + 'pointer: a terminal by construction.',
    ),
  }
}

/**
 * The REAL Mode-1/2 handler. Async by necessity (it reads substrate), which is
 * exactly why the detector-order router above is a separate, synchronous
 * function: the guarantee is that BOTH detectors ran before this function was
 * ever entered.
 */
export async function handleKalaRitualGet(
  params: KalaRitualParams,
  principal: Principal,
): Promise<KalaRitualResult> {
  const route = routeKalaRitualRequest(params)
  if (route.route === 'mortality_withheld') return route.refusal
  if (route.route === 'mode3_redirect') return route.response

  const horizon = resolveHorizon(params.horizon)
  const coverage: KalaCoverageEntry[] = []
  if (!horizon.parsed && (params.horizon ?? '').trim().length > 0) {
    coverage.push(
      honestEmptyCoverage(
        'horizon_parse',
        `the supplied horizon '${params.horizon}' could not be parsed; the search fell back to 90 days. ` +
          'Reported rather than silently reinterpreted.',
      ),
    )
  }

  let reading: ArgumentReading
  let patternSearch: SkyPatternSearchResult | null = null
  let opportunities: Mode1Result | null = null
  let paddhatiDivergence: KalaRitualResponse['paddhati_divergence'] = null

  if (route.mode === 'pattern_search') {
    const spec = (params.sky_pattern_spec ?? {}) as SkyPatternSpec
    const months = spec.horizon?.months ?? horizon.months
    const end = new Date(Date.parse(horizon.start_utc) + months * 30 * 86_400_000).toISOString()
    // Scan ceiling: 3× the horizon, so `next_occurrence` has somewhere to look and
    // `not_within_scan_ceiling` is distinguishable from `not_searched` (§N.8).
    const ceiling = new Date(Date.parse(horizon.start_utc) + months * 90 * 86_400_000).toISOString()
    patternSearch = await searchSkyPattern(
      {
        spec,
        chartId: params.chart_id,
        horizonStartUtc: horizon.start_utc,
        horizonEndUtc: end,
        scanCeilingUtc: ceiling,
        subjectLabel: 'declared sky pattern (YAJÑA-SETU Mode 2)',
      },
      principal,
    )
    reading = buildMode2Reading(params.chart_id, patternSearch)
    paddhatiDivergence = patternSearch.paddhati
      ? { state: patternSearch.paddhati.divergence.state, reason: patternSearch.paddhati.divergence.reason }
      : null
    for (const c of patternSearch.coverage) {
      coverage.push(
        c.state === 'computed'
          ? computedCoverage(c.concept)
          : c.state === 'not_in_corpus'
            ? notInCorpusCoverage(c.concept, c.reason ?? 'no reason recorded')
            : honestEmptyCoverage(c.concept, c.reason ?? 'no reason recorded'),
      )
    }
  } else {
    // Mode 1: the opportunity scan. The horizon is partitioned by the SAME lattice
    // atoms Mode 2 searches — one substrate read, via the frozen engine's fetcher.
    let substrate: LatticeSubstrate
    try {
      substrate = await fetchLatticeSubstrate(
        { start_utc: horizon.start_utc, end_utc: horizon.end_utc },
        principal,
      )
    } catch (err) {
      substrate = {
        lattice_rows: [], parihara_rules: [], census_rows: [],
        lattice_available: false, parihara_available: false, census_available: false,
        unavailable_reason: String(err),
      }
    }
    const windows = buildMode1Windows(substrate, horizon.start_utc, horizon.end_utc)
    opportunities = await scoreMode1Opportunities(
      {
        chartId: params.chart_id,
        activityClass: resolveActivityClass(params),
        windows,
        substrate,
        subjectLabel: 'ritual opportunity (YAJÑA-SETU Mode 1)',
        limit: params.limit ?? 10,
      },
      principal,
    )
    reading = buildMode1Reading(params.chart_id, opportunities)
    coverage.push(
      opportunities.opportunities.length > 0
        ? computedCoverage('mode1_opportunity_scan_ranked_pairs')
        : honestEmptyCoverage(
            'mode1_opportunity_scan_ranked_pairs',
            substrate.lattice_available
              ? 'the lattice was read but no auspicious combination-yoga span exists in the searched ' +
                `horizon (${horizon.start_utc} .. ${horizon.end_utc}), so no (window, rite) pair is asserted`
              : substrate.unavailable_reason ??
                'the muhūrta lattice payload could not be read for this call',
          ),
    )
    coverage.push(
      opportunities.activity_rules.available
        ? computedCoverage('rite_specific_activity_rule_join')
        : honestEmptyCoverage(
            'rite_specific_activity_rule_join',
            opportunities.activity_rules.unavailable_reason ?? 'bg_muhurta_activity_rules could not be read',
          ),
    )
    coverage.push(
      notInCorpusCoverage(
        'temporal_intensity_field_lambda',
        "the field's λ for the rite's domain needs kala_field_windows, which ka_kshetra has written " +
          'no rows to (the N_e critical path). The factor is DROPPED from the score product and the ' +
          'product renormalised over present factors — never imputed, never zero-filled.',
      ),
    )
  }

  const composed = composeArgument(reading)
  const envelope = makeKalaEnvelope({
    reading,
    questionFrame: params.question_frame ?? null,
    fieldSnapshotId: buildFieldSnapshotIdStub({
      paddhati_version: patternSearch?.paddhati?.version ?? null,
    }),
    triPlane: commonTriPlane(),
    coverage,
    freshness: buildKalaFreshness({ ephemerisVersion: null, sweepBuildDate: null, fieldHash: null }),
    calibrationMaturity: noLelCalibrationMaturity(),
  })

  return {
    ...envelope,
    tool: 'kala_ritual_get',
    wrong_view: false,
    mode: route.mode,
    composed_text: composed.full_text,
    pattern_search: patternSearch,
    opportunities,
    paddhati_divergence: paddhatiDivergence,
  }
}

/**
 * Mode 1's candidate windows: the AUSPICIOUS combination-yoga spans the lattice
 * already carries, clipped to the horizon. Selection over already-computed atoms
 * — this facade computes no window of its own (item 44 / ruling R-1).
 */
export function buildMode1Windows(
  substrate: LatticeSubstrate,
  startUtc: string,
  endUtc: string,
): { start_utc: string; end_utc: string; authority_basis: string[]; binding_families: string[] }[] {
  const s = Date.parse(startUtc)
  const e = Date.parse(endUtc)
  return substrate.lattice_rows
    .filter((r) => r.factor_family === 'combination_yoga')
    .filter((r) => String((r.detail as { strength?: unknown } | null)?.strength ?? '') === 'auspicious')
    .filter((r) => {
      const rs = Date.parse(r.start_utc)
      const re = Date.parse(r.end_utc)
      return !Number.isNaN(rs) && !Number.isNaN(re) && rs < e && re > s
    })
    .sort((a, b) => Date.parse(a.start_utc) - Date.parse(b.start_utc))
    .map((r) => ({
      start_utc: new Date(Math.max(Date.parse(r.start_utc), s)).toISOString(),
      end_utc: new Date(Math.min(Date.parse(r.end_utc), e)).toISOString(),
      authority_basis: [`${r.factor_family}/${r.factor_key}@${r.start_utc}`],
      binding_families: [r.factor_family],
    }))
}

// ── Tool description ────────────────────────────────────────────────────────────────

const KALA_RITUAL_DESCRIPTION = `\
What it does: The YAJÑA-SETU capability — Modes 1–2 ONLY. Mode 1 (opportunity scan, given a \
horizon) returns ranked (window, ritual) pairs: which auspicious combinations are coming and \
which yajña exploits each. Mode 2 (pattern search, given a declared sky_pattern_spec) returns \
the times a declared sky-combination occurs, graded. Returns the elevated kala envelope \
(argument-shaped reading, 3-state coverage, freshness attestation, calibration_maturity, \
tri-plane pointers).

MODE-3 ROUTING (binding, KALA_SUPREME_ELEVATION_v1_0.md §8): this tool NEVER accepts an \
undertaking and NEVER returns an act-time slate. Naming an undertaking (e.g. "when should I \
sign the contract, and what rite should I do first") is Mode 3 — call kala_elect_get instead, \
which serves the act-time slate AND the paired preparatory rite as one answer. A call that \
supplies the 'undertaking' field here returns an honest wrong_view response naming \
kala_elect_get, never a passthrough or a slate.

W4 STATUS (current build): Modes 1 and 2 are REAL. Mode 1 returns ranked (window, rite) pairs \
each carrying a FIVE-part score vector with EACH FACTOR'S OWN STATE — a factor that cannot be \
computed is reported not_computed with a reason and DROPPED from the product, which is then \
renormalised over the factors actually present. It is never imputed and never zero-filled, and \
factors_present/factors_absent name the split on every vector, so a 3-factor score can never be \
read as a 5-factor one. Mode 2 compiles a declared sky_pattern_spec v1 into exact interval \
arithmetic over the muhūrta lattice's own boundary atoms — no sampling interval exists inside \
which a satisfying window could hide — and returns a gap report naming the ELIMINATING \
constraint plus the pattern's next occurrence past the horizon (or an explicit \
not_within_scan_ceiling / not_searched, so an absent date is never ambiguous). Every rite served \
is a row that already exists in brahma_remedy_corpus, selected and cited; nothing is composed at \
serve time (B.10).

WITHHELD BY DESIGN: a request whose shape or substrate touches the span-of-life / death-timing \
question returns an honest refusal naming MACRO_PLAN §3.5.C and computes NOTHING — no window, \
no candidate, no diagnosis, because none was attempted. That exclusion is absolute across every \
audience tier and is not conditioned on filing. Ask about timing a rite, a remedy or an \
undertaking instead and the question is served in full.

When to prefer: this is the entry point for "what auspicious combinations are coming" (Mode 1) \
or "when does this specific combination occur" (Mode 2) questions. For "when should I do X" (an \
undertaking), use kala_elect_get instead — always.`

// ── Registration ────────────────────────────────────────────────────────────────────

/**
 * Registers `kala_ritual_get` on the MCP server. Called from registry_bridge.ts's
 * `registerRegistryBridgeTools` — the ONE canonical registration site for this tool.
 */
export function registerKalaRitualGet(server: McpServer, principal: Principal): void {
  server.tool(
    'kala_ritual_get',
    KALA_RITUAL_DESCRIPTION,
    KalaRitualInputShape,
    async ({ chart_id, horizon, sky_pattern_spec, undertaking, question_frame, activity_class, limit }) => {
      if (!chart_id) {
        return {
          content: [
            {
              type: 'text' as const,
              text: JSON.stringify({ error: 'chart_id is required', tool: 'kala_ritual_get' }, null, 2),
            },
          ],
          isError: true as const,
        }
      }
      const response = await handleKalaRitualGet(
        {
          chart_id,
          horizon: horizon ?? null,
          sky_pattern_spec,
          undertaking: undertaking ?? null,
          question_frame: question_frame ?? null,
          activity_class: activity_class ?? null,
          limit: limit ?? null,
        },
        principal,
      )
      return {
        content: [{ type: 'text' as const, text: JSON.stringify(response, null, 2) }],
      }
    },
  )
}
