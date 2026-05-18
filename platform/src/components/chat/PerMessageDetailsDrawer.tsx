'use client'

/**
 * PerMessageDetailsDrawer — β6
 *
 * Shows model, token counts, latency, validators, disclosure tier,
 * citation count, cost, and a "View trace" stub link for a single assistant message.
 *
 * Data sources:
 *   - message.metadata.custom  → model, stack, style, disclosure_tier, queryId, query_class, latency (reload path)
 *   - message.content (DataMessagePart) → data-cost (tokens + dollars), data-citation-gate (result)
 *   - prop: citationCount (passed from the V2AssistantText renderer)
 */

import { useContext, useEffect, useRef } from 'react'
import { useMessage } from '@assistant-ui/react'

// ─── Helpers ──────────────────────────────────────────────────────────────────

function MetaRow({ label, value, testid }: { label: string; value: React.ReactNode; testid?: string }) {
  if (value === null || value === undefined || value === '') return null
  return (
    <div
      className="flex items-start justify-between gap-4 py-1.5 border-b border-zinc-800/60 last:border-0"
      data-testid={testid}
    >
      <span className="text-xs text-zinc-500 shrink-0">{label}</span>
      <span className="text-xs text-zinc-200 text-right font-mono break-all">{value}</span>
    </div>
  )
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="mb-4">
      <p className="text-[10px] font-semibold uppercase tracking-widest text-zinc-600 mb-1">{title}</p>
      {children}
    </div>
  )
}

// ─── Drawer ───────────────────────────────────────────────────────────────────

interface PerMessageDetailsDrawerProps {
  open: boolean
  onClose: () => void
  citationCount?: number
  /** γ6: show cost section for non-admin users. Super-admin always sees cost. */
  costVisible?: boolean
}

export function PerMessageDetailsDrawer({
  open,
  onClose,
  citationCount,
  costVisible = false,
}: PerMessageDetailsDrawerProps) {
  const message = useMessage()
  const drawerRef = useRef<HTMLDivElement>(null)

  // Close on Escape
  useEffect(() => {
    if (!open) return
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, onClose])

  // Move focus into drawer when opened
  useEffect(() => {
    if (open) {
      setTimeout(() => drawerRef.current?.focus(), 50)
    }
  }, [open])

  if (!open) return null

  // ── Extract metadata ──────────────────────────────────────────────────────
  // Reload path: database-persisted metadata_json wraps fields in .custom.
  // Live stream: messageMetadata callback is ignored by assistant-stream; .custom is always {}.
  const meta = (message.metadata?.custom ?? {}) as Record<string, unknown>

  // ── Extract data parts ────────────────────────────────────────────────────
  // @assistant-ui/react-ai-sdk's convertMessage.js converts writer.write({ type: 'data-cost', ... })
  // stream chunks into DataMessagePart ({ type: 'data', name: 'cost', data: {...} }) in message.content.
  type NamedDataPart = { type: 'data'; name: string; data: Record<string, unknown> }
  const namedDataParts = (message.content as ReadonlyArray<unknown>).filter(
    (p): p is NamedDataPart =>
      typeof p === 'object' && p !== null &&
      (p as Record<string, unknown>).type === 'data' &&
      typeof (p as Record<string, unknown>).name === 'string' &&
      typeof (p as Record<string, unknown>).data === 'object' &&
      (p as Record<string, unknown>).data !== null,
  )

  const costEntry = namedDataParts.find(p => p.name === 'cost')
  const cost = costEntry?.data as {
    model?: string
    input_tokens?: number
    output_tokens?: number
    reasoning_tokens?: number
    dollars?: number
    ms?: number
  } | undefined

  const gateEntry = namedDataParts.find(p => p.name === 'citation-gate')
  const gate = gateEntry?.data as { status?: string; issues?: string[] } | undefined

  // γ5: observability data part carries query_id (primary source); fall back to metadata.custom.queryId
  const obsEntry = namedDataParts.find(p => p.name === 'observability')
  const obsQueryId = (obsEntry?.data as { query_id?: string } | undefined)?.query_id

  // ── Format helpers ────────────────────────────────────────────────────────
  const fmt = (n: number | undefined) => n != null ? n.toLocaleString() : '—'
  const fmtMs = (n: number | undefined) => n != null ? `${n.toLocaleString()} ms` : '—'
  const fmtUsd = (n: number | undefined) => n != null ? `$${n.toFixed(5)}` : '—'

  const totalTokens =
    (cost?.input_tokens ?? 0) + (cost?.output_tokens ?? 0)

  const isSuperAdmin = (meta.disclosure_tier as string | undefined) === 'super_admin'
  const showCost = isSuperAdmin || costVisible

  const queryId = obsQueryId ?? (meta.queryId as string | undefined)
  const traceUrl = queryId ? `/observatory/trace/${queryId}` : null

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-40 bg-black/40"
        onClick={onClose}
        aria-hidden="true"
        data-testid="v2-details-backdrop"
      />

      {/* Drawer panel */}
      <div
        ref={drawerRef}
        role="dialog"
        aria-label="Message details"
        aria-modal="true"
        tabIndex={-1}
        className="fixed right-0 top-0 bottom-0 z-50 w-80 bg-zinc-950 border-l border-zinc-800 overflow-y-auto flex flex-col focus:outline-none"
        data-testid="v2-details-drawer"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-zinc-800 shrink-0">
          <h2 className="text-sm font-semibold text-zinc-100">Message details</h2>
          <button
            type="button"
            onClick={onClose}
            className="flex h-6 w-6 items-center justify-center rounded text-zinc-500 hover:bg-zinc-800 hover:text-zinc-300 transition-colors"
            aria-label="Close details"
            data-testid="v2-details-close"
          >
            ×
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto px-4 py-4">

          <Section title="Model">
            <MetaRow label="Model ID" value={(meta.model as string) || (cost?.model as string)} testid="drawer-model" />
            <MetaRow label="Stack" value={meta.stack as string} />
            <MetaRow label="Query class" value={meta.query_class as string} testid="drawer-query-class" />
            <MetaRow label="Style" value={meta.style as string} />
          </Section>

          <Section title="Tokens">
            <MetaRow label="Input" value={fmt(cost?.input_tokens)} testid="drawer-input-tokens" />
            <MetaRow label="Output" value={fmt(cost?.output_tokens)} testid="drawer-output-tokens" />
            {(cost?.reasoning_tokens ?? 0) > 0 && (
              <MetaRow label="Reasoning" value={fmt(cost?.reasoning_tokens)} testid="drawer-reasoning-tokens" />
            )}
            <MetaRow label="Total" value={fmt(totalTokens || undefined)} />
          </Section>

          <Section title="Latency">
            <MetaRow label="Synthesis" value={fmtMs(cost?.ms)} testid="drawer-latency" />
            <MetaRow label="Planning" value={fmtMs(meta.planning_latency_ms as number)} />
          </Section>

          {showCost && (
            <Section title="Cost">
              <MetaRow label="USD" value={fmtUsd(cost?.dollars)} testid="drawer-cost" />
            </Section>
          )}

          <Section title="Validators">
            <MetaRow
              label="Citation gate"
              value={
                gate?.status ? (
                  <span
                    className={
                      gate.status === 'pass'
                        ? 'text-green-400'
                        : gate.status === 'warn'
                          ? 'text-amber-400'
                          : 'text-red-400'
                    }
                    data-testid="v2-details-citation-gate"
                  >
                    {gate.status.toUpperCase()}
                  </span>
                ) : '—'
              }
            />
            {gate?.issues?.map((issue, i) => (
              <MetaRow key={i} label={i === 0 ? 'Issues' : ''} value={issue} />
            ))}
          </Section>

          <Section title="Context">
            <MetaRow label="Disclosure tier" value={meta.disclosure_tier as string} testid="drawer-disclosure-tier" />
            <MetaRow label="Citations" value={citationCount != null ? String(citationCount) : '—'} />
          </Section>

          {queryId && (
            <Section title="Observability">
              <MetaRow label="Query ID" value={
                <span className="text-[10px] font-mono">{queryId.slice(0, 8)}…</span>
              } />
              {traceUrl ? (
                <div className="pt-1">
                  <a
                    href={traceUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs text-indigo-400 hover:text-indigo-300 underline"
                    data-testid="v2-details-trace-link"
                  >
                    View trace →
                  </a>
                </div>
              ) : null}
            </Section>
          )}
        </div>
      </div>
    </>
  )
}
