/**
 * Semantic-hash replay↔persistence comparator — P2-D (PPR-10, FD-9).
 *
 * Drives `compareSemanticEquivalence` with a REAL `PariprashnaEvent[]` stream
 * (the PR-#927 capture feed's shape) on one side and independently-built
 * `PersistedMessagePart[]` rows on the other — never the same object handed
 * to both sides, so a passing "match" case is a real proof, not a tautology.
 */

import { describe, it, expect } from 'vitest'
import {
  compareSemanticEquivalence,
  notComparableSemantic,
  exitCodeForSemantic,
  formatSemanticComparison,
} from '../semantic_compare'
import type { PariprashnaEvent } from '../../protocol/events'
import type { PersistedMessagePart } from '../schema'

const IDENTITY = {
  id: '11111111-1111-1111-1111-111111111111',
  conversation_id: '22222222-2222-2222-2222-222222222222',
  role: 'assistant' as const,
  schema_version: 1,
  model_id: 'm',
  provider: 'p',
}

function persistedPart(seq: number, kind: PersistedMessagePart['kind'], body: unknown): PersistedMessagePart {
  return {
    id: `part-${seq}`,
    message_id: IDENTITY.id,
    seq,
    kind,
    body,
    model_visible: kind === 'text',
    created_at: '2026-08-19T00:00:00.000Z',
  }
}

function captureEvents(): PariprashnaEvent[] {
  return [
    { type: 'turn.open', seq: 0, t: 1, turn_id: 'T', conversation_id: IDENTITY.conversation_id, chart_id: 'X', model_id: 'm', reading_depth: 'auto', length_tier: 'standard' },
    { type: 'block.open', seq: 1, t: 2, block_id: 'b1', pass_id: 1, role: 'prose' },
    { type: 'block.commit', seq: 2, t: 3, block_id: 'b1', text: 'Jupiter in the 10th strengthens career authority.' },
    { type: 'citation.define', seq: 3, t: 4, index: 1, signal_id: 'SIG.MSR.413', layer: 'L2.5', snippet: 'Jupiter/10th', reader_label: 'Jupiter/10th' },
    { type: 'turn.commit', seq: 4, t: 5, turn_id: 'T', conversation_id: IDENTITY.conversation_id, message_id: IDENTITY.id, status: 'ok', assistant_chars: 50 },
    { type: 'turn.close', seq: 5, t: 6, turn_id: 'T', status: 'ok', ms: 10 },
  ]
}

describe('compareSemanticEquivalence — real capture stream vs. independently-built persisted rows', () => {
  it('SEMANTIC MATCH when persisted citation text is an independent re-derivation of the same fact', () => {
    const persistedParts: PersistedMessagePart[] = [
      persistedPart(0, 'text', { text: 'Jupiter in the 10th strengthens career authority.', block_id: 'b1' }),
      // Independently re-derived snippet/reader_label — same signal_id/layer/index.
      persistedPart(1, 'citation', {
        index: 1,
        signal_id: 'SIG.MSR.413',
        layer: 'L2.5',
        snippet: 'Career strength via Jupiter/10th-house placement',
        reader_label: 'Career authority (Jupiter)',
      }),
    ]
    const result = compareSemanticEquivalence({
      turnId: 'T',
      events: captureEvents(),
      message: IDENTITY,
      persistedParts,
    })
    expect(result.status).toBe('semantic_match')
    expect(result.replayed_hash).toBe(result.persisted_hash)
    // The re-derivation IS still surfaced as a diff — never silently dropped —
    // but classed presentation_only, not identity.
    const citationDiff = result.diffs.find((d) => d.kind === 'citation')
    expect(citationDiff?.diff_class).toBe('presentation_only')
    expect(exitCodeForSemantic(result)).toBe(0)
  })

  it('SEMANTIC DIVERGENCE when the persisted prose genuinely differs from the replayed stream', () => {
    const persistedParts: PersistedMessagePart[] = [
      persistedPart(0, 'text', { text: 'Saturn in the 10th restricts career authority.', block_id: 'b1' }),
      persistedPart(1, 'citation', { index: 1, signal_id: 'SIG.MSR.413', layer: 'L2.5', snippet: 'Jupiter/10th' }),
    ]
    const result = compareSemanticEquivalence({
      turnId: 'T',
      events: captureEvents(),
      message: IDENTITY,
      persistedParts,
    })
    expect(result.status).toBe('semantic_diverged')
    expect(result.replayed_hash).not.toBe(result.persisted_hash)
    const textDiff = result.diffs.find((d) => d.kind === 'text')
    expect(textDiff?.diff_class).toBe('identity')
    expect(exitCodeForSemantic(result)).toBe(1)
  })

  it('SEMANTIC DIVERGENCE when a citation identity field differs (wrong signal cited)', () => {
    const persistedParts: PersistedMessagePart[] = [
      persistedPart(0, 'text', { text: 'Jupiter in the 10th strengthens career authority.', block_id: 'b1' }),
      persistedPart(1, 'citation', { index: 1, signal_id: 'SIG.MSR.999', layer: 'L2.5', snippet: 'Jupiter/10th' }),
    ]
    const result = compareSemanticEquivalence({
      turnId: 'T',
      events: captureEvents(),
      message: IDENTITY,
      persistedParts,
    })
    expect(result.status).toBe('semantic_diverged')
    const citationDiff = result.diffs.find((d) => d.kind === 'citation')
    expect(citationDiff?.diff_class).toBe('identity')
  })

  it('notComparableSemantic is a distinct status, never a silent pass, and exit-codes 2', () => {
    const result = notComparableSemantic('T', 'no captured events for this turn')
    expect(result.status).toBe('not_comparable')
    expect(exitCodeForSemantic(result)).toBe(2)
    expect(formatSemanticComparison(result)).toContain('NOT COMPARABLE')
    expect(formatSemanticComparison(result)).not.toContain('SEMANTIC MATCH')
  })

  it('formatSemanticComparison names presentation-only diffs without failing the report', () => {
    const persistedParts: PersistedMessagePart[] = [
      persistedPart(0, 'text', { text: 'Jupiter in the 10th strengthens career authority.', block_id: 'b1' }),
      persistedPart(1, 'citation', { index: 1, signal_id: 'SIG.MSR.413', layer: 'L2.5', snippet: 'A different phrasing of the same citation' }),
    ]
    const result = compareSemanticEquivalence({ turnId: 'T', events: captureEvents(), message: IDENTITY, persistedParts })
    const report = formatSemanticComparison(result)
    expect(report).toContain('SEMANTIC MATCH')
    expect(report).toContain('presentation-only diff')
  })
})
