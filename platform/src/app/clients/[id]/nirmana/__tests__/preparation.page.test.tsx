import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import PreparationPage from '../page'

const { mockQuery, mockResolveAccess, mockRedirect, mockCockpit, mockFetch } = vi.hoisted(() => ({
  mockQuery: vi.fn(),
  mockResolveAccess: vi.fn(),
  mockRedirect: vi.fn(),
  mockCockpit: vi.fn(),
  mockFetch: vi.fn(),
}))

vi.mock('@/lib/db/client', () => ({ query: mockQuery }))
vi.mock('@/lib/auth/chart-page-guard', () => ({ resolveChartPageAccess: mockResolveAccess }))
vi.mock('@/lib/components/cockpit/v2/CockpitShell', () => ({ CockpitShell: mockCockpit }))
vi.mock('next/navigation', () => ({
  redirect: mockRedirect,
  usePathname: () => '/clients/fixture/nirmana',
  useRouter: () => ({ push: vi.fn() }),
}))

const CHART_ID = '00000000-0000-4000-8000-000000000001'
const CHART = { subject_name: 'Synthetic chart', birth_date: null, birth_time: null, birth_place: null }

function loadPreparation() {
  return PreparationPage({ params: Promise.resolve({ id: CHART_ID }) })
}

beforeEach(() => {
  vi.resetAllMocks()
  mockQuery.mockResolvedValue({ rows: [CHART] })
  mockRedirect.mockImplementation(() => { throw new Error('NEXT_REDIRECT') })
  mockCockpit.mockReturnValue(<section aria-label="Preparation controls" />)
  vi.stubGlobal('fetch', mockFetch)
})

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
  expect(mockFetch).not.toHaveBeenCalled()
})

describe('Nirmāṇa preparation page permissions', () => {
  it.each([
    ['chart owner', 'guest'],
    ['super admin', 'super_admin'],
  ] as const)('renders chart-scoped preparation for a %s without dispatch', async (_actor, role) => {
    mockResolveAccess.mockResolvedValue({ user: { uid: 'fixture-user' }, role, permission: 'all', canBuild: true })

    render(await loadPreparation())

    expect(mockResolveAccess).toHaveBeenCalledExactlyOnceWith(CHART_ID)
    expect(mockResolveAccess).toHaveBeenCalledBefore(mockQuery)
    expect(mockQuery).toHaveBeenCalledExactlyOnceWith(
      expect.stringMatching(/^SELECT .* FROM charts WHERE id=\$1$/),
      [CHART_ID],
    )
    expect(screen.getByTestId('build-page-root')).toHaveAttribute('data-permission', 'all')
    expect(screen.getByRole('region', { name: 'Preparation controls' })).toBeVisible()
    expect(mockCockpit.mock.calls[0]?.[0]).toMatchObject({
      chartId: CHART_ID,
      initialChartMeta: CHART,
      variant: 'preparation',
    })
  })

  it.each(['view', 'deny'] as const)('redirects permission=%s before reading chart data or rendering controls', async (permission) => {
    mockResolveAccess.mockResolvedValue({ user: { uid: 'fixture-user' }, role: 'guest', permission, canBuild: false })

    await expect(loadPreparation()).rejects.toThrow('NEXT_REDIRECT')
    expect(mockRedirect).toHaveBeenCalledExactlyOnceWith(`/clients/${CHART_ID}`)
    expect(mockQuery).not.toHaveBeenCalled()
    expect(mockCockpit).not.toHaveBeenCalled()
  })

  it('redirects an unauthenticated request before reading chart data or rendering controls', async () => {
    mockResolveAccess.mockResolvedValue(null)

    await expect(loadPreparation()).rejects.toThrow('NEXT_REDIRECT')
    expect(mockRedirect).toHaveBeenCalledExactlyOnceWith('/login')
    expect(mockQuery).not.toHaveBeenCalled()
    expect(mockCockpit).not.toHaveBeenCalled()
  })
})
