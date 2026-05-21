'use client'

import * as React from 'react'
import type { FreshnessReport, StaleAsset } from '@/lib/performance/freshness'

function CountBadge({
  count,
  label,
  variant,
}: {
  count: number
  label: string
  variant: 'red' | 'amber' | 'green'
}) {
  const colors: Record<typeof variant, { border: string; bg: string; text: string }> = {
    red: {
      border: 'rgba(239,68,68,0.35)',
      bg: 'rgba(239,68,68,0.08)',
      text: 'rgb(252,165,165)',
    },
    amber: {
      border: 'rgba(245,158,11,0.35)',
      bg: 'rgba(245,158,11,0.08)',
      text: 'rgb(252,211,77)',
    },
    green: {
      border: 'rgba(34,197,94,0.35)',
      bg: 'rgba(34,197,94,0.08)',
      text: 'rgb(134,239,172)',
    },
  }
  const c = colors[variant]
  return (
    <div
      className="flex flex-col items-center gap-1 rounded border px-6 py-3 text-center"
      style={{ borderColor: c.border, background: c.bg }}
    >
      <span className="text-3xl font-bold tabular-nums" style={{ color: c.text }}>
        {count}
      </span>
      <span className="text-xs text-muted-foreground">{label}</span>
    </div>
  )
}

function StaleTable({ assets }: { assets: StaleAsset[] }) {
  if (assets.length === 0) return null
  return (
    <div className="overflow-x-auto rounded border" style={{ borderColor: 'rgba(212,175,55,0.14)' }}>
      <table className="w-full text-xs">
        <thead>
          <tr
            className="border-b text-left text-muted-foreground"
            style={{ borderColor: 'rgba(212,175,55,0.12)', background: 'rgba(212,175,55,0.04)' }}
          >
            <th className="px-3 py-2 font-medium">Canonical ID</th>
            <th className="px-3 py-2 font-medium">Status</th>
            <th className="px-3 py-2 font-medium">Path</th>
          </tr>
        </thead>
        <tbody className="divide-y" style={{ borderColor: 'rgba(212,175,55,0.08)' }}>
          {assets.map((a, idx) => (
            <tr
              key={`${a.canonical_id}-${idx}`}
              className="hover:bg-[rgba(212,175,55,0.03)] transition-colors"
            >
              <td
                className="px-3 py-2 font-mono font-medium"
                style={{ color: 'var(--brand-gold-cream)' }}
              >
                {a.canonical_id}
              </td>
              <td className="px-3 py-2">
                <span
                  className="rounded px-1.5 py-0.5 text-xs"
                  style={{
                    background: 'rgba(239,68,68,0.12)',
                    color: 'rgb(252,165,165)',
                    border: '1px solid rgba(239,68,68,0.25)',
                  }}
                >
                  {a.status}
                </span>
              </td>
              <td className="px-3 py-2 font-mono text-muted-foreground">{a.path}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export function FreshnessDiagnosticsSection() {
  const [report, setReport] = React.useState<FreshnessReport | null>(null)
  const [loading, setLoading] = React.useState(true)
  const [error, setError] = React.useState<string | null>(null)

  React.useEffect(() => {
    setLoading(true)
    fetch('/api/performance/freshness')
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        return r.json() as Promise<FreshnessReport>
      })
      .then((data) => {
        setReport(data)
        setLoading(false)
      })
      .catch((e: unknown) => {
        setError(e instanceof Error ? e.message : 'unknown error')
        setLoading(false)
      })
  }, [])

  if (loading) {
    return (
      <div className="space-y-2 animate-pulse">
        {[1, 2].map((i) => (
          <div key={i} className="h-10 rounded bg-muted/20" />
        ))}
      </div>
    )
  }

  if (error || !report) {
    return (
      <div className="rounded border border-red-500/30 p-4 text-sm text-red-400">
        Failed to load freshness report{error ? `: ${error}` : ''}
      </div>
    )
  }

  const { stale_assets, aging_assets, total_scanned } = report
  const allHealthy = stale_assets.length === 0 && aging_assets.length === 0

  return (
    <div className="space-y-4">
      {/* Scanned count */}
      <p className="text-xs text-muted-foreground">
        Scanned <strong>{total_scanned}</strong> manifest entries
      </p>

      {/* Count badges */}
      <div className="flex flex-wrap gap-4">
        <CountBadge
          count={stale_assets.length}
          label="Stale Assets (SUPERSEDED / DEAD_DATA)"
          variant={stale_assets.length > 0 ? 'red' : 'green'}
        />
        <CountBadge
          count={aging_assets.length}
          label="Aging Assets (last_updated > 90 days)"
          variant={aging_assets.length > 0 ? 'amber' : 'green'}
        />
      </div>

      {/* All healthy banner */}
      {allHealthy && (
        <div
          className="rounded border px-4 py-3 text-sm font-medium"
          style={{
            borderColor: 'rgba(34,197,94,0.30)',
            background: 'rgba(34,197,94,0.06)',
            color: 'rgb(134,239,172)',
          }}
        >
          All assets healthy — no stale or aging entries detected.
        </div>
      )}

      {/* Stale assets table */}
      {stale_assets.length > 0 && (
        <div className="space-y-2">
          <h3 className="bt-label text-xs" style={{ color: 'var(--brand-gold)' }}>
            Stale Assets
          </h3>
          <StaleTable assets={stale_assets} />
        </div>
      )}

      {/* Aging assets summary */}
      {aging_assets.length > 0 && (
        <div className="space-y-2">
          <h3 className="bt-label text-xs" style={{ color: 'var(--brand-gold)' }}>
            Aging Assets
          </h3>
          <div className="overflow-x-auto rounded border" style={{ borderColor: 'rgba(212,175,55,0.14)' }}>
            <table className="w-full text-xs">
              <thead>
                <tr
                  className="border-b text-left text-muted-foreground"
                  style={{ borderColor: 'rgba(212,175,55,0.12)', background: 'rgba(212,175,55,0.04)' }}
                >
                  <th className="px-3 py-2 font-medium">Canonical ID</th>
                  <th className="px-3 py-2 font-medium">Last Updated</th>
                  <th className="px-3 py-2 font-medium">Days Since Update</th>
                  <th className="px-3 py-2 font-medium">Path</th>
                </tr>
              </thead>
              <tbody className="divide-y" style={{ borderColor: 'rgba(212,175,55,0.08)' }}>
                {aging_assets.map((a, idx) => (
                  <tr
                    key={`${a.canonical_id}-${idx}`}
                    className="hover:bg-[rgba(212,175,55,0.03)] transition-colors"
                  >
                    <td
                      className="px-3 py-2 font-mono font-medium"
                      style={{ color: 'var(--brand-gold-cream)' }}
                    >
                      {a.canonical_id}
                    </td>
                    <td className="px-3 py-2 text-muted-foreground">{a.last_updated}</td>
                    <td className="px-3 py-2">
                      <span
                        className="rounded px-1.5 py-0.5 text-xs"
                        style={{
                          background: 'rgba(245,158,11,0.12)',
                          color: 'rgb(252,211,77)',
                          border: '1px solid rgba(245,158,11,0.25)',
                        }}
                      >
                        {a.days_since_update}d
                      </span>
                    </td>
                    <td className="px-3 py-2 font-mono text-muted-foreground">{a.path}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
