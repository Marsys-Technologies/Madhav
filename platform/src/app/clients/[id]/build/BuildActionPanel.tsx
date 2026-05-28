'use client'

/**
 * BuildActionPanel — Platform Modernization 4.build_trigger (Stream B, 2/3).
 *
 * Thin client component that surfaces the autonomous Build/Rebuild trigger
 * on the per-chart Build page. Posts to POST /api/build/start, then opens
 * an EventSource to GET /api/build/events/[buildId] for progress streaming.
 *
 * Two-level UX (per BRIEF_4_build_trigger §scope):
 *   - Outer: "asset M of N" — current asset name + counter.
 *   - Inner: "stage: X" — within-asset stage label (compute / persist /
 *     verify / commit / etc.).
 *
 * Kill-switch awareness: a 503 response from /start indicates the
 * feature flag is OFF on the server; the panel surfaces that to the
 * operator without retry.
 */

import { useCallback, useEffect, useRef, useState } from 'react'

interface BuildActionPanelProps {
  chartId: string
}

interface BuildEvent {
  asset?: string | null
  asset_index?: number | null
  asset_total?: number | null
  stage?: string | null
  status?: string | null
  message?: string | null
  stage_seq?: number | null
}

type PanelState =
  | { phase: 'idle' }
  | { phase: 'starting' }
  | { phase: 'running'; buildId: string; lastEvent: BuildEvent | null }
  | { phase: 'done'; buildId: string }
  | { phase: 'error'; message: string; status?: number }

export function BuildActionPanel({ chartId }: BuildActionPanelProps): JSX.Element {
  const [state, setState] = useState<PanelState>({ phase: 'idle' })
  const esRef = useRef<EventSource | null>(null)

  // Cleanup on unmount: close any open EventSource to avoid socket leaks.
  useEffect(() => {
    return (): void => {
      if (esRef.current) {
        esRef.current.close()
        esRef.current = null
      }
    }
  }, [])

  const openStream = useCallback((buildId: string): void => {
    const es = new EventSource(`/api/build/events/${buildId}`)
    esRef.current = es

    es.onmessage = (msg): void => {
      try {
        const ev = JSON.parse(msg.data) as BuildEvent
        setState((prev) =>
          prev.phase === 'running'
            ? { ...prev, lastEvent: ev }
            : prev,
        )
        // Terminal status closes the stream.
        if (ev.status === 'complete' || ev.status === 'failed') {
          es.close()
          esRef.current = null
          setState({ phase: 'done', buildId })
        }
      } catch {
        // Tolerate parse failures — keep listening.
      }
    }

    es.onerror = (): void => {
      // EventSource auto-reconnects; we only flag a hard error if the
      // server explicitly closed the stream (readyState === 2).
      if (es.readyState === 2) {
        setState({
          phase: 'error',
          message: 'Build event stream closed unexpectedly.',
        })
        esRef.current = null
      }
    }
  }, [])

  const handleClick = useCallback(async (): Promise<void> => {
    setState({ phase: 'starting' })
    try {
      const res = await fetch('/api/build/start', {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({
          chart_id: chartId,
          ayanamsha_role: 'jh_true_chitra',
        }),
      })
      if (!res.ok) {
        const text = await res.text()
        setState({
          phase: 'error',
          status: res.status,
          message:
            res.status === 503
              ? 'Build trigger is currently disabled (feature flag off).'
              : `Build start failed (${res.status}): ${text}`,
        })
        return
      }
      const body = (await res.json()) as { build_id?: string }
      const buildId = body.build_id
      if (!buildId) {
        setState({ phase: 'error', message: 'Server did not return a build_id.' })
        return
      }
      setState({ phase: 'running', buildId, lastEvent: null })
      openStream(buildId)
    } catch (err) {
      setState({
        phase: 'error',
        message: `Network error: ${(err as Error).message}`,
      })
    }
  }, [chartId, openStream])

  const isStartable = state.phase === 'idle' || state.phase === 'done' || state.phase === 'error'
  const buttonLabel =
    state.phase === 'starting'
      ? 'Starting…'
      : state.phase === 'running'
        ? 'Build in progress'
        : state.phase === 'done'
          ? 'Rebuild'
          : 'Build chart'

  return (
    <section
      data-testid="build-action-panel"
      aria-label="Autonomous chart build trigger"
      className="rounded-md border border-neutral-200 p-4"
    >
      <button
        type="button"
        data-testid="build-action-button"
        onClick={handleClick}
        disabled={!isStartable}
        className="rounded bg-neutral-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
      >
        {buttonLabel}
      </button>

      {state.phase === 'running' && (
        <div
          data-testid="build-progress"
          role="status"
          aria-live="polite"
          className="mt-3 text-sm text-neutral-700"
        >
          {state.lastEvent ? (
            <div className="space-y-1">
              <div data-testid="build-progress-outer">
                Asset{' '}
                {state.lastEvent.asset_index !== null && state.lastEvent.asset_index !== undefined
                  ? state.lastEvent.asset_index
                  : '?'}{' '}
                of{' '}
                {state.lastEvent.asset_total !== null && state.lastEvent.asset_total !== undefined
                  ? state.lastEvent.asset_total
                  : '?'}
                {state.lastEvent.asset ? `: ${state.lastEvent.asset}` : ''}
              </div>
              <div data-testid="build-progress-inner" className="text-neutral-500">
                Stage: {state.lastEvent.stage ?? '—'} ({state.lastEvent.status ?? '—'})
              </div>
              {state.lastEvent.message && (
                <div className="text-xs text-neutral-400">{state.lastEvent.message}</div>
              )}
            </div>
          ) : (
            <div>Waiting for first event…</div>
          )}
        </div>
      )}

      {state.phase === 'done' && (
        <div data-testid="build-done" className="mt-3 text-sm text-emerald-700">
          Build {state.buildId} reached terminal state.
        </div>
      )}

      {state.phase === 'error' && (
        <div data-testid="build-error" role="alert" className="mt-3 text-sm text-red-700">
          {state.message}
        </div>
      )}
    </section>
  )
}

export default BuildActionPanel
