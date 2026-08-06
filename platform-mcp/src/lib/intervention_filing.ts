/**
 * intervention_filing.ts — ṢAḌ-DARŚANA W4 Lane S "spine": the published contract for
 * filing an adopted intervention's falsifiable prospective entry.
 *
 * Spec: `00_ARCHITECTURE/llm_consumption_audit/briefs/kala_elevation/
 * KALA_W4_UPAYA_DESIGN_v1_0.md` (v1.1) §4.4 (the filing spine), §4.1 ruling S-1 (the
 * prediction spine is `brahma_prospective_ledger` — `mi_sankalpa` never inserts into it
 * directly; filing happens here, at serve time, through the sanctioned HTTP action),
 * §5.3 (ADJUDICATION-13's withhold predicate) and ADJUDICATION-12 (the `adoption_basis`
 * fail-closed rule). `SHAD_DARSHANA_BRIEF_v2_0.md` §2.5 (Nirmāṇa) + §7 (rails) bind the
 * wider campaign; this file's own binding rails are the two gates in `§4.4 ORDERING`
 * below.
 *
 * SEQUENCING (KALA_W4_UPAYA_DESIGN §0.3, binding): this file plus the one-line widening
 * of `callPlatformWrites`'s action union in `client.ts` is Lane S's SPINE PR — it lands
 * FIRST, alone, ahead of the `mi_sankalpa` writer PR, because Lane U's `kala_upaya_get`
 * and Lane R's `kala_ritual_get` / `kala_elect_get` rite-pairing path both build against
 * this published type. Until this PR is merged, those two lanes serve
 * `filing_state: 'filing_path_not_yet_available'` — an honest, named state, never a
 * silent omission and never a fabricated `filed: true`.
 *
 * WHAT THIS FILE DOES NOT DO (§4.4, verbatim): "Beyond [the two gates] the function adds
 * no validation of its own — every other rule (`claim_shape` vs `temporal_shape`, DR-16's
 * five-property adverse gate, `filed_by` stamping) is already enforced server-side, and
 * duplicating a validator is how two copies drift." Every non-gate rejection this module
 * can produce is therefore reported as `filing_failed` with the server's verbatim error —
 * never re-derived or re-worded here.
 */

import type { McpEnvelope, Principal } from '../types.js'
import { callPlatformWrites } from '../client.js'

// ── Platform DB proxy (read-only; used ONLY by the G14b non-vacuity check below, never
//    by the runtime filing gate — see WITHHOLD_EVENT_CLASSES comment). Same shape as
//    `register_gochara_windows.ts`'s `platformQuery` / `registry_bridge.ts`'s. ─────────

const PLATFORM_URL = (process.env['PLATFORM_URL'] ?? 'http://localhost:3000').replace(/\/$/, '')
const MCP_INTERNAL_TOKEN = process.env['MCP_INTERNAL_TOKEN'] ?? ''

async function platformQuery(
  sql: string,
  params: unknown[],
  principal: Principal
): Promise<{ rows: Record<string, unknown>[] }> {
  const res = await fetch(`${PLATFORM_URL}/api/mcp/db/query`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-MCP-Internal-Token': MCP_INTERNAL_TOKEN,
      'X-MCP-User': principal.user_uid,
      'X-MCP-Key-Id': principal.key_id,
    },
    body: JSON.stringify({ sql, params }),
    signal: AbortSignal.timeout(15_000),
  })
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(`[intervention_filing] platform DB query failed (${res.status}): ${text.slice(0, 200)}`)
  }
  return res.json() as Promise<{ rows: Record<string, unknown>[] }>
}

// ── §5.3 — the withhold predicate (ADJUDICATION-13, amendments A + B) ──────────────────
//
// v1.0's predicate (`domain='health' AND magnitude_floor IN ('major','life_altering')`)
// matched ZERO rows against the live ontology — an Earned-Signal (§N.7/§N.8) failure: a
// guardrail that cannot be shown to fire is not evidence the danger is absent. The
// corrected, magnitude-free, three-disjunct predicate:
//
//   SELECT event_class_id FROM brahma_event_ontology
//    WHERE domain = 'health'                 -- illness_acute · chronic_onset · surgery
//       OR lel_category = 'psychological'     -- psychological_arc (domain='character')
//       OR event_class_id = 'bereavement';     -- consent ground (amendment B), NOT health
//
// resolves, verified against the live ontology at design time, to exactly five classes.
// That resolved set is hardcoded here (mirroring `prospective_ledger.ts`'s own
// `ADVERSE_MIXED_OVERRIDE` precedent for the identical reason: the runtime gate must be
// synchronous and incapable of a missed/racy network read on every filing call) and
// `resolveWithholdEventClassesLive` below is the live twin a CI test (gate G14b) runs
// against the real DB to assert the hardcoded set has not silently drifted from the
// ontology and is non-empty — the check that would have caught v1.0's no-op.
export const WITHHOLD_PREDICATE_SQL =
  "SELECT event_class_id FROM brahma_event_ontology " +
  "WHERE domain = 'health' OR lel_category = 'psychological' OR event_class_id = 'bereavement'"

export const WITHHOLD_EVENT_CLASSES: ReadonlySet<string> = new Set([
  'illness_acute',
  'chronic_onset',
  'surgery',
  'psychological_arc',
  'bereavement',
])

/** G14b's live twin. Resolves `WITHHOLD_PREDICATE_SQL` against the LIVE
 *  `brahma_event_ontology` — never called by the runtime filing gate (which must stay
 *  synchronous), only by the non-vacuity CI assertion. */
export async function resolveWithholdEventClassesLive(principal: Principal): Promise<Set<string>> {
  const { rows } = await platformQuery(WITHHOLD_PREDICATE_SQL, [], principal)
  return new Set(rows.map((r) => String(r['event_class_id'])))
}

// ── §5.4 — individualized-mortality-window HARD EXCLUSION, defence in depth ────────────
//
// ADJUDICATION-13, binding: no W4 surface may read āyurdāya/longevity facts into any
// window bound, under any tier, filed or unfiled. The primary defence lives at Lane U's
// `kala_upaya_get` and Lane R's `kala_ritual_get`/`kala_elect_get` entry points (they run
// the detector FIRST, before any substrate read). This module never reads
// `ganita_ayurdaya_get` or any longevity/āyurdāya substrate — it has no capability to
// compose a mortality window in the first place. Its role here is the "defence in depth"
// §5.4 names for `fileInterventionFalsifier`: a pure, synchronous REQUEST-SHAPE check
// (test 2 of §5.4's three) that refuses to file a claim whose own text names a
// mortality/longevity subject, in case one somehow reached this far.
const MORTALITY_REQUEST_SHAPE_PATTERN = /ayurdaya|longevity|\bmaraka\b|\bayus\b|date[\s-]?of[\s-]?death|death[\s-]?date/i

function isMortalityWindowShapedRequest(input: Pick<FileInterventionFalsifierInput, 'event_class' | 'claim' | 'falsifier'>): boolean {
  return (
    MORTALITY_REQUEST_SHAPE_PATTERN.test(input.event_class) ||
    MORTALITY_REQUEST_SHAPE_PATTERN.test(input.claim) ||
    MORTALITY_REQUEST_SHAPE_PATTERN.test(input.falsifier)
  )
}

// ── The published contract ──────────────────────────────────────────────────────────

/** ADJUDICATION-12 + -13 (v1.1): 'filing_refused_adverse_class' is RENAMED
 * 'filing_withheld_pending_native_signoff' — "refused" misdescribed the native's own
 * manual-filing option, which is itself a §3.5.B under-service. 'awaiting_native_confirmation'
 * is the session_inferred / absent-basis fail-closed outcome. */
export type FilingState =
  | 'not_requested'
  | 'filed'
  | 'awaiting_native_confirmation'
  | 'filing_path_not_yet_available'
  | 'filing_withheld_pending_native_signoff'
  | 'filing_failed'

export interface FilingReadyPayload {
  /** Exactly the body the sanctioned route would have received. Returned, never sent,
   *  whenever filing was withheld — so a native-directed follow-up is one hop and
   *  nothing is recomposed (a recomposed claim would not be the claim the native saw). */
  action: 'prospective_ledger_file'
  entry: Record<string, unknown>
  withheld_reason: string
}

export interface FileInterventionFalsifierInput {
  chart_id: string
  intervention_class: 'upaya' | 'yajna' | 'elected_activity'
  event_class: string
  claim: string
  /** MANDATORY — the route rejects a blank one. */
  falsifier: string
  /** Strictly in (0,1) — the route rejects the endpoints. */
  confidence: number
  window: { start: string; end: string }
  source_citation: string
  model: string
  formula_version: string
  /** ADJUDICATION-12. REQUIRED. Anything other than the literal 'native_directed' —
   *  including undefined, null, and any unrecognised string — fails CLOSED to
   *  'awaiting_native_confirmation'. Written as an explicit equality test against the
   *  one filing value, never as a `!== 'session_inferred'` negation: a negation would
   *  let a typo, a future third basis, or a dropped field fall through into a
   *  permanent seal. */
  adoption_basis: 'native_directed' | 'session_inferred'
}

export interface FileInterventionFalsifierResult {
  state: FilingState
  prediction_id: string | null
  filing_ready_payload: FilingReadyPayload | null
  detail: string | null
}

function buildEntry(input: FileInterventionFalsifierInput): Record<string, unknown> {
  // claim_shape is always 'interval' here — every intervention this wave files carries
  // an elected_window (start, end). If the target event_class is canonically
  // 'point'-shaped, the server's shape-vs-ontology trigger rejects the write and this
  // module reports `filing_failed` with the verbatim error (§4.4: "adds no validation
  // of its own" — the shape check is the server's, never duplicated here).
  return {
    claim: input.claim,
    event_class: input.event_class,
    claim_shape: 'interval',
    window_start: input.window.start,
    window_end: input.window.end,
    model: input.model,
    formula_version: input.formula_version,
    confidence: input.confidence,
    falsifier: input.falsifier,
    // Every intervention filed through this spine is composed by the engine
    // (B.10's prose rule; template-over-computed-data), never taken verbatim from an
    // agentic caller's free text — coupling this entry to DR-16's adverse-disclosure
    // gate is intentional, not incidental.
    generator_class: 'engine',
    source_citation: input.source_citation,
    // filed_by is intentionally OMITTED — the route stamps it from the resolved
    // principal (X-MCP-User), never trusted from the caller body (§4.4 / ADJUDICATION-12
    // "filed_by = MCP principal ... provenance, not authorship").
  }
}

/**
 * THE filing spine. Two gates, in this exact order, both BEFORE the network call that
 * would actually file (§4.4):
 *   1. The §5.3 withhold predicate — an adverse/consent-bearing class withholds the
 *      filing and returns `filing_withheld_pending_native_signoff`.
 *   2. The ADJUDICATION-12 basis check — `adoption_basis === 'native_directed'` or
 *      return `awaiting_native_confirmation`.
 * Ordering matters and is not arbitrary: the withhold predicate is the STRONGER
 * constraint (a `native_directed` basis does NOT override it — §3.5.C's sign-off
 * requirement is not satisfiable by a tool parameter), so it is evaluated first and its
 * state is the one reported.
 *
 * A gate-0 check (§5.4 defence in depth) runs before both, pure and synchronous, and
 * short-circuits completely on a mortality/longevity-shaped request — see
 * `isMortalityWindowShapedRequest` above.
 */
export async function fileInterventionFalsifier(
  input: FileInterventionFalsifierInput,
  principal: Principal
): Promise<FileInterventionFalsifierResult> {
  // Gate 0 — §5.4 defence in depth. Not a filing gate in the §5.3 sense (this governs
  // computation, per ADJUDICATION-13) — reported via the closed `filing_failed` state
  // with a detail naming the exclusion, since the FilingState set has no dedicated
  // member for it and this module's only capability is filing, never reading.
  if (isMortalityWindowShapedRequest(input)) {
    return {
      state: 'filing_failed',
      prediction_id: null,
      filing_ready_payload: null,
      detail:
        'refused: individualized-mortality-window HARD EXCLUSION (MACRO_PLAN §3.5.C, ' +
        'ADJUDICATION-13 §5.4) — no W4 surface may file a longevity/mortality-shaped ' +
        'claim, under any audience tier, filed or unfiled.',
    }
  }

  const entry = buildEntry(input)

  // Gate 1 — §5.3 withhold predicate.
  if (WITHHOLD_EVENT_CLASSES.has(input.event_class)) {
    return {
      state: 'filing_withheld_pending_native_signoff',
      prediction_id: null,
      filing_ready_payload: {
        action: 'prospective_ledger_file',
        entry,
        withheld_reason:
          `event_class '${input.event_class}' is in the §5.3 adverse/consent-bearing ` +
          'withhold set (MACRO_PLAN §3.5.A p3/p6, §3.5.C, §3.5.D; ADJUDICATION-13). The ' +
          'diagnosis, falsifier, window, and calibration band are served in full — only ' +
          'the irreversible DB write is withheld. File manually, native-directed, via ' +
          'this filing_ready_payload, at any time.',
      },
      detail: null,
    }
  }

  // Gate 2 — ADJUDICATION-12 fail-closed adoption_basis check.
  if (input.adoption_basis !== 'native_directed') {
    return {
      state: 'awaiting_native_confirmation',
      prediction_id: null,
      filing_ready_payload: {
        action: 'prospective_ledger_file',
        entry,
        withheld_reason:
          "adoption_basis was not the literal 'native_directed' value (ADJUDICATION-12 " +
          'fail-closed: absent, null, session_inferred, and any unrecognised value all ' +
          'resolve here). Resubmit as a native-directed call to file.',
      },
      detail: null,
    }
  }

  // Both gates passed — the one network call.
  let callResult: { status: number; envelope: McpEnvelope }
  try {
    callResult = await callPlatformWrites(
      'prospective_ledger_file',
      { chart_id: input.chart_id, entry },
      principal
    )
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err)
    return { state: 'filing_failed', prediction_id: null, filing_ready_payload: null, detail: message }
  }

  const { status, envelope } = callResult
  if (status !== 200 || !envelope.ok) {
    const message = !envelope.ok
      ? (envelope.error?.message ?? 'prospective_ledger_file failed')
      : `HTTP ${status} from prospective_ledger_file`
    return { state: 'filing_failed', prediction_id: null, filing_ready_payload: null, detail: message }
  }

  const result = envelope.result as { prediction?: { prediction_id?: unknown } } | undefined
  const predictionId = result?.prediction?.prediction_id
  if (typeof predictionId !== 'string' || predictionId.length === 0) {
    return {
      state: 'filing_failed',
      prediction_id: null,
      filing_ready_payload: null,
      detail: 'prospective_ledger_file reported ok=true but returned no resolvable prediction_id',
    }
  }

  return { state: 'filed', prediction_id: predictionId, filing_ready_payload: null, detail: null }
}

// ── The serve-time Intervention Ledger write path (item 42, gate G7) ────────────────────
//
// KALA_W4_UPAYA_DESIGN §4.1 ruling S-1: `mi_sankalpa` (the Python writer) never ORIGINATES
// a ledger row from an elected candidate — it only re-classifies/links already-filed rows.
// Rows are "FILED live, at serve time, through the sanctioned HTTP action" (migration 532's
// own comment). Until this function landed, no such action existed anywhere under
// `platform-mcp/src` — the gap PR #1055's harness lane disclosed. This is that write path:
// one function, calling the platform's `intervention_ledger_record` write action, which
// inserts into `mimamsa_intervention_ledger` with `filed_by` stamped from the resolved
// principal server-side (provenance, never trusted from this body — same rule as
// `prospective_ledger_file`).
//
// §N.3 note: the natural key UNIQUE (chart_id, intervention_class, rite_or_activity_class,
// elected_window) makes re-recording the same adoption idempotent — the route reports
// `created: false` with the existing row's id rather than erroring or duplicating.

export interface RecordInterventionLedgerInput {
  chart_id: string
  /** The native's own stated purpose for the intervention (NOT NULL, non-blank). */
  intent: string
  intervention_class: 'upaya' | 'yajna' | 'elected_activity'
  rite_or_activity_class: string
  event_class: string | null
  window: { start: string; end: string }
  precision_regime: 'intra_day' | 'day_grade'
  precision_basis: string
  /** Frozen snapshot of the judgment at election time (JudgmentLedger verbatim for an
   *  elected act; the diagnosis snapshot for an upāya adoption). Never recomputed (§5.5). */
  adjudication_record: Record<string, unknown>
  /** The 4-factor vector + which factors were present; an honest empty for an upāya
   *  adoption where no election score participated. */
  score_vector: Record<string, unknown>
  efficacy_tier: 'classically_attested' | 'traditional' | 'speculative_extension'
  source_citation: string
  paddhati_version: string
  predicted_differential: string
  /** The sealed brahma_prospective_ledger row this intervention references (ruling S-1) —
   *  null iff no prospective entry was filed (the §4.2 CHECK makes session_inferred +
   *  non-null prediction_id structurally impossible at the DB). */
  prediction_id: string | null
  adoption_basis: 'native_directed' | 'session_inferred'
  authority_basis: string | null
  engine_version: string
}

export interface RecordInterventionLedgerResult {
  recorded: boolean
  intervention_id: string | null
  /** false when the natural key already existed (idempotent re-record). */
  created: boolean
  detail: string | null
}

export async function recordInterventionLedgerEntry(
  input: RecordInterventionLedgerInput,
  principal: Principal
): Promise<RecordInterventionLedgerResult> {
  // §5.4 defence in depth — identical shape to the filing gate above: a ledger row whose
  // own text names a mortality/longevity subject is refused before any network call.
  if (
    MORTALITY_REQUEST_SHAPE_PATTERN.test(input.event_class ?? '') ||
    MORTALITY_REQUEST_SHAPE_PATTERN.test(input.intent) ||
    MORTALITY_REQUEST_SHAPE_PATTERN.test(input.predicted_differential)
  ) {
    return {
      recorded: false,
      intervention_id: null,
      created: false,
      detail:
        'refused: individualized-mortality-window HARD EXCLUSION (MACRO_PLAN §3.5.C, ' +
        'ADJUDICATION-13 §5.4) — no W4 surface may record a longevity/mortality-shaped ' +
        'intervention, under any audience tier.',
    }
  }

  const { chart_id, window, ...rest } = input
  const entry: Record<string, unknown> = {
    ...rest,
    window_start: window.start,
    window_end: window.end,
    // filed_by intentionally OMITTED — stamped server-side from the resolved principal.
  }

  let callResult: { status: number; envelope: McpEnvelope }
  try {
    callResult = await callPlatformWrites('intervention_ledger_record', { chart_id, entry }, principal)
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err)
    return { recorded: false, intervention_id: null, created: false, detail: message }
  }

  const { status, envelope } = callResult
  if (status !== 200 || !envelope.ok) {
    const message = !envelope.ok
      ? (envelope.error?.message ?? 'intervention_ledger_record failed')
      : `HTTP ${status} from intervention_ledger_record`
    return { recorded: false, intervention_id: null, created: false, detail: message }
  }

  const result = envelope.result as { intervention_id?: unknown; created?: unknown } | undefined
  const interventionId = result?.intervention_id
  if (typeof interventionId !== 'string' || interventionId.length === 0) {
    return {
      recorded: false,
      intervention_id: null,
      created: false,
      detail: 'intervention_ledger_record reported ok=true but returned no resolvable intervention_id',
    }
  }

  return {
    recorded: true,
    intervention_id: interventionId,
    created: result?.created === true,
    detail: null,
  }
}
