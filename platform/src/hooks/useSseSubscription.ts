'use client'

/**
 * useSseSubscription — lightweight SSE subscription for build graph events.
 *
 * Subscribes to /api/build/events/${buildId} and returns nodes + edges
 * updated as `node_added` / `edge_added` events arrive from Stream B's
 * sidecar dispatcher.
 *
 * Graceful degradation: if the endpoint is unavailable or Stream B has not
 * yet shipped typed events, the hook returns empty arrays and logs a
 * non-fatal warning. No error boundary needed.
 *
 * Stream B R1 dependency: this hook expects the SSE stream to emit events
 * shaped as:
 *   { type: 'node_added', data: { asset_id, layer, status, row_count? } }
 *   { type: 'edge_added', data: { from, to, live? } }
 *
 * Before Stream B's R1 lands on main, the stream will emit existing event
 * types only — the hook handles unknown event types silently (no errors).
 */

import { useEffect, useState, useRef, useCallback } from 'react'
import type { GraphNode, GraphEdge } from '@/components/cockpit/LiveDependencyGraph'

export interface SseState {
  nodes: GraphNode[]
  edges: GraphEdge[]
  connected: boolean
}

const INITIAL: SseState = { nodes: [], edges: [], connected: false }

export function useSseSubscription(buildId: string | null): SseState {
  const [state, setState] = useState<SseState>(INITIAL)
  const esRef = useRef<EventSource | null>(null)

  const reset = useCallback(() => {
    setState(INITIAL)
  }, [])

  useEffect(() => {
    if (!buildId) {
      reset()
      return
    }

    const url = `/api/build/events/${buildId}`
    const es = new EventSource(url)
    esRef.current = es

    es.onopen = () => {
      setState((prev) => ({ ...prev, connected: true }))
    }

    es.onerror = () => {
      // Non-fatal — stream may not be available yet (pre-Stream-B-R1 baseline)
      setState((prev) => ({ ...prev, connected: false }))
    }

    es.onmessage = (event) => {
      let payload: { type: string; data: Record<string, unknown> }
      try {
        payload = JSON.parse(event.data)
      } catch {
        return
      }

      if (payload.type === 'node_added') {
        const d = payload.data as GraphNode
        setState((prev) => {
          // deduplicate by asset_id
          const exists = prev.nodes.some((n) => n.asset_id === d.asset_id)
          if (exists) {
            // update status in place
            return {
              ...prev,
              nodes: prev.nodes.map((n) =>
                n.asset_id === d.asset_id ? { ...n, ...d } : n,
              ),
            }
          }
          return { ...prev, nodes: [...prev.nodes, d] }
        })
      } else if (payload.type === 'edge_added') {
        const d = payload.data as GraphEdge
        setState((prev) => {
          const exists = prev.edges.some(
            (e) => e.from === d.from && e.to === d.to,
          )
          if (exists) return prev
          return { ...prev, edges: [...prev.edges, d] }
        })
      }
      // unknown event types are silently ignored (pre-Stream-B-R1 tolerance)
    }

    return () => {
      es.close()
      esRef.current = null
    }
  }, [buildId, reset])

  return state
}
