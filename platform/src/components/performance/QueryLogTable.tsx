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
  return (
    <div className="rounded-lg border bg-card">
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead className="border-b bg-muted/40">
            <tr className="text-left">
              <th className="px-3 py-2">Timestamp</th>
              <th className="px-3 py-2">Source</th>
              <th className="px-3 py-2">Class</th>
              <th className="px-3 py-2">Plan type</th>
              <th className="px-3 py-2">Plan accuracy</th>
              <th className="px-3 py-2">Validator</th>
              <th className="px-3 py-2">B.10</th>
              <th className="px-3 py-2">B.11</th>
              <th className="px-3 py-2">Cit.</th>
              <th className="px-3 py-2">Latency (ms)</th>
              <th className="px-3 py-2">Synthesis</th>
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 && (
              <tr>
                <td colSpan={11} className="px-3 py-6 text-center text-muted-foreground">
                  No queries in this window with the current filters.
                </td>
              </tr>
            )}
            {rows.map((r) => (
              <tr
                key={r.id}
                className="cursor-pointer border-b last:border-0 hover:bg-muted/40"
                onClick={() => onRowClick?.(r)}
              >
                <td className="px-3 py-1.5 font-mono text-[10px]">
                  {new Date(r.created_at).toLocaleString()}
                </td>
                <td className="px-3 py-1.5">{r.source}</td>
                <td className="px-3 py-1.5">{fmt(r.query_class)}</td>
                <td className="px-3 py-1.5">{fmt(r.plan_type)}</td>
                <td className="px-3 py-1.5">{fmt(r.plan_accuracy_label)}</td>
                <td className="px-3 py-1.5">{fmt(r.validator_verdict)}</td>
                <td className={`px-3 py-1.5 ${r.b10_violation ? 'text-rose-500' : ''}`}>{r.b10_violation ? '!' : '✓'}</td>
                <td className={`px-3 py-1.5 ${r.b11_violation ? 'text-rose-500' : ''}`}>{r.b11_violation ? '!' : '✓'}</td>
                <td className="px-3 py-1.5">{fmt(r.citation_count)}</td>
                <td className="px-3 py-1.5">{fmt(r.latency_total_ms)}</td>
                <td className="px-3 py-1.5">{fmt(r.synthesis_status)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="flex items-center justify-between border-t px-3 py-2 text-xs text-muted-foreground">
        <span>
          Page {page} of {maxPage} · {total} total
        </span>
        <span className="flex gap-1">
          <button
            disabled={page <= 1}
            onClick={() => onPageChange(page - 1)}
            className="rounded border px-2 py-0.5 disabled:opacity-40"
          >
            Prev
          </button>
          <button
            disabled={page >= maxPage}
            onClick={() => onPageChange(page + 1)}
            className="rounded border px-2 py-0.5 disabled:opacity-40"
          >
            Next
          </button>
        </span>
      </div>
    </div>
  )
}
