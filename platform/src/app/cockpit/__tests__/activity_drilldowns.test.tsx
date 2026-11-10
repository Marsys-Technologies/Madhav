import { render, screen } from '@testing-library/react'
import { afterEach, expect, it, vi } from 'vitest'
import { operatorActivityFilters } from '@/lib/admin/activity-filters'

vi.mock('server-only', () => ({}))

const { usageSummary } = vi.hoisted(() => ({ usageSummary: vi.fn() }))
vi.mock('@/lib/metering/queries', async (importOriginal) => ({
  ...await importOriginal<typeof import('@/lib/metering/queries')>(),
  usageSummary,
}))
vi.mock('@/lib/metering/types', async (importOriginal) => ({
  ...await importOriginal<typeof import('@/lib/metering/types')>(),
  meteringEnabled: () => true,
}))
vi.mock('@/lib/auth/super-admin-page-guard', () => ({ requireSuperAdminPage: vi.fn() }))
vi.mock('@/lib/build/dataSource', () => ({ fetchBuildState: vi.fn() }))
vi.mock('@/lib/config', () => ({ getFlag: () => false }))

import CockpitPage from '../page'

afterEach(() => {
  vi.useRealTimers()
  vi.clearAllMocks()
})

it.each([
  {
    clock: '2026-11-10T00:00:03.200+05:30',
    from: '2026-11-09T00:00:00.000Z',
    to: '2026-11-09T18:30:03.200Z',
  },
  {
    clock: '2026-11-10T00:00:00.000Z',
    from: '2026-11-10T00:00:00.000Z',
    to: '2026-11-10T00:00:00.001Z',
  },
])('opens the same portal interval as the Cockpit figures at $clock', async ({ clock, from, to }) => {
  vi.setSystemTime(new Date(clock))
  usageSummary.mockResolvedValue({
    transport_attempts: 4, complete_usage: 3, transport_failed: 1, validation_attempts: 0,
  })

  render(await CockpitPage())

  const metrics = [
    { label: /Calls today · UTC/, path: '/admin/activity', value: '4' },
    { label: /Call health/, path: '/admin/analytics', value: '1 failed' },
    { label: /Usage evidence/, path: '/admin/analytics', value: '75% complete' },
  ]
  for (const { label, path, value } of metrics) {
    const link = screen.getByRole('link', { name: label })
    expect(link).toHaveTextContent(value)
    const destination = new URL(link.getAttribute('href')!, 'https://example.test')
    expect(destination.pathname).toBe(path)
    const operator = operatorActivityFilters(destination.searchParams, 'admin-1')
    expect(operator.scope).toBe('portal')
    expect(operator.target).toBeNull()
    expect(Object.fromEntries(operator.params)).toEqual({ from, to })
  }
  expect(usageSummary).toHaveBeenCalledWith(expect.objectContaining({ from, to, view: 'summary' }), { ownerId: null })
  expect(screen.getByRole('link', { name: /Open Observatory/ })).toHaveAttribute('href', '/observatory')
})
