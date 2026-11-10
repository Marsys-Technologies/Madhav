import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { afterEach, expect, it, vi } from 'vitest'
import { PendingRequestsTable } from '../PendingRequestsTable'
import { UsersTable } from '../UsersTable'
import type { AdminAccessRequest, AdminUser } from '../types'

const { error } = vi.hoisted(() => ({ error: vi.fn() }))
vi.mock('sonner', () => ({ toast: { error, success: vi.fn() } }))
vi.mock('next/navigation', () => ({ useRouter: () => ({ push: vi.fn() }) }))

const user: AdminUser = {
  id: 'guest-1', role: 'guest', status: 'active', name: 'Asha Rao', username: 'asha',
  email: 'asha@example.test', created_at: '2026-09-27T10:00:00.000Z', approved_at: null,
}
const request: AdminAccessRequest = {
  id: 'req-1', full_name: 'Tara Rao', email: 'tara@example.test', status: 'pending', reason: null,
  requested_at: '2026-09-27T10:00:00.000Z', reviewed_at: null, approved_user_id: null,
  approved_username: null, approved_name: null,
}

afterEach(() => {
  cleanup()
  vi.clearAllMocks()
  vi.unstubAllGlobals()
})

it('names the directory search, its scroll region and the user-specific controls', () => {
  render(<UsersTable users={[user]} currentUserId="admin-1" onMutated={vi.fn()} />)

  const directory = screen.getByRole('region', { name: 'User directory results' })
  expect(directory).toHaveAttribute('tabindex', '0')
  expect(within(directory).getByRole('link', { name: 'Details for Asha Rao' }))
    .toHaveAttribute('href', '/admin/users/guest-1')
  expect(within(directory).getByRole('button', { name: 'Actions for Asha Rao' })).toBeEnabled()

  fireEvent.change(screen.getByRole('searchbox', { name: 'Search users' }), { target: { value: 'unknown' } })
  expect(screen.getByRole('status')).toHaveTextContent('No users match')
})

it('gives the request approval role control an accessible name', async () => {
  render(<PendingRequestsTable requests={[request]} onMutated={vi.fn()} />)
  fireEvent.click(screen.getByRole('button', { name: 'Approve' }))

  const dialog = await screen.findByRole('dialog')
  expect(within(dialog).getByRole('combobox', { name: 'Role' })).toHaveValue('guest')
})

it('reports when a rejection could not be confirmed and keeps the request open for review', async () => {
  const onMutated = vi.fn()
  vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('connection lost')))
  render(<PendingRequestsTable requests={[request]} onMutated={onMutated} />)
  fireEvent.click(screen.getByRole('button', { name: 'Reject' }))

  const dialog = await screen.findByRole('dialog', { name: 'Reject request?' })
  fireEvent.click(within(dialog).getByRole('button', { name: 'Reject' }))

  await waitFor(() => expect(error).toHaveBeenCalledWith('Could not confirm the rejection. Refresh access requests before trying again.'))
  expect(within(dialog).getByRole('button', { name: 'Reject' })).toBeEnabled()
  expect(onMutated).not.toHaveBeenCalled()
})
