/**
 * P2-F (PPR-19) mobile + a11y hardening — deterministic REAL state builders.
 *
 * Folds the SAME production fixture event streams (`fixtures/*`) through the
 * SAME production reducer (`state/reducer.ts`) used by `useFixtureStream` —
 * the only difference from a live browser run is that every event is
 * applied synchronously instead of via real `setTimeout` delays, so a test
 * gets an exact, deterministic snapshot of a real reducer-produced
 * `TurnState` for a given §5.3 state without waiting on wall-clock time.
 * Nothing here re-implements or approximates reducer/rendering behavior —
 * it is the actual `threadReducer` + actual fixture data.
 */
import { threadReducer, initialThreadState, makeInitialTurnState } from '@/components/pariprashna/state/reducer'
import { buildFixtureForMode, type FixtureMode } from '@/components/pariprashna/fixtures'
import type { ThreadState, TurnState, ClassifiedError, WireEvent } from '@/components/pariprashna/state/types'

let seq = 0
function nextTurnId(): string {
  seq += 1
  return `test_turn_${seq}`
}

/** Fold a fixture's full event stream through the real reducer; returns the settled (or fixture-final) TurnState. */
export function playFixtureToEnd(mode: FixtureMode, userText = 'Test question for the fixture battery'): TurnState {
  const turnId = nextTurnId()
  let state: ThreadState = threadReducer(initialThreadState, { type: 'CLIENT_SUBMIT_TURN', turnId, userText })
  const fixture = buildFixtureForMode(mode, turnId, userText)
  for (const { event } of fixture.events) {
    state = threadReducer(state, event)
  }
  const turn = state.turns.find((t) => t.id === turnId)
  if (!turn) throw new Error(`playFixtureToEnd: turn ${turnId} missing after replay`)
  return turn
}

/** Fold only the events up to `fraction` of the fixture's total duration — a genuine mid-stream snapshot (e.g. 'thinking'/'streaming'), not a hand-authored approximation of one. */
export function playFixturePartial(mode: FixtureMode, fraction: number, userText = 'Test question for the fixture battery'): TurnState {
  const turnId = nextTurnId()
  let state: ThreadState = threadReducer(initialThreadState, { type: 'CLIENT_SUBMIT_TURN', turnId, userText })
  const fixture = buildFixtureForMode(mode, turnId, userText)
  const maxMs = Math.max(...fixture.events.map((e) => e.atMs))
  const cutoff = maxMs * fraction
  for (const { atMs, event } of fixture.events) {
    if (atMs > cutoff) break // events are pre-sorted by FixtureBuilder.build()
    state = threadReducer(state, event)
  }
  const turn = state.turns.find((t) => t.id === turnId)
  if (!turn) throw new Error(`playFixturePartial: turn ${turnId} missing after replay`)
  return turn
}

/** A turn stopped mid-stream (§7.8 "STOPPED — KEPT WHAT ARRIVED"). */
export function playFixtureInterrupted(mode: FixtureMode, fraction: number, userText = 'Test question for the fixture battery'): TurnState {
  const turnId = nextTurnId()
  let state: ThreadState = threadReducer(initialThreadState, { type: 'CLIENT_SUBMIT_TURN', turnId, userText })
  const fixture = buildFixtureForMode(mode, turnId, userText)
  const maxMs = Math.max(...fixture.events.map((e) => e.atMs))
  const cutoff = maxMs * fraction
  for (const { atMs, event } of fixture.events) {
    if (atMs > cutoff) break
    state = threadReducer(state, event)
  }
  state = threadReducer(state, { type: 'CLIENT_STOP', turnId })
  const turn = state.turns.find((t) => t.id === turnId)
  if (!turn) throw new Error(`playFixtureInterrupted: turn ${turnId} missing after replay`)
  return turn
}

/** A turn mid-stream that drops and is shown reconnecting (§7.8 "RECONNECTING…"). */
export function playFixtureReconnecting(mode: FixtureMode, fraction: number, userText = 'Test question for the fixture battery'): TurnState {
  const turnId = nextTurnId()
  let state: ThreadState = threadReducer(initialThreadState, { type: 'CLIENT_SUBMIT_TURN', turnId, userText })
  const fixture = buildFixtureForMode(mode, turnId, userText)
  const maxMs = Math.max(...fixture.events.map((e) => e.atMs))
  const cutoff = maxMs * fraction
  for (const { atMs, event } of fixture.events) {
    if (atMs > cutoff) break
    state = threadReducer(state, event)
  }
  const reconnectEvent: WireEvent = { type: 'reconnecting', turnId, eventId: `test-reconnect-${turnId}` }
  state = threadReducer(state, reconnectEvent)
  const turn = state.turns.find((t) => t.id === turnId)
  if (!turn) throw new Error(`playFixtureReconnecting: turn ${turnId} missing after replay`)
  return turn
}

const SAMPLE_ERROR: ClassifiedError = {
  kind: 'rate_limit',
  bandLabel: 'The model is busy — retrying',
  sentence: 'The model is busy right now. Retrying automatically.',
  actions: ['retry', 'switch_model'],
}

/** A turn that errored mid-stream (§7.8 error band lexicon). No fixture emits a real `error` wire
 *  event yet (F-3's edge-state lane owns building that path) — this applies the SAME event shape
 *  the reducer's `case 'error'` branch consumes (state/types.ts `WireEvent` 'error' variant) on top
 *  of a genuine partial stream, so the resulting TurnState is exactly what the reducer would
 *  produce from a real error event, not a hand-faked render. */
export function playFixtureErrored(mode: FixtureMode, fraction: number, userText = 'Test question for the fixture battery'): TurnState {
  const turnId = nextTurnId()
  let state: ThreadState = threadReducer(initialThreadState, { type: 'CLIENT_SUBMIT_TURN', turnId, userText })
  const fixture = buildFixtureForMode(mode, turnId, userText)
  const maxMs = Math.max(...fixture.events.map((e) => e.atMs))
  const cutoff = maxMs * fraction
  for (const { atMs, event } of fixture.events) {
    if (atMs > cutoff) break
    state = threadReducer(state, event)
  }
  const errorEvent: WireEvent = { type: 'error', turnId, error: SAMPLE_ERROR, eventId: `test-error-${turnId}` }
  state = threadReducer(state, errorEvent)
  const turn = state.turns.find((t) => t.id === turnId)
  if (!turn) throw new Error(`playFixtureErrored: turn ${turnId} missing after replay`)
  return turn
}

export { makeInitialTurnState }
