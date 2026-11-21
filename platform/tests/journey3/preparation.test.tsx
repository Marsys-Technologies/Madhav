import { beforeEach, afterEach, describe, expect, it, vi } from 'vitest'
import { render, screen, within, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { CockpitShell } from '@/lib/components/cockpit/v2/CockpitShell'
import { DataAssetsView } from '@/lib/components/cockpit/v2/DataAssetsView'
import type { ActiveRun } from '@/hooks/useActiveRun'
import type { AssetRow as RegistryAssetRow } from '@/hooks/useAssetRegistry'
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
  it.each([
    ['dormant', 'Preparation incomplete'],
    ['incomplete', 'Preparation incomplete'],
    ['blocked', 'Preparation incomplete'],
    ['stale', 'Needs refresh'],
    ['error', 'Preparation needs a retry'],
    ['service_down', 'Preparation incomplete'],
  ] as const)('does not qualify %s upstream evidence', (state, label) => {
    const stats = new Map([
      [DATA_ASSET.asset_id, statOf({ state })],
      [downstream.asset_id, statOf({ state: 'lit' })],
    ])
    expect(preparationLayerState([DATA_ASSET, downstream], stats, 'bodha')).toBe(label)
  })
  it('requires every upstream status and ignores inactive candidates in the layer total', () => {
    const stats = new Map([[downstream.asset_id, statOf({ state: 'lit' })]])
    const assets = [DATA_ASSET, downstream, { ...downstream, asset_id: 'candidate', is_active: false }]
    expect(preparationLayerState(assets, stats, 'bodha')).toBe('Status unavailable')
    stats.set(DATA_ASSET.asset_id, statOf({ state: 'service_ok' }))
    expect(preparationLayerState(assets, stats, 'bodha')).toBe('Prepared')
    expect(preparationLayerState(assets, stats, 'bodha', new Set([DATA_ASSET.asset_id]))).toBe('Preparation in progress')
    expect(preparationLayerState(assets, stats, 'bodha', new Set(['unrelated_asset']))).toBe('Prepared')
    stats.set(DATA_ASSET.asset_id, statOf({ state: 'lit', build_state_stale: true }))
    expect(preparationLayerState(assets, stats, 'bodha')).toBe('Needs refresh')
  })
  it('never labels missing status as unbuilt or exposes preparation actions', () => {
    render(<AssetRow {...rowProps} asset={DATA_ASSET} stat={null} />)
    expect(screen.getByText('Status unavailable')).toBeTruthy()
    expect(screen.queryByRole('button')).toBeNull()
    expect(screen.queryByText('NOT BUILT')).toBeNull()
    expect(screen.getByTitle('Last build not recorded')).toBeTruthy()
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
  it('names assets outside the selected layer in the server-resolved layer plan', async () => {
    const requests = vi.fn().mockResolvedValue({ ok: true, json: async () => ({ data: {
      status: 'ok', plan_waves: [[DATA_ASSET.asset_id], [downstream.asset_id]], blockers: [], estimated_seconds: 12,
    } }) })
    vi.stubGlobal('fetch', requests)
    render(<LayerPanel preparation defaultExpanded layer="ganita" chartId="fictional-chart" activeRun={null}
      assets={[DATA_ASSET]} allAssets={[DATA_ASSET, downstream]} stats={new Map([[DATA_ASSET.asset_id, statOf({ state: 'lit' })]])} onRunStarted={vi.fn()} />)
    const user = userEvent.setup()
    await user.click(screen.getByRole('button', { name: 'Rebuild Gaṇita' }))
    const dialog = await screen.findByRole('dialog', { name: 'Rebuild Gaṇita plan' })
    expect(within(dialog).getAllByText('House themes')).toHaveLength(2) // list and dependency diagram
    await user.click(within(dialog).getByRole('button', { name: 'Cancel' }))
    expect(requests).toHaveBeenCalledTimes(1)
    expect(JSON.parse(requests.mock.calls[0][1].body).action).toBe('rebuild')
  })
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

const pane = vi.hoisted(() => ({
  assets: [] as RegistryAssetRow[],
  run: null as ActiveRun | null,
  stats: new Map<string, ReturnType<typeof statOf>>(),
  lastFetched: new Date('2026-01-01T00:00:00Z'),
  refetchRegistry: vi.fn(),
  refetchStats: vi.fn(),
  refetchLive: vi.fn(),
  refreshRun: vi.fn(),
  subscribe: vi.fn(),
  graph: vi.fn(),
}))

vi.mock('@/hooks/useAssetRegistry', () => ({ useAssetRegistry: () => ({
  assets: pane.assets, isLoading: false, error: null, refetch: pane.refetchRegistry,
}) }))
vi.mock('@/hooks/useAssetStats', () => ({ useAssetStats: () => ({
  stats: pane.stats, lastFetched: pane.lastFetched, error: null,
  refetch: pane.refetchStats, refetchLive: pane.refetchLive,
}) }))
vi.mock('@/hooks/useActiveRun', () => ({ useActiveRun: () => ({ run: pane.run, refresh: pane.refreshRun }) }))
vi.mock('@/hooks/useCockpitSSE', () => ({ useCockpitSSE: pane.subscribe }))
vi.mock('@/hooks/useChartContext', () => ({ useChartContext: () => ({
  chartName: 'Fictional chart', birthDate: null, birthTime: null, birthPlace: null,
}) }))
vi.mock('next/dynamic', () => ({ default: () => pane.graph }))

describe('Journey 3 preparation disclosure', () => {
  const requests = vi.fn(() => { throw new Error('Unexpected request from read-only preparation fixture') })
  const ganita = (state: 'expanded' | 'collapsed') => screen.getByRole('button', { name: `Gaṇita layer, ${state}` })
  const bodha = (state: 'expanded' | 'collapsed') => screen.getByRole('button', { name: `Bodha layer, ${state}` })
  const view = () => render(<DataAssetsView chartId="fictional-chart" variant="preparation"
    activeRun={pane.run} refreshRun={pane.refreshRun} />)

  beforeEach(() => {
    pane.assets = [DATA_ASSET]
    pane.run = null
    pane.stats = new Map([[DATA_ASSET.asset_id, statOf({ state: 'lit' })]])
    vi.stubGlobal('fetch', requests)
    vi.stubGlobal('matchMedia', vi.fn(() => ({ matches: false, addEventListener: vi.fn(), removeEventListener: vi.fn() })))
  })

  afterEach(() => {
    expect(requests).not.toHaveBeenCalled()
    expect(pane.refreshRun).not.toHaveBeenCalled()
    expect(pane.graph).not.toHaveBeenCalled()
  })

  it('reports an empty registry and exposes no asset actions', () => {
    pane.assets = []
    pane.stats = new Map()
    view()
    expect(screen.getByText('No preparation assets are available.')).toBeTruthy()
    const readiness = screen.getByRole('complementary', { name: 'What you can ask now' })
    expect(within(readiness).getByText('Gaṇita · Status unavailable')).toBeTruthy()
    expect(screen.queryByRole('button')).toBeNull()
  })

  it('starts idle layers collapsed and auto-expands only the active run layer', () => {
    pane.assets = [downstream, DATA_ASSET]
    const idle = view()
    expect(ganita('collapsed').getAttribute('aria-expanded')).toBe('false')
    expect(screen.queryByText('Planet positions')).toBeNull()
    idle.unmount()

    pane.run = { id: 'fictional-run', scope: 'layer', scope_target: 'ganita', action: 'rebuild',
      state: 'running', plan: [DATA_ASSET.asset_id], current_asset_id: DATA_ASSET.asset_id,
      created_at: '2026-01-01T00:00:00Z', started_at: null, pause_requested_at: null, stop_requested_at: null }
    view()
    expect(ganita('expanded').getAttribute('aria-expanded')).toBe('true')
    expect(screen.getByText('Planet positions')).toBeTruthy()
    expect(bodha('collapsed').getAttribute('aria-expanded')).toBe('false')
    expect(screen.queryByText('House themes')).toBeNull()
  })

  it('opens the named idle layer and shows its real asset row on first click', async () => {
    view()
    await userEvent.setup().click(ganita('collapsed'))
    expect(ganita('expanded').getAttribute('aria-expanded')).toBe('true')
    expect(screen.getByText('Planet positions')).toBeTruthy()
  })

  it('closes the same idle layer and removes its asset row on second click', async () => {
    view()
    const user = userEvent.setup()
    await user.click(ganita('collapsed'))
    expect(screen.getByText('Planet positions')).toBeTruthy()
    await user.click(ganita('expanded'))
    expect(ganita('collapsed').getAttribute('aria-expanded')).toBe('false')
    await waitFor(() => expect(screen.queryByText('Planet positions')).toBeNull())
  })

  it('renders the preparation toolbar, canonical layers and separate readiness in document order', () => {
    pane.assets = [downstream, DATA_ASSET]
    render(<CockpitShell chartId="fictional-chart" variant="preparation" />)
    const nodes = [screen.getByText('Live chart preparation'), ganita('collapsed'), bodha('collapsed'),
      screen.getByRole('complementary', { name: 'What you can ask now' })]
    for (let index = 1; index < nodes.length; index++) {
      expect(nodes[index - 1].compareDocumentPosition(nodes[index]) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
    }
  })
})
