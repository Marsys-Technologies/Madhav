/**
 * DataCoverage tab — per-asset coverage bars (actual vs expected row counts).
 *
 * Fetches from /api/mcp/health/coverage.
 * Displays a progress bar per (tool, category) pair indicating coverage percentage.
 * caveat_class distinguishes data_depth_gap from tool_reliability_gap.
 *
 * MCPT v3.1.0-S5
 */
'use client'

import { useMemo, useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'

// ── Types ─────────────────────────────────────────────────────────────────────

interface CoverageRow {
  tool: string
  category: string
  expected_rows: number
  actual_rows: number | null
  backfill_phase: string
  status: 'active' | 'pending' | 'sparse' | 'missing'
  caveat?: string
  caveat_class?: 'data_depth_gap' | 'tool_reliability_gap'
}

interface CoverageData {
  ok: boolean
  generated_at: string
  coverage: CoverageRow[]
  caveats: Array<{ tool: string; caveat: string; severity: string }>
  note?: string
}

// ── Fetch ─────────────────────────────────────────────────────────────────────

async function fetchCoverage(): Promise<CoverageData> {
  const res = await fetch('/api/mcp/health/coverage')
  if (!res.ok) throw new Error(`Failed to fetch coverage: ${res.status}`)
  return res.json()
}

// ── Coverage bar ──────────────────────────────────────────────────────────────

function CoverageBar({ actual, expected }: { actual: number | null; expected: number }) {
  const pct = actual === null ? null : Math.min(1, actual / Math.max(expected, 1))
  const barColor =
    pct === null ? 'bg-muted-foreground/30'
      : pct >= 0.95 ? 'bg-green-500'
      : pct >= 0.5  ? 'bg-yellow-500'
      : 'bg-red-500'
  return (
    <div className="flex items-center gap-2">
      <div className="h-2 w-28 rounded-full bg-border/40 overflow-hidden">
        <div
          className={`h-full rounded-full transition-all ${barColor}`}
          style={{ width: pct === null ? '8px' : `${Math.max(4, pct * 100)}%` }}
        />
      </div>
      <span className="text-xs text-muted-foreground tabular-nums">
        {actual === null ? '?' : actual.toLocaleString()} / {expected.toLocaleString()}
        {pct !== null && ` (${(pct * 100).toFixed(0)}%)`}
      </span>
    </div>
  )
}

// ── Status badge ──────────────────────────────────────────────────────────────

function StatusBadge({ status }: { status: CoverageRow['status'] }) {
  const cls =
    status === 'active'  ? 'bg-green-500/10 text-green-400'
    : status === 'sparse'  ? 'bg-yellow-500/10 text-yellow-400'
    : status === 'missing' ? 'bg-red-500/10 text-red-400'
    : 'bg-muted text-muted-foreground'
  return (
    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${cls}`}>
      {status}
    </span>
  )
}

// ── Component ─────────────────────────────────────────────────────────────────

export function DataCoverage() {
  const queryClient = useQueryClient()
  const [filter, setFilter] = useState<'all' | 'pending' | 'active'>('all')

  const coverageQuery = useQuery({
    queryKey: ['admin', 'mcp', 'data-coverage'],
    queryFn: fetchCoverage,
    staleTime: 120_000,
  })

  const grouped = useMemo(() => {
    const rows = coverageQuery.data?.coverage ?? []
    const filtered = filter === 'all' ? rows
      : rows.filter(r => r.status === filter || (filter === 'pending' && (r.status === 'missing' || r.status === 'sparse')))
    const byTool: Record<string, CoverageRow[]> = {}
    for (const row of filtered) {
      ;(byTool[row.tool] ??= []).push(row)
    }
    return byTool
  }, [coverageQuery.data, filter])

  if (coverageQuery.isError) {
    return <p className="text-sm text-red-400">Failed to load data coverage.</p>
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-medium">Data Coverage</h2>
        <div className="flex items-center gap-3">
          <select
            value={filter}
            onChange={e => setFilter(e.target.value as typeof filter)}
            className="text-xs rounded border border-border/50 bg-background px-2 py-1"
          >
            <option value="all">All assets</option>
            <option value="active">Active only</option>
            <option value="pending">Pending/sparse</option>
          </select>
          <button
            onClick={() => queryClient.invalidateQueries({ queryKey: ['admin', 'mcp', 'data-coverage'] })}
            className="text-xs text-muted-foreground hover:text-foreground underline"
          >
            Refresh
          </button>
        </div>
      </div>

      {coverageQuery.data?.note && (
        <p className="text-xs text-muted-foreground italic">{coverageQuery.data.note}</p>
      )}

      {coverageQuery.data?.caveats && coverageQuery.data.caveats.length > 0 && (
        <div className="rounded-lg border border-yellow-500/30 bg-yellow-500/5 p-3 space-y-1">
          {coverageQuery.data.caveats.map((c, i) => (
            <p key={i} className="text-xs text-yellow-300">
              <span className="font-mono text-yellow-400">[{c.tool}]</span> {c.caveat}
            </p>
          ))}
        </div>
      )}

      {coverageQuery.isLoading ? (
        <p className="text-sm text-muted-foreground animate-pulse">Loading coverage data…</p>
      ) : (
        <div className="space-y-6">
          {Object.entries(grouped).map(([toolName, rows]) => (
            <div key={toolName} className="rounded-lg border border-border/50 overflow-hidden">
              <div className="border-b border-border/50 bg-muted/20 px-4 py-2">
                <h3 className="font-mono text-sm text-brand-gold-cream">{toolName}</h3>
              </div>
              <table className="w-full text-sm">
                <thead className="border-b border-border/30 bg-muted/10">
                  <tr>
                    <th className="px-4 py-2 text-left font-medium text-muted-foreground">Category</th>
                    <th className="px-4 py-2 text-left font-medium text-muted-foreground">Coverage</th>
                    <th className="px-4 py-2 text-left font-medium text-muted-foreground">Status</th>
                    <th className="px-4 py-2 text-left font-medium text-muted-foreground">Backfill phase</th>
                    <th className="px-4 py-2 text-left font-medium text-muted-foreground">Caveat class</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/20">
                  {rows.map(row => (
                    <tr key={`${row.tool}-${row.category}`} className="hover:bg-muted/10">
                      <td className="px-4 py-2.5 font-mono text-xs">{row.category}</td>
                      <td className="px-4 py-2.5">
                        <CoverageBar actual={row.actual_rows} expected={row.expected_rows} />
                      </td>
                      <td className="px-4 py-2.5">
                        <StatusBadge status={row.status} />
                      </td>
                      <td className="px-4 py-2.5 text-xs text-muted-foreground">{row.backfill_phase}</td>
                      <td className="px-4 py-2.5 text-xs">
                        {row.caveat_class ? (
                          <span className={row.caveat_class === 'data_depth_gap'
                            ? 'text-blue-400'
                            : 'text-orange-400'
                          }>
                            {row.caveat_class}
                          </span>
                        ) : '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ))}
          {Object.keys(grouped).length === 0 && (
            <p className="text-sm text-muted-foreground">No matching coverage rows.</p>
          )}
        </div>
      )}
    </div>
  )
}
