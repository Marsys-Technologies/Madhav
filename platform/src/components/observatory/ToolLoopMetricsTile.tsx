'use client'

/**
 * ToolLoopMetricsTile.tsx — E-S9 R11.E
 *
 * Observatory dashboard tile: agentic tool-loop iteration telemetry.
 *
 * Displays:
 *   - Iterations per turn × provider × per-day
 *   - Tool call count and error rate
 *   - Cost-per-turn breakdown by iteration
 *   - Cap-exceeded incidents (AgenticLoopCapExceeded events)
 *
 * Data is provided by the parent via the `summaries` prop (aggregated from
 * tool_loop_metrics.ts::aggregateTurnSummary). The tile is a pure display
 * component — no data fetching.
 *
 * Click-path: Observatory Overview → "Tool Loop Metrics" tile → provider row
 * expands to show per-iteration breakdown (E-S9).
 */

import type { ToolLoopTurnSummary } from '@/lib/observatory/tool_loop_metrics'

interface ToolLoopMetricsTileProps {
  summaries: ToolLoopTurnSummary[]
  /** ISO date range for the displayed window, e.g. "2026-05-22". */
  dateRange?: string
  className?: string
}

/** Format a number with comma separators. */
function fmt(n: number): string {
  return n.toLocaleString()
}

/** Format average iterations per turn to 1 decimal. */
function fmtAvg(total: number, count: number): string {
  if (count === 0) return '—'
  return (total / count).toFixed(1)
}

export function ToolLoopMetricsTile({
  summaries,
  dateRange,
  className,
}: ToolLoopMetricsTileProps) {
  if (!summaries.length) {
    return (
      <div
        className={`rounded-lg border border-gray-200 bg-white p-4 ${className ?? ''}`}
        role="region"
        aria-label="Tool loop metrics"
      >
        <h3 className="text-sm font-semibold text-gray-700">Tool Loop Metrics</h3>
        {dateRange && (
          <p className="mt-1 text-xs text-gray-400">{dateRange}</p>
        )}
        <p className="mt-4 text-xs text-gray-400">No tool-loop turns recorded.</p>
      </div>
    )
  }

  // Group by providerId
  const byProvider = summaries.reduce<Record<string, ToolLoopTurnSummary[]>>((acc, s) => {
    const pid = s.providerId
    if (!acc[pid]) acc[pid] = []
    acc[pid].push(s)
    return acc
  }, {})

  const providerOrder = ['anthropic', 'google', 'openai', 'deepseek', 'nvidia']
  const providers = providerOrder.filter(p => byProvider[p])

  return (
    <div
      className={`rounded-lg border border-gray-200 bg-white p-4 ${className ?? ''}`}
      role="region"
      aria-label="Tool loop metrics"
    >
      <h3 className="text-sm font-semibold text-gray-700">Tool Loop Metrics</h3>
      {dateRange && (
        <p className="mt-0.5 text-xs text-gray-400">{dateRange}</p>
      )}

      <table className="mt-3 w-full text-xs" aria-label="Tool loop metrics by provider">
        <thead>
          <tr className="border-b border-gray-100 text-left text-gray-500">
            <th className="pb-1 pr-4 font-medium">Provider</th>
            <th className="pb-1 pr-4 font-medium">Turns</th>
            <th className="pb-1 pr-4 font-medium">Avg iter/turn</th>
            <th className="pb-1 pr-4 font-medium">Tool calls</th>
            <th className="pb-1 pr-4 font-medium">Errors</th>
            <th className="pb-1 font-medium">Cap exceeded</th>
          </tr>
        </thead>
        <tbody>
          {providers.map(pid => {
            const rows = byProvider[pid]
            const turnCount = rows.length
            const totalIter = rows.reduce((s, r) => s + r.totalIterations, 0)
            const totalCalls = rows.reduce((s, r) => s + r.totalToolCalls, 0)
            const totalErrors = rows.reduce((s, r) => s + r.totalToolErrors, 0)
            const capCount = rows.filter(r => r.capExceeded).length

            return (
              <tr key={pid} className="border-b border-gray-50 last:border-0">
                <td className="py-1 pr-4 font-mono text-gray-700">{pid}</td>
                <td className="py-1 pr-4 text-gray-600">{fmt(turnCount)}</td>
                <td className="py-1 pr-4 text-gray-600">{fmtAvg(totalIter, turnCount)}</td>
                <td className="py-1 pr-4 text-gray-600">{fmt(totalCalls)}</td>
                <td className={`py-1 pr-4 ${totalErrors > 0 ? 'text-amber-600' : 'text-gray-600'}`}>
                  {fmt(totalErrors)}
                </td>
                <td className={`py-1 ${capCount > 0 ? 'text-red-600 font-semibold' : 'text-gray-400'}`}>
                  {capCount > 0 ? fmt(capCount) : '—'}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>

      {/* Cap exceeded warning banner */}
      {summaries.some(s => s.capExceeded) && (
        <div
          className="mt-3 rounded bg-red-50 px-3 py-2 text-xs text-red-700"
          role="alert"
        >
          Warning: {summaries.filter(s => s.capExceeded).length} turn(s) hit the 8-iteration cap
          (AgenticLoopCapExceeded). Review turn traces for runaway loop patterns.
        </div>
      )}
    </div>
  )
}
