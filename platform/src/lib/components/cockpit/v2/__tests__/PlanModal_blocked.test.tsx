import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { PlanModal } from '../PlanModal'

const CHART_ID = '1c826d5a-41cb-4450-b4dc-59d440e5f75a'
// Exact data shape from the admitted read-only /plan response recorded on
// 2026-11-14 (normal-api-plan-active.json); no build was dispatched.
const BLOCKED_PLAN = {
  blocked: true,
  blockers: [{
    dep_asset_id: 'ka_kshetra',
    dep_state: 'stale',
    required_by: ['mi_bhara', 'mi_sankalpa'],
  }],
  estimated_seconds: null,
  plan_waves: [],
  protected_assets: [],
  status: 'blocked',
}
const PREVIEW_BODY = { chart_id: CHART_ID, scope: 'global', scope_target: null, action: 'build' }
const mockFetch = vi.fn()

function mountModal() {
  const onClose = vi.fn()
  const onRunStarted = vi.fn()
  return {
    ...render(<PlanModal chartId={CHART_ID} scope="global" scopeTarget={null}
      action="build" label="Build all" preparation onClose={onClose} onRunStarted={onRunStarted} />),
    onClose,
    onRunStarted,
  }
}

function expectReadOnlyPreview() {
  expect(mockFetch).toHaveBeenCalledExactlyOnceWith('/api/cockpit/plan', {
    method: 'POST',
    credentials: 'include',
    signal: expect.any(AbortSignal),
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(PREVIEW_BODY),
  })
  expect(screen.queryByRole('button', { name: /Run plan|Clear & Rebuild|Confirm — clear L0/ })).not.toBeInTheDocument()
}

beforeEach(() => {
  mockFetch.mockReset()
  vi.stubGlobal('fetch', mockFetch)
})

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

describe('PlanModal read-only blocked preview', () => {
  it('shows the actual dependency failure without offering or dispatching a run; close/unmount aborts preview', async () => {
    mockFetch.mockResolvedValue(new Response(JSON.stringify({ data: BLOCKED_PLAN }), { status: 200 }))
    const { onClose, onRunStarted, unmount } = mountModal()

    await waitFor(() => expect(screen.getByText(/ka_kshetra is stale; required by mi_bhara, mi_sankalpa/)).toBeVisible())
    expectReadOnlyPreview()
    expect(onRunStarted).not.toHaveBeenCalled()

    fireEvent.click(screen.getByRole('button', { name: 'Close plan' }))
    expect(onClose).toHaveBeenCalledTimes(1)
    unmount()
    expect(mockFetch.mock.calls[0][1].signal.aborted).toBe(true)
    expect(mockFetch).toHaveBeenCalledTimes(1)
    expect(onRunStarted).not.toHaveBeenCalled()
  })

  it('preserves the route precondition message when blocked is true but resolver status is ok', async () => {
    mockFetch.mockResolvedValue(new Response(JSON.stringify({ data: {
      status: 'ok', blocked: true, plan_waves: [['bo_yoga']], estimated_seconds: null,
      blockers: ['chart_facts is empty — build L1 (Gaṇita) layer first'],
    } }), { status: 200 }))
    const { onRunStarted } = mountModal()

    await waitFor(() => expect(screen.getByText(/chart_facts is empty — build L1 \(Gaṇita\) layer first/)).toBeVisible())
    expectReadOnlyPreview()
    expect(onRunStarted).not.toHaveBeenCalled()
  })

  it('still starts a nonblocked plan only after explicit Run plan confirmation', async () => {
    mockFetch.mockResolvedValueOnce(new Response(JSON.stringify({ data: {
      status: 'ok', blockers: [], plan_waves: [['ga_positions']], estimated_seconds: 1,
    } }), { status: 200 }))
    mockFetch.mockResolvedValueOnce(new Response(JSON.stringify({ data: { run_id: 'existing-run' } }), { status: 200 }))
    const { onRunStarted } = mountModal()

    const confirm = await screen.findByRole('button', { name: 'Run plan' })
    expect(mockFetch).toHaveBeenCalledTimes(1)
    expect(onRunStarted).not.toHaveBeenCalled()
    fireEvent.click(confirm)

    await waitFor(() => expect(onRunStarted).toHaveBeenCalledExactlyOnceWith('existing-run'))
    expect(mockFetch).toHaveBeenCalledTimes(2)
    expect(mockFetch).toHaveBeenLastCalledWith('/api/cockpit/runs', {
      method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...PREVIEW_BODY, clear_before: false }),
    })
  })

  it('aborts an unresolved preview when unmounted without making another request', () => {
    mockFetch.mockReturnValue(new Promise(() => {}))
    const { unmount, onRunStarted } = mountModal()
    expectReadOnlyPreview()
    const signal = mockFetch.mock.calls[0][1].signal as AbortSignal
    expect(signal.aborted).toBe(false)

    unmount()
    expect(signal.aborted).toBe(true)
    expect(mockFetch).toHaveBeenCalledTimes(1)
    expect(onRunStarted).not.toHaveBeenCalled()
  })

  it('confirms the same through-Bodha assets without pre-clearing the chart', async () => {
    const ids = ['ga_positions', 'bo_laksana']
    const body = { chart_id: CHART_ID, scope: 'asset_set', scope_target: ids.join(','), action: 'rebuild' }
    mockFetch.mockResolvedValueOnce(new Response(JSON.stringify({ data: {
      status: 'ok', blockers: [], plan_waves: ids.map(id => [id]), estimated_seconds: 1,
      downstream_may_become_stale: ['ka_kshetra'],
      duration_history: {
        sample_count: 0, last_seconds: null, lower_seconds: null, upper_seconds: null,
        separate_layers: { ganita: 1619, bodha: 6123 },
      },
    } }), { status: 200 }))
    mockFetch.mockResolvedValueOnce(new Response(JSON.stringify({ data: { run_id: 'preparation-run' } })))
    const onRunStarted = vi.fn()
    render(<PlanModal chartId={CHART_ID} scope="asset_set" scopeTarget={ids.join(',')}
      action="rebuild" label="Rebuild through Bodha" preparation onClose={vi.fn()} onRunStarted={onRunStarted} />)
    expect(await screen.findByText(/may need a later refresh: ka_kshetra/)).toBeVisible()
    expect(screen.getByText(/Previous separate rebuilds through verification \(Gaṇita 27m, Bodha 1h 42m\)/)).toBeVisible()
    expect(mockFetch.mock.calls[0][0]).toBe('/api/cockpit/plan')
    expect(JSON.parse(mockFetch.mock.calls[0][1].body)).toEqual({ ...body, preparation: true })
    fireEvent.click(screen.getByRole('button', { name: /^Rebuild$/ }))
    await waitFor(() => expect(onRunStarted).toHaveBeenCalledWith('preparation-run'))
    expect(mockFetch.mock.calls[1][0]).toBe('/api/cockpit/runs')
    expect(JSON.parse(mockFetch.mock.calls[1][1].body)).toEqual({
      ...body, clear_before: false, expected_plan: ids, expected_downstream: ['ka_kshetra'],
    })
  })

  it('shows the actual comparable duration on the whole-layer preview', async () => {
    mockFetch.mockResolvedValue(new Response(JSON.stringify({ data: {
      status: 'ok', blockers: [], plan_waves: [['bo_laksana']], estimated_seconds: null,
      duration_history: { sample_count: 1, last_seconds: 6123, lower_seconds: 6123, upper_seconds: 6123 },
    } })))
    render(<PlanModal chartId={CHART_ID} scope="layer" scopeTarget="bodha"
      action="rebuild" label="Rebuild Bodha" preparation onClose={vi.fn()} onRunStarted={vi.fn()} />)
    await waitFor(() => expect(screen.getByText(/Last comparable run took 1h 42m through verification/)).toBeVisible())
    expect(JSON.parse(mockFetch.mock.calls[0][1].body)).toMatchObject({ scope: 'layer', scope_target: 'bodha', preparation: true })
  })
})
