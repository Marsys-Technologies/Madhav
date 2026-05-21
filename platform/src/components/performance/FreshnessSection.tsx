'use client'

import * as React from 'react'

// ── Types ─────────────────────────────────────────────────────────────────────

export interface FreshnessAsset {
  name: string
  lastTouched: Date | null
  rebuildCadence: string
  isStale: boolean
}

export interface FreshnessSectionProps {
  assets: FreshnessAsset[]
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function formatDate(d: Date | null): string {
  if (d === null) return '—'
  return d.toISOString().slice(0, 10)
}

// ── Row ───────────────────────────────────────────────────────────────────────

function FreshnessRow({ asset }: { asset: FreshnessAsset }) {
  return (
    <tr
      className="border-b"
      style={{ borderColor: 'rgba(var(--brand-gold-rgb),0.08)' }}
    >
      <td className="py-2 pr-3 font-mono text-[12px] text-foreground">
        {asset.name}
      </td>
      <td className="py-2 pr-3 text-[12px] text-muted-foreground tabular-nums">
        {formatDate(asset.lastTouched)}
      </td>
      <td className="py-2 pr-3 text-[12px] text-muted-foreground">
        {asset.rebuildCadence}
      </td>
      <td className="py-2">
        {asset.isStale ? (
          <span
            className="rounded px-1.5 py-0.5 text-[11px] font-medium"
            style={{ background: 'rgba(var(--status-error-rgb,220,38,38),0.12)', color: 'var(--status-error,#ef4444)' }}
            data-testid="stale-badge"
          >
            Stale
          </span>
        ) : (
          <span
            className="rounded px-1.5 py-0.5 text-[11px] font-medium"
            style={{ background: 'rgba(var(--status-success-rgb,34,197,94),0.12)', color: 'var(--status-success,#22c55e)' }}
            data-testid="fresh-badge"
          >
            Fresh
          </span>
        )}
      </td>
    </tr>
  )
}

// ── Main component ────────────────────────────────────────────────────────────

export function FreshnessSection({ assets }: FreshnessSectionProps) {
  const staleCount = assets.filter(a => a.isStale).length

  return (
    <section className="space-y-4" data-testid="freshness-section">
      <div className="flex items-baseline justify-between">
        <h2 className="bt-label bt-label-upper" style={{ color: 'var(--brand-gold)' }}>
          Asset Freshness
        </h2>
        <span className="text-xs text-muted-foreground">
          {staleCount === 0
            ? 'All fresh'
            : `${staleCount} stale`}
        </span>
      </div>

      {assets.length === 0 ? (
        <p className="text-sm text-muted-foreground">No assets tracked.</p>
      ) : staleCount === 0 ? (
        <p
          className="rounded border p-3 text-sm"
          style={{
            borderColor: 'rgba(var(--status-success-rgb,34,197,94),0.2)',
            background: 'rgba(var(--status-success-rgb,34,197,94),0.04)',
            color: 'var(--status-success,#22c55e)',
          }}
          data-testid="no-stale-state"
        >
          No stale assets — all assets are within their rebuild cadence.
        </p>
      ) : null}

      {assets.length > 0 && (
        <div
          className="overflow-x-auto rounded border"
          style={{ borderColor: 'rgba(var(--brand-gold-rgb),0.12)' }}
        >
          <table className="w-full">
            <thead>
              <tr
                className="border-b text-left text-[11px] uppercase text-muted-foreground/60"
                style={{ borderColor: 'rgba(var(--brand-gold-rgb),0.10)' }}
              >
                <th className="pb-2 pl-3 pr-3 pt-2 font-normal">Asset</th>
                <th className="pb-2 pr-3 pt-2 font-normal">Last touched</th>
                <th className="pb-2 pr-3 pt-2 font-normal">Cadence</th>
                <th className="pb-2 pr-3 pt-2 font-normal">Status</th>
              </tr>
            </thead>
            <tbody className="pl-3">
              {assets.map(asset => (
                <FreshnessRow key={asset.name} asset={asset} />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}
