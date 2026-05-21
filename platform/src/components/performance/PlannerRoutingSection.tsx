'use client'

import * as React from 'react'
import type { RetrievalStats } from '@/lib/performance/retrieval_aggregator'

export function PlannerRoutingSection() {
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
      <p className="text-xs" style={{ color: 'var(--brand-muted)' }}>Loading planner routing diagnostics…</p>
    )
  }

  if (error || !data) {
    return (
      <p className="text-xs" style={{ color: 'rgb(239,68,68)' }}>
        Failed to load routing stats: {error ?? 'unknown error'}
      </p>
    )
  }

  const { top_combinations, total_queries } = data
  const hasData = total_queries > 0 && top_combinations.length > 0

  return (
    <div className="space-y-3">
      <p className="text-xs" style={{ color: 'var(--brand-muted)' }}>
        Planner routing diagnostics — last 7 days · {total_queries} quer{total_queries === 1 ? 'y' : 'ies'} sampled
      </p>

      {!hasData ? (
        <div
          className="rounded border px-3 py-3 text-center text-xs"
          style={{ borderColor: 'rgba(212,175,55,0.15)', color: 'var(--brand-muted)' }}
        >
          No query data in window — run a chat query to populate
        </div>
      ) : (
        <div className="overflow-x-auto rounded border" style={{ borderColor: 'rgba(212,175,55,0.15)' }}>
          <table className="w-full text-xs">
            <thead>
              <tr style={{ borderBottom: '1px solid rgba(212,175,55,0.12)', background: 'rgba(212,175,55,0.05)' }}>
                <th className="px-3 py-2 text-left font-medium" style={{ color: 'var(--brand-gold)' }}>Tool set</th>
                <th className="px-3 py-2 text-right font-medium" style={{ color: 'var(--brand-gold)' }}>Count</th>
              </tr>
            </thead>
            <tbody>
              {top_combinations.map((combo, i) => (
                <tr
                  key={i}
                  style={{
                    borderBottom: i < top_combinations.length - 1 ? '1px solid rgba(212,175,55,0.07)' : undefined,
                  }}
                >
                  <td className="px-3 py-1.5 font-mono" style={{ color: 'var(--brand-gold-cream)', wordBreak: 'break-word' }}>
                    {combo.tools.join(', ')}
                  </td>
                  <td className="px-3 py-1.5 text-right tabular-nums font-semibold" style={{ color: 'var(--brand-gold-cream)' }}>
                    {combo.count}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
