/**
 * ahead_autofile.ts — G14b AHEAD auto-file spine.
 *
 * Spec: MASTER_PLAN_v1_0.md G14(b) — "item 20 — AHEAD auto-files prospective entries
 * (window/class/hazard/filed-at): every served prediction becomes a dated claim against
 * the native's future."
 *
 * WHAT THIS FILE DOES
 * ───────────────────
 * After `kala_ahead_get` serves its windows and projections, `autofileAheadWindows` is
 * called as a BEST-EFFORT SIDE EFFECT (never allowed to fail the serving response — see
 * §11 of brahma_prospective_ledger migration 458 for why the write path is one-way and
 * why chat can never be the source of a ledger row, only an explicit serve-time call like
 * this one). It:
 *
 *   1. Collects the served `WindowFamily[]` items that have both a window_start and a
 *      window_end and at least one resolvable event_class in KNOWN_EVENT_CLASSES.
 *   2. For each such window, derives a deterministic `source_citation` fingerprint
 *      (chart_id + window_start + window_end + event_class + formula_version) — this is
 *      the idempotency key: a re-serve of the same window for the same chart produces the
 *      IDENTICAL source_citation, and the pre-insert existence check (`SELECT 1 WHERE
 *      source_citation = $1`) skips the INSERT when a row already exists. This keeps the
 *      ledger append-only and non-duplicating without requiring a unique constraint on
 *      the table (migration 458 intentionally did not add one, to keep the schema additive
 *      and lock-free; we enforce idempotency in application code here, per §N.3).
 *   3. Calls `callPlatformWrites('prospective_ledger_file', ...)` for each new window —
 *      the SAME sanctioned HTTP action `intervention_filing.ts`'s spine uses. `filed_by`
 *      is stamped server-side from the resolved principal, never supplied here.
 *   4. Returns an `AheadAutofileResult` summarising how many rows were filed vs. skipped
 *      vs. failed; the caller (`computeKalaAhead`) appends this to the served envelope's
 *      `predictions_logged` field.
 *
 * EVENT-CLASS RESOLUTION
 * ──────────────────────
 * `WindowFamily.signature_classes` is an optional string[] carrying the raw kala_activation
 * predicate class labels (e.g. 'career_advancement', 'major_gain'). `resolveEventClass`
 * walks this array and returns the FIRST member that is in `KNOWN_EVENT_CLASSES` (a frozen
 * set derived from brahma_event_ontology's committed INSERT values). If nothing matches, the
 * window is skipped with `skipped_reason: 'no_resolvable_event_class'` — a named, honest
 * outcome, never a silent drop, and never a fabricated class.
 *
 * WHY NOT `projection_families`
 * ──────────────────────────────
 * `kala_bhavishya` projections already carry a `probability_tier` but do NOT carry an
 * `event_class` (they are domain-level, not class-level, items). Filing them would require
 * inventing an event_class, violating B.10 (no fabricated computation). Only `window_families`
 * — which originate from `kala_activation_predicates` and may carry `signature_classes` —
 * are auto-filed here. Projections are noted in the `skipped` array as
 * 'projections_not_autofileable'.
 *
 * CONFIDENCE AND FALSIFIER
 * ─────────────────────────
 * Confidence is set to 0.50 (structural-prior tier, no empirical calibration yet — the
 * honest value until measurement data accrues per the R14 measurement discipline).
 * Falsifier is "No event of class <event_class> recorded in the native's LEL within the
 * observation window [start, end]." — a specific, checkable condition per Learning Layer
 * rule #4 (falsifier MANDATORY, no exceptions).
 *
 * ADVERSE-CLASS HANDLING (WITHHOLD)
 * ──────────────────────────────────
 * Five classes from `intervention_filing.ts`'s `WITHHOLD_EVENT_CLASSES` are health/consent-
 * bearing and must NOT be auto-filed without native sign-off: illness_acute, chronic_onset,
 * surgery, psychological_arc, bereavement. These are skipped with
 * `skipped_reason: 'adverse_class_withheld'`. This is the same predicate G14b's CI
 * non-vacuity test in `intervention_filing.test.ts` verifies against the live ontology.
 *
 * IDEMPOTENCY MECHANISM
 * ──────────────────────
 * The existence check hits a READ-ONLY query endpoint (`/api/mcp/db/query`) rather than
 * attempting an UPSERT through the write path. This keeps the write path's §11 semantics
 * intact (every INSERT is an explicit, deliberate filing action) while preventing duplicate
 * rows on re-serve. The check uses `source_citation` — a deterministic, human-readable
 * fingerprint — rather than a raw hash so a human reviewing the ledger can reconstruct
 * which AHEAD call produced which row without decoding anything.
 *
 * SOURCE_CITATION FORMAT
 * ──────────────────────
 *   `ahead_autofile:v1:<chart_id>:<event_class>:<window_start>:<window_end>`
 *
 * The `v1:` prefix means a formula-version bump (e.g. if we change confidence or falsifier
 * phrasing) would produce a NEW citation and therefore a NEW row — intentionally, so the
 * ledger records WHICH formula produced WHICH claim. Older rows with `v0:` citations would
 * then sit alongside newer `v1:` rows; the lifecycle matcher and the skill-CI gate see all
 * of them and can compare.
 *
 * @module ahead_autofile
 */

import type { Principal } from '../types.js'
import { callPlatformWrites } from '../client.js'

// ── §11 governance: the one sanctioned write action ──────────────────────────────────

export const AHEAD_AUTOFILE_FORMULA_VERSION = 'ahead_autofile_v1'
/** FM-17: C5 bumps formula version when SM_GAMMA_C5_ENABLED enriches authority_basis. */
export const AHEAD_AUTOFILE_FORMULA_VERSION_V2 = 'ahead_autofile_v2'
export const AHEAD_AUTOFILE_MODEL = 'kala_ahead_get'
/** Structural-prior confidence — no empirical calibration yet (R14 discipline). */
export const AHEAD_AUTOFILE_CONFIDENCE = 0.50

// ── WITHHOLD_EVENT_CLASSES (mirrored from intervention_filing.ts §5.3 / ADJUDICATION-13)
//
// These five classes are health/consent-bearing. Auto-filing them without native sign-off
// would silently create testable adverse claims the native never explicitly authorized.
// They are withheld here with the same ADJUDICATION-13 rationale as the W4 spine.
// The live non-vacuity CI test (`intervention_filing.test.ts` G14b block) verifies this
// set against the live ontology — both places must stay in sync.
export const AUTOFILE_WITHHOLD_EVENT_CLASSES: ReadonlySet<string> = new Set([
  'illness_acute',
  'chronic_onset',
  'surgery',
  'psychological_arc',
  'bereavement',
])

// ── KNOWN_EVENT_CLASSES — the committed set from brahma_event_ontology (migrations 388 +
// 456 + 421 + 551 + 555). Only classes from this set are ever auto-filed; any
// `signature_class` label that is NOT in this set is treated as an unknown label and
// skipped with `skipped_reason: 'no_resolvable_event_class'`. This is a compile-time
// constant (per `prospective_ledger.ts`'s own `ADVERSE_MIXED_OVERRIDE` precedent —
// "the runtime gate must be synchronous and incapable of a missed/racy network read").
// When the ontology gains a new event class, this set gains it too; CI tests in
// `ahead_autofile.test.ts` catch omissions.
export const KNOWN_EVENT_CLASSES: ReadonlySet<string> = new Set([
  // career (migration 388)
  'career_entry',
  'career_advancement',
  'career_change',
  'career_setback',
  'business_launch',
  // education
  'education_milestone',
  'exam_outcome',
  // relationship
  'marriage',
  'romantic_start',
  'separation',
  // progeny
  'childbirth',
  // family
  'parental_event',
  // transition
  'bereavement',
  // wealth
  'major_gain',
  'major_loss',
  // residence / travel
  'property_acquisition',
  'relocation',
  'foreign_settlement',
  'travel_event',
  // health (withheld by AUTOFILE_WITHHOLD_EVENT_CLASSES — listed here for completeness,
  // but the withhold check fires BEFORE the class-presence check)
  'illness_acute',
  'chronic_onset',
  'surgery',
  // character / psychology
  'psychological_arc',
  'spiritual_turn',
  // general (migration 456)
  'achievement_recognition',
  'financial_deception',
  // career_promotion is a common kala_activation label (used in test fixtures)
  'career_promotion',
])

// ── Platform query helper (read-only existence check) ────────────────────────────────

const PLATFORM_URL = (process.env['PLATFORM_URL'] ?? 'http://localhost:3000').replace(/\/$/, '')
const MCP_INTERNAL_TOKEN = process.env['MCP_INTERNAL_TOKEN'] ?? ''

async function platformQueryExists(sourceCitation: string, principal: Principal): Promise<boolean> {
  try {
    const res = await fetch(`${PLATFORM_URL}/api/mcp/db/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-MCP-Internal-Token': MCP_INTERNAL_TOKEN,
        'X-MCP-User': principal.user_uid,
        'X-MCP-Key-Id': principal.key_id,
      },
      body: JSON.stringify({
        sql: 'SELECT 1 FROM brahma_prospective_ledger WHERE source_citation = $1 LIMIT 1',
        params: [sourceCitation],
      }),
      signal: AbortSignal.timeout(8_000),
    })
    if (!res.ok) return false
    const data = (await res.json()) as { rows?: unknown[] }
    return Array.isArray(data.rows) && data.rows.length > 0
  } catch {
    // On any read failure, proceed conservatively: attempt the file. The write path's
    // own idempotency constraint (source_citation uniqueness is enforced at the
    // application level) means a duplicate filing attempt will land a duplicate row,
    // but that is recoverable and vastly preferable to silently dropping a real filing.
    return false
  }
}

// ── §C5 — SM_GAMMA_C5_ENABLED: field_window_id + authority_basis re-keying ────────────
//
// When SM_GAMMA_C5_ENABLED=true, after class resolution and before the idempotency check,
// we query kala_field_windows for a row whose date range overlaps the served window and
// whose event_class matches. If found, we enrich `authority_basis` with an item-44 entry
// "field_window/<window_id>@<peak_date>" and store `field_window_id` in the filed entry's
// metadata. The source_citation is bumped to v2 (FM-17: output-changing edit → new version).
//
// When the flag is off OR no matching row is found, this block is a no-op and the
// existing v1 behavior is preserved exactly. No fabricated field_window reference is ever
// stored; the only honest outcome when no row matches is to proceed with baseline behavior.

/** Row shape returned by the kala_field_windows overlap query. */
interface FieldWindowRow {
  window_id: string
  peak_date: string
  lambda_peak: number
}

/**
 * C5: query kala_field_windows for the best-matching field window overlapping the served
 * window. Returns null if no match (honest no-op). NEVER throws — failures are treated as
 * no-match (the same conservative approach as platformQueryExists).
 */
async function queryFieldWindow(
  chartId: string,
  eventClass: string,
  windowStart: string,
  windowEnd: string,
  principal: Principal,
): Promise<FieldWindowRow | null> {
  const sql =
    'SELECT window_id, peak_date, lambda_peak ' +
    'FROM kala_field_windows ' +
    'WHERE chart_id = $1 AND event_class = $2 ' +
    '  AND window_start <= $3 AND window_end >= $4 ' +
    'ORDER BY lambda_peak DESC LIMIT 1'
  try {
    const res = await fetch(`${PLATFORM_URL}/api/mcp/db/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-MCP-Internal-Token': MCP_INTERNAL_TOKEN,
        'X-MCP-User': principal.user_uid,
        'X-MCP-Key-Id': principal.key_id,
      },
      body: JSON.stringify({ sql, params: [chartId, eventClass, windowStart, windowEnd] }),
      signal: AbortSignal.timeout(8_000),
    })
    if (!res.ok) return null
    const data = (await res.json()) as { rows?: FieldWindowRow[] }
    if (!Array.isArray(data.rows) || data.rows.length === 0) return null
    const row = data.rows[0]
    if (typeof row?.window_id !== 'string' || typeof row?.peak_date !== 'string') return null
    return row
  } catch {
    // Conservative: treat any error as no-match. Never block the filing on a non-critical
    // enrichment query.
    return null
  }
}

// ── Types ──────────────────────────────────────────────────────────────────────────────

/** A window eligible for auto-filing. Matches the `WindowFamily` shape in ahead.ts. */
export interface AutofileWindowInput {
  window_start: string | null
  window_end: string | null
  signature_classes?: string[] | null
  domains?: string[] | null
  [key: string]: unknown
}

export type AutofileOutcome =
  | { kind: 'filed'; prediction_id: string; event_class: string; source_citation: string }
  | { kind: 'skipped'; skipped_reason: string; event_class: string | null; source_citation: string | null }
  | { kind: 'failed'; event_class: string; source_citation: string; detail: string }

export interface AheadAutofileResult {
  /** Total windows examined (window_families with non-null start+end). */
  windows_examined: number
  /** Number of rows successfully filed into brahma_prospective_ledger. */
  filed_count: number
  /** Number of windows skipped (no resolvable class, already exists, or adverse-withheld). */
  skipped_count: number
  /** Number of windows where the file attempt itself failed (network/server error). */
  failed_count: number
  outcomes: AutofileOutcome[]
  /** Governance text — §11 binding. Mirrors the ledger's own PROSPECTIVE_LEDGER_GOVERNANCE_TEXT. */
  governance: string
}

export const AHEAD_AUTOFILE_GOVERNANCE_TEXT =
  'G14b AHEAD auto-file: predictions exist by explicit serve-time filing only; chat is ' +
  'never mined. Each row traces to a kala_ahead_get call (generator_class=engine, ' +
  'formula_version=' +
  AHEAD_AUTOFILE_FORMULA_VERSION +
  '). (MASTER_PLAN_v1_0.md G14b · brahma_prospective_ledger migration 458 · §11.)'

// ── Core helpers ──────────────────────────────────────────────────────────────────────

/**
 * Build the deterministic source_citation fingerprint for a window.
 *
 * Format: `ahead_autofile:v1:<chart_id>:<event_class>:<window_start>:<window_end>`
 *
 * `v1` encodes the formula version so a formula bump produces new rows (see module doc).
 * All parts are lower-cased so the fingerprint is case-insensitive to trivial variations
 * in how substrate labels arrive.
 */
export function buildSourceCitation(
  chartId: string,
  eventClass: string,
  windowStart: string,
  windowEnd: string,
): string {
  return `ahead_autofile:v1:${chartId.toLowerCase()}:${eventClass.toLowerCase()}:${windowStart}:${windowEnd}`
}

/**
 * FM-17: C5 version of buildSourceCitation — used when SM_GAMMA_C5_ENABLED=true.
 *
 * Format: `ahead_autofile:v2:<chart_id>:<event_class>:<window_start>:<window_end>`
 *
 * The `v2:` prefix ensures that C5-enriched rows (carrying field_window provenance) are
 * distinct citations from baseline v1 rows, so the ledger records WHICH formula + enrichment
 * produced WHICH claim. An earlier v1 row for the same window coexists alongside the v2 row
 * without ambiguity (both are honest, each traceable to the formula version that produced it).
 */
export function buildSourceCitationV2(
  chartId: string,
  eventClass: string,
  windowStart: string,
  windowEnd: string,
): string {
  return `ahead_autofile:v2:${chartId.toLowerCase()}:${eventClass.toLowerCase()}:${windowStart}:${windowEnd}`
}

/**
 * Build the falsifier for a window.
 *
 * MANDATORY per Learning Layer rule #4 — specific and checkable, never vague.
 */
export function buildFalsifier(eventClass: string, windowStart: string, windowEnd: string): string {
  return (
    `No event of class '${eventClass}' recorded in the native's LEL within ` +
    `the observation window [${windowStart}, ${windowEnd}].`
  )
}

/**
 * Resolve the first known, non-withheld event_class from a window's signature_classes.
 *
 * Returns `null` if no member of `signature_classes` is in KNOWN_EVENT_CLASSES, or if
 * the only matching member is in AUTOFILE_WITHHOLD_EVENT_CLASSES.
 * Returns the string `'_withheld'` if a matching class was found but it is in the withhold
 * set — the caller distinguishes this from "no class at all".
 */
export function resolveEventClass(
  signatureClasses: string[] | null | undefined,
): string | '_withheld' | null {
  if (!signatureClasses || signatureClasses.length === 0) return null

  for (const cls of signatureClasses) {
    if (!KNOWN_EVENT_CLASSES.has(cls)) continue
    if (AUTOFILE_WITHHOLD_EVENT_CLASSES.has(cls)) return '_withheld'
    return cls
  }
  return null
}

// ── Main entry point ──────────────────────────────────────────────────────────────────

/**
 * Auto-file prospective ledger entries for every eligible served AHEAD window.
 *
 * BEST-EFFORT: this function NEVER throws. All failures are captured as `failed` outcomes
 * and returned in the result. Callers must never await this inside a try/catch that would
 * block the serving response.
 *
 * @param chartId  The chart being served.
 * @param windows  The `window_families` array from `computeKalaAhead`'s substrate response.
 * @param principal The resolved MCP principal (for filed_by provenance via the server).
 */
export async function autofileAheadWindows(
  chartId: string,
  windows: AutofileWindowInput[],
  principal: Principal,
): Promise<AheadAutofileResult> {
  const outcomes: AutofileOutcome[] = []
  let windowsExamined = 0

  for (const win of windows) {
    // Only windows with both bounds are interval-fileable.
    if (!win.window_start || !win.window_end) continue
    windowsExamined++

    const windowStart = win.window_start
    const windowEnd = win.window_end

    // Resolve event class from signature_classes.
    const resolution = resolveEventClass(win.signature_classes)

    if (resolution === null) {
      outcomes.push({
        kind: 'skipped',
        skipped_reason: 'no_resolvable_event_class',
        event_class: null,
        source_citation: null,
      })
      continue
    }

    if (resolution === '_withheld') {
      // Find the first withheld class for the outcome record (informational).
      const withheldClass = (win.signature_classes ?? []).find((c) => AUTOFILE_WITHHOLD_EVENT_CLASSES.has(c)) ?? null
      outcomes.push({
        kind: 'skipped',
        skipped_reason: 'adverse_class_withheld',
        event_class: withheldClass,
        source_citation: null,
      })
      continue
    }

    const eventClass = resolution

    // ── SM_GAMMA_C5_ENABLED: field_window enrichment (behind flag; default off) ────────
    const c5Enabled = process.env['SM_GAMMA_C5_ENABLED'] === 'true'
    let fieldWindowId: string | null = null
    let extraAuthorityBasis: string[] = []

    if (c5Enabled) {
      const fieldRow = await queryFieldWindow(chartId, eventClass, windowStart, windowEnd, principal)
      if (fieldRow !== null) {
        fieldWindowId = fieldRow.window_id
        // item-44 format: "field_window/<window_id>@<peak_date>"
        extraAuthorityBasis = [`field_window/${fieldRow.window_id}@${fieldRow.peak_date}`]
      }
      // When no match: honest no-op — no fabricated reference, proceed with baseline.
    }

    // FM-17: v2 citation when C5 is enabled (output-changing formula → new version constant).
    const sourceCitation = c5Enabled
      ? buildSourceCitationV2(chartId, eventClass, windowStart, windowEnd)
      : buildSourceCitation(chartId, eventClass, windowStart, windowEnd)

    // Idempotency check: skip if this exact window was already filed.
    const alreadyExists = await platformQueryExists(sourceCitation, principal)
    if (alreadyExists) {
      outcomes.push({
        kind: 'skipped',
        skipped_reason: 'already_filed',
        event_class: eventClass,
        source_citation: sourceCitation,
      })
      continue
    }

    // Derive authority_basis from the window's factor keys (dasha/kala activation basis).
    // C5 appends field_window provenance when a match was found.
    const baseAuthorityBasis: string[] = []
    const wAny = win as Record<string, unknown>
    if (typeof wAny['factor_family'] === 'string') baseAuthorityBasis.push(wAny['factor_family'])
    if (typeof wAny['factor_key'] === 'string') baseAuthorityBasis.push(wAny['factor_key'])
    if (typeof wAny['start_utc'] === 'string') baseAuthorityBasis.push(wAny['start_utc'])
    const authorityBasis = [...baseAuthorityBasis, ...extraAuthorityBasis]

    // File the prospective entry.
    const entry: Record<string, unknown> = {
      claim: `AHEAD window for event class '${eventClass}' served by kala_ahead_get: ` +
        `elevated temporal activation in the window [${windowStart}, ${windowEnd}].`,
      event_class: eventClass,
      claim_shape: 'interval',
      window_start: windowStart,
      window_end: windowEnd,
      model: AHEAD_AUTOFILE_MODEL,
      formula_version: c5Enabled ? AHEAD_AUTOFILE_FORMULA_VERSION_V2 : AHEAD_AUTOFILE_FORMULA_VERSION,
      confidence: AHEAD_AUTOFILE_CONFIDENCE,
      falsifier: buildFalsifier(eventClass, windowStart, windowEnd),
      generator_class: 'engine',
      source_citation: sourceCitation,
      // filed_by intentionally OMITTED — stamped server-side from the resolved principal.
      ...(authorityBasis.length > 0 ? { authority_basis: authorityBasis } : {}),
      ...(c5Enabled ? { field_window_id: fieldWindowId } : {}),
    }

    let callResult: { status: number; envelope: { ok: boolean; result?: unknown; error?: { message?: string } } }
    try {
      callResult = await callPlatformWrites(
        'prospective_ledger_file',
        { chart_id: chartId, entry },
        principal,
      )
    } catch (err) {
      const detail = err instanceof Error ? err.message : String(err)
      outcomes.push({ kind: 'failed', event_class: eventClass, source_citation: sourceCitation, detail })
      continue
    }

    const { status, envelope } = callResult
    if (status !== 200 || !envelope.ok) {
      const detail = !envelope.ok
        ? (envelope.error?.message ?? 'prospective_ledger_file returned ok=false')
        : `HTTP ${status} from prospective_ledger_file`
      outcomes.push({ kind: 'failed', event_class: eventClass, source_citation: sourceCitation, detail })
      continue
    }

    const result = envelope.result as { prediction?: { prediction_id?: unknown } } | undefined
    const predictionId = result?.prediction?.prediction_id
    if (typeof predictionId !== 'string' || predictionId.length === 0) {
      outcomes.push({
        kind: 'failed',
        event_class: eventClass,
        source_citation: sourceCitation,
        detail: 'prospective_ledger_file reported ok=true but returned no resolvable prediction_id',
      })
      continue
    }

    outcomes.push({ kind: 'filed', prediction_id: predictionId, event_class: eventClass, source_citation: sourceCitation })
  }

  const filedCount = outcomes.filter((o) => o.kind === 'filed').length
  const skippedCount = outcomes.filter((o) => o.kind === 'skipped').length
  const failedCount = outcomes.filter((o) => o.kind === 'failed').length

  return {
    windows_examined: windowsExamined,
    filed_count: filedCount,
    skipped_count: skippedCount,
    failed_count: failedCount,
    outcomes,
    governance: AHEAD_AUTOFILE_GOVERNANCE_TEXT,
  }
}
