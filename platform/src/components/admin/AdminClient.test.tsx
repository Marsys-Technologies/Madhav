import { afterEach, describe, expect, it, vi } from 'vitest'
import { useState } from 'react'
import { cleanup, fireEvent, render, screen } from '@testing-library/react'

const navigation = vi.hoisted(() => ({
  push: vi.fn(),
  search: new URLSearchParams(),
}))

const queries = vi.hoisted(() => ({
  auditRefetch: vi.fn(),
}))

vi.mock('@tanstack/react-query', () => ({
  useQuery: ({ queryKey }: { queryKey: string[] }) => {
    if (queryKey.at(-1) === 'users') {
      return {
        data: {
          users: [{
            id: 'user-1', role: 'guest', status: 'active', name: 'Asha Rao',
            username: 'asha', email: 'asha@example.test', created_at: '2026-09-27T10:00:00.000Z',
            approved_at: '2026-09-27T10:00:00.000Z',
          }],
        },
        isError: false,
        refetch: vi.fn(),
      }
    }
    if (queryKey.at(-1) === 'audit-log') {
      return { data: { entries: [] }, isError: false, refetch: queries.auditRefetch }
    }
    return { data: { requests: [] }, isError: false, refetch: vi.fn() }
  },
}))

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: navigation.push }),
  useSearchParams: () => navigation.search,
}))

vi.mock('./PendingRequestsTable', () => ({ PendingRequestsTable: () => <div>Pending panel</div> }))
vi.mock('./UsersTable', () => ({ UsersTable: () => <div>Users panel</div> }))
vi.mock('./AuditLogPanel', () => ({ AuditLogPanel: () => <div>Audit panel</div> }))
vi.mock('./ChartsTab', () => ({ ChartsTab: () => <div>Charts panel</div> }))
vi.mock('./AiAccessTab', () => ({
  AiAccessTab: ({ users, onAuditRefetch, initialUserId }: {
    users: Array<{ id: string; username: string | null }>
    initialUserId?: string | null
    onAuditRefetch: () => void
  }) => {
    const [selectedId] = useState(initialUserId ?? users[0]?.id ?? null)
    return <><p>AI grant target: {selectedId}</p><button type="button" onClick={onAuditRefetch}>
      AI Access panel for {users.map(user => user.username).join(', ')}
    </button></>
  },
}))

import { AdminClient } from './AdminClient'

afterEach(() => {
  cleanup()
  vi.unstubAllEnvs()
  navigation.push.mockReset()
  queries.auditRefetch.mockReset()
  navigation.search = new URLSearchParams()
})

describe('AdminClient', () => {
  it('remounts the grant editor for explicit default and ordinary bookmarked identities', () => {
    vi.stubEnv('NEXT_PUBLIC_MARSYS_FLAG_AI_CONSOLE_BYOK', 'true')
    navigation.search = new URLSearchParams('tab=ai-access')
    const view = render(<AdminClient currentUserId="admin-1" />)
    expect(screen.getByText('AI grant target: user-1')).toBeInTheDocument()
    navigation.search = new URLSearchParams('tab=ai-access&userId=default')
    view.rerender(<AdminClient currentUserId="admin-1" />)
    expect(screen.getByText('AI grant target: default')).toBeInTheDocument()
    navigation.search = new URLSearchParams('tab=ai-access&userId=another-user')
    view.rerender(<AdminClient currentUserId="admin-1" />)
    expect(screen.getByText('AI grant target: another-user')).toBeInTheDocument()
  })

  it('opens the four-block overview without a second legacy tab strip', () => {
    render(<AdminClient currentUserId="admin-1" />)

    expect(screen.getByRole('link', { name: /assets, programme and learning/i })).toHaveAttribute('href', '/admin/assets')
    expect(screen.queryByRole('button', { name: 'Pending Requests' })).toBeNull()
    expect(screen.queryByRole('link', { name: /nirmāṇa elevation tracker/i })).toBeNull()
  })

  it('links to AI Access from the overview while the public feature flag is on', () => {
    vi.stubEnv('NEXT_PUBLIC_MARSYS_FLAG_AI_CONSOLE_BYOK', 'true')
    render(<AdminClient currentUserId="admin-1" />)

    expect(screen.getByRole('link', { name: 'AI Access' })).toHaveAttribute('href', '/admin?tab=ai-access')
    expect(screen.queryByRole('button', { name: 'AI Access' })).toBeNull()
  })

  it.each([
    ['pending', 'Pending panel'],
    ['users', 'Users panel'],
    ['charts', 'Charts panel'],
    ['audit', 'Audit panel'],
  ])('preserves the bookmarked %s panel', (tab, panel) => {
    navigation.search = new URLSearchParams(`tab=${tab}`)
    render(<AdminClient currentUserId="admin-1" />)
    expect(screen.getByText(panel)).toBeInTheDocument()
  })

  it('mounts AI Access with safe users and the audit refresh callback', () => {
    vi.stubEnv('NEXT_PUBLIC_MARSYS_FLAG_AI_CONSOLE_BYOK', 'true')
    navigation.search = new URLSearchParams('tab=ai-access')
    render(<AdminClient currentUserId="admin-1" />)

    const panel = screen.getByRole('button', { name: 'AI Access panel for asha' })
    fireEvent.click(panel)

    expect(queries.auditRefetch).toHaveBeenCalledTimes(1)
  })

  it('hides AI Access and safely normalizes a retained AI Access URL while the flag is off', () => {
    vi.stubEnv('NEXT_PUBLIC_MARSYS_FLAG_AI_CONSOLE_BYOK', 'false')
    navigation.search = new URLSearchParams('tab=ai-access')
    render(<AdminClient currentUserId="admin-1" />)

    expect(screen.queryByRole('button', { name: 'AI Access' })).toBeNull()
    expect(screen.queryByText(/AI Access panel/i)).toBeNull()
    expect(screen.getByText('Pending panel')).toBeInTheDocument()
  })
})
