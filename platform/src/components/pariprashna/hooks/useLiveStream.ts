'use client'

import { useCallback, useMemo, useReducer, useRef } from 'react'
import { threadReducer, initialThreadState } from '../state/reducer'
import type { ThreadAction } from '../state/reducer'
import { decodeEvent } from '@/lib/pariprashna/protocol/events'
import { makeS1LiveAdapter } from '../state/s1LiveAdapter'

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
 * LIVE transport: opens a real SSE stream against `/api/pariprashna` (lane
 * S-1's route) and dispatches decoded, adapted events at the reducer.
 *
 * This is the production-path sibling of `useFixtureStream` (which replays
 * canned event arrays for local dev / component work). Both return the SAME
 * `{ state, submit, stop }` shape, so `PariprashnaApp` can host either without
 * knowing which transport is live.
 *
 * Flow per turn:
 *   1. mint a client turnId + dispatch optimistic CLIENT_SUBMIT_TURN (§5.3).
 *   2. POST { chartId, messages:[user text], reading_depth, … } to the route.
 *   3. read the SSE body as a stream, split on the `\n\n` frame boundary,
 *      pull each frame's `data:` payload, decode with S-1's `decodeEvent`
 *      (returns null — never throws — on a garbled/unknown frame, which we
 *      skip), adapt to WireEvent(s) via `makeS1LiveAdapter`, and dispatch.
 *   4. an AbortController lets `stop()` cancel the in-flight fetch and settle
 *      the turn as interrupted (keeping whatever already arrived).
 */
export function useLiveStream(chartId: string) {
  const [state, dispatch] = useReducer(threadReducer, initialThreadState)
  const controllers = useRef(new Map<string, AbortController>())
  const dispatchTyped = dispatch as (a: ThreadAction) => void

  const submit = useCallback(
    (userText: string, opts: LiveSubmitOptions = {}) => {
      const turnId = nextTurnId()
      const openedAtMs = Date.now()
      dispatchTyped({ type: 'CLIENT_SUBMIT_TURN', turnId, userText })

      const adapter = makeS1LiveAdapter(turnId, userText, openedAtMs)
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

          const reader = resp.body.getReader()
          const decoder = new TextDecoder()
          let buffer = ''

          // Standard SSE framing: events separated by a blank line ("\n\n").
          for (;;) {
            const { value, done } = await reader.read()
            if (done) break
            buffer += decoder.decode(value, { stream: true })

            let sep: number
            while ((sep = buffer.indexOf('\n\n')) !== -1) {
              const frame = buffer.slice(0, sep)
              buffer = buffer.slice(sep + 2)
              const dataLine = frame
                .split('\n')
                .find((l) => l.startsWith('data:'))
              if (!dataLine) continue
              const payload = dataLine.slice(dataLine.indexOf(':') + 1).trimStart()
              const decoded = decodeEvent(payload)
              if (!decoded) continue // skip garbled/unknown frame (never throws)
              for (const wire of adapter.map(decoded)) {
                dispatchTyped(wire)
              }
            }
          }
        } catch (err) {
          // AbortError is expected on stop(); everything else surfaces in-band.
          if ((err as { name?: string })?.name === 'AbortError') return
          dispatchTyped({
            type: 'error',
            turnId,
            error: {
              kind: 'network',
              bandLabel: 'Reconnecting…',
              sentence: 'The connection was interrupted.',
              actions: ['retry'],
            },
            eventId: `${turnId}-neterr`,
          })
        } finally {
          controllers.current.delete(turnId)
        }
      })()

      return turnId
    },
    [chartId, dispatchTyped],
  )

  const stop = useCallback(
    (turnId: string) => {
      const ac = controllers.current.get(turnId)
      if (ac) ac.abort()
      controllers.current.delete(turnId)
      dispatchTyped({ type: 'CLIENT_STOP', turnId })
    },
    [dispatchTyped],
  )

  return useMemo(() => ({ state, submit, stop }), [state, submit, stop])
}
