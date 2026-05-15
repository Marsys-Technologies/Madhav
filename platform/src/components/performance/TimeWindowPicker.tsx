'use client'

import * as React from 'react'

const PRESETS = [
  { id: '24h',   label: 'Last 24h',  ms: 24 * 60 * 60 * 1000 },
  { id: '7d',    label: 'Last 7 days', ms: 7 * 24 * 60 * 60 * 1000 },
  { id: '30d',   label: 'Last 30 days', ms: 30 * 24 * 60 * 60 * 1000 },
  { id: 'all',   label: 'All-time', ms: 0 },
] as const

export type WindowPreset = (typeof PRESETS)[number]['id'] | 'custom'

export interface TimeWindow {
  start: string // ISO 8601
  end: string   // ISO 8601
  preset: WindowPreset
}

export function resolveWindow(preset: WindowPreset, custom?: { start: string; end: string }): TimeWindow {
  const now = new Date()
  if (preset === 'custom' && custom) return { start: custom.start, end: custom.end, preset: 'custom' }
  if (preset === 'all') {
    return {
      start: new Date('2020-01-01T00:00:00.000Z').toISOString(),
      end: now.toISOString(),
      preset: 'all',
    }
  }
  const def = PRESETS.find((p) => p.id === preset) ?? PRESETS[1]
  return {
    start: new Date(now.getTime() - def.ms).toISOString(),
    end: now.toISOString(),
    preset: def.id,
  }
}

interface Props {
  value: WindowPreset
  customRange?: { start: string; end: string }
  onChange: (preset: WindowPreset, custom?: { start: string; end: string }) => void
}

export function TimeWindowPicker({ value, customRange, onChange }: Props) {
  const [customStart, setCustomStart] = React.useState(customRange?.start.slice(0, 10) ?? '')
  const [customEnd, setCustomEnd] = React.useState(customRange?.end.slice(0, 10) ?? '')

  const btnClass = (active: boolean) =>
    `rounded-full border px-3 py-1 text-xs font-medium transition-colors ${
      active
        ? 'border-[rgba(212,175,55,0.40)] bg-[rgba(212,175,55,0.12)] text-[var(--brand-gold)]'
        : 'border-transparent text-muted-foreground hover:bg-[rgba(212,175,55,0.06)] hover:text-[var(--brand-gold)]'
    }`

  return (
    <div className="flex flex-wrap items-center gap-1.5 py-1">
      <span className="bt-label mr-1">Window:</span>
      {PRESETS.map((p) => (
        <button key={p.id} onClick={() => onChange(p.id)} className={btnClass(value === p.id)}>
          {p.label}
        </button>
      ))}
      <button
        onClick={() => {
          if (customStart && customEnd) {
            onChange('custom', {
              start: new Date(customStart).toISOString(),
              end: new Date(customEnd + 'T23:59:59.999Z').toISOString(),
            })
          }
        }}
        className={btnClass(value === 'custom')}
      >
        Custom
      </button>
      {value === 'custom' && (
        <span className="flex items-center gap-1 text-xs">
          <input
            type="date"
            value={customStart}
            onChange={(e) => setCustomStart(e.target.value)}
            className="rounded border px-2 py-1 text-xs focus:outline-none focus:ring-1"
            style={{
              borderColor: 'rgba(212,175,55,0.25)',
              background: 'var(--input)',
              color: 'var(--brand-gold-cream)',
              outline: 'none',
            }}
          />
          <span className="text-muted-foreground">→</span>
          <input
            type="date"
            value={customEnd}
            onChange={(e) => setCustomEnd(e.target.value)}
            className="rounded border px-2 py-1 text-xs focus:outline-none"
            style={{
              borderColor: 'rgba(212,175,55,0.25)',
              background: 'var(--input)',
              color: 'var(--brand-gold-cream)',
            }}
          />
        </span>
      )}
    </div>
  )
}
