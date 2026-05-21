'use client'

import * as React from 'react'

// ── Types ─────────────────────────────────────────────────────────────────────

export interface ToolDiagnostic {
  toolName: string
  errorRate: number
  emptyRate: number
  schemaMismatches: number
}

export interface RecentFailure {
  toolName: string
  timestamp: Date
  message: string
}

export interface DiagnosticsSectionProps {
  toolDiagnostics: ToolDiagnostic[]
  recentFailures: RecentFailure[]
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function pct(v: number): string {
  return `${(v * 100).toFixed(1)}%`
}

function formatTs(d: Date): string {
  return d.toISOString().replace('T', ' ').slice(0, 19) + ' UTC'
}

// ── Tool row ──────────────────────────────────────────────────────────────────

function ToolDiagRow({ row }: { row: ToolDiagnostic }) {
  const hasError = row.errorRate > 0.05
  const hasEmpty = row.emptyRate > 0.2
  const hasMismatch = row.schemaMismatches > 0

  return (
    <tr
      className="border-b"
      style={{ borderColor: 'rgba(var(--brand-gold-rgb),0.08)' }}
    >
      <td className="py-2 pr-3 font-mono text-[12px] text-foreground">
        {row.toolName}
      </td>
      <td
        className="py-2 pr-3 text-[12px] tabular-nums"
        style={{ color: hasError ? 'var(--status-error,#ef4444)' : 'var(--status-success,#22c55e)' }}
      >
        {pct(row.errorRate)}
      </td>
      <td
        className="py-2 pr-3 text-[12px] tabular-nums"
        style={{ color: hasEmpty ? 'var(--status-warn,#f59e0b)' : 'inherit' }}
      >
        {pct(row.emptyRate)}
      </td>
      <td
        className="py-2 text-[12px] tabular-nums"
        style={{ color: hasMismatch ? 'var(--status-error,#ef4444)' : 'inherit' }}
      >
        {row.schemaMismatches}
      </td>
    </tr>
  )
}

// ── Failure row ───────────────────────────────────────────────────────────────

function FailureRow({ failure }: { failure: RecentFailure }) {
  return (
    <li
      className="rounded border p-3 text-[12px]"
      style={{
        borderColor: 'rgba(var(--status-error-rgb,220,38,38),0.15)',
        background: 'rgba(var(--status-error-rgb,220,38,38),0.04)',
      }}
    >
      <div className="flex items-baseline justify-between gap-2">
        <span className="font-mono font-medium text-foreground">{failure.toolName}</span>
        <span className="shrink-0 text-muted-foreground tabular-nums">{formatTs(failure.timestamp)}</span>
      </div>
      <p className="mt-1 text-muted-foreground">{failure.message}</p>
    </li>
  )
}

// ── Main component ────────────────────────────────────────────────────────────

export function DiagnosticsSection({
  toolDiagnostics,
  recentFailures,
}: DiagnosticsSectionProps) {
  return (
    <section className="space-y-4" data-testid="diagnostics-section">
      <div className="flex items-baseline justify-between">
        <h2 className="bt-label bt-label-upper" style={{ color: 'var(--brand-gold)' }}>
          Tool Diagnostics
        </h2>
        <span className="text-xs text-muted-foreground">
          {toolDiagnostics.length} tool{toolDiagnostics.length !== 1 ? 's' : ''}
        </span>
      </div>

      {/* Per-tool metrics table */}
      {toolDiagnostics.length === 0 ? (
        <p className="text-sm text-muted-foreground">No tool diagnostics available.</p>
      ) : (
        <div
          className="overflow-x-auto rounded border"
          style={{ borderColor: 'rgba(var(--brand-gold-rgb),0.12)' }}
        >
          <table className="w-full">
            <thead>
              <tr
                className="border-b text-left text-[11px] uppercase text-muted-foreground/60"
                style={{ borderColor: 'rgba(var(--brand-gold-rgb),0.10)' }}
              >
                <th className="pb-2 pl-3 pr-3 pt-2 font-normal">Tool</th>
                <th className="pb-2 pr-3 pt-2 font-normal">Error rate</th>
                <th className="pb-2 pr-3 pt-2 font-normal">Empty rate</th>
                <th className="pb-2 pr-3 pt-2 font-normal">Schema mismatches</th>
              </tr>
            </thead>
            <tbody className="pl-3">
              {toolDiagnostics.map(row => (
                <ToolDiagRow key={row.toolName} row={row} />
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Recent failures */}
      <div>
        <h3
          className="bt-label mb-2 text-[12px]"
          style={{ color: 'var(--brand-gold)' }}
        >
          Recent failures
        </h3>
        {recentFailures.length === 0 ? (
          <p
            className="rounded border p-3 text-sm"
            style={{
              borderColor: 'rgba(var(--status-success-rgb,34,197,94),0.2)',
              background: 'rgba(var(--status-success-rgb,34,197,94),0.04)',
              color: 'var(--status-success,#22c55e)',
            }}
            data-testid="no-failures-state"
          >
            No failures recorded.
          </p>
        ) : (
          <ul className="space-y-2" data-testid="failures-list">
            {recentFailures.map((f, i) => (
              <FailureRow key={`${f.toolName}-${i}`} failure={f} />
            ))}
          </ul>
        )}
      </div>
    </section>
  )
}
