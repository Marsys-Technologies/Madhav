/**
 * V3-E-024 — a clarification-only turn's server stream never emits
 * `turn.commit` (confirmed live 2026-08-28: the deployed Portal's SSE trace
 * for a clarification turn goes `block.commit` (the clarifying question) →
 * `phase:plan end` → `turn.close, status:"ok", ms:458` directly — no
 * `turn.commit` at all). The reducer's `turn.close` case only ever
 * transitioned a turn to `'settled'` when its CURRENT status was already
 * `'settling'` — a status `turn.commit` is the ONLY action that sets. For a
 * turn that never receives `turn.commit`, `turn.close` left `status`
 * completely unchanged, so the turn was stuck forever in its pre-close
 * status (e.g. `'submitted'`) — rendered by the UI as still "composing",
 * with the composer disabled, even though the server-side turn had fully
 * and successfully closed within half a second. Reader impact: the
 * composer never re-enables, so the reader cannot answer the clarifying
 * question that is fully visible on screen in front of them.
 */
import { describe, it, expect } from 'vitest'
import { threadReducer, initialThreadState, type ThreadAction } from '../reducer'
import type { ThreadState } from '../types'

function applyAll(state: ThreadState, events: ThreadAction[]): ThreadState {
  return events.reduce((s, e) => threadReducer(s, e), state)
}

function turnOf(state: ThreadState, turnId: string) {
  const t = state.turns.find((t) => t.id === turnId)
  if (!t) throw new Error(`turn ${turnId} not found`)
  return t
}

describe('turn.close settles a turn even when turn.commit never arrived (clarification-only turns)', () => {
  it('a clarification turn (block.commit, no turn.commit, then turn.close) reaches settled, not stuck', () => {
    const state = applyAll(initialThreadState, [
      { type: 'CLIENT_SUBMIT_TURN', turnId: 'T1', userText: 'Is it a good time?' },
      { type: 'block.open', turnId: 'T1', blockId: 'clar-0', kind: 'paragraph', eventId: 'e1' },
      {
        type: 'block.commit',
        turnId: 'T1',
        blockId: 'clar-0',
        kind: 'paragraph',
        html: 'Could you clarify what you would like to know?',
        eventId: 'e2',
      },
      { type: 'turn.close', turnId: 'T1', eventId: 'e3' },
    ])
    const t = turnOf(state, 'T1')
    expect(t.status).toBe('settled')
  })

  it('does not regress the existing turn.commit -> turn.close path', () => {
    const state = applyAll(initialThreadState, [
      { type: 'CLIENT_SUBMIT_TURN', turnId: 'T1', userText: 'hi' },
      {
        type: 'turn.commit',
        turnId: 'T1',
        grounding: { factorCount: 1, classicalCount: 0, elapsedLabel: '0:01', gradeSummaryLabel: 'x', source: 'client_estimate' },
        eventId: 'e1',
        persistStatus: 'ok',
      },
      { type: 'turn.close', turnId: 'T1', eventId: 'e2' },
    ])
    const t = turnOf(state, 'T1')
    expect(t.status).toBe('settled')
  })

  it('a turn.close arriving after the user already pressed Stop does not resurrect it into settled', () => {
    const state = applyAll(initialThreadState, [
      { type: 'CLIENT_SUBMIT_TURN', turnId: 'T1', userText: 'hi' },
      { type: 'CLIENT_STOP', turnId: 'T1' },
      { type: 'turn.close', turnId: 'T1', eventId: 'e1' },
    ])
    const t = turnOf(state, 'T1')
    expect(t.status).toBe('interrupted')
  })

  it('a turn.close arriving after an error does not overwrite the error state', () => {
    const state = applyAll(initialThreadState, [
      { type: 'CLIENT_SUBMIT_TURN', turnId: 'T1', userText: 'hi' },
      {
        type: 'error',
        turnId: 'T1',
        error: { kind: 'timeout', bandLabel: 'Taking longer than usual…', sentence: 'The provider timed out.', actions: ['retry'] },
        eventId: 'e1',
      },
      { type: 'turn.close', turnId: 'T1', eventId: 'e2' },
    ])
    const t = turnOf(state, 'T1')
    expect(t.status).toBe('errored')
  })
})
