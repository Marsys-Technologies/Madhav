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
}

export interface V3Envelope extends LegacyEnvelope {
  response_format: 'v3'
  chart_header: ChartHeader | null
  epistemic: EpistemicSummary
  timing: TimingBlock
  coverage: CoverageStamp | null
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
  const pagination: PaginationBlock = {
    offset: params.pagination?.offset ?? 0,
    limit: params.pagination?.limit ?? 0,
    total: params.pagination?.total ?? null,
    next_cursor: params.pagination?.next_cursor ?? null,
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
