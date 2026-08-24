import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'

vi.mock('@tanstack/react-query', () => ({
  useQuery: () => ({ data: { requests: [], users: [], entries: [] }, isError: false, refetch: vi.fn() }),
}))

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn() }),
  useSearchParams: () => new URLSearchParams(),
}))

vi.mock('./PendingRequestsTable', () => ({ PendingRequestsTable: () => <div /> }))
vi.mock('./UsersTable', () => ({ UsersTable: () => <div /> }))
vi.mock('./AuditLogPanel', () => ({ AuditLogPanel: () => <div /> }))
vi.mock('./ChartsTab', () => ({ ChartsTab: () => <div /> }))

import { AdminClient } from './AdminClient'

describe('AdminClient', () => {
  it('links super-admins to the Nirmāṇa elevation tracker', () => {
    render(<AdminClient currentUserId="admin-1" />)

    expect(screen.getByRole('link', { name: /nirmāṇa elevation tracker/i })).toHaveAttribute(
      'href',
      '/admin/nirmana-elevation',
    )
  })
})
