/**
 * kala_upaya_diagnosis.ts — ṢAḌ-DARŚANA W4 Lane U (item 26 UPĀYA-SETU, full).
 * Design authority: KALA_W4_UPAYA_DESIGN_v1_0.md (v1.1) §2 + §5.3/§5.4; SHAD_DARSHANA_BRIEF
 * _v2_0.md §7 rails. This is the ONLY file (besides its own test + `tools/kala_views/upaya.ts`)
 * Lane U owns — see the design doc §0.1 anti-collision table.
 * ============================================================================================
 * WHAT THIS FILE IS (the fill-in of `kala_upaya_get`'s three W0 coverage concepts):
 *   `pact_link_diagnosis` — walks the PACT chain via the existing `pact_query` capability and
 *     maps its closed `pact_status` vocabulary onto the diagnosed failing link (design §2.2).
 *   `alternate_routing_search` — a path search over the L2 promise graph (`bodha_graph_*`) for
 *     a DIFFERENT mechanism reaching a similar outcome (design §2.3, ruling U-2).
 *   `efficacy_tiers` — a deterministic, citation-derived tier assignment over rows already
 *     computed by three pre-existing remedy surfaces (design §2.1/§2.5) — NEVER a recomputed
 *     remedy ranking, NEVER a fourth remedy store (ruling U-1).
 *
 * ══════════════════════════════════════════════════════════════════════════════════════════
 * THE MORTALITY-EXCLUSION SUBSTRATE BAN (ADJUDICATION-13, absolute — design §5.4, gate G16).
 * `isMortalityExcludedRequest` is PURE and SYNCHRONOUS, and `upaya.ts` calls it FIRST, before
 * any other statement in the handler — before `pact_query`, before any substrate read. No W4
 * surface may read āyurdāya/longevity facts into any window bound, under any audience tier,
 * filed or unfiled. This file never imports, calls, or names `ganita_ayurdaya_get`, and the
 * forbidden-identifier substrate ban (`ayurdaya`, `longevity`, `maraka`, `ayus`) is enforced by
 * a source-level regex scan in `kala_upaya_diagnosis.test.ts` AND `upaya.test.ts` — a rail with
 * no proof it can fire is null (CLAUDE.md §N.8), so both test files include a case that
 * actually trips the detector, not merely asserts the identifiers are absent.
 * ══════════════════════════════════════════════════════════════════════════════════════════
 *
 * §N.5 rail (the lower layer is the authority): every row this file serves carries
 * `source_surface` + the row's own primary key, and NO value is recomputed — only selected,
 * tiered by citation-presence, and routed to the diagnosed failing link. Ruling U-1 is
 * structural in this file: there is no local remedy table, no ranking formula, no rewritten
 * `resonance_score`/`proportionality_basis`/`classical_strength_rating` — those fields are
 * read from the row and passed through verbatim.
 */

import type { Principal } from '../types.js'
import { callPlatformPrimitive } from '../client.js'
import { callKalaRegistryCap, unwrapKalaPayload } from '../tools/kala_views/shared.js'

// ══════════════════════════════════════════════════════════════════════════════════════════
// §5.4 — THE INDIVIDUALIZED-MORTALITY-WINDOW HARD EXCLUSION (ADJUDICATION-13, gate G16)
// ══════════════════════════════════════════════════════════════════════════════════════════

/**
 * Forbidden identifiers, ANYWHERE in a W4 lane file (design §5.4 test 1 — the SUBSTRATE ban).
 * This constant exists so the source-level scan test can assert against ONE definition rather
 * than re-typing the pattern, and so this file's own body can be scanned for self-consistency.
 * The pattern intentionally matches `ayurdaya` case-insensitively including the MCP tool name
 * `ganita_ayurdaya_get` (contains `ayurdaya`), `longevity`, `maraka`, and the whole word `ayus`.
 */
export const MORTALITY_FORBIDDEN_IDENTIFIER_PATTERN = /ayurdaya|longevity|maraka|\bayus\b/i

/** Free-text fields a caller might use to shape a mortality/longevity request (design §5.4
 *  test 2 — the REQUEST-SHAPE ban). Deliberately the same small, exhaustively-testable
 *  surface as `ritual.ts`'s `isMode3ShapedRequest` — every field this function reads is a
 *  field `kala_upaya_get`'s own input shape actually accepts. */
export interface MortalityExclusionCheckInput {
  event_class?: string | null
  domain?: string | null
  question_frame?: {
    domain?: string | null
    entity?: string | null
    horizon?: string | null
    intent_verb?: string | null
    stakes?: string | null
    comparison_target?: string | null
  } | null
}

/**
 * True iff `params` is mortality/longevity-shaped by the request-shape test (§5.4 test 2).
 * PURE and SYNCHRONOUS — structurally incapable of awaiting I/O, so it cannot be reordered
 * after a fetch by a later refactor (the same property `isMode3ShapedRequest` has, and the
 * same reason it matters: the caller MUST be able to run this before any network call).
 *
 * This is the request-shape half only. The substrate-ban half (test 1: no W4 file ever reads
 * an āyurdāya/longevity fact into a window bound) is a STRUCTURAL property of this codebase —
 * this file, `upaya.ts`, and the whole platform-mcp Lane-U file set never import or call
 * `ganita_ayurdaya_get` and never reference an āyurdāya-category `chart_facts` row — proved by
 * the source-level regex scan test (§9 G16(b)), not by a runtime check (there is nothing to
 * check at runtime if the import never exists).
 */
export function isMortalityExcludedRequest(params: MortalityExclusionCheckInput): boolean {
  const candidateFields: Array<string | null | undefined> = [
    params.event_class,
    params.domain,
    params.question_frame?.domain,
    params.question_frame?.entity,
    params.question_frame?.horizon,
    params.question_frame?.intent_verb,
    params.question_frame?.stakes,
    params.question_frame?.comparison_target,
  ]
  return candidateFields.some((field) => typeof field === 'string' && MORTALITY_FORBIDDEN_IDENTIFIER_PATTERN.test(field))
}

/** The honest refusal envelope (§5.4: "short-circuits completely... no partial computation,
 *  no candidate list, no window — the `buildMode3WrongViewResponse` pattern: a response that
 *  carries no content because none was attempted"). Deliberately NOT a `KalaEnvelope` — same
 *  reasoning as `ritual.ts`'s `KalaRitualWrongView`. `audience_tier` is echoed, never used to
 *  gate: §5.4 is explicit that `native_self` does NOT unlock this exclusion (gate G16(c)). */
export interface MortalityExclusionRefusal {
  tool: 'kala_upaya_get'
  excluded: true
  exclusion: 'individualized_mortality_window'
  reason: string
  citation: string
  audience_tier_evaluated: string | null
}

export function buildMortalityExclusionRefusal(audienceTier: string | null = null): MortalityExclusionRefusal {
  return {
    tool: 'kala_upaya_get',
    excluded: true,
    exclusion: 'individualized_mortality_window',
    reason:
      'This request is refused under the individualized-mortality-window hard exclusion. No W4 ' +
      'surface may read āyurdāya/longevity facts into any window bound, under any audience ' +
      'tier, filed or unfiled — a computed window here would produce a date-of-death claim by ' +
      'composition even though no field of this response ever claims to serve one. No ' +
      'diagnosis, candidate, or window was computed for this request; none was attempted.',
    citation: 'MACRO_PLAN_v2_0.md §3.5.C (Ethical Framework); KALA_W4_UPAYA_DESIGN_v1_0.md §5.4, ' +
      'ADJUDICATION-13 (binding), gate G16.',
    audience_tier_evaluated: audienceTier,
  }
}

// ══════════════════════════════════════════════════════════════════════════════════════════
// §2.2 — PACT-linked diagnosis: pact_status → failing_link (closed vocabularies, verbatim)
// ══════════════════════════════════════════════════════════════════════════════════════════

/** `pact_query`'s own closed `pact_status` vocabulary (register_d10_pact.ts), copied verbatim
 *  — copying it here (rather than a loose `string`) is what makes the PACT↔diagnosis mapping
 *  machine-checkable (design §2.2: "the diagnosis machine-checkable rather than prose"). */
export type PactStatus =
  | 'denied_at_promise'
  | 'denied_at_confirmation'
  | 'denied_at_activation'
  | 'chain_pending_activation'
  | 'chain_incomplete_infra'
  | 'chain_complete'

export type FailingLink = 'promise' | 'confirmation' | 'activation' | 'trigger'

/**
 * The design §2.2 table, made executable. `chain_pending_activation` maps to `'activation'`
 * (the eligibility-side bottleneck) even though PACT itself calls that status "pending, not
 * denied" — the failing_link field names WHERE the lever would apply, not a claim that the
 * link is broken; the diagnosis statement (below) states the "eligible, not yet reached"
 * distinction in prose. `chain_complete` and `chain_incomplete_infra` both map to `null`:
 * `chain_complete` because there is genuinely no failing link (`no_lever` is the correct
 * answer, design §2.2); `chain_incomplete_infra` because the chain could not be walked, so no
 * link can be honestly named as failing (never re-worded into an astrological finding).
 */
export function mapPactStatusToFailingLink(status: PactStatus): FailingLink | null {
  switch (status) {
    case 'denied_at_promise':
      return 'promise'
    case 'denied_at_confirmation':
      return 'confirmation'
    case 'denied_at_activation':
      return 'activation'
    case 'chain_pending_activation':
      return 'activation'
    case 'chain_complete':
    case 'chain_incomplete_infra':
      return null
  }
}

/** Template-composed (B.10 — no generative call), one sentence per `pact_status`, matching
 *  the design §2.2 table's own wording closely enough that a reader can verify the mapping by
 *  eye. `chain_complete` states the no-manufactured-remedy rail explicitly (design §2.2:
 *  "Manufacturing a remedy for a complete chain is the Offer-Law failure this wave must not
 *  commit"). `chain_incomplete_infra` states the infra-vs-classical distinction explicitly. */
export function composeDiagnosisStatement(status: PactStatus, reasonFromPact: string | null): string {
  const reason = reasonFromPact ? ` (${reasonFromPact})` : ''
  switch (status) {
    case 'denied_at_promise':
      return `The rāśi promise is absent or weak at L2${reason} — the chain halts at PROMISE.`
    case 'denied_at_confirmation':
      return `Promised in rāśi, but the operative varga does not confirm it${reason} — the ` +
        'rāśi-level promise does not survive divisional confirmation.'
    case 'denied_at_activation':
      return `Promised and confirmed, but no daśā eligibility exists in the computed horizon${reason} — ` +
        'the rāśi does not promise a dasha vehicle to deliver it.'
    case 'chain_pending_activation':
      return `Promised, confirmed, and eligible — the activation window has not yet been reached${reason}. ` +
        'This is the case where the honest lever is often "wait"; the instrument states that ' +
        'plainly rather than manufacturing urgency.'
    case 'chain_complete':
      return 'Every PACT stage is satisfied — there is no failing link to repair. Manufacturing a ' +
        'remedy for a complete chain would be a fabricated intervention (Offer-Law failure); the ' +
        'correct answer is no_lever.'
    case 'chain_incomplete_infra':
      return `The chain could not be fully walked for an infrastructure reason, not a classical ` +
        `denial${reason} — never re-worded into an astrological finding.`
  }
}

/** One PACT-diagnosed stage result, the shape this file needs from `pact_query`'s response. */
export interface PactDiagnosis {
  pact_status: PactStatus
  failing_link: FailingLink | null
  statement: string
  /** item 44 — the pact_query stage id this diagnosis rests on (design §2.7's
   *  `diagnosis.authority_basis`). `null` when the chain could not be walked at all. */
  authority_basis: string | null
  /** The graha this diagnosis should route remedies toward (the promise-carrying bhāveśa),
   *  when `pact_query` supplied one. Used by the alternate-routing search (§2.3) as its seed. */
  targeted_graha: string | null
  fact_ids: string[]
}

const PACT_STATUS_SET: ReadonlySet<string> = new Set<PactStatus>([
  'denied_at_promise', 'denied_at_confirmation', 'denied_at_activation',
  'chain_pending_activation', 'chain_incomplete_infra', 'chain_complete',
])

export interface PactDiagnosisResult {
  state: 'computed' | 'honest_empty'
  reason: string | null
  diagnosis: PactDiagnosis | null
}

/**
 * Fetches `pact_query` (marsys://tool/L-PACT/pact_query) via the shared registry-capability
 * caller (`kala_views/shared.ts`'s `callKalaRegistryCap` — the SAME path `pact_query`'s own
 * MCP registration in `registry_bridge.ts` uses, not a second implementation of the proxy).
 * Lane U CALLS this capability; it never re-walks the PACT chain itself (design §2.2).
 *
 * Honest degradation: a missing `domain`/`bhava` (pact_query's own required-input pair), an
 * error response, or a `pact_status` outside the closed set all yield `honest_empty` with a
 * named reason — never a fabricated diagnosis (this IS the detector named in design §2.2:
 * "Detector that could make it read false: pact_query erroring, or returning a status outside
 * the set").
 */
export async function fetchPactDiagnosis(
  params: { chart_id: string; domain?: string | null; bhava?: number | null; as_of_date?: string | null },
  principal: Principal,
): Promise<PactDiagnosisResult> {
  if (!params.domain && params.bhava == null) {
    return {
      state: 'honest_empty',
      reason: 'pact_query requires either `domain` or `bhava` — neither was supplied to kala_upaya_get.',
      diagnosis: null,
    }
  }
  try {
    const raw = await callKalaRegistryCap(
      'marsys://tool/L-PACT/pact_query',
      {
        chart_id: params.chart_id,
        ...(params.domain ? { domain: params.domain } : {}),
        ...(params.bhava != null ? { bhava: params.bhava } : {}),
        ...(params.as_of_date ? { as_of_date: params.as_of_date } : {}),
      },
      principal,
    )
    const payload = unwrapKalaPayload(raw)
    if ('error' in payload) {
      return { state: 'honest_empty', reason: `pact_query returned an error: ${String(payload['error'])}`, diagnosis: null }
    }
    const statusRaw = payload['pact_status']
    if (typeof statusRaw !== 'string' || !PACT_STATUS_SET.has(statusRaw)) {
      return {
        state: 'honest_empty',
        reason: `pact_query returned pact_status="${String(statusRaw)}", outside the closed vocabulary — ` +
          'never mapped to a failing_link (B.10).',
        diagnosis: null,
      }
    }
    const status = statusRaw as PactStatus
    const stages = Array.isArray(payload['stages']) ? (payload['stages'] as Array<Record<string, unknown>>) : []
    const lastStage = stages[stages.length - 1]
    const reasonFromPact = lastStage && typeof lastStage['reason'] === 'string' ? (lastStage['reason'] as string) : null
    // The promise-carrying bhāveśa is not carried on the PROMISE stage row itself — it first
    // appears on the CONFIRMATION stage's `dignities` array (register_d10_pact.ts's
    // `gradeGrahaInVarga` rows), so that is where this reads it from.
    const confirmationStage = stages.find((s) => s['stage'] === 'CONFIRMATION')
    const dignities = confirmationStage && Array.isArray(confirmationStage['dignities'])
      ? (confirmationStage['dignities'] as Array<Record<string, unknown>>)
      : []
    const bhaveshaRow = dignities.find((d) => d['role'] === 'bhavesha')
    const targetedGraha = bhaveshaRow && typeof bhaveshaRow['graha'] === 'string' ? (bhaveshaRow['graha'] as string) : null

    const factIdsRaw = payload['fact_id_refs']
    const fact_ids = Array.isArray(factIdsRaw) ? factIdsRaw.filter((f): f is string => typeof f === 'string') : []

    return {
      state: 'computed',
      reason: null,
      diagnosis: {
        pact_status: status,
        failing_link: mapPactStatusToFailingLink(status),
        statement: composeDiagnosisStatement(status, reasonFromPact),
        authority_basis: `pact_query:${status}`,
        targeted_graha: targetedGraha,
        fact_ids,
      },
    }
  } catch (err) {
    return { state: 'honest_empty', reason: `pact_query call failed: ${String(err)}`, diagnosis: null }
  }
}

// ══════════════════════════════════════════════════════════════════════════════════════════
// §2.1 / §2.5 — the three pre-existing remedy surfaces, efficacy tiers, and the density split
// ══════════════════════════════════════════════════════════════════════════════════════════

export type EfficacyTier = 'classically_attested' | 'traditional' | 'speculative_extension'

/** One served intervention row, source-attributed per §N.5 ("any row Lane U serves carries
 *  `source_surface` + the row's own primary key, so a reader can always get back to the
 *  authority"). Never a locally-generated remedy — every field here is read, not computed. */
export interface UpayaIntervention {
  id: string
  intervention_class: 'phala_mitigation' | 'bodha_rm_prescription' | 'remedy_corpus'
  source_surface: string
  source_pk: string
  label: string
  efficacy_tier: EfficacyTier
  citation: string | null
  targets_link: FailingLink | null
  feasibility: number | null
}

/**
 * Design §2.5's tier table, made executable: `classically_attested` iff the row carries a
 * resolvable classical citation; `traditional` iff the row lives in a live corpus surface but
 * carries none; `speculative_extension` is reserved for an inference THIS WAVE made (never
 * used by the row-mapping functions below, which only ever read real rows — see the RAIL note
 * in the design doc: "speculative_extension is a serving label on a real row, never a licence
 * to synthesize a rite"). `isLiveSurface=false` with no citation would mean the row does not
 * even claim to be live corpus content — this file's three mappers below always pass `true`
 * for `isLiveSurface` because all three source tables ARE the live corpus; the
 * `speculative_extension` branch exists for future callers that assemble an inference (e.g. a
 * deity correspondence NOT backed by a corpus row) and MUST NOT be used to route an
 * unattested row into the `interventions` array — such a row is not served at all.
 */
export function assignEfficacyTier(params: { hasCitation: boolean; isLiveSurface: boolean }): EfficacyTier {
  if (params.hasCitation) return 'classically_attested'
  if (params.isLiveSurface) return 'traditional'
  return 'speculative_extension'
}

function nonBlank(v: unknown): string | null {
  if (typeof v !== 'string') return null
  const trimmed = v.trim()
  return trimmed.length > 0 ? trimmed : null
}

/** `phala_mitigation` row shape (design §2.1 table — the columns Lane U actually reads). */
export interface PhalaMitigationRow {
  mitigation_id: string
  afflicting_graha: string | null
  obstruction_severity: number | null
  intensity_tier: string | null
  proportionality_basis: string | null
  classical_citation: string | null
}

export function phalaMitigationToIntervention(row: PhalaMitigationRow, targetsLink: FailingLink | null): UpayaIntervention {
  const citation = nonBlank(row.classical_citation)
  return {
    id: `phala_mitigation:${row.mitigation_id}`,
    intervention_class: 'phala_mitigation',
    source_surface: 'phala_mitigation',
    source_pk: row.mitigation_id,
    label: [row.intensity_tier, row.afflicting_graha ? `for ${row.afflicting_graha}` : null, row.proportionality_basis]
      .filter((x): x is string => Boolean(x))
      .join(' — ') || `phala_mitigation ${row.mitigation_id}`,
    efficacy_tier: assignEfficacyTier({ hasCitation: citation !== null, isLiveSurface: true }),
    citation,
    targets_link: targetsLink,
    feasibility: null,
  }
}

/** `bodha_rm_remedy_prescriptions` row shape (design §2.1 table). `classical_sources_jsonb` is
 *  treated as carrying a citation whenever it is a non-empty array/object (design §2.5:
 *  "carries a non-empty citations[]/text_chunk_ids[]"); `citation_human`/`citation_ref` are the
 *  serving-layer's own flat citation fields (seen live in `query_rm_prescriptions.ts`) and are
 *  checked first because they are already the resolved, human-legible form. */
export interface BodhaRmPrescriptionRow {
  prescription_id: string
  target_graha: string | null
  remedy_category: string | null
  remedy_label_human: string | null
  classical_strength_rating: number | null
  classical_sources_jsonb: unknown
  feasibility_score: number | null
  citation_ref: string | null
  citation_human: string | null
}

function classicalSourcesJsonbHasCitation(v: unknown): boolean {
  if (v == null) return false
  if (Array.isArray(v)) return v.length > 0
  if (typeof v === 'object') return Object.keys(v as Record<string, unknown>).length > 0
  if (typeof v === 'string') return v.trim().length > 0
  return false
}

export function bodhaRmPrescriptionToIntervention(row: BodhaRmPrescriptionRow, targetsLink: FailingLink | null): UpayaIntervention {
  const citation = nonBlank(row.citation_human) ?? nonBlank(row.citation_ref)
  const hasCitation = citation !== null || classicalSourcesJsonbHasCitation(row.classical_sources_jsonb)
  return {
    id: `bodha_rm_remedy_prescriptions:${row.prescription_id}`,
    intervention_class: 'bodha_rm_prescription',
    source_surface: 'bodha_rm_remedy_prescriptions',
    source_pk: row.prescription_id,
    label: row.remedy_label_human
      ?? [row.remedy_category, row.target_graha ? `for ${row.target_graha}` : null].filter((x): x is string => Boolean(x)).join(' ')
      ?? `bodha_rm prescription ${row.prescription_id}`,
    efficacy_tier: assignEfficacyTier({ hasCitation, isLiveSurface: true }),
    citation: citation ?? (hasCitation ? 'see classical_sources_jsonb' : null),
    targets_link: targetsLink,
    feasibility: typeof row.feasibility_score === 'number' ? row.feasibility_score : null,
  }
}

/** `brahma_remedy_corpus` row shape (design §2.1 table + the §2.1 sourcing rail: source via
 *  `query_remedies_for_chart`/`read_remedy`, NEVER `query_remedies_by_planet`/`query_mantras`,
 *  because those two primitives do not select `source_citation`). A row whose
 *  `source_citation` AND `classical_ref` AND `classical_attestation_text` are all blank is a
 *  catalog row (design §2.1's second sourcing rail) and is density-split OUT of
 *  `interventions` by the caller — this mapper still tiers it honestly
 *  (`speculative_extension` would be wrong here too; an unattested corpus row is `traditional`
 *  if the corpus itself is a live, non-scaffold surface, which `brahma_remedy_corpus` is). */
export interface RemedyCorpusRow {
  remedy_id: string
  planet: string | null
  domain: string | null
  deity: string | null
  prescription_text: string | null
  source_citation: string | null
  classical_ref: string | null
  classical_attestation_text: string | null
}

export function remedyCorpusRowToIntervention(row: RemedyCorpusRow, targetsLink: FailingLink | null): UpayaIntervention {
  const citation = nonBlank(row.source_citation) ?? nonBlank(row.classical_ref) ?? nonBlank(row.classical_attestation_text)
  return {
    id: `brahma_remedy_corpus:${row.remedy_id}`,
    intervention_class: 'remedy_corpus',
    source_surface: 'brahma_remedy_corpus',
    source_pk: row.remedy_id,
    label: row.prescription_text
      ?? [row.deity, row.planet ? `(${row.planet})` : null].filter((x): x is string => Boolean(x)).join(' ')
      ?? `brahma_remedy_corpus ${row.remedy_id}`,
    efficacy_tier: assignEfficacyTier({ hasCitation: citation !== null, isLiveSurface: true }),
    citation,
    targets_link: targetsLink,
    feasibility: null,
  }
}

/**
 * §N.6 density split: an intervention with no resolvable citation is served in its own field
 * with its own count (`uncited_remedy_rows`/`uncited_remedy_row_count`), never merged into
 * `interventions` — mirrors `kala_lattice_query.ts`'s `convention_only_factors` shape exactly
 * (design §2.1's second sourcing rail). A row with `efficacy_tier==='classically_attested'` is
 * always cited by construction (that IS the tier's definition); every other tier is a
 * candidate for the uncited bucket, and this function decides by the row's own `citation`
 * field, never by re-deriving citedness from the tier label.
 */
export function splitCitedUncited(rows: UpayaIntervention[]): { cited: UpayaIntervention[]; uncited: UpayaIntervention[] } {
  const cited: UpayaIntervention[] = []
  const uncited: UpayaIntervention[] = []
  for (const row of rows) {
    if (row.citation !== null) cited.push(row)
    else uncited.push(row)
  }
  return { cited, uncited }
}

export interface RemedyFetchResult {
  interventions: UpayaIntervention[]
  errors: string[]
}

/**
 * Fetches all three remedy surfaces (design §2.1's inventory) and maps each row through its
 * own mapper — no local ranking, no recomputation (ruling U-1). Each surface is fetched
 * independently and a failure on one never blocks the others (Promise.allSettled discipline);
 * a failed surface is named in `errors`, never silently dropped (B.10).
 *
 * §N.6 sourcing rail: `brahma_remedy_corpus` is read via `query_remedies_for_chart` (which
 * selects `source_citation`), NEVER via `query_remedies_by_planet`/`query_mantras` (which do
 * not) — see `RemedyCorpusRow`'s doc comment.
 */
export async function fetchRemedyRows(
  params: { chart_id: string; targetedGraha: string | null; failingLink: FailingLink | null },
  principal: Principal,
): Promise<RemedyFetchResult> {
  const errors: string[] = []
  const interventions: UpayaIntervention[] = []

  const [mitigationSettled, prescriptionSettled, corpusSettled] = await Promise.allSettled([
    callPlatformPrimitive('query_remedy_program', { chart_id: params.chart_id, limit: 50 }, principal),
    callPlatformPrimitive('query_rm_prescriptions', { chart_id: params.chart_id, limit: 50 }, principal),
    params.targetedGraha
      ? callPlatformPrimitive('query_remedies_for_chart', { chart_id: params.chart_id, affliction: params.targetedGraha, top_k: 20 }, principal)
      : Promise.resolve(null),
  ])

  if (mitigationSettled.status === 'fulfilled' && mitigationSettled.value) {
    const { status, envelope } = mitigationSettled.value
    if (status === 200 && envelope.ok) {
      const rows = (envelope.result as { remedies?: PhalaMitigationRow[] } | null)?.remedies ?? []
      for (const row of rows) interventions.push(phalaMitigationToIntervention(row, params.failingLink))
    } else {
      errors.push(`query_remedy_program returned status ${status}`)
    }
  } else if (mitigationSettled.status === 'rejected') {
    errors.push(`query_remedy_program threw: ${String(mitigationSettled.reason)}`)
  }

  if (prescriptionSettled.status === 'fulfilled' && prescriptionSettled.value) {
    const { status, envelope } = prescriptionSettled.value
    if (status === 200 && envelope.ok) {
      const rows = (envelope.result as { rows?: BodhaRmPrescriptionRow[] } | null)?.rows ?? []
      const targetFiltered = params.targetedGraha
        ? rows.filter((r) => !r.target_graha || r.target_graha === params.targetedGraha)
        : rows
      for (const row of targetFiltered) interventions.push(bodhaRmPrescriptionToIntervention(row, params.failingLink))
    } else {
      errors.push(`query_rm_prescriptions returned status ${status}`)
    }
  } else if (prescriptionSettled.status === 'rejected') {
    errors.push(`query_rm_prescriptions threw: ${String(prescriptionSettled.reason)}`)
  }

  if (corpusSettled.status === 'fulfilled' && corpusSettled.value) {
    const { status, envelope } = corpusSettled.value
    if (status === 200 && envelope.ok) {
      const rows = (envelope.result as { remedies?: RemedyCorpusRow[] } | null)?.remedies ?? []
      for (const row of rows) interventions.push(remedyCorpusRowToIntervention(row, params.failingLink))
    } else {
      errors.push(`query_remedies_for_chart returned status ${status}`)
    }
  } else if (corpusSettled.status === 'rejected') {
    errors.push(`query_remedies_for_chart threw: ${String(corpusSettled.reason)}`)
  }

  return { interventions, errors }
}

// ══════════════════════════════════════════════════════════════════════════════════════════
// §2.3 — Alternate-routing search (ruling U-2: bodha_graph primary, kala_field_routes optional)
// ══════════════════════════════════════════════════════════════════════════════════════════

export interface AlternateRoute {
  mechanism_id: string
  statement: string
  fact_ids: string[]
  distinct_from_blocked: boolean
}

export interface AlternateRoutingResult {
  state: 'computed' | 'honest_empty'
  basis: 'bodha_graph' | 'bodha_graph_plus_kala_field_routes' | null
  reason: string | null
  routes: AlternateRoute[]
}

/**
 * Ruling U-2: the alternate-routing search runs over the L2 CGM graph
 * (`marsys://tool/L2/traverse_chart_graph`, MCP-facing `get_cgm_subgraph`/`bodha_graph_traverse_get`)
 * as its PRIMARY substrate. `kala_field_routes` is NOT consulted here — it is documented as
 * empty in production (ADJUDICATION-2, the N_e blocker) and there is no MCP-exposed primitive
 * for it at this build tier; the design's own enrichment clause ("a single `if
 * (routes.length > 0)` branch; when W2 unblocks, nothing in Lane U changes") is preserved as a
 * literal no-op branch below so the wiring is a one-line change when that primitive exists,
 * not a rewrite.
 *
 * A returned route is filtered `distinct_from_blocked=false` (and dropped) when its node is
 * literally the seed node itself (the blocked significator) — this build tier does not attempt
 * the design's full "significator SET is a subset of the blocked route's" comparison (that
 * check needs `brahma_activity_ontology.significators`, which is Lane R's ritual-resonance
 * substrate, §3.3); this is a narrower, honestly-scoped distinctness test, named as such in
 * `reason`.
 */
export async function fetchAlternateRoutes(
  params: { chart_id: string; blockedGraha: string | null },
  principal: Principal,
): Promise<AlternateRoutingResult> {
  if (!params.blockedGraha) {
    return {
      state: 'honest_empty',
      basis: null,
      reason: 'No promise-carrying graha was identified by the PACT diagnosis to seed the alternate-routing search.',
      routes: [],
    }
  }
  // The single enrichment branch ruling U-2 describes. There is no MCP-exposed primitive for
  // kala_field_routes yet (the N_e blocker, ADJUDICATION-2) — `fieldRoutesAvailable` stays
  // `false` structurally until one exists; when it does, this is the one line that changes.
  const fieldRoutesAvailable = false

  try {
    const raw = await callKalaRegistryCap(
      'marsys://tool/L2/traverse_chart_graph',
      { chart_id: params.chart_id, mode: 'neighbors', about: [`graha(${params.blockedGraha})`], max_depth: 1 },
      principal,
    )
    const payload = unwrapKalaPayload(raw)
    if ('error' in payload) {
      return { state: 'honest_empty', basis: null, reason: `traverse_chart_graph returned an error: ${String(payload['error'])}`, routes: [] }
    }
    const nodes = Array.isArray(payload['nodes']) ? (payload['nodes'] as Array<Record<string, unknown>>) : []
    const edges = Array.isArray(payload['edges']) ? (payload['edges'] as Array<Record<string, unknown>>) : []
    const seedNodeIds = new Set(
      nodes.filter((n) => n['node_subject'] === params.blockedGraha).map((n) => String(n['node_id'])),
    )

    const routes: AlternateRoute[] = []
    for (const edge of edges) {
      const fromId = String(edge['from_node_id'] ?? '')
      const toId = String(edge['to_node_id'] ?? '')
      const otherId = seedNodeIds.has(fromId) ? toId : fromId
      const distinct = otherId.length > 0 && !seedNodeIds.has(otherId)
      const factIdsRaw = edge['fact_id_refs'] ?? edge['fact_ids']
      const fact_ids = Array.isArray(factIdsRaw) ? factIdsRaw.filter((f): f is string => typeof f === 'string') : []
      if (!distinct) continue
      routes.push({
        mechanism_id: String(edge['edge_id'] ?? `${fromId}->${toId}`),
        statement: `A ${String(edge['relationship_basis'] ?? 'graph')} link reaches a node outside ` +
          `${params.blockedGraha}'s own neighborhood — a candidate alternate mechanism, not a restatement ` +
          'of the blocked promise. Distinctness here is tested at the graph-node level only (this build ' +
          'tier does not compare full significator sets — see KALA_W4_UPAYA_DESIGN_v1_0.md §2.3).',
        fact_ids,
        distinct_from_blocked: true,
      })
    }

    if (routes.length === 0) {
      return {
        state: 'honest_empty',
        basis: fieldRoutesAvailable ? 'bodha_graph_plus_kala_field_routes' : 'bodha_graph',
        reason: `No alternate-mechanism edge (distinct from ${params.blockedGraha}'s own neighborhood) was ` +
          'found in the L2 promise graph.',
        routes: [],
      }
    }
    return {
      state: 'computed',
      basis: fieldRoutesAvailable ? 'bodha_graph_plus_kala_field_routes' : 'bodha_graph',
      reason: null,
      routes,
    }
  } catch (err) {
    return { state: 'honest_empty', basis: null, reason: `traverse_chart_graph call failed: ${String(err)}`, routes: [] }
  }
}

// ══════════════════════════════════════════════════════════════════════════════════════════
// §2.4 — Eligibility-side: least-opposed windows (ruling U-3 — Lane U computes NO window)
// ══════════════════════════════════════════════════════════════════════════════════════════

/**
 * Ruling U-3 (SINGLE TEMPORAL AUTHORITY, brief §7 item 44): Lane U NEVER computes its own
 * window — it emits a pointer naming the `for_intervention` contract it published for Lane R
 * to implement in `elect.ts` (design §2.4). Until that lands, this is an honest `not_in_corpus`
 * pointer, never a fabricated window and never a duplicate implementation of ELECT's candidate
 * stack (that would be a build error under the SINGLE TEMPORAL AUTHORITY rail, not a
 * divergence to classify).
 */
export interface EligibilityPointer {
  state: 'not_in_corpus'
  instrument: 'kala_elect_get'
  contract_param: 'for_intervention'
  reason: string
}

export function buildEligibilityPointer(failingLink: FailingLink | null): EligibilityPointer {
  return {
    state: 'not_in_corpus',
    instrument: 'kala_elect_get',
    contract_param: 'for_intervention',
    reason:
      'The least-opposed-window search is served through kala_elect_get\'s existing candidate ' +
      'stack via a `for_intervention` parameter (failing_link/event_class/upaya_ref) published by ' +
      'this design (KALA_W4_UPAYA_DESIGN_v1_0.md §2.4) for Lane R to implement in elect.ts — Lane U ' +
      'computes no window of its own (SINGLE TEMPORAL AUTHORITY, brief §7 item 44). Until Lane R\'s ' +
      'PR lands, call kala_elect_get directly with undertaking="remedial_ritual" as the honest ' +
      `interim substitute.${failingLink ? ` (failing_link: ${failingLink})` : ''}`,
  }
}

// ══════════════════════════════════════════════════════════════════════════════════════════
// §4.5 / E6 — efficacy reporting (read-back from Lane S's ledger; honest_empty at this build tier)
// ══════════════════════════════════════════════════════════════════════════════════════════

export interface EfficacyReport {
  state: 'computed' | 'honest_empty'
  reason: string | null
  n_elected_and_acted: number
  n_acted_without_election: number
  n_elected_not_acted: number
  n_outcome_linked: number
  n_resolved_prospective_hits: number
}

/**
 * E6 efficacy reporting reads Lane S's `mimamsa_intervention_ledger` (design §4.5) — a table
 * `mi_sankalpa` (Lane S, item 42) writes. Lane U builds against the PUBLISHED contract only
 * (design §0.3 sequencing note): there is no MCP-exposed primitive for this ledger at this
 * build tier (Lane S's spine + writer are a separate, parallel lane), so this ALWAYS returns
 * `honest_empty` with the exact LAW ZERO reason the design specifies — "a rate here would be a
 * LAW ZERO violation" — never a fabricated confidence number (E6's own binding constraint).
 * When Lane S's read path exists, this is the one function that changes.
 */
export function buildEfficacyReport(): EfficacyReport {
  return {
    state: 'honest_empty',
    reason:
      'No resolved intervention outcomes recorded yet — mimamsa_intervention_ledger (mi_sankalpa, ' +
      'Lane S item 42) has no MCP-exposed read path at this build tier. A percentage or confidence ' +
      'number here before real calibration data exists would be a LAW ZERO violation ' +
      '(KALA_SUPREME_ELEVATION_v1_0.md §13); counts are honestly reported as zero, never a rate.',
    n_elected_and_acted: 0,
    n_acted_without_election: 0,
    n_elected_not_acted: 0,
    n_outcome_linked: 0,
    n_resolved_prospective_hits: 0,
  }
}

// ══════════════════════════════════════════════════════════════════════════════════════════
// §5.3 — the withhold predicate (ADJUDICATION-13, RATIFIED + CORRECTED; gate G14/G14b)
// ══════════════════════════════════════════════════════════════════════════════════════════

/**
 * The five event classes the design's corrected, magnitude-free, three-disjunct predicate
 * resolves to against the LIVE `brahma_event_ontology` (design §5.3 amendment A, verified at
 * design time). `platform-mcp` has no direct DB connection and no MCP-exposed primitive for
 * querying `brahma_event_ontology` by `domain`/`lel_category` (only per-chart/global reference
 * primitives exist in the surgical whitelist — see `tool_name_bridge.ts`'s `SURGICAL_TOOLS`,
 * which carries no event-ontology query) — so this is a VERIFIED SNAPSHOT constant, not a live
 * query. This is a real, honestly-named scope limit (not a live-DB assertion), and it is
 * exactly what `isAdverseWithholdClass`'s own test proves is non-vacuous (§9 G14b, scoped to
 * what this file can verify): the set has five members, matching the design doc's own
 * live-verified resolution. Widening this to a genuinely live query needs a new primitive
 * (`query_event_ontology_class` or similar) — out of Lane U's exclusive-write file scope
 * (design §0.1); flagged here for the Conductor, not silently worked around.
 */
export const ADVERSE_WITHHOLD_EVENT_CLASSES = [
  'illness_acute',
  'chronic_onset',
  'surgery',
  'psychological_arc',
  'bereavement',
] as const

export type AdverseWithholdEventClass = (typeof ADVERSE_WITHHOLD_EVENT_CLASSES)[number]

/** `bereavement` is on this ground for the CONSENT reason design §5.3 amendment (B) states
 *  (a third-party mortality window, not the native's own health) — recorded here so a reader
 *  auditing `constraints_applied` sees the correct citation, not a health mis-file. */
export function withholdGroundFor(eventClass: string): 'health' | 'psychological' | 'consent_third_party' | null {
  if (eventClass === 'bereavement') return 'consent_third_party'
  if (eventClass === 'psychological_arc') return 'psychological'
  if (eventClass === 'illness_acute' || eventClass === 'chronic_onset' || eventClass === 'surgery') return 'health'
  return null
}

export function isAdverseWithholdClass(eventClass: string | null | undefined): eventClass is AdverseWithholdEventClass {
  if (!eventClass) return false
  return (ADVERSE_WITHHOLD_EVENT_CLASSES as readonly string[]).includes(eventClass)
}

// ══════════════════════════════════════════════════════════════════════════════════════════
// §2.6 / §4.4 — adoption_basis fail-closed resolution + the filing-state machine
// ══════════════════════════════════════════════════════════════════════════════════════════

export type FilingState =
  | 'not_requested'
  | 'filed'
  | 'awaiting_native_confirmation'
  | 'filing_path_not_yet_available'
  | 'filing_withheld_pending_native_signoff'
  | 'filing_failed'

/** ADJUDICATION-12: all four fields required together, or the call is a plain read. */
export interface AdoptInterventionInput {
  intervention_id: string
  confidence: number
  falsifier: string
  adoption_basis?: string | null
}

export interface FilingReadyPayload {
  action: 'prospective_ledger_file'
  entry: Record<string, unknown>
  withheld_reason: string
}

export interface FilingResolution {
  state: FilingState
  filing_ready_payload: FilingReadyPayload | null
  filed_prediction_id: string | null
  adoption_basis: 'native_directed' | 'session_inferred' | null
}

function buildFilingEntry(params: {
  chart_id: string
  event_class: string | null
  adopt: AdoptInterventionInput
  diagnosisStatement: string | null
}): Record<string, unknown> {
  return {
    chart_id: params.chart_id,
    intervention_class: 'upaya',
    event_class: params.event_class,
    claim: params.diagnosisStatement ?? `Adopted intervention ${params.adopt.intervention_id}`,
    falsifier: params.adopt.falsifier,
    confidence: params.adopt.confidence,
    source_citation: 'kala_upaya_get diagnosis + intervention row citation (see interventions[].citation)',
    model: 'kala_upaya_get/upaya-setu-w4',
    formula_version: 'upaya_setu_v1',
  }
}

/**
 * The §2.6/§4.4 filing-state machine, evaluated in the design's exact order (§4.4: "the
 * withhold predicate is the STRONGER constraint... so it is evaluated first"):
 *   1. no `adopt_intervention` supplied → `not_requested` (a plain read NEVER files).
 *   2. §5.3 withhold predicate matches the event class → `filing_withheld_pending_native_signoff`,
 *      regardless of `adoption_basis` — a `native_directed` basis does NOT override §3.5.C.
 *   3. `adoption_basis !== 'native_directed'` (explicit equality test, per ADJUDICATION-12's own
 *      instruction — "never as a `!== 'session_inferred'` negation" — so an absent, null, typo'd,
 *      or future third value all fail CLOSED) → `awaiting_native_confirmation`.
 *   4. otherwise (native_directed, not an adverse class) → `filing_path_not_yet_available`, NOT
 *      `filed` — `platform-mcp/src/lib/intervention_filing.ts` (Lane S's spine PR) does not exist
 *      in this build tier (design §0.3 sequencing note: "Until that spine PR merges, Lanes U and
 *      R... serve `filing_state: 'filing_path_not_yet_available'`... never a fabricated
 *      `filed: true`"). This is the ONE branch that changes once Lane S's spine lands: swap this
 *      return for an awaited call to `fileInterventionFalsifier`.
 * In every branch except `not_requested`, `filing_ready_payload` carries EXACTLY the body a
 * real filing call would send — so a native-directed follow-up call, once the spine exists, is
 * one hop and byte-identical to what was shown (design §4.4/§5.3: "the claim the native
 * confirms is byte-identical to the claim the native read").
 */
export function resolveFilingState(params: {
  chart_id: string
  event_class: string | null
  diagnosisStatement: string | null
  adopt?: AdoptInterventionInput | null
}): FilingResolution {
  if (!params.adopt) {
    return { state: 'not_requested', filing_ready_payload: null, filed_prediction_id: null, adoption_basis: null }
  }

  const entry = buildFilingEntry({
    chart_id: params.chart_id,
    event_class: params.event_class,
    adopt: params.adopt,
    diagnosisStatement: params.diagnosisStatement,
  })

  // Step 2: §5.3 withhold predicate — stronger than any tool-supplied basis.
  if (isAdverseWithholdClass(params.event_class)) {
    const ground = withholdGroundFor(params.event_class as string)
    return {
      state: 'filing_withheld_pending_native_signoff',
      filing_ready_payload: {
        action: 'prospective_ledger_file',
        entry,
        withheld_reason:
          `event_class="${params.event_class}" is on the §3.5.C sign-off requirement's withhold list ` +
          `(ground: ${ground}) — filing requires explicit native sign-off through this same route; ` +
          'the diagnosis, falsifier, and calibration band above are served in full regardless (§3.5.B ' +
          'is fully honoured; only the irreversible DB write is withheld).',
      },
      filed_prediction_id: null,
      adoption_basis: null,
    }
  }

  // Step 3: ADJUDICATION-12 fail-closed basis check — explicit equality, never a negation.
  const basisRaw = params.adopt.adoption_basis
  const isNativeDirected = basisRaw === 'native_directed'
  if (!isNativeDirected) {
    return {
      state: 'awaiting_native_confirmation',
      filing_ready_payload: {
        action: 'prospective_ledger_file',
        entry,
        withheld_reason:
          `adoption_basis="${String(basisRaw)}" is not the literal 'native_directed' — an absent, null, ` +
          'session_inferred, or unrecognised basis all fail CLOSED (ADJUDICATION-12). Re-call with ' +
          "adoption_basis: 'native_directed' once the native has confirmed this specific intervention.",
      },
      filed_prediction_id: null,
      adoption_basis: 'session_inferred',
    }
  }

  // Step 4: native_directed, not adverse — but the filing spine (Lane S, item 42) is not yet
  // available in this build tier. Never fabricate `filed: true`.
  return {
    state: 'filing_path_not_yet_available',
    filing_ready_payload: {
      action: 'prospective_ledger_file',
      entry,
      withheld_reason:
        'The sanctioned filing route (platform-mcp/src/lib/intervention_filing.ts, Lane S item 42 ' +
        'spine PR) has not landed in this build — an honest, named degradation ' +
        '(KALA_W4_UPAYA_DESIGN_v1_0.md §0.3 sequencing note), never a fabricated filed:true.',
    },
    filed_prediction_id: null,
    adoption_basis: 'native_directed',
  }
}

// ══════════════════════════════════════════════════════════════════════════════════════════
// §5.2 — disclosure tier (stated, never assumed)
// ══════════════════════════════════════════════════════════════════════════════════════════

export interface DisclosureBlock {
  audience_tier: 'native_self' | 'cohort_subject' | 'acharya_reviewer' | 'public_redacted'
  basis: string
  constraints_applied: string[]
}

const CANONICAL_NATIVE_CHART_IDS = new Set<string>([
  '482012f1-710e-4a25-994a-93821f5871aa',
  '1c826d5a-41cb-4450-b4dc-59d440e5f75a',
])

/**
 * Resolves and STATES the disclosure tier — never a silently-assumed default (design §5.2: "a
 * tool that assumes the most permissive tier is one principal-resolution bug away from serving
 * a non-consenting subject"). `platform-mcp` has no separate audience-tier resolution utility
 * at this build tier (the X-MCP-Audience-Tier header was excised project-wide — entitlement is
 * owned by the channel/entitlement layer, per `client.ts`'s own comments); this function
 * therefore resolves `native_self` ONLY for the two canonical charts this campaign is scoped
 * to, and states that basis explicitly rather than defaulting silently for any other chart_id.
 * A caller resolving a non-canonical chart gets `acharya_reviewer` (the narrower, non-self
 * tier) with a reason naming the gap — never a silent `native_self` broadening.
 */
export function resolveDisclosureTier(chartId: string, constraintsApplied: string[]): DisclosureBlock {
  if (CANONICAL_NATIVE_CHART_IDS.has(chartId)) {
    return {
      audience_tier: 'native_self',
      basis:
        `chart_id=${chartId} is one of the two ṢAḌ-DARŚANA canonical native charts — resolved ` +
        'native_self (full output, full calibration disclosure, unfiltered).',
      constraints_applied: constraintsApplied,
    }
  }
  return {
    audience_tier: 'acharya_reviewer',
    basis:
      `chart_id=${chartId} is not one of the two canonical native charts, and platform-mcp has no ` +
      'separate audience-tier resolution utility at this build tier (entitlement is owned by the ' +
      'channel layer) — resolved to the narrower acharya_reviewer tier rather than defaulting to ' +
      'the most permissive native_self (design §5.2 rail).',
    constraints_applied: constraintsApplied,
  }
}
