'use client'

import { useQuery } from '@tanstack/react-query'
import { PendingRequestsTable } from './PendingRequestsTable'
import { UsersTable } from './UsersTable'
import { AuditLogPanel } from './AuditLogPanel'
import type { AdminAccessRequest, AdminUser } from './types'
import type { AuditLogEntry } from '@/app/api/admin/audit-log/route'

async function fetchJson<T>(url: string): Promise<T> {
  const res = await fetch(url)
  if (!res.ok) throw new Error(`Request failed: ${res.status}`)
  return (await res.json()) as T
}

export function AdminClient({ currentUserId }: { currentUserId: string }) {
  const requestsQuery = useQuery({
    queryKey: ['admin', 'access-requests'],
    queryFn: () =>
      fetchJson<{ requests: AdminAccessRequest[] }>('/api/admin/access-requests'),
  })
  const usersQuery = useQuery({
    queryKey: ['admin', 'users'],
    queryFn: () => fetchJson<{ users: AdminUser[] }>('/api/admin/users'),
  })
  const auditQuery = useQuery({
    queryKey: ['admin', 'audit-log'],
    queryFn: () => fetchJson<{ entries: AuditLogEntry[] }>('/api/admin/audit-log'),
  })

  function refetchAll() {
    requestsQuery.refetch()
    usersQuery.refetch()
    auditQuery.refetch()
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="font-serif text-3xl font-medium tracking-wide text-brand-gold-cream">
          User management
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Pending access requests and active accounts.
        </p>
      </div>

      {requestsQuery.isError ? (
        <p className="text-sm text-red-400">Could not load access requests — check DB proxy.</p>
      ) : (
        <PendingRequestsTable
          requests={requestsQuery.data?.requests ?? []}
          onMutated={refetchAll}
        />
      )}

      {usersQuery.isError ? (
        <p className="text-sm text-red-400">Could not load users — check DB proxy.</p>
      ) : (
        <UsersTable
          users={usersQuery.data?.users ?? []}
          currentUserId={currentUserId}
          onMutated={refetchAll}
        />
      )}

      <div>
        <h2 className="mb-3 text-lg font-medium tracking-wide text-brand-gold-cream">
          Recent admin activity
        </h2>
        {auditQuery.isError ? (
          <p className="text-sm text-red-400">Could not load audit log.</p>
        ) : (
          <AuditLogPanel entries={auditQuery.data?.entries ?? []} />
        )}
      </div>
    </div>
  )
}
