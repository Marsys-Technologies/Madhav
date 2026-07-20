/**
 * envelope.ts — THE UNIFIED RETRIEVAL ENVELOPE (R5 W0b, design §10 bill-of-needs + §19
 * single-source mandate + brief §6.3 consumer format negotiation)
 * ======================================================================================
 * SINGLE-SOURCE DECLARATION of the envelope shape. Per design §18's premise verdict, the
 * platform (this process) and platform-mcp (a separate Node process) previously grew TWO
 * incompatible, hand-maintained envelope shapes — one hardcoded every field to null/[]
 * (`register_p1_synthesis.ts` / `register_p1_ganita.ts`), the other (`lib/mcp/epistemics.ts`)
 * served a different consumer family entirely. This file is the canonical spec for the
 * retrieval-instrument envelope (as distinct from the MCP_BRIEF §4.2 ask_madhav envelope,
 * which epistemics.ts continues to own).
 *
 * PROCESS-BOUNDARY NOTE (§19): platform-mcp is a standalone TS project with its own
 * tsconfig/build (NodeNext, no path mapping into this repo's `@/` aliases) — it cannot
 * `import` this file directly today. Its mirror lives at
 * `platform-mcp/src/lib/envelope.ts` and MUST be kept byte-structurally identical to the
 * types/logic below until the r5/w0b-codegen lane's contract generator supersedes the
 * hand-mirror with a real generated artifact. Any edit here requires the same edit there.
 *
 * CONSUMER FORMAT NEGOTIATION (brief §6.3, MARO precedent — see maro/normalizer.ts):
 *   response_format: 'legacy' | 'v3', default 'legacy'.
 *   - 'legacy' → byte-identical to the pre-W0b hollow envelope. No consumer breaks.
 *   - 'v3'     → additive: every legacy field still ships, PLUS chart_header / epistemic /
 *                timing / coverage, AND the previously-null verdict/ranking_basis/grounding/
 *                drill_pointers/judgment_flags are populated from data already computed in
 *                the same response (never fabricated — B.10).
 * The default flips to 'v3' only after the W4 answer-rubric battery passes (brief §6.3);
 * until then 'v3' is strictly opt-in.
 */

import {
  buildRegisterBlock,
  buildReadingContract,
  collectSignalReaderText,
  type RegisterEntry,
} from './register_block'

export type { RegisterEntry, RegisterTokenKind } from './register_block'

// ── Format negotiation ────────────────────────────────────────────────────────

export type EnvelopeFormat = 'legacy' | 'v3'

/** Parse a caller-supplied response_format value defensively. Unrecognized → 'legacy' (never break silently). */
export function resolveEnvelopeFormat(requested: unknown): EnvelopeFormat {
  return requested === 'v3' ? 'v3' : 'legacy'
}

// ── §10.2 — closed epistemic vocabulary ───────────────────────────────────────

export type EpistemicGrade =
  | 'ganita_fact'
  | 'verified_signal'
  | 'single_pass_signal'
  | 'classical_contested'
  | 'calibrated_posterior'
  | 'structural_prior'
  | 'floored_null'

export interface EpistemicSummary {
  grade: EpistemicGrade
  /** Fraction (0..1) of rows in THIS response with verification_pass_status='two_pass_verified'|'pass'; null if not computable. */
  verified_fraction: number | null
  note: string
}

/**
 * D2 — derive an EpistemicGrade from signals already available in the serving layer
 * (verification_pass_status ratio, calibration/floor state). Never invents a grade —
 * floored/contested callers must say so explicitly.
 */
export function deriveEpistemicGrade(input: {
  verifiedFraction: number | null
  isFloored?: boolean
  isContested?: boolean
  isCalibratedPosterior?: boolean
}): EpistemicGrade {
  if (input.isFloored) return 'floored_null'
  if (input.isContested) return 'classical_contested'
  if (input.isCalibratedPosterior) return 'calibrated_posterior'
  if (input.verifiedFraction === null) return 'structural_prior'
  if (input.verifiedFraction >= 0.95) return 'ganita_fact'
  if (input.verifiedFraction >= 0.5) return 'verified_signal'
  return 'single_pass_signal'
}

export function buildEpistemicSummary(input: {
  verifiedFraction: number | null
  isFloored?: boolean
  isContested?: boolean
  isCalibratedPosterior?: boolean
  note?: string
}): EpistemicSummary {
  const grade = deriveEpistemicGrade(input)
  return {
    grade,
    verified_fraction: input.verifiedFraction,
    note: input.note ?? `Grade computed live from this response's own rows (${grade}).`,
  }
}

// ── §10.1 — frame safety ──────────────────────────────────────────────────────

export interface ChartHeader {
  chart_id_short: string
  name: string | null
  lagna_sign: string | null
  lagna_deg: number | null
  moon_sign: string | null
  sun_sign: string | null
  ayanamsha: string
  current_maha_antar: string | null
}

// ── §10.4 / §12 D7 — timing (cheap; full server-timing telemetry is E-8, a separate lane) ──

/**
 * CACHE-SAFETY NOTE (W3-L8, W-28 envelope half): `computed_at` is CALL-TIME METADATA —
 * it is `new Date().toISOString()` taken at the moment `buildRetrievalEnvelope` runs, so
 * it legitimately differs between two calls even when every other field is byte-identical
 * (same tool, same args, same build_id, same ledger_version). A response cache keyed on
 * (uri, chart_id, build_id, ledger_version, args, projection, format) per W-28 MUST treat
 * `computed_at` as excluded from the cached/compared "stable content" — it is metadata
 * ABOUT the call, not content the call produced. `as_of_date` is content: it defaults to
 * `computed_at`'s date, but a caller that passes it explicitly (the honest, cache-safe
 * usage) gets a value that is stable for the whole day regardless of call time.
 */
export interface TimingBlock {
  as_of_date: string
  /** CALL-TIME METADATA — excluded from the cache-safe "stable content" comparison. See
   *  the cache-safety note above. */
  computed_at: string
  /**
   * W3 Lane L7 (plan §8 R-2 item 6 / strategy S-6): honest anchor flag. `true` only
   * when the response's time-sensitive content is genuinely anchored to a resolved
   * dasha / activation / transit window for `as_of_date`; `false` (never silently
   * omitted) when a time-sensitive tool could not anchor its reading — the machine-
   * readable form of `judgment_query`'s existing `timing_anchored` judgment_flag
   * (register_d9_judgment.ts Step 9), lifted out of the ad-hoc flags array so every
   * signal-bearing response can state it uniformly. Undefined on responses that carry
   * no time-sensitive claim at all (a flat natal fact has nothing to anchor).
   */
  timing_anchored?: boolean
  /**
   * W3 Lane L7: the calendar window the reading APPLIES TO (not when it was computed —
   * that is `computed_at`). Formalizes the informal "current dasha window" /
   * "activation_start..activation_end" span that time-sensitive tools like
   * `judgment_query` and the kala activation hooks return inside their payload today.
   * `null` bounds are honest ("open-ended" / "unknown"), never fabricated. `null` for
   * the whole field when the response is not window-scoped.
   */
  applies_window?: { start: string | null; end: string | null } | null
  /**
   * W3 Lane L7: staleness bound — the date after which this response's time-sensitive
   * content should be recomputed (typically the end of the current active dasha/transit
   * window, or `as_of_date` + the tool's freshness horizon). Lets a caching/consuming
   * layer know a served "what is active now" reading has an expiry rather than treating
   * it as timeless. `null` when the content does not go stale (pure natal facts).
   */
  valid_until?: string | null
}

// ── §10.5 — coverage receipts ──────────────────────────────────────────────────

export interface CoverageStamp {
  family: string
  served: number
  total: number | null
}

/**
 * D5 coverage-receipt helper (design §10.5 / §12 D5).
 *
 * `family` names the complete relevant set this response is a bounded slice of
 * (e.g. `'msr_signals[domain=career]'`, `'yoga_dosha_rows'`) — a stable, filter-
 * qualified label so two responses with different filters are never mistaken
 * for describing the same family. `served` is the row/entity count actually
 * returned in THIS response. `total` is the true family size — a COUNT (or
 * equivalent aggregate) the caller already computed against the SAME filter
 * conditions as the main query, never a re-guess or a copy of `served`.
 *
 * `total: null` is the honest value when the family size genuinely is not
 * computable for this response (e.g. the underlying capability has no cheap
 * count path yet) — B.10 forbids fabricating a number to fill the field.
 */
export function buildCoverageStamp(family: string, served: number, total: number | null): CoverageStamp {
  return { family, served, total }
}

// ── shared envelope substructures ─────────────────────────────────────────────

export interface GroundingBlock {
  fact_ids: string[]
  citations: string[]
  grounding_score: number | null
}

export interface PaginationBlock {
  offset: number
  limit: number
  total: number | null
  next_cursor: string | null
  /**
   * WP-1.5 (LCA-18 receipt honesty) — TRUE iff this response is a bounded slice and MORE
   * rows exist beyond it. The single honest "was I trimmed?" bit every consumer reads
   * instead of guessing from a null cursor. Computed, never guessed:
   *   - total != null  → `offset + served < total`
   *   - total == null  → `served >= limit` (a full page is presumptively not the last page)
   * When `more_available` is true, `next_cursor` MUST be a working cursor (never null).
   * The audit's canonical lie — `truncated:false` at 200/7014 with a null cursor, or
   * orientation serving 10 of ~13.3k with `total:null` and no `more_available` — is
   * structurally unrepresentable through the honest builder below.
   */
  more_available: boolean
}

/**
 * WP-1.5 — the program-wide ENVELOPE-HONESTY contract helper. Every serving tool that
 * returns a bounded slice builds its PaginationBlock through this function so the three
 * receipt fields can never disagree with the served rows:
 *   - `total`         : the true family size the caller COUNTed under the SAME filters
 *                       (or null when genuinely uncomputable — B.10 forbids fabrication).
 *   - `more_available`: computed from (served, limit, offset, total) — never passed in.
 *   - `next_cursor`   : a WORKING opaque cursor (base64 `{offset[,fp]}`) present exactly when
 *                       `more_available` is true; null otherwise. Decode with decodeCursor
 *                       (offset-only, unchanged) or decodeCursorFull (offset + fingerprint,
 *                       W3 — see checkCursorFingerprint below).
 *
 * `served` is the row count actually in THIS response (rows.length) — not `limit`.
 *
 * `filterFingerprint` (W3 — RETRIEVAL_PLANE_ELEVATION_PLAN §R-2 item 4, "cursors embed a
 * filter/sort fingerprint hash") is OPTIONAL and ADDITIVE: omit it and the emitted cursor is
 * byte-identical to the pre-W3 offset-only shape (no behavior change for existing callers).
 * A caller that varies its own filters/sort between calls should pass
 * `computeFilterFingerprint({...its own facet params})` here so a cursor minted under one
 * filter set is detectably stale when replayed under a different one.
 */
export function buildHonestPagination(params: {
  served: number
  limit: number
  offset?: number
  total: number | null
  filterFingerprint?: string
}): PaginationBlock {
  const offset = params.offset ?? 0
  const served = Math.max(0, params.served)
  const more_available =
    params.total != null
      ? offset + served < params.total
      : params.limit > 0 && served >= params.limit
  return {
    offset,
    limit: params.limit,
    total: params.total,
    next_cursor: more_available ? encodeCursor(offset + served, params.filterFingerprint) : null,
    more_available,
  }
}

/**
 * Encode a next-page offset into an opaque, round-trippable cursor.
 *
 * `filterFingerprint` (W3, optional) is embedded alongside the offset so a later
 * `checkCursorFingerprint` call can detect a stale replay under different filters/sort.
 * Omitting it produces exactly the pre-W3 wire shape (`base64({"offset":N})`) — additive,
 * never a breaking change for a caller that decodes with the original `decodeCursor`.
 */
export function encodeCursor(nextOffset: number, filterFingerprint?: string): string {
  const payload: { offset: number; fp?: string } = { offset: nextOffset }
  if (filterFingerprint) payload.fp = filterFingerprint
  return Buffer.from(JSON.stringify(payload), 'utf8').toString('base64')
}

/**
 * Decode a cursor produced by encodeCursor back to its offset; null if malformed.
 * Ignores any embedded fingerprint — unchanged signature/behavior from pre-W3 (existing
 * consumers of this function are unaffected by the W3 cursor-fingerprint addition). A
 * caller that needs the fingerprint (to detect a stale-filter replay) uses
 * `decodeCursorFull` / `checkCursorFingerprint` instead.
 */
export function decodeCursor(cursor: string | null | undefined): number | null {
  if (!cursor) return null
  try {
    const parsed = JSON.parse(Buffer.from(cursor, 'base64').toString('utf8')) as { offset?: unknown }
    return typeof parsed.offset === 'number' && Number.isFinite(parsed.offset) ? parsed.offset : null
  } catch {
    return null
  }
}

// ── W3 "One Envelope" — cursor filter/sort fingerprints ───────────────────────
// RETRIEVAL_IMPLEMENTATION_MASTER_BRIEF §E "W3" + RETRIEVAL_PLANE_ELEVATION_PLAN §R-2 item 4:
// "cursors embed a filter/sort fingerprint hash; mismatched replay → explicit
// `cursor_filter_mismatch` flag, not wrong pages." §1.2's finding: pre-W3, a cursor encoded
// only `{offset}` — replaying it under a different filter/sort silently paginated the wrong
// family (e.g. page-2 of a `domain=career` query, replayed with `domain=wealth`, returned
// rows 10-20 of the WEALTH family mislabeled as a continuation).
//
// IMPORTANT: this file is codegen'd verbatim into platform-mcp (see the file's header note +
// `generate_envelope.ts`'s AST guard, which HALTS on any `import`/`import =` declaration in
// this source). The fingerprint hash below is therefore a small, dependency-free, pure-TS
// function — NOT `crypto.createHash` — even though Node's `crypto` module is available
// elsewhere in this codebase (`platform/src/lib/retrieval/cache.ts` uses sha256 for its own,
// unrelated cache-key hash). This is not a security boundary — it only needs to be
// deterministic and collision-resistant enough to catch a same-process replay under
// different filters, not to resist an adversary.

/**
 * cyrb53 — Bryc's public-domain 53-bit non-cryptographic hash. Deterministic, good avalanche
 * behavior, zero dependencies (required — see note above). Returns a fixed-width hex string.
 */
function cyrb53Hex(str: string, seed = 0): string {
  let h1 = 0xdeadbeef ^ seed
  let h2 = 0x41c6ce57 ^ seed
  for (let i = 0; i < str.length; i++) {
    const ch = str.charCodeAt(i)
    h1 = Math.imul(h1 ^ ch, 2654435761)
    h2 = Math.imul(h2 ^ ch, 1597334677)
  }
  h1 = Math.imul(h1 ^ (h1 >>> 16), 2246822507) ^ Math.imul(h2 ^ (h2 >>> 13), 3266489909)
  h2 = Math.imul(h2 ^ (h2 >>> 16), 2246822507) ^ Math.imul(h1 ^ (h1 >>> 13), 3266489909)
  const combined = 4294967296 * (2097151 & h2) + (h1 >>> 0)
  return combined.toString(16).padStart(14, '0')
}

/**
 * Stable (key-sorted, recursive) JSON serialization — the SAME normalization discipline
 * `cache.ts`'s `_stableStringify` uses for its cache keys, reimplemented here so this file
 * stays import-free (see note above). Two filter objects that differ only in key insertion
 * order, or that carry `undefined` values, serialize IDENTICALLY, so their fingerprints
 * always agree.
 */
function stableStringifyForFingerprint(value: unknown): string {
  if (value === undefined) return 'null'
  if (value === null || typeof value !== 'object') return JSON.stringify(value) ?? 'null'
  if (Array.isArray(value)) return `[${value.map(stableStringifyForFingerprint).join(',')}]`
  const obj = value as Record<string, unknown>
  const keys = Object.keys(obj)
    .filter(k => obj[k] !== undefined)
    .sort()
  return `{${keys.map(k => `${JSON.stringify(k)}:${stableStringifyForFingerprint(obj[k])}`).join(',')}}`
}

/**
 * Compute a deterministic fingerprint of a paginated call's filter+sort parameters.
 * Key order and `undefined` values never affect the result (stable-stringified first).
 * A capability with genuinely no filters should still call this with `{}` (or omit the
 * fingerprint entirely and rely on the offset-only cursor shape) — either is honest;
 * what must never happen is silently treating a filter-bearing capability as filterless.
 */
export function computeFilterFingerprint(filters: Record<string, unknown>): string {
  return cyrb53Hex(stableStringifyForFingerprint(filters))
}

/** A cursor's fully-decoded payload: offset plus whichever fingerprint (if any) it carries. */
export interface DecodedCursor {
  offset: number
  /** null when the cursor pre-dates W3, or was minted by a filterless capability. */
  filterFingerprint: string | null
}

/** Decode a cursor to its offset AND embedded fingerprint (if any); null if malformed. */
export function decodeCursorFull(cursor: string | null | undefined): DecodedCursor | null {
  if (!cursor) return null
  try {
    const parsed = JSON.parse(Buffer.from(cursor, 'base64').toString('utf8')) as {
      offset?: unknown
      fp?: unknown
    }
    if (typeof parsed.offset !== 'number' || !Number.isFinite(parsed.offset)) return null
    return {
      offset: parsed.offset,
      filterFingerprint: typeof parsed.fp === 'string' ? parsed.fp : null,
    }
  } catch {
    return null
  }
}

/** The reserved judgment_flags code (W3-L2's closed enum) for a detected cursor replay
 *  under different filters/sort — use this literal, never a re-derived string. */
export const CURSOR_FILTER_MISMATCH_FLAG = 'cursor_filter_mismatch' as const

/** Result of checking a replayed cursor against the CURRENT call's filter fingerprint. */
export interface CursorFingerprintCheck {
  /**
   * The offset a handler should actually use to build this page.
   *   - no cursor supplied            → 0
   *   - cursor matches / no fp to check → the cursor's own offset (real continuation)
   *   - MISMATCH                       → 0 (never the stale offset — restarting the current
   *                                       filter's family at page 1 is honest; silently
   *                                       returning "page 2" of a DIFFERENT family is the
   *                                       exact bug this mechanism exists to prevent)
   */
  offset: number
  /** True iff a cursor was supplied whose embedded fingerprint disagrees with the current
   *  call's filters/sort. The caller MUST add CURSOR_FILTER_MISMATCH_FLAG to its
   *  judgment_flags (or equivalent) when this is true — never silently serve `offset`. */
  mismatch: boolean
  /** True iff no fingerprint was available to check (no cursor at all, a pre-W3 cursor, or
   *  a filterless capability's cursor) — an honest "not applicable", distinct from a
   *  confirmed match and from a confirmed mismatch. */
  noFingerprint: boolean
}

/**
 * The W3 replay-safety check. Call once per handler invocation with the caller-supplied
 * `cursor` (may be undefined/null on a first call) and the CURRENT call's fingerprint
 * (`computeFilterFingerprint` over this exact call's filter+sort args). Use the returned
 * `offset` to build the page; when `mismatch` is true, surface `CURSOR_FILTER_MISMATCH_FLAG`
 * instead of trusting the decoded offset.
 */
export function checkCursorFingerprint(
  cursor: string | null | undefined,
  currentFingerprint: string,
): CursorFingerprintCheck {
  const decoded = decodeCursorFull(cursor)
  if (decoded === null) return { offset: 0, mismatch: false, noFingerprint: true }
  if (decoded.filterFingerprint === null) return { offset: decoded.offset, mismatch: false, noFingerprint: true }
  if (decoded.filterFingerprint !== currentFingerprint) {
    return { offset: 0, mismatch: true, noFingerprint: false }
  }
  return { offset: decoded.offset, mismatch: false, noFingerprint: false }
}

/**
 * The closed astrologically-typed drill-pointer vocabulary (design §28.4 — "the
 * closed pointer vocabulary becomes shastra moves"). Each value names a classical
 * NEXT STEP an acharya would actually take, not a generic "more data" pointer:
 *   confirm_in_varga      — confirm the promise in the operative divisional chart
 *   check_from_moon       — re-judge the same matter from the chandra frame (Sudarshana)
 *   check_bhanga          — check for a cancellation/near-miss on a bearing yoga/dosha
 *   opposing_yoga         — a yoga/dosha with the OPPOSITE valence bears on the same matter
 *   karaka_condition      — examine the significator graha's own condition directly
 *   dasha_of_promise      — locate which dasha period carries/activates the promise
 *   transit_gate          — check current/upcoming transits gating an already-activated promise
 *   dispositor_chain      — follow the lord-of-the-lord (dispositor) indirection one level deeper
 *   tail_dissent          — the mandatory dissent/tail-check step of the investigation protocol
 *   other                 — a real next step outside the classical vocabulary above (rare; kept
 *                           so this remains additive rather than a hard enum that could reject a
 *                           genuinely useful pointer with no classical-move label)
 * Field is OPTIONAL and ADDITIVE — every existing `{instrument, hint}` pointer remains valid
 * without a `pointer_type`; callers written against the untyped shape are unaffected.
 */
export type DrillPointerType =
  | 'confirm_in_varga'
  | 'check_from_moon'
  | 'check_bhanga'
  | 'opposing_yoga'
  | 'karaka_condition'
  | 'dasha_of_promise'
  | 'transit_gate'
  | 'dispositor_chain'
  | 'tail_dissent'
  | 'other'

/**
 * PACT chain stage marker (design §26 + §28.3 — "the same PACT chain the L4 redesign
 * already encodes at the data layer"). The four classically-falsifiable stages, in
 * chain order: PROMISE (judgment_query's checklist verdict) → CONFIRMATION (operative-
 * varga check) → ACTIVATION (which promise-carrier dasha, when) → TRIGGER (transit gate
 * in-window). A drill_pointer carrying `pact_stage` names WHICH stage firing this
 * pointer would advance to — the mechanism the brief calls "typed pointers chain
 * through all four stages". Optional/additive, same discipline as `pointer_type`.
 */
export type PactStage = 'promise' | 'confirmation' | 'activation' | 'trigger'

export interface DrillPointer {
  instrument: string
  hint: string
  /** Astrologically typed classification of this pointer's classical move (design §28.4).
   *  Optional/additive — see DrillPointerType doc comment. */
  pointer_type?: DrillPointerType
  /** Which PACT-chain stage firing this pointer advances to (design §28.3 + §30 chain-honesty
   *  acceptance). Optional/additive — absent on pointers outside a PACT investigation. */
  pact_stage?: PactStage
}

// ── §10.3 / W3-L2 — closed judgment-flag vocabulary (RETRIEVAL_IMPLEMENTATION_MASTER_BRIEF
// §E W3 item 2 "flags closed enum + d8/hollow-emitter migration", RETRIEVAL_PLANE_ELEVATION_PLAN
// §"R-2 One Envelope" item 2, GT-46/GT-53) ─────────────────────────────────────
//
// PROBLEM THIS CLOSES: `judgment_flags` was a fully open `string[]` — any emitter could push
// any free-text string, so a consumer had no closed vocabulary to branch on and no way to
// distinguish a structured, machine-checkable disclosure from ad-hoc prose. This section is the
// SINGLE SOURCE for the closed code vocabulary (`JUDGMENT_FLAG_CODES`/`JudgmentFlagCode`) plus
// the structured entry shape every emitter in the codebase now targets.
//
// COMPAT (plan §"ship a compat shim during transition"): `JudgmentFlagEntry` additionally
// accepts a bare `string` so a consumer reading the field defensively — or an emitter in a
// parallel lane not yet migrated (e.g. session-pin drift's own `judgment_flags: string[]`,
// which is a distinct subsystem outside this file's envelope-building path) — never hard-breaks.
// New emitters should always push the structured `{code, detail?, severity?}` shape via the
// `judgmentFlag()` builder below; `judgmentFlagsInclude`/`judgmentFlagText` let a consumer check/
// render either shape without caring which one a given entry happens to be.
export const JUDGMENT_FLAG_CODES = [
  // ── generic row/page honesty (shared across many list-shaped tools) ──
  'zero_rows_returned',
  'zero_entity_profiles',
  'response_size_truncated',
  'partial_page_more_available',
  'catalog_only_rows_present',
  'system_facet_unrecognized',
  'time_sensitive_low_confidence',
  // ── L1 get_dasha_lord_capability / get_dashas ──
  'unmapped_lord_graha',
  'house_class_unresolved',
  'ratification_unavailable',
  // ── D9 judgment_query checklist legs ──
  'karaka_unresolved',
  'from_moon_resolution_failed',
  'varga_confirmation_failed',
  'yoga_firings_fetch_failed',
  'bearing_yogas_empty',
  'bearing_yogas_no_domain_match',
  'yoga_signal_corroboration_fetch_failed',
  'bearing_yogas_corroboration_caveat',
  'notably_absent_not_checked',
  'kala_activations_trimmed',
  'kala_activations_single_cycle',
  'timing_anchored_false',
  'timing_anchored_forced_false',
  'timing_hook_failed',
  'afflictions_fetch_failed',
  'afflictions_empty',
  'afflictions_present',
  // ── D8 assess_domain (folds the former {claim, requires_acharya_validation} object shape) ──
  'domain_inference_requires_acharya_validation',
  // ── D10 pact_query chain-honesty halts ──
  'confirmation_graha_unrecognized',
  'pact_halted_at_promise',
  'pact_halted_at_confirmation',
  'pact_halted_at_activation',
  'pact_trigger_infra_incomplete',
  // ── graha_portrait / get_chart_orientation / get_signals (registry_bridge.ts) ──
  'partial_portrait_section_errors',
  'no_parivartana_or_catalog_matches_for_graha',
  'no_mahadasha_periods_for_graha',
  // ── response_budget.ts finalizeMcpBudget hard-cap ──
  'budget_exceeded_after_trim',
  // ── session-pin drift (distinct subsystem, session_pin.ts) — included so a value it
  // already emits (as a plain string, unconverted this wave) is always a VALID code, not
  // an orphaned literal outside the closed vocabulary. ──
  'chart_rebuilt_mid_session_pin_refreshed',
  // ── coordination placeholders for parallel W3 lanes (do not rename — see brief) ──
  'chart_header_unresolved', // W3-L1 (chart_header fail-loud)
  'cursor_filter_mismatch', // W3-L4 (cursor-fingerprint)
  // ── hollow-emitter honesty (register_p1_synthesis.ts / register_p1_reference.ts) ──
  'hollow_envelope_no_data_rows',
  'hollow_envelope_shape_not_evaluated',
  // ── transitional catch-all for a bare string this migration cannot classify further ──
  'legacy_unstructured_flag',
] as const

export type JudgmentFlagCode = typeof JUDGMENT_FLAG_CODES[number]

/** Runtime membership check against the closed vocabulary above — the "registry-checked" half
 *  of "closed, registry-checked flag-code enum" (tests assert every real emitter's code is a
 *  member of this array, not just that the TS union compiles). */
export function isJudgmentFlagCode(value: unknown): value is JudgmentFlagCode {
  return typeof value === 'string' && (JUDGMENT_FLAG_CODES as readonly string[]).includes(value)
}

export interface JudgmentFlag {
  code: JudgmentFlagCode
  /** Free-text elaboration (the dynamic part of what used to be baked into a single
   *  interpolated string — e.g. the caught error, the row count, the graha name). Optional:
   *  a self-explanatory code (e.g. `zero_rows_returned`) needs none. */
  detail?: string
  severity?: 'info' | 'warning' | 'error'
}

/** Transitional compat shape (W3-L2 migration): every field TYPED as carrying
 *  `JudgmentFlagEntry[]` tolerates a bare legacy string alongside the new structured shape —
 *  see the module-doc note above for why this is deliberate, not a loose escape hatch. */
export type JudgmentFlagEntry = JudgmentFlag | string

/** The one constructor every migrated emitter in the codebase uses to push a flag — avoids
 *  each call site hand-rolling the object literal (and mistyping a code past the closed
 *  vocabulary, since TS rejects an out-of-union `code` argument here at the call site). */
export function judgmentFlag(code: JudgmentFlagCode, detail?: string, severity?: JudgmentFlag['severity']): JudgmentFlag {
  return { code, ...(detail !== undefined ? { detail } : {}), ...(severity !== undefined ? { severity } : {}) }
}

/** Defensive, either-shape accessor — true iff `flags` carries `code`, whether the matching
 *  entry is the new `{code,...}` shape or a not-yet-migrated bare string equal to (or prefixed
 *  `code: `, the pre-migration convention several emitters used) that code. Never throws on a
 *  mixed array. */
export function judgmentFlagsInclude(flags: JudgmentFlagEntry[] | null | undefined, code: JudgmentFlagCode): boolean {
  if (!flags) return false
  return flags.some(f => (typeof f === 'string' ? f === code || f.startsWith(`${code}:`) : f.code === code))
}

/** Render a flag entry (either shape) as a single human-readable string — never throws on
 *  either shape. For a consumer that just wants prose (e.g. a legacy log line, or a caller
 *  that has not yet adopted the structured shape). */
export function judgmentFlagText(flag: JudgmentFlagEntry): string {
  if (typeof flag === 'string') return flag
  return flag.detail ? `${flag.code}: ${flag.detail}` : flag.code
}

// ── R5.1 C1 — MCP-consume response-budget trim report ─────────────────────────

/**
 * One trimmed section of a response (R5.1 C1 "budget facet + trim discipline"). Names
 * WHAT was cut (a dot-path into `content`), how much, and the exact instrument/params a
 * caller uses to recover the full detail — the trim never destroys data server-side, it
 * only declines to default-serve it over the size-constrained MCP channel (B.10-adjacent
 * discipline: never silently drop information without saying so and naming the way back).
 */
export interface TrimReportEntry {
  /** Dot-path into the response `content` where a section was shortened, e.g.
   *  "checklist.bearing_yogas" or "dignity.all_varga_rows". */
  path: string
  /** How many entries the untrimmed section actually had. */
  original_count: number
  /** How many entries survived in this response. */
  kept_count: number
  /** Human-readable reason (always names the byte-budget rule, never silent). */
  reason: string
  /** The drill_pointer-shaped recipe for recovering the trimmed detail. */
  recover_via: { instrument: string; hint: string }
}

// ── W3 Lane L7 — standardized prediction shape (plan §8 R-2 item 7) ──────────────

/**
 * A single, self-describing prediction/forecast claim carried by a response.
 *
 * Plan §8 R-2 item 7 mandates a STANDARDIZED prediction shape —
 * "claim + window + mechanism + confidence + calibration lineage — ledger-ready on
 * both channels." This interface is that shape, designed to be **ledger-ready**: it
 * maps field-for-field onto the L5 Mīmāṃsā prospective prediction ledger
 * (`mimamsa_predictions`, migration `brahma_mimamsa_prediction_ledger.sql`, tool
 * `log_prediction`) so a served prediction can be logged verbatim and later scored by
 * `record_outcome()` — the project's existing falsifiable-prediction pattern. We ALIGN
 * with that schema rather than invent an incompatible one:
 *
 *   PredictionClaim field   →  mimamsa_predictions column
 *   ─────────────────────────────────────────────────────
 *   claim                   →  prediction_text
 *   domain                  →  domain
 *   horizon_date            →  horizon_date        (DATE; the "by when" of the claim)
 *   confidence              →  confidence          (STRICT open interval (0,1) — the
 *                                                    ledger CHECK rejects 0.0 and 1.0)
 *   falsifier               →  falsifier           (NON-NULL: "If [event] does not
 *                                                    occur by [date], this is false")
 *   calibration_lineage.source_citation → source_citation (NON-NULL, B.3 mandate)
 *
 * `mechanism` (the astrological driver — which yoga/dasha/karaka carries the promise)
 * and `applies_window` (the active window the claim rides, distinct from the single
 * `horizon_date` deadline) are additive over the ledger columns: they are the plan's
 * "mechanism" + "window" requirements, carried on the wire for the reading LLM even
 * though the ledger stores only the deadline date. NO-LEAKAGE discipline is inherited
 * from the ledger contract: a PredictionClaim is logged BEFORE any outcome; it never
 * carries an observed outcome (that is `record_outcome()`'s sole write path).
 */
export interface PredictionClaim {
  /** The prediction, stated as a falsifiable claim. → mimamsa_predictions.prediction_text */
  claim: string
  /** Life domain (career/wealth/health/marriage/…). → mimamsa_predictions.domain */
  domain: string
  /** ISO 8601 date (YYYY-MM-DD) by which the claim resolves. → mimamsa_predictions.horizon_date */
  horizon_date: string
  /** The active window the claim rides (dasha/transit span), distinct from the horizon
   *  deadline. `null` bounds are honest; whole field `null` if not window-scoped. */
  applies_window?: { start: string | null; end: string | null } | null
  /** The astrological mechanism driving the claim (which yoga/dasha-lord/karaka carries
   *  the promise) — plan §8 R-2 "mechanism". Grounds the claim; not a ledger column. */
  mechanism: string
  /** Calibrated probability in the STRICT open interval (0,1). → mimamsa_predictions.confidence */
  confidence: number
  /** The falsification condition. → mimamsa_predictions.falsifier (NON-NULL). */
  falsifier: string
  /** Calibration lineage — how this prediction traces back for later scoring. */
  calibration_lineage: {
    /** Provenance citation, B.3 mandate. → mimamsa_predictions.source_citation (NON-NULL). */
    source_citation: string
    /** Prediction technique for the (technique, ayanamsha) calibration slice
     *  (mimamsa_calibration): vimshottari | yogini | kp | jaimini_chara | … */
    technique?: string
    /** Ayanamsha the reading used (lahiri | true_chitra | kp | raman | …). */
    ayanamsha_id?: string
  }
}

/**
 * Validate that a PredictionClaim is LEDGER-READY — i.e. it would pass the
 * `mimamsa_predictions` insert CHECK constraints (migration
 * `brahma_mimamsa_prediction_ledger.sql`). Pure; returns the list of problems
 * (empty array = ready). Kept in lock-step with the SQL contract so a response can
 * self-check before claiming its prediction is loggable.
 */
export function validatePredictionClaim(p: PredictionClaim): string[] {
  const problems: string[] = []
  const isIsoDate = (s: string): boolean => /^\d{4}-\d{2}-\d{2}$/.test(s)

  if (!p.claim || p.claim.trim() === '') problems.push('claim is empty (mimamsa_predictions.prediction_text is NOT NULL)')
  if (!p.domain || p.domain.trim() === '') problems.push('domain is empty (mimamsa_predictions.domain is NOT NULL)')
  if (!isIsoDate(p.horizon_date)) problems.push('horizon_date is not ISO 8601 YYYY-MM-DD (mimamsa_predictions.horizon_date is a DATE)')
  // Strict open interval — the ledger CHECK is (confidence > 0.0 AND confidence < 1.0).
  if (!(typeof p.confidence === 'number' && p.confidence > 0 && p.confidence < 1)) {
    problems.push('confidence must be in the STRICT open interval (0,1) — 0.0 and 1.0 are not valid probabilities (ledger CHECK)')
  }
  if (!p.falsifier || p.falsifier.trim() === '') problems.push('falsifier is empty (mimamsa_predictions.falsifier is NOT NULL — Learning Layer rule #4)')
  if (!p.mechanism || p.mechanism.trim() === '') problems.push('mechanism is empty (plan §8 R-2 requires a stated mechanism)')
  if (!p.calibration_lineage || !p.calibration_lineage.source_citation || p.calibration_lineage.source_citation.trim() === '') {
    problems.push('calibration_lineage.source_citation is empty (mimamsa_predictions.source_citation is NOT NULL — B.3)')
  }
  // Mirror the ledger's horizon_after_log CHECK against the compute date.
  if (isIsoDate(p.horizon_date) && p.applies_window?.start && isIsoDate(p.applies_window.start)) {
    if (p.horizon_date < p.applies_window.start) {
      problems.push('horizon_date precedes applies_window.start (a claim cannot resolve before its window opens)')
    }
  }
  return problems
}

/** Convenience: is this claim ledger-ready (would pass the mimamsa_predictions insert)? */
export function isPredictionClaimLedgerReady(p: PredictionClaim): boolean {
  return validatePredictionClaim(p).length === 0
}

/** The row shape `log_prediction` inserts into `mimamsa_predictions`. */
export interface PredictionLedgerRow {
  chart_id: string
  domain: string
  prediction_text: string
  horizon_date: string
  confidence: number
  falsifier: string
  source_citation: string
}

/**
 * Project a served PredictionClaim onto the exact column set `log_prediction` writes
 * to `mimamsa_predictions`. The additive `mechanism`/`applies_window` fields are
 * intentionally dropped here (they are wire-only enrichment, not ledger columns) — the
 * mapping is deliberately lossy in exactly the direction the ledger schema is narrower.
 */
export function predictionClaimToLedgerRow(p: PredictionClaim, chart_id: string): PredictionLedgerRow {
  return {
    chart_id,
    domain: p.domain,
    prediction_text: p.claim,
    horizon_date: p.horizon_date,
    confidence: p.confidence,
    falsifier: p.falsifier,
    source_citation: p.calibration_lineage.source_citation,
  }
}

// ── envelope shapes ────────────────────────────────────────────────────────────

export interface LegacyEnvelope {
  envelope_version: 'v1'
  tool: string
  verdict: unknown | null
  ranking_basis: Record<string, unknown> | null
  grounding: GroundingBlock
  pagination: PaginationBlock
  drill_pointers: DrillPointer[]
  judgment_flags: JudgmentFlagEntry[]
  insight_type: string | null
  query_class: string
  content: unknown
  /** R5.1 C1 — additive, null unless this response's `content` was shortened to fit a
   *  channel size ceiling (e.g. the MCP-channel budget facet). Never populated by fabrication
   *  — only ever reports a trim that actually happened to THIS response's own content. */
  trim_report: TrimReportEntry[] | null
}

export interface V3Envelope extends Omit<LegacyEnvelope, 'envelope_version'> {
  /** Honest per-format value (W3-L1, GT-47/W-9) — 'v3' here, never the legacy 'v1' literal.
   *  Distinct from `response_format` (which already carried the correct value): this field
   *  had been hardcoded to 'v1' on every response, v3 included, since the W0b envelope
   *  landed — a caller reading `envelope_version` alone (rather than `response_format`)
   *  was silently lied to about which shape it actually received. */
  envelope_version: 'v3'
  response_format: 'v3'
  chart_header: ChartHeader | null
  epistemic: EpistemicSummary
  timing: TimingBlock
  coverage: CoverageStamp | null
  /** W3 Lane L7 (plan §8 R-2 item 7) — the standardized prediction claim this response
   *  carries, or `null` when the response makes no forecast. Additive; never fabricated
   *  (a response only sets this when it genuinely computed a falsifiable prediction). */
  prediction?: PredictionClaim | null
  /** Design §31.5 BUILD PROVENANCE AT SERVE TIME — chart-level build identifier for
   *  this response's data. Undefined/null when not supplied by the caller (honest
   *  null, never fabricated — B.10); callers that track chart builds (e.g. session-pin
   *  serving, design §10.6/§31.3) populate this from the chart's latest complete
   *  `builds` row. Consistency invariant (E-4, extended): one response = one build_id. */
  build_id?: string | null
  /** W3-L8 (RETRIEVAL_PLANE_ELEVATION_PLAN §9.6-3/4 + §9.7, W-26/W-28): the serving-catalog
   *  staleness signal, orthogonal to `build_id` — see `session_pin.ts`'s `SessionPinValues.
   *  ledger_version` doc and `concept_ledger/ledger.ts#getLedgerVersion` for the full
   *  derivation. `build_id` says "this chart's data hasn't moved"; `ledger_version` says
   *  "the concept ledger (which capabilities are SERVED/RETIRED/etc) hasn't moved" — the
   *  second, independent axis the W-28 response-cache key needs
   *  (uri, chart_id, build_id, ledger_version, args, projection, format). Undefined/null
   *  when not supplied by the caller (honest null, never fabricated — B.10); this is a
   *  STABLE, cacheable field — it does not change between calls unless the underlying
   *  ledger state actually changes, so it is safe to include verbatim in a cache key. */
  ledger_version?: string | null

  // ── W3-L3 "One Envelope" register block (plan §R-2 item 3; A-18) ─────────────
  /**
   * The REGISTER block — a machine-readable map from every internal token that ACTUALLY
   * appears in this response (MSR signal-class codes, SIG.MSR.NNN ids, marsys:// drill
   * URIs, judgment-flag codes, epistemic-grade tokens, PACT stages, pointer types) to a
   * short plain-language label + its kind. Rides in the envelope so a careless-reading
   * foreign LLM gets the label adjacent to the token (handoff §7.2). Built by
   * buildRegisterBlock; response-scoped (never the whole glossary). Additive/optional. */
  register?: RegisterEntry[]
  /**
   * The READING-CONTRACT header — ONE generated paragraph telling the consuming model how
   * to read THIS response's grades/coverage/flags/register. Generated from the response's
   * actual content shape (buildReadingContract), so a confirmed-grounded response and a
   * sparse/floored one differ visibly (§N.6: density signaling is data, not narration). */
  reading_contract?: string | null
  /**
   * DRAFT reader text for the MSR signal classes present in this response (one short
   * paragraph per class explaining what the class means to a reading model). ⚠️ Generated
   * DRAFT — flagged for native editorial polish post-campaign (master brief §E W3 item 3);
   * the taxonomy/coverage is committed, the exact wording is not final acharya-grade prose. */
  signal_reader_text?: Record<string, string>
}

export type RetrievalEnvelope = LegacyEnvelope | V3Envelope

// ── builder ────────────────────────────────────────────────────────────────────

export interface BuildRetrievalEnvelopeParams {
  tool: string
  content: unknown
  query_class?: string
  insight_type?: string | null
  pagination?: Partial<PaginationBlock>
  // Populated only when format === 'v3'; ignored (never emitted) under 'legacy' so the
  // legacy wire shape stays byte-identical for existing consumers (brief §6.3).
  chart_header?: ChartHeader | null
  epistemic?: EpistemicSummary
  as_of_date?: string
  /** W3 Lane L7 — optional timing-hook extensions (plan §8 R-2 item 6). All optional;
   *  omitted → the TimingBlock only carries as_of_date + computed_at as before. */
  timing_anchored?: boolean
  applies_window?: { start: string | null; end: string | null } | null
  valid_until?: string | null
  /** W3 Lane L7 — the standardized prediction claim (plan §8 R-2 item 7), if any. */
  prediction?: PredictionClaim | null
  coverage?: CoverageStamp | null
  verdict?: unknown
  ranking_basis?: Record<string, unknown> | null
  grounding?: Partial<GroundingBlock>
  drill_pointers?: DrillPointer[]
  judgment_flags?: JudgmentFlagEntry[]
  build_id?: string | null
  /** W3-L8 — see `V3Envelope.ledger_version` doc. Passed through verbatim to the v3 envelope. */
  ledger_version?: string | null
  /** R5.1 C1 — populated only by callers that ran this response's content through the
   *  response-budget trimmer (e.g. platform-mcp's response_budget.ts). Emitted under BOTH
   *  formats (additive on legacy too) since the trim is a channel-transport fact, not a
   *  v3-only enrichment. */
  trim_report?: TrimReportEntry[] | null

  // ── W3-L3 "One Envelope" register-block inputs (v3 only) ────────────────────
  /** Injected flag-code → label map (W3-L2 coordination): lets the register block label any
   *  judgment-flag code (e.g. a closed enum landing in a parallel lane) without hardcoding it. */
  flag_labels?: Record<string, string>
  /** Extra caller-supplied register entries appended verbatim (escape hatch for bespoke tokens). */
  register_extra?: RegisterEntry[]
  /** 0..1 verified-row fraction for this response (drives the reading_contract verification
   *  sentence). Falls back to `epistemic.verified_fraction` when omitted. */
  verified_fraction?: number | null
  /** TRUE if this response contains catalog-only rows (single-pass label matches awaiting
   *  cross-verification) — surfaces the §N.6 catalog-only caution in the reading_contract. */
  has_catalog_only_rows?: boolean
  /** TRUE if the serving capability declares a density_contract (drives the density sentence). */
  has_density_contract?: boolean
  /** Set false to suppress register/reading_contract/signal_reader_text generation on this v3
   *  response (default true — they ride on every v3 response). */
  emit_register_block?: boolean
}

/**
 * Build the retrieval envelope for either wire format.
 *
 * ADDITIVE-ONLY (§2 standing ruling): 'v3' never removes a legacy field, only adds new
 * ones and populates previously-null legacy fields with real, response-scoped content.
 */
export function buildRetrievalEnvelope(
  params: BuildRetrievalEnvelopeParams,
  format: EnvelopeFormat = 'legacy',
): RetrievalEnvelope {
  // WP-1.5 receipt honesty: `more_available` is always emitted. If the caller supplied it
  // (e.g. via buildHonestPagination — the authoritative path), honor it. Otherwise derive it
  // conservatively so the field is never a silent `false`: a present next_cursor always means
  // more remains; else a known total that exceeds the served page means more remains.
  const pOffset = params.pagination?.offset ?? 0
  const pLimit = params.pagination?.limit ?? 0
  const pTotal = params.pagination?.total ?? null
  const pCursor = params.pagination?.next_cursor ?? null
  const derivedMore =
    pCursor != null ? true : pTotal != null ? pOffset + pLimit < pTotal : false
  const pagination: PaginationBlock = {
    offset: pOffset,
    limit: pLimit,
    total: pTotal,
    next_cursor: pCursor,
    more_available: params.pagination?.more_available ?? derivedMore,
  }

  const legacy: LegacyEnvelope = {
    envelope_version: 'v1',
    tool: params.tool,
    verdict: null,
    ranking_basis: null,
    grounding: { fact_ids: [], citations: [], grounding_score: null },
    pagination,
    drill_pointers: [],
    judgment_flags: [],
    insight_type: params.insight_type ?? null,
    query_class: params.query_class ?? 'per_chart_structural',
    content: params.content,
    trim_report: params.trim_report ?? null,
  }

  if (format !== 'v3') return legacy

  const nowIso = new Date().toISOString()
  const v3: V3Envelope = {
    ...legacy,
    envelope_version: 'v3',
    response_format: 'v3',
    chart_header: params.chart_header ?? null,
    epistemic:
      params.epistemic ??
      buildEpistemicSummary({ verifiedFraction: null, note: 'No epistemic signal computed for this response.' }),
    timing: {
      as_of_date: params.as_of_date ?? nowIso.slice(0, 10),
      computed_at: nowIso,
      // W3 Lane L7 — emit the extension fields only when the caller supplied them, so a
      // response that carries no time-sensitive claim keeps the minimal 2-field TimingBlock.
      ...(params.timing_anchored !== undefined ? { timing_anchored: params.timing_anchored } : {}),
      ...(params.applies_window !== undefined ? { applies_window: params.applies_window } : {}),
      ...(params.valid_until !== undefined ? { valid_until: params.valid_until } : {}),
    },
    coverage: params.coverage ?? null,
    prediction: params.prediction ?? null,
    verdict: params.verdict ?? null,
    ranking_basis: params.ranking_basis ?? null,
    grounding: {
      fact_ids: params.grounding?.fact_ids ?? [],
      citations: params.grounding?.citations ?? [],
      grounding_score: params.grounding?.grounding_score ?? null,
    },
    drill_pointers: params.drill_pointers ?? [],
    judgment_flags: params.judgment_flags ?? [],
    build_id: params.build_id ?? null,
    ledger_version: params.ledger_version ?? null,
  }

  // ── W3-L3 "One Envelope": register block + reading_contract + signal_reader_text ──
  // Generated additively on every v3 response (unless explicitly suppressed). Everything is
  // derived from THIS response's own assembled content/fields — nothing is fabricated (B.10).
  if (params.emit_register_block !== false) {
    const register = buildRegisterBlock({
      content: v3.content,
      epistemicGrade: v3.epistemic.grade,
      judgmentFlags: v3.judgment_flags,
      drillPointers: v3.drill_pointers,
      flag_labels: params.flag_labels,
      register_extra: params.register_extra,
    })
    v3.register = register

    const registerKinds = Array.from(new Set(register.map(e => e.kind)))
    const signalClassTokens = register.filter(e => e.kind === 'signal_class').map(e => e.token)

    v3.reading_contract = buildReadingContract({
      epistemicGrade: v3.epistemic.grade,
      verifiedFraction: params.verified_fraction ?? v3.epistemic.verified_fraction,
      groundingFactCount: v3.grounding.fact_ids.length,
      coverage: v3.coverage ? { served: v3.coverage.served, total: v3.coverage.total } : null,
      moreAvailable: v3.pagination.more_available,
      judgmentFlags: v3.judgment_flags,
      hasCatalogOnlyRows: params.has_catalog_only_rows,
      hasDensityContract: params.has_density_contract,
      registerKinds,
    })

    // Signal-reader text only for the signal classes actually present in this response.
    v3.signal_reader_text = collectSignalReaderText(signalClassTokens)
  }

  return v3
}

// ── generic best-effort grounding extraction ──────────────────────────────────

/**
 * Best-effort extraction of grounding (fact_ids/citations/grounding_score) from a rowset
 * that already carries fact_id / citation_ref / verification_pass_status columns (the
 * standard L1 chart_facts projection — see get_yoga_dosha.ts, get_positions.ts, etc).
 * Never queries anything new; purely aggregates what the response already served.
 */
export function extractGroundingFromFactRows(
  rows: Array<Record<string, unknown>> | undefined | null,
): GroundingBlock {
  if (!rows || rows.length === 0) {
    return { fact_ids: [], citations: [], grounding_score: null }
  }
  const fact_ids = Array.from(
    new Set(rows.map(r => r['fact_id']).filter((v): v is string => typeof v === 'string' && v.length > 0)),
  )
  const citations = Array.from(
    new Set(rows.map(r => r['citation_ref']).filter((v): v is string => typeof v === 'string' && v.length > 0)),
  )
  const verifiedCount = rows.filter(r => {
    const s = r['verification_pass_status']
    return s === 'two_pass_verified' || s === 'pass'
  }).length
  const grounding_score = rows.length > 0 ? Math.round((verifiedCount / rows.length) * 1000) / 1000 : null
  return { fact_ids, citations, grounding_score }
}
