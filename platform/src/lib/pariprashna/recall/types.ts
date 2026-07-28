/**
 * recall/types.ts — PB-2 (SMṚTI) lane M-4 ("pgvector recall").
 *
 * Types for per-chart, cross-thread recall: given a chart and a query, find
 * the most relevant PRIOR conversation conclusions from OTHER threads of the
 * SAME chart, ranked by vector similarity + a freshness signal. Isomorphic —
 * no `pg`, no `server-only` — so `rank.ts` is unit-testable with plain
 * fixtures (see `tests/pariprashna/recall/rank.test.ts`).
 */

/** What the caller asks recall for. */
export interface RecallQueryInput {
  readonly chartId: string
  /** Exclude this conversation (normally the CURRENT thread) from candidates. */
  readonly excludeConversationId?: string
  /** Caller-computed query embedding (768-dim, matches `conversation_message_embeddings`). */
  readonly queryEmbedding: readonly number[]
  /** Over-fetch cap for the DB candidate query; final result count is `RankOptions.limit`. */
  readonly candidateLimit?: number
}

/** One embedded prior message, before ranking. */
export interface RecallCandidate {
  readonly message_id: string
  readonly conversation_id: string
  readonly conversation_title: string | null
  /** ISO timestamp of the source message (the recalled turn's own `created_at`). */
  readonly created_at: string
  /** Extracted text/reasoning content — the "prior conclusion" itself. */
  readonly content: string
  /** Cosine similarity in [0,1] (`1 - cosine_distance`; not clamped for out-of-range embeddings). */
  readonly similarity: number
}

/**
 * Optional external freshness signal for one candidate, in [0,1] (1 = most
 * fresh/current). PB-2 dependency note: as of lane M-4, no turn/message in
 * this codebase carries a genuine PROVENANCE STAMP (a fact-recency /
 * dasha-window marker distinguishing "this conclusion is still live" from
 * "this conclusion has since been superseded") — that is lane M-6's
 * responsibility. `rankRecallCandidates` therefore accepts this as an
 * INJECTABLE parameter rather than hardcoding today's absence: pass a
 * `freshnessOf` callback once M-6 exposes a real stamp, and the ranking
 * formula does not need to change shape, only its freshness INPUT.
 */
export type FreshnessLookup = (candidate: RecallCandidate) => number | undefined

export interface RankOptions {
  /** Final result count after ranking (default 5). */
  readonly limit?: number
  /** Weight on similarity in the composite score (default 0.7). */
  readonly similarityWeight?: number
  /** Weight on freshness in the composite score (default 0.3). */
  readonly freshnessWeight?: number
  /**
   * M-6 dependency seam: supply a real provenance-freshness signal per
   * candidate. When omitted (today's reality — no stamp exists yet), ranking
   * falls back to a naive recency-of-created_at proxy (see `rank.ts`) — an
   * honest placeholder, not a provenance stamp.
   */
  readonly freshnessOf?: FreshnessLookup
  /** Injectable clock for deterministic tests; defaults to `new Date()`. */
  readonly now?: Date
}

export type FreshnessSource = 'provenance_stamp' | 'recency_fallback'

/** A ranked candidate, ready to be surfaced (via `citation.ts`) as a `prior_reading` citation. */
export interface RecallResult extends RecallCandidate {
  /** The freshness value actually used (external signal if supplied, else the recency fallback). */
  readonly freshness: number
  /** Which source produced `freshness` — `provenance_stamp` once M-6 lands, `recency_fallback` today. */
  readonly freshness_source: FreshnessSource
  /** Composite ranking score = similarityWeight*similarity + freshnessWeight*freshness. */
  readonly score: number
}
