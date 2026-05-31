'use client'

/**
 * BuildControlsBar — top-bar build action cluster
 * [PHASE-C-06]
 */

import { useState, useCallback } from 'react'

interface Props {
  chartId: string
  buildId?: string
  buildStatus?: string
  onBuildStart: (buildId?: string) => void
}

type Action = 'build' | 'continue' | 'rebuild-all' | 'stop'

async function postBuildAction(
  action: Action,
  chartId: string,
  buildId?: string,
): Promise<{ ok: boolean; build_id?: string }> {
  const endpoints: Record<Action, string> = {
    'build':       '/api/build/start',
    'continue':    '/api/build/continue',
    'rebuild-all': '/api/build/rebuild-all',
    'stop':        '/api/build/stop',
  }
  const body: Record<string, string> = action === 'stop'
    ? { build_id: buildId ?? '' }
    : { chart_id: chartId }
  const res = await fetch(endpoints[action], {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  return res.json()
}

// [BUILD-ORCH-D-S4] Cancel hits /api/build/cancel/[buildId] (not the stop endpoint)
async function requestCancel(buildId: string): Promise<{ ok: boolean }> {
  const res = await fetch(`/api/build/cancel/${buildId}`, { method: 'POST' })
  return { ok: res.ok }
}

export function BuildControlsBar({ chartId, buildId, buildStatus, onBuildStart }: Props) {
  const [busy, setBusy] = useState(false)
  const [cancelling, setCancelling] = useState(false)

  const execute = useCallback(async (action: Action) => {
    setBusy(true)
    try {
      const result = await postBuildAction(action, chartId, buildId)
      if (result.ok) onBuildStart(result.build_id)
    } finally {
      setBusy(false)
    }
  }, [chartId, buildId, onBuildStart])

  const handleCancel = useCallback(async () => {
    if (!buildId) return
    setCancelling(true)
    try {
      await requestCancel(buildId)
    } finally {
      setCancelling(false)
    }
  }, [buildId])

  const isRunning = buildStatus === 'queued' || buildStatus === 'running' || buildStatus === 'cancelling'
  const isFailed  = buildStatus === 'failed' || buildStatus === 'partial'
  const isDone    = buildStatus === 'success'
  const hasNoBuild = !buildStatus

  return (
    <div data-testid="build-controls-bar" className="flex items-center gap-2">
      {isRunning ? (
        <>
          {/* Running state: stop + cancel buttons */}
          <button
            onClick={() => execute('stop')}
            disabled={busy}
            className="px-4 py-1.5 rounded-lg text-sm text-[#9c3a2a] border border-[#9c3a2a]/40 hover:bg-[#9c3a2a]/10 transition-colors disabled:opacity-50"
          >
            Stop
          </button>
          {buildId && buildStatus !== 'cancelling' && (
            <button
              data-testid="cancel-build-btn"
              onClick={handleCancel}
              disabled={cancelling || busy}
              className="px-4 py-1.5 rounded-lg text-sm text-[#8a8070] border border-[#2a2620] hover:text-[#c8bfb0] hover:bg-[#1a1820] transition-colors disabled:opacity-50"
            >
              {cancelling ? 'Cancelling…' : 'Cancel'}
            </button>
          )}
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
              <button
                onClick={() => execute('continue')}
                disabled={busy}
                className="px-4 py-1.5 rounded-lg text-sm border border-[#d4a648] text-[#d4a648] hover:bg-[#d4a648]/10 transition-colors disabled:opacity-50"
              >
                Continue Build
              </button>
              <button
                onClick={() => execute('rebuild-all')}
                disabled={busy}
                className="px-4 py-1.5 rounded-lg text-sm text-[#8a8070] hover:text-[#c8bfb0] hover:bg-[#1a1820] transition-colors disabled:opacity-50"
              >
                Rebuild All
              </button>
            </>
          )}
          {isDone && (
            <button
              onClick={() => execute('rebuild-all')}
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
