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
  notInCorpusCoverage,
  noLeverPointer,
  pointerTo,
  type KalaEnvelope,
  type ArgumentReading,
  type QuestionFrame,
  type TriPlanePointers,
} from '../../lib/kala_envelope.js'
import { composeArgument } from '../../lib/argument_composer.js'

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
}

export interface KalaRitualParams {
  chart_id: string
  horizon?: string | null
  sky_pattern_spec?: unknown
  undertaking?: string | null
  question_frame?: QuestionFrame | null
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
}

export type KalaRitualResult = KalaRitualWrongView | KalaRitualResponse

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

export function buildKalaRitualStubReading(mode: KalaRitualMode, chartId: string): ArgumentReading {
  const modeLabel = mode === 'pattern_search' ? 'Mode 2 (pattern search)' : 'Mode 1 (opportunity scan)'
  return {
    thesis:
      `YAJÑA-SETU ${modeLabel} real computation has not been built for chart ${chartId} yet — ` +
      `this is the W0 facade shell wired to the shared kala envelope, serving an honest ` +
      `not-computed ledger ahead of the real engine at W4 (SHAD_DARSHANA_BRIEF_v2_0.md §3 W4, ` +
      `item 40; KALA_SUPREME_ELEVATION_v1_0.md §8).`,
    evidence: [],
    dissent: [],
    verdict: {
      statement: `No ${modeLabel.toLowerCase()} candidates have been computed for this chart yet.`,
      tier: 'unresolved',
    },
    falsifier: null,
  }
}

export function buildKalaRitualStubResponse(params: KalaRitualParams, mode: KalaRitualMode): KalaRitualResponse {
  const reading = buildKalaRitualStubReading(mode, params.chart_id)
  const composed = composeArgument(reading)
  const coverageConcept = mode === 'pattern_search' ? 'mode2_sky_pattern_search' : 'mode1_opportunity_scan_ranked_pairs'
  const coverageReason =
    mode === 'pattern_search'
      ? 'YAJÑA-SETU Mode 2 (coarse-to-fine sky-pattern search over the muhūrta lattice) lands at W4 — SHAD_DARSHANA_BRIEF_v2_0.md §3 W4, items 26/40. The declared sky_pattern_spec is accepted and echoed but not yet compiled or searched.'
      : 'YAJÑA-SETU Mode 1 (4-factor scoring: structural resonance × temporal intensity × election quality × rarity) lands at W4 — SHAD_DARSHANA_BRIEF_v2_0.md §3 W4, items 26/40.'

  const envelope = makeKalaEnvelope({
    reading,
    questionFrame: params.question_frame ?? null,
    fieldSnapshotId: buildFieldSnapshotIdStub({}),
    triPlane: {
      // item 40 (brief §14): kala_ritual_get's tri-plane wiring is a W5 planner-integration
      // task. Honest no_lever rather than a possibly-dangling pointer at W0 — see upaya.ts
      // for the identical reasoning (this is the SAME rail applied to the sibling facade).
      interpretation_ref: noLeverPointer(
        'kala_now_get (interpretation plane) is not yet wired to this facade — planner wiring lands at W5 (SHAD_DARSHANA_BRIEF_v2_0.md §3 W5).',
      ),
      prediction_ref: noLeverPointer(
        'kala_ahead_get (prediction plane) is not yet wired to this facade — planner wiring lands at W5; Mode-1 rows join the AHEAD digest starting W4 per Elevation §6 D4.',
      ),
      // ND-1 (ṢAḌ-DARŚANA W1 verify-reopen, 2026-07-30): was a bare `null` — worth naming
      // explicitly, because the ND-1 report cited kala_ritual_get as the facade that
      // "already correctly uses" the no_lever contract. That was only half true: this file
      // used noLeverPointer for the two planes it cannot serve, but still emitted a bare
      // null for its OWN plane, exactly like now/ahead/elect. Now consistent — see
      // ahead.ts's prediction_ref for the full rationale.
      intervention_ref: noLeverPointer(
        'kala_ritual_get IS the intervention plane (YAJÑA-SETU) — this response is itself the '
          + 'intervention surface, so there is no further lever to traverse to. Not a missing '
          + 'pointer: a terminal by construction.',
      ),
    },
    coverage: [notInCorpusCoverage(coverageConcept, coverageReason)],
    freshness: buildKalaFreshness({ ephemerisVersion: null, sweepBuildDate: null, fieldHash: null }),
    calibrationMaturity: noLelCalibrationMaturity(),
  })
  return { ...envelope, tool: 'kala_ritual_get', wrong_view: false, mode, composed_text: composed.full_text }
}

// ── The single entry point (detector runs FIRST, always) ──────────────────────────────

/**
 * The ONE function the tool handler below calls. Detector-first, unconditionally: a
 * Mode-3-shaped `params` NEVER reaches `determineRitualMode`/`buildKalaRitualStubResponse` —
 * there is no code path in this file that computes anything for an undertaking.
 */
export function buildKalaRitualResponse(params: KalaRitualParams): KalaRitualResult {
  if (isMode3ShapedRequest(params)) {
    // params.undertaking is guaranteed a non-blank string by isMode3ShapedRequest's own check.
    return buildMode3WrongViewResponse({ chart_id: params.chart_id, undertaking: params.undertaking as string })
  }
  const mode = determineRitualMode(params)
  return buildKalaRitualStubResponse(params, mode)
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

W0 STATUS (current build): this tool is a facade shell for Modes 1–2 — it serves an HONEST \
not_in_corpus coverage ledger (mode1_opportunity_scan_ranked_pairs / mode2_sky_pattern_search) \
naming exactly what is not yet computed and why. No ritual-opportunity or pattern-match row is \
fabricated. The real engine lands at ṢAḌ-DARŚANA wave W4 — call again after that wave closes \
for real content.

When to prefer: once real (post-W4), this is the entry point for "what auspicious combinations \
are coming" (Mode 1) or "when does this specific combination occur" (Mode 2) questions. For \
"when should I do X" (an undertaking), use kala_elect_get instead — always.`

// ── Registration ────────────────────────────────────────────────────────────────────

/**
 * Registers `kala_ritual_get` on the MCP server. Called from registry_bridge.ts's
 * `registerRegistryBridgeTools` — the ONE canonical registration site for this tool.
 */
export function registerKalaRitualGet(server: McpServer, _principal: Principal): void {
  server.tool(
    'kala_ritual_get',
    KALA_RITUAL_DESCRIPTION,
    KalaRitualInputShape,
    // eslint-disable-next-line @typescript-eslint/require-await -- matches the async tool-handler convention used across this MCP surface
    async ({ chart_id, horizon, sky_pattern_spec, undertaking, question_frame }) => {
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
      const response = buildKalaRitualResponse({
        chart_id,
        horizon: horizon ?? null,
        sky_pattern_spec,
        undertaking: undertaking ?? null,
        question_frame: question_frame ?? null,
      })
      return {
        content: [{ type: 'text' as const, text: JSON.stringify(response, null, 2) }],
      }
    },
  )
}
