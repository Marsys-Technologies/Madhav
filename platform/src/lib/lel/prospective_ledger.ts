/**
 * prospective_ledger.ts — D-4a Lane A-4 "Prospective ledger, LIVE".
 *
 * The live prediction store: TEMPORAL_ENGINE_ARC_PLAN §3 A-4 + §11 data governance,
 * BRIEF_D4A.md Lane A-4. Table: `brahma_prospective_ledger` (migration 458).
 *
 * §11 GOVERNANCE (binding, TEMPORAL_ENGINE_ARC_PLAN §11): predictions exist by
 * explicit filing only; chat is never mined. `fileProspectivePrediction` below is the
 * ONE sanctioned write path into this ledger — every row traces to an explicit call
 * to this function (or the `prospective_ledger_file` MCP tool that wraps it), never to
 * an inference drawn from a conversation transcript. The DB migration backs this with
 * a structural CHECK (`filing_method = 'explicit_filing_tool'`) so a write that
 * bypasses this module is a loud constraint failure, not a silent contamination.
 *
 * Shape enforcement: claim_shape MUST match the event_class's canonical
 * brahma_event_ontology.temporal_shape (DR-13/DIS.026 event-shape symmetry). This
 * module enforces it in application code via Lane A-2's
 * `validateClaimShape`/`assertClaimShape` (platform/src/lib/lel/event_ontology_shapes.ts)
 * BEFORE issuing the INSERT; migration 458's DB trigger enforces the identical rule a
 * second time at the database, so a mismatched shape is rejected at insert time no
 * matter which layer is bypassed.
 *
 * Outcome-matching hook: `matchOpenPredictionsForLelEvent` is the reusable core Lane
 * A-1's shape-aware matcher work is drawn on for — see the doc comment above that
 * function for exactly what is and is not reused from
 * platform/scripts/audit/t0_retrodiction/lib/checks.ts.
 *
 * @module prospective_ledger
 */

import 'server-only'
import crypto from 'crypto'
import { query } from '@/lib/db/client'
import {
  getEventClassOntology,
  assertClaimShape,
  type ClaimShape,
  type TemporalShape,
  type EventClassOntologyEntry,
} from './event_ontology_shapes'

// DR-13(d) confidence-scaled point tolerance — kept as a small local duplicate rather
// than a cross-directory import of platform/scripts/audit/t0_retrodiction/lib/checks.ts's
// identical `toleranceDaysFor`/`DateConfidence`. Reasoning: that script directory is
// executed standalone (tsx/node, outside the Next.js bundler) and a live import probe
// during this lane's work surfaced a Node 24 ESM/CJS interop cycle
// (ERR_REQUIRE_CYCLE_MODULE) when the two directories are cross-imported under `tsx`
// — importing it from `src/` risks the same fragility inside the Next.js build even
// where tsc/eslint see no error. The VALUES are the single source of truth
// (checks.ts's own comment cites DR-11/DIS.024's PROXIMITY_DAYS=45 and DR-13(d)'s
// month_known=75); if either changes, both call sites must change together (a
// property both files' test suites cover).
export type DateConfidence = 'exact' | 'month_known' | 'year_only'
const POINT_TOLERANCE_EXACT_DAYS = 45 // DR-11 (DIS.024)
const POINT_TOLERANCE_MONTH_KNOWN_DAYS = 75 // DR-13(d)
export function toleranceDaysFor(dateConfidence: DateConfidence): number {
  if (dateConfidence === 'exact') return POINT_TOLERANCE_EXACT_DAYS
  if (dateConfidence === 'month_known') return POINT_TOLERANCE_MONTH_KNOWN_DAYS
  return POINT_TOLERANCE_EXACT_DAYS // year_only is not point-scored primary; matched via the wider interval path upstream
}

// ── §11 governance text — embedded on the surface itself, not just in docs ─────────
//
// This exact string is returned in every fileProspectivePrediction/listOpenPredictions
// response payload (`governance` field) AND in the MCP tool descriptions that wrap
// this module (prospective_ledger.ts's MCP registration), per BRIEF_D4A's explicit
// requirement that §11 text be "served on the surface itself ... not just in a
// separate doc" — mirroring how judgment_query embeds judgment_flags (CLAUDE.md §N.6).
export const PROSPECTIVE_LEDGER_GOVERNANCE_TEXT =
  'Predictions exist by explicit filing only; chat is never mined. Every row in this ' +
  'ledger traces to an explicit filing action (fileProspectivePrediction / the ' +
  'prospective_ledger_file tool) — never inferred from a conversation transcript. ' +
  '(TEMPORAL_ENGINE_ARC_PLAN §11, DR-16.)'

// ── Types ────────────────────────────────────────────────────────────────────────

export type GeneratorClass =
  | 'anchor_engine'
  | 'reading_synthesis'
  | 'engine'
  | 'native_intuition'

export type LifecycleStatus = 'open' | 'matched' | 'confirmed' | 'falsified' | 'withdrawn'

export interface MilestoneEntry {
  milestone_id: string
  expected_date: string // ISO date — the reading's best-estimate target for this milestone
  name_en?: string
}

/** Input to fileProspectivePrediction. Exactly the shape-relevant subset for claim_shape is required. */
export interface FileProspectivePredictionInput {
  chart_id: string
  claim: string
  event_class: string
  claim_shape: TemporalShape
  /** point shape only. */
  point_date?: string
  /** interval shape only. */
  window_start?: string
  window_end?: string
  /** chain shape only. */
  milestones?: MilestoneEntry[]
  model: string
  formula_version: string
  confidence: number
  falsifier: string
  generator_class: GeneratorClass
  configuration_signature?: string | null
  filed_by: string
  source_citation: string
  /** REQUIRED when `generator_class === 'engine'` AND the event_class is
   * adverse-valence (BRIEF_D5 §4, DR-16 — hard acceptance item). Ignored/optional
   * for every other combination; `fileProspectivePrediction` rejects an adverse
   * engine claim missing this. */
  dr16_adverse_disclosure?: Dr16AdverseDisclosure
}

export interface ProspectiveLedgerRow {
  prediction_id: string
  chart_id: string
  claim: string
  event_class: string
  claim_shape: TemporalShape
  observation_window: string | null
  milestone_set: MilestoneEntry[] | null
  model: string
  formula_version: string
  confidence: number
  falsifier: string
  as_of: string
  generator_class: GeneratorClass
  configuration_signature: string | null
  lifecycle_status: LifecycleStatus
  matched_event_id: string | null
  matched_at: string | null
  match_note: string | null
  filed_by: string
  filing_method: string
  source_citation: string
  created_at: string
}

export interface FileProspectivePredictionResult {
  row: ProspectiveLedgerRow
  governance: string
  /** Present only for adverse-valence `generator_class='engine'` claims (BRIEF_D5 §4).
   * Not a persisted DB column — `brahma_prospective_ledger` (migration 458) was frozen
   * by D-4a's A-4 lane and G-5's may_touch does not include a new migration, so this
   * property is validated at filing time (mechanically REJECTED if incomplete, see
   * `assertDr16AdverseDisclosure`) and served back in this response — the "one served
   * payload" DR-16 §4 requires — rather than stored as its own column. It reconstructs
   * identically from the same inputs on any re-derivation, so nothing here is lost;
   * this is a documented engineering judgment call, see the G-5 session report. */
  dr16_disclosure?: Dr16AdverseDisclosure
}

// ── §D-5 Lane G-5 — engine claims, configuration_signature, DR-16 gate ─────────────
//
// BRIEF_D5.md §1 G-5 row + §4 (DR-16 honest-clarity gate on adverse serving) +
// §10/§11. This module already carried `generator_class: 'engine'` and an optional
// `configuration_signature` column (D-4a's A-4 pre-wired the column, migration 458,
// confirmed nullable — see BRIEF_D5 §B.4). G-5 adds: (1) a deterministic, reproducible
// `computeConfigurationSignature` derivation from a REAL `kala_gochara_windows` row
// (G-4's served output) or a G-3 `IntensityResult`-shaped source, so an engine claim's
// signature is never fabricated; (2) mechanical DR-16 five-property enforcement on
// adverse-valence engine claims, mirroring G-3's `CalibrationDisclosureError` pattern
// (models.py) — a hard REJECT, not a documented convention.

/** The subset of a real `kala_gochara_windows` row (G-4) — or an `IntensityResult`
 * (G-3, computed directly for a class G-4 hasn't swept yet) — `computeConfigurationSignature`
 * needs. Every field here must come from a genuine engine computation; nothing here is
 * free-form caller input. */
export interface EngineConfigurationSource {
  chart_id: string
  event_class: string
  temporal_shape: TemporalShape
  window_start: string // ISO date
  window_end: string // ISO date
  peak_date: string // ISO date
  /** DR-10 peak-basis provenance (e.g. 'gochara_lambda_e_v1') — mandatory per
   * migration 460's own column discipline. */
  peak_basis: string
  /** G-2 ConfigurationSentence.to_dict()-shaped entries carrying `fact_ids` —
   * the active configuration sentences at peak. Only `fact_ids` is read here. */
  active_sentences: Array<{ fact_ids?: unknown[] }>
  /** G-3 permission_detail.systems / G-4 contributing_systems — the DR-14
   * independent timing systems judged active at peak. Only `system_id` is read here. */
  contributing_systems: Array<{ system_id?: string }>
}

/**
 * Deterministic, reproducible fingerprint of the EXACT engine configuration that
 * produced a G-5 `generator_class='engine'` claim.
 *
 * Composition (engineering judgment, documented per BRIEF_D5's requirement — not a
 * doctrine ruling): a SHA-256 content hash of the pipe-joined, sorted tuple of
 *   `v1 | chart_id | event_class | temporal_shape | window_start | window_end |
 *    peak_date | peak_basis | sorted(unique fact_ids from active_sentences) |
 *    sorted(unique contributing system_ids)`
 * prefixed with the human-legible `peak_basis` so a signature is recognizable as
 * "which engine" produced it without decoding the hash. Sorting the fact_id / system_id
 * sets makes the signature independent of array ORDER (two runs that assemble the same
 * active-sentence pool in a different order still fingerprint identically — a
 * reproducibility property this function is explicitly designed to hold), while still
 * changing if the underlying configuration (which facts / which systems / which window)
 * changes. This is genuinely DERIVED from the source, never fabricated: every input
 * field traces to a real `kala_gochara_windows` row (G-4) or `IntensityResult` (G-3).
 */
export function computeConfigurationSignature(source: EngineConfigurationSource): string {
  const factIds = Array.from(
    new Set(
      source.active_sentences
        .flatMap((s) => (Array.isArray(s.fact_ids) ? s.fact_ids : []))
        .map((f) => String(f))
    )
  ).sort()
  const systemIds = Array.from(
    new Set(
      source.contributing_systems
        .map((s) => (s.system_id != null ? String(s.system_id) : null))
        .filter((s): s is string => s !== null)
    )
  ).sort()

  const canonical = [
    'v1',
    source.chart_id,
    source.event_class,
    source.temporal_shape,
    source.window_start,
    source.window_end,
    source.peak_date,
    source.peak_basis,
    factIds.join(','),
    systemIds.join(','),
  ].join('|')

  const digest = crypto.createHash('sha256').update(canonical).digest('hex')
  return `${source.peak_basis}:${digest}`
}

// ── DR-16 (DIS.029) — adverse-valence engine claim disclosure ─────────────────────

/** Mirrors `gochara_intensity.valence._ADVERSE_MIXED_OVERRIDE` (Python, G-3) exactly —
 * `psychological_arc` is 'mixed'-valence but is the wave brief's own named adverse
 * specimen; kept as its own named set so the exception stays visible in review, same
 * discipline as the Python original. */
const ADVERSE_MIXED_OVERRIDE = new Set(['psychological_arc'])

/** Sign decision mirrored from `gochara_intensity/valence.py` (G-3, the SAME rule,
 * so a claim filed via this ledger and a window served via `kala_gochara_windows`
 * never disagree on which classes are adverse). */
export function isAdverseEventClass(ontology: Pick<EventClassOntologyEntry, 'event_class_id' | 'evidence_requirements'>): boolean {
  return ontology.evidence_requirements.valence === 'loss' || ADVERSE_MIXED_OVERRIDE.has(ontology.event_class_id)
}

/** DR-16 property (2): "always probabilistic, never fatalistic ... no death-date,
 * ruin-date, or catastrophe point-claims". A textual honesty check on the two
 * free-text DR-16 fields — not a substitute for human judgment, but a mechanical
 * floor that rejects the specific failure mode DR-16 names by name. */
const FATALISTIC_PHRASE_PATTERNS: RegExp[] = [
  /\bwill die\b/i,
  /\bdeath date\b/i,
  /\bdate of death\b/i,
  /\bcertain(ly)? (to )?(die|lose|fail|happen)\b/i,
  /\bguaranteed\b/i,
  /\bscheduled (misfortune|death|ruin|doom)\b/i,
  /\bdoom(ed)?\b/i,
  /\bruin(ed|ation)?\b/i,
  /\bfated\b/i,
  /\binevitable\b/i,
]

function findFatalisticPhrase(text: string): string | null {
  for (const re of FATALISTIC_PHRASE_PATTERNS) {
    const m = text.match(re)
    if (m) return m[0]
  }
  return null
}

/** DR-16's five co-required disclosure properties (BRIEF_D5 §4), carried in ONE
 * served/filed payload — never split across calls, never served bare. */
export interface Dr16AdverseDisclosure {
  /** (1) Honest clarity: domain, window, mechanism stated clearly and specifically —
   * no euphemism. */
  honest_clarity: {
    domain: string
    window_description: string
    mechanism: string
  }
  /** (2) Always probabilistic, never fatalistic: framed as elevated hazard for an
   * event-CLASS, never a scheduled/certain misfortune. */
  probabilistic_framing: {
    hazard_statement: string
  }
  /** (4) Mitigation-paired: suppression analysis + a remedy-leverage pointer, in the
   * SAME payload, never bare. `remedy_pointer` REFERENCES the existing remedy-lookup
   * surface (`query_remedies` / `bodha_remedies_get`, `platform/src/lib/retrieval/
   * registry/layers/L2_bodha/query_remedies.ts`) rather than inventing a new one. */
  mitigation: {
    suppression_analysis: Record<string, unknown>
    remedy_pointer: {
      instrument: string
      params?: Record<string, unknown>
      hint: string
    }
  }
  /** (5) Confidence-honest: calibration_state/n_observations/control_delta disclosed
   * alongside the claim — n_observations/control_delta are explicit `null` (not
   * omitted) when honestly absent, per B.10 ("honestly absent, never omitted"). */
  confidence_disclosure: {
    calibration_state: 'structural_prior' | 'empirically_calibrated'
    n_observations: number | null
    control_delta: number | null
  }
}

/** Raised when an adverse-valence `generator_class='engine'` claim is filed without
 * ALL FIVE DR-16 properties present in one payload. Mirrors G-3's
 * `CalibrationDisclosureError` (gochara_intensity/models.py) mechanical-enforcement
 * pattern: DR-16 compliance is a code-level guarantee here, not a convention a caller
 * must remember to honor (BRIEF_D5 §4: "a hard acceptance item, not a diagnostic"). */
export class Dr16DisclosureError extends Error {}

/**
 * Throws `Dr16DisclosureError` unless `disclosure` carries all five DR-16 properties,
 * each individually well-formed:
 *   (1) honest_clarity.{domain,window_description,mechanism} all non-empty strings.
 *   (2) probabilistic_framing.hazard_statement non-empty AND free of the fatalistic-
 *       language patterns DR-16(2) names by name (no death/ruin/doom/certainty claims).
 *   (3) falsifier-bearing — checked by the caller via the SAME mandatory `falsifier`
 *       field every other ledger row requires (fileProspectivePrediction already
 *       enforces `falsifier` is non-empty before this function runs); re-asserted here
 *       so a caller invoking this function directly gets the same guarantee.
 *   (4) mitigation.suppression_analysis (non-empty object) AND mitigation.remedy_pointer
 *       (instrument + hint non-empty) both present — never one without the other.
 *   (5) confidence_disclosure.calibration_state present and valid; n_observations and
 *       control_delta are explicit keys (may be `null`, may not be `undefined`/absent).
 */
export function assertDr16AdverseDisclosure(
  falsifier: string | undefined,
  disclosure: Dr16AdverseDisclosure | null | undefined
): void {
  if (!disclosure) {
    throw new Dr16DisclosureError(
      'DR-16 violation: adverse-valence engine claim requires a dr16_adverse_disclosure payload ' +
        'carrying all 5 properties (honest_clarity, probabilistic_framing, falsifier, mitigation, ' +
        'confidence_disclosure) in the SAME filing — none was provided.'
    )
  }

  // (1) honest clarity
  const hc = disclosure.honest_clarity
  if (!hc || !hc.domain?.trim() || !hc.window_description?.trim() || !hc.mechanism?.trim()) {
    throw new Dr16DisclosureError(
      'DR-16(1) violation: honest_clarity requires non-empty domain, window_description, and ' +
        'mechanism — vagueness/euphemism/withholding is itself a disclosure failure (DR-16(1)).'
    )
  }

  // (2) always probabilistic, never fatalistic
  const pf = disclosure.probabilistic_framing
  if (!pf || !pf.hazard_statement?.trim()) {
    throw new Dr16DisclosureError(
      'DR-16(2) violation: probabilistic_framing.hazard_statement is required — an adverse claim ' +
        'must be framed as elevated hazard for an event-class, never left unstated.'
    )
  }
  const hcHit = findFatalisticPhrase(hc.mechanism) ?? findFatalisticPhrase(hc.window_description)
  const pfHit = findFatalisticPhrase(pf.hazard_statement)
  const hit = pfHit ?? hcHit
  if (hit) {
    throw new Dr16DisclosureError(
      `DR-16(2) violation: fatalistic language detected ('${hit}') — adverse claims are served as ` +
        'elevated hazard for an event-CLASS, never as a certain/scheduled misfortune or a death/' +
        'ruin/doom point-claim (DR-16(2)).'
    )
  }

  // (3) falsifier-bearing — same mandatory field every ledger row already carries.
  if (!falsifier || !falsifier.trim()) {
    throw new Dr16DisclosureError(
      'DR-16(3) violation: adverse claims enter the ledger like any other claim — falsifier is ' +
        'mandatory (re-asserted here; also enforced globally by fileProspectivePrediction).'
    )
  }

  // (4) mitigation-paired — suppression analysis AND remedy pointer, never one without the other.
  const mit = disclosure.mitigation
  const hasSuppression = !!mit?.suppression_analysis && Object.keys(mit.suppression_analysis).length > 0
  const hasRemedy = !!mit?.remedy_pointer?.instrument?.trim() && !!mit?.remedy_pointer?.hint?.trim()
  if (!hasSuppression || !hasRemedy) {
    throw new Dr16DisclosureError(
      'DR-16(4) violation: mitigation must carry BOTH a non-empty suppression_analysis AND a ' +
        'remedy_pointer (instrument + hint) in the SAME payload — an adverse window is never served ' +
        `bare. Missing: ${!hasSuppression ? 'suppression_analysis' : ''}${!hasSuppression && !hasRemedy ? ' and ' : ''}${!hasRemedy ? 'remedy_pointer' : ''}.`
    )
  }

  // (5) confidence-honest — keys must be PRESENT (null is honest; undefined/absent is not).
  const cd = disclosure.confidence_disclosure
  if (!cd || !cd.calibration_state || !('n_observations' in cd) || !('control_delta' in cd)) {
    throw new Dr16DisclosureError(
      'DR-16(5) violation: confidence_disclosure requires calibration_state plus explicit ' +
        "'n_observations' and 'control_delta' keys (null when honestly absent — never omitted)."
    )
  }
  if (cd.calibration_state !== 'structural_prior' && cd.calibration_state !== 'empirically_calibrated') {
    throw new Dr16DisclosureError(
      `DR-16(5) violation: confidence_disclosure.calibration_state must be 'structural_prior' or ` +
        `'empirically_calibrated', got '${cd.calibration_state}'.`
    )
  }
}

// ── Claim-shape -> DB row translation ───────────────────────────────────────────

/** Builds the A-2 ClaimShape value this input represents, for assertClaimShape. */
function toClaimShape(input: FileProspectivePredictionInput): ClaimShape {
  if (input.claim_shape === 'point') {
    if (!input.point_date) {
      throw new Error(
        `fileProspectivePrediction: claim_shape='point' requires point_date (event_class '${input.event_class}')`
      )
    }
    return { kind: 'point', date: input.point_date }
  }
  if (input.claim_shape === 'interval') {
    if (!input.window_start || !input.window_end) {
      throw new Error(
        `fileProspectivePrediction: claim_shape='interval' requires window_start and window_end (event_class '${input.event_class}')`
      )
    }
    return { kind: 'interval', start: input.window_start, end: input.window_end }
  }
  // chain
  if (!input.milestones || input.milestones.length === 0) {
    throw new Error(
      `fileProspectivePrediction: claim_shape='chain' requires at least one milestone (event_class '${input.event_class}')`
    )
  }
  return {
    kind: 'chain',
    milestones: input.milestones.map((m) => ({ milestone_id: m.milestone_id, date: m.expected_date })),
  }
}

// ── fileProspectivePrediction — THE sanctioned write path ──────────────────────────

/**
 * File a new prospective prediction. Enforces (in order):
 *   1. falsifier + confidence + all required fields present (throws otherwise —
 *      falsifier is MANDATORY, no exceptions).
 *   2. event_class exists in brahma_event_ontology (getEventClassOntology returns null
 *      -> UNKNOWN_EVENT_CLASS).
 *   3. claim_shape matches the ontology's canonical temporal_shape for event_class
 *      (Lane A-2's assertClaimShape — throws with the exact SHAPE_MISMATCH /
 *      INVERTED_INTERVAL / etc. violation on failure). This is APPLICATION-level
 *      enforcement; migration 458's DB trigger enforces the same rule a second time
 *      at the database as defense in depth.
 *   4. confidence strictly in (0, 1) — DB CHECK also enforces this; checked here first
 *      for a clean error message instead of a raw Postgres constraint-violation string.
 *
 * Returns the inserted row plus the §11 governance text (BRIEF_D4A: "served on the
 * surface itself").
 */
export async function fileProspectivePrediction(
  input: FileProspectivePredictionInput
): Promise<FileProspectivePredictionResult> {
  if (!input.falsifier || input.falsifier.trim().length === 0) {
    throw new Error('fileProspectivePrediction: falsifier is MANDATORY — no exceptions (Learning Layer rule #4).')
  }
  if (!(input.confidence > 0 && input.confidence < 1)) {
    throw new Error(
      `fileProspectivePrediction: confidence must be in the open interval (0, 1); got ${input.confidence}.`
    )
  }
  if (!input.filed_by || input.filed_by.trim().length === 0) {
    throw new Error('fileProspectivePrediction: filed_by is required (§11 explicit-filing provenance).')
  }

  const ontology = await getEventClassOntology(input.event_class)
  if (!ontology) {
    throw new Error(
      `fileProspectivePrediction: unknown event_class '${input.event_class}' — not present in brahma_event_ontology.`
    )
  }

  // ── D-5 Lane G-5 (BRIEF_D5 §1 G-5 / §10): configuration_signature is MANDATORY,
  // non-null for every engine-generated claim — this is the hard "populated (non-null)"
  // ledger requirement, enforced here rather than left to convention.
  if (input.generator_class === 'engine' && !input.configuration_signature) {
    throw new Error(
      "fileProspectivePrediction: generator_class='engine' requires a non-null " +
        'configuration_signature (BRIEF_D5 §10) — derive one with computeConfigurationSignature ' +
        'from a real kala_gochara_windows row (G-4) or IntensityResult (G-3); never fabricate it.'
    )
  }

  // ── DR-16 (DIS.029) §4 — hard acceptance gate on adverse-valence engine claims.
  const isAdverse = input.generator_class === 'engine' && isAdverseEventClass(ontology)
  if (isAdverse) {
    assertDr16AdverseDisclosure(input.falsifier, input.dr16_adverse_disclosure)
  }

  const claim = toClaimShape(input)
  // Throws with the precise ShapeViolation(s) on mismatch — e.g. a point-claim
  // against an interval-shaped class (major_gain, major_loss, ...) is rejected here
  // before any SQL is issued.
  assertClaimShape(ontology, claim)

  let observationWindowLiteral: string | null = null
  let milestoneSetJson: string | null = null

  if (input.claim_shape === 'point') {
    const d = input.point_date as string
    observationWindowLiteral = `[${d},${addOneDay(d)})`
  } else if (input.claim_shape === 'interval') {
    observationWindowLiteral = `[${input.window_start},${input.window_end}]`
  } else {
    milestoneSetJson = JSON.stringify(input.milestones)
  }

  const { rows } = await query<ProspectiveLedgerRow>(
    `INSERT INTO brahma_prospective_ledger
        (chart_id, claim, event_class, claim_shape, observation_window, milestone_set,
         model, formula_version, confidence, falsifier, generator_class,
         configuration_signature, filed_by, source_citation)
     VALUES
        ($1::uuid, $2, $3, $4, $5::daterange, $6::jsonb,
         $7, $8, $9, $10, $11,
         $12, $13, $14)
     RETURNING prediction_id, chart_id, claim, event_class, claim_shape,
               observation_window::text, milestone_set, model, formula_version,
               confidence, falsifier, as_of, generator_class, configuration_signature,
               lifecycle_status, matched_event_id, matched_at, match_note,
               filed_by, filing_method, source_citation, created_at`,
    [
      input.chart_id,
      input.claim,
      input.event_class,
      input.claim_shape,
      observationWindowLiteral,
      milestoneSetJson,
      input.model,
      input.formula_version,
      input.confidence,
      input.falsifier,
      input.generator_class,
      input.configuration_signature ?? null,
      input.filed_by,
      input.source_citation,
    ]
  )

  const row = rows[0]
  if (!row) throw new Error('fileProspectivePrediction: INSERT returned no row.')
  return {
    row,
    governance: PROSPECTIVE_LEDGER_GOVERNANCE_TEXT,
    ...(isAdverse ? { dr16_disclosure: input.dr16_adverse_disclosure } : {}),
  }
}

function addOneDay(isoDate: string): string {
  const d = new Date(`${isoDate}T00:00:00Z`)
  d.setUTCDate(d.getUTCDate() + 1)
  return d.toISOString().slice(0, 10)
}

function subOneDay(isoDate: string): string {
  const d = new Date(`${isoDate}T00:00:00Z`)
  d.setUTCDate(d.getUTCDate() - 1)
  return d.toISOString().slice(0, 10)
}

/**
 * Postgres always normalizes a daterange to canonical exclusive-upper-bound form
 * on read (`[start,end)`), regardless of the `[`/`]` notation used on insert. For a
 * point claim this is exactly what we constructed (`[d, d+1)`), so `point_date =
 * lower`. For an interval claim filed as `[window_start, window_end]` (inclusive), the
 * stored/read-back upper bound is `window_end + 1` — this helper converts back to the
 * human-facing inclusive `window_end` a caller filed. Chain shape returns nulls (no
 * observation_window on a chain row).
 */
export function deriveWindowFields(
  row: Pick<ProspectiveLedgerRow, 'claim_shape' | 'observation_window'>
): { point_date: string | null; window_start: string | null; window_end: string | null } {
  if (!row.observation_window) return { point_date: null, window_start: null, window_end: null }
  const parsed = parseDaterange(row.observation_window)
  // Postgres EMPTY range == no window: same all-null shape as a missing window.
  if (!parsed) return { point_date: null, window_start: null, window_end: null }
  const [start, end] = parsed
  if (row.claim_shape === 'point') return { point_date: start, window_start: null, window_end: null }
  return { point_date: null, window_start: start, window_end: subOneDay(end) }
}

// ── Query surface ────────────────────────────────────────────────────────────────

export interface ListOpenPredictionsResult {
  rows: ProspectiveLedgerRow[]
  governance: string
}

/** List predictions for a chart, optionally filtered by lifecycle_status/event_class. */
export async function listProspectivePredictions(
  chartId: string,
  opts: { status?: LifecycleStatus; eventClass?: string; limit?: number } = {}
): Promise<ListOpenPredictionsResult> {
  const conditions: string[] = ['chart_id = $1']
  const params: unknown[] = [chartId]
  if (opts.status) {
    params.push(opts.status)
    conditions.push(`lifecycle_status = $${params.length}`)
  }
  if (opts.eventClass) {
    params.push(opts.eventClass)
    conditions.push(`event_class = $${params.length}`)
  }
  const limit = opts.limit ?? 50
  params.push(limit)

  const { rows } = await query<ProspectiveLedgerRow>(
    `SELECT prediction_id, chart_id, claim, event_class, claim_shape,
            observation_window::text, milestone_set, model, formula_version,
            confidence, falsifier, as_of, generator_class, configuration_signature,
            lifecycle_status, matched_event_id, matched_at, match_note,
            filed_by, filing_method, source_citation, created_at
       FROM brahma_prospective_ledger
      WHERE ${conditions.join(' AND ')}
      ORDER BY as_of DESC
      LIMIT $${params.length}`,
    params
  )
  return { rows, governance: PROSPECTIVE_LEDGER_GOVERNANCE_TEXT }
}

// ── §2 — LEL-append -> outcome-matching hook (Lane A-1 reuse) ──────────────────────
//
// This hook fires when a new LEL event is appended (see the caller site in
// platform/src/app/api/mcp/writes/[action]/route.ts's lel_event_record handler,
// alongside the existing enqueueLelRecalibration best-effort side effect). It is
// DELIBERATELY a lighter-weight cousin of Lane A-1's checks.ts matcher, not a
// reimport of scoreShapeAwareEvent itself:
//
//   - checks.ts's scoreShapeAwareEvent scores a MODEL's computed activation curve
//     (built from dasha periods + significators) against a real event — "does the
//     model predict elevated activation near this date". That requires a
//     significator set, which is a per-technique astrological configuration this
//     ledger row does not carry (a filed claim is "X will happen by Y", not "here is
//     my curve-generating significator set").
//   - This hook answers a different, simpler question: "does a newly-recorded LEL
//     event's shape/date OVERLAP an OPEN prediction's claimed shape/window for the
//     SAME event_class" — i.e. real-world outcome detection for reading_synthesis /
//     native_intuition / engine claims, not model scoring. That is exactly what a
//     prospective ledger's outcome-matching means (BRIEF_D4A: "auto-check if any
//     falsifier/claim now has a matching real-world outcome").
//
// What IS reused directly from Lane A-1's matcher: `toleranceDaysFor` (DR-13(d) —
// exact=±45d / month_known=±75d confidence-scaled point tolerance) — the identical
// function checks.ts's scorePointEvent calls, imported here rather than
// re-implemented, so a point-shaped claim is matched against a point-shaped LEL event
// with the SAME tolerance discipline the model-scoring harness uses. This is the
// "triggerable via Lane A-1's matcher" integration BRIEF_D4A asks for.

export interface LelEventForMatching {
  chart_id: string
  life_event_id: string // life_events.id (uuid)
  event_class: string
  event_date: string // ISO date
  date_confidence?: DateConfidence // defaults to 'exact' — matches the DB column default
  interval_start?: string | null
  interval_end?: string | null
  milestone_label?: string | null
}

export interface MatchCandidate {
  prediction_id: string
  claim: string
  claim_shape: TemporalShape
  match_note: string
}

/**
 * Match a newly-appended LEL event against this chart's OPEN predictions in the same
 * event_class. Any candidate match transitions the row to lifecycle_status='matched'
 * (a human/reading-synthesis call still promotes matched -> confirmed|falsified — this
 * hook flags candidates, it does not itself adjudicate truth). Returns the list of
 * rows that were matched (empty if none).
 *
 * Best-effort: a caller (route.ts) should treat this as a non-fatal side effect,
 * mirroring the existing enqueueLelRecalibration pattern at the same call site — a
 * failure here must never fail the underlying LEL append.
 */
export async function matchOpenPredictionsForLelEvent(
  event: LelEventForMatching
): Promise<MatchCandidate[]> {
  const { rows: open } = await query<ProspectiveLedgerRow>(
    `SELECT prediction_id, chart_id, claim, event_class, claim_shape,
            observation_window::text, milestone_set, model, formula_version,
            confidence, falsifier, as_of, generator_class, configuration_signature,
            lifecycle_status, matched_event_id, matched_at, match_note,
            filed_by, filing_method, source_citation, created_at
       FROM brahma_prospective_ledger
      WHERE chart_id = $1::uuid AND event_class = $2 AND lifecycle_status = 'open'`,
    [event.chart_id, event.event_class]
  )

  const matches: MatchCandidate[] = []
  const eventDate = new Date(`${event.event_date}T00:00:00Z`).getTime()
  const dateConfidence: DateConfidence = event.date_confidence ?? 'exact'
  const toleranceMs = toleranceDaysFor(dateConfidence) * 86_400_000

  for (const row of open) {
    let hit = false
    let note = ''

    if (row.claim_shape === 'point' && row.observation_window && parseDaterange(row.observation_window)) {
      const [pointStart] = parseDaterange(row.observation_window) as [string, string]
      const diffMs = Math.abs(eventDate - new Date(`${pointStart}T00:00:00Z`).getTime())
      if (diffMs <= toleranceMs) {
        hit = true
        note = `LEL event ${event.life_event_id} (${event.event_date}) is within ${dateConfidence} tolerance (±${toleranceDaysFor(dateConfidence)}d) of point claim ${pointStart}.`
      }
    } else if (row.claim_shape === 'interval' && row.observation_window && parseDaterange(row.observation_window)) {
      const [winStart, winEnd] = parseDaterange(row.observation_window) as [string, string]
      const evStart = event.interval_start ?? event.event_date
      const evEnd = event.interval_end ?? event.event_date
      const overlap =
        new Date(`${evStart}T00:00:00Z`).getTime() <= new Date(`${winEnd}T00:00:00Z`).getTime() &&
        new Date(`${evEnd}T00:00:00Z`).getTime() >= new Date(`${winStart}T00:00:00Z`).getTime()
      if (overlap) {
        hit = true
        note = `LEL event ${event.life_event_id} [${evStart}, ${evEnd}] overlaps interval claim [${winStart}, ${winEnd}].`
      }
    } else if (row.claim_shape === 'chain' && row.milestone_set && event.milestone_label) {
      const known = row.milestone_set.some((m) => m.milestone_id === event.milestone_label)
      if (known) {
        hit = true
        note = `LEL event ${event.life_event_id}'s milestone_label '${event.milestone_label}' matches a milestone in chain claim ${row.prediction_id}'s milestone_set.`
      }
    }

    if (hit) {
      await query(
        `UPDATE brahma_prospective_ledger
            SET lifecycle_status = 'matched', matched_event_id = $2::uuid, matched_at = now(), match_note = $3
          WHERE prediction_id = $1::uuid`,
        [row.prediction_id, event.life_event_id, note]
      )
      matches.push({ prediction_id: row.prediction_id, claim: row.claim, claim_shape: row.claim_shape, match_note: note })
    }
  }

  return matches
}

/** Parses a Postgres daterange text representation, e.g. "[2027-04-09,2027-08-19)" -> ['2027-04-09','2027-08-18']. Handles both '[' and ')'/']' bound styles.
 *
 * Returns `null` for Postgres's EMPTY range, whose canonical text literal is the bare
 * word `empty` — a legal daterange value, not corrupt data (PARIPŪRṆA audit, 2026-08-15).
 * LIVE DEFECT this closes: `standing_predictions_read` threw
 * "could not parse daterange literal 'empty'" and 500'd for EVERY caller on the
 * canonical chart, because 6 brahma_prospective_ledger rows carry
 * observation_window='empty' with claim_shape='interval' AND lifecycle_status='open'
 * — i.e. the tool's DEFAULT (status=open) read returns them on the happy path.
 * Semantics: an empty window is "no window", so callers treat it exactly as a missing
 * observation_window (null derived dates; matches no event) rather than throwing.
 * NOTE (separate, filed): rows SHOULD not normally be filed with an empty window —
 * the producer that created these 6 is a distinct write-path question, deliberately
 * NOT conflated with this read-path crash fix.
 */
function parseDaterange(text: string): [string, string] | null {
  if (text.trim().toLowerCase() === 'empty') return null
  const m = text.match(/[[(]([^,]*),([^)\]]*)[)\]]/)
  if (!m) throw new Error(`parseDaterange: could not parse daterange literal '${text}'`)
  return [m[1] as string, m[2] as string]
}
