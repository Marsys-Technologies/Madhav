'use client'

/**
 * PrimaryStrip — the 6-row primary anga display.
 *
 * Rows: Tithi, Nakshatra, Yoga, Karana, Vara, Paksha+Masa
 * Each row: Sanskrit name + label + ends_at time (local TZ, HH:MM) where applicable.
 *
 * Phase: 4C-4-S1 (Item 5)
 */

import type { PanchangAngas } from '../hooks/usePanchangDay'

interface PrimaryStripProps {
  angas: PanchangAngas
  /** Local timezone offset in minutes (default 330 = IST +5:30) */
  tzOffsetMinutes?: number
  /** ISO date string for the displayed day */
  date: string
}

interface AngaRow {
  label: string
  sanskritLabel: string
  value: string | null
  endsAt: string | null
}

/** Convert UTC ISO string to local HH:MM given offset in minutes */
function utcToLocalTime(utcIso: string | null | undefined, tzOffsetMinutes: number): string | null {
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

/** Number → ordinal suffix for Tithi display */
function ordinal(n: number | null | undefined): string {
  if (n == null) return ''
  const s = ['th', 'st', 'nd', 'rd']
  const v = n % 100
  return n + (s[(v - 20) % 10] ?? s[v] ?? s[0])
}

export function PrimaryStrip({ angas, tzOffsetMinutes = 330, date }: PrimaryStripProps) {
  const rows: AngaRow[] = [
    {
      label: 'Tithi',
      sanskritLabel: 'तिथि',
      value: angas.tithi
        ? `${angas.tithi.name}${angas.tithi.number != null ? ` (${ordinal(angas.tithi.number)})` : ''}`
        : null,
      endsAt: angas.tithi?.ends_at_local
        ? utcToLocalTime(angas.tithi.ends_at_local, tzOffsetMinutes)
        : null,
    },
    {
      label: 'Nakshatra',
      sanskritLabel: 'नक्षत्र',
      value: angas.nakshatra?.name ?? null,
      endsAt: angas.nakshatra?.ends_at_local
        ? utcToLocalTime(angas.nakshatra.ends_at_local, tzOffsetMinutes)
        : null,
    },
    {
      label: 'Yoga',
      sanskritLabel: 'योग',
      value: angas.yoga?.name ?? null,
      endsAt: angas.yoga?.ends_at_local
        ? utcToLocalTime(angas.yoga.ends_at_local, tzOffsetMinutes)
        : null,
    },
    {
      label: 'Karana',
      sanskritLabel: 'करण',
      value: angas.karana_first?.name ?? null,
      endsAt: angas.karana_first?.ends_at_local
        ? utcToLocalTime(angas.karana_first.ends_at_local, tzOffsetMinutes)
        : null,
    },
    {
      label: 'Vara',
      sanskritLabel: 'वार',
      value: angas.vara?.name ?? null,
      endsAt: null, // Vara spans the full day; no end time shown
    },
    {
      label: 'Paksha',
      sanskritLabel: 'पक्ष',
      value: angas.paksha ?? null,
      endsAt: null,
    },
  ]

  return (
    <section
      aria-label="Five Angas — Primary Panchang Strip"
      className="mx-auto max-w-4xl px-4 py-6"
    >
      <div className="rounded-xl border border-[rgba(212,175,55,0.14)] bg-[rgba(28,28,26,0.50)] overflow-hidden shadow-[0_0_40px_rgba(212,175,55,0.04)]">
        {rows.map((row, i) => (
          <PrimaryStripRow key={row.label} row={row} isLast={i === rows.length - 1} />
        ))}
      </div>

      {/* Secondary Karana — shown if present */}
      {angas.karana_second && (
        <div className="mt-2 rounded-lg border border-[rgba(212,175,55,0.10)] bg-[rgba(28,28,26,0.35)] px-5 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-xs font-medium text-[rgba(212,175,55,0.40)] uppercase tracking-widest w-20">
              Karana 2
            </span>
            <span className="font-serif text-sm" style={{ color: 'var(--brand-gold-cream)' }}>
              {angas.karana_second.name}
            </span>
          </div>
          {angas.karana_second.ends_at_local && (
            <EndsBadge time={utcToLocalTime(angas.karana_second.ends_at_local, tzOffsetMinutes)} />
          )}
        </div>
      )}

      <p className="mt-3 text-right text-xs opacity-30 pr-1" aria-hidden="true">
        {date} · IST
      </p>
    </section>
  )
}

function PrimaryStripRow({ row, isLast }: { row: AngaRow; isLast: boolean }) {
  const isEmpty = !row.value

  return (
    <div
      className={`flex items-center justify-between px-5 py-4 ${!isLast ? 'border-b border-[rgba(212,175,55,0.08)]' : ''}`}
      role="row"
      aria-label={`${row.label}: ${row.value ?? 'unavailable'}`}
    >
      <div className="flex items-center gap-3 min-w-0">
        {/* Sanskrit label */}
        <span
          className="shrink-0 font-serif text-xs w-14 text-right"
          style={{ color: 'rgba(212,175,55,0.35)' }}
          aria-hidden="true"
        >
          {row.sanskritLabel}
        </span>

        {/* English label */}
        <span
          className="shrink-0 text-xs font-medium uppercase tracking-widest w-20"
          style={{ color: 'rgba(212,175,55,0.45)' }}
        >
          {row.label}
        </span>

        {/* Value */}
        {isEmpty ? (
          <span className="text-sm italic opacity-30">—</span>
        ) : (
          <span
            className="font-serif text-base font-medium truncate"
            style={{ color: 'var(--brand-gold-cream, #fce29a)' }}
          >
            {row.value}
          </span>
        )}
      </div>

      {/* Ends-at badge */}
      {row.endsAt && <EndsBadge time={row.endsAt} />}
    </div>
  )
}

function EndsBadge({ time }: { time: string | null }) {
  if (!time) return null
  return (
    <span
      className="ml-4 shrink-0 rounded-md border border-[rgba(212,175,55,0.18)] bg-[rgba(212,175,55,0.06)] px-2.5 py-1 text-xs font-mono tabular-nums"
      style={{ color: 'rgba(212,175,55,0.65)' }}
      aria-label={`Ends at ${time}`}
    >
      ends {time}
    </span>
  )
}
