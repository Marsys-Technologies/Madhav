'use client'

import * as React from 'react'

// ── Types ─────────────────────────────────────────────────────────────────────

export interface CoverageStats {
  totalAssets: number
  assetsWithTool: number
  toolsWithManifest: number
  plannerVisibleTools: number
}

export interface PlannerRoutingSectionProps {
  /** queryClass → array of tool-set arrays (each inner array is the tools used in one query) */
  routingData: Record<string, string[][]>
  coverageStats: CoverageStats
}

// ── Helpers ───────────────────────────────────────────────────────────────────

interface ComboFreq {
  combo: string
  count: number
}

function topCombos(toolSets: string[][], topN = 3): ComboFreq[] {
  const freq = new Map<string, number>()
  for (const tools of toolSets) {
    const key = [...tools].sort().join(', ') || '(no tools)'
    freq.set(key, (freq.get(key) ?? 0) + 1)
  }
  return Array.from(freq.entries())
    .map(([combo, count]) => ({ combo, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, topN)
}

// ── Sub-components ────────────────────────────────────────────────────────────

function ScoreCard({ label, value }: { label: string; value: number }) {
  return (
    <div
      className="rounded border p-3"
      style={{
        borderColor: 'rgba(var(--brand-gold-rgb),0.12)',
        background: 'rgba(var(--brand-gold-rgb),0.03)',
      }}
    >
      <div className="bt-display text-lg" style={{ color: 'var(--brand-gold-cream)' }}>
        {value.toLocaleString()}
      </div>
      <div className="bt-label mt-0.5 text-[11px] text-muted-foreground">{label}</div>
    </div>
  )
}

function ClassRoutingRow({ queryClass, toolSets }: { queryClass: string; toolSets: string[][] }) {
  const combos = topCombos(toolSets, 3)
  return (
    <div className="space-y-1">
      <div className="flex items-baseline gap-2">
        <span className="font-mono text-[12px] font-semibold text-foreground">{queryClass}</span>
        <span className="text-[11px] text-muted-foreground">({toolSets.length} queries)</span>
      </div>
      <table className="w-full text-[11px]">
        <thead>
          <tr className="text-left text-[10px] uppercase text-muted-foreground/50">
            <th className="pb-1 pr-4 font-normal">tool combination</th>
            <th className="pb-1 font-normal w-12 text-right">count</th>
          </tr>
        </thead>
        <tbody>
          {combos.map(({ combo, count }) => (
            <tr key={combo} className="border-b" style={{ borderColor: 'rgba(var(--brand-gold-rgb),0.06)' }}>
              <td className="py-1 pr-4 font-mono text-muted-foreground">{combo}</td>
              <td className="py-1 text-right tabular-nums text-foreground">{count}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

// ── Main component ────────────────────────────────────────────────────────────

export function PlannerRoutingSection({
  routingData,
  coverageStats,
}: PlannerRoutingSectionProps) {
  const queryClasses = Object.keys(routingData).filter(k => k !== 'mismatches')
  const mismatches: string[][] = (routingData['mismatches'] as string[][] | undefined) ?? []

  return (
    <section className="space-y-4" data-testid="planner-routing-section">
      <div className="flex items-baseline justify-between">
        <h2 className="bt-label bt-label-upper" style={{ color: 'var(--brand-gold)' }}>
          Planner Routing
        </h2>
        <span className="text-xs text-muted-foreground">{queryClasses.length} query classes</span>
      </div>

      {/* Coverage scoreboard */}
      <div className="grid grid-cols-4 gap-3" data-testid="coverage-scoreboard">
        <ScoreCard label="Total assets" value={coverageStats.totalAssets} />
        <ScoreCard label="Assets with tool" value={coverageStats.assetsWithTool} />
        <ScoreCard label="Tools with manifest" value={coverageStats.toolsWithManifest} />
        <ScoreCard label="Planner-visible tools" value={coverageStats.plannerVisibleTools} />
      </div>

      {/* Per-class routing summary */}
      {queryClasses.length === 0 ? (
        <p className="text-sm text-muted-foreground">No routing data available.</p>
      ) : (
        <div
          className="space-y-5 rounded border p-4"
          style={{ borderColor: 'rgba(var(--brand-gold-rgb),0.12)' }}
          data-testid="routing-summary"
        >
          {queryClasses.map(qc => (
            <ClassRoutingRow
              key={qc}
              queryClass={qc}
              toolSets={routingData[qc] ?? []}
            />
          ))}
        </div>
      )}

      {/* Mismatch panel */}
      {mismatches.length > 0 && (
        <div
          className="rounded border p-4"
          style={{ borderColor: 'rgba(220,50,50,0.35)', background: 'rgba(220,50,50,0.05)' }}
          data-testid="mismatch-panel"
        >
          <p className="bt-label mb-3 text-[12px]" style={{ color: '#e05555' }}>
            Routing mismatches ({mismatches.length})
          </p>
          <ul className="space-y-1">
            {mismatches.flat().map((toolName, i) => (
              <li key={`${toolName}-${i}`} className="font-mono text-[11px] text-foreground">
                {toolName}
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  )
}
