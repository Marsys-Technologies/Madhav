'use client'

/**
 * PanchangCachePanel — Observatory panel for Panchang cache hit ratio.
 *
 * Phase 4C-9 Item 2: As specified in master plan §5.7, the cache layer is N/A
 * until Phase 4C-2 lands (pending Phase 4B MEAN_NODE rebuild).
 *
 * This panel renders the "Cache layer pending Phase 4B" placeholder as required
 * by the brief, and documents the conditions for it becoming active.
 */

import * as React from 'react'
import { ObsCard } from '../shared/ObsCard'

export function PanchangCachePanel(): React.ReactElement {
  return (
    <ObsCard tone="neutral" padding="normal" data-testid="panchang-cache-panel">
      {/* Header */}
      <div className="mb-4 flex items-start justify-between gap-3">
        <div>
          <p
            className="text-sm font-semibold"
            style={{ color: 'var(--brand-gold)' }}
          >
            Panchang Cache Hit Ratio
          </p>
          <p className="mt-0.5 text-xs text-muted-foreground">
            panchang_daily SQL cache — 24h hit / miss / bypass breakdown
          </p>
        </div>
        <span
          className="shrink-0 rounded-full border px-2 py-0.5 text-[10px] font-medium"
          style={{
            borderColor: 'rgba(212,175,55,0.20)',
            color: 'rgba(212,175,55,0.50)',
            background: 'rgba(212,175,55,0.04)',
          }}
        >
          pending
        </span>
      </div>

      {/* Pending state */}
      <div className="flex flex-col items-center justify-center py-6 text-center">
        {/* Gauge placeholder */}
        <div
          className="h-16 w-16 rounded-full border-4 flex items-center justify-center mb-3"
          style={{ borderColor: 'rgba(212,175,55,0.15)' }}
          aria-hidden="true"
        >
          <span className="text-lg" style={{ color: 'rgba(212,175,55,0.35)' }}>—</span>
        </div>

        <p
          className="text-sm font-medium mb-1"
          style={{ color: 'rgba(212,175,55,0.65)' }}
        >
          Cache layer pending Phase 4B
        </p>
        <p className="max-w-xs text-xs text-muted-foreground leading-relaxed">
          The SQL cache (panchang_daily table, Phase 4C-2) cannot be backfilled until
          Phase 4B rebuilds ephemeris_daily with corrected MEAN_NODE Rahu values.
          Currently serving all requests engine-direct.
        </p>
      </div>

      {/* Conditions list */}
      <div
        className="mt-3 rounded-lg border px-3 py-3 text-xs space-y-1.5"
        style={{
          borderColor: 'rgba(212,175,55,0.10)',
          background: 'rgba(212,175,55,0.03)',
        }}
      >
        <p className="font-medium mb-2" style={{ color: 'rgba(212,175,55,0.60)' }}>
          Conditions to activate this panel:
        </p>
        {[
          'Phase 4B closes (ephemeris_daily rebuilt with MEAN_NODE Rahu)',
          'Phase 4C-2 executes (migration 060; panchang_daily 292K-row backfill)',
          'Sidecar /api/compute/panchanga wired to SQL cache with engine fallback',
          'Observatory telemetry captures cache_hit boolean per request',
        ].map((condition, i) => (
          <div key={i} className="flex items-start gap-2">
            <span
              className="mt-0.5 shrink-0 text-[10px]"
              style={{ color: 'rgba(212,175,55,0.35)' }}
            >
              {i + 1}.
            </span>
            <span style={{ color: 'rgba(212,175,55,0.55)' }}>{condition}</span>
          </div>
        ))}
      </div>
    </ObsCard>
  )
}
