'use client'

import { useEffect, useRef } from 'react'

// ── Event shape ────────────────────────────────────────────────────────────────

type AssetState = 'dormant' | 'building' | 'lit' | 'stale' | 'error'
type RunState   = 'planned' | 'running' | 'paused' | 'completed' | 'stopped' | 'failed'

export type CockpitEvent =
  | { type: 'asset.state_change'; asset_id: string; from_state: AssetState; to_state: AssetState }
  | { type: 'asset.progress';     asset_id: string; rows_written: number; expected_rows: number | null }
  | { type: 'edge.first_signal';  from_asset_id: string; to_asset_id: string }
  | { type: 'run.state_change';   run_id: string; state: RunState }

// ── Hook ──────────────────────────────────────────────────────────────────────

export function useCockpitSSE(
  chartId: string,
  onEvent: (e: CockpitEvent) => void
): void {
  const onEventRef = useRef(onEvent)
  onEventRef.current = onEvent

  useEffect(() => {
    let es: EventSource | null = null
    let retryDelay = 1000     // start at 1s
    let aborted = false
    let heartbeatTimeout: ReturnType<typeof setTimeout> | null = null

    function resetHeartbeat() {
      if (heartbeatTimeout) clearTimeout(heartbeatTimeout)
      heartbeatTimeout = setTimeout(() => {
        // No event in 60s — assume dead, reconnect
        if (!aborted) { es?.close(); connect() }
      }, 60_000)
    }

    function connect() {
      if (aborted) return
      es = new EventSource(`/api/cockpit/sse?chart_id=${encodeURIComponent(chartId)}`, { withCredentials: true })

      es.addEventListener('hello', () => {
        retryDelay = 1000  // reset on successful connect
        resetHeartbeat()
      })

      es.addEventListener('asset.state_change', (e) => {
        resetHeartbeat()
        try { onEventRef.current(JSON.parse((e as MessageEvent).data) as CockpitEvent) } catch { /* ignore */ }
      })
      es.addEventListener('asset.progress', (e) => {
        resetHeartbeat()
        try { onEventRef.current(JSON.parse((e as MessageEvent).data) as CockpitEvent) } catch { /* ignore */ }
      })
      es.addEventListener('edge.first_signal', (e) => {
        resetHeartbeat()
        try { onEventRef.current(JSON.parse((e as MessageEvent).data) as CockpitEvent) } catch { /* ignore */ }
      })
      es.addEventListener('run.state_change', (e) => {
        resetHeartbeat()
        try { onEventRef.current(JSON.parse((e as MessageEvent).data) as CockpitEvent) } catch { /* ignore */ }
      })

      es.onerror = () => {
        es?.close()
        if (!aborted) {
          setTimeout(() => { connect() }, retryDelay)
          retryDelay = Math.min(retryDelay * 2, 30_000)  // backoff, cap 30s
        }
      }

      resetHeartbeat()
    }

    connect()

    return () => {
      aborted = true
      if (heartbeatTimeout) clearTimeout(heartbeatTimeout)
      es?.close()
    }
  }, [chartId])
}
