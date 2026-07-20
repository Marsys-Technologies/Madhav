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

export interface TimingBlock {
  as_of_date: string
  computed_at: string
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

// ── envelope shapes ────────────────────────────────────────────────────────────

export interface LegacyEnvelope {
  envelope_version: 'v1'
  tool: string
  verdict: unknown | null
  ranking_basis: Record<string, unknown> | null
  grounding: GroundingBlock
  pagination: PaginationBlock
  drill_pointers: DrillPointer[]
  judgment_flags: string[]
  insight_type: string | null
  query_class: string
  content: unknown
  /** R5.1 C1 — additive, null unless this response's `content` was shortened to fit a
   *  channel size ceiling (e.g. the MCP-channel budget facet). Never populated by fabrication
   *  — only ever reports a trim that actually happened to THIS response's own content. */
  trim_report: TrimReportEntry[] | null
}

export interface V3Envelope extends LegacyEnvelope {
  response_format: 'v3'
  chart_header: ChartHeader | null
  epistemic: EpistemicSummary
  timing: TimingBlock
  coverage: CoverageStamp | null
  /** Design §31.5 BUILD PROVENANCE AT SERVE TIME — chart-level build identifier for
   *  this response's data. Undefined/null when not supplied by the caller (honest
   *  null, never fabricated — B.10); callers that track chart builds (e.g. session-pin
   *  serving, design §10.6/§31.3) populate this from the chart's latest complete
   *  `builds` row. Consistency invariant (E-4, extended): one response = one build_id. */
  build_id?: string | null
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
  coverage?: CoverageStamp | null
  verdict?: unknown
  ranking_basis?: Record<string, unknown> | null
  grounding?: Partial<GroundingBlock>
  drill_pointers?: DrillPointer[]
  judgment_flags?: string[]
  build_id?: string | null
  /** R5.1 C1 — populated only by callers that ran this response's content through the
   *  response-budget trimmer (e.g. platform-mcp's response_budget.ts). Emitted under BOTH
   *  formats (additive on legacy too) since the trim is a channel-transport fact, not a
   *  v3-only enrichment. */
  trim_report?: TrimReportEntry[] | null
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
    response_format: 'v3',
    chart_header: params.chart_header ?? null,
    epistemic:
      params.epistemic ??
      buildEpistemicSummary({ verifiedFraction: null, note: 'No epistemic signal computed for this response.' }),
    timing: {
      as_of_date: params.as_of_date ?? nowIso.slice(0, 10),
      computed_at: nowIso,
    },
    coverage: params.coverage ?? null,
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
