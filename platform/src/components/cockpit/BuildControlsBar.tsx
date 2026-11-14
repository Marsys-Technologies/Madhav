'use client'

/**
 * BuildControlsBar — top-bar build action cluster
 * [PHASE-C-06]
 *
 * R6 fix: this component previously called /api/build/start (410 GONE — decommissioned)
 * and /api/build/rebuild-all (a stub that only inserts an unprocessed build_events row,
 * never actually invokes a build) — clicking any button here silently did nothing or
 * logged a dead event. The real, current build-orchestration endpoint is
 * POST /api/cockpit/runs (chart_id/scope/action, invokes the Cloud Run job, returns
 * {data:{run_id,...}}), and stopping a run is POST /api/cockpit/runs/[id]/stop. The old
 * status checks ('queued'/'success'/'partial'/'cancelling') also never matched the real
 * build_runs.state enum (planned/running/paused/completed/failed/stopped) — fixed below.
 */

import { useState, useCallback } from 'react'

interface Props {
  chartId: string
  buildId?: string
  buildStatus?: string
  onBuildStart: (buildId?: string) => void
}

type Action = 'build' | 'rebuild' | 'stop'

function actionError(action: Action): string {
  return action === 'stop'
    ? 'Unable to stop this build. Please try again.'
    : 'Unable to start this build. Please try again.'
}

function actionResult(body: unknown, ok: boolean, action: Action): { run_id?: string; error?: string } {
  if (!ok || !body || typeof body !== 'object' || Array.isArray(body)) {
    return { error: actionError(action) }
  }
  const data = (body as { data?: { run_id?: unknown } }).data
  const runId = data?.run_id
  if (typeof runId === 'string' && runId.trim()) return { run_id: runId }
  // A successful stop may acknowledge the request without echoing the run ID.
  return action === 'stop' ? {} : { error: actionError(action) }
}

async function postBuildAction(
  action: Action,
  chartId: string,
  buildId?: string,
): Promise<{ run_id?: string; error?: string }> {
  if (action === 'stop') {
    const res = await fetch(`/api/cockpit/runs/${buildId ?? ''}/stop`, { method: 'POST' })
    const body = await res.json()
    return actionResult(body, res.ok, action)
  }
  const res = await fetch('/api/cockpit/runs', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ chart_id: chartId, scope: 'global', action }),
  })
  const body = await res.json()
  return actionResult(body, res.ok, action)
}

export function BuildControlsBar({ chartId, buildId, buildStatus, onBuildStart }: Props) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const execute = useCallback(async (action: Action) => {
    setBusy(true)
    setError(null)
    try {
      const result = await postBuildAction(action, chartId, buildId)
      if (result.error) setError(result.error)
      else if (result.run_id) onBuildStart(result.run_id)
    } catch {
      setError(actionError(action))
    } finally {
      setBusy(false)
    }
  }, [chartId, buildId, onBuildStart])

  const isRunning = buildStatus === 'planned' || buildStatus === 'running' || buildStatus === 'paused'
  const isFailed  = buildStatus === 'failed' || buildStatus === 'stopped'
  const isDone    = buildStatus === 'completed'
  const hasNoBuild = !buildStatus

  return (
    <div className="flex flex-wrap items-center gap-2">
      {error && <p role="alert" className="w-full text-sm text-[var(--danger)]">{error}</p>}
      {isRunning ? (
        <>
          {/* Running state: stop button + breathing pill already shown in top bar */}
          <button
            onClick={() => execute('stop')}
            disabled={busy}
            className="px-4 py-1.5 rounded-lg text-sm text-[#9c3a2a] border border-[#9c3a2a]/40 hover:bg-[#9c3a2a]/10 transition-colors disabled:opacity-50"
          >
            Stop
          </button>
        </>
      ) : (
        <>
          {hasNoBuild && (
            <button
              onClick={() => execute('build')}
              disabled={busy}
              className="px-5 py-2 rounded-lg text-sm bg-[#d4a648] text-[#08070a] hover:bg-[#e8c878] font-semibold transition-colors disabled:opacity-50"
            >
              Build Chart
            </button>
          )}
          {isFailed && (
            <>
              {/* action='build' only targets assets still dormant/error — the real
                  equivalent of "continue": already-lit assets from the failed run are
                  skipped, not rebuilt. */}
              <button
                onClick={() => execute('build')}
                disabled={busy}
                className="px-4 py-1.5 rounded-lg text-sm border border-[#d4a648] text-[#d4a648] hover:bg-[#d4a648]/10 transition-colors disabled:opacity-50"
              >
                Continue Build
              </button>
              <button
                onClick={() => execute('rebuild')}
                disabled={busy}
                className="px-4 py-1.5 rounded-lg text-sm text-[#8a8070] hover:text-[#c8bfb0] hover:bg-[#1a1820] transition-colors disabled:opacity-50"
              >
                Rebuild All
              </button>
            </>
          )}
          {isDone && (
            <button
              onClick={() => execute('rebuild')}
              disabled={busy}
              className="px-4 py-1.5 rounded-lg text-sm text-[#8a8070] hover:text-[#c8bfb0] hover:bg-[#1a1820] transition-colors disabled:opacity-50"
            >
              Rebuild All
            </button>
          )}
        </>
      )}
    </div>
  )
}
