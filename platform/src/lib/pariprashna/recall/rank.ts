/**
 * recall/rank.ts — PB-2 (SMṚTI) lane M-4.
 *
 * Pure ranking function over `RecallCandidate[]`: combines vector similarity
 * with a freshness signal into one composite score. No DB, no I/O — the DAL
 * half (`query.ts`) fetches candidates; this module only orders them. Kept
 * pure and injectable-clock so it is deterministically unit-testable (see
 * `tests/pariprashna/recall/rank.test.ts`).
 */
import type { RankOptions, RecallCandidate, RecallResult } from './types'

const DEFAULT_LIMIT = 5
const DEFAULT_SIMILARITY_WEIGHT = 0.7
const DEFAULT_FRESHNESS_WEIGHT = 0.3

/**
 * Recency-fallback half-life, in days: a candidate this old scores 0.5 on the
 * naive fallback freshness proxy used ONLY when no `freshnessOf` signal is
 * supplied. This is a placeholder curve, not a provenance model — see the
 * `FreshnessLookup` doc in `types.ts` for the lane M-6 dependency this stands
 * in for. Exported so tests/consumers can reason about the exact curve.
 */
export const RECENCY_FALLBACK_HALF_LIFE_DAYS = 90

const MS_PER_DAY = 86_400_000

/** Naive recency-as-freshness proxy: exponential decay, 1.0 at age 0, 0.5 at the half-life. */
export function recencyFallbackFreshness(createdAt: string, now: Date): number {
  const ageMs = Math.max(0, now.getTime() - new Date(createdAt).getTime())
  const ageDays = ageMs / MS_PER_DAY
  return Math.pow(0.5, ageDays / RECENCY_FALLBACK_HALF_LIFE_DAYS)
}

/**
 * Rank recall candidates by a composite (similarity, freshness) score and
 * return the top `limit`. Freshness prefers an injected `freshnessOf` signal
 * (the M-6 provenance-stamp seam) and falls back to `recencyFallbackFreshness`
 * only when that callback is absent or returns `undefined` for a candidate —
 * so the ranking SHAPE never changes when M-6 lands, only the freshness input.
 */
export function rankRecallCandidates(
  candidates: readonly RecallCandidate[],
  opts: RankOptions = {},
): RecallResult[] {
  const similarityWeight = opts.similarityWeight ?? DEFAULT_SIMILARITY_WEIGHT
  const freshnessWeight = opts.freshnessWeight ?? DEFAULT_FRESHNESS_WEIGHT
  const limit = opts.limit ?? DEFAULT_LIMIT
  const now = opts.now ?? new Date()

  const scored: RecallResult[] = candidates.map((candidate) => {
    const external = opts.freshnessOf?.(candidate)
    const usingExternal = external !== undefined
    const freshness = usingExternal ? external : recencyFallbackFreshness(candidate.created_at, now)
    return {
      ...candidate,
      freshness,
      freshness_source: usingExternal ? 'provenance_stamp' : 'recency_fallback',
      score: similarityWeight * candidate.similarity + freshnessWeight * freshness,
    }
  })

  scored.sort((a, b) => b.score - a.score)
  return scored.slice(0, limit)
}
