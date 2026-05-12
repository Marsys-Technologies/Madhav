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
  if (d > 0.01) return { sym: '↑', color: 'text-emerald-500', label: `${(d * 100).toFixed(1)}% better` }
  if (d < -0.01) return { sym: '↓', color: 'text-rose-500', label: `${Math.abs(d * 100).toFixed(1)}% worse` }
  return { sym: '—', color: 'text-muted-foreground', label: 'unchanged' }
}

export function KpiTile(props: KpiTileProps) {
  const { title, description, headline, secondary, delta, sparkline, extra } = props
  const arrow = deltaArrow(delta)
  const safeSparkline = sparkline.length > 0 ? sparkline : []

  return (
    <div className="rounded-lg border bg-card p-4 shadow-sm">
      <div className="flex items-baseline justify-between">
        <h3 className="text-sm font-semibold text-foreground" title={description}>{title}</h3>
        <span className={`text-xs ${arrow.color}`} aria-label={arrow.label}>{arrow.sym}</span>
      </div>
      <div className="mt-2 text-3xl font-semibold tracking-tight">{headline.value}</div>
      <div className="text-xs text-muted-foreground">{headline.label}</div>
      <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted-foreground">
        {secondary.map((s) => (
          <span key={s.label}>
            <span className="font-medium text-foreground">{s.value}</span> {s.label}
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
                stroke="currentColor"
                strokeWidth={1.5}
                dot={false}
                isAnimationActive={false}
                connectNulls
              />
              <Tooltip
                contentStyle={{ fontSize: '11px', padding: '4px 8px' }}
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
