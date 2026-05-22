/**
 * ToolHealth tab — sortable table of per-tool metrics fetched from
 * /api/mcp/health/tools. Includes inline CaveatEditor and ToolDisableToggle.
 *
 * Columns (sortable): tool_name | calls_24h | ok_rate | error_rate |
 *   zero_rows_rate | avg_latency_ms | audit_findings | enabled | caveats
 *
 * MCPT v3.1.0-S5
 */
'use client'

import { useState, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { AlertThresholds } from '../components/AlertThresholds'
import { CaveatEditor } from '../components/CaveatEditor'
import { ToolDisableToggle } from '../components/ToolDisableToggle'

// ── Types ─────────────────────────────────────────────────────────────────────

export interface ToolRow {
  tool_name: string
  call_count_24h: number | null
  error_rate: number | null
  avg_latency_ms: number | null
  audit_finding_count: number | null
  caveats: Array<{
    text?: string
    caveat_text?: string
    class?: string
    caveat_class?: string
    severity?: string
  }>
  data_note?: string
  enabled?: boolean
}

type SortKey = keyof ToolRow
type SortDir = 'asc' | 'desc'

// ── Fetch helpers ─────────────────────────────────────────────────────────────

async function fetchTools(): Promise<ToolRow[]> {
  const res = await fetch('/api/mcp/health/tools')
  if (!res.ok) throw new Error(`Failed to fetch tool health: ${res.status}`)
  const data = await res.json() as { tools?: ToolRow[] }
  return data.tools ?? []
}

async function fetchToolRegistry(): Promise<Record<string, boolean>> {
  const res = await fetch('/api/admin/mcp/tool-registry')
  if (!res.ok) return {}
  const data = await res.json() as { registry?: Record<string, boolean> }
  return data.registry ?? {}
}

// ── Sorting ───────────────────────────────────────────────────────────────────

function sortRows(rows: ToolRow[], key: SortKey, dir: SortDir): ToolRow[] {
  return [...rows].sort((a, b) => {
    const av = a[key] ?? -Infinity
    const bv = b[key] ?? -Infinity
    if (av < bv) return dir === 'asc' ? -1 : 1
    if (av > bv) return dir === 'asc' ? 1 : -1
    return 0
  })
}

// ── Component ─────────────────────────────────────────────────────────────────

export function ToolHealth() {
  const queryClient = useQueryClient()
  const [sortKey, setSortKey] = useState<SortKey>('tool_name')
  const [sortDir, setSortDir] = useState<SortDir>('asc')
  const [expandedTool, setExpandedTool] = useState<string | null>(null)
  const [showAlertConfig, setShowAlertConfig] = useState(false)

  const toolsQuery = useQuery({
    queryKey: ['admin', 'mcp', 'tool-health'],
    queryFn: fetchTools,
    staleTime: 60_000,
  })

  const registryQuery = useQuery({
    queryKey: ['admin', 'mcp', 'tool-registry'],
    queryFn: fetchToolRegistry,
    staleTime: 30_000,
  })

  const sorted = useMemo(() => {
    if (!toolsQuery.data) return []
    return sortRows(toolsQuery.data, sortKey, sortDir)
  }, [toolsQuery.data, sortKey, sortDir])

  function handleSort(key: SortKey) {
    if (sortKey === key) {
      setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    } else {
      setSortKey(key)
      setSortDir('asc')
    }
  }

  function SortIcon({ col }: { col: SortKey }) {
    if (sortKey !== col) return <span className="ml-1 opacity-30">↕</span>
    return <span className="ml-1">{sortDir === 'asc' ? '↑' : '↓'}</span>
  }

  function fmtRate(v: number | null): string {
    if (v === null) return '—'
    return `${(v * 100).toFixed(1)}%`
  }

  function fmtNum(v: number | null): string {
    if (v === null) return '—'
    return v.toFixed(0)
  }

  function rateClass(v: number | null, warnAt: number, badAt: number): string {
    if (v === null) return 'text-muted-foreground'
    if (v >= badAt) return 'text-red-400 font-semibold'
    if (v >= warnAt) return 'text-yellow-400'
    return 'text-green-400'
  }

  if (toolsQuery.isError) {
    return <p className="text-sm text-red-400">Failed to load tool health metrics.</p>
  }

  return (
    <div className="space-y-4">
      {/* Header row */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-medium">Tool Health (24h window)</h2>
        <div className="flex gap-2">
          <button
            onClick={() => queryClient.invalidateQueries({ queryKey: ['admin', 'mcp', 'tool-health'] })}
            className="text-xs text-muted-foreground hover:text-foreground underline"
          >
            Refresh
          </button>
          <button
            onClick={() => setShowAlertConfig(v => !v)}
            className="text-xs text-brand-gold-cream hover:underline"
          >
            {showAlertConfig ? 'Hide' : 'Configure alerts'}
          </button>
        </div>
      </div>

      {showAlertConfig && (
        <div className="rounded-lg border border-border/50 p-4">
          <AlertThresholds />
        </div>
      )}

      {toolsQuery.isLoading ? (
        <p className="text-sm text-muted-foreground animate-pulse">Loading metrics…</p>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-border/50">
          <table className="w-full text-sm">
            <thead className="border-b border-border/50 bg-muted/30">
              <tr>
                {([
                  ['tool_name', 'Tool'],
                  ['call_count_24h', 'Calls 24h'],
                  ['error_rate', 'Error rate'],
                  ['audit_finding_count', 'Audit findings'],
                ] as [SortKey, string][]).map(([key, label]) => (
                  <th
                    key={key}
                    className="px-4 py-2 text-left font-medium text-muted-foreground cursor-pointer select-none hover:text-foreground"
                    onClick={() => handleSort(key)}
                  >
                    {label}<SortIcon col={key} />
                  </th>
                ))}
                <th className="px-4 py-2 text-left font-medium text-muted-foreground">Latency p50</th>
                <th className="px-4 py-2 text-left font-medium text-muted-foreground">Enabled</th>
                <th className="px-4 py-2 text-left font-medium text-muted-foreground">Caveats</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/30">
              {sorted.map(tool => {
                const isEnabled = registryQuery.data?.[tool.tool_name] ?? true
                const hasCaveats = tool.caveats.length > 0
                return (
                  <>
                    <tr
                      key={tool.tool_name}
                      className="hover:bg-muted/20 cursor-pointer"
                      onClick={() => setExpandedTool(v => v === tool.tool_name ? null : tool.tool_name)}
                    >
                      <td className="px-4 py-3 font-mono text-xs text-brand-gold-cream">
                        {tool.tool_name}
                      </td>
                      <td className="px-4 py-3 text-muted-foreground">
                        {fmtNum(tool.call_count_24h)}
                      </td>
                      <td className={`px-4 py-3 ${rateClass(tool.error_rate, 0.05, 0.1)}`}>
                        {fmtRate(tool.error_rate)}
                      </td>
                      <td className={`px-4 py-3 ${(tool.audit_finding_count ?? 0) > 0 ? 'text-yellow-400' : 'text-muted-foreground'}`}>
                        {fmtNum(tool.audit_finding_count)}
                      </td>
                      <td className="px-4 py-3 text-muted-foreground">
                        {fmtNum(tool.avg_latency_ms)}ms
                      </td>
                      <td className="px-4 py-3" onClick={e => e.stopPropagation()}>
                        <ToolDisableToggle
                          toolName={tool.tool_name}
                          enabled={isEnabled}
                          onToggle={() => {
                            queryClient.invalidateQueries({ queryKey: ['admin', 'mcp', 'tool-registry'] })
                          }}
                        />
                      </td>
                      <td className="px-4 py-3">
                        {hasCaveats ? (
                          <span className="text-xs text-yellow-400">{tool.caveats.length} caveat(s)</span>
                        ) : (
                          <span className="text-xs text-muted-foreground">—</span>
                        )}
                      </td>
                    </tr>
                    {expandedTool === tool.tool_name && (
                      <tr key={`${tool.tool_name}-expanded`}>
                        <td colSpan={7} className="px-4 py-3 bg-muted/10">
                          <div className="space-y-3">
                            {tool.data_note && (
                              <p className="text-xs text-muted-foreground italic">{tool.data_note}</p>
                            )}
                            <CaveatEditor toolName={tool.tool_name} initialCaveats={tool.caveats} />
                          </div>
                        </td>
                      </tr>
                    )}
                  </>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
