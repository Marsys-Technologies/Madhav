'use client'

/**
 * MuhuratResultsList — renders the ranked Muhurat Finder results.
 *
 * Each row shows:
 *   - Date (formatted: "Thursday, June 12, 2026")
 *   - Star rating (from MuhuratWindow.star_rating)
 *   - Time window (UTC → local, formatted as IST range)
 *   - Breakdown badges (key → score contribution from breakdown dict)
 *   - Inline actions: "Export to Calendar" (enabled in 4C-7) + "Ask Madhav"
 *
 * Sorted by score descending (backend already sorts; we sort defensively).
 * Loading skeleton shown during fetch. Empty state if no windows.
 *
 * Phase: 4C-6-S3 (Item 3 + Item 4); 4C-7 (Item 9 — Export to Calendar wired);
 *        4C-8 (Panchang context injection in Ask-Madhav deep links — Item 5)
 */

import { useRouter } from 'next/navigation'
import { CalendarDays, MessageCircle } from 'lucide-react'
import { StarRating } from '@/components/ui/star-rating'
import type { MuhuratWindow } from '../hooks/useMuhuratFinder'
import { buildMuhuratWindowIcs, downloadIcs } from '@/lib/panchang/ics_client'
import { serialiseContext } from './AskMadhavLink'

// ── Types ─────────────────────────────────────────────────────────────────────

interface MuhuratResultsListProps {
  windows: MuhuratWindow[] | null
  isLoading: boolean
  error: string | null
  /** The selected event key — used in Ask-Madhav prompt generation */
  event: string
  /** Panchang data for the displayed day to enrich Ask-Madhav prompt */
  tzOffsetMinutes?: number
  /**
   * Full Panchang day JSON injected as context into Ask-Madhav deep links.
   * 4C-8 (Item 5)
   */
  panchangContext?: object | null
}

// ── Helpers ───────────────────────────────────────────────────────────────────

/** Human-readable label for a breakdown key from the engine */
function labelForBreakdownKey(key: string): string {
  const labels: Record<string, string> = {
    tithi: 'Tithi',
    nakshatra: 'Nakshatra',
    vara: 'Vara',
    yoga: 'Special Yoga',
    planet: 'Planet strength',
    avoid: 'Inauspicious penalty',
    tara_bala: 'Tara Bala',
    chandra_bala: 'Chandra Bala',
  }
  return labels[key] ?? key
}

/** Format an ISO UTC datetime as a local time string (HH:MM AM/PM) */
function formatWindowTime(utcIso: string | null, tzOffsetMinutes: number): string {
  if (!utcIso) return '—'
  try {
    const utcMs = new Date(utcIso).getTime()
    const localMs = utcMs + tzOffsetMinutes * 60 * 1000
    const d = new Date(localMs)
    const hh = d.getUTCHours()
    const mm = d.getUTCMinutes().toString().padStart(2, '0')
    const ampm = hh >= 12 ? 'PM' : 'AM'
    const h12 = hh % 12 || 12
    return `${h12}:${mm} ${ampm}`
  } catch {
    return '—'
  }
}

/** Format an ISO UTC datetime as a long date string, e.g. "Thursday, June 12, 2026" */
function formatWindowDate(utcIso: string | null, tzOffsetMinutes: number): string {
  if (!utcIso) return 'Unknown date'
  try {
    const utcMs = new Date(utcIso).getTime()
    const localMs = utcMs + tzOffsetMinutes * 60 * 1000
    const d = new Date(localMs)
    return new Intl.DateTimeFormat('en-IN', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      timeZone: 'UTC', // already shifted to local
    }).format(d)
  } catch {
    return utcIso.split('T')[0]
  }
}

/** Score contribution label: "+0.95" or "−0.30" */
function formatScore(score: number): string {
  if (score >= 0) return `+${score.toFixed(2)}`
  return score.toFixed(2)
}

/** Breakdown badge color: green-tinted for positive, red-tinted for avoid/negative */
function badgeStyle(key: string, score: number): React.CSSProperties {
  if (key === 'avoid' || score < 0) {
    return {
      color: 'rgba(220,80,60,0.90)',
      background: 'rgba(220,80,60,0.08)',
      border: '1px solid rgba(220,80,60,0.18)',
    }
  }
  return {
    color: 'rgba(212,175,55,0.85)',
    background: 'rgba(212,175,55,0.08)',
    border: '1px solid rgba(212,175,55,0.18)',
  }
}

// Native client ID for Ask-Madhav deep link (mirrors ActionBar.tsx)
const NATIVE_CLIENT_ID = 'abhisek_mohanty_primary'

// ── Sub-components ────────────────────────────────────────────────────────────

/** Loading skeleton for a single result row */
function SkeletonRow() {
  return (
    <div className="rounded-xl border border-[rgba(212,175,55,0.10)] bg-[rgba(28,28,26,0.55)] p-4">
      <div className="flex items-center justify-between mb-2">
        <div className="h-4 w-48 rounded bg-[rgba(212,175,55,0.10)] animate-pulse" />
        <div className="h-4 w-20 rounded bg-[rgba(212,175,55,0.08)] animate-pulse" />
      </div>
      <div className="h-3 w-32 rounded bg-[rgba(212,175,55,0.08)] animate-pulse mb-3" />
      <div className="flex gap-2">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-5 w-24 rounded-full bg-[rgba(212,175,55,0.07)] animate-pulse" />
        ))}
      </div>
    </div>
  )
}

/** A single Muhurat result row */
function MuhuratRow({
  window: w,
  rank,
  event,
  tzOffsetMinutes,
  panchangContext,
}: {
  window: MuhuratWindow
  rank: number
  event: string
  tzOffsetMinutes: number
  panchangContext?: object | null
}) {
  const router = useRouter()

  const dateLabel = formatWindowDate(w.start_utc, tzOffsetMinutes)
  const startTime = formatWindowTime(w.start_utc, tzOffsetMinutes)
  const endTime = formatWindowTime(w.end_utc, tzOffsetMinutes)

  // Build the Ask-Madhav prompt — deep link into chat with pre-loaded Panchang context (4C-8)
  function handleAskMadhav() {
    // Identify top breakdown factors for the prompt
    const topFactors = Object.entries(w.breakdown)
      .filter(([, v]) => v > 0)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 3)
      .map(([k, v]) => `${labelForBreakdownKey(k)} (${formatScore(v)})`)
      .join(', ')

    const visiblePrompt =
      `Walk me through why ${dateLabel} is ranked #${rank} for ${event.replace(/_/g, ' ')}. ` +
      `The Panchang engine gave it ${w.star_rating} stars (score ${w.score.toFixed(2)}). ` +
      (topFactors ? `Top factors: ${topFactors}. ` : '') +
      `What does this mean for planning this event?`

    const params = new URLSearchParams()
    params.set('prompt', visiblePrompt)
    if (panchangContext) {
      params.set('context', serialiseContext(panchangContext))
    }
    router.push(`/clients/${NATIVE_CLIENT_ID}/consume?${params.toString()}`)
  }

  // Export this window as an ICS file (browser-safe, client-side build)
  function handleExport() {
    const ics = buildMuhuratWindowIcs(
      {
        start_utc: w.start_utc,
        end_utc: w.end_utc,
        star_rating: w.star_rating,
        score: w.score,
        breakdown: w.breakdown,
        event: w.event,
      },
      'Bhubaneswar, IN',
      event,
    )
    if (!ics) return
    const datePart = w.start_utc ? w.start_utc.slice(0, 10) : 'muhurat'
    downloadIcs(ics, `muhurat-${event}-${datePart}.ics`)
  }

  const breakdownEntries = Object.entries(w.breakdown).filter(([, v]) => v !== 0)

  return (
    <div className="rounded-xl border border-[rgba(212,175,55,0.14)] bg-[rgba(28,28,26,0.55)] p-4 flex flex-col gap-3">
      {/* Row header: date + rank badge */}
      <div className="flex items-start justify-between gap-2">
        <div className="flex flex-col gap-1">
          <span className="font-serif text-base" style={{ color: 'var(--brand-gold)' }}>
            {dateLabel}
          </span>
          <span className="text-xs text-muted-foreground">
            {startTime} — {endTime}
          </span>
        </div>

        <div className="flex flex-col items-end gap-1 shrink-0">
          <StarRating value={w.star_rating} size="md" />
          <span
            className="text-xs font-mono rounded-full px-2 py-0.5"
            style={{
              color: 'rgba(212,175,55,0.55)',
              background: 'rgba(212,175,55,0.06)',
              border: '1px solid rgba(212,175,55,0.12)',
            }}
          >
            #{rank} · {w.score.toFixed(2)}
          </span>
        </div>
      </div>

      {/* Breakdown badges */}
      {breakdownEntries.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {breakdownEntries.map(([key, score]) => (
            <span
              key={key}
              className="text-xs rounded-full px-2.5 py-0.5 font-medium"
              style={badgeStyle(key, score)}
              title={`${labelForBreakdownKey(key)}: ${formatScore(score)}`}
            >
              {labelForBreakdownKey(key)} {formatScore(score)}
            </span>
          ))}
        </div>
      )}

      {/* Inline actions */}
      <div className="flex gap-2 mt-1">
        {/* Export to Calendar — enabled in 4C-7 */}
        <button
          onClick={handleExport}
          aria-label={`Export ${dateLabel} muhurat to calendar`}
          title="Download as .ics file"
          className="flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs font-medium transition-colors hover:bg-[rgba(212,175,55,0.12)]"
          style={{
            color: 'var(--brand-gold)',
            borderColor: 'rgba(212,175,55,0.30)',
            background: 'rgba(212,175,55,0.07)',
          }}
        >
          <CalendarDays className="h-3 w-3 shrink-0" aria-hidden="true" />
          <span>Export to Calendar</span>
        </button>

        {/* Ask Madhav — functional */}
        <button
          onClick={handleAskMadhav}
          aria-label={`Ask Madhav about ${dateLabel} for ${event.replace(/_/g, ' ')}`}
          title="Opens chat with pre-loaded muhurat context"
          className="flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs font-semibold transition-colors hover:bg-[rgba(212,175,55,0.12)]"
          style={{
            color: 'var(--brand-gold)',
            borderColor: 'rgba(212,175,55,0.30)',
            background: 'rgba(212,175,55,0.07)',
          }}
        >
          <MessageCircle className="h-3 w-3 shrink-0" aria-hidden="true" />
          <span>Ask Madhav about this date</span>
        </button>
      </div>
    </div>
  )
}

// ── Main component ─────────────────────────────────────────────────────────────

export function MuhuratResultsList({
  windows,
  isLoading,
  error,
  event,
  tzOffsetMinutes = 330,
  panchangContext,
}: MuhuratResultsListProps) {
  // Loading state
  if (isLoading) {
    return (
      <div className="flex flex-col gap-3" aria-busy="true" aria-label="Loading muhurat results">
        {Array.from({ length: 5 }).map((_, i) => (
          <SkeletonRow key={i} />
        ))}
      </div>
    )
  }

  // Error state
  if (error) {
    return (
      <div
        role="alert"
        className="rounded-xl border border-[rgba(220,80,60,0.20)] bg-[rgba(220,80,60,0.05)] px-5 py-6 text-center"
      >
        <p className="font-serif text-base" style={{ color: 'rgba(220,80,60,0.85)' }}>
          ॥ Muhurat Engine Error ॥
        </p>
        <p className="mt-2 text-sm text-muted-foreground">{error}</p>
      </div>
    )
  }

  // Not yet searched (null = no fetch triggered yet)
  if (windows === null) {
    return null
  }

  // Empty state — no windows scored above zero (unusual)
  if (windows.length === 0) {
    return (
      <div className="rounded-xl border border-[rgba(212,175,55,0.10)] bg-[rgba(28,28,26,0.40)] px-5 py-8 text-center">
        <p className="font-serif text-base" style={{ color: 'rgba(212,175,55,0.55)' }}>
          No auspicious windows found
        </p>
        <p className="mt-2 text-sm text-muted-foreground">
          All days in this range have conflicting inauspicious factors. Try extending the date range.
        </p>
      </div>
    )
  }

  // Sort defensively by score descending (backend already sorts)
  const sorted = [...windows].sort((a, b) => b.score - a.score)

  return (
    <div className="flex flex-col gap-3">
      <p className="text-xs text-muted-foreground px-1">
        {sorted.length} window{sorted.length !== 1 ? 's' : ''} · sorted by auspiciousness
      </p>
      {sorted.map((w, i) => (
        <MuhuratRow
          key={`${w.start_utc ?? i}`}
          window={w}
          rank={i + 1}
          event={event}
          tzOffsetMinutes={tzOffsetMinutes}
          panchangContext={panchangContext}
        />
      ))}
    </div>
  )
}
