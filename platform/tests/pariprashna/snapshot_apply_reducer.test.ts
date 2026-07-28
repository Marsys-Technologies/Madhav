/**
 * PB-2/M-5 — reducer handling of the `snapshot.apply` action (the client half
 * of the buffer-evicted reconnect fallback). Proves the reducer applies it as
 * ONE write that REPLACES `blocks`/`tail` wholesale (never appends onto
 * whatever partial state the client already had — after a gap the client
 * cannot trust its own partial block list) and that it is itself subject to
 * the same dedup discipline as every other wire event.
 */
import { describe, it, expect } from 'vitest'
import { threadReducer, initialThreadState } from '@/components/pariprashna/state/reducer'
import type { ThreadAction } from '@/components/pariprashna/state/reducer'
import type { ThreadState } from '@/components/pariprashna/state/types'

const TURN = 't1'

function run(actions: ThreadAction[]): ThreadState {
  return actions.reduce((s, a) => threadReducer(s, a), initialThreadState)
}

describe('threadReducer — snapshot.apply (buffer-evicted reconnect fallback)', () => {
  it('replaces a partial tail + block list wholesale with the snapshot text, in one write', () => {
    const state = run([
      { type: 'CLIENT_SUBMIT_TURN', turnId: TURN, userText: 'q' },
      { type: 'block.open', turnId: TURN, blockId: 'b1', kind: 'paragraph', eventId: 'e-open' },
      { type: 'block.delta', turnId: TURN, blockId: 'b1', textDelta: 'partial frag', eventId: 'd1' },
      {
        type: 'snapshot.apply',
        turnId: TURN,
        text: 'The complete, current answer as of the snapshot.',
        citations: [],
        turnStatus: 'open',
        eventId: 's1',
      },
    ])
    const turn = state.turns.find((t) => t.id === TURN)!
    expect(turn.tail).toBeNull() // no dangling tail left over from before the gap
    expect(turn.blocks).toHaveLength(1)
    expect(turn.blocks[0].html).toBe('The complete, current answer as of the snapshot.')
    expect(turn.status).toBe('streaming')
  })

  it('sets status to interrupted when the snapshot reports the turn died server-side', () => {
    const state = run([
      { type: 'CLIENT_SUBMIT_TURN', turnId: TURN, userText: 'q' },
      {
        type: 'snapshot.apply',
        turnId: TURN,
        text: 'Whatever arrived before the server died.',
        citations: [],
        turnStatus: 'interrupted',
        eventId: 's1',
      },
    ])
    const turn = state.turns.find((t) => t.id === TURN)!
    expect(turn.status).toBe('interrupted')
    expect(turn.blocks[0].html).toBe('Whatever arrived before the server died.')
  })

  it('merges snapshot citations into the citation map, keyed by index', () => {
    const state = run([
      { type: 'CLIENT_SUBMIT_TURN', turnId: TURN, userText: 'q' },
      {
        type: 'snapshot.apply',
        turnId: TURN,
        text: 'Text with a citation.',
        citations: [
          { n: 1, title: 'Saturn', sourceClass: 'chart_factor', relevance: 'x', ref: 'FACT.1', grade: 'catalog' },
        ],
        turnStatus: 'open',
        eventId: 's1',
      },
    ])
    const turn = state.turns.find((t) => t.id === TURN)!
    expect(turn.citations[1]?.title).toBe('Saturn')
  })

  it('drops a non-adjacent duplicate snapshot.apply (dedup applies here too)', () => {
    const snap = (eventId: string) =>
      ({
        type: 'snapshot.apply' as const,
        turnId: TURN,
        text: 'FIRST snapshot text',
        citations: [],
        turnStatus: 'open' as const,
        eventId,
      })
    const state = run([
      { type: 'CLIENT_SUBMIT_TURN', turnId: TURN, userText: 'q' },
      snap('s1'),
      { type: 'flag', turnId: TURN, flag: 'noop', eventId: 'f1' },
      { type: 'snapshot.apply', turnId: TURN, text: 'SECOND (should be dropped, same id)', citations: [], turnStatus: 'open', eventId: 's1' },
    ])
    const turn = state.turns.find((t) => t.id === TURN)!
    expect(turn.blocks[0].html).toBe('FIRST snapshot text')
  })
})
