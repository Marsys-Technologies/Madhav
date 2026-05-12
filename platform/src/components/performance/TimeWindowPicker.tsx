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

  return (
    <div className="flex flex-wrap items-center gap-2 py-2">
      <span className="text-sm text-muted-foreground">Window:</span>
      {PRESETS.map((p) => (
        <button
          key={p.id}
          onClick={() => onChange(p.id)}
          className={`rounded-full px-3 py-1 text-xs font-medium transition ${
            value === p.id
              ? 'bg-foreground text-background'
              : 'bg-muted text-foreground hover:bg-muted/70'
          }`}
        >
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
        className={`rounded-full px-3 py-1 text-xs font-medium transition ${
          value === 'custom' ? 'bg-foreground text-background' : 'bg-muted text-foreground hover:bg-muted/70'
        }`}
      >
        Custom
      </button>
      {value === 'custom' && (
        <span className="flex items-center gap-1 text-xs">
          <input
            type="date"
            value={customStart}
            onChange={(e) => setCustomStart(e.target.value)}
            className="rounded border bg-background px-2 py-1"
          />
          <span>→</span>
          <input
            type="date"
            value={customEnd}
            onChange={(e) => setCustomEnd(e.target.value)}
            className="rounded border bg-background px-2 py-1"
          />
        </span>
      )}
    </div>
  )
}
