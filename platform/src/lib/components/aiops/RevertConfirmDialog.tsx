'use client'

import { useState, useEffect, useRef } from 'react'

interface AuditEntry {
  id:         number
  action:     string
  stack:      string | null
  call_type:  string | null
  param_name: string | null
  before_value: unknown
  after_value:  unknown
}

interface RevertConfirmDialogProps {
  entry:     AuditEntry
  onReverted: () => void
  onCancel:  () => void
}

function describeValue(v: unknown): string {
  if (v == null) return '(none)'
  if (typeof v === 'object') return JSON.stringify(v)
  return String(v)
}

export function RevertConfirmDialog({ entry, onReverted, onCancel }: RevertConfirmDialogProps) {
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState<string | null>(null)
  const cancelRef              = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    cancelRef.current?.focus()
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onCancel() }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onCancel])

  async function handleConfirm() {
    setLoading(true)
    setError(null)
    try {
      const resp = await fetch(`/api/admin/aiops/audit/${entry.id}/revert`, { method: 'POST' })
      if (!resp.ok) {
        const body = await resp.json().catch(() => ({})) as { error?: { message?: string } }
        setError(body?.error?.message ?? 'Revert failed')
        return
      }
      onReverted()
    } catch {
      setError('Network error — please retry')
    } finally {
      setLoading(false)
    }
  }

  const scope = [entry.stack, entry.call_type, entry.param_name].filter(Boolean).join(' / ')

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="revert-dialog-title"
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60"
    >
      <div className="w-full max-w-md rounded-xl border border-border bg-card p-6 shadow-2xl">
        <h2
          id="revert-dialog-title"
          className="text-base font-semibold text-foreground"
        >
          Revert this change?
        </h2>

        <div className="mt-3 space-y-1 text-xs text-muted-foreground">
          <p><span className="font-medium text-foreground">Action:</span> {entry.action}</p>
          {scope && <p><span className="font-medium text-foreground">Scope:</span> {scope}</p>}
          <div className="mt-2 rounded border border-border bg-muted/30 p-3 font-mono text-[11px]">
            <div className="text-red-400 line-through">Before: {describeValue(entry.before_value)}</div>
            <div className="text-green-400">After: {describeValue(entry.after_value)}</div>
          </div>
          <p className="pt-1 text-muted-foreground/70">
            This will restore the &ldquo;Before&rdquo; state. The revert itself is also recorded in the audit log.
          </p>
        </div>

        {error && (
          <p role="alert" className="mt-3 text-xs text-red-400">{error}</p>
        )}

        <div className="mt-4 flex gap-3 justify-end">
          <button
            ref={cancelRef}
            type="button"
            onClick={onCancel}
            disabled={loading}
            className="rounded border border-border bg-muted/30 px-3 py-1.5 text-xs text-foreground hover:bg-muted/50 disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleConfirm}
            disabled={loading}
            className="rounded border border-red-500/40 bg-red-500/10 px-3 py-1.5 text-xs text-red-400 hover:bg-red-500/20 disabled:opacity-50"
          >
            {loading ? 'Reverting…' : 'Confirm Revert'}
          </button>
        </div>
      </div>
    </div>
  )
}
