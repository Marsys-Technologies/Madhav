/**
 * recall/rank.test.ts — PB-2 (SMṚTI) lane M-4.
 *
 * Fixture-based proof of cross-thread recall: given several candidate
 * messages recalled from OTHER threads of the same chart, `rankRecallCandidates`
 * (a) returns the most-similar prior conclusion, (b) breaks near-ties toward
 * the fresher candidate, and (c) lets an injected M-6-style provenance signal
 * override the naive recency fallback without changing the ranking's shape.
 */
import { describe, expect, it } from 'vitest'
import {
  RECENCY_FALLBACK_HALF_LIFE_DAYS,
  rankRecallCandidates,
  recencyFallbackFreshness,
} from '@/lib/pariprashna/recall/rank'
import type { RecallCandidate } from '@/lib/pariprashna/recall/types'

const NOW = new Date('2026-07-28T00:00:00.000Z')

function candidate(overrides: Partial<RecallCandidate>): RecallCandidate {
  return {
    message_id: 'msg-default',
    conversation_id: 'conv-default',
    conversation_title: null,
    created_at: NOW.toISOString(),
    content: 'default content',
    similarity: 0.5,
    ...overrides,
  }
}

describe('rankRecallCandidates — cross-thread recall fixture', () => {
  it('returns the prior conclusion from an OTHER thread, ranked above a weaker match', () => {
    const otherThreadStrongMatch = candidate({
      message_id: 'msg-strong',
      conversation_id: 'conv-marriage-2026-01',
      conversation_title: 'Marriage timing — Jan 2026',
      created_at: '2026-06-01T00:00:00.000Z',
      content: 'Jupiter dasha favors marriage timing in the Oct 2026 – Mar 2027 window.',
      similarity: 0.93,
    })
    const otherThreadWeakMatch = candidate({
      message_id: 'msg-weak',
      conversation_id: 'conv-career-2025-11',
      conversation_title: 'Career pivot — Nov 2025',
      created_at: '2025-11-01T00:00:00.000Z',
      content: 'Saturn transit suggests a career pivot is well-supported.',
      similarity: 0.41,
    })

    const ranked = rankRecallCandidates([otherThreadWeakMatch, otherThreadStrongMatch], { now: NOW })

    expect(ranked).toHaveLength(2)
    expect(ranked[0].message_id).toBe('msg-strong')
    expect(ranked[0].conversation_id).not.toBe('conv-current-thread') // sanity: never the current thread
    expect(ranked[0].score).toBeGreaterThan(ranked[1].score)
  })

  it('excludes nothing itself (exclusion is the DAL\'s job) but ranks purely on score', () => {
    const a = candidate({ message_id: 'a', similarity: 0.6, created_at: NOW.toISOString() })
    const b = candidate({ message_id: 'b', similarity: 0.6, created_at: new Date(NOW.getTime() - 365 * 86_400_000).toISOString() })

    const ranked = rankRecallCandidates([a, b], { now: NOW })

    // Equal similarity, but `a` is fresher (age 0) than `b` (age 365d) — `a` wins on freshness.
    expect(ranked[0].message_id).toBe('a')
    expect(ranked[0].freshness).toBeGreaterThan(ranked[1].freshness)
  })

  it('respects the `limit` option', () => {
    const many = Array.from({ length: 10 }, (_, i) =>
      candidate({ message_id: `m${i}`, similarity: i / 10, created_at: NOW.toISOString() }),
    )
    const ranked = rankRecallCandidates(many, { now: NOW, limit: 3 })
    expect(ranked).toHaveLength(3)
    // Highest similarity (m9) should be first.
    expect(ranked[0].message_id).toBe('m9')
  })

  it('recencyFallbackFreshness decays to 0.5 at exactly the documented half-life', () => {
    const created = new Date(NOW.getTime() - RECENCY_FALLBACK_HALF_LIFE_DAYS * 86_400_000).toISOString()
    const freshness = recencyFallbackFreshness(created, NOW)
    expect(freshness).toBeCloseTo(0.5, 6)
  })

  it('uses recency_fallback by default (no M-6 provenance stamp available yet)', () => {
    const ranked = rankRecallCandidates([candidate({ message_id: 'x' })], { now: NOW })
    expect(ranked[0].freshness_source).toBe('recency_fallback')
  })

  it('prefers an injected freshnessOf signal (the M-6 dependency seam) over the recency fallback', () => {
    const old = candidate({
      message_id: 'old-but-freshly-reaffirmed',
      created_at: new Date(NOW.getTime() - 400 * 86_400_000).toISOString(), // very old by recency proxy
      similarity: 0.5,
    })
    const recentButStale = candidate({
      message_id: 'recent-but-superseded',
      created_at: NOW.toISOString(), // very fresh by recency proxy
      similarity: 0.5,
    })

    // Simulated M-6 provenance stamp: the "old" turn's underlying fact set was
    // reaffirmed (freshness 0.95); the "recent" turn's conclusion has since
    // been superseded by newer chart data (freshness 0.05). Recency alone
    // would rank these the OPPOSITE way.
    const ranked = rankRecallCandidates([old, recentButStale], {
      now: NOW,
      freshnessOf: (c) => (c.message_id === 'old-but-freshly-reaffirmed' ? 0.95 : 0.05),
    })

    expect(ranked[0].message_id).toBe('old-but-freshly-reaffirmed')
    expect(ranked[0].freshness_source).toBe('provenance_stamp')
    expect(ranked[1].freshness_source).toBe('provenance_stamp')
  })

  it('falls back to recency when freshnessOf returns undefined for a specific candidate', () => {
    const ranked = rankRecallCandidates([candidate({ message_id: 'unstamped' })], {
      now: NOW,
      freshnessOf: () => undefined,
    })
    expect(ranked[0].freshness_source).toBe('recency_fallback')
  })
})
