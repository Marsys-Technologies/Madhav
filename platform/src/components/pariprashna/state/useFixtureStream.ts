'use client'

import { useCallback, useMemo, useReducer, useRef } from 'react'
import { threadReducer, initialThreadState } from './reducer'
import type { ThreadAction } from './reducer'
import { buildFixtureForMode, type FixtureMode } from '../fixtures'

let turnSeq = 0
function nextTurnId(): string {
  turnSeq += 1
  return `turn_${Date.now()}_${turnSeq}`
}

/**
 * STUB transport: replays a recorded fixture's scheduled events against the
 * reducer with real setTimeout delays, standing in for an SSE subscription.
 *
 * WHAT'S REAL vs WHAT'S STUBBED:
 *  - The reducer (`state/reducer.ts`), the wire-event shape (`state/types.ts`),
 *    and every rendering component consuming `ThreadState` are the real,
 *    load-bearing implementation — swapping this hook for one that opens an
 *    EventSource/fetch-stream to a real `/api/pariprashna/...` endpoint and
 *    dispatches parsed `WireEvent`s is the ONLY change S-1's landing requires.
 *  - `submit()` here always plays a canned fixture chosen by `mode` rather
 *    than sending the user's actual text to an engine. The user's text IS
 *    threaded through (`turn.open.userText`) so the composer/turn plumbing
 *    is exercised honestly; the *content* of the reading is canned.
 *  - Two of the six available modes (`c2-single`, `c2-gap`) replay lane
 *    C-2's own recorded protocol fixtures through `state/c2ProtocolAdapter.ts`
 *    rather than our hand-authored ones — see that adapter's doc comment.
 *  - Stop cancels our local timers; a real transport would also need to
 *    signal the server to abort generation.
 */
export function useFixtureStream() {
  const [state, dispatch] = useReducer(threadReducer, initialThreadState)
  const timers = useRef(new Map<string, ReturnType<typeof setTimeout>[]>())

  const clearTurnTimers = useCallback((turnId: string) => {
    const list = timers.current.get(turnId)
    if (!list) return
    list.forEach((t) => clearTimeout(t))
    timers.current.delete(turnId)
  }, [])

  const dispatchTyped = dispatch as (a: ThreadAction) => void

  const submit = useCallback(
    (userText: string, mode: FixtureMode = 'adaptive') => {
      const turnId = nextTurnId()
      // Optimistic mount — the instant the user submits, before any "server" event (§5.3 `submitted`, M3).
      dispatchTyped({ type: 'CLIENT_SUBMIT_TURN', turnId, userText })

      const fixture = buildFixtureForMode(mode, turnId, userText)
      const scheduled: ReturnType<typeof setTimeout>[] = []
      for (const { atMs, event } of fixture.events) {
        const handle = setTimeout(() => dispatchTyped(event), atMs)
        scheduled.push(handle)
      }
      timers.current.set(turnId, scheduled)
      return turnId
    },
    [dispatchTyped],
  )

  const stop = useCallback(
    (turnId: string) => {
      clearTurnTimers(turnId)
      dispatchTyped({ type: 'CLIENT_STOP', turnId })
    },
    [clearTurnTimers, dispatchTyped],
  )

  return useMemo(() => ({ state, submit, stop }), [state, submit, stop])
}
