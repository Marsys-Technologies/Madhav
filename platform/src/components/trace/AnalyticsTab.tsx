'use client'

/**
 * AnalyticsTab — BHISMA-B3 §5.7
 *
 * Sub-tab inside the History tab showing cross-query analytics over the
 * last N queries. Fetches /api/trace/history?mode=analytics&limit=30 on
 * mount, aggregates client-side, renders four panels:
 *   1. Query class distribution (donut)
 *   2. Latency trend (line — plan / tool_fetch / synthesis)
 *   3. Tool usage frequency (horizontal bars)
 *   4. Error rate + planning fallback rate (numeric KPIs)
 *
 * Charts are pure SVG / div-bar — no external charting lib. The donut + line
 * chart math is inlined for the same reason. Designed to render gracefully
 * when fields are absent (BHISMA-B2 may not yet emit query_class on all rows).
 */

import { useEffect, useState } from 'react'
import { PieChart, TrendingUp, BarChart3, AlertTriangle } from 'lucide-react'
import type { TraceHistoryRow } from '@/lib/trace/types'

interface Props {
  visible: boolean
}

const PALETTE = [
  'rgba(244,209,96,0.85)',     // gold
  'rgba(140,190,240,0.85)',    // blue
  'rgba(190,150,240,0.85)',    // violet
  'rgba(140,210,170,0.85)',    // green
  'rgba(240,170,100,0.85)',    // orange
  'rgba(240,150,120,0.85)',    // red-orange
  'rgba(130,210,230,0.85)',    // cyan
  'rgba(212,175,55,0.5)',      // dim gold (unknown)
]

function colorForIndex(i: number): string {
  return PALETTE[i % PALETTE.length]
}

function fmtMs(ms: number | null | undefined): string {
  if (ms == null) return '—'
  if (ms < 1000) return `${ms}ms`
  return `${(ms / 1000).toFixed(2)}s`
}

// ── Aggregations ─────────────────────────────────────────────────────────────

function aggregateClassDistribution(rows: TraceHistoryRow[]): Array<{ key: string; count: number }> {
  const m = new Map<string, number>()
  for (const r of rows) {
    const k = r.query_class ?? 'unknown'
    m.set(k, (m.get(k) ?? 0) + 1)
  }
  return Array.from(m.entries())
    .map(([key, count]) => ({ key, count }))
    .sort((a, b) => b.count - a.count)
}

function aggregateToolFrequency(rows: TraceHistoryRow[]): Array<{ tool: string; count: number }> {
  const m = new Map<string, number>()
  for (const r of rows) {
    for (const t of r.tools_used ?? []) {
      m.set(t, (m.get(t) ?? 0) + 1)
    }
  }
  return Array.from(m.entries())
    .map(([tool, count]) => ({ tool, count }))
    .sort((a, b) => b.count - a.count)
}

function aggregateErrorRate(rows: TraceHistoryRow[]): {
  total: number
  errors: number
  fallbacks: number
  avg_tool_count: number | null
} {
  const errors = rows.filter(r => r.has_error).length
  const fallbacks = rows.filter(r => r.planning_confidence === 0).length
  // I.2: average tool count per plan across queries that have tools_used data
  const withTools = rows.filter(r => r.tools_used && r.tools_used.length > 0)
  const avg_tool_count = withTools.length > 0
    ? Math.round((withTools.reduce((s, r) => s + (r.tools_used?.length ?? 0), 0) / withTools.length) * 10) / 10
    : null
  return { total: rows.length, errors, fallbacks, avg_tool_count }
}

// ── Donut chart (SVG) ────────────────────────────────────────────────────────

function DonutChart({ data }: { data: Array<{ key: string; count: number }> }) {
  const total = data.reduce((s, d) => s + d.count, 0)
  if (total === 0) {
    return <div className="text-[10px] text-[rgba(212,175,55,0.4)] italic">No queries with class data yet.</div>
  }

  const radius = 36
  const strokeWidth = 14
  const circ = 2 * Math.PI * radius

  const segments = data.map((d, i) => {
    const portion = d.count / total
    const dash = circ * portion
    const offset = data
      .slice(0, i)
      .reduce((sum, preceding) => sum + circ * (preceding.count / total), 0)
    const seg = (
      <circle
        key={d.key}
        r={radius}
        cx={50}
        cy={50}
        fill="transparent"
        stroke={colorForIndex(i)}
        strokeWidth={strokeWidth}
        strokeDasharray={`${dash} ${circ - dash}`}
        strokeDashoffset={-offset}
        transform="rotate(-90 50 50)"
      >
        <title>{`${d.key}: ${d.count} (${Math.round(portion * 100)}%)`}</title>
      </circle>
    )
    return seg
  })

  return (
    <div className="flex items-center gap-3">
      <svg width="100" height="100" viewBox="0 0 100 100" className="flex-shrink-0">
        {segments}
        <text
          x="50" y="48"
          textAnchor="middle"
          className="fill-[rgba(252,226,154,0.85)]"
          style={{ fontSize: '14px', fontWeight: 600 }}
        >
          {total}
        </text>
        <text
          x="50" y="60"
          textAnchor="middle"
          className="fill-[rgba(212,175,55,0.5)]"
          style={{ fontSize: '7px', letterSpacing: '0.1em' }}
        >
          QUERIES
        </text>
      </svg>

      <div className="flex-1 space-y-0.5 text-[10px]">
        {data.map((d, i) => {
          const portion = Math.round((d.count / total) * 100)
          return (
            <div key={d.key} className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-sm flex-shrink-0" style={{ background: colorForIndex(i) }} />
              <span className="text-[rgba(252,226,154,0.7)] flex-1 truncate">{d.key}</span>
              <span className="text-[rgba(212,175,55,0.55)] tabular-nums">{d.count} · {portion}%</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}

// ── Latency line chart (SVG) ─────────────────────────────────────────────────

function LatencyTrend({ rows }: { rows: TraceHistoryRow[] }) {
  // Sort by created_at ascending so x-axis flows left → right oldest → newest
  const sorted = rows.slice().sort((a, b) => a.created_at.localeCompare(b.created_at))
  const series: Array<{ label: string; color: string; values: Array<number | null> }> = [
    { label: 'plan',     color: 'rgba(244,209,96,0.85)',  values: sorted.map(r => r.plan_latency_ms ?? null) },
    { label: 'fetch',    color: 'rgba(120,210,160,0.85)', values: sorted.map(r => r.tool_fetch_latency_ms ?? null) },
    { label: 'synth',    color: 'rgba(190,150,240,0.85)', values: sorted.map(r => r.synthesis_latency_ms ?? null) },
  ]

  // Determine max for y-axis
  const allValues = series.flatMap(s => s.values).filter((v): v is number => v != null)
  if (allValues.length === 0) {
    return <div className="text-[10px] text-[rgba(212,175,55,0.4)] italic">No latency data yet.</div>
  }
  const maxY = Math.max(...allValues, 1)

  const W = 240, H = 60, PAD = 4
  const xStep = sorted.length > 1 ? (W - PAD * 2) / (sorted.length - 1) : 0

  function pointsFor(values: Array<number | null>): string {
    return values
      .map((v, i) => v == null ? null : `${PAD + i * xStep},${H - PAD - (v / maxY) * (H - PAD * 2)}`)
      .filter((p): p is string => p != null)
      .join(' ')
  }

  return (
    <div>
      <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} className="block">
        {/* Y-axis tick at top */}
        <text x={W - 2} y={9} textAnchor="end" className="fill-[rgba(212,175,55,0.4)]" style={{ fontSize: '8px' }}>
          {fmtMs(maxY)}
        </text>
        {series.map(s => (
          <polyline
            key={s.label}
            fill="none"
            stroke={s.color}
            strokeWidth={1.4}
            points={pointsFor(s.values)}
          />
        ))}
      </svg>
      <div className="flex items-center gap-3 text-[9px] mt-1">
        {series.map(s => (
          <span key={s.label} className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-sm" style={{ background: s.color }} />
            <span className="text-[rgba(252,226,154,0.7)]">{s.label}</span>
          </span>
        ))}
        <span className="ml-auto text-[rgba(212,175,55,0.4)] font-mono">{sorted.length} queries · oldest → newest</span>
      </div>
    </div>
  )
}

// ── Tool frequency bars ──────────────────────────────────────────────────────

function ToolFrequency({ data, totalQueries }: { data: Array<{ tool: string; count: number }>; totalQueries: number }) {
  if (data.length === 0) {
    return <div className="text-[10px] text-[rgba(212,175,55,0.4)] italic">No tool usage data yet.</div>
  }

  const maxCount = data[0].count

  return (
    <div className="space-y-1">
      {data.map(({ tool, count }) => {
        const widthPct = (count / maxCount) * 100
        const usagePct = Math.round((count / totalQueries) * 100)
        return (
          <div key={tool} className="flex items-center gap-2">
            <span className="text-[10px] font-mono text-[rgba(252,226,154,0.7)] w-32 truncate">{tool}</span>
            <div className="flex-1 h-1.5 bg-[rgba(212,175,55,0.06)] rounded-sm overflow-hidden">
              <div className="h-full bg-[rgba(212,175,55,0.5)] rounded-sm" style={{ width: `${widthPct}%` }} />
            </div>
            <span className="text-[10px] text-[rgba(212,175,55,0.55)] w-16 text-right tabular-nums">
              {count} · {usagePct}%
            </span>
          </div>
        )
      })}
    </div>
  )
}

// ── Error / fallback KPIs ────────────────────────────────────────────────────

function ErrorPanel({ rate }: { rate: { total: number; errors: number; fallbacks: number; avg_tool_count: number | null } }) {
  const errPct = rate.total > 0 ? Math.round((rate.errors / rate.total) * 100) : 0
  const fbkPct = rate.total > 0 ? Math.round((rate.fallbacks / rate.total) * 100) : 0
  return (
    <div className="grid grid-cols-4 gap-2">
      <div className="px-2 py-2 bg-[rgba(212,175,55,0.04)] border border-[rgba(212,175,55,0.10)]">
        <div className="text-[8px] uppercase tracking-[0.1em] text-[rgba(212,175,55,0.45)]">Queries</div>
        <div className="text-[18px] font-bold text-[rgba(252,226,154,0.85)] tabular-nums">{rate.total}</div>
      </div>
      {/* I.2: avg tool count per plan */}
      <div className="px-2 py-2 bg-[rgba(212,175,55,0.04)] border border-[rgba(212,175,55,0.10)]">
        <div className="text-[8px] uppercase tracking-[0.1em] text-[rgba(212,175,55,0.45)]">Avg tools/plan</div>
        <div className="text-[18px] font-bold text-[rgba(252,226,154,0.85)] tabular-nums">
          {rate.avg_tool_count != null ? rate.avg_tool_count : <span className="text-[rgba(212,175,55,0.4)] text-[12px]">—</span>}
        </div>
      </div>
      <div className={`px-2 py-2 border ${rate.fallbacks > 0 ? 'bg-[rgba(220,140,60,0.08)] border-[rgba(220,140,60,0.25)]' : 'bg-[rgba(212,175,55,0.04)] border-[rgba(212,175,55,0.10)]'}`}>
        <div className="text-[8px] uppercase tracking-[0.1em] text-[rgba(212,175,55,0.45)]">Fallbacks</div>
        <div className={`text-[18px] font-bold tabular-nums ${rate.fallbacks > 0 ? 'text-[rgba(240,170,100,0.95)]' : 'text-[rgba(252,226,154,0.85)]'}`}>
          {rate.fallbacks} <span className="text-[10px] font-normal opacity-70">· {fbkPct}%</span>
        </div>
      </div>
      <div className={`px-2 py-2 border ${rate.errors > 0 ? 'bg-[rgba(220,90,60,0.08)] border-[rgba(220,90,60,0.25)]' : 'bg-[rgba(212,175,55,0.04)] border-[rgba(212,175,55,0.10)]'}`}>
        <div className="text-[8px] uppercase tracking-[0.1em] text-[rgba(212,175,55,0.45)]">Errors</div>
        <div className={`text-[18px] font-bold tabular-nums ${rate.errors > 0 ? 'text-[rgba(240,150,120,0.95)]' : 'text-[rgba(252,226,154,0.85)]'}`}>
          {rate.errors} <span className="text-[10px] font-normal opacity-70">· {errPct}%</span>
        </div>
      </div>
    </div>
  )
}

// ── Section panel ────────────────────────────────────────────────────────────

function Panel({
  icon,
  title,
  children,
}: {
  icon: React.ReactNode
  title: string
  children: React.ReactNode
}) {
  return (
    <div className="border border-[rgba(212,175,55,0.10)] bg-[rgba(13,10,5,0.5)] p-3">
      <div className="flex items-center gap-1.5 mb-2 pb-1 border-b border-[rgba(212,175,55,0.08)]">
        {icon}
        <span className="text-[9px] font-bold uppercase tracking-[0.16em] text-[rgba(212,175,55,0.6)]">{title}</span>
      </div>
      {children}
    </div>
  )
}

// ── Main component ──────────────────────────────────────────────────────────

export function AnalyticsTab({ visible }: Props) {
  const [rows, setRows] = useState<TraceHistoryRow[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!visible || rows !== null || loading) return
    const initialFetch = setTimeout(() => {
      setLoading(true)
      fetch('/api/trace/history?mode=analytics&limit=30')
        .then(r => {
          if (!r.ok) throw new Error(`HTTP ${r.status}`)
          return r.json()
        })
        .then((data: TraceHistoryRow[]) => {
          setRows(Array.isArray(data) ? data : [])
          setLoading(false)
        })
        .catch(err => {
          console.error('[AnalyticsTab] fetch failed', err)
          setError(String(err))
          setLoading(false)
        })
    }, 0)
    return () => clearTimeout(initialFetch)
  }, [visible, rows, loading])

  if (!visible) return null

  if (loading || rows === null) {
    return <div className="px-4 py-3 text-[11px] text-[rgba(212,175,55,0.5)]">Loading analytics…</div>
  }

  if (error) {
    return (
      <div className="px-4 py-3 text-[11px] text-[rgba(240,150,120,0.85)]">
        Failed to load analytics: {error}
      </div>
    )
  }

  if (rows.length === 0) {
    return (
      <div className="px-4 py-3 text-[11px] text-[rgba(212,175,55,0.5)] italic">
        No trace history yet. Run a query first.
      </div>
    )
  }

  const classDist = aggregateClassDistribution(rows)
  const toolFreq = aggregateToolFrequency(rows)
  const errRate = aggregateErrorRate(rows)

  return (
    <div className="p-3 space-y-3 overflow-y-auto">
      <Panel
        icon={<AlertTriangle size={11} className="text-[rgba(212,175,55,0.55)]" />}
        title="Health"
      >
        <ErrorPanel rate={errRate} />
      </Panel>

      <Panel
        icon={<PieChart size={11} className="text-[rgba(212,175,55,0.55)]" />}
        title="Query class distribution"
      >
        <DonutChart data={classDist} />
      </Panel>

      <Panel
        icon={<TrendingUp size={11} className="text-[rgba(212,175,55,0.55)]" />}
        title="Latency trend"
      >
        <LatencyTrend rows={rows} />
      </Panel>

      <Panel
        icon={<BarChart3 size={11} className="text-[rgba(212,175,55,0.55)]" />}
        title="Tool usage frequency"
      >
        <ToolFrequency data={toolFreq} totalQueries={rows.length} />
      </Panel>
    </div>
  )
}
