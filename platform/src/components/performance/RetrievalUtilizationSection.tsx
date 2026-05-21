'use client'

import * as React from 'react'
import type { RetrievalStats, ToolStats } from '@/lib/performance/retrieval_aggregator'

function ScoreCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div
      className="flex flex-col gap-1 rounded border p-3 text-center"
      style={{ borderColor: 'rgba(212,175,55,0.18)', background: 'rgba(212,175,55,0.04)' }}
    >
      <span
        className="text-2xl font-semibold tabular-nums"
        style={{ color: 'var(--brand-gold-cream)' }}
      >
        {value}
      </span>
      <span className="text-xs" style={{ color: 'var(--brand-muted)' }}>{label}</span>
    </div>
  )
}

function StatusBadge({ isOrphaned }: { isOrphaned: boolean }) {
  if (isOrphaned) {
    return (
      <span
        className="rounded-full px-2 py-0.5 text-xs font-medium"
        style={{ background: 'rgba(234,179,8,0.15)', color: 'rgb(234,179,8)' }}
      >
        Orphaned
      </span>
    )
  }
  return (
    <span
      className="rounded-full px-2 py-0.5 text-xs font-medium"
      style={{ background: 'rgba(34,197,94,0.12)', color: 'rgb(34,197,94)' }}
    >
      Active
    </span>
  )
}

function formatDate(iso: string | null): string {
  if (!iso) return '—'
  try {
    return new Date(iso).toLocaleString('en-US', {
      month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
    })
  } catch {
    return iso
  }
}

export function RetrievalUtilizationSection() {
  const [data, setData] = React.useState<RetrievalStats | null>(null)
  const [loading, setLoading] = React.useState(true)
  const [error, setError] = React.useState<string | null>(null)

  React.useEffect(() => {
    setLoading(true)
    fetch('/api/performance/retrieval-stats?window=168')
      .then(r => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        return r.json() as Promise<RetrievalStats>
      })
      .then(d => { setData(d); setLoading(false) })
      .catch(e => { setError(String(e)); setLoading(false) })
  }, [])

  if (loading) {
    return (
      <p className="text-xs" style={{ color: 'var(--brand-muted)' }}>Loading retrieval utilization…</p>
    )
  }

  if (error || !data) {
    return (
      <p className="text-xs" style={{ color: 'rgb(239,68,68)' }}>
        Failed to load retrieval stats: {error ?? 'unknown error'}
      </p>
    )
  }

  const { coverage_scoreboard, orphaned_tools, tools } = data

  return (
    <div className="space-y-4">
      {/* Coverage scoreboard */}
      <div className="grid grid-cols-3 gap-3">
        <ScoreCard label="Total tools" value={coverage_scoreboard.total_tools} />
        <ScoreCard label="Called ≥1× in 7d" value={coverage_scoreboard.tools_called_at_least_once} />
        <ScoreCard label="% coverage" value={`${coverage_scoreboard.pct_coverage}%`} />
      </div>

      {/* Orphaned tools callout */}
      {orphaned_tools.length === 0 ? (
        <div
          className="rounded border px-3 py-2 text-xs font-medium"
          style={{ borderColor: 'rgba(34,197,94,0.25)', background: 'rgba(34,197,94,0.07)', color: 'rgb(34,197,94)' }}
        >
          All tools called in the last 7 days
        </div>
      ) : (
        <div
          className="rounded border px-3 py-2 text-xs"
          style={{ borderColor: 'rgba(234,179,8,0.30)', background: 'rgba(234,179,8,0.06)', color: 'rgb(234,179,8)' }}
        >
          <span className="font-semibold">Orphaned tools (zero-call, 7d):</span>{' '}
          {orphaned_tools.join(', ')}
        </div>
      )}

      {/* Tool utilization table */}
      <div className="overflow-x-auto rounded border" style={{ borderColor: 'rgba(212,175,55,0.15)' }}>
        <table className="w-full text-xs">
          <thead>
            <tr style={{ borderBottom: '1px solid rgba(212,175,55,0.12)', background: 'rgba(212,175,55,0.05)' }}>
              <th className="px-3 py-2 text-left font-medium" style={{ color: 'var(--brand-gold)' }}>Tool name</th>
              <th className="px-3 py-2 text-right font-medium" style={{ color: 'var(--brand-gold)' }}>Calls (7d)</th>
              <th className="px-3 py-2 text-left font-medium" style={{ color: 'var(--brand-gold)' }}>Last called</th>
              <th className="px-3 py-2 text-left font-medium" style={{ color: 'var(--brand-gold)' }}>Status</th>
            </tr>
          </thead>
          <tbody>
            {tools.map((t: ToolStats, i: number) => (
              <tr
                key={t.tool_name}
                style={{
                  borderBottom: i < tools.length - 1 ? '1px solid rgba(212,175,55,0.07)' : undefined,
                  background: t.is_orphaned ? 'rgba(234,179,8,0.03)' : undefined,
                }}
              >
                <td className="px-3 py-1.5 font-mono" style={{ color: 'var(--brand-gold-cream)' }}>
                  {t.tool_name}
                </td>
                <td className="px-3 py-1.5 text-right tabular-nums" style={{ color: 'var(--brand-gold-cream)' }}>
                  {t.call_count}
                </td>
                <td className="px-3 py-1.5" style={{ color: 'var(--brand-muted)' }}>
                  {formatDate(t.last_called_at)}
                </td>
                <td className="px-3 py-1.5">
                  <StatusBadge isOrphaned={t.is_orphaned} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
