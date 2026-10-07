'use client'

import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ConfirmDialog } from './ConfirmDialog'
import { adminCard } from './styles'
import type { AdminCliGrant, AdminCliId, AdminUser } from './types'

interface GrantResponse {
  grants: AdminCliGrant[]
}

interface GrantTarget {
  userId: string
  userLabel: string
  cliId: AdminCliId
  productName: string
}

function userLabel(user: AdminUser): string {
  return user.name ?? user.username ?? user.email ?? user.id
}

async function fetchGrants(userId: string): Promise<GrantResponse> {
  const response = await fetch(`/api/admin/users/${encodeURIComponent(userId)}/ai-cli-grants`)
  if (!response.ok) throw new Error('grant_query_failed')
  return response.json() as Promise<GrantResponse>
}

export function AiAccessTab({
  users,
  onAuditRefetch,
  initialUserId,
}: {
  users: AdminUser[]
  initialUserId?: string | null
  onAuditRefetch: () => unknown | Promise<unknown>
}) {
  const queryClient = useQueryClient()
  const [selectedId, setSelectedId] = useState<string | null>(initialUserId ?? users[0]?.id ?? null)
  const [revokeTarget, setRevokeTarget] = useState<GrantTarget | null>(null)
  const [mutationError, setMutationError] = useState<string | null>(null)
  const selectedUser = users.find(user => user.id === selectedId) ?? null
  const selectedLabel = selectedUser ? userLabel(selectedUser) : ''
  const grantQueryKey = ['admin', 'ai-cli-grants', selectedUser?.id] as const

  const grantQuery = useQuery({
    queryKey: grantQueryKey,
    queryFn: () => fetchGrants(selectedUser!.id),
    enabled: selectedUser !== null,
  })

  const mutation = useMutation({
    mutationFn: async ({ target, granted }: { target: GrantTarget; granted: boolean }) => {
      setMutationError(null)
      const response = await fetch(`/api/admin/users/${encodeURIComponent(target.userId)}/ai-cli-grants`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cliId: target.cliId, granted }),
      })
      if (!response.ok) throw new Error('grant_mutation_failed')
      await queryClient.invalidateQueries({
        queryKey: ['admin', 'ai-cli-grants', target.userId],
        exact: true,
        refetchType: 'active',
      })
      await onAuditRefetch()
    },
    onSuccess: () => setRevokeTarget(null),
    onError: () => {
      setRevokeTarget(null)
      setMutationError('Could not update AI access. Try again.')
    },
  })

  function toggleGrant(grant: AdminCliGrant) {
    if (!selectedUser || mutation.isPending) return
    const target: GrantTarget = {
      userId: selectedUser.id,
      userLabel: selectedLabel,
      cliId: grant.cliId,
      productName: grant.productName,
    }
    if (grant.granted) {
      setRevokeTarget(target)
      return
    }
    if (selectedUser.status !== 'active') return
    mutation.mutate({ target, granted: true })
  }

  function confirmRevoke() {
    if (!revokeTarget || mutation.isPending) return
    mutation.mutate({ target: revokeTarget, granted: false })
  }

  return (
    <section className={adminCard + ' overflow-hidden'}>
      <header className="border-b border-[rgba(var(--brand-gold-rgb),0.15)] px-6 py-4">
        <h2 className="font-serif text-lg text-brand-gold-cream">AI Access</h2>
        <p className="mt-0.5 text-xs text-muted-foreground">
          Grant each local AI product separately. Host availability does not change access policy.
        </p>
      </header>

      <div className="flex min-h-[480px] flex-col md:flex-row">
        <div className="shrink-0 border-b border-[rgba(var(--brand-gold-rgb),0.12)] bg-[rgba(0,0,0,0.2)] md:w-64 md:border-b-0 md:border-r">
          <div className="border-b border-[rgba(var(--brand-gold-rgb),0.08)] px-4 py-3">
            <span className="text-[10px] uppercase tracking-[0.16em] text-muted-foreground">Users</span>
          </div>
          {users.length === 0 ? (
            <p className="px-4 py-8 text-center text-xs text-muted-foreground">No users available.</p>
          ) : (
            <div className="space-y-1 p-2">
              {users.map(user => {
                const label = userLabel(user)
                const selected = user.id === selectedUser?.id
                return (
                  <button
                    key={user.id}
                    type="button"
                    aria-pressed={selected}
                    aria-label={`Select ${label}`}
                    onClick={() => {
                      setSelectedId(user.id)
                      setMutationError(null)
                    }}
                    disabled={mutation.isPending}
                    className={[
                      'flex min-h-11 w-full items-center justify-between rounded-md border px-3 py-2 text-left transition-colors focus:outline-none focus:ring-2 focus:ring-brand-gold/50 disabled:cursor-wait disabled:opacity-50',
                      selected
                        ? 'border-[rgba(var(--brand-gold-rgb),0.35)] bg-[rgba(var(--brand-gold-rgb),0.08)]'
                        : 'border-transparent hover:bg-[rgba(var(--brand-gold-rgb),0.04)]',
                    ].join(' ')}
                  >
                    <span className="min-w-0">
                      <span className={`block truncate text-sm font-medium ${selected ? 'text-brand-gold' : 'text-muted-foreground'}`}>
                        {label}
                      </span>
                      <span className="block truncate text-[11px] capitalize text-muted-foreground/60">
                        {user.role.replace('_', ' ')} · {user.status}
                      </span>
                    </span>
                  </button>
                )
              })}
            </div>
          )}
        </div>

        <div className="min-w-0 flex-1 px-4 py-5 sm:px-6">
          {!selectedUser ? (
            <p className="py-10 text-center text-sm text-muted-foreground">Select a user to manage AI access.</p>
          ) : (
            <>
              <div className="mb-4">
                <h3 className="font-serif text-base text-brand-gold-cream">{selectedLabel}&apos;s local CLI access</h3>
                <p className="mt-1 text-xs text-muted-foreground">
                  Access is denied until an administrator grants an individual product.
                </p>
                {selectedUser.status !== 'active' && (
                  <p className="mt-2 text-xs text-amber-300">
                    Inactive users cannot receive new CLI grants. Existing grants can still be revoked.
                  </p>
                )}
              </div>

              {mutationError && (
                <p role="alert" className="mb-3 text-sm text-red-400">{mutationError}</p>
              )}

              {grantQuery.isPending ? (
                <p role="status" className="py-8 text-center text-sm text-muted-foreground">Loading AI access…</p>
              ) : grantQuery.isError ? (
                <p role="alert" className="py-8 text-center text-sm text-red-400">Could not load AI access.</p>
              ) : (
                <div className="space-y-2">
                  {(grantQuery.data?.grants ?? []).map(grant => {
                    const cannotGrant = selectedUser.status !== 'active' && !grant.granted
                    const statusId = `ai-cli-status-${selectedUser.id}-${grant.cliId}`
                    return (
                      <div
                        key={grant.cliId}
                        className="flex min-h-16 items-center justify-between gap-4 rounded-lg border border-[rgba(var(--brand-gold-rgb),0.12)] px-4 py-3"
                      >
                        <div className="min-w-0">
                          <div className="font-serif text-sm text-brand-gold-cream">{grant.productName}</div>
                          <div id={statusId} className="mt-1 flex flex-wrap gap-x-3 gap-y-1 text-[11px]">
                            <span className={grant.granted ? 'text-emerald-300' : 'text-muted-foreground'}>
                              {grant.granted ? 'Granted' : 'Not granted'}
                            </span>
                            <span className={grant.hostState === 'reachable' ? 'text-emerald-300' : 'text-muted-foreground'}>
                              {grant.hostState === 'reachable' ? 'Reachable' : 'Unavailable'}
                            </span>
                          </div>
                        </div>
                        <button
                          type="button"
                          role="switch"
                          aria-checked={grant.granted}
                          aria-describedby={statusId}
                          aria-label={`${selectedLabel} ${grant.productName} access`}
                          disabled={mutation.isPending || cannotGrant}
                          onClick={() => toggleGrant(grant)}
                          className={[
                            'relative min-h-11 min-w-14 shrink-0 rounded-full border p-1 transition-colors focus:outline-none focus:ring-2 focus:ring-brand-gold/50 disabled:cursor-not-allowed disabled:opacity-45',
                            grant.granted
                              ? 'border-emerald-700/60 bg-emerald-950/50'
                              : 'border-[rgba(var(--brand-gold-rgb),0.28)] bg-brand-ink',
                          ].join(' ')}
                        >
                          <span
                            aria-hidden="true"
                            className={[
                              'block h-5 w-5 rounded-full transition-transform',
                              grant.granted ? 'translate-x-6 bg-emerald-300' : 'translate-x-0 bg-muted-foreground',
                            ].join(' ')}
                          />
                        </button>
                      </div>
                    )
                  })}
                </div>
              )}
            </>
          )}
        </div>
      </div>

      <ConfirmDialog
        open={revokeTarget !== null}
        onOpenChange={open => {
          if (!open && !mutation.isPending) setRevokeTarget(null)
        }}
        title={revokeTarget ? `Revoke ${revokeTarget.productName} for ${revokeTarget.userLabel}?` : 'Revoke AI access?'}
        description={revokeTarget
          ? `${revokeTarget.userLabel} will lose access to ${revokeTarget.productName}. The next invocation will be blocked.`
          : ''}
        confirmLabel="Revoke access"
        destructive
        loading={mutation.isPending}
        onConfirm={confirmRevoke}
      />
    </section>
  )
}
