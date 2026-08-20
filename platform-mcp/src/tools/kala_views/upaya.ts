/**
 * upaya.ts — ṢAḌ-DARŚANA W4 Lane U: `kala_upaya_get` (item 26 UPĀYA-SETU, full + E6 efficacy
 * reporting). Design authority: KALA_W4_UPAYA_DESIGN_v1_0.md (v1.1) §2 + §5;
 * SHAD_DARSHANA_BRIEF_v2_0.md §2.5 Nirmāṇa contract + §7 rails.
 * ==========================================================================================
 * W0 → W4: this file was a facade shell serving an honest `not_in_corpus` ledger for three
 * named coverage concepts (`pact_link_diagnosis`, `alternate_routing_search`,
 * `efficacy_tiers` — kept verbatim, per the design doc: "the completeness census and the
 * specificity gate both key off them"). This is the W4 fill-in. All real computation lives in
 * `../../lib/kala_upaya_diagnosis.ts` (the ONLY other file this lane owns) — this file is
 * assembly: envelope wiring, tri-plane pointers, coverage derivation, and MCP registration.
 *
 * ══════════════════════════════════════════════════════════════════════════════════════════
 * THE MORTALITY-EXCLUSION HARD EXCLUSION (ADJUDICATION-13, ABSOLUTE — design §5.4, gate G16).
 * `isMortalityExcludedRequest` is the FIRST statement `buildKalaUpayaResult` evaluates — before
 * `pact_query`, before any substrate read, before ANY `await`. It is pure and synchronous
 * (kala_upaya_diagnosis.ts), so it is structurally incapable of being reordered after a fetch.
 * An excluded request reaches no diagnosis code path at all: `buildMortalityExclusionRefusal`
 * returns a response carrying no candidate, window, or diagnosis field of any kind. This is
 * NOT a disclosure-tier concept — `native_self` does NOT unlock it (§5.4: "under any audience
 * tier, means it"). Never touch this ordering when editing this file.
 *
 * Ruling U-1 (binding): no fourth remedy store, no recomputed remedy ranking. Every served
 * intervention is a SELECTED row from one of three pre-existing surfaces (`phala_mitigation`,
 * `bodha_rm_*`, `brahma_remedy_corpus`), carrying `source_surface` + its own primary key.
 * Ruling U-2: alternate routing runs over `bodha_graph_*` (L2), `kala_field_routes` optional.
 * Ruling U-3: least-opposed windows are NOT computed here — kala_upaya_get emits a pointer
 * naming the `for_intervention` contract this design PUBLISHES for Lane R to implement in
 * `elect.ts` (never a duplicate window computation — SINGLE TEMPORAL AUTHORITY, brief §7 item 44).
 *
 * Registration: `registerKalaUpayaGet` is called from `registry_bridge.ts`'s
 * `registerRegistryBridgeTools` — ONE canonical registration for this tool, per brief §2.
 */
import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { Principal } from '../../types.js'
// F-125: the B.11 orientation gate — see the export-site note in registry_bridge.ts. This
// is a per_chart interpretive-synthesis surface (PACT-chain diagnosis + prescription), not
// an RS-4-exempt factual lookup, so it is in scope for the gate (spec §2b).
import { fetchOrientationContext } from '../registry_bridge.js'
import {
  makeKalaEnvelope,
  fetchCalibrationMaturity,
  buildKalaFreshness,
  resolveFieldSnapshot,
  computedCoverage,
  honestEmptyCoverage,
  noLeverPointer,
  pointerTo,
  type KalaEnvelope,
  type ArgumentReading,
  type ArgumentEvidence,
  type QuestionFrame,
  type KalaCoverageEntry,
} from '../../lib/kala_envelope.js'
import { composeArgument } from '../../lib/argument_composer.js'
import {
  isMortalityExcludedRequest,
  buildMortalityExclusionRefusal,
  fetchPactDiagnosis,
  fetchRemedyRows,
  fetchAlternateRoutes,
  buildEligibilityPointer,
  buildEfficacyReport,
  resolveAndFileFilingState,
  resolveDisclosureTier,
  splitCitedUncited,
  type MortalityExclusionRefusal,
  type PactDiagnosis,
  type UpayaIntervention,
  type AlternateRoute,
  type EligibilityPointer,
  type EfficacyReport,
  type FilingState,
  type FilingReadyPayload,
  type DisclosureBlock,
  type AdoptInterventionInput,
} from '../../lib/kala_upaya_diagnosis.js'
import { recordInterventionLedgerEntry } from '../../lib/intervention_filing.js'

// ── Input shape ──────────────────────────────────────────────────────────────────────

// E4 (Elevation §5) — question_frame mirrored locally as a zod shape. Not re-exported from
// kala_envelope.ts (that file defines the TS interface only, no zod dependency) — each W0
// facade defines its own copy of this small, stable shape rather than the shared lib taking
// on a zod dependency for eight call sites. See ritual.ts for the identical shape.
const QuestionFrameShape = {
  domain: z.string().optional().describe("e.g. 'career', 'marriage', 'health', 'wealth'."),
  entity: z.string().optional().describe('The specific undertaking/entity named, if any (free text).'),
  horizon: z.string().optional().describe("Caller-stated horizon, e.g. '90d', 'next 24 months' — not yet resolved to a window."),
  intent_verb: z.string().optional().describe("e.g. 'should_i', 'when_should_i', 'what_is'."),
  stakes: z.string().optional().describe('Free-text statement of what is at stake, if supplied.'),
  comparison_target: z.string().optional().describe('For CONTRAST-shaped questions: what to diff against.'),
}

// ADJUDICATION-12 (design §2.6): all four fields required TOGETHER, or the call is a plain
// read that never files. `adoption_basis` has NO zod default and NO enum coercion to a
// fallback — an absent/unrecognised value must reach `resolveFilingState` as-is so the
// fail-CLOSED equality test (`=== 'native_directed'`) is the thing that decides, never a zod
// default silently turning "missing" into "session_inferred" before that check ever runs.
const AdoptInterventionShape = z.object({
  intervention_id: z.string().describe('The id of the served intervention row being adopted (UpayaIntervention.id).'),
  confidence: z.number().gt(0).lt(1).describe('Strictly in the open interval (0,1) — the sanctioned filing route rejects the endpoints.'),
  falsifier: z.string().min(1).describe('MANDATORY — the specific condition that would falsify this adopted intervention.'),
  adoption_basis: z.string().optional().describe(
    "'native_directed' (the native asked for this to be filed) or 'session_inferred' (the model concluded the " +
    "native would want it — this NEVER files). Absent/null/any other string fails CLOSED to " +
    'awaiting_native_confirmation (ADJUDICATION-12) — never defaults to native_directed.',
  ),
  claim: z.string().min(1).optional().describe(
    'The claim text for the filed prospective entry. Absent ⇒ the engine composes a template ' +
    'claim from the diagnosis statement (B.10 template rule, never generative).',
  ),
  window: z.object({
    start: z.string().describe('ISO date/timestamp — window start.'),
    end: z.string().describe('ISO date/timestamp — window end.'),
  }).optional().describe(
    'The window the falsifier is evaluated against. REQUIRED for an actual filing ' +
    "(claim_shape='interval') — a native-directed adoption without it reports filing_failed " +
    'honestly; the engine never composes a window bound on your behalf (B.10).',
  ),
})

const KalaUpayaInputShape = {
  chart_id: z.string().uuid().describe('Chart UUID. Required — no default chart.'),
  // pact_query's own required-input pair (register_d10_pact.ts) — kala_upaya_get forwards
  // whichever is supplied; neither present degrades the diagnosis to honest_empty (never a
  // hard tool error — the mortality check, remedy sourcing, and envelope still run).
  domain: z.string().optional().describe(
    'Life-domain name for the PACT diagnosis (marriage/relationship/partnership, career/vocation, ' +
    'wealth/finance, health/vitality, progeny/children, education, spirituality) — same vocabulary ' +
    'pact_query/judgment_query accept. Takes precedence over `bhava` if both given.',
  ),
  bhava: z.number().int().min(1).max(12).optional().describe('Bhava (house) number 1-12, same semantics as pact_query.'),
  event_class: z.string().optional().describe(
    'brahma_event_ontology event_class_id, if known — used ONLY for the §5.3 withhold-predicate ' +
    'check and echoed back on the response; does not itself select the PACT domain/bhava.',
  ),
  as_of_date: z.string().optional().describe('Date (YYYY-MM-DD) to evaluate PACT ACTIVATION/TRIGGER as-of. Default: today.'),
  adopt_intervention: AdoptInterventionShape.optional().describe(
    'Explicit adoption act (ADJUDICATION-12). Omit for a plain read — a plain read NEVER files.',
  ),
  question_frame: z
    .object(QuestionFrameShape)
    .optional()
    .describe(
      'Optional question_frame (Elevation §5 E4): domain/entity/horizon/intent_verb/stakes/comparison_target. The chart is always implicit (chart_id); this is the only per-question input.',
    ),
}

export interface KalaUpayaParams {
  chart_id: string
  domain?: string | null
  bhava?: number | null
  event_class?: string | null
  as_of_date?: string | null
  adopt_intervention?: AdoptInterventionInput | null
  question_frame?: QuestionFrame | null
}

export interface KalaUpayaResponse extends KalaEnvelope {
  tool: 'kala_upaya_get'
  chart_id: string
  event_class: string | null
  diagnosis: {
    pact_status: PactDiagnosis['pact_status'] | null
    failing_link: PactDiagnosis['failing_link']
    statement: string
    authority_basis: string | null
  }
  interventions: UpayaIntervention[]
  intervention_count: number
  uncited_remedy_rows: UpayaIntervention[]
  uncited_remedy_row_count: number
  uncited_remedy_note: string | null
  alternate_routes: AlternateRoute[]
  eligibility_pointer: EligibilityPointer
  efficacy_report: EfficacyReport
  filing_state: FilingState
  adoption_basis: 'native_directed' | 'session_inferred' | null
  filed_prediction_id: string | null
  filing_ready_payload: FilingReadyPayload | null
  /** The verbatim error when filing_state === 'filing_failed' (design §2.6); else null. */
  filing_detail: string | null
  /** The serve-time `mimamsa_intervention_ledger` recording result — populated only when a
   *  filing actually happened (`filing_state === 'filed'`, item 42 / gate G7); null on every
   *  plain read and every withheld/failed filing. */
  intervention_ledger: {
    recorded: boolean
    intervention_id: string | null
    created: boolean
    detail: string | null
  } | null
  disclosure: DisclosureBlock
  composed_text: string
}

export type KalaUpayaResult = MortalityExclusionRefusal | KalaUpayaResponse

/** Narrows a `KalaUpayaResult` to the mortality-exclusion refusal shape. Exported so tests/
 *  callers don't have to re-derive the discriminant field by hand. */
export function isMortalityRefusal(result: KalaUpayaResult): result is MortalityExclusionRefusal {
  return (result as MortalityExclusionRefusal).excluded === true
}

// ── Pure reading builder (unit-tested directly) ─────────────────────────────────────────

/**
 * Builds the argument-shaped reading from already-computed diagnosis/intervention data. Pure
 * (no I/O) — the caller (`buildKalaUpayaResult`) hands it whatever it fetched.
 */
export function buildKalaUpayaReading(params: {
  chart_id: string
  diagnosis: PactDiagnosis | null
  diagnosisReason: string | null
  interventions: UpayaIntervention[]
}): ArgumentReading {
  const evidence: ArgumentEvidence[] = params.diagnosis
    ? [{ claim: params.diagnosis.statement, fact_ids: params.diagnosis.fact_ids, strength: 'strong' }]
    : []
  for (const row of params.interventions.slice(0, 3)) {
    evidence.push({
      claim: `${row.label} (${row.efficacy_tier}, ${row.source_surface}:${row.source_pk})`,
      fact_ids: [],
      strength: row.efficacy_tier === 'classically_attested' ? 'strong' : 'moderate',
    })
  }

  const thesis = params.diagnosis
    ? `UPĀYA-SETU diagnosis for chart ${params.chart_id}: ${params.diagnosis.statement}`
    : `UPĀYA-SETU could not diagnose a PACT-linked failing link for chart ${params.chart_id}` +
      (params.diagnosisReason ? ` (${params.diagnosisReason})` : '') + '.'

  return {
    thesis,
    evidence,
    dissent: [],
    verdict: {
      statement: params.diagnosis
        ? (params.diagnosis.failing_link
          ? `The failing link is ${params.diagnosis.failing_link}; ${params.interventions.length} intervention(s) routed to it.`
          : 'No failing link exists — no_lever is the correct answer.')
        : 'No diagnosis could be computed for this call.',
      tier: 'structural_prior',
    },
    falsifier: null,
  }
}

// ── The single async entry point (mortality check runs FIRST, unconditionally) ─────────

/**
 * Builds the full `kala_upaya_get` result. The mortality-exclusion check is the FIRST
 * statement — before any `await`, before `pact_query`, before any substrate read — exactly
 * mirroring `ritual.ts`'s `isMode3ShapedRequest`-first discipline for the analogous rail.
 */
export async function buildKalaUpayaResult(params: KalaUpayaParams, principal: Principal): Promise<KalaUpayaResult> {
  // ── §5.4 / gate G16 — MUST be the first statement, pure and synchronous. ──
  if (
    isMortalityExcludedRequest({
      event_class: params.event_class,
      domain: params.domain,
      question_frame: params.question_frame,
    })
  ) {
    // The disclosure tier is resolved only to be ECHOED on the refusal (never to gate it —
    // §5.4: native_self does NOT unlock this exclusion, gate G16(c)).
    const tierPreview = resolveDisclosureTier(params.chart_id, []).audience_tier
    return buildMortalityExclusionRefusal(tierPreview)
  }

  const pactResult = await fetchPactDiagnosis(
    { chart_id: params.chart_id, domain: params.domain, bhava: params.bhava, as_of_date: params.as_of_date },
    principal,
  )
  const diagnosis = pactResult.diagnosis
  const failingLink = diagnosis?.failing_link ?? null
  const targetedGraha = diagnosis?.targeted_graha ?? null

  const [remedyResult, alternateRoutes] = await Promise.all([
    fetchRemedyRows({ chart_id: params.chart_id, targetedGraha, failingLink }, principal),
    fetchAlternateRoutes({ chart_id: params.chart_id, blockedGraha: targetedGraha }, principal),
  ])

  const { cited, uncited } = splitCitedUncited(remedyResult.interventions)
  const eligibilityPointer = buildEligibilityPointer(failingLink)
  const efficacyReport = buildEfficacyReport()

  // The adopted row, when the adoption names one we actually served — its citation/tier are
  // INHERITED (§N.5), never restated, by both the filing and the ledger recording below.
  const adopt = params.adopt_intervention ?? null
  const adoptedRow = adopt
    ? [...cited, ...uncited].find((r) => r.id === adopt.intervention_id) ?? null
    : null

  const filingResolution = await resolveAndFileFilingState(
    {
      chart_id: params.chart_id,
      event_class: params.event_class ?? null,
      diagnosisStatement: diagnosis?.statement ?? null,
      adopt,
      sourceCitation: adoptedRow?.citation ?? null,
    },
    principal,
  )

  // Serve-time Intervention Ledger recording (item 42 / gate G7) — ONLY after a real filing,
  // and only over data we actually served (a row we cannot resolve would force fabricated
  // tier/citation values — refused honestly instead).
  let interventionLedger: KalaUpayaResponse['intervention_ledger'] = null
  if (filingResolution.state === 'filed' && adopt) {
    if (!adoptedRow) {
      interventionLedger = {
        recorded: false,
        intervention_id: null,
        created: false,
        detail:
          `adopt_intervention.intervention_id '${adopt.intervention_id}' did not match any served ` +
          'intervention row — the ledger row was not recorded (its efficacy_tier and ' +
          'source_citation must be inherited from a served row, never fabricated).',
      }
    } else if (!adopt.window) {
      // Unreachable while filing requires a window, kept as a structural guard.
      interventionLedger = { recorded: false, intervention_id: null, created: false, detail: 'no adoption window — ledger row not recorded' }
    } else {
      const claimText =
        (typeof adopt.claim === 'string' && adopt.claim.trim().length > 0)
          ? adopt.claim.trim()
          : (diagnosis?.statement ?? `Adopted intervention ${adopt.intervention_id}`)
      interventionLedger = await recordInterventionLedgerEntry(
        {
          chart_id: params.chart_id,
          intent: claimText,
          intervention_class: 'upaya',
          rite_or_activity_class: adopt.intervention_id,
          event_class: params.event_class ?? null,
          window: adopt.window,
          // A caller-stated adoption window carries no lattice adjudication — day_grade is the
          // honest (coarsest-correct) label, and the basis names exactly that.
          precision_regime: 'day_grade',
          precision_basis: 'caller-stated adoption window (upāya adoption; no lattice adjudication participated)',
          adjudication_record: {
            kind: 'upaya_adoption',
            pact_status: diagnosis?.pact_status ?? null,
            failing_link: failingLink,
            statement: diagnosis?.statement ?? null,
            authority_basis: diagnosis?.authority_basis ?? null,
          },
          score_vector: {
            factors_present: [],
            note: 'upāya adoption — the 4-factor election score does not apply; no factor was computed (honest empty, not zero-filled)',
          },
          efficacy_tier: adoptedRow.efficacy_tier,
          source_citation:
            adoptedRow.citation ??
            'kala_upaya_get diagnosis + intervention row citation (uncited catalog row — see uncited_remedy_note)',
          paddhati_version: 'none_applied_upaya_adoption',
          predicted_differential: `adopted upāya window vs no-intervention baseline: ${claimText}`,
          prediction_id: filingResolution.filed_prediction_id,
          adoption_basis: 'native_directed',
          authority_basis: diagnosis?.authority_basis ?? null,
          engine_version: 'upaya_setu_v1',
        },
        principal,
      )
    }
  }

  const constraintsApplied: string[] = []
  if (filingResolution.state === 'filing_withheld_pending_native_signoff') {
    constraintsApplied.push('filing_withheld_pending_native_signoff')
  }
  const disclosure = resolveDisclosureTier(params.chart_id, constraintsApplied)

  const reading = buildKalaUpayaReading({
    chart_id: params.chart_id,
    diagnosis,
    diagnosisReason: pactResult.reason,
    interventions: cited,
  })
  const composed = composeArgument(reading)

  // ── 3-state coverage per named concept (the three stable identifiers, kept verbatim) ──
  const pactCoverage: KalaCoverageEntry =
    pactResult.state === 'computed'
      ? computedCoverage('pact_link_diagnosis')
      : honestEmptyCoverage('pact_link_diagnosis', pactResult.reason ?? 'pact_query did not resolve.')

  const routingCoverage: KalaCoverageEntry =
    alternateRoutes.state === 'computed'
      ? computedCoverage(`alternate_routing_search (basis: ${alternateRoutes.basis})`)
      : honestEmptyCoverage(
        'alternate_routing_search',
        alternateRoutes.reason ?? 'No alternate route was found.',
      )

  const efficacyCoverage: KalaCoverageEntry =
    remedyResult.interventions.length > 0 && remedyResult.interventions.every((r) => r.efficacy_tier != null)
      ? computedCoverage('efficacy_tiers')
      : honestEmptyCoverage(
        'efficacy_tiers',
        remedyResult.interventions.length === 0
          ? `No intervention rows were served for this diagnosis (errors: ${remedyResult.errors.join('; ') || 'none'}).`
          : 'One or more served rows carried no tier.',
      )

  // W2 (E5): the real field snapshot read — served id, or an honest marker; never a stub.
  const fieldSnapshot = await resolveFieldSnapshot(params.chart_id, principal)

  const envelope = makeKalaEnvelope({
    reading,
    questionFrame: params.question_frame ?? null,
    fieldSnapshot,
    triPlane: {
      interpretation_ref: noLeverPointer(
        'kala_now_get (interpretation plane) is not yet wired to this facade — planner wiring lands at W5 (SHAD_DARSHANA_BRIEF_v2_0.md §3 W5).',
      ),
      prediction_ref: noLeverPointer(
        'kala_ahead_get (prediction plane) is not yet wired to this facade — planner wiring lands at W5 (SHAD_DARSHANA_BRIEF_v2_0.md §3 W5).',
      ),
      intervention_ref: failingLink
        ? pointerTo('kala_elect_get', `Least-opposed windows for the ${failingLink} link — for_intervention contract (design §2.4, published, Lane R implements).`)
        : noLeverPointer(
          'kala_upaya_get IS the intervention plane (UPĀYA-SETU) — this response is itself the '
            + 'intervention surface, so there is no further lever to traverse to. Not a missing '
            + 'pointer: a terminal by construction.',
        ),
    },
    coverage: [pactCoverage, routingCoverage, efficacyCoverage],
    freshness: buildKalaFreshness({ ephemerisVersion: null, sweepBuildDate: null, fieldHash: fieldSnapshot.field_content_hash }),
    calibrationMaturity: await fetchCalibrationMaturity(params.chart_id, principal),
  })

  return {
    ...envelope,
    tool: 'kala_upaya_get',
    chart_id: params.chart_id,
    event_class: params.event_class ?? null,
    diagnosis: {
      pact_status: diagnosis?.pact_status ?? null,
      failing_link: failingLink,
      statement: diagnosis?.statement ?? reading.thesis,
      authority_basis: diagnosis?.authority_basis ?? null,
    },
    interventions: cited,
    intervention_count: cited.length,
    uncited_remedy_rows: uncited,
    uncited_remedy_row_count: uncited.length,
    uncited_remedy_note:
      uncited.length > 0
        ? `${uncited.length} row(s) carry no resolvable classical citation — served here as catalog ` +
          'rows, never counted as confirmed attested interventions (§N.6 density split).'
        : null,
    alternate_routes: alternateRoutes.routes,
    eligibility_pointer: eligibilityPointer,
    efficacy_report: efficacyReport,
    filing_state: filingResolution.state,
    adoption_basis: filingResolution.adoption_basis,
    filed_prediction_id: filingResolution.filed_prediction_id,
    filing_ready_payload: filingResolution.filing_ready_payload,
    filing_detail: filingResolution.filing_detail,
    intervention_ledger: interventionLedger,
    disclosure,
    composed_text: composed.full_text,
  }
}

// ── Tool description ────────────────────────────────────────────────────────────────

const KALA_UPAYA_DESCRIPTION = `\
What it does: The UPĀYA-SETU capability — PACT-linked remedy diagnosis (which link in the \
PROMISE→CONFIRMATION→ACTIVATION→TRIGGER chain failed, and which already-attested rite/remedy \
row reaches it), alternate-routing search across the chart's own promise graph, and citation- \
derived efficacy tiers (classically_attested / traditional / speculative_extension) — never a \
recomputed remedy ranking, never a fourth remedy store (every row cites phala_mitigation, \
bodha_rm_*, or brahma_remedy_corpus by source_surface + primary key). Optionally files an \
auto-falsifiable prospective entry on explicit native-directed adoption (adopt_intervention). \
Returns the elevated kala envelope (argument-shaped reading, 3-state coverage, freshness \
attestation, calibration_maturity, tri-plane pointers) plus a disclosure block.

INDIVIDUALIZED LIFE-SPAN EXCLUSION (absolute, every audience tier): a request touching a \
date-of-death or life-span subject is refused outright — no diagnosis, candidate, or window of \
any kind is computed or served, native_self included.

Least-opposed timing windows are served through kala_elect_get's for_intervention parameter \
(published contract; Lane R implements) — this tool computes no window of its own.

When to prefer: "what remedy should I do about X" / "how do I address this weakness" — paired \
with kala_ritual_get for yajña/vrata options and kala_elect_get for the paired act-time when \
the remedy accompanies an undertaking.`

// ── Registration ────────────────────────────────────────────────────────────────────

/**
 * Registers `kala_upaya_get` on the MCP server. Called from registry_bridge.ts's
 * `registerRegistryBridgeTools` — the ONE canonical registration site for this tool.
 */
export function registerKalaUpayaGet(server: McpServer, principal: Principal): void {
  server.tool(
    'kala_upaya_get',
    KALA_UPAYA_DESCRIPTION,
    KalaUpayaInputShape,
    async ({ chart_id, domain, bhava, event_class, as_of_date, adopt_intervention, question_frame }) => {
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
      const response = await buildKalaUpayaResult(
        {
          chart_id,
          domain: domain ?? null,
          bhava: bhava ?? null,
          event_class: event_class ?? null,
          as_of_date: as_of_date ?? null,
          adopt_intervention: adopt_intervention ?? null,
          question_frame: question_frame ?? null,
        },
        principal,
      )
      // F-125: B.11 orientation gate. `kala_upaya_get` issues a PACT-chain verdict +
      // prescription — interpretive synthesis per A4 of the F-125 diagnosis, not an
      // RS-4-exempt factual lookup — so it must carry the same `orientation_context`/
      // `orientation_ok` floor the `assess_*` family and every registry_bridge.ts domain
      // tool already carry.
      //
      // Skipped on a mortality-exclusion refusal: gate G16 (ADJUDICATION-13, absolute) is
      // that an excluded request triggers NO network call of any kind, before ANY await —
      // upaya.test.ts's G16 firing-proof asserts exactly zero substrate calls on refusal.
      // A B.11 orientation pre-fetch is itself a substrate call, so extending the gate to a
      // refusal would violate that stronger, already-tested invariant. A refusal carries no
      // diagnosis/candidate/window of any kind (by design); it has nothing for a holistic
      // orientation context to attach to.
      if (isMortalityRefusal(response)) {
        return {
          content: [{ type: 'text' as const, text: JSON.stringify(response, null, 2) }],
        }
      }
      const { orientation_context, orientation_ok } = await fetchOrientationContext(
        chart_id, undefined, principal,
      )
      return {
        content: [{
          type: 'text' as const,
          text: JSON.stringify({ ...response, orientation_context, orientation_ok }, null, 2),
        }],
      }
    },
  )
}
