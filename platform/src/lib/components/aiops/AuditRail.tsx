'use client'

import { useState, useEffect } from 'react'
import type { LlmConfigAuditRow } from '@/lib/db/schema/aiops'

interface AuditResponse {
  rows:  LlmConfigAuditRow[]
  count: number
}

export function AuditRail() {
  const [rows,    setRows]    = useState<LlmConfigAuditRow[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('/api/admin/aiops/audit?limit=20')
      .then(r => r.json() as Promise<AuditResponse>)
      .then(data => setRows(data.rows ?? []))
      .catch(() => {/* silently fail */})
      .finally(() => setLoading(false))
  }, [])

  return (
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
              <span className="font-mono text-foreground">{row.action}</span>
              {row.stack && <span> · {row.stack}</span>}
              {row.call_type && <span>/{row.call_type}</span>}
              <span className="block">{new Date(row.occurred_at).toLocaleTimeString()}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
