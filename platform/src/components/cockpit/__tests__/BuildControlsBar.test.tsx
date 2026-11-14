import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
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

describe('controlled action feedback', () => {
  afterEach(() => { vi.unstubAllGlobals(); vi.restoreAllMocks() })

  it.each([
    ['permission refusal', () => Promise.resolve({ ok: false, json: async () => ({ error: 'PRIVATE_SERVER_DETAIL' }) })],
    ['service refusal', () => Promise.resolve({ ok: false, json: async () => ({ error: { internal: 'PRIVATE_SERVER_DETAIL' } }) })],
    ['invalid JSON', () => Promise.resolve({ ok: true, json: async () => { throw new SyntaxError('PRIVATE_SERVER_DETAIL') } })],
    ['network failure', () => Promise.reject(new Error('PRIVATE_SERVER_DETAIL'))],
    ['null response', () => Promise.resolve({ ok: true, json: async () => null })],
    ['missing run ID', () => Promise.resolve({ ok: true, json: async () => ({ data: {} }) })],
    ['invalid run ID', () => Promise.resolve({ ok: true, json: async () => ({ data: { run_id: 42 } }) })],
  ])('shows a generic error after settled %s and preserves retry', async (_name, reply) => {
    const fetch = vi.fn(reply)
    vi.stubGlobal('fetch', fetch)
    const onBuildStart = vi.fn()
    render(<BuildControlsBar chartId="synthetic-chart" onBuildStart={onBuildStart} />)
    const button = screen.getByRole('button', { name: 'Build Chart' })
    // Settle the actual event promise; absence of feedback must fail an assertion,
    // rather than waiting for a response or alert that may never arrive.
    await act(async () => { fireEvent.click(button); await Promise.resolve(); await Promise.resolve() })
    expect(button).not.toBeDisabled()
    expect(screen.getByRole('alert')).toHaveTextContent('Unable to start this build. Please try again.')
    expect(document.body.textContent).not.toContain('PRIVATE_SERVER_DETAIL')
    expect(onBuildStart).not.toHaveBeenCalled()
    expect(fetch).toHaveBeenCalledTimes(1)
  })

  it('clears a failed action message after a successful retry with the exact run ID', async () => {
    const fetch = vi.fn()
      .mockResolvedValueOnce({ ok: false, json: async () => ({ error: 'private' }) })
      .mockResolvedValueOnce({ ok: true, json: async () => ({ data: { run_id: 'exact-synthetic-run' } }) })
    vi.stubGlobal('fetch', fetch)
    const onBuildStart = vi.fn()
    render(<BuildControlsBar chartId="synthetic-chart" onBuildStart={onBuildStart} />)
    const button = screen.getByRole('button', { name: 'Build Chart' })
    await act(async () => { fireEvent.click(button) })
    expect(screen.getByRole('alert')).toBeTruthy()
    await act(async () => { fireEvent.click(button) })
    expect(screen.queryByRole('alert')).toBeNull()
    expect(onBuildStart).toHaveBeenCalledExactlyOnceWith('exact-synthetic-run')
    expect(fetch).toHaveBeenCalledTimes(2)
  })

  it('settles a failed stop without changing the known run', async () => {
    vi.stubGlobal('fetch', mockFetchOnce(403, { error: 'PRIVATE_SERVER_DETAIL' }))
    const onBuildStart = vi.fn()
    render(<BuildControlsBar chartId="synthetic-chart" buildId="known-run" buildStatus="running" onBuildStart={onBuildStart} />)
    await act(async () => { fireEvent.click(screen.getByRole('button', { name: 'Stop' })) })
    expect(screen.getByRole('alert')).toHaveTextContent('Unable to stop this build. Please try again.')
    expect(onBuildStart).not.toHaveBeenCalled()
  })

  it('retains a successful stop without an echoed run ID', async () => {
    vi.stubGlobal('fetch', mockFetchOnce(200, { data: { stop_requested: true } }))
    const onBuildStart = vi.fn()
    render(<BuildControlsBar chartId="synthetic-chart" buildId="known-run" buildStatus="running" onBuildStart={onBuildStart} />)
    await act(async () => { fireEvent.click(screen.getByRole('button', { name: 'Stop' })) })
    expect(screen.queryByRole('alert')).toBeNull()
    expect(onBuildStart).not.toHaveBeenCalled()
    expect(screen.getByRole('button', { name: 'Stop' })).not.toBeDisabled()
  })
})
