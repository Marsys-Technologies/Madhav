/**
 * Paripraśna canonical message-parts schema — PB-2 (SMṚTI) lane M-1.
 *
 * SINGLE SOURCE OF TRUTH for the shape of a persisted `message_parts` row's
 * `body` per `kind`. Backs migration 467
 * (supabase/migrations/467_pariprashna_canonical_message_parts.sql): the DB
 * enforces the closed `kind` enum via a CHECK constraint; this module enforces
 * the per-kind `body` shape via Zod so nothing malformed can be written or read.
 *
 * This module is ISOMORPHIC on purpose — pure Zod + pure types, no `server-only`,
 * no `pg`, no Node imports — so the serializer (serialize.ts) and both the writer
 * and reader (writer.ts / reader.ts) share exactly these definitions, and PB-2's
 * next lane (M-2, the byte-equality gate) can import the kind vocabulary without
 * dragging in a DB connection.
 *
 * Derivation discipline (matches CLAUDE.md B.3 spirit): where a part derives
 * directly from a wire event in
 * `platform/src/lib/pariprashna/protocol/events.ts`, its body field names MIRROR
 * that event's payload fields (minus the transport envelope `type`/`seq`/`t`).
 * Each kind's schema documents which wire event it derives from, or notes it is
 * M-1-defined where the protocol carries no corresponding event yet.
 */

import { z } from 'zod'

// ---------------------------------------------------------------------------
// Closed kind enum — MUST stay in lockstep with migration 467's CHECK constraint.
// ---------------------------------------------------------------------------

export const MESSAGE_PART_KINDS = [
  'text',
  'reasoning',
  'tool_call',
  'tool_result',
  'citation',
  'prediction_candidate',
  'attachment',
] as const

export const MessagePartKindSchema = z.enum(MESSAGE_PART_KINDS)
export type MessagePartKind = z.infer<typeof MessagePartKindSchema>

// ---------------------------------------------------------------------------
// Per-kind body schemas
// ---------------------------------------------------------------------------

/**
 * `text` — reader-visible prose. Derives from a `block.commit` event whose
 * originating `block.open` had `role: 'prose'` (events.ts BlockCommitEvent →
 * `{ block_id, text }`). `block_id` is retained so a persisted part can be
 * traced back to its stream block; it is optional because non-streamed callers
 * (tests, backfill of a synthesized message) may not carry one.
 */
export const TextBodySchema = z
  .object({
    text: z.string(),
    block_id: z.string().optional(),
  })
  .strict()
export type TextBody = z.infer<typeof TextBodySchema>

/**
 * `reasoning` — model thinking / provider reasoning. Derives from a
 * `block.commit` event whose block `role` was `'thinking'`, plus provider
 * reasoning metadata. Shape is fixed by the M-1 contract:
 *   { text, signature?, provider_opaque? }
 * `provider_opaque` is a storable-but-never-replayed-cross-provider blob
 * (opaque reasoning tokens / redacted content): it round-trips through the DB
 * but the serializer treats it as inert data, never as replayable prose.
 */
export const ReasoningBodySchema = z
  .object({
    text: z.string(),
    signature: z.string().optional(),
    provider_opaque: z.string().optional(),
    block_id: z.string().optional(),
  })
  .strict()
export type ReasoningBody = z.infer<typeof ReasoningBodySchema>

/**
 * `tool_call` — an agentic-loop tool invocation. Shape fixed by the M-1
 * contract:
 *   { call_id, tool_name, args, envelope_ref? }
 * `tool_name` is the CANONICAL / human-safe tool name (the same reader-safe
 * name the wire surfaces on `activity.upsert`) — NEVER a raw provider
 * function-call frame name. `args` is the (already reader-safe) argument object.
 * `envelope_ref` optionally points at the audit-channel envelope holding the
 * raw provider frame, which is kept server-side and out of the canonical body.
 */
export const ToolCallBodySchema = z
  .object({
    call_id: z.string(),
    tool_name: z.string(),
    args: z.record(z.string(), z.unknown()),
    envelope_ref: z.string().optional(),
  })
  .strict()
export type ToolCallBody = z.infer<typeof ToolCallBodySchema>

/**
 * `tool_result` — the terminal outcome of a `tool_call`. Field names mirror the
 * `activity.upsert` wire event (events.ts ActivityUpsertEvent →
 * `{ status, detail?, count?, ms? }`) that reports a tool activity's completion,
 * narrowed to the terminal statuses, plus `call_id` linking it back to its
 * `tool_call` part and an optional `envelope_ref` to the audit-channel payload.
 * `result` carries the reader-safe structured output when one is surfaced.
 */
export const ToolResultBodySchema = z
  .object({
    call_id: z.string(),
    status: z.enum(['done', 'error']),
    detail: z.string().optional(),
    count: z.number().int().nonnegative().optional(),
    ms: z.number().int().nonnegative().optional(),
    result: z.unknown().optional(),
    envelope_ref: z.string().optional(),
  })
  .strict()
export type ToolResultBody = z.infer<typeof ToolResultBodySchema>

/**
 * `citation` — a citation the prose references. Derives DIRECTLY from the
 * `citation.define` wire event (events.ts CitationDefineEvent); body carries
 * exactly what that event carries minus the transport envelope:
 *   { index, signal_id, layer, snippet, reader_label?, grade? }
 * Audit-channel internals (source table, fact ids) are deliberately NOT carried
 * here — they stay server-side, matching the wire event's own discipline.
 */
export const CitationBodySchema = z
  .object({
    index: z.number().int(),
    signal_id: z.string(),
    layer: z.string(),
    snippet: z.string(),
    reader_label: z.string().optional(),
    grade: z.string().optional(),
  })
  .strict()
export type CitationBody = z.infer<typeof CitationBodySchema>

/**
 * `prediction_candidate` — a falsifiable prediction surfaced by the turn. The
 * wire protocol has no dedicated prediction event (a candidate is hinted via a
 * `flag`), so this body is M-1-DEFINED rather than wire-derived. Its fields
 * mirror the live prospective-ledger contract (migration 458
 * brahma_prospective_ledger): a claim, an optional window/confidence, and a
 * MANDATORY-in-spirit falsifier. `source_flag_code` optionally records the
 * `flag.code` that surfaced the candidate on the stream. Kept intentionally
 * lean here; PB-2 downstream lanes own promoting a candidate into the ledger.
 */
export const PredictionCandidateBodySchema = z
  .object({
    claim: z.string(),
    window: z.string().optional(),
    confidence: z.number().min(0).max(1).optional(),
    falsifier: z.string().optional(),
    source_flag_code: z.string().optional(),
  })
  .strict()
export type PredictionCandidateBody = z.infer<typeof PredictionCandidateBodySchema>

/**
 * `attachment` — a non-prose attachment (image, file, generated asset). No wire
 * event carries one today, so this body is M-1-DEFINED. `media_type` (IANA type)
 * is required; the payload is referenced by `url` or an out-of-band
 * `attachment_id` / `envelope_ref` rather than inlined, keeping the canonical
 * body small and deterministic.
 */
export const AttachmentBodySchema = z
  .object({
    media_type: z.string(),
    attachment_id: z.string().optional(),
    filename: z.string().optional(),
    url: z.string().optional(),
    bytes: z.number().int().nonnegative().optional(),
    envelope_ref: z.string().optional(),
  })
  .strict()
export type AttachmentBody = z.infer<typeof AttachmentBodySchema>

// ---------------------------------------------------------------------------
// Kind → body registry + discriminated validation
// ---------------------------------------------------------------------------

/** Map from kind literal to its body Zod schema. */
export const BODY_SCHEMA_BY_KIND = {
  text: TextBodySchema,
  reasoning: ReasoningBodySchema,
  tool_call: ToolCallBodySchema,
  tool_result: ToolResultBodySchema,
  citation: CitationBodySchema,
  prediction_candidate: PredictionCandidateBodySchema,
  attachment: AttachmentBodySchema,
} as const satisfies Record<MessagePartKind, z.ZodType>

/**
 * A validated (kind, body) pair as a discriminated union. Each member pins
 * `kind` to a literal and `body` to that kind's schema, so `parse` both checks
 * the body shape AND narrows the TS type by `kind`.
 */
export const MessagePartContentSchema = z.discriminatedUnion('kind', [
  z.object({ kind: z.literal('text'), body: TextBodySchema }),
  z.object({ kind: z.literal('reasoning'), body: ReasoningBodySchema }),
  z.object({ kind: z.literal('tool_call'), body: ToolCallBodySchema }),
  z.object({ kind: z.literal('tool_result'), body: ToolResultBodySchema }),
  z.object({ kind: z.literal('citation'), body: CitationBodySchema }),
  z.object({ kind: z.literal('prediction_candidate'), body: PredictionCandidateBodySchema }),
  z.object({ kind: z.literal('attachment'), body: AttachmentBodySchema }),
])
export type MessagePartContent = z.infer<typeof MessagePartContentSchema>

/**
 * Validate a raw (kind, body) pair against the correct per-kind schema.
 * Throws (via Zod) if `kind` is not a member of the closed enum or if `body`
 * does not satisfy that kind's shape. Returns the narrowed, parsed content.
 */
export function parsePartContent(kind: string, body: unknown): MessagePartContent {
  return MessagePartContentSchema.parse({ kind, body })
}

// ---------------------------------------------------------------------------
// Row-level shapes (writer input / reader output)
// ---------------------------------------------------------------------------

/** Roles allowed on conversation_messages (mirrors the DB role CHECK). */
export const MessageRoleSchema = z.enum(['user', 'assistant', 'tool'])
export type MessageRole = z.infer<typeof MessageRoleSchema>

/**
 * A UUID string as Postgres's `uuid` type accepts it: any 8-4-4-4-12 hex layout.
 * Deliberately NOT `z.uuid()` — Zod 4's uuid validator enforces RFC 4122
 * version/variant bits, which is STRICTER than the DB column (Postgres accepts
 * any hex in the canonical layout). Gating stricter than the storage engine
 * would reject ids the DB would happily store, so we mirror the DB's leniency.
 */
const UUID_RE = /^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/
export const UuidLikeSchema = z.string().regex(UUID_RE, 'must be an 8-4-4-4-12 hex UUID')

/**
 * The conversation_messages row the canonical writer inserts. `id` and
 * `conversation_id` are caller-supplied (the turn already owns them: `turn.open`
 * carries `turn_id` + `conversation_id`, `turn.commit` carries `message_id`).
 * `schema_version`, `model_id`, `provider` are the additive columns migration
 * 467 adds — always set on a canonical row (never NULL, unlike legacy rows).
 */
export const CanonicalMessageSchema = z
  .object({
    id: UuidLikeSchema,
    conversation_id: UuidLikeSchema,
    role: MessageRoleSchema,
    schema_version: z.number().int().positive(),
    model_id: z.string(),
    provider: z.string(),
    /** Optional turn/metadata blob written to metadata_json; NOT part of the
     *  canonical serialization (see serialize.ts). Defaults to {} when omitted. */
    metadata: z.record(z.string(), z.unknown()).optional(),
    parent_message_id: UuidLikeSchema.optional(),
  })
  .strict()
export type CanonicalMessage = z.infer<typeof CanonicalMessageSchema>

/** The current canonical schema version stamped on every M-1 message row. */
export const CANONICAL_SCHEMA_VERSION = 1

/**
 * Declared compatibility (P2-D, PPR-10 versioning clause). The oldest
 * `schema_version` a reader in THIS build is willing to interpret. Equal to
 * `CANONICAL_SCHEMA_VERSION` today (v1 is the only version ever written); a
 * future writer bump that keeps the reader able to serve v1 rows (e.g. a
 * purely-additive body field) would lower this floor rather than raise it —
 * raising it without a migrated backfill would make old rows unreadable.
 */
export const MIN_SUPPORTED_CANONICAL_SCHEMA_VERSION = 1

/**
 * True iff a row's `schema_version` is one this build declares it can read.
 * A reader that encounters `false` here has a real, actionable signal — "this
 * row was written by a schema version I do not speak" — rather than silently
 * misinterpreting an old or a too-new row shape. Never used to gate WRITES
 * (a writer always stamps `CANONICAL_SCHEMA_VERSION` — see writer.ts); this is
 * a read-path compatibility check only.
 */
export function isCanonicalSchemaVersionSupported(v: number): boolean {
  return Number.isInteger(v) && v >= MIN_SUPPORTED_CANONICAL_SCHEMA_VERSION && v <= CANONICAL_SCHEMA_VERSION
}

/**
 * A part as supplied to the writer (pre-persist): the caller provides `seq`,
 * `kind`, `body`, and `model_visible`. `id`/`message_id`/`created_at` are
 * assigned by the DB. `body` is validated against the per-kind schema at write
 * time via `parsePartContent`.
 */
export const MessagePartInputSchema = z
  .object({
    seq: z.number().int().nonnegative(),
    kind: MessagePartKindSchema,
    body: z.unknown(),
    model_visible: z.boolean(),
  })
  .strict()
export type MessagePartInput = z.infer<typeof MessagePartInputSchema>

/** A part as read back from the DB (persisted): includes DB-assigned fields. */
export interface PersistedMessagePart {
  id: string
  message_id: string
  seq: number
  kind: MessagePartKind
  body: unknown
  model_visible: boolean
  created_at: string
}
