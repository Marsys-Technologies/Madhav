import { afterEach, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import type { ActiveRun } from '@/hooks/useActiveRun'
import { CockpitShell } from '@/lib/components/cockpit/v2/CockpitShell'

const fixture = vi.hoisted(() => ({
  run: null as ActiveRun | null,
  stats: new Map(),
  refresh: vi.fn(),
}))
vi.mock('@/hooks/useAssetRegistry', async () => {
  const { DATA_ASSET } = await import('./fixtures')
  const result = { assets: [DATA_ASSET], isLoading: false, error: null, refetch: fixture.refresh }
  return { useAssetRegistry: () => result }
})
vi.mock('@/hooks/useAssetStats', () => ({ useAssetStats: () => ({
  stats: fixture.stats, lastFetched: null, error: 'HTTP 503', refetch: fixture.refresh, refetchLive: fixture.refresh,
}) }))
vi.mock('@/hooks/useActiveRun', () => ({ useActiveRun: () => ({ run: fixture.run, assets: [], refresh: fixture.refresh }) }))
vi.mock('@/hooks/useChartContext', () => ({ useChartContext: () => ({ chartName: 'Fictional Native' }) }))
vi.mock('@/hooks/useCockpitSSE', () => ({ useCockpitSSE: vi.fn() }))
vi.mock('@/hooks/useUserRole', () => ({ useUserRole: () => ({ isSuperAdmin: false }) }))
afterEach(() => vi.unstubAllGlobals())

it.each(['running', 'paused'])('keeps %s run controls available during a status outage without allowing a new build', async state => {
  fixture.run = { id: 'fictional-run', scope: 'asset', scope_target: 'fixture', action: 'build', state,
    plan: ['fixture'], current_asset_id: 'fixture', created_at: '2026-10-05T19:00:00Z', started_at: null,
    pause_requested_at: null, stop_requested_at: null }
  const requests = vi.fn()
  vi.stubGlobal('fetch', requests)
  vi.stubGlobal('matchMedia', vi.fn().mockReturnValue({ matches: false, addEventListener: vi.fn(), removeEventListener: vi.fn() }))
  const { rerender } = render(<CockpitShell chartId="fictional-chart" variant="preparation" />)
  expect(screen.getByRole('alert').textContent).toContain('unavailable')
  expect(screen.getByRole('button', { name: state === 'paused' ? /Resume/ : /Pause/ }).hasAttribute('disabled')).toBe(false)
  const user = userEvent.setup()
  await user.click(screen.getByRole('button', { name: /Stop/ }))
  expect(screen.getByRole('button', { name: 'Confirm stop' })).toBeTruthy()
  await user.click(screen.getByRole('button', { name: 'Cancel' }))
  expect(requests).not.toHaveBeenCalled()
  fixture.run = null
  rerender(<CockpitShell chartId="fictional-chart" variant="preparation" />)
  expect(screen.queryByRole('button', { name: /Pause|Resume|Stop|Build|Rebuild/ })).toBeNull()
})
