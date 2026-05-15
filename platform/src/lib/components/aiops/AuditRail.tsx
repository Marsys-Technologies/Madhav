'use client'

import { useState, useEffect, useCallback, useMemo } from 'react'
import type { LlmConfigAuditRow, AiopsAction } from '@/lib/db/schema/aiops'
import { RevertConfirmDialog } from './RevertConfirmDialog'
import {
  ACTION_DISPLAY,
  STACK_DISPLAY,
  CALL_TYPE_DISPLAY,
  PARAM_DISPLAY,
  displayOf,
} from './displayNames'
import type { ParamName } from './displayNames'
import type { CallType, ModelStack } from '@/lib/models/registry'

interface AuditResponse {
  rows:  LlmConfigAuditRow[]
  count: number
}

const REVERTIBLE_ACTIONS: AiopsAction[] = ['set_stack', 'set_routing', 'set_param', 'reset_param', 'reset_routing']

const PROPAGATION_TTL_MS = 60_000

export function AuditRail() {
  const [rows,          setRows]          = useState<LlmConfigAuditRow[]>([])
  const [loading,       setLoading]       = useState(true)
  const [revertTarget,  setRevertTarget]  = useState<LlmConfigAuditRow | null>(null)
  const [now,           setNow]           = useState<number>(() => Date.now())

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

  // Countdown ticker (1 Hz). Derives the propagation window from `now` state
  // (which is updated via setInterval) rather than calling Date.now() during render.
  const latest = rows[0]
  const latestMs = latest ? new Date(latest.occurred_at).getTime() : 0
  const withinWindow = latest != null && (now - latestMs) < PROPAGATION_TTL_MS

  useEffect(() => {
    if (!withinWindow) return
    const id = window.setInterval(() => setNow(Date.now()), 1000)
    return () => window.clearInterval(id)
  }, [withinWindow])

  const propagation = useMemo(() => {
    if (!latest) return null
    const elapsed = now - latestMs
    if (elapsed >= PROPAGATION_TTL_MS) return null
    const remaining = PROPAGATION_TTL_MS - elapsed
    return {
      elapsedSec: Math.max(0, Math.floor(elapsed / 1000)),
      remainingSec: Math.max(0, Math.ceil(remaining / 1000)),
      pct: Math.max(0, Math.min(100, (remaining / PROPAGATION_TTL_MS) * 100)),
    }
  }, [latest, latestMs, now])

  return (
    <>
      <div className="rounded-lg border border-border bg-card p-4">
        <h3 className="bt-label bt-label-upper">Recent Changes</h3>

        {/* Propagation countdown (visible only when within TTL window) */}
        {propagation && (
          <div className="mt-2 rounded border border-[rgba(var(--brand-gold-rgb),0.18)] bg-[rgba(var(--brand-gold-rgb),0.05)] px-2 py-1.5">
            <div className="flex items-center justify-between text-[10px] text-muted-foreground">
              <span>Last change {propagation.elapsedSec}s ago</span>
              <span style={{ color: 'var(--brand-gold)' }}>
                propagating · {propagation.remainingSec}s
              </span>
            </div>
            <div className="mt-1 h-0.5 w-full overflow-hidden rounded-full bg-[rgba(var(--brand-gold-rgb),0.10)]">
              <div
                className="h-full rounded-full transition-[width] duration-1000 ease-linear"
                style={{ width: `${propagation.pct}%`, background: 'var(--brand-gold)' }}
              />
            </div>
          </div>
        )}

        {loading ? (
          <p className="mt-2 text-xs text-muted-foreground">Loading…</p>
        ) : rows.length === 0 ? (
          <p className="mt-2 text-xs text-muted-foreground">No changes yet.</p>
        ) : (
          <ul className="mt-2 space-y-2">
            {rows.map(row => (
              <AuditEntry
                key={row.id}
                row={row}
                onRevert={REVERTIBLE_ACTIONS.includes(row.action) ? () => setRevertTarget(row) : null}
              />
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

function AuditEntry({ row, onRevert }: { row: LlmConfigAuditRow; onRevert: (() => void) | null }) {
  const time = new Date(row.occurred_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
  const subject = formatSubject(row)
  const diff = formatDiff(row)

  return (
    <li className="text-[10px] text-muted-foreground">
      <div className="flex items-start justify-between gap-1">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-1.5">
            <span className="text-foreground">{actionLabel(row.action)}</span>
            {subject && <span className="text-muted-foreground/80">· {subject}</span>}
          </div>
          {diff && (
            <p className="mt-0.5 truncate font-mono text-[10px]" title={diff.full}>
              <span className="text-muted-foreground/60">{diff.before}</span>
              <span className="mx-1" style={{ color: 'var(--brand-gold)' }}>→</span>
              <span className="text-foreground">{diff.after}</span>
            </p>
          )}
          <span className="block text-[9px] text-muted-foreground/60">{time}</span>
        </div>
        {onRevert && (
          <button
            type="button"
            onClick={onRevert}
            className="shrink-0 rounded p-1 text-[12px] text-muted-foreground/70 hover:bg-[rgba(var(--brand-gold-rgb),0.10)] hover:text-[var(--brand-gold)]"
            aria-label={`Revert change ${row.id}`}
            title="Revert this change"
          >
            ↩
          </button>
        )}
      </div>
    </li>
  )
}

function actionLabel(action: AiopsAction): string {
  return ACTION_DISPLAY[action] ?? action
}

function formatSubject(row: LlmConfigAuditRow): string {
  const parts: string[] = []
  if (row.stack)      parts.push(displayOf(STACK_DISPLAY, row.stack as ModelStack))
  if (row.call_type)  parts.push(displayOf(CALL_TYPE_DISPLAY, row.call_type as CallType))
  if (row.param_name) parts.push(displayOf(PARAM_DISPLAY, row.param_name as ParamName))
  return parts.join(' · ')
}

interface Diff {
  before: string
  after:  string
  full:   string
}

function formatDiff(row: LlmConfigAuditRow): Diff | null {
  const before = row.before_value
  const after  = row.after_value
  if (before === null && after === null) return null

  // Actions whose values are stack identifiers (e.g. 'deepseek') get
  // routed through STACK_DISPLAY so the user sees "DeepSeek" not "deepseek".
  // Cast through string because the API in practice emits 'set_active_stack',
  // which the schema's AiopsAction union does not yet include.
  const action = row.action as string
  const isStackAction = action === 'set_stack' || action === 'set_active_stack'

  const beforeStr = formatValue(before, isStackAction)
  const afterStr  = formatValue(after, isStackAction)
  if (beforeStr === afterStr) return null
  return {
    before: truncate(beforeStr, 28),
    after:  truncate(afterStr, 28),
    full:   `${beforeStr} → ${afterStr}`,
  }
}

function formatValue(v: unknown, isStack = false): string {
  if (v === null || v === undefined) return '—'
  if (typeof v === 'string') {
    return isStack ? displayOf(STACK_DISPLAY, v as ModelStack) : v
  }
  if (typeof v === 'number' || typeof v === 'boolean') return String(v)
  if (typeof v === 'object') {
    // routing override shape: { primary_model, fallback_model }
    const rec = v as Record<string, unknown>
    if ('primary_model' in rec && 'fallback_model' in rec) {
      return `p:${rec.primary_model} f:${rec.fallback_model}`
    }
    if ('primary_model' in rec) return String(rec.primary_model)
    if ('active_stack' in rec) {
      const s = String(rec.active_stack)
      return displayOf(STACK_DISPLAY, s as ModelStack)
    }
    if ('param_value' in rec) return formatValue(rec.param_value)
    return JSON.stringify(v)
  }
  return String(v)
}

function truncate(s: string, max: number): string {
  if (s.length <= max) return s
  return s.slice(0, max - 1) + '…'
}
