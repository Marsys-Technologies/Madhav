/**
 * Paripraśna wire protocol — canonical event schema (DRAFT).
 *
 * Lane: PB-1 / C-2 (the harness). Owner-of-record: S-1 (protocol/route lane).
 *
 * Why this file exists: S-1's real SSE event schema does not exist yet, but the
 * C-2 acceptance harness (replay server, fixtures, gates, reducer) needs a wire
 * shape to build against *today*. This module is that shape — a reasonable,
 * minimal, well-documented guess at what a Paripraśna turn's SSE stream looks
 * like. S-1 is expected to ADOPT, RENAME, or REPLACE this file wholesale; treat
 * everything here as a proposal frozen just long enough to unblock the harness,
 * not as a contract C-2 is entitled to defend.
 *
 * Design intent (matches the brief's no-layout-shift / no-transmutation goals):
 *  - A turn is a sequence of "blocks" (paragraphs, tables, lists, code, etc).
 *    Each block is opened once, receives zero or more deltas (streamed text),
 *    and is committed exactly once. Once committed, a block's rendered DOM
 *    must never change shape again (G-TRANSMUTE) — no delta or seam event may
 *    target a committed block.
 *  - "Activities" (tool calls, retrieval passes, reasoning steps) are reported
 *    out-of-band from block content via `activity.upsert`, keyed so repeated
 *    upserts to the same key update in place rather than appending duplicate
 *    rows (e.g. a retrieval pass going pending -> done).
 *  - "Seams" are inline citation/annotation anchors inside a block's text that
 *    get bound to a citation definition (`citation.define`) — this lets a
 *    citation chip's *content* stream in after the seam position is already
 *    fixed in the committed text, without moving surrounding prose.
 *  - Every event carries a monotonic-per-turn `seq`. Consumers (the reducer)
 *    MUST drop events whose `id` has already been applied — the wire is
 *    allowed to redeliver (reconnect-and-replay, at-least-once relays), and
 *    idempotent dedup on `id` is what makes that safe.
 *
 * Non-goals of this draft:
 *  - Auth/session framing, transport envelope (SSE `data:` line wrapping),
 *    backpressure/credits — those are S-1's route-layer concerns.
 *  - Any real lexicon/citation content shape — that's S-2/S-3.
 */
import { z } from 'zod'

// ─── Shared primitives ──────────────────────────────────────────────────────

/** Every event on the wire carries a globally-unique-per-turn id for dedup. */
const EventBase = z.object({
  /** Unique per (turn_id, id) — the reducer's dedup key. Redelivery-safe. */
  id: z.string().min(1),
  /** Monotonic sequence number within the turn. Ties broken by arrival order. */
  seq: z.number().int().nonnegative(),
  /** Wall-clock ms since epoch, for latency/stall diagnostics only — never
   *  used for ordering (that's `seq`'s job). */
  t: z.number().int().nonnegative(),
})

const BlockKind = z.enum([
  'paragraph',
  'heading',
  'list',
  'table',
  'code',
  'blockquote',
  'divider',
])

// ─── turn.open / turn.commit / turn.close ──────────────────────────────────

const TurnOpenEvent = EventBase.extend({
  type: z.literal('turn.open'),
  turn_id: z.string().min(1),
  /** Reading-depth contract this turn was planned under (retrieval | standard
   *  | deep_dive | exhaustive) — informational for the client, drives nothing
   *  client-side. */
  reading_depth: z.string().optional(),
})

/** Emitted once, after the last block of the turn commits, before turn.close.
 *  Carries turn-level judgment/summary metadata — never prose content. */
const TurnCommitEvent = EventBase.extend({
  type: z.literal('turn.commit'),
  turn_id: z.string().min(1),
  block_count: z.number().int().nonnegative(),
  citation_count: z.number().int().nonnegative(),
})

const TurnCloseEvent = EventBase.extend({
  type: z.literal('turn.close'),
  turn_id: z.string().min(1),
  reason: z.enum(['complete', 'stopped', 'error']),
})

// ─── phase ──────────────────────────────────────────────────────────────────

/** Coarse "what is the assistant doing right now" signal — drives the header
 *  status line, not block content. Never mutates a committed block. */
const PhaseEvent = EventBase.extend({
  type: z.literal('phase'),
  phase: z.enum(['planning', 'retrieving', 'synthesizing', 'grading', 'done']),
  label: z.string().optional(),
})

// ─── activity.upsert ────────────────────────────────────────────────────────

/**
 * Keyed upsert for out-of-band activity rows (tool calls, retrieval passes,
 * reasoning steps). Same `key` + same `pass_id` = update-in-place, not a new
 * row — this is what lets a client render a coalesced "3 passes" tracker
 * instead of an ever-growing log.
 */
const ActivityUpsertEvent = EventBase.extend({
  type: z.literal('activity.upsert'),
  /** Stable identity for this activity row across repeated upserts. */
  key: z.string().min(1),
  /** Which retrieval/reasoning pass this activity belongs to (adaptive-N-pass
   *  fixtures rely on this to group rows under "Pass 1", "Pass 2", ...). */
  pass_id: z.string().min(1),
  /** Human-facing label key — a lexicon key (S-2 owns resolution), not raw
   *  prose, so translation/tone stays centralized. */
  label_key: z.string().min(1),
  status: z.enum(['pending', 'active', 'done', 'skipped', 'error']),
  /** Optional short detail string (e.g. tool name, row count). */
  detail: z.string().optional(),
})

// ─── block.open / block.delta / block.commit ───────────────────────────────

const BlockOpenEvent = EventBase.extend({
  type: z.literal('block.open'),
  block_id: z.string().min(1),
  kind: BlockKind,
  /** Ordinal position within the turn — blocks commit in non-decreasing
   *  order of `index`. */
  index: z.number().int().nonnegative(),
})

/** Appends text to an OPEN block. A delta targeting a block that has already
 *  committed is a protocol violation (G-TRANSMUTE's core invariant) and the
 *  reference reducer throws rather than silently accepting it. */
const BlockDeltaEvent = EventBase.extend({
  type: z.literal('block.delta'),
  block_id: z.string().min(1),
  /** Raw text/markdown fragment to append. */
  text: z.string(),
})

/** Closes a block permanently. Once committed, the block's serialized DOM
 *  must be byte-identical at every later render (G-TRANSMUTE). */
const BlockCommitEvent = EventBase.extend({
  type: z.literal('block.commit'),
  block_id: z.string().min(1),
  /** Final full text of the block, for reducer-side consistency checks
   *  against the accumulated delta stream (should equal the concatenation
   *  of all prior deltas for this block_id — a mismatch is a protocol bug). */
  final_text: z.string(),
})

// ─── seam.open / seam.set ───────────────────────────────────────────────────

/**
 * A "seam" is an inline anchor inside a block's text (typically a citation
 * marker) whose final resolved content is not yet known when the block
 * commits. `seam.open` reserves the position; `seam.set` fills it in later
 * (e.g. once S-3's citation-verification pass completes). A seam MAY still
 * be set after its parent block has committed — that is the one sanctioned
 * exception to "committed blocks never change", and it is restricted to a
 * single well-defined inline span (never a layout-affecting reflow).
 */
const SeamOpenEvent = EventBase.extend({
  type: z.literal('seam.open'),
  seam_id: z.string().min(1),
  block_id: z.string().min(1),
  /** Character offset within the block's committed text where the seam
   *  anchors — fixed at open time, never moves. */
  anchor_offset: z.number().int().nonnegative(),
})

const SeamSetEvent = EventBase.extend({
  type: z.literal('seam.set'),
  seam_id: z.string().min(1),
  /** Reference to a citation.define event's `citation_id`, or null if the
   *  seam resolved to "no citation available" (an honest gap, not silence). */
  citation_id: z.string().nullable(),
})

// ─── citation.define ────────────────────────────────────────────────────────

const CitationDefineEvent = EventBase.extend({
  type: z.literal('citation.define'),
  citation_id: z.string().min(1),
  /** Short display label for the citation chip (e.g. "BPHS 6.12"). */
  label: z.string().min(1),
  /** Verification tier — mirrors the CLAUDE.md §N.6 density discipline:
   *  a citation must never be presented as confirmed until cross-verified. */
  verification: z.enum(['confirmed', 'catalog_only']),
  source_ref: z.string().optional(),
})

// ─── flag ───────────────────────────────────────────────────────────────────

/** Out-of-band, non-content signal — contradictions, honest gaps, escalation
 *  valves (RS-4 B.11 carve-out). Never rendered as prose inline. */
const FlagEvent = EventBase.extend({
  type: z.literal('flag'),
  flag_key: z.string().min(1),
  severity: z.enum(['info', 'notice', 'warning']),
  detail: z.string().optional(),
})

// ─── grade ──────────────────────────────────────────────────────────────────

/** Calibration/confidence grade for the turn or a specific block — structural
 *  metadata, never fabricated prose (B.10). */
const GradeEvent = EventBase.extend({
  type: z.literal('grade'),
  target_block_id: z.string().nullable(),
  score: z.number().min(0).max(1),
  basis: z.string().optional(),
})

// ─── error ──────────────────────────────────────────────────────────────────

const ErrorEvent = EventBase.extend({
  type: z.literal('error'),
  code: z.string().min(1),
  message: z.string().min(1),
  /** Whether the client should treat this as terminal (stream will not
   *  continue) or recoverable (a retry may follow). */
  fatal: z.boolean(),
})

// ─── discriminated union + exports ──────────────────────────────────────────

export const PariprashnaEvent = z.discriminatedUnion('type', [
  TurnOpenEvent,
  PhaseEvent,
  ActivityUpsertEvent,
  BlockOpenEvent,
  BlockDeltaEvent,
  BlockCommitEvent,
  SeamOpenEvent,
  SeamSetEvent,
  CitationDefineEvent,
  FlagEvent,
  GradeEvent,
  TurnCommitEvent,
  TurnCloseEvent,
  ErrorEvent,
])

export type PariprashnaEventT = z.infer<typeof PariprashnaEvent>

export type TurnOpenEventT = z.infer<typeof TurnOpenEvent>
export type PhaseEventT = z.infer<typeof PhaseEvent>
export type ActivityUpsertEventT = z.infer<typeof ActivityUpsertEvent>
export type BlockOpenEventT = z.infer<typeof BlockOpenEvent>
export type BlockDeltaEventT = z.infer<typeof BlockDeltaEvent>
export type BlockCommitEventT = z.infer<typeof BlockCommitEvent>
export type SeamOpenEventT = z.infer<typeof SeamOpenEvent>
export type SeamSetEventT = z.infer<typeof SeamSetEvent>
export type CitationDefineEventT = z.infer<typeof CitationDefineEvent>
export type FlagEventT = z.infer<typeof FlagEvent>
export type GradeEventT = z.infer<typeof GradeEvent>
export type TurnCommitEventT = z.infer<typeof TurnCommitEvent>
export type TurnCloseEventT = z.infer<typeof TurnCloseEvent>
export type ErrorEventT = z.infer<typeof ErrorEvent>

export type EventType = PariprashnaEventT['type']

/** Parse+validate a single decoded SSE `data:` payload (already JSON.parsed)
 *  against the canonical schema. Throws a ZodError on malformed events — the
 *  malformed-sentinel-variants fixture exists precisely to exercise this. */
export function parseEvent(raw: unknown): PariprashnaEventT {
  return PariprashnaEvent.parse(raw)
}

/** Non-throwing variant — returns a discriminated result instead. Prefer this
 *  in the replay client / reducer, which need to keep streaming past a single
 *  malformed frame rather than crash the whole turn. */
export function safeParseEvent(raw: unknown): ReturnType<typeof PariprashnaEvent.safeParse> {
  return PariprashnaEvent.safeParse(raw)
}
