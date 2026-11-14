import { describe, it, expect, vi, afterEach } from 'vitest'
import { act, fireEvent, render, screen } from '@testing-library/react'
import { CockpitShell } from '../CockpitShell'
import { LiveBuildGraph } from '../LiveBuildGraph'
import { AssetTable } from '../AssetTable'

vi.mock('../LiveBuildGraph', () => ({ LiveBuildGraph: vi.fn(() => <div data-testid="retained-graph-boundary" />) }))
vi.mock('../AssetTable', () => ({ AssetTable: vi.fn(() => <div data-testid="retained-assets-boundary" />) }))
const props = { chartId: 'synthetic-chart', chartName: 'Synthetic', birthDate: '', birthTime: '', birthPlace: '' }
const build = (status: string) => ({ build_id: 'previous-run', status, created_at: '2026-01-01T00:00:00Z', ayanamshas: ['synthetic-frame'] })
afterEach(() => { vi.unstubAllGlobals(); vi.restoreAllMocks() })

describe('current and retained status disclosure', () => {
  it.each([
    ['planned', 'PLANNED'], ['running', 'BUILDING'], ['paused', 'PAUSED'], ['completed', 'COMPLETE'],
    ['failed', 'FAILED'], ['stopped', 'STOPPED'], ['queued', 'BUILDING'], ['success', 'COMPLETE'],
    ['partial', 'PARTIAL'], ['cancelled', 'STOPPED'],
  ])('renders %s as %s without a request', (state, label) => {
    const fetch = vi.fn(() => { throw new Error('unexpected fetch') })
    vi.stubGlobal('fetch', fetch)
    render(<CockpitShell {...props} latestBuild={build(state)} />)
    expect(screen.getAllByText(label)).toHaveLength(2)
    expect(fetch).not.toHaveBeenCalled()
    expect(screen.getByTestId('retained-graph-boundary')).toBeTruthy()
  })

  it('preserves the initial no-build state and available build action', () => {
    render(<CockpitShell {...props} latestBuild={null} />)
    expect(screen.getByText('IDLE')).toBeTruthy()
    expect(screen.getByText('No builds yet.')).toBeTruthy()
    expect(screen.getByRole('button', { name: 'Build Chart' })).toBeTruthy()
  })
})

describe('acknowledged request is not observed execution', () => {
  it.each([null, build('completed')])('uses pending state without inheriting or fabricating run metadata', async latestBuild => {
    const fetch = vi.fn().mockResolvedValue({ ok: true, json: async () => ({ data: { run_id: 'new-run' } }) })
    vi.stubGlobal('fetch', fetch)
    render(<CockpitShell {...props} latestBuild={latestBuild} />)
    const name = latestBuild ? 'Rebuild All' : 'Build Chart'
    await act(async () => { fireEvent.click(screen.getByRole('button', { name })) })
    expect(screen.getAllByText('PENDING')).toHaveLength(2)
    expect(screen.queryByText('BUILDING')).toBeNull()
    expect(screen.getByText('Not yet available')).toBeTruthy()
    expect(screen.getByRole('status')).toHaveTextContent('Request accepted. Refresh the page for the current run status.')
    expect(fetch).toHaveBeenCalledExactlyOnceWith('/api/cockpit/runs', expect.objectContaining({
      method: 'POST', body: JSON.stringify({ chart_id: props.chartId, scope: 'global', action: latestBuild ? 'rebuild' : 'build' }),
    }))
    expect(screen.queryByRole('button', { name: 'Build Chart' })).toBeNull()
  })

  it('preserves an observed paused state when a stop request echoes the same run', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: async () => ({ data: { run_id: 'previous-run', stop_requested: true } }) }))
    render(<CockpitShell {...props} latestBuild={build('paused')} />)
    await act(async () => { fireEvent.click(screen.getByRole('button', { name: 'Stop' })) })
    expect(screen.getAllByText('PAUSED')).toHaveLength(2)
    expect(screen.queryByText('PENDING')).toBeNull()
    expect(screen.getByRole('status')).toHaveTextContent('Request accepted.')
  })
})

describe('latest build lookup availability', () => {
  it('shows explicit unavailable without implying empty or offering a build against unknown state', () => {
    const fetch = vi.fn(() => { throw new Error('unexpected fetch') })
    const eventSource = vi.fn(() => { throw new Error('unexpected event subscription') })
    vi.stubGlobal('fetch', fetch)
    vi.stubGlobal('EventSource', eventSource)
    render(<CockpitShell {...props} latestBuild={null} latestBuildUnavailable />)
    expect(screen.getByRole('heading', { name: props.chartName })).toBeTruthy()
    expect(screen.getByText('UNAVAILABLE')).toBeTruthy()
    expect(screen.getByRole('status')).toHaveTextContent('Latest build status is temporarily unavailable. Refresh the page to try again.')
    expect(screen.queryByText('IDLE')).toBeNull()
    expect(screen.queryByText('No builds yet.')).toBeNull()
    expect(screen.queryByText('No prior builds.')).toBeNull()
    expect(screen.getByText('Build history is unavailable.')).toBeTruthy()
    expect(screen.queryByRole('button', { name: 'Build Chart' })).toBeNull()
    expect(screen.queryByRole('button', { name: 'Stop' })).toBeNull()
    expect(screen.queryByRole('button', { name: 'Continue Build' })).toBeNull()
    expect(screen.queryByRole('button', { name: 'Rebuild All' })).toBeNull()
    expect(screen.queryByTestId('retained-graph-boundary')).toBeNull()
    expect(fetch).not.toHaveBeenCalled()
    expect(eventSource).not.toHaveBeenCalled()
  })

  it.each([null, build('paused')])('preserves successful empty or known state with explicit false', latestBuild => {
    render(<CockpitShell {...props} latestBuild={latestBuild} latestBuildUnavailable={false} />)
    if (latestBuild) {
      expect(screen.getAllByText('PAUSED')).toHaveLength(2)
      expect(screen.getByRole('button', { name: 'Stop' })).toBeTruthy()
    } else {
      expect(screen.getByText('IDLE')).toBeTruthy()
      expect(screen.getByText('No builds yet.')).toBeTruthy()
      expect(screen.getByRole('button', { name: 'Build Chart' })).toBeTruthy()
    }
    expect(screen.queryByText('UNAVAILABLE')).toBeNull()
  })
})

describe('authoritative refreshed snapshots on the same Shell', () => {
  it('does not mount graph or asset children while the latest lookup is explicitly unknown', () => {
    const graphBefore = vi.mocked(LiveBuildGraph).mock.calls.length
    const assetsBefore = vi.mocked(AssetTable).mock.calls.length
    render(<CockpitShell {...props} latestBuild={null} latestBuildUnavailable />)
    expect(vi.mocked(LiveBuildGraph).mock.calls.length).toBe(graphBefore)
    fireEvent.click(screen.getByRole('button', { name: 'Assets' }))
    expect(vi.mocked(AssetTable).mock.calls.length).toBe(assetsBefore)
    expect(screen.getByText('Build details are temporarily unavailable.')).toBeTruthy()
    expect(screen.queryByRole('button', { name: 'Build Chart' })).toBeNull()
  })

  it('recovers unknown to a fresh paused run without an IDLE or build action', () => {
    const view = render(<CockpitShell {...props} latestBuild={null} latestBuildUnavailable />)
    view.rerender(<CockpitShell {...props} latestBuild={build('paused')} latestBuildUnavailable={false} />)
    expect(screen.getAllByText('PAUSED')).toHaveLength(2)
    expect(screen.getByRole('button', { name: 'Stop' })).toBeTruthy()
    expect(screen.queryByText('IDLE')).toBeNull()
    expect(screen.queryByRole('button', { name: 'Build Chart' })).toBeNull()
    expect(screen.getByTestId('retained-graph-boundary')).toBeTruthy()
  })

  it('makes a refreshed failure authoritative over the prior paused run and Stop control', () => {
    const view = render(<CockpitShell {...props} latestBuild={build('paused')} />)
    view.rerender(<CockpitShell {...props} latestBuild={null} latestBuildUnavailable />)
    expect(screen.getByText('UNAVAILABLE')).toBeTruthy()
    expect(screen.queryByText('PAUSED')).toBeNull()
    expect(screen.queryByRole('button', { name: 'Stop' })).toBeNull()
    expect(screen.queryByTestId('retained-graph-boundary')).toBeNull()
  })

  it('preserves pending on an equivalent parent render, then accepts a fresh observed run', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: async () => ({ data: { run_id: 'new-run' } }) }))
    const view = render(<CockpitShell {...props} latestBuild={null} />)
    await act(async () => { fireEvent.click(screen.getByRole('button', { name: 'Build Chart' })) })
    view.rerender(<CockpitShell {...props} latestBuild={null} latestBuildUnavailable={false} />)
    expect(screen.getAllByText('PENDING')).toHaveLength(2)
    view.rerender(<CockpitShell {...props} latestBuild={{ ...build('paused'), build_id: 'new-run' }} />)
    expect(screen.getAllByText('PAUSED')).toHaveLength(2)
    expect(screen.queryByText('PENDING')).toBeNull()
    expect(screen.queryByText('Request accepted. Refresh the page for the current run status.')).toBeNull()
    expect(fetch).toHaveBeenCalledTimes(1)
  })

  it('does not revive an old pending acknowledgment after unavailable then fresh successful empty', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: async () => ({ data: { run_id: 'new-run' } }) }))
    const view = render(<CockpitShell {...props} latestBuild={null} />)
    await act(async () => { fireEvent.click(screen.getByRole('button', { name: 'Build Chart' })) })
    view.rerender(<CockpitShell {...props} latestBuild={null} latestBuildUnavailable />)
    expect(screen.getByText('UNAVAILABLE')).toBeTruthy()
    view.rerender(<CockpitShell {...props} latestBuild={null} latestBuildUnavailable={false} />)
    expect(screen.getByText('IDLE')).toBeTruthy()
    expect(screen.getByRole('button', { name: 'Build Chart' })).toBeTruthy()
    expect(screen.queryByText('PENDING')).toBeNull()
  })

  it('keeps the selected tab across server snapshot transitions', () => {
    const view = render(<CockpitShell {...props} latestBuild={build('paused')} />)
    fireEvent.click(screen.getByRole('button', { name: 'Assets' }))
    expect(screen.getByTestId('retained-assets-boundary')).toBeTruthy()
    view.rerender(<CockpitShell {...props} latestBuild={null} latestBuildUnavailable />)
    expect(screen.queryByTestId('retained-assets-boundary')).toBeNull()
    view.rerender(<CockpitShell {...props} latestBuild={build('running')} />)
    expect(screen.getByTestId('retained-assets-boundary')).toBeTruthy()
    expect(screen.queryByTestId('retained-graph-boundary')).toBeNull()
  })

  it('ignores a late action acknowledgment from the previous chart snapshot', async () => {
    let complete!: (value: unknown) => void
    vi.stubGlobal('fetch', vi.fn().mockImplementation(() => new Promise(resolve => { complete = resolve })))
    const view = render(<CockpitShell {...props} latestBuild={null} />)
    fireEvent.click(screen.getByRole('button', { name: 'Build Chart' }))
    view.rerender(<CockpitShell {...props} chartId="other-synthetic-chart" latestBuild={build('paused')} />)
    await act(async () => { complete({ ok: true, json: async () => ({ data: { run_id: 'old-chart-run' } }) }) })
    expect(screen.getAllByText('PAUSED')).toHaveLength(2)
    expect(screen.queryByText('PENDING')).toBeNull()
    expect(screen.getByRole('button', { name: 'Stop' })).toBeTruthy()
  })
})

describe('asynchronous acknowledgment across a combined snapshot ABA', () => {
  it('does not accept an old chart A response after A to B to A', async () => {
    let complete!: (value: unknown) => void
    const fetch = vi.fn(() => new Promise(resolve => { complete = resolve }))
    vi.stubGlobal('fetch', fetch)
    const view = render(<CockpitShell {...props} latestBuild={null} />)
    fireEvent.click(screen.getByRole('button', { name: 'Build Chart' }))
    view.rerender(<CockpitShell {...props} chartId="other-synthetic-chart" latestBuild={null} />)
    view.rerender(<CockpitShell {...props} latestBuild={null} />)
    await act(async () => { complete({ ok: true, json: async () => ({ data: { run_id: 'stale-A-run' } }) }) })
    expect(screen.queryByText('PENDING')).toBeNull()
    expect(screen.queryByText('Request accepted. Refresh the page for the current run status.')).toBeNull()
    expect(screen.getByText('IDLE')).toBeTruthy()
    expect(screen.getByRole('button', { name: 'Build Chart' })).not.toBeDisabled()
    expect(fetch).toHaveBeenCalledTimes(1)
  })

  it('does not accept an old response after available to unknown to the same successful empty snapshot', async () => {
    let complete!: (value: unknown) => void
    const fetch = vi.fn(() => new Promise(resolve => { complete = resolve }))
    vi.stubGlobal('fetch', fetch)
    const view = render(<CockpitShell {...props} latestBuild={null} />)
    fireEvent.click(screen.getByRole('button', { name: 'Build Chart' }))
    view.rerender(<CockpitShell {...props} latestBuild={null} latestBuildUnavailable />)
    expect(screen.getByText('UNAVAILABLE')).toBeTruthy()
    view.rerender(<CockpitShell {...props} latestBuild={null} latestBuildUnavailable={false} />)
    await act(async () => { complete({ ok: true, json: async () => ({ data: { run_id: 'stale-empty-run' } }) }) })
    expect(screen.queryByText('PENDING')).toBeNull()
    expect(screen.queryByText('Request accepted. Refresh the page for the current run status.')).toBeNull()
    expect(screen.getByText('IDLE')).toBeTruthy()
    expect(screen.getByRole('button', { name: 'Build Chart' })).not.toBeDisabled()
    expect(fetch).toHaveBeenCalledTimes(1)
  })

  it('accepts an in-flight response across an equivalent parent render with no snapshot transition', async () => {
    let complete!: (value: unknown) => void
    const fetch = vi.fn(() => new Promise(resolve => { complete = resolve }))
    vi.stubGlobal('fetch', fetch)
    const view = render(<CockpitShell {...props} latestBuild={null} />)
    fireEvent.click(screen.getByRole('button', { name: 'Build Chart' }))
    view.rerender(<CockpitShell {...props} latestBuild={null} latestBuildUnavailable={false} />)
    await act(async () => { complete({ ok: true, json: async () => ({ data: { run_id: 'current-request-run' } }) }) })
    expect(screen.getAllByText('PENDING')).toHaveLength(2)
    expect(screen.getByRole('status')).toHaveTextContent('Request accepted.')
    expect(fetch).toHaveBeenCalledTimes(1)
  })
})
