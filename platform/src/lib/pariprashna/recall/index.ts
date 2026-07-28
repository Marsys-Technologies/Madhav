/**
 * pariprashna/recall — PB-2 (SMṚTI) lane M-4 ("pgvector recall") public API.
 *
 * Per-chart recall of prior conversation conclusions across OTHER threads of
 * the same chart, ranked by vector similarity + freshness, surfaced only as
 * `prior_reading`-graded citations (structurally the weakest grade — see
 * `../citations/floor_gate.ts`).
 *
 * Mirrors the M-1 store barrel's isomorphic/server-only split:
 *   Types + ranking + citation mapping (isomorphic — safe on client & server):
 *     RecallCandidate, RecallResult, RankOptions, rankRecallCandidates,
 *     toPriorReadingCitation(s).
 *
 *   DAL (server-only — pulls in the pg pool; NOT re-exported here):
 *     fetchCrossThreadCandidates  → import from '@/lib/pariprashna/recall/query'
 *     recallPriorConclusions      → import from '@/lib/pariprashna/recall/service'
 */

export * from './types'
export * from './rank'
export * from './citation'
