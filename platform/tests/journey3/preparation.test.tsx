import { beforeEach, afterEach, describe, expect, it, vi } from 'vitest'
import { render, screen, within, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { AssetRow } from '@/lib/components/cockpit/v2/AssetRow'
import { LayerPanel } from '@/lib/components/cockpit/v2/LayerPanel'
import { preparationLayerState } from '@/lib/components/cockpit/v2/PreparationReadiness'
import { DATA_ASSET, statOf } from './fixtures'

vi.mock('@/hooks/useUserRole', () => ({ useUserRole: () => ({ isSuperAdmin: false }) }))
const rowProps = { chartId: 'fictional-chart', activeRunId: null, activeRunPaused: false, onRunStarted: vi.fn(), preparation: true }
const downstream = { ...DATA_ASSET, asset_id: 'bo_themes', layer: 'bodha', english_name: 'House themes', sanskrit_name: 'Bhāva', depends_on: [DATA_ASSET.asset_id] }

beforeEach(() => vi.clearAllMocks())
afterEach(() => vi.unstubAllGlobals())

describe('Journey 3 truthful preparation', () => {
  it.each(['dormant', 'incomplete', 'blocked', 'stale', 'error', 'service_down'] as const)('does not qualify %s upstream evidence', state => {
    const stats = new Map([
      [DATA_ASSET.asset_id, statOf({ state })],
      [downstream.asset_id, statOf({ state: 'lit' })],
    ])
    expect(preparationLayerState([DATA_ASSET, downstream], stats, 'bodha')).toBe('Preparation incomplete')
  })
  it('requires every upstream status and ignores inactive candidates in the layer total', () => {
    const stats = new Map([[downstream.asset_id, statOf({ state: 'lit' })]])
    const assets = [DATA_ASSET, downstream, { ...downstream, asset_id: 'candidate', is_active: false }]
    expect(preparationLayerState(assets, stats, 'bodha')).toBe('Status unavailable')
    stats.set(DATA_ASSET.asset_id, statOf({ state: 'service_ok' }))
    expect(preparationLayerState(assets, stats, 'bodha')).toBe('Prepared')
    stats.set(DATA_ASSET.asset_id, statOf({ state: 'lit', build_state_stale: true }))
    expect(preparationLayerState(assets, stats, 'bodha')).toBe('Preparation incomplete')
  })
  it('never labels missing status as unbuilt or exposes preparation actions', () => {
    render(<AssetRow {...rowProps} asset={DATA_ASSET} stat={null} />)
    expect(screen.getByText('Status unavailable')).toBeTruthy()
    expect(screen.queryByRole('button')).toBeNull()
    expect(screen.queryByText('NOT BUILT')).toBeNull()
  })
  it('renders an inactive candidate without runnable actions or fabricated Sanskrit', () => {
    render(<AssetRow {...rowProps} asset={{ ...DATA_ASSET, is_active: false, sanskrit_name: DATA_ASSET.asset_id }} stat={null} />)
    expect(screen.getByText('Inactive · not runnable')).toBeTruthy()
    expect(screen.getByText('Sanskrit label pending')).toBeTruthy()
    expect(screen.queryByText(DATA_ASSET.asset_id)).toBeNull()
    expect(screen.queryByRole('button')).toBeNull()
  })
  it('keeps foundation actions restricted to the existing super-admin role', () => {
    render(<LayerPanel preparation defaultExpanded layer="brahmagyan" chartId="fictional-chart" activeRun={null}
      assets={[{ ...DATA_ASSET, layer: 'brahmagyan' }]} stats={new Map([[DATA_ASSET.asset_id, statOf({ state: 'lit' })]])} onRunStarted={vi.fn()} />)
    expect(screen.queryByRole('button', { name: /Rebuild|Refresh|Clear/ })).toBeNull()
  })
})

describe('Journey 3 scoped confirmation', () => {
  function setup() {
    const requests = vi.fn().mockResolvedValueOnce({ ok: true, json: async () => ({ data: {
      status: 'ok', plan_waves: [[DATA_ASSET.asset_id], [downstream.asset_id]], blockers: [], estimated_seconds: 12,
    } }) }).mockResolvedValue({ ok: true, json: async () => ({ data: { plan: [DATA_ASSET.asset_id, downstream.asset_id] } }) })
    vi.stubGlobal('fetch', requests)
    render(<AssetRow {...rowProps} asset={DATA_ASSET} allAssets={[DATA_ASSET, downstream]} stat={statOf({ state: 'lit', actual_rows: 9 })} />)
    return requests
  }
  it('shows named scope and downstream assets, traps focus, and cancels without a run', async () => {
    const requests = setup(), user = userEvent.setup()
    const trigger = screen.getByRole('button', { name: 'Rebuild Planet positions' })
    await user.click(trigger)
    const dialog = await screen.findByRole('dialog', { name: 'Confirm preparation of Planet positions' })
    expect(within(dialog).getByText('House themes')).toBeTruthy()
    expect(within(dialog).getByText('Planet positions')).toBeTruthy()
    expect(document.activeElement).toBe(within(dialog).getByRole('button', { name: 'Cancel' }))
    await user.keyboard('{Shift>}{Tab}{/Shift}')
    expect(document.activeElement).toBe(within(dialog).getByRole('button', { name: 'Build' }))
    await user.keyboard('{Escape}')
    expect(screen.queryByRole('dialog')).toBeNull()
    expect(document.activeElement).toBe(trigger)
    expect(requests).toHaveBeenCalledTimes(1)
    expect(JSON.parse(requests.mock.calls[0][1].body)).toMatchObject({ chart_id: 'fictional-chart', scope: 'asset', scope_target: DATA_ASSET.asset_id, action: 'rebuild' })
  })
  it('starts only the server-resolved selected scope after explicit confirmation', async () => {
    const requests = setup(), user = userEvent.setup()
    await user.click(screen.getByRole('button', { name: 'Rebuild Planet positions' }))
    const dialog = await screen.findByRole('dialog')
    await user.click(within(dialog).getByRole('button', { name: 'Build' }))
    await waitFor(() => expect(requests).toHaveBeenCalledTimes(2))
    expect(requests.mock.calls[1][0]).toBe('/api/cockpit/runs')
    expect(JSON.parse(requests.mock.calls[1][1].body)).toEqual({ chart_id: 'fictional-chart', scope: 'asset', scope_target: DATA_ASSET.asset_id, action: 'rebuild' })
  })
})
