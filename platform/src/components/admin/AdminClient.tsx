'use client'

import { useQuery } from '@tanstack/react-query'
import Link from 'next/link'
import { useRouter, useSearchParams } from 'next/navigation'
import { PendingRequestsTable } from './PendingRequestsTable'
import { UsersTable } from './UsersTable'
import { AuditLogPanel } from './AuditLogPanel'
import { ChartsTab } from './ChartsTab'
import type { AdminAccessRequest, AdminUser } from './types'
import type { AuditLogEntry } from '@/app/api/admin/audit-log/route'

type Tab = 'pending' | 'users' | 'charts' | 'audit'

const TABS: { id: Tab; label: string }[] = [
  { id: 'pending', label: 'Pending Requests' },
  { id: 'users',   label: 'Users' },
  { id: 'charts',  label: 'Charts' },
  { id: 'audit',   label: 'Audit Log' },
]

async function fetchJson<T>(url: string): Promise<T> {
  const res = await fetch(url)
  if (!res.ok) throw new Error(`Request failed: ${res.status}`)
  return (await res.json()) as T
}

export function AdminClient({ currentUserId }: { currentUserId: string }) {
  const router = useRouter()
  const searchParams = useSearchParams()
  const activeTab = (searchParams.get('tab') as Tab | null) ?? 'pending'

  function setTab(tab: Tab) {
    router.push(`/admin?tab=${tab}`, { scroll: false })
  }

  const requestsQuery = useQuery({
    queryKey: ['admin', 'access-requests'],
    queryFn: () => fetchJson<{ requests: AdminAccessRequest[] }>('/api/admin/access-requests'),
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

  const pendingCount = (requestsQuery.data?.requests ?? []).filter(r => r.status === 'pending').length

  return (
    <div className="space-y-6">
      <div>
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <h1 className="font-serif text-3xl font-medium tracking-wide text-brand-gold-cream">
              Administration
            </h1>
            <p className="mt-1 text-sm text-muted-foreground">
              Manage users, chart access, and platform activity.
            </p>
          </div>
          <Link
            href="/admin/nirmana-elevation"
            className="rounded-md border border-[rgba(var(--brand-gold-rgb),0.35)] px-3 py-2 text-xs font-medium tracking-wide text-brand-gold transition-colors hover:bg-[rgba(var(--brand-gold-rgb),0.10)] focus:outline-none focus:ring-2 focus:ring-brand-gold/50"
          >
            Nirmāṇa Elevation Tracker
          </Link>
        </div>
      </div>

      {/* Tab bar */}
      <div className="flex border-b border-[rgba(var(--brand-gold-rgb),0.18)]">
        {TABS.map(tab => (
          <button
            key={tab.id}
            onClick={() => setTab(tab.id)}
            className={[
              'relative px-5 py-3 text-[11px] uppercase tracking-[0.14em] transition-colors',
              activeTab === tab.id
                ? 'text-brand-gold after:absolute after:bottom-0 after:left-0 after:right-0 after:h-[2px] after:bg-brand-gold'
                : 'text-muted-foreground hover:text-brand-gold-cream',
            ].join(' ')}
          >
            {tab.label}
            {tab.id === 'pending' && pendingCount > 0 && (
              <span className="ml-1.5 rounded-full bg-amber-950/60 border border-amber-700/40 px-1.5 py-0.5 text-[10px] text-amber-400">
                {pendingCount}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Tab panels */}
      {activeTab === 'pending' && (
        requestsQuery.isError ? (
          <p className="text-sm text-red-400">Could not load access requests — check DB proxy.</p>
        ) : (
          <PendingRequestsTable
            requests={requestsQuery.data?.requests ?? []}
            onMutated={refetchAll}
          />
        )
      )}

      {activeTab === 'users' && (
        usersQuery.isError ? (
          <p className="text-sm text-red-400">Could not load users — check DB proxy.</p>
        ) : (
          <UsersTable
            users={usersQuery.data?.users ?? []}
            currentUserId={currentUserId}
            onMutated={refetchAll}
          />
        )
      )}

      {activeTab === 'charts' && (
        usersQuery.isError ? (
          <p className="text-sm text-red-400">Could not load guests — check DB proxy.</p>
        ) : (
          <ChartsTab
            users={usersQuery.data?.users ?? []}
            onGrantMutated={auditQuery.refetch}
          />
        )
      )}

      {activeTab === 'audit' && (
        auditQuery.isError ? (
          <p className="text-sm text-red-400">Could not load audit log.</p>
        ) : (
          <AuditLogPanel entries={auditQuery.data?.entries ?? []} />
        )
      )}
    </div>
  )
}
