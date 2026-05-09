'use client'

import { useState } from 'react'
import { toast } from 'sonner'
import { ApproveDialog } from './ApproveDialog'
import { ConfirmDialog } from './ConfirmDialog'
import { adminCard, adminGhostBtn, adminPrimaryBtn, adminTableTd, adminTableTh, adminTableRow } from './styles'
import type { AdminAccessRequest } from './types'

function formatRelative(iso: string): string {
  const d = new Date(iso)
  const diffMs = Date.now() - d.getTime()
  const minutes = Math.round(diffMs / 60000)
  if (minutes < 1) return 'just now'
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.round(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.round(hours / 24)
  if (days < 30) return `${days}d ago`
  return d.toLocaleDateString()
}

export function PendingRequestsTable({
  requests,
  onMutated,
}: {
  requests: AdminAccessRequest[]
  onMutated: () => void
}) {
  const [approving, setApproving] = useState<AdminAccessRequest | null>(null)
  const [rejecting, setRejecting] = useState<AdminAccessRequest | null>(null)
  const [working, setWorking] = useState(false)

  async function handleReject() {
    if (!rejecting) return
    setWorking(true)
    try {
      const res = await fetch(`/api/admin/access-requests/${rejecting.id}/reject`, {
        method: 'POST',
      })
      const body = await res.json().catch(() => ({}))
      if (!res.ok) {
        toast.error(body?.error ?? 'Reject failed.')
      } else {
        toast.success('Request rejected.')
        setRejecting(null)
        onMutated()
      }
    } finally {
      setWorking(false)
    }
  }

  return (
    <section className={adminCard + ' overflow-hidden'}>
      <header className="flex items-center justify-between border-b border-[rgba(var(--brand-gold-rgb),0.15)] px-6 py-4">
        <h2 className="font-serif text-lg text-brand-gold-cream">Pending access requests</h2>
        <span className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
          {requests.length} pending
        </span>
      </header>

      {requests.length === 0 ? (
        <p className="px-6 py-8 text-center text-sm text-muted-foreground">
          No pending requests.
        </p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr>
                <th className={adminTableTh}>Requested</th>
                <th className={adminTableTh}>Name</th>
                <th className={adminTableTh}>Email</th>
                <th className={adminTableTh}>Reason</th>
                <th className={adminTableTh}></th>
              </tr>
            </thead>
            <tbody>
              {requests.map((r) => (
                <tr key={r.id} className={adminTableRow}>
                  <td className={adminTableTd + ' whitespace-nowrap text-muted-foreground'}>
                    {formatRelative(r.requested_at)}
                  </td>
                  <td className={adminTableTd}>{r.full_name}</td>
                  <td className={adminTableTd + ' text-brand-gold'}>{r.email}</td>
                  <td className={adminTableTd + ' max-w-md text-muted-foreground'}>
                    <span title={r.reason ?? ''} className="line-clamp-1">
                      {r.reason || '—'}
                    </span>
                  </td>
                  <td className={adminTableTd + ' whitespace-nowrap text-right'}>
                    <div className="flex justify-end gap-2">
                      <button onClick={() => setApproving(r)} className={adminPrimaryBtn}>
                        Approve
                      </button>
                      <button onClick={() => setRejecting(r)} className={adminGhostBtn}>
                        Reject
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <ApproveDialog
        request={approving}
        open={approving !== null}
        onOpenChange={(open) => {
          if (!open) setApproving(null)
        }}
        onApproved={onMutated}
      />
      <ConfirmDialog
        open={rejecting !== null}
        onOpenChange={(open) => {
          if (!open) setRejecting(null)
        }}
        title="Reject request?"
        description={
          rejecting
            ? `Reject access request from ${rejecting.full_name} (${rejecting.email})? This cannot be undone, but the user can submit a new request.`
            : ''
        }
        confirmLabel="Reject"
        destructive
        loading={working}
        onConfirm={handleReject}
      />
    </section>
  )
}
