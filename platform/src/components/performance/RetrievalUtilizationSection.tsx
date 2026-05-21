'use client'

import * as React from 'react'

// ── Types ─────────────────────────────────────────────────────────────────────

export interface RetrievalUtilizationSectionProps {
  /** List of tool names from RETRIEVAL_TOOLS */
  tools: string[]
  /** tool name → array of 24 hourly call counts */
  callData: Record<string, number[]>
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function totalCalls(counts: number[]): number {
  return counts.reduce((a, b) => a + b, 0)
}

/** Returns an rgba string from white (0) to deep blue (1) for heatmap cells. */
function heatColor(value: number, max: number): string {
  if (max === 0 || value === 0) return 'transparent'
  const intensity = value / max
  // interpolate: light blue (intensity~0.1) → deep blue (intensity=1)
  const r = Math.round(30 + (1 - intensity) * 180)
  const g = Math.round(80 + (1 - intensity) * 140)
  const b = Math.round(180 + (1 - intensity) * 55)
  return `rgba(${r},${g},${b},${0.15 + intensity * 0.75})`
}

// ── Sub-components ────────────────────────────────────────────────────────────

function HeatCell({ count, max }: { count: number; max: number }) {
  return (
    <div
      title={`${count} calls`}
      style={{
        background: heatColor(count, max),
        border: '1px solid rgba(var(--brand-gold-rgb),0.06)',
        borderRadius: 2,
        minWidth: 18,
        height: 18,
      }}
    />
  )
}

// ── Main component ────────────────────────────────────────────────────────────

export function RetrievalUtilizationSection({
  tools,
  callData,
}: RetrievalUtilizationSectionProps) {
  // Ensure every tool has exactly 24 hourly buckets
  const normalizedData = React.useMemo<Record<string, number[]>>(() => {
    const out: Record<string, number[]> = {}
    for (const tool of tools) {
      const raw = callData[tool] ?? []
      out[tool] = Array.from({ length: 24 }, (_, i) => raw[i] ?? 0)
    }
    return out
  }, [tools, callData])

  const globalMax = React.useMemo(() => {
    let max = 0
    for (const counts of Object.values(normalizedData)) {
      for (const c of counts) if (c > max) max = c
    }
    return max
  }, [normalizedData])

  const zeroCallTools = React.useMemo(
    () => tools.filter(t => totalCalls(normalizedData[t] ?? []) === 0),
    [tools, normalizedData],
  )

  const hours = Array.from({ length: 24 }, (_, i) => i)

  return (
    <section className="space-y-4" data-testid="retrieval-utilization-section">
      <div className="flex items-baseline justify-between">
        <h2 className="bt-label bt-label-upper" style={{ color: 'var(--brand-gold)' }}>
          Retrieval Utilization (24 h)
        </h2>
        <span className="text-xs text-muted-foreground">{tools.length} tools</span>
      </div>

      {/* Heatmap grid */}
      <div
        className="overflow-x-auto rounded border"
        style={{ borderColor: 'rgba(var(--brand-gold-rgb),0.12)' }}
      >
        <div style={{ minWidth: 640 }}>
          {/* Hour header */}
          <div
            className="grid items-center"
            style={{ gridTemplateColumns: '180px repeat(24, 1fr)', gap: 2, padding: '6px 8px 2px' }}
          >
            <div className="text-[10px] text-muted-foreground/50">tool</div>
            {hours.map(h => (
              <div key={h} className="text-center text-[9px] text-muted-foreground/50">
                {h}
              </div>
            ))}
          </div>

          {/* Tool rows */}
          {tools.map(tool => {
            const counts = normalizedData[tool] ?? []
            const total = totalCalls(counts)
            return (
              <div
                key={tool}
                className="grid items-center"
                style={{ gridTemplateColumns: '180px repeat(24, 1fr)', gap: 2, padding: '2px 8px' }}
              >
                <div className="flex items-center gap-1.5 overflow-hidden">
                  <span
                    className="truncate font-mono text-[11px] text-foreground"
                    title={tool}
                  >
                    {tool}
                  </span>
                  {total === 0 && (
                    <span
                      className="shrink-0 rounded px-1 text-[9px] font-medium"
                      style={{ background: 'rgba(150,150,150,0.15)', color: '#888' }}
                    >
                      0 calls
                    </span>
                  )}
                </div>
                {counts.map((count, h) => (
                  <HeatCell key={h} count={count} max={globalMax} />
                ))}
              </div>
            )
          })}
        </div>
      </div>

      {/* Zero-call callout */}
      {zeroCallTools.length > 0 && (
        <div
          className="rounded border p-3"
          style={{
            borderColor: 'rgba(150,150,150,0.25)',
            background: 'rgba(150,150,150,0.05)',
          }}
          data-testid="zero-call-callout"
        >
          <p className="bt-label mb-2 text-[11px] text-muted-foreground">
            Zero-call tools (7 d) — {zeroCallTools.length} tool{zeroCallTools.length !== 1 ? 's' : ''} never called
          </p>
          <ul className="flex flex-wrap gap-2">
            {zeroCallTools.map(t => (
              <li
                key={t}
                className="rounded px-2 py-0.5 font-mono text-[11px]"
                style={{ background: 'rgba(150,150,150,0.12)', color: '#aaa' }}
                data-testid={`zero-call-tool-${t}`}
              >
                {t}
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  )
}
