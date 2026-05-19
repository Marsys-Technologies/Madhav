'use client'

/**
 * PrimaryStrip — the 6-row primary anga display.
 *
 * Rows: Tithi, Nakshatra, Yoga, Karana, Vara, Paksha+Masa
 * Each row: Sanskrit name + label + ends_at time (local TZ, HH:MM) where applicable.
 *
 * When native_context is provided, the Nakshatra row shows a Tara Bala badge.
 *
 * Phase: 4C-4-S1 (Item 5); 4C-5 (Tara Bala badge — Item 7);
 *        4C-8 (AskMadhavLink on Tithi + Tara Bala badge rows — Item 5)
 */

import type { PanchangAngas, NativeContext } from '../hooks/usePanchangDay'
import { computeTaraBala, type TaraBalaClass } from '@/lib/panchang/tara_bala'
import { AskMadhavLink } from './AskMadhavLink'

interface PrimaryStripProps {
  angas: PanchangAngas
  /** Local timezone offset in minutes (default 330 = IST +5:30) */
  tzOffsetMinutes?: number
  /** ISO date string for the displayed day */
  date: string
  /** Native overlay — when present, show Tara Bala badge on Nakshatra row */
  nativeContext?: NativeContext | null
  /**
   * Full Panchang day JSON injected as context into Ask-Madhav deep links.
   * Passed by PanchangClientView from the usePanchangDay result.
   * 4C-8 (Item 5)
   */
  panchangContext?: object | null
}

interface AngaRow {
  label: string
  sanskritLabel: string
  value: string | null
  endsAt: string | null
  /** nakshatra_id from sidecar — used for Tara Bala computation */
  nakshatraId?: number | null
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

export function PrimaryStrip({ angas, tzOffsetMinutes = 330, date, nativeContext, panchangContext }: PrimaryStripProps) {
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
      nakshatraId: angas.nakshatra?.number ?? null,
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

  // Build the Ask-Madhav prompt for the Tithi row (4C-8 Item 5)
  const tithiName = angas.tithi?.name ?? null
  const tithiPrompt = tithiName
    ? `What does ${tithiName} mean for me today?`
    : null

  // Tara Bala prompt — used when nativeContext is present (personalised view)
  const nakshatraName = angas.nakshatra?.name ?? null
  const taraBalaPrompt =
    nativeContext && nakshatraName
      ? `Is today's ${nakshatraName} Nakshatra a Tara day for me? What does that mean for planning?`
      : null

  return (
    <section
      aria-label="Five Angas — Primary Panchang Strip"
      className="mx-auto max-w-4xl px-4 py-6"
    >
      <div className="rounded-xl border border-[rgba(212,175,55,0.14)] bg-[rgba(28,28,26,0.50)] overflow-hidden shadow-[0_0_40px_rgba(212,175,55,0.04)]">
        {rows.map((row, i) => (
          <PrimaryStripRow
            key={row.label}
            row={row}
            isLast={i === rows.length - 1}
            nativeContext={nativeContext}
            // Inject AskMadhavLink on Tithi row
            askMadhavPrompt={
              row.label === 'Tithi' && tithiPrompt
                ? tithiPrompt
                : row.label === 'Nakshatra' && taraBalaPrompt
                  ? taraBalaPrompt
                  : null
            }
            panchangContext={panchangContext ?? undefined}
          />
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

// ── Tara Bala badge ───────────────────────────────────────────────────────────

const TARA_COLORS: Record<TaraBalaClass, { bg: string; text: string; border: string }> = {
  auspicious:   { bg: 'rgba(80,200,130,0.12)',  text: 'rgba(80,200,130,0.95)',  border: 'rgba(80,200,130,0.30)'  },
  inauspicious: { bg: 'rgba(220,80,60,0.12)',   text: 'rgba(220,80,60,0.95)',   border: 'rgba(220,80,60,0.30)'   },
  mixed:        { bg: 'rgba(212,175,55,0.10)',  text: 'rgba(212,175,55,0.85)',  border: 'rgba(212,175,55,0.28)'  },
}

function TaraBadge({
  nativeContext,
  currentNakshatraId,
}: {
  nativeContext: NativeContext
  currentNakshatraId: number
}) {
  let result
  try {
    result = computeTaraBala(nativeContext.birth_nakshatra_id, currentNakshatraId)
  } catch {
    return null
  }
  const colors = TARA_COLORS[result.classification]
  return (
    <span
      className="ml-2 shrink-0 rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide"
      style={{ background: colors.bg, color: colors.text, borderColor: colors.border }}
      title={`Tara Bala: ${result.tara} (count ${result.count})`}
      aria-label={`Tara Bala: ${result.tara}`}
    >
      {result.tara}
    </span>
  )
}

function PrimaryStripRow({
  row,
  isLast,
  nativeContext,
  askMadhavPrompt,
  panchangContext,
}: {
  row: AngaRow
  isLast: boolean
  nativeContext?: NativeContext | null
  /** When set, renders an AskMadhavLink icon at the end of the row. */
  askMadhavPrompt?: string | null
  panchangContext?: object
}) {
  const isEmpty = !row.value
  const showTaraBadge =
    row.label === 'Nakshatra' &&
    nativeContext != null &&
    row.nakshatraId != null &&
    row.nakshatraId >= 1 &&
    row.nakshatraId <= 27

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

        {/* Tara Bala badge — only on Nakshatra row when native personalised */}
        {showTaraBadge && (
          <TaraBadge
            nativeContext={nativeContext!}
            currentNakshatraId={row.nakshatraId!}
          />
        )}
      </div>

      {/* Right-side cluster: ends-at + Ask-Madhav link */}
      <div className="flex items-center gap-2 shrink-0 ml-2">
        {row.endsAt && <EndsBadge time={row.endsAt} />}
        {askMadhavPrompt && (
          <AskMadhavLink
            prompt={askMadhavPrompt}
            panchang_context={panchangContext}
          />
        )}
      </div>
    </div>
  )
}

function EndsBadge({ time }: { time: string | null }) {
  if (!time) return null
  return (
    <span
      className="shrink-0 rounded-md border border-[rgba(212,175,55,0.18)] bg-[rgba(212,175,55,0.06)] px-2.5 py-1 text-xs font-mono tabular-nums"
      style={{ color: 'rgba(212,175,55,0.65)' }}
      aria-label={`Ends at ${time}`}
    >
      ends {time}
    </span>
  )
}
