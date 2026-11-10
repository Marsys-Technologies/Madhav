import { render, screen, within } from '@testing-library/react'
import { afterEach, expect, it, vi } from 'vitest'

const { query } = vi.hoisted(() => ({ query: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query }))
vi.mock('@/lib/auth/access-control', () => ({
  getServerUserWithProfile: vi.fn(async () => ({ user: { uid: 'admin-1' }, profile: { role: 'super_admin' } })),
}))

import TrackerPage from '../page'

afterEach(() => vi.resetAllMocks())

it('separates a failed active-build read, an empty recent result and an unavailable matrix', async () => {
  query.mockRejectedValueOnce(new Error('data source offline')).mockResolvedValueOnce({ rows: [] })

  render(await TrackerPage())

  const active = screen.getByRole('region', { name: 'Active Builds' })
  expect(within(active).getByRole('alert')).toHaveTextContent('Build records could not be read')
  expect(screen.getByText('No builds.', { exact: true })).toBeInTheDocument()
  expect(screen.getByText('Per-ayanamsha build history is unavailable in this tracker.')).toBeInTheDocument()
})
