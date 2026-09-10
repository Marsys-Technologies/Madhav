/**
 * P2-D (PPR-10, FD-9) — settled_visual vs. durably_persisted, in the reducer.
 */

import { describe, it, expect } from 'vitest'
import {
  threadReducer,
  initialThreadState,
  makeInitialTurnState,
  isSettledVisual,
  isDurablyPersisted,
  isIncompleteTurn,
  type ThreadAction,
} from '../reducer'
import type { ThreadState } from '../types'

function applyAll(state: ThreadState, events: ThreadAction[]): ThreadState {
  return events.reduce((s, e) => threadReducer(s, e), state)
}

function turnOf(state: ThreadState, turnId: string) {
  const t = state.turns.find((t) => t.id === turnId)
  if (!t) throw new Error(`turn ${turnId} not found`)
  return t
}

describe('makeInitialTurnState', () => {
  it('starts with persistence "unknown", never optimistically durable', () => {
    const t = makeInitialTurnState('T1', 'hi')
    expect(t.persistence).toBe('unknown')
    expect(isSettledVisual(t)).toBe(false)
    expect(isDurablyPersisted(t)).toBe(false)
    expect(isIncompleteTurn(t)).toBe(false) // not settled yet — no banner while streaming
  })
})

describe('back-compat: turn.commit alone (no turn.persisted ever arrives)', () => {
  it('a settled turn with persistStatus "ok" and no turn.persisted event is durably_persisted (no false banner)', () => {
    const state = applyAll(initialThreadState, [
      { type: 'CLIENT_SUBMIT_TURN', turnId: 'T1', userText: 'hi' },
      { type: 'turn.commit', turnId: 'T1', grounding: { factorCount: 1, classicalCount: 0, elapsedLabel: '0:01', gradeSummaryLabel: 'x', source: 'client_estimate' }, eventId: 'e1', persistStatus: 'ok' },
      { type: 'turn.close', turnId: 'T1', eventId: 'e2' },
    ])
    const t = turnOf(state, 'T1')
    expect(t.status).toBe('settled')
    expect(isSettledVisual(t)).toBe(true)
    expect(t.persistence).toBe('durable')
    expect(isDurablyPersisted(t)).toBe(true)
    expect(isIncompleteTurn(t)).toBe(false)
  })

  it('a pre-P2-D fixture that never sets persistStatus at all stays "unknown" — never a fabricated durable claim', () => {
    const state = applyAll(initialThreadState, [
      { type: 'CLIENT_SUBMIT_TURN', turnId: 'T1', userText: 'hi' },
      { type: 'turn.commit', turnId: 'T1', grounding: { factorCount: 1, classicalCount: 0, elapsedLabel: '0:01', gradeSummaryLabel: 'x', source: 'client_estimate' }, eventId: 'e1' },
      { type: 'turn.close', turnId: 'T1', eventId: 'e2' },
    ])
    const t = turnOf(state, 'T1')
    expect(t.status).toBe('settled')
    expect(t.persistence).toBe('unknown')
    // Honest null, not a false positive AND not a false incomplete-banner —
    // isIncompleteTurn itself excludes 'unknown' (see its doc comment).
    expect(isIncompleteTurn(t)).toBe(false)
  })

  it('persistStatus "error" resolves to failed, not durable', () => {
    const state = applyAll(initialThreadState, [
      { type: 'CLIENT_SUBMIT_TURN', turnId: 'T1', userText: 'hi' },
      { type: 'turn.commit', turnId: 'T1', grounding: { factorCount: 0, classicalCount: 0, elapsedLabel: '0:01', gradeSummaryLabel: 'x', source: 'client_estimate' }, eventId: 'e1', persistStatus: 'error' },
      { type: 'turn.close', turnId: 'T1', eventId: 'e2' },
    ])
    const t = turnOf(state, 'T1')
    expect(t.persistence).toBe('failed')
    expect(isIncompleteTurn(t)).toBe(true)
  })
})

describe('the real gap: outbox-mode turn.persisted refines/overrides the optimistic guess', () => {
  it('settled_visual arrives before durably_persisted — the honest incomplete-turn window', () => {
    let state = applyAll(initialThreadState, [
      { type: 'CLIENT_SUBMIT_TURN', turnId: 'T1', userText: 'hi' },
      // Exercises the reducer with persistence left 'unknown' at commit time
      // (no persistStatus forwarded) so the subsequent turn.persisted events
      // are the ONLY signal driving the transition — isolates the exact
      // mechanic PPR-10 asks for, independent of the commit-time seed tested
      // separately above.
      { type: 'turn.commit', turnId: 'T1', grounding: { factorCount: 1, classicalCount: 0, elapsedLabel: '0:01', gradeSummaryLabel: 'x', source: 'client_estimate' }, eventId: 'e1' },
      { type: 'turn.persisted', turnId: 'T1', status: 'pending', eventId: 'e2' },
      { type: 'turn.close', turnId: 'T1', eventId: 'e3' },
    ])
    let t = turnOf(state, 'T1')
    expect(isSettledVisual(t)).toBe(true) // turn.close fired — the reader sees it as done
    expect(isDurablyPersisted(t)).toBe(false)
    expect(isIncompleteTurn(t)).toBe(true) // the honest, visible gap PPR-10 requires

    // The write-ahead confirms later (a follow-on turn.persisted, e.g. after
    // a recovery sweep or the in-request outbox apply completes):
    state = applyAll(state, [{ type: 'turn.persisted', turnId: 'T1', status: 'durable', eventId: 'e4' }])
    t = turnOf(state, 'T1')
    expect(isDurablyPersisted(t)).toBe(true)
    expect(isIncompleteTurn(t)).toBe(false)
  })

  it('a later turn.persisted DOWNGRADES an optimistic durable guess (defensive latest-wins)', () => {
    let state = applyAll(initialThreadState, [
      { type: 'CLIENT_SUBMIT_TURN', turnId: 'T1', userText: 'hi' },
      { type: 'turn.commit', turnId: 'T1', grounding: { factorCount: 1, classicalCount: 0, elapsedLabel: '0:01', gradeSummaryLabel: 'x', source: 'client_estimate' }, eventId: 'e1', persistStatus: 'ok' },
    ])
    expect(turnOf(state, 'T1').persistence).toBe('durable')
    state = applyAll(state, [{ type: 'turn.persisted', turnId: 'T1', status: 'failed', detail: 'disk full', eventId: 'e2' }])
    expect(turnOf(state, 'T1').persistence).toBe('failed')
  })

  it('duplicate eventId is dropped idempotently, exactly like every other reducer case', () => {
    let state = applyAll(initialThreadState, [
      { type: 'CLIENT_SUBMIT_TURN', turnId: 'T1', userText: 'hi' },
      { type: 'turn.persisted', turnId: 'T1', status: 'durable', eventId: 'e1' },
    ])
    const before = turnOf(state, 'T1')
    state = threadReducer(state, { type: 'turn.persisted', turnId: 'T1', status: 'failed', eventId: 'e1' })
    const after = turnOf(state, 'T1')
    expect(after.persistence).toBe(before.persistence) // the redelivery (same eventId) was a no-op
  })
})
