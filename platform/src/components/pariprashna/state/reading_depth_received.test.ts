/**
 * Lane P2-C (PPR-09/16) — the reducer half of the honest depth-received
 * disclosure. Pins that `reading_depth.received` writes to the turn (unlike
 * the overloaded S-3 `grade` event, which the reducer intentionally no-ops on
 * today), is idempotent under a replayed event id, and that an untouched turn
 * reports the honest absence (`null`), never a guessed value.
 */

import { describe, it, expect } from 'vitest'

import { threadReducer, initialThreadState } from './reducer'

function submitted(turnId: string) {
  return threadReducer(initialThreadState, { type: 'CLIENT_SUBMIT_TURN', turnId, userText: 'q' })
}

describe('reading_depth.received reducer case', () => {
  it('stores the depth-received value on the matching turn', () => {
    const state = threadReducer(submitted('t1'), {
      type: 'reading_depth.received',
      turnId: 't1',
      depth: 'standard',
      eventId: 't1-5',
    })
    expect(state.turns[0].readingDepthReceived).toBe('standard')
  })

  it('a turn with no reading_depth.received event reports null, not a guess', () => {
    const state = submitted('t1')
    expect(state.turns[0].readingDepthReceived).toBeNull()
  })

  it('drops a duplicate event id (reconnect-safe dedup)', () => {
    const once = threadReducer(submitted('t1'), {
      type: 'reading_depth.received',
      turnId: 't1',
      depth: 'standard',
      eventId: 't1-5',
    })
    const replayed = threadReducer(once, {
      type: 'reading_depth.received',
      turnId: 't1',
      depth: 'deep_dive',
      eventId: 't1-5',
    })
    expect(replayed.turns[0].readingDepthReceived).toBe('standard')
  })

  it('does not touch an unrelated turn', () => {
    let state = submitted('t1')
    state = threadReducer(state, { type: 'CLIENT_SUBMIT_TURN', turnId: 't2', userText: 'q2' })
    state = threadReducer(state, { type: 'reading_depth.received', turnId: 't1', depth: 'quick', eventId: 't1-1' })
    const t2 = state.turns.find((t) => t.id === 't2')!
    expect(t2.readingDepthReceived).toBeNull()
  })
})
