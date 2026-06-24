'use client'

import { adminCard, adminLabel, adminTableTd, adminTableTh, adminTableRow } from './styles'
import type { AuditLogEntry } from '@/app/api/admin/audit-log/route'

const ACTION_LABELS: Record<string, string> = {
  create_user:    'Created user',
  edit_username:  'Changed username',
  disable_user:   'Disabled account',
  enable_user:    'Enabled account',
  delete_user:    'Deleted user',
  role_change:    'Changed role',
  reset_password: 'Sent password reset',
}

function ActionBadge({ action }: { action: string }) {
  const isDestructive = action === 'delete_user' || action === 'disable_user'
  const isPromote     = action === 'role_change' || action === 'create_user'
  const color = isDestructive
    ? 'text-red-400 bg-red-950/30 border-red-900/40'
    : isPromote
      ? 'text-brand-gold bg-brand-gold/10 border-brand-gold/20'
      : 'text-muted-foreground bg-white/5 border-white/10'
  return (
    <span className={`inline-flex items-center rounded-md border px-2 py-0.5 text-[11px] font-medium ${color}`}>
      {ACTION_LABELS[action] ?? action}
    </span>
  )
}

function formatRelative(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime()
  const m = Math.floor(diff / 60_000)
  if (m < 1)  return 'just now'
  if (m < 60) return `${m}m ago`
  const h = Math.floor(m / 60)
  if (h < 24) return `${h}h ago`
  return new Date(iso).toLocaleDateString()
}

export function AuditLogPanel({ entries }: { entries: AuditLogEntry[] }) {
  if (entries.length === 0) {
    return (
      <div className={`${adminCard} px-6 py-8 text-center`}>
        <p className="text-sm text-muted-foreground">No admin activity recorded yet.</p>
      </div>
    )
  }

  return (
    <div className={adminCard}>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[600px]">
          <thead>
            <tr>
              <th className={adminTableTh}>When</th>
              <th className={adminTableTh}>Actor</th>
              <th className={adminTableTh}>Action</th>
              <th className={adminTableTh}>Target</th>
              <th className={adminTableTh}>Detail</th>
            </tr>
          </thead>
          <tbody>
            {entries.map((e) => (
              <tr key={e.id} className={adminTableRow}>
                <td className={`${adminTableTd} whitespace-nowrap`} title={e.created_at}>
                  {formatRelative(e.created_at)}
                </td>
                <td className={adminTableTd}>
                  <span className="text-sm">{e.actor_name ?? e.actor_email ?? e.actor_id ?? '—'}</span>
                </td>
                <td className={adminTableTd}>
                  <ActionBadge action={e.action} />
                </td>
                <td className={adminTableTd}>
                  {e.target_name ?? e.target_email ?? (e.detail?.deleted_user_id != null ? String(e.detail.deleted_user_id) : '—')}
                </td>
                <td className={`${adminTableTd} max-w-[220px] truncate text-xs text-muted-foreground`}>
                  {e.detail ? JSON.stringify(e.detail) : ''}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className={`${adminLabel} border-t border-[rgba(var(--brand-gold-rgb),0.12)] px-4 py-2`}>
        Showing last {entries.length} action{entries.length !== 1 ? 's' : ''}
      </p>
    </div>
  )
}
