/**
 * Paripraśna wire protocol — typed SSE event vocabulary (lane PB-1/S-1).
 *
 * This module is the SINGLE SOURCE OF TRUTH for the Paripraśna stream wire
 * format. It is deliberately ISOMORPHIC (pure Zod + pure functions, no
 * `server-only`, no Node/stream imports) so it can be imported by BOTH the
 * server route (`app/api/pariprashna/route.ts`, which emits) AND client code
 * (which decodes). The server-bound writer lives separately in
 * `./emitter.ts` (it binds a `ReadableStreamDefaultController`); this file
 * stays free of any runtime-specific surface.
 *
 * Design invariants (gate assertions for lane S-1):
 *   • ZERO `as any` — every event is a Zod-validated, statically-typed object.
 *   • Every event carries a monotonic `seq` and an emission timestamp `t`.
 *   • The union is a `z.discriminatedUnion` on `type`, so a decoder can
 *     narrow exhaustively.
 *
 * Event vocabulary (locked with sibling lane C-2 — this authored fresh; C-2
 * had not yet drafted the module):
 *   turn.open · phase · activity.upsert · block.open|delta|commit ·
 *   seam.open|set · citation.define · flag · grade · turn.commit · turn.close · error
 */

import { z } from 'zod'

// ---------------------------------------------------------------------------
// Shared enums / scalars
// ---------------------------------------------------------------------------

/**
 * `reading_depth` request tier. `auto` = engine-chosen coverage; `deep_dive`
 * forces the completeness / dossier composition path (maximal chart coverage).
 * The set is intentionally open to extension; at least `auto` + `deep_dive`
 * per the PB-1 contract.
 */
export const ReadingDepthSchema = z.enum(['auto', 'deep_dive'])
export type ReadingDepth = z.infer<typeof ReadingDepthSchema>

/**
 * Verbosity / length tier. NOTE: the web engine has no live verbosity contract
 * (the `reading_depth:deep_dive` + `exhaustive` verbosity contract landed
 * MCP-side in the samapana track-B work, which is out of scope for this Next.js
 * app). These values are accepted and echoed on `turn.open` for the client, but
 * only `standard`/`brief` currently bind to a live lever (the ConsumeStyle
 * `brief` suffix). See TODO(PB-4) in the route.
 */
export const LengthTierSchema = z.enum(['brief', 'standard', 'exhaustive'])
export type LengthTier = z.infer<typeof LengthTierSchema>

/** Phase names the engine transitions through. */
export const PhaseNameSchema = z.enum(['plan', 'retrieve', 'synthesize', 'finalize'])
export type PhaseName = z.infer<typeof PhaseNameSchema>

/** Every event carries these. */
const EnvelopeShape = {
  /** Monotonic per-turn sequence number, starting at 0. */
  seq: z.number().int().nonnegative(),
  /** Emission wall-clock time, epoch ms. */
  t: z.number().int().nonnegative(),
} as const

// ---------------------------------------------------------------------------
// Event schemas
// ---------------------------------------------------------------------------

/**
 * `turn.open` — ALWAYS the first event on the stream, written BEFORE the
 * planner runs. Establishes turn identity + the bound request params.
 */
export const TurnOpenEventSchema = z.object({
  type: z.literal('turn.open'),
  ...EnvelopeShape,
  turn_id: z.string(),
  conversation_id: z.string(),
  chart_id: z.string(),
  model_id: z.string(),
  reading_depth: ReadingDepthSchema,
  length_tier: LengthTierSchema,
})
export type TurnOpenEvent = z.infer<typeof TurnOpenEventSchema>

/**
 * `phase` — coarse pipeline-phase transition. The initial `{plan, start}` is
 * emitted immediately after `turn.open`, before the planner is invoked.
 * `pass_id` is present on retrieve/synthesize phases of adaptive multi-pass turns.
 */
export const PhaseEventSchema = z.object({
  type: z.literal('phase'),
  ...EnvelopeShape,
  phase: PhaseNameSchema,
  status: z.enum(['start', 'end']),
  pass_id: z.number().int().positive().optional(),
  ms: z.number().int().nonnegative().optional(),
})
export type PhaseEvent = z.infer<typeof PhaseEventSchema>

/**
 * `activity.upsert` — a KEYED, upsertable activity row (planner-selected tool,
 * agentic-loop tool call, or a deterministic stage). The client keys on `key`
 * and replaces prior state, so running→done is one row, not two. Carries the
 * i18n `label_key` and the `pass_id` it belongs to (so the client can group
 * activities under the correct adaptive pass).
 */
export const ActivityUpsertEventSchema = z.object({
  type: z.literal('activity.upsert'),
  ...EnvelopeShape,
  key: z.string(),
  label_key: z.string(),
  pass_id: z.number().int().positive(),
  status: z.enum(['running', 'done', 'error']),
  detail: z.string().optional(),
  count: z.number().int().nonnegative().optional(),
  ms: z.number().int().nonnegative().optional(),
})
export type ActivityUpsertEvent = z.infer<typeof ActivityUpsertEventSchema>

/** `block.open` — a new prose (or thinking) block begins within a pass. */
export const BlockOpenEventSchema = z.object({
  type: z.literal('block.open'),
  ...EnvelopeShape,
  block_id: z.string(),
  pass_id: z.number().int().positive(),
  role: z.enum(['prose', 'thinking']),
})
export type BlockOpenEvent = z.infer<typeof BlockOpenEventSchema>

/** `block.delta` — an incremental text chunk appended to an open block. */
export const BlockDeltaEventSchema = z.object({
  type: z.literal('block.delta'),
  ...EnvelopeShape,
  block_id: z.string(),
  delta: z.string(),
})
export type BlockDeltaEvent = z.infer<typeof BlockDeltaEventSchema>

/** `block.commit` — a block is finalized; carries the full committed text. */
export const BlockCommitEventSchema = z.object({
  type: z.literal('block.commit'),
  ...EnvelopeShape,
  block_id: z.string(),
  text: z.string(),
})
export type BlockCommitEvent = z.infer<typeof BlockCommitEventSchema>

/**
 * `seam.open` — marks a pass boundary on an adaptive multi-pass turn: the
 * engine re-entered retrieval AFTER already emitting prose. Derived from the
 * engine's own control flow (a tool-use event following prose), never from
 * text heuristics. `pass_id` is the id of the NEW pass being opened.
 */
export const SeamOpenEventSchema = z.object({
  type: z.literal('seam.open'),
  ...EnvelopeShape,
  pass_id: z.number().int().positive(),
  label_key: z.string(),
})
export type SeamOpenEvent = z.infer<typeof SeamOpenEventSchema>

/**
 * `seam.set` — emitted when prose RESUMES after a `seam.open`; carries a short
 * human summary of what the new pass is doing / found.
 */
export const SeamSetEventSchema = z.object({
  type: z.literal('seam.set'),
  ...EnvelopeShape,
  pass_id: z.number().int().positive(),
  summary: z.string(),
})
export type SeamSetEvent = z.infer<typeof SeamSetEventSchema>

/**
 * `citation.define` — defines a citation the prose references (SIG.MSR.NNN etc).
 *
 * `reader_label` + `grade` are OPTIONAL, additive fields (PB-1/integrate
 * reconciliation with lane S-3's citation pipeline). S-3 resolves each citation
 * to a reader-safe label + a verification grade; carrying them here lets that
 * rich data ride on the SINGLE `citation.define` event rather than forcing a
 * correlated split `grade` event. Both are optional so pre-S-3 emitters (and
 * the isomorphic decoder) stay valid without them.
 *   • `snippet` remains the reader-visible short text (S-3 sets it = reader_label).
 *   • `reader_label` is the explicit reader-safe label (never an internal id).
 *   • `grade` is S-3's verification tier (primary | supporting | contextual |
 *     unverified) rendered as a string — a graded assessment, not narration.
 * Audit-channel internals (source table, fact ids) are DELIBERATELY not carried
 * on this event — they stay server-side (see citations/protocol_adapter.ts).
 */
export const CitationDefineEventSchema = z.object({
  type: z.literal('citation.define'),
  ...EnvelopeShape,
  index: z.number().int(),
  signal_id: z.string(),
  layer: z.string(),
  snippet: z.string(),
  reader_label: z.string().optional(),
  grade: z.string().optional(),
})
export type CitationDefineEvent = z.infer<typeof CitationDefineEventSchema>

/**
 * `flag` — a judgment/quality flag surfaced to the caller (e.g.
 * `no_leakage_capabilities_stripped`, `citation_gate_warn`, a prediction
 * candidate). `code` is a stable label_key; `level` grades severity.
 */
export const FlagEventSchema = z.object({
  type: z.literal('flag'),
  ...EnvelopeShape,
  code: z.string(),
  level: z.enum(['info', 'warn', 'error']),
  detail: z.string().optional(),
})
export type FlagEvent = z.infer<typeof FlagEventSchema>

/**
 * `grade` — a graded assessment of some subject (e.g. `citation_gate` → PASS,
 * `completeness` → a coverage fraction rendered as a string). Data, not narration.
 */
export const GradeEventSchema = z.object({
  type: z.literal('grade'),
  ...EnvelopeShape,
  subject: z.string(),
  grade: z.string(),
  detail: z.string().optional(),
})
export type GradeEvent = z.infer<typeof GradeEventSchema>

/**
 * `grounding_summary` — G2-B (PPR-08/FD-2/FD-6) SERVER-DERIVED citation
 * rollup for a turn, carried as an OPTIONAL, ADDITIVE field on `turn.commit`
 * (same non-breaking-extension convention `citation.define`'s `reader_label`
 * + `grade` fields used for the S-3 reconciliation — see that schema's
 * comment). Computed from the ACTUAL `citation.define` events the S-3
 * rewriter resolved this turn (never re-derived from prose) plus the turn's
 * own floor/completeness receipt — never a second, independently-computed
 * coverage number (`pipeline/citations/grounding_summary.ts` is the single
 * builder).
 *
 * PRESENCE IS THE SIGNAL: when this field is absent, the client has no
 * server-derived rollup for the turn and must fall back to its own
 * client-side citation tally — and must label that fallback as an estimate
 * (`state/groundingRollup.ts` / `state/s1LiveAdapter.ts`, GroundingSummary.
 * source). Never invent this field's shape from something else; an honest
 * absence is the correct signal for "no server rollup" (§N.7 item 6).
 */
export const GroundingSummaryGradeCountsSchema = z.object({
  primary: z.number().int().nonnegative(),
  supporting: z.number().int().nonnegative(),
  contextual: z.number().int().nonnegative(),
  unverified: z.number().int().nonnegative(),
  prior_reading: z.number().int().nonnegative(),
})
export type GroundingSummaryGradeCounts = z.infer<typeof GroundingSummaryGradeCountsSchema>

export const ServerGroundingSummarySchema = z.object({
  citation_count: z.number().int().nonnegative(),
  hallucination_count: z.number().int().nonnegative(),
  grade_counts: GroundingSummaryGradeCountsSchema,
  /** Read straight off the turn's WebCompletenessReceipt.coverage — null when no receipt was built. */
  completeness: z
    .object({
      served: z.number().int().nonnegative(),
      floor_item_total: z.number().int().nonnegative(),
    })
    .nullable(),
  /** Human-readable one-line rollup, e.g. "4/6 floor items served". Null when no receipt exists. */
  completeness_line: z.string().nullable(),
})
export type ServerGroundingSummary = z.infer<typeof ServerGroundingSummarySchema>

/**
 * `turn.commit` — the assistant message has been persisted; carries the
 * durable message id + persistence status.
 */
export const TurnCommitEventSchema = z.object({
  type: z.literal('turn.commit'),
  ...EnvelopeShape,
  turn_id: z.string(),
  conversation_id: z.string(),
  message_id: z.string(),
  status: z.enum(['ok', 'error']),
  assistant_chars: z.number().int().nonnegative(),
  grounding_summary: ServerGroundingSummarySchema.optional(),
})
export type TurnCommitEvent = z.infer<typeof TurnCommitEventSchema>

/** `turn.close` — the LAST event on the stream. */
export const TurnCloseEventSchema = z.object({
  type: z.literal('turn.close'),
  ...EnvelopeShape,
  turn_id: z.string(),
  status: z.enum(['ok', 'error', 'aborted']),
  ms: z.number().int().nonnegative(),
})
export type TurnCloseEvent = z.infer<typeof TurnCloseEventSchema>

/**
 * `error` — an IN-STREAM error. Planner faults, chart-resolution failures, and
 * adapter faults are all surfaced here (never as a post-headers HTTP status),
 * because the stream is already open by the time any of them can occur.
 */
export const ErrorEventSchema = z.object({
  type: z.literal('error'),
  ...EnvelopeShape,
  code: z.string(),
  message: z.string(),
  retryable: z.boolean(),
  phase: PhaseNameSchema.optional(),
})
export type ErrorEvent = z.infer<typeof ErrorEventSchema>

/**
 * `snapshot.apply` — ADDITIVE (lane PB-2/M-5, resume protocol). Emitted by
 * the reconnect path (`/api/pariprashna/resume`) INSTEAD OF an incremental
 * replay when the client's requested `Last-Event-ID` seq has already been
 * evicted from the server's per-turn ring buffer (buffer too small / too
 * much time passed since disconnect). Carries the CURRENT COMMITTED STATE as
 * ONE blob — never a partial replay — so the client applies it in a single
 * write with NO replay animation (B.10: never silently lose data; never
 * silently duplicate a block). Always paired with a preceding `flag` event
 * `code: 'resumed_via_snapshot'` for disclosure — reusing the existing `flag`
 * event type (its `code` is a free string) rather than adding a new field,
 * per the additive-only extension constraint on this module.
 */
export const SnapshotApplyEventSchema = z.object({
  type: z.literal('snapshot.apply'),
  ...EnvelopeShape,
  turn_id: z.string(),
  /** Full committed-so-far text (all committed blocks + any open tail), one blob. */
  text: z.string(),
  citations: z.array(
    z.object({
      index: z.number().int(),
      signal_id: z.string(),
      layer: z.string(),
      snippet: z.string(),
    }),
  ),
  /** What state the turn is in as of the snapshot — `open` may still be tailed live. */
  turn_status: z.enum(['open', 'closed', 'interrupted']),
})
export type SnapshotApplyEvent = z.infer<typeof SnapshotApplyEventSchema>

// ---------------------------------------------------------------------------
// Discriminated union
// ---------------------------------------------------------------------------

export const PariprashnaEventSchema = z.discriminatedUnion('type', [
  TurnOpenEventSchema,
  PhaseEventSchema,
  ActivityUpsertEventSchema,
  BlockOpenEventSchema,
  BlockDeltaEventSchema,
  BlockCommitEventSchema,
  SeamOpenEventSchema,
  SeamSetEventSchema,
  CitationDefineEventSchema,
  FlagEventSchema,
  GradeEventSchema,
  TurnCommitEventSchema,
  TurnCloseEventSchema,
  ErrorEventSchema,
  SnapshotApplyEventSchema,
])
export type PariprashnaEvent = z.infer<typeof PariprashnaEventSchema>

/** The set of SSE `event:` names this protocol uses. */
export const PARIPRASHNA_EVENT_TYPES = [
  'turn.open',
  'phase',
  'activity.upsert',
  'block.open',
  'block.delta',
  'block.commit',
  'seam.open',
  'seam.set',
  'citation.define',
  'flag',
  'grade',
  'turn.commit',
  'turn.close',
  'error',
  'snapshot.apply',
] as const
export type PariprashnaEventType = (typeof PARIPRASHNA_EVENT_TYPES)[number]

// ---------------------------------------------------------------------------
// Serialize / decode (isomorphic)
// ---------------------------------------------------------------------------

/**
 * Validate + serialize an event to a single SSE frame.
 * Throws if the event does not satisfy the schema — a fail-fast guard so a
 * malformed event can never reach the wire. Format:
 *
 *   event: <type>\n
 *   data: <json>\n
 *   \n
 */
export function serializeEvent(event: PariprashnaEvent): string {
  const parsed = PariprashnaEventSchema.parse(event)
  return `event: ${parsed.type}\ndata: ${JSON.stringify(parsed)}\n\n`
}

/**
 * Client-side decode of a raw `data:` JSON payload back into a typed event.
 * Returns `null` (never throws) on any validation failure, so a client render
 * loop can skip an unknown/garbled frame without crashing.
 */
export function decodeEvent(rawData: string): PariprashnaEvent | null {
  let json: unknown
  try {
    json = JSON.parse(rawData)
  } catch {
    return null
  }
  const result = PariprashnaEventSchema.safeParse(json)
  return result.success ? result.data : null
}
