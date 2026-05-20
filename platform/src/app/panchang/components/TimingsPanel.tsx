'use client'

/**
 * TimingsPanel — Sunrise/Sunset/Moonrise/Moonset + Inauspicious + Auspicious windows.
 *
 * Layout per §4.2 mockup:
 *   - Sun/Moon timings block (4 rows)
 *   - Divider
 *   - Inauspicious windows (Rahu Kalam, Yamagandam, Gulika Kalam, Dur Muhurta) — warning color
 *   - Divider
 *   - Auspicious windows (Abhijit, Brahma Muhurta, Amrit Kalam, Varjyam) — success color
 *
 * All times displayed in local TZ using tzOffsetMinutes.
 * Missing moon transitions show "—".
 *
 * Phase: 4C-4-S2 (Item 1)
 */

import type { PanchangTimings } from '../hooks/usePanchangDay'

interface TimingEntry {
  label: string
  start_utc: string | null
  end_utc: string | null
}

interface TimingsPanelProps {
  timings: PanchangTimings
  /** Local timezone offset in minutes (default 330 = IST +5:30) */
  tzOffsetMinutes?: number
}

// ── Label display names ───────────────────────────────────────────────────────

const INAUSPICIOUS_LABEL_MAP: Record<string, string> = {
  rahu_kalam: 'Rahu Kalam',
  yamagandam: 'Yamagandam',
  gulika_kalam: 'Gulika Kalam',
  dur_muhurta: 'Dur Muhurta',
}

const AUSPICIOUS_LABEL_MAP: Record<string, string> = {
  abhijit: 'Abhijit Muhurta',
  brahma_muhurta: 'Brahma Muhurta',
  amrit_kalam: 'Amrit Kalam',
  varjyam: 'Varjyam',
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

function formatWindow(
  start_utc: string | null,
  end_utc: string | null,
  tzOffsetMinutes: number,
): string {
  const start = utcToLocalHHMM(start_utc, tzOffsetMinutes)
  const end = utcToLocalHHMM(end_utc, tzOffsetMinutes)
  if (start && end) return `${start} – ${end}`
  if (start) return `from ${start}`
  if (end) return `until ${end}`
  return '—'
}

// ── Sub-components ────────────────────────────────────────────────────────────

function SectionHeading({ children }: { children: React.ReactNode }) {
  return (
    <div className="px-5 py-2 border-b border-[rgba(212,175,55,0.08)]">
      <span
        className="text-[10px] font-semibold uppercase tracking-[0.15em]"
        style={{ color: 'rgba(212,175,55,0.35)' }}
      >
        {children}
      </span>
    </div>
  )
}

function TimingRow({
  label,
  value,
  isLast,
  variant,
}: {
  label: string
  value: string
  isLast: boolean
  variant: 'neutral' | 'warning' | 'success'
}) {
  const valueColor =
    variant === 'warning'
      ? 'rgba(220,80,60,0.90)'
      : variant === 'success'
        ? 'rgba(80,200,130,0.90)'
        : 'var(--brand-gold-cream, #fce29a)'

  return (
    <div
      className={`flex items-center justify-between px-5 py-3 ${!isLast ? 'border-b border-[rgba(212,175,55,0.06)]' : ''}`}
      role="row"
      aria-label={`${label}: ${value}`}
    >
      <span
        className="text-sm font-medium"
        style={{ color: 'rgba(212,175,55,0.65)' }}
      >
        {label}
      </span>
      <span
        className="font-mono text-sm tabular-nums"
        style={{ color: valueColor }}
      >
        {value}
      </span>
    </div>
  )
}

// ── Main component ────────────────────────────────────────────────────────────

export function TimingsPanel({ timings, tzOffsetMinutes = 330 }: TimingsPanelProps) {
  const sunrise = utcToLocalHHMM(timings.sunrise_utc, tzOffsetMinutes) ?? '—'
  const sunset = utcToLocalHHMM(timings.sunset_utc, tzOffsetMinutes) ?? '—'
  const moonrise = utcToLocalHHMM(timings.moonrise_utc, tzOffsetMinutes) ?? '—'
  const moonset = utcToLocalHHMM(timings.moonset_utc, tzOffsetMinutes) ?? '—'

  // Parse inauspicious list: [{label, start_utc, end_utc}]
  const inauspiciousList: TimingEntry[] = Array.isArray(timings.inauspicious)
    ? (timings.inauspicious as TimingEntry[])
    : []

  // Parse auspicious list
  const auspiciousList: TimingEntry[] = Array.isArray(timings.auspicious)
    ? (timings.auspicious as TimingEntry[])
    : []

  const sunMoonRows = [
    { label: 'Sunrise', value: sunrise },
    { label: 'Sunset', value: sunset },
    { label: 'Moonrise', value: moonrise },
    { label: 'Moonset', value: moonset },
  ]

  return (
    <section
      aria-label="Timings — Sun, Moon, Inauspicious and Auspicious Windows"
      className="rounded-xl border border-[rgba(212,175,55,0.14)] bg-[rgba(28,28,26,0.50)] overflow-hidden shadow-[0_0_40px_rgba(212,175,55,0.04)]"
    >
      {/* Sun / Moon block */}
      <SectionHeading>Sun &amp; Moon</SectionHeading>
      {sunMoonRows.map((row, i) => (
        <TimingRow
          key={row.label}
          label={row.label}
          value={row.value}
          isLast={i === sunMoonRows.length - 1}
          variant="neutral"
        />
      ))}

      {/* Inauspicious block */}
      <SectionHeading>Inauspicious</SectionHeading>
      {inauspiciousList.length === 0 ? (
        <div className="px-5 py-3">
          <span className="text-sm italic opacity-30">None computed</span>
        </div>
      ) : (
        inauspiciousList.map((entry, i) => (
          <TimingRow
            key={entry.label}
            label={INAUSPICIOUS_LABEL_MAP[entry.label] ?? entry.label}
            value={formatWindow(entry.start_utc, entry.end_utc, tzOffsetMinutes)}
            isLast={i === inauspiciousList.length - 1}
            variant="warning"
          />
        ))
      )}

      {/* Auspicious block */}
      <SectionHeading>Auspicious</SectionHeading>
      {auspiciousList.length === 0 ? (
        <div className="px-5 py-3">
          <span className="text-sm italic opacity-30">None computed</span>
        </div>
      ) : (
        auspiciousList.map((entry, i) => (
          <TimingRow
            key={entry.label}
            label={AUSPICIOUS_LABEL_MAP[entry.label] ?? entry.label}
            value={formatWindow(entry.start_utc, entry.end_utc, tzOffsetMinutes)}
            isLast={i === auspiciousList.length - 1}
            variant="success"
          />
        ))
      )}
    </section>
  )
}
