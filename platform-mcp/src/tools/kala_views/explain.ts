/**
 * explain.ts — ṢAḌ-DARŚANA W0.4: `kala_explain_get` (SHAD_DARSHANA_BRIEF_v2_0.md §3 W0.4 ·
 * §2 file map; design authority KALA_SIX_VIEWS_DESIGN_v1_0.md §6 / v2_0.md §E "EXPLAIN").
 * ==========================================================================
 * VIEW 6 — EXPLAIN: "Why do you say that?"
 *
 * W0 SCOPE (thin facade over EXISTING substrate — no new computation, per brief §3 W0.4):
 * the v1.0 design's full EXPLAIN ("provenance graph materialized at build time... window →
 * predicates → signals → natal facts") needs the field-write provenance edges (item 11) that
 * do not exist until W2. What already exists TODAY that answers "why do you say that?" for a
 * temporal claim is `pact_query` (registry_bridge.ts) — the PACT protocol as one chained
 * investigation ("promise in the rashi → confirmation in the varga → activation in the dasha
 * → trigger in the transit"), which HALTS HONESTLY at the first denied stage and names it.
 * That halting stage IS v1.0 §6.2's "the weakest link — the least-attested edge, named
 * honestly" for this substrate: the stage the chain currently rests on. This facade wraps
 * `marsys://tool/L-PACT/pact_query` — the same capability `pact_query` calls — and re-serves
 * it through the elevated `kala_envelope.ts` shape.
 *
 * NOT YET BUILT (honestly flagged via coverage, never silently omitted per B.10):
 * the classical-citation join (item 11, chain link → śāstra passage, EXPLAIN's "pedagogy
 * mode"), the school-ledger / multi-system dissent object (Law 2, needs W3K's KP voice),
 * and the counterfactual mode (E6, "without the vedha this grades one tier higher").
 */

import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { Principal } from '../../types.js'
import {
  makeKalaEnvelope,
  buildFieldSnapshotIdStub,
  pointerTo,
  noLeverPointer,
  computedCoverage,
  honestEmptyCoverage,
  notInCorpusCoverage,
  buildKalaFreshness,
  noLelCalibrationMaturity,
  type ArgumentReading,
  type ArgumentEvidence,
  type KalaCoverageEntry,
  type TriPlanePointers,
  type KalaDensityContract,
  type QuestionFrame,
} from '../../lib/kala_envelope.js'
import { composeArgument } from '../../lib/argument_composer.js'
import { callKalaRegistryCap, unwrapKalaPayload, kalaBudgetedDualOutput, kalaErrorOutput } from './shared.js'

const AYANAMSHA_ALIAS: Record<string, string> = {
  lahiri: 'lahiri_chitrapaksha', LAHIRI: 'lahiri_chitrapaksha', Lahiri: 'lahiri_chitrapaksha',
  lahiri_chitrapaksha: 'lahiri_chitrapaksha', true_chitra: 'lahiri_chitrapaksha',
}
function resolveAyanamsha(id?: string): string { return id ? (AYANAMSHA_ALIAS[id] ?? id) : 'lahiri_chitrapaksha' }

const TOOL_NAME = 'kala_explain_get'
const CAPABILITY_URI = 'marsys://tool/L-PACT/pact_query'

const QuestionFrameSchema = z.object({
  domain: z.string().optional(),
  entity: z.string().optional(),
  horizon: z.string().optional(),
  intent_verb: z.string().optional(),
  stakes: z.string().optional(),
  comparison_target: z.string().optional(),
}).optional().describe(
  'Optional question frame (Elevation E4): {domain, entity, horizon, intent_verb, stakes, ' +
  'comparison_target}. The chart is always implicit. Echoed back verbatim in the envelope.',
)

type PactStatus =
  | 'denied_at_promise' | 'denied_at_confirmation' | 'denied_at_activation'
  | 'chain_pending_activation' | 'chain_incomplete_infra' | 'chain_complete'

const PACT_STATUS_VERDICT: Record<PactStatus, string> = {
  denied_at_promise:
    'This matter is not promised by the rashi checklist — the chain halts at PROMISE; no later stage can deliver what the rashi does not promise.',
  denied_at_confirmation:
    'The rashi\'s promise is not confirmed in the operative varga — the chain halts at CONFIRMATION.',
  denied_at_activation:
    'The promise is confirmed but has no dasha vehicle left to deliver it — the chain halts at ACTIVATION.',
  chain_pending_activation:
    'The promise is confirmed and a future dasha window carries it, but that window has not opened yet — TRIGGER is not yet reachable.',
  chain_incomplete_infra:
    'All four PACT stages were attempted, but TRIGGER could not be evaluated (ephemeris sidecar unreachable/empty) — an infrastructure gap, not a classical denial.',
  chain_complete:
    'The full PACT chain (promise → confirmation → activation → trigger) is intact as of the evaluation date.',
}

interface PactStage {
  stage?: string
  status?: string
  reason?: string
  dignities?: Array<{ fact_id?: string | null }>
  [k: string]: unknown
}

/** Labels the matter under investigation from pact_query's `about` block (falls back through
 *  label → domain → "bhava N" → a generic honest placeholder — never fabricated). */
function labelAbout(about: Record<string, unknown> | undefined): string {
  if (!about) return 'this matter'
  const label = about['label']
  if (typeof label === 'string' && label.trim()) return label
  const domain = about['domain']
  if (typeof domain === 'string' && domain.trim()) return domain
  const bhava = about['bhava']
  if (typeof bhava === 'number') return `bhava ${bhava}`
  return 'this matter'
}

/** Builds the ArgumentReading from the raw PACT `stages` + `pact_status` the underlying
 *  `pact_query` capability already computed. Pure assembly — no new chain evaluation. */
function buildReading(params: {
  stages: PactStage[]
  pactStatus: PactStatus | string
  aboutLabel: string
  asOfDate: string
}): ArgumentReading {
  const { stages, pactStatus, aboutLabel, asOfDate } = params
  const verdictStatement = PACT_STATUS_VERDICT[pactStatus as PactStatus]
    ?? `PACT status: ${pactStatus} (unrecognized status string — served verbatim, not fabricated).`

  const thesis = `Why for ${aboutLabel} as of ${asOfDate}: ${verdictStatement}`

  // One evidence row per stage actually attempted, in chain order — each carries the
  // stage's own reason sentence (already the most specific claim this substrate makes).
  // Only the CONFIRMATION stage's per-graha dignity rows carry a genuine fact_id at this
  // substrate tier (register_d10_pact.ts's `gradeGrahaInVarga`) — other stages' reasons are
  // NOT re-attributed to a fact_id we don't actually have (§N.7: never overclaim a citation).
  const evidence: ArgumentEvidence[] = stages.map((stage): ArgumentEvidence => {
    const factIds =
      stage.stage === 'CONFIRMATION' && Array.isArray(stage.dignities)
        ? (stage.dignities.map((d) => d.fact_id).filter((f): f is string => typeof f === 'string'))
        : []
    return {
      claim: `${stage.stage ?? 'stage'} (${stage.status ?? 'unknown'}): ${stage.reason ?? 'no reason recorded'}`,
      fact_ids: factIds,
    }
  })

  return {
    thesis,
    evidence,
    dissent: [],
    verdict: { statement: verdictStatement, tier: 'structural_prior' },
    falsifier: null,
  }
}

export function registerKalaExplainTool(server: McpServer, principal: Principal): void {
  server.tool(
    TOOL_NAME,
    'VIEW 6 — EXPLAIN ("why do you say that?"). Wraps the same PACT-protocol chained ' +
    'investigation pact_query calls (promise in the rashi → confirmation in the varga → ' +
    'activation in the dasha → trigger in the transit), re-served on the elevated kala_* ' +
    'envelope: an argument-shaped reading naming the causal chain, its weakest link (the ' +
    'stage the chain currently halts at or rests on — v1.0 §6.2\'s "least-attested edge, ' +
    'named honestly"), tri-plane pointers (a denied/pending chain points to kala_upaya_get ' +
    'for intervention diagnosis; a live/complete chain points to kala_elect_get), 3-state ' +
    'coverage (the field-write provenance graph / classical-citation join / counterfactual ' +
    'mode, items 11 and E6, are NOT yet built — honestly flagged, not silently omitted), ' +
    'freshness, and calibration_maturity (always the honest zero stub at W0). Pass `domain` ' +
    'or `bhava` exactly as judgment_query/pact_query accept — one is required. ' +
    '[ṢAḌ-DARŚANA W0.4]',
    {
      chart_id: z.string().uuid().describe('Chart UUID. Required.'),
      ayanamsha_id: z.string().optional().describe("Ayanamsha (default: 'lahiri_chitrapaksha')."),
      domain: z.string().optional().describe(
        'Life-domain name (judgment_query\'s shastra map): marriage/relationship/partnership, ' +
        'career/vocation, wealth/finance, health/vitality, progeny/children, education, ' +
        'spirituality. Takes precedence over `bhava` if both given.'),
      bhava: z.number().int().min(1).max(12).optional().describe(
        'Bhava (house) number 1-12. Required if `domain` is omitted.'),
      as_of_date: z.string().optional().describe('Date (YYYY-MM-DD) to evaluate ACTIVATION/TRIGGER as-of. Default: today.'),
      max_signals: z.number().int().min(1).max(50).optional().describe(
        'Forwarded to the PROMISE stage (judgment_query). Default 15, max 50.'),
      question_frame: QuestionFrameSchema,
    },
    async (params) => {
      const {
        chart_id, ayanamsha_id, domain, bhava, as_of_date, max_signals, question_frame,
      } = params as Record<string, unknown>

      if (!chart_id || typeof chart_id !== 'string') {
        return kalaErrorOutput(TOOL_NAME, 'chart_id is required')
      }
      if (!domain && bhava === undefined) {
        return kalaErrorOutput(TOOL_NAME, 'either `domain` or `bhava` is required')
      }

      try {
        const resolvedAyanamsha = resolveAyanamsha(ayanamsha_id as string | undefined)
        const raw = await callKalaRegistryCap(
          CAPABILITY_URI,
          {
            chart_id,
            ayanamsha_id: resolvedAyanamsha,
            ...(domain ? { domain } : {}),
            ...(bhava !== undefined ? { bhava } : {}),
            ...(as_of_date ? { as_of_date } : {}),
            ...(max_signals != null ? { max_signals } : {}),
          },
          principal,
        )
        const payload = unwrapKalaPayload(raw)
        const stages = Array.isArray(payload['stages']) ? (payload['stages'] as PactStage[]) : []
        const pactStatus = (payload['pact_status'] as PactStatus | string | undefined) ?? 'unknown'
        const about = (payload['about'] as Record<string, unknown> | undefined) ?? undefined
        const aboutLabel = labelAbout(about)
        const resolvedAsOfDate = (payload['as_of_date'] as string | undefined) ?? (as_of_date as string | undefined) ?? 'today'
        const factIdRefs = Array.isArray(payload['fact_id_refs']) ? (payload['fact_id_refs'] as string[]) : []
        const pactDrillPointers = Array.isArray(payload['drill_pointers']) ? payload['drill_pointers'] : []

        const reading = buildReading({ stages, pactStatus, aboutLabel, asOfDate: resolvedAsOfDate })

        const weakestLink = stages.length > 0
          ? (() => {
              const last = stages[stages.length - 1] as PactStage
              return { stage: last.stage ?? null, status: last.status ?? null, reason: last.reason ?? null }
            })()
          : null

        // A denied/pending chain routes to the intervention-leverage engine (UPĀYA-SETU is
        // exactly "this outcome is unlikely for me; what would raise its likelihood?"); a
        // live/complete chain routes to ELECT (timing the act inside an already-open window).
        const chainIsLive = pactStatus === 'chain_complete' || pactStatus === 'chain_pending_activation'
        const triPlane: TriPlanePointers = {
          // ND-1 (ṢAḌ-DARŚANA W1 verify-reopen, 2026-07-30): was a bare `null`. This reading
          // genuinely IS the interpretive/causal-chain ground for the claim it explains, but
          // see ahead.ts's prediction_ref for why a bare null is still the wrong SHAPE for
          // saying so — tri_plane_no_dead_end_gate.ts grades it `WARN`, an honest no_lever
          // `PASS`.
          interpretation_ref: noLeverPointer(
            'kala_explain_get IS the interpretation plane — this response is itself the '
              + 'interpretive/causal-chain ground for the claim it explains, so there is no '
              + 'further interpretive surface to traverse to. Not a missing pointer: a '
              + 'terminal by construction.',
          ),
          prediction_ref: pointerTo(
            'kala_ahead_get',
            'see the forward-looking windows for this domain/bhava once/while the chain is live.',
          ),
          intervention_ref: chainIsLive
            ? pointerTo('kala_elect_get', 'elect the best window inside this already-confirmed/pending chain.')
            : pointerTo('kala_upaya_get', `diagnose an intervention for the failing link named in weakest_link (${weakestLink?.stage ?? 'n/a'}).`),
        }

        const coverage: KalaCoverageEntry[] = [
          computedCoverage('pact_chain_promise_confirmation_activation_trigger'),
          honestEmptyCoverage(
            'dissent_multi_system_concurrence',
            'Law-2 concurrence/dissent across systems (e.g. the KP sub-lord voice) is not yet ' +
            'computed for this chain — lands W3K (item 18).',
          ),
          notInCorpusCoverage(
            'classical_citation_join',
            'field-write provenance edges + rule→classical-chunk citation join (item 11) are not ' +
            'yet built — chain reasons above are computed prose, not yet linked to specific ' +
            'śāstra passages (EXPLAIN\'s pedagogy mode, E6).',
          ),
          notInCorpusCoverage(
            'counterfactual_mode',
            'counterfactual mode ("without the vedha this grades one tier higher", E6) is not yet ' +
            'built — lands W2/W3.',
          ),
        ]

        const freshness = buildKalaFreshness({ ephemerisVersion: null, sweepBuildDate: null, fieldHash: null })

        const fieldSnapshotId = buildFieldSnapshotIdStub({
          chart_id,
          ayanamsha_id: resolvedAyanamsha,
          as_of_date: resolvedAsOfDate,
          domain: (domain as string | undefined) ?? null,
          bhava: bhava !== undefined ? String(bhava) : null,
        })

        const densityContract: KalaDensityContract = {
          paginated: false,
          facets: ['domain', 'bhava'],
          empty_reason: true,
        }

        const envelope = makeKalaEnvelope({
          reading,
          questionFrame: (question_frame as QuestionFrame | undefined) ?? null,
          fieldSnapshotId,
          triPlane,
          coverage,
          freshness,
          calibrationMaturity: noLelCalibrationMaturity(),
        })

        const content = {
          ok: true as const,
          tool: TOOL_NAME,
          chart_id,
          ...envelope,
          composed: composeArgument(envelope.reading),
          density_contract: densityContract,
          about: about ?? null,
          pact_status: pactStatus,
          weakest_link: weakestLink,
          chain: stages,
          fact_id_refs: factIdRefs,
          pact_drill_pointers: pactDrillPointers,
        }

        return kalaBudgetedDualOutput(content, TOOL_NAME)
      } catch (err) {
        return kalaErrorOutput(TOOL_NAME, err instanceof Error ? err.message : String(err), { chart_id })
      }
    },
  )
}
