/**
 * Sessions tab — recent MCP sessions/traces table.
 *
 * Fetches from /api/mcp/recent (built in S1/v1 MCP workstream).
 * Shows: trace_id, timestamp, tool_name, audience_tier, status, duration,
 *        rows_returned, audit findings count.
 * Click row → opens drill-down with full trace steps.
 *
 * MCPT v3.1.0-S5
 */
'use client'

import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'

// ── Types ─────────────────────────────────────────────────────────────────────

interface TraceRow {
  query_id: string
  user_id?: string
  tool_name?: string
  mcp_tool_name?: string
  audience_tier?: string
  status: 'ok' | 'error' | 'zero_rows' | string
  started_at?: string
  completed_at?: string
  latency_ms?: number | null
  rows_returned?: number | null
  source?: string
  audit_finding_count?: number
}

interface TraceStep {
  step_name: string
  step_seq: number
  status: string
  started_at?: string
  completed_at?: string
  data_summary?: Record<string, unknown>
}

interface TraceDetail {
  trace_id: string
  steps: TraceStep[]
  audit_findings?: Array<{ class: string; severity: string; description: string; attached_at: string }>
}

// ── Fetch helpers ─────────────────────────────────────────────────────────────

async function fetchRecentSessions(limit: number): Promise<TraceRow[]> {
  const res = await fetch(`/api/mcp/recent?limit=${limit}`)
  if (!res.ok) {
    if (res.status === 404) return []
    throw new Error(`Failed to fetch sessions: ${res.status}`)
  }
  const data = await res.json() as { queries?: TraceRow[]; recent?: TraceRow[] }
  return data.queries ?? data.recent ?? []
}

async function fetchTraceDetail(traceId: string): Promise<TraceDetail | null> {
  const res = await fetch(`/api/mcp/trace/${traceId}`)
  if (!res.ok) return null
  const data = await res.json() as { ok: boolean; result?: TraceDetail }
  return data.result ?? null
}

// ── Status badge ──────────────────────────────────────────────────────────────

function StatusBadge({ status }: { status: string }) {
  const cls =
    status === 'ok'        ? 'bg-green-500/10 text-green-400'
    : status === 'error'   ? 'bg-red-500/10 text-red-400'
    : status === 'zero_rows' ? 'bg-yellow-500/10 text-yellow-400'
    : 'bg-muted text-muted-foreground'
  return (
    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${cls}`}>
      {status}
    </span>
  )
}

// ── Trace drill-down modal ────────────────────────────────────────────────────

function TraceModal({ traceId, onClose }: { traceId: string; onClose: () => void }) {
  const detailQuery = useQuery({
    queryKey: ['admin', 'mcp', 'trace', traceId],
    queryFn: () => fetchTraceDetail(traceId),
    staleTime: 300_000,
  })

  const detail = detailQuery.data

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div className="relative max-h-[85vh] w-full max-w-2xl overflow-y-auto rounded-xl border border-border bg-background p-6 shadow-xl">
        <button
          onClick={onClose}
          className="absolute right-4 top-4 text-muted-foreground hover:text-foreground"
        >
          ✕
        </button>
        <h3 className="text-base font-semibold mb-1">Trace Detail</h3>
        <p className="font-mono text-xs text-muted-foreground mb-4">{traceId}</p>

        {detailQuery.isLoading && (
          <p className="text-sm text-muted-foreground animate-pulse">Loading trace…</p>
        )}
        {detailQuery.isError && (
          <p className="text-sm text-red-400">Failed to load trace detail.</p>
        )}
        {detail && (
          <div className="space-y-4">
            {/* Steps */}
            {detail.steps && detail.steps.length > 0 && (
              <div>
                <h4 className="text-sm font-medium mb-2">Steps ({detail.steps.length})</h4>
                <div className="space-y-1">
                  {detail.steps.map(step => (
                    <div key={step.step_seq} className="flex items-center gap-3 text-xs py-1 border-b border-border/20">
                      <span className="text-muted-foreground tabular-nums w-6">{step.step_seq}</span>
                      <span className="font-mono text-brand-gold-cream">{step.step_name}</span>
                      <StatusBadge status={step.status} />
                      {step.data_summary?.rows_returned !== undefined && (
                        <span className="text-muted-foreground">{String(step.data_summary.rows_returned)} rows</span>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Audit findings */}
            {detail.audit_findings && detail.audit_findings.length > 0 && (
              <div>
                <h4 className="text-sm font-medium mb-2">Audit findings</h4>
                <div className="space-y-2">
                  {detail.audit_findings.map((f, i) => (
                    <div
                      key={i}
                      className={`rounded-md p-2 text-xs ${f.severity === 'class_1'
                        ? 'bg-red-500/10 border border-red-500/30'
                        : f.severity === 'warn'
                        ? 'bg-yellow-500/10 border border-yellow-500/30'
                        : 'bg-muted/20'
                      }`}
                    >
                      <div className="flex items-center gap-2 mb-0.5">
                        <code>{f.class}</code>
                        <span className="text-muted-foreground">{f.severity}</span>
                      </div>
                      <p className="text-muted-foreground">{f.description}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {detail.steps?.length === 0 && (
              <p className="text-sm text-muted-foreground">No steps recorded for this trace.</p>
            )}
          </div>
        )}
        {detail === null && !detailQuery.isLoading && (
          <p className="text-sm text-muted-foreground">Trace detail not available (no transcript).</p>
        )}
      </div>
    </div>
  )
}

// ── Component ─────────────────────────────────────────────────────────────────

export function Sessions() {
  const queryClient = useQueryClient()
  const [limit, setLimit] = useState(50)
  const [selectedTrace, setSelectedTrace] = useState<string | null>(null)

  const sessionsQuery = useQuery({
    queryKey: ['admin', 'mcp', 'sessions', limit],
    queryFn: () => fetchRecentSessions(limit),
    staleTime: 30_000,
  })

  const rows = sessionsQuery.data ?? []

  function fmtMs(ms: number | null | undefined): string {
    if (ms === null || ms === undefined) return '—'
    if (ms < 1000) return `${ms.toFixed(0)}ms`
    return `${(ms / 1000).toFixed(1)}s`
  }

  if (sessionsQuery.isError) {
    return <p className="text-sm text-red-400">Failed to load session traces.</p>
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-medium">Recent Sessions / Traces</h2>
        <div className="flex items-center gap-3">
          <select
            value={limit}
            onChange={e => setLimit(Number(e.target.value))}
            className="text-xs rounded border border-border/50 bg-background px-2 py-1"
          >
            <option value={25}>Last 25</option>
            <option value={50}>Last 50</option>
            <option value={100}>Last 100</option>
          </select>
          <button
            onClick={() => queryClient.invalidateQueries({ queryKey: ['admin', 'mcp', 'sessions'] })}
            className="text-xs text-muted-foreground hover:text-foreground underline"
          >
            Refresh
          </button>
        </div>
      </div>

      {sessionsQuery.isLoading ? (
        <p className="text-sm text-muted-foreground animate-pulse">Loading sessions…</p>
      ) : rows.length === 0 ? (
        <div className="rounded-lg border border-border/30 p-6 text-center">
          <p className="text-sm text-muted-foreground">No sessions found. MCP calls will appear here.</p>
        </div>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-border/50">
          <table className="w-full text-sm">
            <thead className="border-b border-border/50 bg-muted/30">
              <tr>
                <th className="px-4 py-2 text-left font-medium text-muted-foreground">Trace ID</th>
                <th className="px-4 py-2 text-left font-medium text-muted-foreground">Tool</th>
                <th className="px-4 py-2 text-left font-medium text-muted-foreground">Tier</th>
                <th className="px-4 py-2 text-left font-medium text-muted-foreground">Status</th>
                <th className="px-4 py-2 text-left font-medium text-muted-foreground">Latency</th>
                <th className="px-4 py-2 text-left font-medium text-muted-foreground">Rows</th>
                <th className="px-4 py-2 text-left font-medium text-muted-foreground">Findings</th>
                <th className="px-4 py-2 text-left font-medium text-muted-foreground">Time</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/30">
              {rows.map(row => (
                <tr
                  key={row.query_id}
                  className="hover:bg-muted/20 cursor-pointer"
                  onClick={() => setSelectedTrace(row.query_id)}
                >
                  <td className="px-4 py-2.5 font-mono text-xs text-muted-foreground">
                    {row.query_id.slice(0, 8)}…
                  </td>
                  <td className="px-4 py-2.5 font-mono text-xs text-brand-gold-cream">
                    {row.mcp_tool_name ?? row.tool_name ?? '—'}
                  </td>
                  <td className="px-4 py-2.5 text-xs text-muted-foreground">
                    {row.audience_tier ?? '—'}
                  </td>
                  <td className="px-4 py-2.5">
                    <StatusBadge status={row.status} />
                  </td>
                  <td className="px-4 py-2.5 text-xs text-muted-foreground tabular-nums">
                    {fmtMs(row.latency_ms)}
                  </td>
                  <td className="px-4 py-2.5 text-xs text-muted-foreground tabular-nums">
                    {row.rows_returned ?? '—'}
                  </td>
                  <td className="px-4 py-2.5">
                    {(row.audit_finding_count ?? 0) > 0 ? (
                      <span className="text-xs text-yellow-400">{row.audit_finding_count}</span>
                    ) : (
                      <span className="text-xs text-muted-foreground">0</span>
                    )}
                  </td>
                  <td className="px-4 py-2.5 text-xs text-muted-foreground whitespace-nowrap">
                    {row.started_at ? new Date(row.started_at).toLocaleString() : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {selectedTrace && (
        <TraceModal traceId={selectedTrace} onClose={() => setSelectedTrace(null)} />
      )}
    </div>
  )
}
