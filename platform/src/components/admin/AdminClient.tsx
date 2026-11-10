'use client'

import { useQuery } from '@tanstack/react-query'
import Link from 'next/link'
import { useSearchParams } from 'next/navigation'
import { PendingRequestsTable } from './PendingRequestsTable'
import { UsersTable } from './UsersTable'
import { AuditLogPanel } from './AuditLogPanel'
import { ChartsTab } from './ChartsTab'
import { AiAccessTab } from './AiAccessTab'
import { ADMIN_BLOCKS } from './AdminNavigation'
import folio from './folio-context.module.css'
import { PageTitle, type PageName } from '@/components/journey1/Titles'
import type { AdminAccessRequest, AdminUser } from './types'
import type { AuditLogEntry } from '@/app/api/admin/audit-log/route'

type Tab = 'overview' | 'pending' | 'users' | 'charts' | 'ai-access' | 'audit'

const BASE_TABS: { id: Tab; label: string }[] = [
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
  const searchParams = useSearchParams()
  const aiAccessEnabled = process.env.NEXT_PUBLIC_MARSYS_FLAG_AI_CONSOLE_BYOK === 'true'
  const tabs = aiAccessEnabled
    ? [...BASE_TABS.slice(0, 3), { id: 'ai-access' as const, label: 'AI Access' }, ...BASE_TABS.slice(3)]
    : BASE_TABS
  const requestedTab = searchParams.get('tab')
  const activeTab: Tab = requestedTab == null ? 'overview' : tabs.some(tab => tab.id === requestedTab) ? requestedTab as Tab : 'pending'
  const title: PageName = {overview:'admin',pending:'accessRequests',users:'adminUsers',charts:'chartManagement','ai-access':'aiAccess',audit:'administrationLog'}[activeTab] as PageName

  const requestsQuery = useQuery({
    queryKey: ['admin', currentUserId, 'access-requests'],
    queryFn: () => fetchJson<{ requests: AdminAccessRequest[] }>('/api/admin/access-requests'),
  })
  const usersQuery = useQuery({
    queryKey: ['admin', currentUserId, 'users'],
    queryFn: () => fetchJson<{ users: AdminUser[] }>('/api/admin/users'),
  })
  const auditQuery = useQuery({
    queryKey: ['admin', currentUserId, 'audit-log'],
    queryFn: () => fetchJson<{ entries: AuditLogEntry[] }>('/api/admin/audit-log'),
  })

  function refetchAll() {
    requestsQuery.refetch()
    usersQuery.refetch()
    auditQuery.refetch()
  }

  const pendingCount = (requestsQuery.data?.requests ?? []).filter(r => r.status === 'pending').length
  const showRequestRecovery = requestsQuery.isError || (requestsQuery.isPending && requestsQuery.isFetched)
  const portalHeader = activeTab === 'overview' || activeTab === 'pending'

  return (
    <div className="space-y-6">
      <div className={portalHeader ? folio.context : undefined}>
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <PageTitle name={title} />
            {portalHeader && (
              <p className={folio.scope}>
                {activeTab === 'overview' ? 'Portal scope · administration overview' : 'Portal scope'}
              </p>
            )}
            <p className="mt-1 text-sm text-muted-foreground">
              Portal administration in four blocks. Your account, preferences, personas and AI defaults stay under My Account.
            </p>
          </div>
        </div>
      </div>

      {activeTab === 'overview' && <>
        <div className="j6-blocks">{ADMIN_BLOCKS.map(block => <Link className="j5-panel" key={block.href} href={block.href}><h2>{block.label}</h2><p className="j1-note">{block.description}</p></Link>)}</div>
        <div className="j5-panel"><h2>People and access</h2><p>{requestsQuery.isPending ? 'Requests loading…' : requestsQuery.isError ? 'Request count unavailable' : `${pendingCount} requests awaiting review`}</p><div className="j6-links"><Link href="/admin?tab=users">Users</Link><Link href="/admin?tab=charts">Chart Management</Link>{aiAccessEnabled && <Link href="/admin?tab=ai-access">AI Access</Link>}<Link href="/admin/administration-log">Administration Log</Link><Link href="/admin/mcp/keys">MCP / Client Keys</Link></div></div>
        <div className="j5-panel"><h2>Activity scope</h2><div className="j6-links"><Link href="/account/ai-cockpit/observatory">My activity</Link><Link href="/admin/activity?scope=portal">Portal activity</Link><Link href="/admin/activity?scope=user">Selected user activity</Link></div><p className="j1-note">Inspecting a user never impersonates them or changes their settings.</p></div>
      </>}
      {/* Tab panels */}
      {activeTab === 'pending' && (
        showRequestRecovery ? (
          <div className="j5-panel space-y-3">
            {requestsQuery.isFetching
              ? <p role="status">Retrying access requests…</p>
              : <p role="alert" className="text-sm text-[var(--folio-error)]">Could not load access requests.</p>}
            <button
              type="button"
              className="min-h-11 rounded-md border border-[var(--folio-boundary)] px-3 text-[var(--folio-action)] hover:bg-[var(--folio-selected)] focus-visible:outline-2 focus-visible:outline-[var(--folio-focus)] aria-disabled:opacity-50"
              aria-disabled={requestsQuery.isFetching}
              onClick={() => {
                if (!requestsQuery.isFetching) void requestsQuery.refetch({ cancelRefetch: false })
              }}
            >
              Retry access requests
            </button>
          </div>
        ) : requestsQuery.isPending ? <p role="status">Loading access requests…</p> : (
          <PendingRequestsTable
            requests={requestsQuery.data?.requests ?? []}
            onMutated={refetchAll}
          />
        )
      )}

      {activeTab === 'users' && (
        usersQuery.isPending ? <p role="status">Loading users…</p> : usersQuery.isError ? (
          <p className="text-sm text-red-400">Could not load users.</p>
        ) : (
          <UsersTable
            users={usersQuery.data?.users ?? []}
            currentUserId={currentUserId}
            onMutated={refetchAll}
          />
        )
      )}

      {activeTab === 'charts' && (
        usersQuery.isPending ? <p role="status">Loading chart access…</p> : usersQuery.isError ? (
          <p className="text-sm text-red-400">Could not load users for chart access.</p>
        ) : (
          <ChartsTab
            users={usersQuery.data?.users ?? []}
            onGrantMutated={auditQuery.refetch}
          />
        )
      )}

      {activeTab === 'ai-access' && aiAccessEnabled && (
        usersQuery.isPending ? <p role="status">Loading AI access…</p> : usersQuery.isError ? (
          <p className="text-sm text-red-400">Could not load users.</p>
        ) : (
          <AiAccessTab
            key={JSON.stringify(searchParams.get('userId'))}
            initialUserId={searchParams.get('userId')}
            users={usersQuery.data?.users ?? []}
            onAuditRefetch={() => auditQuery.refetch()}
          />
        )
      )}

      {activeTab === 'audit' && (
        auditQuery.isPending ? <p role="status">Loading audit records…</p> : auditQuery.isError ? (
          <p className="text-sm text-red-400">Could not load audit log.</p>
        ) : (
          <><Link href="/admin/administration-log">Filter and browse administration records</Link><AuditLogPanel entries={auditQuery.data?.entries ?? []} /></>
        )
      )}
    </div>
  )
}
