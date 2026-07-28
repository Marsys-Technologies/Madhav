/**
 * PB-1/integrate — C-1 transcript reducer duplicate-event dedup.
 *
 * Regression net for the verifier-flagged bug: the reducer used to compare an
 * incoming event id only against `turn.lastEventId` (a SINGLE slot), so a
 * NON-adjacent duplicate — e.g. a reconnect replaying an earlier batch, with
 * other events in between — slipped through and double-applied (a block.delta
 * appended its text twice). The fix is a per-turn seen-SET. These tests prove
 * BOTH an adjacent and a non-adjacent redelivery are dropped.
 */
import { describe, it, expect } from 'vitest'
import { threadReducer, initialThreadState } from '@/components/pariprashna/state/reducer'
import type { ThreadAction } from '@/components/pariprashna/state/reducer'
import type { ThreadState } from '@/components/pariprashna/state/types'

function run(actions: ThreadAction[]): ThreadState {
  return actions.reduce((s, a) => threadReducer(s, a), initialThreadState)
}

const TURN = 't1'

function tailText(state: ThreadState): string {
  return state.turns.find((t) => t.id === TURN)?.tail?.text ?? ''
}

describe('threadReducer — duplicate-event dedup (seen-set)', () => {
  it('drops a NON-adjacent duplicate block.delta (the reconnect-replay bug)', () => {
    const state = run([
      { type: 'CLIENT_SUBMIT_TURN', turnId: TURN, userText: 'q' },
      { type: 'block.open', turnId: TURN, blockId: 'b1', kind: 'paragraph', eventId: 'e-open' },
      { type: 'block.delta', turnId: TURN, blockId: 'b1', textDelta: 'Hello', eventId: 'd1' },
      { type: 'block.delta', turnId: TURN, blockId: 'b1', textDelta: ' World', eventId: 'd2' },
      // NON-adjacent redelivery of d1 — 'd2' was applied in between, so the old
      // single-slot lastEventId check (lastEventId === 'd2') would have MISSED
      // this and re-appended 'Hello' → 'Hello WorldHello'.
      { type: 'block.delta', turnId: TURN, blockId: 'b1', textDelta: 'Hello', eventId: 'd1' },
    ])
    expect(tailText(state)).toBe('Hello World')
  })

  it('drops an ADJACENT (back-to-back) duplicate block.delta too', () => {
    const state = run([
      { type: 'CLIENT_SUBMIT_TURN', turnId: TURN, userText: 'q' },
      { type: 'block.open', turnId: TURN, blockId: 'b1', kind: 'paragraph', eventId: 'e-open' },
      { type: 'block.delta', turnId: TURN, blockId: 'b1', textDelta: 'Hello', eventId: 'd1' },
      { type: 'block.delta', turnId: TURN, blockId: 'b1', textDelta: 'Hello', eventId: 'd1' },
    ])
    expect(tailText(state)).toBe('Hello')
  })

  it('does NOT drop a distinct delta that merely repeats earlier text (id is the key, not content)', () => {
    const state = run([
      { type: 'CLIENT_SUBMIT_TURN', turnId: TURN, userText: 'q' },
      { type: 'block.open', turnId: TURN, blockId: 'b1', kind: 'paragraph', eventId: 'e-open' },
      { type: 'block.delta', turnId: TURN, blockId: 'b1', textDelta: 'Hello', eventId: 'd1' },
      { type: 'block.delta', turnId: TURN, blockId: 'b1', textDelta: 'Hello', eventId: 'd2' },
    ])
    expect(tailText(state)).toBe('HelloHello')
  })

  it('dedups a non-adjacent duplicate citation.define (only defined once)', () => {
    const cite = (eventId: string) =>
      ({
        type: 'citation.define' as const,
        turnId: TURN,
        citation: {
          n: 1,
          title: 'Saturn',
          sourceClass: 'chart_factor' as const,
          relevance: 'x',
          ref: 'FACT.1',
          grade: 'confirmed' as const,
        },
        eventId,
      })
    const state = run([
      { type: 'CLIENT_SUBMIT_TURN', turnId: TURN, userText: 'q' },
      cite('c1'),
      { type: 'flag', turnId: TURN, flag: 'noop', eventId: 'f1' },
      cite('c1'), // non-adjacent duplicate
    ])
    const turn = state.turns.find((t) => t.id === TURN)!
    expect(Object.keys(turn.citations)).toHaveLength(1)
    expect(turn.seenEventIds.has('c1')).toBe(true)
  })
})
