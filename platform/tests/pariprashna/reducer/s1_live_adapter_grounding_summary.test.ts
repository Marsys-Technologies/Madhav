/**
 * G2-B "Citations at first paint" — `s1LiveAdapter`'s honest degrade-path
 * contract: `GroundingSummary.source` must truthfully say whether the rollup
 * came from the server's own `grounding_summary` wire field or from the
 * client's own citation tally, and the two must never be indistinguishable.
 */

import { describe, it, expect } from 'vitest'
import { makeS1LiveAdapter } from '@/components/pariprashna/state/s1LiveAdapter'
import type { PariprashnaEvent } from '@/lib/pariprashna/protocol/events'
import type { WireEvent } from '@/components/pariprashna/state/types'

function turnCommitGrounding(events: PariprashnaEvent[]) {
  const adapter = makeS1LiveAdapter('client-turn-1', 'a question', Date.now())
  const mapped: WireEvent[] = []
  for (const ev of events) mapped.push(...adapter.map(ev))
  const commit = mapped.find((e) => e.type === 'turn.commit')
  if (!commit || commit.type !== 'turn.commit') throw new Error('no turn.commit produced')
  return commit.grounding
}

describe('s1LiveAdapter — grounding summary source labeling', () => {
  it('server grounding_summary present → source "server", numbers taken from the wire, never re-derived', () => {
    const events: PariprashnaEvent[] = [
      {
        type: 'citation.define',
        seq: 0,
        t: 0,
        index: 1,
        signal_id: 'SIG.MSR.413',
        layer: 'L2.5',
        snippet: 'Mercury convergence',
        reader_label: 'Mercury convergence',
        grade: 'primary',
      },
      {
        type: 'turn.commit',
        seq: 1,
        t: 0,
        turn_id: 'srv-turn-1',
        conversation_id: 'conv-1',
        message_id: 'msg-1',
        status: 'ok',
        assistant_chars: 42,
        grounding_summary: {
          citation_count: 1,
          hallucination_count: 0,
          grade_counts: { primary: 1, supporting: 0, contextual: 0, unverified: 0, prior_reading: 0 },
          completeness: { served: 4, floor_item_total: 6 },
          completeness_line: '4/6 floor items served',
        },
      },
    ]
    const grounding = turnCommitGrounding(events)
    expect(grounding.source).toBe('server')
    expect(grounding.completenessLine).toBe('4/6 floor items served')
    expect(grounding.gradeSummaryLabel).toBe('Core claim: WELL-GROUNDED')
  })

  it('no server grounding_summary → source "client_estimate", no completenessLine invented', () => {
    const events: PariprashnaEvent[] = [
      {
        type: 'citation.define',
        seq: 0,
        t: 0,
        index: 1,
        signal_id: 'SIG.MSR.413',
        layer: 'L2.5',
        snippet: 'Mercury convergence',
        reader_label: 'Mercury convergence',
        grade: 'primary',
      },
      {
        type: 'turn.commit',
        seq: 1,
        t: 0,
        turn_id: 'srv-turn-1',
        conversation_id: 'conv-1',
        message_id: 'msg-1',
        status: 'ok',
        assistant_chars: 42,
        // no grounding_summary — the flag-off / not-built case.
      },
    ]
    const grounding = turnCommitGrounding(events)
    expect(grounding.source).toBe('client_estimate')
    expect(grounding.completenessLine).toBeUndefined()
    // Still honestly rolled up from the one real citation seen on the wire.
    expect(grounding.gradeSummaryLabel).toBe('Core claim: WELL-GROUNDED')
  })

  it('a mixed server grade distribution never reads as WELL-GROUNDED (matches the honest-rollup rule)', () => {
    const events: PariprashnaEvent[] = [
      {
        type: 'turn.commit',
        seq: 0,
        t: 0,
        turn_id: 'srv-turn-2',
        conversation_id: 'conv-2',
        message_id: 'msg-2',
        status: 'ok',
        assistant_chars: 10,
        grounding_summary: {
          citation_count: 2,
          hallucination_count: 1,
          grade_counts: { primary: 1, supporting: 0, contextual: 0, unverified: 1, prior_reading: 0 },
          completeness: null,
          completeness_line: null,
        },
      },
    ]
    const grounding = turnCommitGrounding(events)
    expect(grounding.source).toBe('server')
    expect(grounding.gradeSummaryLabel).not.toBe('Core claim: WELL-GROUNDED')
  })
})
