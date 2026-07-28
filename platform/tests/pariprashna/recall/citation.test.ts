/**
 * recall/citation.test.ts — PB-2 (SMṚTI) lane M-4.
 *
 * Proves every citation `toPriorReadingCitation(s)` produces is graded
 * `prior_reading` — never any other grade — and that the audit channel (not
 * the reader-facing label) carries the recall provenance.
 */
import { describe, expect, it } from 'vitest'
import { toPriorReadingCitation, toPriorReadingCitations } from '@/lib/pariprashna/recall/citation'
import { rankRecallCandidates } from '@/lib/pariprashna/recall/rank'
import type { RecallCandidate } from '@/lib/pariprashna/recall/types'
import { CITATION_GRADE_WEIGHT } from '@/lib/pariprashna/citations/types'

const NOW = new Date('2026-07-28T00:00:00.000Z')

function candidate(overrides: Partial<RecallCandidate>): RecallCandidate {
  return {
    message_id: 'msg-1',
    conversation_id: 'conv-other-thread',
    conversation_title: 'A prior reading',
    created_at: '2026-05-01T00:00:00.000Z',
    content: 'Saturn return favors a structural career decision within the next 18 months.',
    similarity: 0.87,
    ...overrides,
  }
}

describe('toPriorReadingCitation(s)', () => {
  it('always grades the citation prior_reading', () => {
    const [ranked] = rankRecallCandidates([candidate({})], { now: NOW })
    const citation = toPriorReadingCitation(ranked)
    expect(citation.grade).toBe('prior_reading')
  })

  it('never leaks the internal message/conversation id into the reader-facing label', () => {
    const [ranked] = rankRecallCandidates([candidate({ message_id: 'SECRET-ID-123' })], { now: NOW })
    const citation = toPriorReadingCitation(ranked)
    expect(citation.reader_label).not.toContain('SECRET-ID-123')
    expect(citation.reader_label).toMatch(/Earlier reading/)
  })

  it('carries recall provenance (similarity, freshness, ids) only in audit_detail', () => {
    const [ranked] = rankRecallCandidates([candidate({})], { now: NOW })
    const citation = toPriorReadingCitation(ranked)
    expect(citation.audit_detail).toContain('conv-other-thread')
    expect(citation.audit_detail).toContain('msg-1')
    expect(citation.audit_detail).toMatch(/similarity=/)
    expect(citation.audit_detail).toMatch(/freshness=/)
  })

  it('batch form preserves order and grades every citation prior_reading', () => {
    const ranked = rankRecallCandidates(
      [candidate({ message_id: 'a', similarity: 0.9 }), candidate({ message_id: 'b', similarity: 0.4 })],
      { now: NOW },
    )
    const citations = toPriorReadingCitations(ranked)
    expect(citations).toHaveLength(2)
    expect(citations.every((c) => c.grade === 'prior_reading')).toBe(true)
    expect(citations[0].ref).toContain('a')
  })

  it('prior_reading is the strict minimum of CITATION_GRADE_WEIGHT (structural weakness)', () => {
    const weights = Object.values(CITATION_GRADE_WEIGHT)
    expect(CITATION_GRADE_WEIGHT.prior_reading).toBe(Math.min(...weights))
    // Strictly below every other grade, including `unverified` (the
    // hallucination-flagged grade) — a REAL recalled citation still ranks
    // structurally weaker than even a flagged, possibly-hallucinated one.
    expect(CITATION_GRADE_WEIGHT.prior_reading).toBeLessThan(CITATION_GRADE_WEIGHT.unverified)
    expect(CITATION_GRADE_WEIGHT.prior_reading).toBeLessThan(CITATION_GRADE_WEIGHT.contextual)
    expect(CITATION_GRADE_WEIGHT.prior_reading).toBeLessThan(CITATION_GRADE_WEIGHT.supporting)
    expect(CITATION_GRADE_WEIGHT.prior_reading).toBeLessThan(CITATION_GRADE_WEIGHT.primary)
  })
})
