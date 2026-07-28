'use client'

import { useCallback, useEffect, useMemo, useReducer, useRef } from 'react'
import { threadReducer, initialThreadState } from '../state/reducer'
import type { ThreadAction } from '../state/reducer'
import { decodeEvent } from '@/lib/pariprashna/protocol/events'
import { makeS1LiveAdapter, type S1LiveAdapter } from '../state/s1LiveAdapter'

let turnSeq = 0
function nextTurnId(): string {
  turnSeq += 1
  return `turn_${Date.now()}_${turnSeq}`
}

export interface LiveSubmitOptions {
  reading_depth?: 'auto' | 'deep_dive'
  model_id?: string
  length_tier?: 'brief' | 'standard' | 'exhaustive'
}

/**
 * Per-client-turn connection bookkeeping (PB-2/M-5). Tracks exactly what a
 * reconnect needs: the SERVER's `turn_id` (minted fresh by the route, distinct
 * from the client-minted `turnId` used for reducer identity — captured off
 * the first `turn.open` event), the highest `seq` actually applied (sent back
 * as `Last-Event-ID`), when the last frame arrived (the staleness signal the
 * `visibilitychange` path uses), and whether the turn has reached a terminal
 * state (no further reconnect should ever be attempted past that point).
 */
interface TurnConnState {
  serverTurnId: string | null
  lastSeq: number
  lastFrameAtMs: number
  terminal: boolean
  /**
   * The ONE adapter instance for this turn, reused across the initial
   * connection and every reconnect. `makeS1LiveAdapter` is stateful (it
   * tallies citation grades to synthesize `turn.commit`'s grounding
   * summary — S-1's wire doesn't carry one) — minting a fresh adapter on
   * reconnect would silently reset that tally and undercount the eventual
   * grounding summary, so the SAME instance rides out every reconnect.
   */
  adapter: S1LiveAdapter
}

/**
 * A backgrounded tab returning after this long with NO frame received is
 * treated as "the connection probably died while we weren't watching" and
 * gets the same reconnect treatment as an explicit network error — the
 * SAME path, not a special case keyed on *why* focus changed. A tab that
 * comes back after a brief blur (still receiving frames normally) does
 * nothing extra: the ongoing fetch just keeps streaming.
 */
const VISIBILITY_STALL_THRESHOLD_MS = 8_000
const RECONNECT_MAX_ATTEMPTS = 5
const RECONNECT_BASE_DELAY_MS = 1_000
const RECONNECT_MAX_DELAY_MS = 8_000

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

/**
 * LIVE transport: opens a real SSE stream against `/api/pariprashna` (lane
 * S-1's route) and dispatches decoded, adapted events at the reducer. On an
 * unexpected disconnect — or a backgrounded tab returning to a turn that has
 * gone quiet — reconnects via `/api/pariprashna/resume` (lane PB-2/M-5),
 * sending the last-applied `seq` as `Last-Event-ID` so the server can either
 * replay exactly what was missed or fall back to a snapshot; either way the
 * reducer's existing per-turn seen-set dedup makes any overlap idempotent.
 *
 * This is the production-path sibling of `useFixtureStream` (which replays
 * canned event arrays for local dev / component work). Both return the SAME
 * `{ state, submit, stop }` shape, so `PariprashnaApp` can host either without
 * knowing which transport is live.
 */
export function useLiveStream(chartId: string) {
  const [state, dispatch] = useReducer(threadReducer, initialThreadState)
  const controllers = useRef(new Map<string, AbortController>())
  const connState = useRef(new Map<string, TurnConnState>())
  const dispatchTyped = dispatch as (a: ThreadAction) => void

  /**
   * Read one SSE body to completion, dispatching every decoded+adapted event
   * and updating this turn's connection bookkeeping as frames arrive. Shared
   * by both the initial POST and every resume GET so reconnect behaves
   * identically to a fresh connection from the reducer's point of view.
   */
  const pumpBody = useCallback(
    async (body: ReadableStream<Uint8Array>, turnId: string, cs: TurnConnState): Promise<void> => {
      const adapter = cs.adapter
      const reader = body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      for (;;) {
        const { value, done } = await reader.read()
        if (done) return
        buffer += decoder.decode(value, { stream: true })

        let sep: number
        while ((sep = buffer.indexOf('\n\n')) !== -1) {
          const frame = buffer.slice(0, sep)
          buffer = buffer.slice(sep + 2)
          const dataLine = frame.split('\n').find((l) => l.startsWith('data:'))
          if (!dataLine) continue
          const payload = dataLine.slice(dataLine.indexOf(':') + 1).trimStart()
          const decoded = decodeEvent(payload)
          if (!decoded) continue // skip garbled/unknown frame (never throws)

          cs.lastSeq = decoded.seq
          cs.lastFrameAtMs = Date.now()
          if (decoded.type === 'turn.open') cs.serverTurnId = decoded.turn_id
          if (decoded.type === 'turn.close' || decoded.type === 'error') cs.terminal = true

          for (const wire of adapter.map(decoded)) {
            dispatchTyped(wire)
          }
        }
      }
    },
    [dispatchTyped],
  )

  /**
   * Reconnect a turn via `/api/pariprashna/resume`, with capped exponential
   * backoff across transient failures. Generic over WHY it was called — a
   * thrown network error and a stale-tab `visibilitychange` both land here.
   */
  const reconnectLoop = useCallback(
    async (turnId: string, cs: TurnConnState): Promise<void> => {
      if (cs.terminal) return
      if (!cs.serverTurnId) {
        // Never even received turn.open — there is nothing server-side to
        // resume from (the server mints turn_id on its own first byte).
        dispatchTyped({
          type: 'error',
          turnId,
          error: {
            kind: 'network',
            bandLabel: 'Something went wrong',
            sentence: 'The connection was lost before the turn could start.',
            actions: ['retry'],
          },
          eventId: `${turnId}-noturnopen`,
        })
        return
      }

      const serverTurnId = cs.serverTurnId // captured once — narrows past the mutable-field/await boundary below
      dispatchTyped({ type: 'reconnecting', turnId, eventId: `${turnId}-reconnecting-${cs.lastSeq}` })

      for (let attempt = 1; attempt <= RECONNECT_MAX_ATTEMPTS; attempt++) {
        if (cs.terminal) return
        const ac = new AbortController()
        controllers.current.set(turnId, ac)
        try {
          const resp = await fetch(
            `/api/pariprashna/resume?turn_id=${encodeURIComponent(serverTurnId)}&last_event_id=${cs.lastSeq}`,
            {
              method: 'GET',
              headers: { 'Last-Event-ID': String(cs.lastSeq) },
              signal: ac.signal,
            },
          )
          if (!resp.ok || !resp.body) throw new Error(`resume failed (${resp.status})`)

          dispatchTyped({ type: 'reconnected', turnId, eventId: `${turnId}-reconnected-${cs.lastSeq}` })
          await pumpBody(resp.body, turnId, cs)
          return // pumpBody returned cleanly (stream ended) — done, whether terminal or not
        } catch (err) {
          if ((err as { name?: string })?.name === 'AbortError') return // stop() or unmount — not a failure
          if (attempt === RECONNECT_MAX_ATTEMPTS) {
            dispatchTyped({
              type: 'error',
              turnId,
              error: {
                kind: 'network',
                bandLabel: 'Something went wrong',
                sentence: 'Could not resume the connection after several attempts.',
                actions: ['retry'],
              },
              eventId: `${turnId}-resume-exhausted`,
            })
            return
          }
          const delay = Math.min(RECONNECT_BASE_DELAY_MS * 2 ** (attempt - 1), RECONNECT_MAX_DELAY_MS)
          await sleep(delay)
        } finally {
          controllers.current.delete(turnId)
        }
      }
    },
    [dispatchTyped, pumpBody],
  )

  const submit = useCallback(
    (userText: string, opts: LiveSubmitOptions = {}) => {
      const turnId = nextTurnId()
      const openedAtMs = Date.now()
      dispatchTyped({ type: 'CLIENT_SUBMIT_TURN', turnId, userText })

      const adapter = makeS1LiveAdapter(turnId, userText, openedAtMs)
      const cs: TurnConnState = { serverTurnId: null, lastSeq: -1, lastFrameAtMs: openedAtMs, terminal: false, adapter }
      connState.current.set(turnId, cs)

      const ac = new AbortController()
      controllers.current.set(turnId, ac)

      void (async () => {
        try {
          const resp = await fetch('/api/pariprashna', {
            method: 'POST',
            headers: { 'content-type': 'application/json' },
            body: JSON.stringify({
              chartId,
              reading_depth: opts.reading_depth ?? 'auto',
              model_id: opts.model_id,
              length_tier: opts.length_tier,
              messages: [
                {
                  id: `${turnId}-user`,
                  role: 'user',
                  parts: [{ type: 'text', text: userText }],
                },
              ],
            }),
            signal: ac.signal,
          })

          if (!resp.ok || !resp.body) {
            dispatchTyped({
              type: 'error',
              turnId,
              error: {
                kind: 'network',
                bandLabel: 'Something went wrong',
                sentence: `The request failed (${resp.status}).`,
                actions: ['retry'],
              },
              eventId: `${turnId}-httpfail`,
            })
            return
          }

          await pumpBody(resp.body, turnId, cs)
        } catch (err) {
          // AbortError is expected on stop(); everything else is a genuine
          // drop — reconnect via the SAME path a stale-tab return would use.
          if ((err as { name?: string })?.name === 'AbortError') return
          await reconnectLoop(turnId, cs)
        } finally {
          controllers.current.delete(turnId)
        }
      })()

      return turnId
    },
    [chartId, dispatchTyped, pumpBody, reconnectLoop],
  )

  const stop = useCallback(
    (turnId: string) => {
      const cs = connState.current.get(turnId)
      if (cs) cs.terminal = true
      const ac = controllers.current.get(turnId)
      if (ac) ac.abort()
      controllers.current.delete(turnId)
      dispatchTyped({ type: 'CLIENT_STOP', turnId })
    },
    [dispatchTyped],
  )

  // `visibilitychange` reconnect (§ requirement 4): when the tab regains
  // visibility, any tracked turn that has gone quiet for longer than the
  // stall threshold AND hasn't reached a terminal state gets the exact same
  // `reconnectLoop` a thrown network error would trigger — no separate code
  // path, so a "why" never gets special-cased.
  useEffect(() => {
    const onVisible = (): void => {
      if (document.visibilityState !== 'visible') return
      const now = Date.now()
      for (const [turnId, cs] of connState.current.entries()) {
        if (cs.terminal) continue
        if (now - cs.lastFrameAtMs < VISIBILITY_STALL_THRESHOLD_MS) continue
        if (controllers.current.has(turnId)) continue // a fetch is already in flight for this turn
        void reconnectLoop(turnId, cs)
      }
    }
    document.addEventListener('visibilitychange', onVisible)
    return () => document.removeEventListener('visibilitychange', onVisible)
  }, [reconnectLoop])

  return useMemo(() => ({ state, submit, stop }), [state, submit, stop])
}
