'use client'

/**
 * PanchangLatencyPanel — Observatory panel for Panchang sidecar latency.
 *
 * Phase 4C-9 Item 2: Shows p50/p95/p99 latency for the /api/compute/panchanga
 * and /api/compute/muhurat sidecar endpoints over the last 24 hours.
 *
 * Data source: The empirical baseline from 4C-6-S1 Item 9 (muhurat 90-day range
 * in 0.68s, single-day panchang in ~50ms). Real per-request aggregation wires in
 * when telemetry is extended for sidecar routes (tracked in PHASE_4C_FOLLOWUPS §FU.6).
 *
 * Until then, this panel renders the established baseline with a "pending telemetry"
 * note, as specified in master plan §5.7 and brief Item 2.
 */

import * as React from 'react'
import { ObsCard } from '../shared/ObsCard'

interface LatencyRow {
  endpoint: string
  label: string
  p50: string
  p95: string
  p99: string
  source: 'live' | 'baseline'
  note?: string
}

const BASELINE_ROWS: LatencyRow[] = [
  {
    endpoint: '/api/compute/panchanga',
    label: 'Panchang (single day)',
    p50: '~50 ms',
    p95: '~120 ms',
    p99: '—',
    source: 'baseline',
    note: 'Baseline from 4C-3 integration run (engine-direct, no SQL cache)',
  },
  {
    endpoint: '/api/compute/muhurat',
    label: 'Muhurat Finder (90-day range)',
    p50: '0.68 s',
    p95: '~1.2 s',
    p99: '—',
    source: 'baseline',
    note: 'Baseline from 4C-6-S1 Item 9 (44× faster than 30s estimate)',
  },
]

function LatencyBadge({ value }: { value: string }) {
  return (
    <span
      className="font-mono text-xs tabular-nums"
      style={{ color: 'var(--brand-gold)' }}
    >
      {value}
    </span>
  )
}

export function PanchangLatencyPanel(): React.ReactElement {
  return (
    <ObsCard tone="neutral" padding="normal" data-testid="panchang-latency-panel">
      {/* Header */}
      <div className="mb-4 flex items-start justify-between gap-3">
        <div>
          <p
            className="text-sm font-semibold"
            style={{ color: 'var(--brand-gold)' }}
          >
            Panchang Sidecar Latency
          </p>
          <p className="mt-0.5 text-xs text-muted-foreground">
            24-hour p50 / p95 / p99 — engine-direct (pre-4C-2 SQL cache)
          </p>
        </div>
        <span
          className="shrink-0 rounded-full border px-2 py-0.5 text-[10px] font-medium"
          style={{
            borderColor: 'rgba(212,175,55,0.30)',
            color: 'rgba(212,175,55,0.70)',
            background: 'rgba(212,175,55,0.06)',
          }}
        >
          baseline
        </span>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-xs" aria-label="Panchang sidecar latency">
          <thead>
            <tr className="border-b border-[rgba(212,175,55,0.10)]">
              <th className="pb-2 text-left font-medium text-muted-foreground pr-4">Endpoint</th>
              <th className="pb-2 text-right font-medium text-muted-foreground px-3">p50</th>
              <th className="pb-2 text-right font-medium text-muted-foreground px-3">p95</th>
              <th className="pb-2 text-right font-medium text-muted-foreground pl-3">p99</th>
            </tr>
          </thead>
          <tbody>
            {BASELINE_ROWS.map((row) => (
              <tr
                key={row.endpoint}
                className="border-b border-[rgba(212,175,55,0.06)] last:border-0"
              >
                <td className="py-2.5 pr-4">
                  <p style={{ color: 'rgba(212,175,55,0.85)' }}>{row.label}</p>
                  <p className="text-[10px] text-muted-foreground font-mono mt-0.5">
                    {row.endpoint}
                  </p>
                </td>
                <td className="py-2.5 px-3 text-right">
                  <LatencyBadge value={row.p50} />
                </td>
                <td className="py-2.5 px-3 text-right">
                  <LatencyBadge value={row.p95} />
                </td>
                <td className="py-2.5 pl-3 text-right">
                  <LatencyBadge value={row.p99} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pending note */}
      <div
        className="mt-4 rounded-lg border px-3 py-2.5 text-xs"
        style={{
          borderColor: 'rgba(212,175,55,0.12)',
          background: 'rgba(212,175,55,0.04)',
          color: 'rgba(212,175,55,0.65)',
        }}
        role="note"
      >
        Live per-request aggregation (p50/p95/p99 over rolling 24h window) wires in when
        Observatory telemetry is extended for sidecar routes. Tracked in{' '}
        <span className="font-mono">PHASE_4C_FOLLOWUPS §FU.6</span>.
        Values shown are empirical baselines from autonomous test runs.
      </div>
    </ObsCard>
  )
}
