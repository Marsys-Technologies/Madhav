import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { BuildControlsBar } from '../BuildControlsBar'

/**
 * Locks the R6 fix: this component previously called /api/build/start (410 GONE) and
 * /api/build/rebuild-all (a stub that never invoked a real build) — every button
 * silently did nothing or logged a dead event. It must call the real
 * POST /api/cockpit/runs (chart_id/scope/action) and POST /api/cockpit/runs/[id]/stop,
 * parse the real {data:{run_id}} response shape, and gate its button set on the real
 * build_runs.state enum (planned/running/paused/completed/failed/stopped) — not the
 * old, never-matching queued/success/partial/cancelling strings.
 */

function mockFetchOnce(status: number, body: unknown) {
  return vi.fn().mockResolvedValue({
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  })
}

describe('BuildControlsBar', () => {
  let onBuildStart: (buildId?: string) => void

  beforeEach(() => {
    onBuildStart = vi.fn()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('hasNoBuild: "Build Chart" POSTs /api/cockpit/runs with scope=global, action=build', async () => {
    global.fetch = mockFetchOnce(201, { data: { run_id: 'run-1', plan: ['ga_positions'], asset_count: 1 } })
    render(<BuildControlsBar chartId="chart-1" onBuildStart={onBuildStart} />)

    fireEvent.click(screen.getByText('Build Chart'))

    await waitFor(() => expect(onBuildStart).toHaveBeenCalledWith('run-1'))
    expect(global.fetch).toHaveBeenCalledWith('/api/cockpit/runs', expect.objectContaining({
      method: 'POST',
      body: JSON.stringify({ chart_id: 'chart-1', scope: 'global', action: 'build' }),
    }))
  })

  it('isRunning (state=planned): shows Stop, which POSTs /api/cockpit/runs/[id]/stop', async () => {
    global.fetch = mockFetchOnce(200, { data: { run_id: 'run-2', stop_requested: true } })
    render(<BuildControlsBar chartId="chart-1" buildId="run-2" buildStatus="planned" onBuildStart={onBuildStart} />)

    fireEvent.click(screen.getByText('Stop'))

    await waitFor(() => expect(global.fetch).toHaveBeenCalledWith('/api/cockpit/runs/run-2/stop', { method: 'POST' }))
  })

  it('isRunning (state=running): shows Stop', () => {
    render(<BuildControlsBar chartId="chart-1" buildId="run-2" buildStatus="running" onBuildStart={onBuildStart} />)
    expect(screen.getByText('Stop')).toBeTruthy()
  })

  it('isRunning (state=paused): shows Stop', () => {
    render(<BuildControlsBar chartId="chart-1" buildId="run-2" buildStatus="paused" onBuildStart={onBuildStart} />)
    expect(screen.getByText('Stop')).toBeTruthy()
  })

  it('isFailed (state=failed): "Continue Build" uses action=build (dormant/error only, not a forced rebuild)', async () => {
    global.fetch = mockFetchOnce(201, { data: { run_id: 'run-3' } })
    render(<BuildControlsBar chartId="chart-1" buildId="run-2" buildStatus="failed" onBuildStart={onBuildStart} />)

    fireEvent.click(screen.getByText('Continue Build'))

    await waitFor(() => expect(global.fetch).toHaveBeenCalledWith('/api/cockpit/runs', expect.objectContaining({
      body: JSON.stringify({ chart_id: 'chart-1', scope: 'global', action: 'build' }),
    })))
  })

  it('isFailed (state=failed): "Rebuild All" uses action=rebuild (forces every asset in scope)', async () => {
    global.fetch = mockFetchOnce(201, { data: { run_id: 'run-4' } })
    render(<BuildControlsBar chartId="chart-1" buildId="run-2" buildStatus="failed" onBuildStart={onBuildStart} />)

    fireEvent.click(screen.getByText('Rebuild All'))

    await waitFor(() => expect(global.fetch).toHaveBeenCalledWith('/api/cockpit/runs', expect.objectContaining({
      body: JSON.stringify({ chart_id: 'chart-1', scope: 'global', action: 'rebuild' }),
    })))
  })

  it('isFailed also covers state=stopped (a manually-stopped run offers the same recovery actions as a failed one)', () => {
    render(<BuildControlsBar chartId="chart-1" buildId="run-2" buildStatus="stopped" onBuildStart={onBuildStart} />)
    expect(screen.getByText('Continue Build')).toBeTruthy()
    expect(screen.getByText('Rebuild All')).toBeTruthy()
  })

  it('isDone (state=completed): shows only "Rebuild All", action=rebuild', async () => {
    global.fetch = mockFetchOnce(201, { data: { run_id: 'run-5' } })
    render(<BuildControlsBar chartId="chart-1" buildId="run-2" buildStatus="completed" onBuildStart={onBuildStart} />)

    expect(screen.queryByText('Build Chart')).toBeNull()
    expect(screen.queryByText('Continue Build')).toBeNull()
    fireEvent.click(screen.getByText('Rebuild All'))

    await waitFor(() => expect(global.fetch).toHaveBeenCalledWith('/api/cockpit/runs', expect.objectContaining({
      body: JSON.stringify({ chart_id: 'chart-1', scope: 'global', action: 'rebuild' }),
    })))
  })

  it('does not call onBuildStart when the API returns an error (e.g. 409 RUN_ACTIVE)', async () => {
    global.fetch = mockFetchOnce(409, { error: 'A build is already in progress for this chart', code: 'RUN_ACTIVE' })
    render(<BuildControlsBar chartId="chart-1" onBuildStart={onBuildStart} />)

    fireEvent.click(screen.getByText('Build Chart'))

    await waitFor(() => expect(global.fetch).toHaveBeenCalled())
    expect(onBuildStart).not.toHaveBeenCalled()
  })

  it('never calls the decommissioned legacy endpoints', async () => {
    global.fetch = mockFetchOnce(201, { data: { run_id: 'run-6' } })
    render(<BuildControlsBar chartId="chart-1" onBuildStart={onBuildStart} />)
    fireEvent.click(screen.getByText('Build Chart'))
    await waitFor(() => expect(global.fetch).toHaveBeenCalled())

    const calledUrls = (global.fetch as ReturnType<typeof vi.fn>).mock.calls.map(c => c[0])
    expect(calledUrls).not.toContain('/api/build/start')
    expect(calledUrls).not.toContain('/api/build/rebuild-all')
    expect(calledUrls).not.toContain('/api/build/continue')
    expect(calledUrls).not.toContain('/api/build/stop')
  })
})
