'use client'

/**
 * HoraPanel — Collapsible Hora (planetary hours) panel.
 *
 * Data shape from sidecar serialize.py:
 *   hora: [{label: "hora_sun"|"hora_moon"|..., start_utc, end_utc}, ...] (24 entries)
 *
 * Horas run in Chaldean order: Saturn, Jupiter, Mars, Sun, Venus, Mercury, Moon
 * starting from the vara lord at sunrise. The sidecar engine computes the sequence;
 * this panel is pure presentation.
 *
 * Each hora row: planet name + Sanskrit + time window + planet color accent.
 *
 * Collapsed by default.
 *
 * Phase: 4C-4-S3 (Item 3)
 */

import { CollapsibleRoot, CollapsibleTrigger, CollapsibleContent } from '@/components/ui/collapsible'

// ── Data shape ────────────────────────────────────────────────────────────────

interface HoraSegment {
  label: string       // "hora_sun", "hora_moon", "hora_mars", etc.
  start_utc: string | null
  end_utc: string | null
}

// ── Planet display metadata ───────────────────────────────────────────────────

interface PlanetMeta {
  display: string
  sanskrit: string
  color: string       // accent color for the planet
}

const HORA_PLANET_META: Record<string, PlanetMeta> = {
  sun:     { display: 'Sun',     sanskrit: 'सूर्य',  color: 'rgba(255,180,50,0.85)' },
  moon:    { display: 'Moon',    sanskrit: 'चन्द्र', color: 'rgba(200,210,230,0.80)' },
  mars:    { display: 'Mars',    sanskrit: 'मंगल',  color: 'rgba(220,70,50,0.85)' },
  mercury: { display: 'Mercury', sanskrit: 'बुध',   color: 'rgba(80,200,130,0.80)' },
  jupiter: { display: 'Jupiter', sanskrit: 'गुरु',  color: 'rgba(255,200,80,0.85)' },
  venus:   { display: 'Venus',   sanskrit: 'शुक्र', color: 'rgba(220,150,200,0.80)' },
  saturn:  { display: 'Saturn',  sanskrit: 'शनि',   color: 'rgba(120,120,160,0.80)' },
}

function getPlanetMeta(label: string): PlanetMeta {
  // Labels: "hora_sun", "hora_moon", etc.
  const key = label.replace(/^hora_/, '').toLowerCase()
  return HORA_PLANET_META[key] ?? { display: label, sanskrit: '', color: 'rgba(212,175,55,0.75)' }
}

// ── Time utilities ────────────────────────────────────────────────────────────

function utcToLocalHHMM(utcIso: string | null | undefined, tzOffsetMinutes: number): string | null {
  if (!utcIso) return null
  try {
    const utcMs = new Date(utcIso).getTime()
    if (isNaN(utcMs)) return null
    const localMs = utcMs + tzOffsetMinutes * 60 * 1000
    const d = new Date(localMs)
    const hh = String(d.getUTCHours()).padStart(2, '0')
    const mm = String(d.getUTCMinutes()).padStart(2, '0')
    return `${hh}:${mm}`
  } catch {
    return null
  }
}

function formatWindow(start: string | null, end: string | null, tz: number): string {
  const s = utcToLocalHHMM(start, tz)
  const e = utcToLocalHHMM(end, tz)
  if (s && e) return `${s} – ${e}`
  if (s) return `from ${s}`
  if (e) return `until ${e}`
  return '—'
}

// ── Hora row ──────────────────────────────────────────────────────────────────

function HoraRow({
  segment,
  index,
  tzOffsetMinutes,
  isLast,
}: {
  segment: HoraSegment
  index: number
  tzOffsetMinutes: number
  isLast: boolean
}) {
  const meta = getPlanetMeta(segment.label)
  const window = formatWindow(segment.start_utc, segment.end_utc, tzOffsetMinutes)

  return (
    <div
      className={`flex items-center justify-between px-5 py-2.5 ${!isLast ? 'border-b border-[rgba(212,175,55,0.05)]' : ''}`}
      role="row"
      aria-label={`Hora ${index + 1}: ${meta.display}, ${window}`}
    >
      {/* Index + planet */}
      <div className="flex items-center gap-3">
        <span
          className="text-[10px] font-mono tabular-nums w-4 text-right shrink-0"
          style={{ color: 'rgba(212,175,55,0.30)' }}
          aria-hidden="true"
        >
          {index + 1}
        </span>
        <span
          className="text-sm font-medium"
          style={{ color: meta.color }}
        >
          {meta.display}
        </span>
        {meta.sanskrit && (
          <span
            className="font-serif text-[11px]"
            style={{ color: 'rgba(212,175,55,0.30)' }}
            aria-hidden="true"
          >
            {meta.sanskrit}
          </span>
        )}
      </div>

      {/* Time window */}
      <span
        className="font-mono text-xs tabular-nums shrink-0"
        style={{ color: 'rgba(212,175,55,0.55)' }}
      >
        {window}
      </span>
    </div>
  )
}

// ── Props ─────────────────────────────────────────────────────────────────────

interface HoraPanelProps {
  hora: unknown[] | null | undefined
  /** Local timezone offset in minutes (default 330 = IST +5:30) */
  tzOffsetMinutes?: number
}

// ── Main component ────────────────────────────────────────────────────────────

export function HoraPanel({
  hora,
  tzOffsetMinutes = 330,
}: HoraPanelProps) {
  const segments = (Array.isArray(hora) ? hora : []) as HoraSegment[]

  return (
    <CollapsibleRoot
      defaultOpen={false}
      className="rounded-xl border border-[rgba(212,175,55,0.14)] bg-[rgba(28,28,26,0.50)] overflow-hidden shadow-[0_0_40px_rgba(212,175,55,0.04)]"
    >
      <CollapsibleTrigger
        className="px-5 py-3 border-b border-[rgba(212,175,55,0.08)] hover:bg-[rgba(212,175,55,0.03)] transition-colors"
      >
        <div className="flex flex-col items-start">
          <span
            className="text-[10px] font-semibold uppercase tracking-[0.15em]"
            style={{ color: 'rgba(212,175,55,0.35)' }}
          >
            Hora
          </span>
          <span
            className="text-xs mt-0.5"
            style={{ color: 'rgba(212,175,55,0.50)' }}
          >
            {segments.length > 0
              ? `${segments.length} planetary hours (Chaldean order)`
              : '24 planetary hours'}
          </span>
        </div>
      </CollapsibleTrigger>

      <CollapsibleContent>
        {segments.length === 0 ? (
          <div className="px-5 py-4">
            <span
              className="text-sm italic"
              style={{ color: 'rgba(212,175,55,0.35)' }}
            >
              Hora data not available.
            </span>
          </div>
        ) : (
          segments.map((seg, i) => (
            <HoraRow
              key={`hora-${i}`}
              segment={seg}
              index={i}
              tzOffsetMinutes={tzOffsetMinutes}
              isLast={i === segments.length - 1}
            />
          ))
        )}
      </CollapsibleContent>
    </CollapsibleRoot>
  )
}
