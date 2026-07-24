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

// ── W3-L3 "One Envelope" register block + reading_contract + signal_reader_text ─────
// Inlined from the former register_block.ts (2026-07-20, W3 integration) — the envelope
// codegen mirror (generate_envelope.ts) enforces a hard zero-import constraint on this
// file (process-boundary self-containment, §19), and this module's cross-import of
// EpistemicGrade/DrillPointerType/PactStage from envelope.ts tripped that guard. Content
// unchanged from the original module; register_block.ts is now a thin re-export shim.
// ── Token-kind taxonomy (the generic register-entry shape) ─────────────────────

/**
 * The kind of internal token a register entry labels. Deliberately a GENERIC open-ish
 * union (per the W3-L2 coordination note in the lane brief): a parallel lane is landing a
 * closed judgment-flag-code enum, and the register block must be ABLE to label ANY of their
 * codes without hardcoding them — so `flag` is a generic kind and flag labels can be injected
 * at build time (see `flag_labels` on BuildRegisterBlockParams). The kinds:
 *   - `signal_class`   — an MSR `signal_type_class` code (composite_state, yoga, dosha, …)
 *   - `signal_ref`     — a `SIG.MSR.NNN` signal-id reference token
 *   - `epistemic_grade`— one of the 7 closed epistemic-grade tokens
 *   - `drill_uri`      — a `marsys://…` capability/drill URI (labelled by its family segment)
 *   - `flag`           — a judgment-flag code (generic; label injectable by W3-L2's enum)
 *   - `pact_stage`     — a PACT-chain stage marker on a drill pointer
 *   - `pointer_type`   — a typed drill-pointer classical-move code
 */
export type RegisterTokenKind =
  | 'signal_class'
  | 'signal_ref'
  | 'epistemic_grade'
  | 'drill_uri'
  | 'flag'
  | 'pact_stage'
  | 'pointer_type'

/**
 * One register entry: an internal token, its plain-language label, and the token kind.
 * `token` is the exact literal as it appears in the envelope content (so a consumer can
 * string-match it); `label` is a short human/LLM-readable gloss; `kind` classifies it.
 */
export interface RegisterEntry {
  token: string
  label: string
  kind: RegisterTokenKind
}

// ── Canonical label maps (the plain-language glossary source) ──────────────────

/**
 * MSR signal-class labels — enumerated from the LIVE `bodha_msr_signals.signal_type_class`
 * column (19 distinct classes as of 2026-07-20; the migration-325 schema comment is stale).
 * Each label is a compact gloss of what the class MEANS to a reading model. The longer
 * reader-facing paragraphs live in SIGNAL_READER_TEXT below.
 */
export const SIGNAL_CLASS_LABELS: Record<string, string> = {
  composite_state:
    'Composite planetary-state signal (dignity + house + aspect + strength rolled into one graded factor).',
  karaka_alignment: 'Significator (karaka) alignment — how a matter’s natural significator is placed and supported.',
  sade_sati: 'Sade Sati / Saturn-transit-over-Moon phase signal.',
  varga_pattern: 'Divisional-chart (varga) pattern — promise seen in the operative sub-chart (D9, D10, …).',
  panchanga: 'Panchanga (five-limb calendar) signal — tithi / vara / nakshatra / yoga / karana of the birth moment.',
  tradition_specific: 'Tradition-specific rule signal (a reading confined to a named classical school/system).',
  annual: 'Annual (varshaphala / Tajaka) signal keyed to a solar-return year.',
  parivartana: 'Parivartana (mutual sign-exchange) between two grahas’ dispositors.',
  configuration: 'Multi-graha configuration / geometry signal (a named placement pattern).',
  yoga: 'Yoga signal — a named benefic/combinatorial planetary combination.',
  dosha: 'Dosha signal — a named affliction/blemish planetary combination.',
  bhavat_bhavam_amplifier: 'Bhavat-bhavam amplifier — a house judged from itself (Nth-from-Nth) reinforcing a matter.',
  nakshatra_semantic: 'Nakshatra-semantic signal — meaning drawn from the lunar-mansion symbolism.',
  sudarshana_agreement: 'Sudarshana agreement — concurrence of the Lagna, Chandra and Surya vantage charts.',
  varga_ratification_divergence:
    'Varga ratification/divergence — whether the divisional chart confirms or contradicts the rasi promise.',
  arudha: 'Arudha (perceived-image) signal — the projected/manifest reflection of a house.',
  special_lagna: 'Special-lagna signal (Arudha Lagna, Hora Lagna, Ghati Lagna, Bhava Lagna, …).',
  dhana_axis: 'Dhana-axis signal — the wealth-house (2nd/11th and lords) configuration.',
  vargottama_amplification: 'Vargottama amplification — a graha in the same sign in rasi and navamsa, strengthening it.',
}

/**
 * DRAFT reader text, one short paragraph per MSR signal class, telling a reading model what
 * that class MEANS and how much epistemic weight to give it. Enumerated 1:1 with the live
 * `bodha_msr_signals.signal_type_class` values (19 classes).
 *
 * ⚠️ NATIVE-POLISH-PENDING (master brief §E "W3" item 3, verbatim: "generate draft reader
 * text per signal class, flag for native polish post-campaign"). This is GENERATED DRAFT
 * prose — a scaffold that makes the field structurally complete and non-empty — NOT a claim
 * of final acharya-grade wording (CLAUDE.md §J). The native editorial pass replaces this map
 * in a later wave; the taxonomy/coverage is what this lane commits to, the exact wording is not.
 */
export const SIGNAL_READER_TEXT: Record<string, string> = {
  composite_state:
    'DRAFT (native-polish-pending). A composite-state signal fuses a graha’s dignity, house placement, aspects and computed strength into a single graded factor. Read it as the workhorse layer of the chart: most rows are of this class. Weigh it by its epistemic grade and verification status, not by its raw count — a large composite-state population is breadth, not confirmation.',
  karaka_alignment:
    'DRAFT (native-polish-pending). A karaka-alignment signal reports how the natural significator of a matter (e.g. Jupiter for children, Venus for spouse) is itself placed and supported. Treat it as a second, significator-frame reading that must AGREE with the house-frame reading before a promise is called confirmed.',
  sade_sati:
    'DRAFT (native-polish-pending). A sade-sati signal marks the ~7.5-year Saturn transit over the Moon and its flanking signs. Read it as a timing/pressure phase, not a fixed birth promise — its bearing is on WHEN a matter is stressed, not WHETHER it is promised.',
  varga_pattern:
    'DRAFT (native-polish-pending). A varga-pattern signal reads the promise in an operative divisional chart (D9 for marriage/dharma, D10 for career, …). Treat it as the ratification layer: a rasi promise the relevant varga does not echo is weaker than its rasi row alone suggests.',
  panchanga:
    'DRAFT (native-polish-pending). A panchanga signal draws on the five calendrical limbs of the birth moment (tithi, vara, nakshatra, yoga, karana). Read it as constitutional temperament grounding rather than an event predictor.',
  tradition_specific:
    'DRAFT (native-polish-pending). A tradition-specific signal is confined to a named classical school or system and may not generalise. Read it as school-scoped: cite the tradition, and do not silently merge it with mainstream Parashari findings.',
  annual:
    'DRAFT (native-polish-pending). An annual signal is keyed to a solar-return (varshaphala / Tajaka) year. Read it as a one-year overlay on the natal promise — it modulates timing within a year, it does not restate the lifetime promise.',
  parivartana:
    'DRAFT (native-polish-pending). A parivartana signal reports a mutual sign-exchange between two grahas’ dispositors, linking their houses. Read it as a structural bridge: the two houses’ fortunes become coupled, for better or worse depending on the exchange type.',
  configuration:
    'DRAFT (native-polish-pending). A configuration signal names a multi-graha geometry or placement pattern. Read it as a structural feature of the chart to be corroborated by dignity/strength before it carries predictive weight.',
  yoga:
    'DRAFT (native-polish-pending). A yoga signal names a benefic/combinatorial planetary combination. IMPORTANT: an MSR yoga-class row is a catalog-level match — confirm it against the firings-authoritative surface (ganita_yoga_firings) before reading it as an active, cross-verified yoga rather than a mere pattern present.',
  dosha:
    'DRAFT (native-polish-pending). A dosha signal names an affliction/blemish combination. As with yoga, an MSR dosha row is catalog-level: check for cancellation (bhanga) and confirm firing before reading it as an operative affliction.',
  bhavat_bhavam_amplifier:
    'DRAFT (native-polish-pending). A bhavat-bhavam-amplifier signal judges a house from itself (the Nth house from the Nth), reinforcing a matter when both vantages agree. Read it as an amplifier, not an independent promise.',
  nakshatra_semantic:
    'DRAFT (native-polish-pending). A nakshatra-semantic signal draws meaning from lunar-mansion symbolism (deity, gana, symbol). Read it as qualitative colouring of a placement, not a quantitative strength term.',
  sudarshana_agreement:
    'DRAFT (native-polish-pending). A sudarshana-agreement signal reports concurrence across the Lagna, Chandra and Surya vantage charts. Read HIGH agreement as a robustness/confidence multiplier and disagreement as a flag to re-judge from the dissenting frame.',
  varga_ratification_divergence:
    'DRAFT (native-polish-pending). A varga-ratification/divergence signal states whether the divisional chart confirms or contradicts the rasi promise. Read a DIVERGENCE as a demotion of confidence and a pointer to re-check the matter in the varga.',
  arudha:
    'DRAFT (native-polish-pending). An arudha signal reports the projected/perceived image of a house (how a matter APPEARS to the world), distinct from its literal placement. Read it as the perception layer, kept separate from material reality.',
  special_lagna:
    'DRAFT (native-polish-pending). A special-lagna signal reads a matter from a non-standard ascendant (Arudha, Hora, Ghati, Bhava Lagna, …). Read it as an additional vantage, corroborating or qualifying the rasi-Lagna reading.',
  dhana_axis:
    'DRAFT (native-polish-pending). A dhana-axis signal reports the wealth-house configuration (2nd/11th houses and their lords). Read it as the material-resource layer, to be timed against the operative dasha before any wealth-timing claim.',
  vargottama_amplification:
    'DRAFT (native-polish-pending). A vargottama-amplification signal marks a graha occupying the same sign in the rasi and the navamsa, strengthening its significations. Read it as a strength amplifier on whatever that graha already promises.',
}

/** The closed epistemic-grade vocabulary (mirrors envelope.ts EpistemicGrade), plain-labelled. */
export const EPISTEMIC_GRADE_LABELS: Record<EpistemicGrade, string> = {
  ganita_fact: 'Deterministic L1 chart fact — computed, not interpreted; treat as ground truth.',
  verified_signal: 'Cross-verified signal (≥50% of rows two-pass verified) — a confirmed reading.',
  single_pass_signal: 'Single-pass signal (<50% verified) — a candidate reading awaiting cross-verification; not confirmed.',
  classical_contested: 'Classically contested — sources disagree; present both sides, do not resolve silently.',
  calibrated_posterior: 'Calibrated posterior — an empirically calibrated probability from accrued outcome data.',
  structural_prior: 'Structural prior — a structural (uncalibrated) estimate; no outcome data yet backs the number.',
  floored_null: 'Floored null — no supporting data; the honest empty result, NOT a negative finding.',
}

/** PACT-chain stage labels (mirrors envelope.ts PactStage). */
export const PACT_STAGE_LABELS: Record<PactStage, string> = {
  promise: 'PACT stage 1 — PROMISE: the checklist verdict that a matter is natally promised.',
  confirmation: 'PACT stage 2 — CONFIRMATION: the operative-varga check ratifying the promise.',
  activation: 'PACT stage 3 — ACTIVATION: which dasha period carries/activates the promise.',
  trigger: 'PACT stage 4 — TRIGGER: the transit gate that fires an activated promise in-window.',
}

/** Typed drill-pointer classical-move labels (mirrors envelope.ts DrillPointerType). */
export const POINTER_TYPE_LABELS: Record<DrillPointerType, string> = {
  confirm_in_varga: 'Next step: confirm the promise in the operative divisional chart.',
  check_from_moon: 'Next step: re-judge the same matter from the Chandra (Moon) frame (Sudarshana).',
  check_bhanga: 'Next step: check for a cancellation / near-miss (bhanga) on a bearing yoga or dosha.',
  opposing_yoga: 'Next step: a yoga/dosha of OPPOSITE valence also bears on this matter — weigh it.',
  karaka_condition: 'Next step: examine the significator (karaka) graha’s own condition directly.',
  dasha_of_promise: 'Next step: locate which dasha period carries/activates the promise.',
  transit_gate: 'Next step: check current/upcoming transits gating an already-activated promise.',
  dispositor_chain: 'Next step: follow the lord-of-the-lord (dispositor) indirection one level deeper.',
  tail_dissent: 'Next step: the mandatory dissent / tail-check step of the investigation protocol.',
  other: 'Next step outside the closed classical-move vocabulary (see the pointer hint).',
}

/**
 * `marsys://` drill-URI FAMILY labels. A drill URI is `marsys://<primitive>/<segment>/<name>`;
 * we label by the `<primitive>/<segment>` family (layer or role) rather than enumerating every
 * leaf, so any URI in the estate resolves to a family label. Keyed by the family prefix.
 */
export const DRILL_URI_FAMILY_LABELS: Record<string, string> = {
  'tool/L0': 'L0 Brahmagyan tool — classical-text / reference retrieval.',
  'tool/L1': 'L1 Ganita tool — deterministic chart-fact lookup.',
  'tool/L2': 'L2 Bodha tool — interpreted signal / synthesis surface.',
  'tool/L3': 'L3 Kala tool — time-keyed (dasha / transit / muhurta) surface.',
  'tool/L4': 'L4 Phala tool — predictive outlook / anchor surface.',
  'tool/L5': 'L5 Mimamsa tool — calibration / trust-metadata surface.',
  'tool/L-DOMAIN': 'Life-domain assessment umbrella (career / health / marriage / wealth).',
  'tool/L-JUDGMENT': 'Judgment-query surface — checklist verdict with grounding.',
  'tool/L-PACT': 'PACT-chain query surface — promise → confirmation → activation → trigger.',
  'tool/L-TIMING': 'Timing surface — yoga activation by dasha.',
  'tool/synergy': 'Cross-layer synergy synthesizer.',
  'tool/channel': 'Channel / routing surface.',
  'tool/synthesis': 'Cross-layer synthesis surface.',
  'tool/maro': 'MARO adapter/profile surface.',
  'tool/router': 'Router surface.',
  'resource/asset-registry': 'Asset-registry resource — build-catalog metadata.',
  'resource/ephemeris-cache': 'Ephemeris-cache resource — precomputed positions.',
  'resource/sutravali': 'Sutravali resource — classical-rule corpus.',
  'resource/catalog': 'Capability-catalog resource.',
  'prompt/intent-classify': 'Intent-classification prompt.',
}

// ── Token detection ────────────────────────────────────────────────────────────

const SIG_MSR_RE = /SIG\.MSR\.[0-9]+/g
const MARSYS_URI_RE = /marsys:\/\/[A-Za-z0-9/_-]+/g

/** Extract the `<primitive>/<segment>` family key from a marsys:// URI, or null. */
export function drillUriFamily(uri: string): string | null {
  const m = uri.match(/^marsys:\/\/([A-Za-z0-9-]+)\/([A-Za-z0-9-]+)/)
  if (!m) return null
  return `${m[1]}/${m[2]}`
}

// ── Register-block builder ─────────────────────────────────────────────────────

export interface BuildRegisterBlockParams {
  /** The assembled v3 content (any shape); deep-scanned for signal-class + SIG.MSR + marsys tokens. */
  content?: unknown
  /** The response's epistemic grade (labelled if present). */
  epistemicGrade?: EpistemicGrade | null
  /** judgment_flags array (either shape — structured {code,...} or a legacy bare string);
   *  each entry's code is labelled as a `flag`. */
  judgmentFlags?: JudgmentFlagEntry[]
  /** drill_pointers; their pointer_type / pact_stage / instrument URIs are labelled. */
  drillPointers?: Array<{ instrument?: string; pointer_type?: string; pact_stage?: string }>
  /**
   * Injected flag-code labels (W3-L2 coordination): a map from a flag code to its plain-language
   * label. Any judgment-flag code present in the response that also appears here is labelled from
   * this map; codes not here still get a generic labelled entry (so no token is left unlabelled).
   */
  flag_labels?: Record<string, string>
  /** Extra caller-supplied entries appended verbatim (escape hatch; e.g. bespoke tokens). */
  register_extra?: RegisterEntry[]
}

/**
 * Build the register block: scan the response for internal tokens that ACTUALLY APPEAR and
 * emit one labelled entry per distinct token. Response-scoped by construction — it never
 * dumps the whole glossary, only the tokens this response uses (plan §R-2: "adjacent to it").
 */
export function buildRegisterBlock(params: BuildRegisterBlockParams): RegisterEntry[] {
  const entries = new Map<string, RegisterEntry>() // keyed by `${kind}:${token}` for dedupe
  const add = (token: string, label: string, kind: RegisterTokenKind) => {
    const key = `${kind}:${token}`
    if (!entries.has(key)) entries.set(key, { token, label, kind })
  }

  const json = params.content === undefined ? '' : safeStringify(params.content)

  // signal-class tokens: any known class code appearing anywhere in the content.
  for (const [cls, label] of Object.entries(SIGNAL_CLASS_LABELS)) {
    // match as a whole-word token to avoid substring false positives.
    const re = new RegExp(`(?<![A-Za-z0-9_])${cls}(?![A-Za-z0-9_])`)
    if (re.test(json)) add(cls, label, 'signal_class')
  }

  // SIG.MSR.NNN signal-id references.
  for (const m of json.matchAll(SIG_MSR_RE)) {
    add(m[0], `MSR signal reference ${m[0]} — resolve via bodha_signals_get for its constituent L1 facts.`, 'signal_ref')
  }

  // marsys:// drill URIs (from content AND from drill_pointer instruments).
  const uriSources = [json, ...(params.drillPointers ?? []).map(p => p.instrument ?? '')]
  for (const src of uriSources) {
    for (const m of src.matchAll(MARSYS_URI_RE)) {
      const fam = drillUriFamily(m[0])
      const label = (fam && DRILL_URI_FAMILY_LABELS[fam]) || 'Internal drill URI — a capability to call for the next step.'
      add(m[0], label, 'drill_uri')
    }
  }

  // epistemic grade.
  if (params.epistemicGrade) {
    add(params.epistemicGrade, EPISTEMIC_GRADE_LABELS[params.epistemicGrade], 'epistemic_grade')
  }

  // judgment-flag codes.
  for (const raw of params.judgmentFlags ?? []) {
    const code = flagCode(raw)
    if (!code) continue
    const injected = params.flag_labels?.[code]
    add(code, injected ?? `Judgment flag — an honest coverage/resolution disclosure (${code}); see the flag text for detail.`, 'flag')
  }

  // pointer_type + pact_stage on drill pointers.
  for (const p of params.drillPointers ?? []) {
    if (p.pointer_type && p.pointer_type in POINTER_TYPE_LABELS) {
      add(p.pointer_type, POINTER_TYPE_LABELS[p.pointer_type as DrillPointerType], 'pointer_type')
    }
    if (p.pact_stage && p.pact_stage in PACT_STAGE_LABELS) {
      add(p.pact_stage, PACT_STAGE_LABELS[p.pact_stage as PactStage], 'pact_stage')
    }
  }

  const out = Array.from(entries.values())
  if (params.register_extra) out.push(...params.register_extra)
  return out
}

/** The flag CODE — read directly off `.code` for the structured shape; for a legacy bare
 *  string, the token before the first ':' (e.g. `karaka_unresolved: Jupiter` → `karaka_unresolved`). */
function flagCode(raw: JudgmentFlagEntry): string | null {
  if (!raw) return null
  if (typeof raw !== 'string') return raw.code
  const idx = raw.indexOf(':')
  return (idx >= 0 ? raw.slice(0, idx) : raw).trim() || null
}

/** JSON.stringify that never throws on cycles (best-effort token scan). */
function safeStringify(v: unknown): string {
  const seen = new WeakSet()
  try {
    return JSON.stringify(v, (_k, val) => {
      if (typeof val === 'object' && val !== null) {
        if (seen.has(val as object)) return undefined
        seen.add(val as object)
      }
      return val
    }) ?? ''
  } catch {
    return String(v)
  }
}

// ── reading_contract generator ─────────────────────────────────────────────────

export interface BuildReadingContractParams {
  epistemicGrade?: EpistemicGrade | null
  /** 0..1 fraction of two-pass-verified rows in this response, if computed. */
  verifiedFraction?: number | null
  /** grounding fact_ids present in this response (used to say whether the verdict is grounded). */
  groundingFactCount?: number
  /** coverage: served vs total for the family this response slices (drives the completeness sentence). */
  coverage?: { served: number; total: number | null } | null
  /** more rows exist beyond this page (pagination.more_available). */
  moreAvailable?: boolean
  /** judgment_flags present (drives the honest-gap sentence). */
  judgmentFlags?: JudgmentFlagEntry[]
  /** TRUE if the response contains catalog-only rows (e.g. requires_pass / catalog_only markers). */
  hasCatalogOnlyRows?: boolean
  /** whether the response carries a density_contract declaration on its capability. */
  hasDensityContract?: boolean
  /** distinct register-entry kinds present (drives the "how to read tokens" sentence). */
  registerKinds?: RegisterTokenKind[]
}

/**
 * Generate the reading_contract: a SINGLE paragraph telling the consuming LLM how to read
 * THIS response's grades/coverage/flags/register. GENERATED from the response's content shape
 * — a fully-grounded confirmed response and a sparse/floored one produce visibly different
 * paragraphs (§N.6: density signaling is data, not narration; the contract must not be static
 * boilerplate). Never lets a catalog-only row read as confirmed; never papers over an empty gap.
 */
export function buildReadingContract(params: BuildReadingContractParams): string {
  const s: string[] = []

  // 1. Grade sentence — how to weight this response's central finding.
  const grade = params.epistemicGrade ?? null
  if (grade) {
    s.push(`This response is graded ${grade}: ${EPISTEMIC_GRADE_LABELS[grade]}`)
  } else {
    s.push('This response carries no computed epistemic grade; treat its content as unweighted context, not a confirmed finding.')
  }

  // 2. Grounding sentence — is the verdict backed by resolvable L1 facts?
  if (grade === 'floored_null') {
    s.push('It is an HONEST EMPTY result — no supporting data was found; do not read the absence as a negative finding, and do not manufacture a reading from it.')
  } else if ((params.groundingFactCount ?? 0) > 0) {
    s.push(`Its reading is grounded in ${params.groundingFactCount} resolvable L1 fact reference(s) — you may follow each fact_id down to its deterministic source.`)
  } else {
    s.push('Its reading is NOT yet anchored to resolvable L1 fact references in this envelope; drill via the pointers before treating it as confirmed.')
  }

  // 3. Verification sentence — only when a fraction was computed.
  if (params.verifiedFraction != null) {
    const pct = Math.round(params.verifiedFraction * 100)
    s.push(
      pct >= 50
        ? `${pct}% of the rows here are cross-verified (two-pass) — the majority layer is confirmed.`
        : `Only ${pct}% of the rows here are cross-verified — most are single-pass candidates, not confirmations.`,
    )
  }

  // 4. Catalog-only caution — §N.6 Part 1: never let a label match read as a confirmed finding.
  if (params.hasCatalogOnlyRows) {
    s.push('Some rows are CATALOG-ONLY (single-pass label matches awaiting cross-verification): they are counted and served but are NOT confirmed findings — confirm them against the firings-authoritative surface before relying on them.')
  }

  // 5. Coverage/completeness sentence.
  if (params.coverage) {
    const { served, total } = params.coverage
    if (total == null) {
      s.push(`This is a bounded slice of ${served} served row(s); the full family size is not computable here, so do not read the served count as the total.`)
    } else if (served < total) {
      s.push(`This is ${served} of ${total} rows in the family — a partial slice; more remain.`)
    } else {
      s.push(`This is the complete family (${served} of ${total} rows) — nothing is withheld.`)
    }
  } else if (params.moreAvailable) {
    s.push('More rows exist beyond this page — page via the cursor before drawing a whole-family conclusion.')
  }

  // 6. Flags sentence — honest-gap disclosures.
  const flags = params.judgmentFlags ?? []
  if (flags.length > 0) {
    s.push(`It carries ${flags.length} judgment flag(s) disclosing coverage/resolution gaps (see judgment_flags) — read each as a stated limit on the verdict, not decoration.`)
  }

  // 7. Register sentence — how to decode the tokens.
  const kinds = params.registerKinds ?? []
  if (kinds.length > 0) {
    s.push(`Internal tokens in this envelope (${kinds.join(', ')}) each have a plain-language label in the \`register\` block — read the label adjacent to any token you do not recognise rather than guessing.`)
  }

  // 8. Density sentence — only when a density contract is declared.
  if (params.hasDensityContract) {
    s.push('This capability declares a density contract: rows are layered by confidence, and the densest/confirmed layer is protected from truncation first — do not flatten the layers into one undifferentiated list.')
  }

  return s.join(' ')
}

// ── signal_reader_text selector ────────────────────────────────────────────────

/**
 * Collect the draft reader text for the signal classes PRESENT in this response (from the
 * register block's signal_class entries). Response-scoped: only the classes actually served
 * get their paragraph attached. Pass `all: true` to get the full 19-class map (used by the
 * coverage test / a docs projection).
 */
export function collectSignalReaderText(
  signalClassTokens: string[],
  opts?: { all?: boolean },
): Record<string, string> {
  if (opts?.all) return { ...SIGNAL_READER_TEXT }
  const out: Record<string, string> = {}
  for (const cls of signalClassTokens) {
    if (SIGNAL_READER_TEXT[cls]) out[cls] = SIGNAL_READER_TEXT[cls]
  }
  return out
}

/** The count of enumerated signal classes (for reporting / test assertions). */
export const SIGNAL_CLASS_COUNT = Object.keys(SIGNAL_READER_TEXT).length


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
  // ── provenance-stamp drift (distinct subsystem, provenance_stamp.ts) — included so a
  // value it already emits (as a plain string, unconverted this wave) is always a VALID
  // code, not an orphaned literal outside the closed vocabulary. ──
  'chart_rebuilt_mid_provenance_stamp_refreshed',
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
   *  null, never fabricated — B.10); callers that track chart builds (e.g. provenance-stamp
   *  serving, design §10.6/§31.3) populate this from the chart's latest complete
   *  `builds` row. Consistency invariant (E-4, extended): one response = one build_id. */
  build_id?: string | null
  /** W3-L8 (RETRIEVAL_PLANE_ELEVATION_PLAN §9.6-3/4 + §9.7, W-26/W-28): the serving-catalog
   *  staleness signal, orthogonal to `build_id` — see `provenance_stamp.ts`'s `ProvenanceStampValues.
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
  /**
   * Entitlement gate for raw internal schema detail (finding: "provenance.tables /
   * source_table expose raw internal schema names regardless of entitlement"). Pass
   * `false` when the calling principal is an ordinary end-user (not native/debug-tier) —
   * `content` is then run through `redactProvenanceTables`, which strips the raw DB
   * `tables` / `source_table` fields off every `provenance` block it finds (every other
   * provenance field — `source`, `note`, `ranking_note`, ... — rides through unchanged).
   * Omitted or `true` (the default) preserves today's byte-identical content for every
   * existing call site — this is opt-in gating, not a silent behavior change. Applies to
   * BOTH wire formats: a `provenance` block already lives inside `content` regardless of
   * `legacy` vs `v3`, so the gate must not be v3-only. */
  entitled?: boolean
}

/**
 * WP — B.11 orientation/provenance schema-detail gate (finding: "provenance.tables /
 * source_table expose raw internal schema names regardless of entitlement"). Recursively
 * walks an arbitrary content tree and, when the caller is NOT entitled to internal schema
 * detail (native/debug tier only), strips the raw DB `tables` / `source_table` fields off
 * every `provenance` block it finds — every other provenance field (`source`, `note`,
 * `ranking_note`, ...) rides through unchanged, and a `schema_detail_gated: true` marker is
 * added so a caller can tell the block was trimmed rather than simply empty (B.10 — never a
 * silent drop). Pure/non-mutating: returns the SAME reference when nothing needed
 * redacting (cheap no-op for the overwhelmingly common case — most content trees carry no
 * `provenance` block at all), a new object only along the path where one was found.
 *
 * Consistent with the envelope's own documented intent (design §19 process-boundary
 * discipline / §10 technical-scaffolding-vs-user-facing-content split): raw internal table
 * names are scaffolding for a native/debug caller auditing where a claim came from, not
 * content an ordinary end-user-facing call needs to see.
 */
export function redactProvenanceTables<T>(value: T, entitled: boolean): T {
  if (entitled) return value
  return redactProvenanceTablesWalk(value) as T
}

function redactProvenanceTablesWalk(value: unknown): unknown {
  if (value === null || typeof value !== 'object') return value
  if (Array.isArray(value)) {
    let changed = false
    const next = value.map(v => {
      const r = redactProvenanceTablesWalk(v)
      if (r !== v) changed = true
      return r
    })
    return changed ? next : value
  }
  const obj = value as Record<string, unknown>
  let changed = false
  const next: Record<string, unknown> = {}
  for (const [k, v] of Object.entries(obj)) {
    if (k === 'provenance' && v !== null && typeof v === 'object' && !Array.isArray(v)) {
      const prov = v as Record<string, unknown>
      if ('tables' in prov || 'source_table' in prov) {
        changed = true
        const redacted: Record<string, unknown> = {}
        for (const [pk, pv] of Object.entries(prov)) {
          if (pk === 'tables' || pk === 'source_table') continue
          redacted[pk] = pv
        }
        redacted['schema_detail_gated'] = true
        next[k] = redacted
        continue
      }
    }
    const r = redactProvenanceTablesWalk(v)
    if (r !== v) changed = true
    next[k] = r
  }
  return changed ? next : value
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
    content: redactProvenanceTables(params.content, params.entitled !== false),
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
