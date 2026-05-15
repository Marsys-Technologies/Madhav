'use client'

import * as React from 'react'
import type { QueryLogRow } from '@/lib/performance/api_client'

interface Props {
  rows: QueryLogRow[]
  total: number
  page: number
  pageSize: number
  onPageChange: (page: number) => void
  onRowClick?: (row: QueryLogRow) => void
}

function fmt(v: unknown): string {
  if (v === null || v === undefined) return '—'
  if (typeof v === 'boolean') return v ? 'yes' : 'no'
  if (typeof v === 'number') return v.toString()
  return String(v)
}

export function QueryLogTable({ rows, total, page, pageSize, onPageChange, onRowClick }: Props) {
  const maxPage = Math.max(1, Math.ceil(total / pageSize))
  const thClass = 'bt-label bt-label-upper px-3 py-2.5 text-left whitespace-nowrap'
  const pagBtn = 'rounded border px-2 py-0.5 text-xs transition-colors disabled:opacity-30'

  return (
    <div className="rounded-lg border bg-card">
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead className="border-b" style={{ borderColor: 'rgba(212,175,55,0.12)', background: 'rgba(212,175,55,0.04)' }}>
            <tr>
              <th className={thClass}>Timestamp</th>
              <th className={thClass}>Source</th>
              <th className={thClass}>Class</th>
              <th className={thClass}>Plan type</th>
              <th className={thClass}>Plan accuracy</th>
              <th className={thClass}>Validator</th>
              <th className={thClass}>B.10</th>
              <th className={thClass}>B.11</th>
              <th className={thClass}>Cit.</th>
              <th className={thClass}>Latency (ms)</th>
              <th className={thClass}>Synthesis</th>
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 && (
              <tr>
                <td colSpan={11} className="px-3 py-8 text-center text-muted-foreground">
                  No queries in this window with the current filters.
                </td>
              </tr>
            )}
            {rows.map((r) => (
              <tr
                key={r.id}
                className="cursor-pointer border-b last:border-0 transition-colors"
                style={{ borderColor: 'rgba(212,175,55,0.08)' }}
                onClick={() => onRowClick?.(r)}
                onMouseEnter={e => { e.currentTarget.style.background = 'rgba(212,175,55,0.05)' }}
                onMouseLeave={e => { e.currentTarget.style.background = '' }}
              >
                <td className="px-3 py-2 font-mono text-[10px] text-muted-foreground">
                  {new Date(r.created_at).toLocaleString()}
                </td>
                <td className="px-3 py-2">{r.source}</td>
                <td className="px-3 py-2">{fmt(r.query_class)}</td>
                <td className="px-3 py-2">{fmt(r.plan_type)}</td>
                <td className="px-3 py-2">{fmt(r.plan_accuracy_label)}</td>
                <td className="px-3 py-2">{fmt(r.validator_verdict)}</td>
                <td className={`px-3 py-2 ${r.b10_violation ? 'text-[var(--status-halt)]' : 'text-[var(--status-success)]'}`}>{r.b10_violation ? '!' : '✓'}</td>
                <td className={`px-3 py-2 ${r.b11_violation ? 'text-[var(--status-halt)]' : 'text-[var(--status-success)]'}`}>{r.b11_violation ? '!' : '✓'}</td>
                <td className="px-3 py-2">{fmt(r.citation_count)}</td>
                <td className="px-3 py-2 tabular-nums">{fmt(r.latency_total_ms)}</td>
                <td className="px-3 py-2">{fmt(r.synthesis_status)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="flex items-center justify-between border-t px-3 py-2 text-xs text-muted-foreground" style={{ borderColor: 'rgba(212,175,55,0.12)' }}>
        <span>Page {page} of {maxPage} · {total} total</span>
        <span className="flex gap-1">
          <button
            disabled={page <= 1}
            onClick={() => onPageChange(page - 1)}
            className={pagBtn}
            style={{ borderColor: 'rgba(212,175,55,0.20)' }}
          >
            Prev
          </button>
          <button
            disabled={page >= maxPage}
            onClick={() => onPageChange(page + 1)}
            className={pagBtn}
            style={{ borderColor: 'rgba(212,175,55,0.20)' }}
          >
            Next
          </button>
        </span>
      </div>
    </div>
  )
}
