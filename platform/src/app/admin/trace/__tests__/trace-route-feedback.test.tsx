import { act, render, screen } from '@testing-library/react'
import { expect, it, vi } from 'vitest'

const { fetchTraceEnvelope, requireSuperAdminPage } = vi.hoisted(() => ({
  fetchTraceEnvelope: vi.fn(), requireSuperAdminPage: vi.fn(),
}))
vi.mock('@/lib/admin/trace_client', () => ({ fetchTraceEnvelope }))
vi.mock('@/lib/auth/super-admin-page-guard', () => ({ requireSuperAdminPage }))

import TracePage from '../[query_id]/page'

it('provides loading and failure feedback and a return link on a bookmarked trace', async () => {
  let rejectRead: (reason: Error) => void = () => {}
  fetchTraceEnvelope.mockReturnValue(new Promise((_resolve, reject) => { rejectRead = reject }))

  render(await TracePage({ params: Promise.resolve({ query_id: 'fixture-query' }) }))

  const back = screen.getByRole('link', { name: 'Back to query sessions' })
  expect(back).toHaveAttribute('href', '/admin/trace')
  expect(screen.getByRole('status')).toHaveTextContent('Loading trace')

  await act(async () => rejectRead(new Error('data source offline')))
  expect(screen.getByRole('alert')).toHaveTextContent('Trace could not be loaded')
  expect(back).toBeVisible()
})
