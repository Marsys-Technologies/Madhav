'use client'

import { useState, useEffect, useCallback } from 'react'
import type { LlmConfigAuditRow } from '@/lib/db/schema/aiops'
import { RevertConfirmDialog } from './RevertConfirmDialog'

interface AuditResponse {
  rows:  LlmConfigAuditRow[]
  count: number
}

const REVERTIBLE_ACTIONS = ['set_stack', 'set_routing', 'set_param', 'reset_param', 'reset_routing']

export function AuditRail() {
  const [rows,          setRows]          = useState<LlmConfigAuditRow[]>([])
  const [loading,       setLoading]       = useState(true)
  const [revertTarget,  setRevertTarget]  = useState<LlmConfigAuditRow | null>(null)

  const load = useCallback(() => {
    setLoading(true)
    fetch('/api/admin/aiops/audit?limit=20')
      .then(r => r.json() as Promise<AuditResponse>)
      .then(data => setRows(data.rows ?? []))
      .catch(() => null)
      .finally(() => setLoading(false))
  }, [])

  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { load() }, [load])

  return (
    <>
      <div className="rounded-lg border border-border bg-card p-4">
        <h3 className="text-sm font-semibold text-foreground">Recent Changes</h3>
        {loading ? (
          <p className="mt-2 text-xs text-muted-foreground">Loading…</p>
        ) : rows.length === 0 ? (
          <p className="mt-2 text-xs text-muted-foreground">No changes yet.</p>
        ) : (
          <ul className="mt-2 space-y-1.5">
            {rows.map(row => (
              <li key={row.id} className="text-[10px] text-muted-foreground">
                <div className="flex items-start justify-between gap-1">
                  <div>
                    <span className="font-mono text-foreground">{row.action}</span>
                    {row.stack && <span> · {row.stack}</span>}
                    {row.call_type && <span>/{row.call_type}</span>}
                    <span className="block">{new Date(row.occurred_at).toLocaleTimeString()}</span>
                  </div>
                  {REVERTIBLE_ACTIONS.includes(row.action) && (
                    <button
                      type="button"
                      onClick={() => setRevertTarget(row)}
                      className="shrink-0 rounded px-1 py-0.5 text-[9px] text-muted-foreground/60 hover:bg-muted/40 hover:text-foreground"
                      aria-label={`Revert change ${row.id}`}
                    >
                      ↩
                    </button>
                  )}
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>

      {revertTarget && (
        <RevertConfirmDialog
          entry={revertTarget}
          onReverted={() => {
            setRevertTarget(null)
            load()
          }}
          onCancel={() => setRevertTarget(null)}
        />
      )}
    </>
  )
}
