/**
 * upaya.ts — ṢAḌ-DARŚANA W0.4: `kala_upaya_get`
 * (SHAD_DARSHANA_BRIEF_v2_0.md §0.4 / §2 file map / §3 W0.4 · item 26 UPĀYA-SETU).
 * ==========================================================================
 * W0 SCOPE (this file only builds the FACADE SHELL):
 *   `kala_upaya_get` is a capability, not one of the six views (KALA_SUPREME_ELEVATION_v1_0.md
 *   §8: "UPĀYA-SETU and YAJÑA-SETU share one spine: upāya repairs the weak; yajña amplifies
 *   the strong"). At W0 it computes NOTHING — the real PACT-linked diagnosis, alternate-
 *   routing search over the contender lattice, efficacy tiers, and auto-filed falsifiers all
 *   land at W4 (brief §3 W4, item 26; Elevation §6). This file wires the shared envelope
 *   (`lib/kala_envelope.ts`) + the shared prose engine (`lib/argument_composer.ts`) around an
 *   honest `not_in_corpus` coverage ledger for every concept the W4 build will fill in —
 *   never a fabricated diagnosis (CLAUDE.md B.10).
 *
 * Registration: `registerKalaUpayaGet` is called from `registry_bridge.ts`'s
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
  type KalaEnvelope,
  type ArgumentReading,
  type QuestionFrame,
} from '../../lib/kala_envelope.js'
import { composeArgument } from '../../lib/argument_composer.js'

// ── Input shape ──────────────────────────────────────────────────────────────────────

// E4 (Elevation §5) — question_frame mirrored locally as a zod shape. Not re-exported from
// kala_envelope.ts (that file defines the TS interface only, no zod dependency) — each W0
// facade defines its own copy of this small, stable shape rather than the shared lib taking
// on a zod dependency for eight call sites. See ritual.ts for the identical shape.
const QuestionFrameShape = {
  domain: z.string().optional().describe("e.g. 'career', 'marriage', 'health', 'wealth'."),
  entity: z.string().optional().describe("The specific undertaking/entity named, if any (free text)."),
  horizon: z.string().optional().describe("Caller-stated horizon, e.g. '90d', 'next 24 months' — not yet resolved to a window."),
  intent_verb: z.string().optional().describe("e.g. 'should_i', 'when_should_i', 'what_is'."),
  stakes: z.string().optional().describe('Free-text statement of what is at stake, if supplied.'),
  comparison_target: z.string().optional().describe("For CONTRAST-shaped questions: what to diff against."),
}

const KalaUpayaInputShape = {
  chart_id: z.string().uuid().describe('Chart UUID. Required — no default chart.'),
  question_frame: z
    .object(QuestionFrameShape)
    .optional()
    .describe(
      'Optional question_frame (Elevation §5 E4): domain/entity/horizon/intent_verb/stakes/comparison_target. The chart is always implicit (chart_id); this is the only per-question input.',
    ),
}

export interface KalaUpayaParams {
  chart_id: string
  question_frame?: QuestionFrame | null
}

export interface KalaUpayaResponse extends KalaEnvelope {
  tool: 'kala_upaya_get'
  composed_text: string
}

// ── Pure builders (unit-tested directly; no server/registration involved) ─────────────

/**
 * The W0 stub reading: an honest "not yet computed" argument, never a fabricated remedy
 * diagnosis. `verdict.tier: 'unresolved'` is the honest tier — neither `structural_prior` nor
 * `calibrated*` claims a computation that has not run.
 */
export function buildKalaUpayaReading(chartId: string): ArgumentReading {
  return {
    thesis:
      `UPĀYA-SETU (remedy diagnosis · alternate-routing search · efficacy tiers) has not been ` +
      `built for chart ${chartId} yet — this is the W0 facade shell wired to the shared kala ` +
      `envelope, serving an honest not-computed ledger ahead of the real engine at W4 ` +
      `(SHAD_DARSHANA_BRIEF_v2_0.md §3 W4, item 26; KALA_SUPREME_ELEVATION_v1_0.md §6).`,
    evidence: [],
    dissent: [],
    verdict: {
      statement: 'No remedy diagnosis has been computed for this chart yet.',
      tier: 'unresolved',
    },
    // Honest null — there is no open claim yet to falsify (nothing has been asserted about
    // this chart's remedies). Never invent a resolves_by date (B.10).
    falsifier: null,
  }
}

/**
 * Assembles the full `kala_upaya_get` envelope. Pure and deterministic (no I/O, no
 * generative call) — the ONE function the tool handler below calls.
 */
export function buildKalaUpayaResponse(params: KalaUpayaParams): KalaUpayaResponse {
  const reading = buildKalaUpayaReading(params.chart_id)
  const composed = composeArgument(reading)
  const envelope = makeKalaEnvelope({
    reading,
    questionFrame: params.question_frame ?? null,
    // Nothing was read from any substrate build (nothing is computed yet) — the honest
    // snapshot id is the documented "unknown" fallback, not a fabricated per-chart hash.
    fieldSnapshotId: buildFieldSnapshotIdStub({}),
    triPlane: {
      // item 40 (brief §14): kala_upaya_get's tri-plane wiring is a W5 planner-integration
      // task, not a W0 one. Pointing at kala_now_get/kala_ahead_get here would be a live
      // pointer to a tool this build cannot yet guarantee is registered — honest `no_lever`
      // instead of a possibly-dangling reference (never a silent omission either — B.10).
      interpretation_ref: noLeverPointer(
        'kala_now_get (interpretation plane) is not yet wired to this facade — planner wiring lands at W5 (SHAD_DARSHANA_BRIEF_v2_0.md §3 W5).',
      ),
      prediction_ref: noLeverPointer(
        'kala_ahead_get (prediction plane) is not yet wired to this facade — planner wiring lands at W5 (SHAD_DARSHANA_BRIEF_v2_0.md §3 W5).',
      ),
      // ND-1 (ṢAḌ-DARŚANA W1 verify-reopen, 2026-07-30): was a bare `null`. See ahead.ts's
      // prediction_ref for the full rationale — the campaign's own tri_plane_no_dead_end_gate.ts
      // already grades a bare null `WARN` ("not independently verifiable at v0"); an honest,
      // self-describing `no_lever` states the same fact in the shape the contract provides.
      intervention_ref: noLeverPointer(
        'kala_upaya_get IS the intervention plane (UPĀYA-SETU) — this response is itself the '
          + 'intervention surface, so there is no further lever to traverse to. Not a missing '
          + 'pointer: a terminal by construction.',
      ),
    },
    coverage: [
      notInCorpusCoverage(
        'pact_link_diagnosis',
        'UPĀYA-SETU PACT-linked diagnosis lands at W4 — SHAD_DARSHANA_BRIEF_v2_0.md §3 W4, item 26.',
      ),
      notInCorpusCoverage(
        'alternate_routing_search',
        'Alternate-routing search over the contender lattice depends on the lattice engine (item 36, W3) and lands with item 26 at W4.',
      ),
      notInCorpusCoverage(
        'efficacy_tiers',
        'Efficacy tiers + auto-filed falsifiers land at W4 — item 26; efficacy reporting E6 (KALA_SUPREME_ELEVATION_v1_0.md §6).',
      ),
    ],
    freshness: buildKalaFreshness({ ephemerisVersion: null, sweepBuildDate: null, fieldHash: null }),
    calibrationMaturity: noLelCalibrationMaturity(),
  })
  return { ...envelope, tool: 'kala_upaya_get', composed_text: composed.full_text }
}

// ── Tool description ────────────────────────────────────────────────────────────────

const KALA_UPAYA_DESCRIPTION = `\
What it does: The UPĀYA-SETU capability — remedy diagnosis for a weak/afflicted configuration \
in the chart, alternate-routing search across remedial paths, and efficacy tiers on prior \
interventions. Returns the elevated kala envelope (argument-shaped reading, 3-state coverage, \
freshness attestation, calibration_maturity, tri-plane pointers).

W0 STATUS (current build): this tool is a facade shell — it serves an HONEST not_in_corpus \
coverage ledger naming exactly what is not yet computed (pact_link_diagnosis, \
alternate_routing_search, efficacy_tiers) and why. No remedy diagnosis is fabricated. The real \
engine (PACT-linked diagnosis, contender-lattice alternate-routing, efficacy reporting) lands \
at ṢAḌ-DARŚANA wave W4 — call again after that wave closes for real content.

When to prefer: once real (post-W4), this is the entry point for "what remedy should I do about \
X" / "how do I address this weakness" questions — paired with kala_ritual_get for yajña/vrata \
options and kala_elect_get for the paired act-time when the remedy accompanies an undertaking.`

// ── Registration ────────────────────────────────────────────────────────────────────

/**
 * Registers `kala_upaya_get` on the MCP server. Called from registry_bridge.ts's
 * `registerRegistryBridgeTools` — the ONE canonical registration site for this tool.
 */
export function registerKalaUpayaGet(server: McpServer, _principal: Principal): void {
  server.tool(
    'kala_upaya_get',
    KALA_UPAYA_DESCRIPTION,
    KalaUpayaInputShape,
    // eslint-disable-next-line @typescript-eslint/require-await -- matches the async tool-handler convention used across this MCP surface
    async ({ chart_id, question_frame }) => {
      if (!chart_id) {
        return {
          content: [
            {
              type: 'text' as const,
              text: JSON.stringify({ error: 'chart_id is required', tool: 'kala_upaya_get' }, null, 2),
            },
          ],
          isError: true as const,
        }
      }
      const response = buildKalaUpayaResponse({ chart_id, question_frame: question_frame ?? null })
      return {
        content: [{ type: 'text' as const, text: JSON.stringify(response, null, 2) }],
      }
    },
  )
}
