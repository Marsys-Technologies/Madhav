'use client'

import * as React from 'react'
import { LineChart, Line, ResponsiveContainer, Tooltip } from 'recharts'

export interface KpiSparklinePoint {
  t: string
  v: number | null
}

interface KpiTileProps {
  bundle: 'pipeline_correctness' | 'answer_quality' | 'performance_health' | 'retrieval_health'
  title: string
  description: string
  headline: { label: string; value: string }
  secondary: Array<{ label: string; value: string }>
  delta?: number | null // -1..+1 relative change; null for insufficient data
  sparkline: KpiSparklinePoint[]
  extra?: React.ReactNode
}

function deltaArrow(d: number | null | undefined) {
  if (d == null) return { sym: '—', color: 'text-muted-foreground', label: 'no comparison' }
  if (d > 0.01) return { sym: '↑', color: 'text-[var(--status-success)]', label: `${(d * 100).toFixed(1)}% better` }
  if (d < -0.01) return { sym: '↓', color: 'text-[var(--status-halt)]', label: `${Math.abs(d * 100).toFixed(1)}% worse` }
  return { sym: '—', color: 'text-muted-foreground', label: 'unchanged' }
}

export function KpiTile(props: KpiTileProps) {
  const { title, description, headline, secondary, delta, sparkline, extra } = props
  const arrow = deltaArrow(delta)
  const safeSparkline = sparkline.length > 0 ? sparkline : []

  return (
    <div className="rounded-lg border bg-card p-4">
      <div className="flex items-start justify-between gap-2">
        <h3 className="bt-label bt-label-upper" title={description} style={{ color: 'rgba(212,175,55,0.55)' }}>{title}</h3>
        <span className={`text-xs shrink-0 ${arrow.color}`} aria-label={arrow.label}>{arrow.sym}</span>
      </div>
      <div className="mt-3 bt-num" style={{ color: 'var(--brand-gold-cream)' }}>{headline.value}</div>
      <div className="bt-label mt-0.5">{headline.label}</div>
      <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1">
        {secondary.map((s) => (
          <span key={s.label} className="text-xs">
            <span className="font-semibold" style={{ color: 'var(--brand-gold-cream)' }}>{s.value}</span>
            <span className="ml-1 text-muted-foreground">{s.label}</span>
          </span>
        ))}
      </div>
      <div className="mt-3 h-12">
        {safeSparkline.length > 0 ? (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={safeSparkline}>
              <Line
                type="monotone"
                dataKey="v"
                stroke="rgba(212,175,55,0.60)"
                strokeWidth={1.5}
                dot={false}
                isAnimationActive={false}
                connectNulls
              />
              <Tooltip
                contentStyle={{
                  fontSize: '11px',
                  padding: '4px 8px',
                  background: 'oklch(0.13 0.012 70)',
                  border: '1px solid rgba(212,175,55,0.25)',
                  borderRadius: '4px',
                  color: 'oklch(0.92 0.075 88)',
                }}
                formatter={(value: unknown) => [
                  typeof value === 'number' ? value.toFixed(3) : '—',
                  'value',
                ]}
                labelFormatter={(l) => new Date(l as string).toLocaleString()}
              />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <div className="flex h-full items-center justify-center text-xs text-muted-foreground">
            no data in window
          </div>
        )}
      </div>
      {extra && <div className="mt-3">{extra}</div>}
    </div>
  )
}
