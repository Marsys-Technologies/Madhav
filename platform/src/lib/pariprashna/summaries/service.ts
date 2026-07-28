/**
 * Paripraśna durable conversation summaries — PB-2 (SMṚTI) lane M-3 — orchestration.
 *
 * The single entry point that decides "reuse the existing summary" vs. "a new
 * threshold has been crossed — render, summarize, and persist a new row."
 * Pure orchestration over injected `SummaryStore` / `SummarizerWorker`
 * dependencies (isomorphic, no direct DB/LLM import) so it is unit-testable
 * with in-memory fakes — the SAME contract a real Postgres-backed store /
 * LLM-backed worker present in production.
 *
 * Reuse-on-restart: a process restart has no in-memory state to lose — the
 * next call's `deps.store.findLatest()` reads the same persisted row a prior
 * process wrote, so the decision below ("threshold not yet crossed again ->
 * reuse") is identical before and after a restart. The unit test
 * (`__tests__/service.test.ts`) demonstrates this directly: two independent
 * calls against the same store state produce the same summary with the worker
 * invoked at most once.
 *
 * Carries `server-only` transitively: it imports `render.ts`, which resolves
 * tool reader-labels via the retrieval registry (a server-side catalog) — so
 * this module is not part of the plain isomorphic barrel (see index.ts);
 * import it directly.
 */
import 'server-only'

import {
  DEFAULT_SUMMARIZE_EVERY_N_MESSAGES,
  DEFAULT_VERBATIM_TAIL_MESSAGES,
  shouldSummarize,
} from './threshold'
import { appendCitationBlock, renderTurnsForSummary } from './render'
import type {
  CanonicalTurn,
  ConversationSummaryRow,
  SummarizerWorker,
  SummaryStore,
} from './types'

export interface GetOrCreateSummaryDeps {
  store: SummaryStore
  worker: SummarizerWorker
}

export interface GetOrCreateSummaryParams {
  conversationId: string
  /** ALL canonical turns for this conversation, oldest first. */
  turns: readonly CanonicalTurn[]
  everyN?: number
  verbatimTail?: number
}

export interface GetOrCreateSummaryResult {
  /** The summary to splice into context (existing reused, or freshly written);
   *  null if no summary exists yet AND the threshold has not been crossed. */
  summary: ConversationSummaryRow | null
  /** True only when THIS call wrote a brand-new row (i.e. called the worker). */
  created: boolean
}

/**
 * Decide + (if needed) perform one summarization pass for a conversation.
 *
 * Algorithm:
 *   1. Read the most recent existing summary (if any).
 *   2. Find turns strictly AFTER its `covers_through_message_id` (or all turns,
 *      if none exists yet).
 *   3. Reserve the last `verbatimTail` of those as never-summarized.
 *   4. If what remains is >= `everyN`, render + summarize + persist a NEW row
 *      covering through the last of those remaining turns.
 *   5. Otherwise, reuse whatever existed in step 1 (possibly null) — ZERO
 *      calls to `deps.worker.summarize()`.
 */
export async function getOrCreateSummary(
  deps: GetOrCreateSummaryDeps,
  params: GetOrCreateSummaryParams,
): Promise<GetOrCreateSummaryResult> {
  const {
    conversationId,
    turns,
    everyN = DEFAULT_SUMMARIZE_EVERY_N_MESSAGES,
    verbatimTail = DEFAULT_VERBATIM_TAIL_MESSAGES,
  } = params

  const existing = await deps.store.findLatest(conversationId)

  const coveredThroughIdx = existing
    ? turns.findIndex((t) => t.message_id === existing.covers_through_message_id)
    : -1
  const newTurnsSinceLastSummary = turns.slice(coveredThroughIdx + 1)

  const eligibleCount = Math.max(0, newTurnsSinceLastSummary.length - verbatimTail)
  const summarizableCandidates = newTurnsSinceLastSummary.slice(0, eligibleCount)

  if (!shouldSummarize({ eligibleNewMessageCount: summarizableCandidates.length }, everyN)) {
    // Cache hit — reuse whatever exists (possibly null). Zero worker calls.
    return { summary: existing, created: false }
  }

  const rendered = renderTurnsForSummary(summarizableCandidates, existing?.summary_text ?? null)
  const citationRefs = rendered.citations.map((c) => c.signal_id)

  const llmProse = await deps.worker.summarize({
    conversationId,
    renderedText: rendered.text,
    citationRefs,
  })
  const summaryText = appendCitationBlock(llmProse, rendered.citations)

  const newCoversThroughId = summarizableCandidates[summarizableCandidates.length - 1].message_id
  const row = await deps.store.insert({
    conversation_id: conversationId,
    covers_through_message_id: newCoversThroughId,
    summary_text: summaryText,
    model_id: deps.worker.lastModelId?.() ?? null,
  })

  return { summary: row, created: true }
}
