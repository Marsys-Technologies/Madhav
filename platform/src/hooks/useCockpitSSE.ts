'use client'

import { useEffect, useRef } from 'react'

// ── Event shape ────────────────────────────────────────────────────────────────

type AssetState = 'dormant' | 'building' | 'lit' | 'stale' | 'error'
type RunState   = 'planned' | 'running' | 'paused' | 'completed' | 'stopped' | 'failed'

export type CockpitEvent =
  | { type: 'asset.state_change'; asset_id: string; from_state: AssetState; to_state: AssetState }
  | { type: 'asset.progress';     asset_id: string; rows_written: number; expected_rows: number | null }
  | { type: 'asset.substep';      asset_id: string; chart_id: string; substep_key: string; substep_label: string; index: number; total: number; rows_written: number }
  | { type: 'edge.first_signal';  from_asset_id: string; to_asset_id: string }
  | { type: 'run.state_change';   run_id: string; state: RunState }

// ── Hook ──────────────────────────────────────────────────────────────────────

// In dev, cap reconnects to prevent an infinite retry storm when the SSE route
// fails (e.g. no GCP creds). In prod, allow unlimited reconnects.
const MAX_RECONNECT_ATTEMPTS = process.env.NODE_ENV === 'development' ? 5 : Infinity
const MIN_RECONNECT_INTERVAL_MS = 1000

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
    let attemptCount = 0
    let lastAttemptAt = 0

    function resetHeartbeat() {
      if (heartbeatTimeout) clearTimeout(heartbeatTimeout)
      heartbeatTimeout = setTimeout(() => {
        // No event in 60s — assume dead, reconnect
        if (!aborted) { es?.close(); connect() }
      }, 60_000)
    }

    function connect() {
      if (aborted) return

      if (attemptCount >= MAX_RECONNECT_ATTEMPTS) {
        console.warn('[useCockpitSSE] max reconnect attempts reached; giving up')
        return
      }

      const sinceLastAttempt = Date.now() - lastAttemptAt
      if (sinceLastAttempt < MIN_RECONNECT_INTERVAL_MS) {
        setTimeout(connect, MIN_RECONNECT_INTERVAL_MS - sinceLastAttempt)
        return
      }

      attemptCount += 1
      lastAttemptAt = Date.now()

      es = new EventSource(`/api/cockpit/sse?chart_id=${encodeURIComponent(chartId)}`, { withCredentials: true })

      es.addEventListener('hello', () => {
        attemptCount = 0   // reset on successful connection
        retryDelay = 1000
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
      es.addEventListener('asset.substep', (e) => {
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
