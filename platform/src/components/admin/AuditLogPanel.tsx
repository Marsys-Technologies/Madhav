'use client'

import type { AuditLogEntry } from '@/app/api/admin/audit-log/route'

const tableHeading = 'px-4 py-3 text-left text-xs font-semibold text-[var(--folio-muted)]'
const tableCell = 'px-4 py-3 text-sm text-[var(--folio-ink)]'

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
    ? 'text-[var(--folio-error)] border-[var(--folio-error)]'
    : isPromote
      ? 'text-[var(--folio-action)] bg-[var(--folio-selected)] border-[var(--folio-boundary)]'
      : 'text-[var(--folio-muted)] border-[var(--folio-divider)]'
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
      <div className="j5-panel text-center">
        <p className="text-sm text-[var(--folio-muted)]">No admin activity recorded yet.</p>
      </div>
    )
  }

  return (
    <div className="j5-panel">
      <div className="overflow-x-auto focus-visible:outline-2 focus-visible:outline-[var(--folio-focus)]" role="region" aria-label="Administration records" tabIndex={0}>
        <table className="w-full min-w-[600px]">
          <thead>
            <tr>
              <th className={tableHeading}>When</th>
              <th className={tableHeading}>Actor</th>
              <th className={tableHeading}>Action</th>
              <th className={tableHeading}>Source</th>
              <th className={tableHeading}>Target</th>
              <th className={tableHeading}>Detail</th>
            </tr>
          </thead>
          <tbody>
            {entries.map((e) => (
              <tr key={e.id} className="border-t border-[var(--folio-divider)]">
                <td className={`${tableCell} whitespace-nowrap`} title={e.created_at}>
                  {formatRelative(e.created_at)}
                </td>
                <td className={tableCell}>
                  <span className="text-sm">{e.actor_name ?? e.actor_email ?? e.actor_id ?? '—'}</span>
                </td>
                <td className={tableCell}>
                  <ActionBadge action={e.action} />
                </td>
                <td className={tableCell}>{e.source === 'ai_configuration' ? 'AI configuration' : 'Administration'}</td>
                <td className={tableCell}>
                  {e.target_name ?? e.target_email ?? (e.detail?.deleted_user_id != null ? String(e.detail.deleted_user_id) : '—')}
                </td>
                <td className="max-w-[220px] truncate px-4 py-3 text-xs text-[var(--folio-muted)]">
                  {e.detail ? JSON.stringify(e.detail) : ''}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="border-t border-[var(--folio-divider)] px-4 py-2 text-xs text-[var(--folio-muted)]">
        Showing last {entries.length} action{entries.length !== 1 ? 's' : ''}
      </p>
    </div>
  )
}
