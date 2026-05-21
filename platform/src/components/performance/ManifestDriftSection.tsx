'use client'

import * as React from 'react'

// ── Types ─────────────────────────────────────────────────────────────────────

export interface DriftCategory {
  status: string
  missing?: string[]
  unbound?: string[]
}

export interface DriftReport {
  verdict: string
  categories: Record<string, DriftCategory>
  run_at: string
}

export interface ManifestDriftSectionProps {
  driftReport: DriftReport | null
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function VerdictBadge({ verdict }: { verdict: string }) {
  const isPass = verdict === 'PASS'
  return (
    <span
      className="rounded px-2 py-0.5 text-[12px] font-semibold"
      style={{
        background: isPass
          ? 'rgba(var(--status-success-rgb,34,197,94),0.12)'
          : 'rgba(var(--status-error-rgb,220,38,38),0.12)',
        color: isPass
          ? 'var(--status-success,#22c55e)'
          : 'var(--status-error,#ef4444)',
      }}
      data-testid="verdict-badge"
    >
      {verdict}
    </span>
  )
}

// ── Category detail ───────────────────────────────────────────────────────────

function CategoryDetail({
  name,
  category,
}: {
  name: string
  category: DriftCategory
}) {
  const isOk = category.status === 'PASS' || category.status === 'OK'
  const missing = category.missing ?? []
  const unbound = category.unbound ?? []

  return (
    <div
      className="rounded border p-3"
      style={{
        borderColor: isOk
          ? 'rgba(var(--status-success-rgb,34,197,94),0.15)'
          : 'rgba(var(--status-error-rgb,220,38,38),0.15)',
        background: isOk
          ? 'rgba(var(--status-success-rgb,34,197,94),0.04)'
          : 'rgba(var(--status-error-rgb,220,38,38),0.04)',
      }}
      data-testid={`drift-category-${name}`}
    >
      <div className="flex items-center gap-2">
        <span className="font-mono text-[12px] font-medium text-foreground">{name}</span>
        <span
          className="text-[11px]"
          style={{
            color: isOk
              ? 'var(--status-success,#22c55e)'
              : 'var(--status-error,#ef4444)',
          }}
        >
          {category.status}
        </span>
      </div>

      {missing.length > 0 && (
        <div className="mt-2">
          <p className="text-[11px] text-muted-foreground mb-1">Missing:</p>
          <ul className="space-y-0.5">
            {missing.map(item => (
              <li key={item} className="font-mono text-[11px] text-muted-foreground">
                — {item}
              </li>
            ))}
          </ul>
        </div>
      )}

      {unbound.length > 0 && (
        <div className="mt-2">
          <p className="text-[11px] text-muted-foreground mb-1">Unbound:</p>
          <ul className="space-y-0.5">
            {unbound.map(item => (
              <li key={item} className="font-mono text-[11px] text-muted-foreground">
                — {item}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

// ── Main component ────────────────────────────────────────────────────────────

export function ManifestDriftSection({ driftReport }: ManifestDriftSectionProps) {
  return (
    <section className="space-y-4" data-testid="manifest-drift-section">
      <div className="flex items-baseline justify-between">
        <h2 className="bt-label bt-label-upper" style={{ color: 'var(--brand-gold)' }}>
          Manifest Fingerprint Drift
        </h2>
        {driftReport && (
          <span className="text-xs text-muted-foreground">
            Run at {driftReport.run_at}
          </span>
        )}
      </div>

      {driftReport === null ? (
        <p
          className="rounded border p-3 text-sm text-muted-foreground"
          style={{ borderColor: 'rgba(var(--brand-gold-rgb),0.12)' }}
          data-testid="no-drift-report"
        >
          No drift report available — run{' '}
          <code className="font-mono text-[12px]">coverage_gate.py</code> to generate.
        </p>
      ) : (
        <div className="space-y-3">
          {/* Verdict banner */}
          <div
            className="flex items-center gap-3 rounded border p-3"
            style={{ borderColor: 'rgba(var(--brand-gold-rgb),0.12)' }}
          >
            <VerdictBadge verdict={driftReport.verdict} />
            <span className="text-[12px] text-muted-foreground">
              Overall verdict — {driftReport.verdict === 'PASS' ? 'no drift detected' : 'drift or missing coverage detected'}
            </span>
          </div>

          {/* Category details */}
          <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
            {Object.entries(driftReport.categories).map(([name, cat]) => (
              <CategoryDetail key={name} name={name} category={cat} />
            ))}
          </div>
        </div>
      )}
    </section>
  )
}
