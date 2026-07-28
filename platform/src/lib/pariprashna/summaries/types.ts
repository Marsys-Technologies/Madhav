/**
 * Paripraśna durable conversation summaries — PB-2 (SMṚTI) lane M-3 — shared types.
 *
 * ISOMORPHIC on purpose (pure types, no `server-only`, no `pg`) — mirrors the
 * discipline M-1's `store/schema.ts` set: the pure shapes live here so
 * render.ts / threshold.ts / service.ts can all import them without dragging
 * in a DB connection, and so tests can exercise the decision logic against a
 * fake `SummaryStore` / `SummarizerWorker` with zero DB dependency.
 */

import type { PersistedMessagePart } from '../store/schema'

/** A canonical message + its ordered parts, as read via M-1's `readTurnParts`. */
export interface CanonicalTurn {
  message_id: string
  role: 'user' | 'assistant' | 'tool'
  parts: PersistedMessagePart[]
}

/** A persisted `conversation_summaries` row (mirrors migration 468). */
export interface ConversationSummaryRow {
  id: string
  conversation_id: string
  covers_through_message_id: string
  summary_text: string
  model_id: string | null
  created_at: string
}

/** The fields the store writes; `id`/`created_at` are DB-assigned. */
export interface ConversationSummaryInsert {
  conversation_id: string
  covers_through_message_id: string
  summary_text: string
  model_id: string | null
}

/**
 * The persistence seam for `conversation_summaries`. An interface (not a
 * concrete class import) so `service.ts`'s decision logic can be unit-tested
 * against an in-memory fake — the SAME contract a real Postgres restart would
 * present (a restart is just a fresh `findLatest` read; there is no in-memory
 * state to lose either way).
 */
export interface SummaryStore {
  /** The most recently written summary for this conversation, or null if none exists yet. */
  findLatest(conversationId: string): Promise<ConversationSummaryRow | null>
  /** Append a new summary row. Never updates/deletes — see migration 468's comment. */
  insert(row: ConversationSummaryInsert): Promise<ConversationSummaryRow>
}

/** Input handed to a `SummarizerWorker.summarize()` call. */
export interface SummarizeInput {
  conversationId: string
  /** The rendered, human-readable text of the turns being folded into a summary
   *  (see render.ts `renderTurnsForSummary`) — tool activity already rendered
   *  as "consulted ⟨label⟩ → ⟨result⟩" lines, never raw internal names. */
  renderedText: string
  /** Citation signal ids present in the summarized range — informational for
   *  the worker (it MAY reference them in prose); VERBATIM survival is
   *  guaranteed independently by `appendCitationBlock`, not by worker behavior. */
  citationRefs: readonly string[]
}

/**
 * A family-worker interface: one provider-backed implementation today
 * (`LlmSummarizerWorker`, worker.ts), designed so a future second
 * implementation (a different model family / a non-LLM extractive summarizer)
 * can be swapped in behind the same call shape.
 */
export interface SummarizerWorker {
  summarize(input: SummarizeInput): Promise<string>
  /** The model id the worker used for its most recent call, if it tracks one —
   *  read by the caller to stamp `conversation_summaries.model_id`. Optional so
   *  a non-LLM future implementation isn't forced to fabricate one. */
  lastModelId?(): string | null
}
