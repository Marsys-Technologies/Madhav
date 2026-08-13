/**
 * kala_envelope.ts — ṢAḌ-DARŚANA W0.3 (SHAD_DARSHANA_BRIEF_v2_0.md §3 W0.3 · §2 file map).
 * ==========================================================================
 * THE ONE shared envelope implementation for the eight kala_* views/capabilities
 * (`kala_now_get`, `kala_ahead_get`, `kala_elect_get`, `kala_story_get`,
 * `kala_priority_get`, `kala_explain_get`, `kala_upaya_get`, `kala_ritual_get`).
 * This lane (w0-spine) builds ONLY this shared library + `argument_composer.ts` — the
 * eight tool facades that CONSUME this envelope are a separate lane's job (W0.4).
 *
 * SAMPŪRTI-γ C4/C5 (2026-08-13): SM_GAMMA_C4_ENABLED gates gochara_narrative injection into
 * kala_now_get and a5_gochara_agreement into kala_explain_get (§N.8 byte-identical flag-off
 * discipline). SM_GAMMA_C5_ENABLED gates ahead_autofile field_window/<id>@<peak> citation.
 *
 * Design authority (highest wins on conflict): KALA_SUPREME_ELEVATION_v1_0.md (v1.2,
 * "the Elevation") §5 (E3/E4/E5 — argument · question_frame · continuity), §7 (Living-LEL
 * calibration_maturity), §11 (item 43 — tri-plane traversability), CLAUDE.md §N.6 (Serving
 * Density Principle / hardFloor discipline). Every field this file emits traces to a
 * specific Elevation §-reference cited inline below.
 *
 * WHAT THIS FILE IS NOT (W0 scope discipline — see brief §3 W0.3):
 *   - It does NOT compute anything astrological. It is pure envelope/shape + small,
 *     deterministic assembly helpers. The actual field/point-process math lands at W2
 *     (`ka_kshetra`); this file only reserves the SHAPE that math will fill in.
 *   - It does NOT implement the `authority_basis` / item-44 census machinery (that is a
 *     separate registry item with its own CI census, seeded at W0 "beside" this file per
 *     the brief, not inside it).
 *   - It does NOT implement CI (specificity gate, tri-plane no-dead-end battery, etc.) —
 *     those are W0.6 CI skeletons, a distinct file set.
 */

import type { TrimmableSection } from './response_budget.js'

// ── E3 (Elevation §5) — the argument-shaped reading ────────────────────────────────
// "thesis → strongest evidence (2–3 drivers with fact_ids) → strongest counter-current
// or dissent → verdict with tier → falsifier / cost-of-inaction." Template-composed,
// deterministic, B.10-clean — the actual prose composition lives in argument_composer.ts;
// this file only defines the STRUCTURE the composer consumes.

/** One evidentiary driver for the thesis. `fact_ids` traces to L1/L2+ facts (§N.5 —
 *  an L2+ signal never restates an L1 value, it references the fact_id). */
export interface ArgumentEvidence {
  claim: string
  fact_ids: string[]
  /** Optional graded strength — omit when the underlying signal has no graded strength
   *  (a bare presence/absence fact). Never fabricated to fill the field (B.10). */
  strength?: 'strong' | 'moderate' | 'weak'
}

/** The strongest counter-current or dissenting system/clock — served as intelligence,
 *  never hidden (Elevation §0 vision property 4: "disagreement served as intelligence"). */
export interface ArgumentDissent {
  claim: string
  fact_ids: string[]
  /** Which system/clock/method dissents (e.g. 'KP sub-lord clock', 'vimshottari daśā'). */
  source: string
}

/** Calibration tier vocabulary mirrors the Living-LEL three-scenario contract
 *  (Elevation §7): a chart with no LEL serves `structural_prior`; a growing chart
 *  migrates tier-by-tier as maturity crosses thresholds; `unresolved` is the honest
 *  state when neither prior nor calibration currently supports a claim. */
export type ArgumentVerdictTier = 'structural_prior' | 'calibrated_provisional' | 'calibrated' | 'unresolved'

export interface ArgumentVerdict {
  statement: string
  tier: ArgumentVerdictTier
}

/** The falsifier / cost-of-inaction clause. `resolves_by` is an ISO date when the claim
 *  has a natural resolution horizon; `null` is the honest value for an open-ended claim
 *  (never a fabricated date — B.10). */
export interface ArgumentFalsifier {
  statement: string
  resolves_by: string | null
}

export interface ArgumentReading {
  thesis: string
  evidence: ArgumentEvidence[]
  dissent: ArgumentDissent[]
  verdict: ArgumentVerdict
  /** `null` is legal — not every reading has a stated falsifier yet (e.g. a pure
   *  interpretation-plane NOW state with no open prediction). Never invented. */
  falsifier: ArgumentFalsifier | null
}

/** W0 skeleton-level well-formedness check (NOT the W2 hard specificity gate — that gate
 *  proves chart-specificity across a cohort; this only proves the shape is non-vacuous).
 *  Useful in tests and as a cheap runtime assertion in the eight tool facades. */
export function isWellFormedArgumentReading(reading: ArgumentReading): boolean {
  return (
    typeof reading.thesis === 'string' &&
    reading.thesis.trim().length > 0 &&
    reading.verdict != null &&
    typeof reading.verdict.statement === 'string' &&
    reading.verdict.statement.trim().length > 0
  )
}

// ── E4 (Elevation §5) — the question_frame parameter shape ─────────────────────────
// "Every view accepts optional `question_frame` — {domain, entity, horizon, intent_verb,
// stakes, comparison_target} — and relevance scoring, insight selection, and reading
// composition all condition on it. The chart is ALWAYS implicit (the session's chart);
// the frame is the only per-question input."

export interface QuestionFrame {
  /** e.g. 'career', 'marriage', 'health', 'wealth' — the domain vocabulary this product
   *  already shares product-wide (CLAUDE.md §7 rail: ONE canonical domain vocabulary). */
  domain?: string
  /** The specific undertaking/entity the question concerns, if named (e.g. 'the Singapore
   *  role', 'this contract'). Free text — no enum, the question compiler owns extraction. */
  entity?: string
  /** A time horizon expressed as the caller stated it (e.g. '90d', 'next 24 months'),
   *  not yet resolved to a concrete window — that resolution is the view's job. */
  horizon?: string
  /** The verb naming the user's intent (e.g. 'should_i', 'when_should_i', 'what_is'). */
  intent_verb?: string
  /** Free-text statement of what is at stake, if the caller supplied one. */
  stakes?: string
  /** For CONTRAST-shaped questions: what this reading should be diffed against
  *   ('last_month' | 'last_year' | a pinned field_snapshot_id | another named option). */
  comparison_target?: string
}

// ── E5 (Elevation §5) — field_snapshot_id (dialogue continuity) ────────────────────
// "Every envelope carries `field_snapshot_id` (the field build hash). Follow-ups resolve
// against the same snapshot: ids stable, EXPLAIN drills always land, CONTRAST insights
// computable against the pinned baseline."
//
// W2 (ṢAḌ-DARŚANA w2-envelope-real-snapshot lane): the W0 stub
// (`buildFieldSnapshotIdStub` — 'stub:key=value;…' composed from substrate build ids) is
// RETIRED. `ka_kshetra` (python sidecar, `services/ka_kshetra/writer.py`) now computes the
// REAL snapshot row: `kala_field_snapshots.field_snapshot_id = 'kfs_' + sha256(pins)[:32]`
// and `field_content_hash = 'kfh_' + sha256(stage-0–8 rows)[:32]` (KALA_W2_FIELD_DESIGN
// _v1_0.md §7.4). This function reads the chart's NEWEST snapshot row and serves it.
//
// HONESTY CONTRACT (B.10 / §N.8): production `kala_field_snapshots` is EMPTY until the
// first field build runs. When no row exists for the chart, the envelope serves the
// explicit marker `FIELD_NOT_YET_BUILT` plus a reason — NEVER a fabricated id and NEVER a
// silent null. When the read itself cannot be performed (route rejects the table / DB
// unreachable / the migration creating the table has not been applied), the DISTINCT
// marker `FIELD_SNAPSHOT_UNREACHABLE` is served — "not built" and "could not look" are
// different honest states and must not be conflated (mirrors the 3-state coverage
// vocabulary below: honest_empty vs not-evaluable).

/** Honest marker served as `field_snapshot_id` when the read succeeded but the chart has
 *  no `kala_field_snapshots` row yet (the first field build has not run). */
export const FIELD_NOT_YET_BUILT = 'field_not_yet_built'

/** Honest marker served as `field_snapshot_id` when the snapshot read itself could not be
 *  performed (DB proxy rejected/unreachable) — distinct from "built nothing yet". */
export const FIELD_SNAPSHOT_UNREACHABLE = 'field_snapshot_unreachable'

export type FieldSnapshotState = 'served' | 'field_not_yet_built' | 'field_snapshot_unreachable'

export interface FieldSnapshotResolution {
  /** `'kfs_…'` (real, from the newest `kala_field_snapshots` row) when state='served';
   *  otherwise exactly `FIELD_NOT_YET_BUILT` or `FIELD_SNAPSHOT_UNREACHABLE`. */
  field_snapshot_id: string
  /** `'kfh_…'` when served; `null` otherwise. Feeds `KalaFreshness.field_hash` (the
   *  envelope slot the design names for it — KALA_W2_FIELD_DESIGN_v1_0.md §9's note that
   *  `buildKalaFreshness` reads `kala_field_snapshots` at W2). */
  field_content_hash: string | null
  field_snapshot_state: FieldSnapshotState
  /** Required in substance whenever state !== 'served'; `null` when served. */
  field_snapshot_reason: string | null
}

/** Structural subset of `Principal` (types.ts) — declared here so this lib does not
 *  import the tool-layer type; any real `Principal` satisfies it. */
export interface FieldSnapshotPrincipalLike {
  user_uid: string
  key_id: string
}

/**
 * Reads the chart's newest `kala_field_snapshots` row through the platform's whitelisted
 * read-only DB proxy (`POST /api/mcp/db/query`) — the SAME serving path every kala_views
 * facade already uses for its own direct-SQL reads (now.ts / ahead.ts /
 * register_gochara_windows.ts precedent; the MCP server holds no direct DB connection).
 *
 * "Newest" is a total order (§N.7 item 2): `ORDER BY built_at DESC, field_snapshot_id
 * DESC LIMIT 1` — never a bare category read that could flap between generations.
 *
 * THE ONE replacement point the W0 stub's TODO reserved: every one of the eight kala_*
 * facades goes through this function; none composes its own snapshot id.
 *
 * KNOWN HONEST GAP (disclosed, not papered over): until `kala_field_snapshots` is added
 * to the db/query route's `ALLOWED_TABLES` whitelist
 * (platform/src/app/api/mcp/db/query/route.ts — owned outside this lane's file contract),
 * the route 400s the query and this function serves `FIELD_SNAPSHOT_UNREACHABLE` with the
 * route's own reason text. That marker is CORRECT for that state — the moment the
 * whitelist entry lands, this same code path starts serving real rows with no further
 * change here.
 */
export async function resolveFieldSnapshot(
  chartId: string,
  principal: FieldSnapshotPrincipalLike,
): Promise<FieldSnapshotResolution> {
  const platformUrl = (process.env['PLATFORM_URL'] ?? 'http://localhost:3000').replace(/\/$/, '')
  const internalToken = process.env['MCP_INTERNAL_TOKEN'] ?? ''
  try {
    const res = await fetch(`${platformUrl}/api/mcp/db/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-mcp-internal-token': internalToken,
        'x-mcp-user': principal.user_uid,
        'x-mcp-key-id': principal.key_id,
      },
      body: JSON.stringify({
        sql:
          'SELECT field_snapshot_id, field_content_hash FROM kala_field_snapshots ' +
          'WHERE chart_id = $1 ORDER BY built_at DESC, field_snapshot_id DESC LIMIT 1',
        params: [chartId],
      }),
      signal: AbortSignal.timeout(10_000),
    })
    if (!res.ok) {
      const text = await res.text().catch(() => '')
      return {
        field_snapshot_id: FIELD_SNAPSHOT_UNREACHABLE,
        field_content_hash: null,
        field_snapshot_state: 'field_snapshot_unreachable',
        field_snapshot_reason:
          `kala_field_snapshots read failed (HTTP ${res.status}): ${text.slice(0, 200)} — ` +
          'served as an explicit unreachable marker, never a fabricated id (B.10).',
      }
    }
    const data = (await res.json()) as { rows?: Array<Record<string, unknown>> }
    const row = data.rows?.[0]
    const snapshotId = typeof row?.['field_snapshot_id'] === 'string' ? (row['field_snapshot_id'] as string) : null
    if (!row || !snapshotId) {
      return {
        field_snapshot_id: FIELD_NOT_YET_BUILT,
        field_content_hash: null,
        field_snapshot_state: 'field_not_yet_built',
        field_snapshot_reason:
          'ka_kshetra has written no kala_field_snapshots row for this chart yet — the first ' +
          'field build has not run. Honest empty marker per B.10/§N.8; the real ' +
          "'kfs_…' id is served automatically once the field build lands.",
      }
    }
    return {
      field_snapshot_id: snapshotId,
      field_content_hash:
        typeof row['field_content_hash'] === 'string' ? (row['field_content_hash'] as string) : null,
      field_snapshot_state: 'served',
      field_snapshot_reason: null,
    }
  } catch (err) {
    return {
      field_snapshot_id: FIELD_SNAPSHOT_UNREACHABLE,
      field_content_hash: null,
      field_snapshot_state: 'field_snapshot_unreachable',
      field_snapshot_reason:
        `kala_field_snapshots read threw (${err instanceof Error ? err.message : String(err)}) — ` +
        'served as an explicit unreachable marker, never a fabricated id (B.10).',
    }
  }
}

// ── item 43 (Elevation §11) — tri-plane traversability pointers ────────────────────
// "every served temporal object carries live pointers into the other two planes... or an
// honest `no_lever (reason)`." CI battery (a separate W0.6 lane): no view ships a row that
// dead-ends. This file only defines the SHAPE the no-dead-end battery checks against.

export interface DrillPointerLike {
  instrument: string
  hint: string
}

/** The honest "no lever exists" terminal state — distinct from a missing/omitted pointer
 *  (which the tri-plane no-dead-end CI battery treats as a defect). A `KalaNoLever` value
 *  IS the pointer slot filled in, honestly, with a reason — never a silent `null`. */
export interface KalaNoLever {
  no_lever: true
  reason: string
}

export type TriPlanePointer = DrillPointerLike | KalaNoLever

export interface TriPlanePointers {
  /** Points at the interpretive ground for this object (e.g. an EXPLAIN chain). `null`
   *  only legal when this object IS the interpretation plane already. */
  interpretation_ref: TriPlanePointer | null
  /** Points at the predictive continuation (e.g. `ahead_ref`). `null` only legal when
   *  this object IS the prediction plane already. */
  prediction_ref: TriPlanePointer | null
  /** Points at the intervention lever (`elect_ref` / `upaya_ref` / `ritual_ref`), or an
   *  honest `KalaNoLever` when none exists for this object. */
  intervention_ref: TriPlanePointer | null
}

export function pointerTo(instrument: string, hint: string): DrillPointerLike {
  return { instrument, hint }
}

export function noLeverPointer(reason: string): KalaNoLever {
  return { no_lever: true, reason }
}

export function isNoLever(pointer: TriPlanePointer | null | undefined): pointer is KalaNoLever {
  return pointer != null && (pointer as KalaNoLever).no_lever === true
}

// ── 3-state coverage (Elevation §5 envelope note) ───────────────────────────────────
// "three-state coverage (`served` / `empty_for_this_chart` / `not_computed`)". This file
// names the three states `computed` / `honest_empty` / `not_in_corpus` to match the more
// specific vocabulary the Elevation design uses elsewhere for the SAME distinction (§9
// Muhūrta Factor Census: "computed / not_computed / not_in_corpus"; §8 Mode-2 fixture PASS
// condition 4). `honest_empty` = computed the check, chart has nothing there right now;
// `not_in_corpus` = the corpus/rule table this concept needs is not ingested (an honest
// gap, filed as an ingestion work item — never silently dropped, B.10).

export type CoverageState = 'computed' | 'honest_empty' | 'not_in_corpus'

export interface KalaCoverageEntry {
  /** Names the concept family this entry covers (e.g. 'recurrence_ladder',
   *  'agnivasa_residence') — stable enough for a completeness-census CI diff. */
  concept: string
  state: CoverageState
  /** Required in substance (not type-enforced — B.10 forbids fabricating a reason as much
   *  as fabricating data) whenever state !== 'computed'. See `honestEmptyCoverage` /
   *  `notInCorpusCoverage` below, which make the reason mandatory at the call site. */
  reason?: string
}

export function computedCoverage(concept: string): KalaCoverageEntry {
  return { concept, state: 'computed' }
}

export function honestEmptyCoverage(concept: string, reason: string): KalaCoverageEntry {
  return { concept, state: 'honest_empty', reason }
}

export function notInCorpusCoverage(concept: string, reason: string): KalaCoverageEntry {
  return { concept, state: 'not_in_corpus', reason }
}

// ── freshness attestation (Elevation §5 / §12 E7.2) ─────────────────────────────────
// "every envelope names ephemeris version, sweep build date, field hash; staleness served
// as a flag, never silently (kills the LC-5 class at serving)."

export interface KalaFreshness {
  ephemeris_version: string | null
  sweep_build_date: string | null
  field_hash: string | null
  /**
   * `true` / `false` only when a real detector ran; `null` when staleness is genuinely
   * NOT EVALUABLE this call (CLAUDE.md §N.8 Earned-Signal Principle: "a signal without a
   * real detector is null, not green").
   *
   * ṢAḌ-DARŚANA W1 verify-reopen fix (ND-2), 2026-07-30: this field was previously typed
   * `boolean` and every W0/W1 facade served a confident `stale: false` while
   * `ephemeris_version`, `sweep_build_date` AND `field_hash` were all `null` — i.e. an
   * unfalsifiable freshness claim, asserted with literally zero attestation evidence behind
   * it and no code path that could ever have produced `true`. `false` there did not mean
   * "verified fresh", it meant "no horizon was supplied", which is the §N.8 defect exactly.
   */
  stale: boolean | null
  stale_reason: string | null
}

/** The honest `stale_reason` when no attestation evidence exists to evaluate staleness
 *  against. Exported so the tri-plane/coverage CI batteries can assert on the exact string
 *  rather than re-spelling it (and so a future W2 wiring pass can grep every consumer). */
export const KALA_FRESHNESS_NOT_EVALUABLE_REASON =
  'Staleness not evaluable this call: no attestation evidence available (ephemeris_version, ' +
  'sweep_build_date and field_hash are all null, and the substrate declared no horizon). ' +
  'A confident `stale: false` here would be an unfalsifiable claim — reported as null per ' +
  'CLAUDE.md §N.8 (Earned-Signal Principle). Real ephemeris/sweep/field attestation lands ' +
  'with ka_kshetra at wave W2 (SHAD_DARSHANA_BRIEF_v2_0.md §3 W2, E5/E7.2).'

/**
 * Builds a freshness attestation.
 *
 * Three honest outcomes, in order:
 *   1. `staleAfter` supplied and `now` is past it        → `stale: true`  + reason.
 *   2. `staleAfter` supplied and `now` is within it      → `stale: false` (a real detector
 *      ran against a real declared horizon, so `false` is EARNED).
 *   3. no `staleAfter` AND no attestation field at all   → `stale: null` + the
 *      not-evaluable reason. There is nothing to evaluate; saying `false` would assert
 *      freshness on no evidence (ND-2).
 *
 * Case 3 is the current state of every W0/W1 facade — deliberately surfaced rather than
 * papered over, because `ka_kshetra` (which produces the real field hash and sweep build
 * date) does not exist until W2.
 *
 * If ANY attestation field is populated but no horizon is declared, `stale` is `false`:
 * there is evidence of provenance and no horizon to have expired.
 */
export function buildKalaFreshness(params: {
  ephemerisVersion: string | null
  sweepBuildDate: string | null
  fieldHash: string | null
  staleAfter?: string | null
  now?: Date
}): KalaFreshness {
  const now = params.now ?? new Date()
  const hasAttestation =
    (params.ephemerisVersion != null && params.ephemerisVersion !== '') ||
    (params.sweepBuildDate != null && params.sweepBuildDate !== '') ||
    (params.fieldHash != null && params.fieldHash !== '')

  let stale: boolean | null
  let staleReason: string | null = null
  if (params.staleAfter) {
    const threshold = new Date(params.staleAfter)
    if (!Number.isNaN(threshold.getTime()) && now.getTime() > threshold.getTime()) {
      stale = true
      staleReason = `substrate horizon expired at ${params.staleAfter}`
    } else {
      stale = false
    }
  } else if (hasAttestation) {
    stale = false
  } else {
    stale = null
    staleReason = KALA_FRESHNESS_NOT_EVALUABLE_REASON
  }

  return {
    ephemeris_version: params.ephemerisVersion,
    sweep_build_date: params.sweepBuildDate,
    field_hash: params.fieldHash,
    stale,
    stale_reason: staleReason,
  }
}

// ── calibration_maturity (Elevation §7 — Living-LEL) ────────────────────────────────
// "`calibration_maturity: {n_events, prospective_resolutions, event_class_coverage,
// weights_version, skill_score}` — carried in every envelope's coverage block."

export interface CalibrationMaturity {
  n_events: number
  prospective_resolutions: number
  /** Fraction in [0, 1] of event classes with any calibration signal. `0` (not `null`)
   *  is the honest value for a chart with zero LEL events — see `noLelCalibrationMaturity`
   *  below, which implements the Elevation §7 LEL-absent scenario exactly. */
  event_class_coverage: number
  weights_version: string | null
  skill_score: number | null
}

/**
 * The Elevation §7 "LEL-absent" scenario, made concrete: "cohort priors only; weights =
 * classical structural priors... an honest calibration_maturity of zero." Every W0/W1
 * facade over a chart with no LEL entries should serve exactly this — never a null
 * `calibration_maturity` block (that would be an omission, not an honest zero).
 */
export function noLelCalibrationMaturity(): CalibrationMaturity {
  return {
    n_events: 0,
    prospective_resolutions: 0,
    event_class_coverage: 0,
    weights_version: null,
    skill_score: null,
  }
}

// ── the envelope itself ──────────────────────────────────────────────────────────────

export interface KalaEnvelope<TReading = ArgumentReading> {
  reading: TReading
  question_frame: QuestionFrame | null
  field_snapshot_id: string
  /** W2: machine-readable honesty state behind `field_snapshot_id` — 'served' carries a
   *  real 'kfs_…' id; the other two states carry their honest marker string as the id. */
  field_snapshot_state: FieldSnapshotState
  /** `null` when served; the honest reason otherwise (mirrors coverage's reason rule). */
  field_snapshot_reason: string | null
  tri_plane: TriPlanePointers
  coverage: KalaCoverageEntry[]
  freshness: KalaFreshness
  calibration_maturity: CalibrationMaturity
}

export interface MakeKalaEnvelopeParams<TReading = ArgumentReading> {
  reading: TReading
  questionFrame?: QuestionFrame | null
  /** The resolved field snapshot (real row, or an honest marker) — from
   *  `resolveFieldSnapshot`. Facades must not compose their own id (E5: ONE source). */
  fieldSnapshot: FieldSnapshotResolution
  triPlane: TriPlanePointers
  coverage: KalaCoverageEntry[]
  freshness: KalaFreshness
  calibrationMaturity: CalibrationMaturity
}

/** The single assembly point every one of the eight kala_* tool facades calls to produce
 *  its envelope — "ONE implementation, eight consumers" (brief §3 W0.3). Pure assembly:
 *  no computation, no defaults papered over silently (every field is a required param —
 *  a facade that has nothing for a slot must call one of the honest builders above, e.g.
 *  `noLelCalibrationMaturity()` or `noLeverPointer(reason)`, rather than omit it). */
export function makeKalaEnvelope<TReading = ArgumentReading>(
  params: MakeKalaEnvelopeParams<TReading>,
): KalaEnvelope<TReading> {
  return {
    reading: params.reading,
    question_frame: params.questionFrame ?? null,
    field_snapshot_id: params.fieldSnapshot.field_snapshot_id,
    field_snapshot_state: params.fieldSnapshot.field_snapshot_state,
    field_snapshot_reason: params.fieldSnapshot.field_snapshot_reason,
    tri_plane: params.triPlane,
    coverage: params.coverage,
    freshness: params.freshness,
    calibration_maturity: params.calibrationMaturity,
  }
}

// ── §N.6 hardFloor / density-contract discipline (consistent with response_budget.ts) ──
// CLAUDE.md §N.6: "the densest, most-actionable layer is the one a budget trim protects
// first." For a KalaEnvelope, that layer is `reading.evidence` — the cited drivers behind
// the thesis/verdict. Declaring it `hardFloor: true` (see response_budget.ts's
// TrimmableSection.hardFloor + its two-tier PASS ranking) means it is the LAST section any
// `applyResponseBudget`/`finalizeMcpBudget` pass ever zeroes; catalog-shaped, lower-density
// sections a facade may also declare (e.g. a raw signal list backing an insight) drain
// first. This helper does not itself trim anything — it hands a facade a ready-made,
// correctly-configured TrimmableSection<T> for its own envelope-shaped content, exactly
// the pattern response_budget.ts's existing callers already use.
export function kalaEvidenceTrimmableSection<T extends { reading: { evidence: ArgumentEvidence[] } }>(
  recover: { instrument: string; hint: string },
): TrimmableSection<T> {
  return {
    path: 'reading.evidence',
    label: 'argument evidence',
    minKeep: 1,
    hardFloor: true,
    getArray: (content) => content.reading.evidence,
    setArray: (content, kept) => {
      content.reading.evidence = kept as ArgumentEvidence[]
    },
    recover,
  }
}

/**
 * Type-shape mirror of `platform/src/lib/retrieval/registry/types.ts`'s
 * `CapabilityDescriptor.density_contract` (§N.6 part 4: "density signaling is data, not
 * narration"). Declared here (not imported — this file is `platform-mcp`, the registry
 * type lives in the sibling `platform` package) so the eight kala_* tool registrations can
 * declare their own density contract in the SAME shape a census/CI harness already knows
 * how to read, without a cross-package import. Kept field-for-field identical on purpose;
 * if the registry shape changes, update this mirror in the same PR.
 */
export interface KalaDensityContract {
  max_verdict_bytes?: number
  max_digest_bytes?: number
  paginated: boolean
  facets: string[]
  empty_reason: boolean
}
