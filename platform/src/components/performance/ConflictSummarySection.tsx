'use client'

import * as React from 'react'
import { useQuery } from '@tanstack/react-query'
import type { ConflictSummaryReport, ConflictSummaryEntry, ConflictStatus } from '@/lib/performance/conflict_summary'

// ─────────────────────────────────────────────────────────────────────────────
// Fetcher
// ─────────────────────────────────────────────────────────────────────────────

async function fetchConflictSummary(): Promise<ConflictSummaryReport> {
  const res = await fetch('/api/performance/conflict-summary')
  if (!res.ok) throw new Error(`conflict-summary fetch failed: ${res.status}`)
  return res.json() as Promise<ConflictSummaryReport>
}

// ─────────────────────────────────────────────────────────────────────────────
// Status badge
// ─────────────────────────────────────────────────────────────────────────────

function StatusBadge({ status }: { status: ConflictStatus }) {
  const styles: Record<ConflictStatus, { bg: string; color: string; border: string }> = {
    RESOLVED: {
      bg: 'rgba(34,197,94,0.12)',
      color: 'var(--status-success)',
      border: '1px solid rgba(34,197,94,0.25)',
    },
    PROPOSED: {
      bg: 'rgba(212,175,55,0.12)',
      color: 'var(--brand-gold)',
      border: '1px solid rgba(212,175,55,0.25)',
    },
    OPEN: {
      bg: 'rgba(239,68,68,0.10)',
      color: 'rgba(239,68,68,0.85)',
      border: '1px solid rgba(239,68,68,0.20)',
    },
  }
  const s = styles[status]
  return (
    <span
      className="inline-block rounded px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide"
      style={{ background: s.bg, color: s.color, border: s.border }}
    >
      {status}
    </span>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Conflict row
// ─────────────────────────────────────────────────────────────────────────────

const MAX_DESC = 120

function ConflictRow({ entry }: { entry: ConflictSummaryEntry }) {
  const desc =
    entry.description.length > MAX_DESC
      ? entry.description.slice(0, MAX_DESC) + '…'
      : entry.description

  return (
    <tr
      className="border-b text-xs"
      style={{ borderColor: 'rgba(212,175,55,0.08)' }}
    >
      <td className="py-2 pr-3 font-mono whitespace-nowrap" style={{ color: 'var(--brand-gold-cream)' }}>
        {entry.conflict_id}
      </td>
      <td className="py-2 pr-3 text-center whitespace-nowrap">
        <span
          className="rounded px-1.5 py-0.5 text-[10px] font-semibold"
          style={{ background: 'rgba(212,175,55,0.08)', color: 'var(--brand-gold)' }}
        >
          {entry.conflict_class}
        </span>
      </td>
      <td className="py-2 pr-3 font-mono text-[10px] text-muted-foreground whitespace-nowrap">
        {entry.signal_ids_affected.join(', ')}
      </td>
      <td className="py-2 pr-3 text-muted-foreground" style={{ maxWidth: '28rem' }}>
        {desc}
      </td>
      <td className="py-2 whitespace-nowrap">
        <StatusBadge status={entry.status} />
      </td>
    </tr>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Summary bar
// ─────────────────────────────────────────────────────────────────────────────

function SummaryBar({ report }: { report: ConflictSummaryReport }) {
  return (
    <div className="flex flex-wrap items-center gap-4 text-xs">
      <span className="text-muted-foreground">
        <span style={{ color: 'var(--brand-gold-cream)' }} className="font-semibold">
          {report.total}
        </span>{' '}
        conflict{report.total !== 1 ? 's' : ''} detected
      </span>
      <span style={{ color: 'var(--status-success)' }}>
        {report.resolved_count} resolved
      </span>
      <span style={{ color: 'var(--brand-gold)' }}>
        {report.proposed_count} proposed
      </span>
      <span style={{ color: 'rgba(239,68,68,0.85)' }}>
        {report.open_count} open
      </span>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Main component
// ─────────────────────────────────────────────────────────────────────────────

export function ConflictSummarySection() {
  const q = useQuery({
    queryKey: ['perf-conflict-summary'],
    queryFn: fetchConflictSummary,
    refetchInterval: 60_000,
    refetchOnWindowFocus: true,
  })

  if (q.isPending) {
    return (
      <p className="bt-label text-xs text-muted-foreground animate-pulse">
        Loading conflict summary…
      </p>
    )
  }

  if (q.isError) {
    return (
      <p className="bt-label text-xs" style={{ color: 'var(--status-error)' }}>
        Failed to load conflict summary.
      </p>
    )
  }

  const report = q.data

  if (report.total === 0) {
    return (
      <p className="bt-label text-xs text-muted-foreground italic">
        No conflicts detected in ICR_DETECTOR_OUTPUT.
      </p>
    )
  }

  return (
    <div className="space-y-3">
      <SummaryBar report={report} />
      <div className="overflow-x-auto rounded border" style={{ borderColor: 'rgba(212,175,55,0.12)' }}>
        <table className="w-full text-left">
          <thead>
            <tr
              className="border-b text-[10px] uppercase tracking-wide"
              style={{ borderColor: 'rgba(212,175,55,0.12)', color: 'var(--brand-gold)' }}
            >
              <th className="py-2 pr-3 font-semibold">Conflict ID</th>
              <th className="py-2 pr-3 font-semibold text-center">Class</th>
              <th className="py-2 pr-3 font-semibold">Signal IDs</th>
              <th className="py-2 pr-3 font-semibold">Description</th>
              <th className="py-2 font-semibold">Status</th>
            </tr>
          </thead>
          <tbody>
            {report.entries.map(entry => (
              <ConflictRow key={entry.conflict_id} entry={entry} />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
