'use client'

/**
 * ChoghadiyaPanel — Collapsible Choghadiya panel.
 *
 * Data shape from sidecar serialize.py _serialize_choghadiya:
 *   { day: [{label, start_utc, end_utc}, ...], night: [{label, start_utc, end_utc}, ...] }
 * Each period has 8 segments (24h / 3h per vara = 8 day + 8 night).
 *
 * Choghadiya quality mapping:
 *   Good:    Amrit (1), Shubh (2), Labh (3) — success green
 *   Neutral: Char (4)                         — neutral gold
 *   Bad:     Rog (5), Kaal (6), Udveg (7)     — warning red
 *
 * Collapsed by default. Toggle opens both Day and Night sub-sections.
 *
 * Phase: 4C-4-S3 (Item 2)
 */

import { CollapsibleRoot, CollapsibleTrigger, CollapsibleContent } from '@/components/ui/collapsible'

// ── Data shape ────────────────────────────────────────────────────────────────

interface ChoghadiyaSegment {
  label: string
  start_utc: string | null
  end_utc: string | null
}

interface ChoghadiyaData {
  day?: ChoghadiyaSegment[]
  night?: ChoghadiyaSegment[]
}

// ── Display metadata ──────────────────────────────────────────────────────────

type ChoghadiyaQuality = 'good' | 'neutral' | 'bad'

interface ChoghadiyaMeta {
  display: string
  sanskrit: string
  quality: ChoghadiyaQuality
}

const CHOGHADIYA_META: Record<string, ChoghadiyaMeta> = {
  // Good muhurtas
  amrit:  { display: 'Amrit',  sanskrit: 'अमृत',  quality: 'good' },
  shubh:  { display: 'Shubh',  sanskrit: 'शुभ',   quality: 'good' },
  labh:   { display: 'Labh',   sanskrit: 'लाभ',   quality: 'good' },
  // Neutral
  char:   { display: 'Char',   sanskrit: 'चर',    quality: 'neutral' },
  // Bad
  rog:    { display: 'Rog',    sanskrit: 'रोग',   quality: 'bad' },
  kaal:   { display: 'Kaal',   sanskrit: 'काल',   quality: 'bad' },
  udveg:  { display: 'Udveg',  sanskrit: 'उद्वेग', quality: 'bad' },
}

function getChoghadiyaMeta(label: string): ChoghadiyaMeta {
  // Labels from sidecar: "choghadiya_amrit", "choghadiya_shubh", etc.
  const key = label.replace(/^choghadiya_/, '').toLowerCase()
  return CHOGHADIYA_META[key] ?? { display: label, sanskrit: '', quality: 'neutral' }
}

const QUALITY_COLOR: Record<ChoghadiyaQuality, string> = {
  good:    'rgba(80,200,130,0.90)',
  neutral: 'rgba(212,175,55,0.75)',
  bad:     'rgba(220,80,60,0.90)',
}

const QUALITY_BG: Record<ChoghadiyaQuality, string> = {
  good:    'rgba(80,200,130,0.04)',
  neutral: 'rgba(212,175,55,0.03)',
  bad:     'rgba(220,80,60,0.04)',
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

// ── Segment row ───────────────────────────────────────────────────────────────

function SegmentRow({
  segment,
  tzOffsetMinutes,
  isLast,
}: {
  segment: ChoghadiyaSegment
  tzOffsetMinutes: number
  isLast: boolean
}) {
  const meta = getChoghadiyaMeta(segment.label)
  const window = formatWindow(segment.start_utc, segment.end_utc, tzOffsetMinutes)

  return (
    <div
      className={`flex items-center justify-between px-5 py-2.5 ${!isLast ? 'border-b border-[rgba(212,175,55,0.05)]' : ''}`}
      style={{ background: QUALITY_BG[meta.quality] }}
      role="row"
      aria-label={`${meta.display}: ${window}`}
    >
      <div className="flex items-center gap-2">
        <span
          className="text-sm font-medium"
          style={{ color: QUALITY_COLOR[meta.quality] }}
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
      <span
        className="font-mono text-xs tabular-nums"
        style={{ color: 'rgba(212,175,55,0.55)' }}
      >
        {window}
      </span>
    </div>
  )
}

// ── Sub-section ───────────────────────────────────────────────────────────────

function ChoghadiyaSubSection({
  title,
  segments,
  tzOffsetMinutes,
}: {
  title: string
  segments: ChoghadiyaSegment[]
  tzOffsetMinutes: number
}) {
  return (
    <div>
      <div
        className="px-5 py-1.5 border-b border-[rgba(212,175,55,0.08)]"
        style={{ background: 'rgba(212,175,55,0.02)' }}
      >
        <span
          className="text-[10px] font-semibold uppercase tracking-[0.12em]"
          style={{ color: 'rgba(212,175,55,0.30)' }}
        >
          {title}
        </span>
      </div>
      {segments.length === 0 ? (
        <div className="px-5 py-3">
          <span className="text-sm italic opacity-30">No data</span>
        </div>
      ) : (
        segments.map((seg, i) => (
          <SegmentRow
            key={`${seg.label}-${i}`}
            segment={seg}
            tzOffsetMinutes={tzOffsetMinutes}
            isLast={i === segments.length - 1}
          />
        ))
      )}
    </div>
  )
}

// ── Props ─────────────────────────────────────────────────────────────────────

interface ChoghadiyaPanelProps {
  choghadiya: unknown | null | undefined
  /** Local timezone offset in minutes (default 330 = IST +5:30) */
  tzOffsetMinutes?: number
}

// ── Main component ────────────────────────────────────────────────────────────

export function ChoghadiyaPanel({
  choghadiya,
  tzOffsetMinutes = 330,
}: ChoghadiyaPanelProps) {
  const data = (choghadiya && typeof choghadiya === 'object' && !Array.isArray(choghadiya))
    ? (choghadiya as ChoghadiyaData)
    : null

  const daySegments: ChoghadiyaSegment[] = Array.isArray(data?.day) ? (data.day as ChoghadiyaSegment[]) : []
  const nightSegments: ChoghadiyaSegment[] = Array.isArray(data?.night) ? (data.night as ChoghadiyaSegment[]) : []
  const totalSegments = daySegments.length + nightSegments.length

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
            Choghadiya
          </span>
          <span
            className="text-xs mt-0.5"
            style={{ color: 'rgba(212,175,55,0.50)' }}
          >
            {totalSegments > 0 ? `${totalSegments} segments (Day + Night)` : 'Day & Night muhurtas'}
          </span>
        </div>
      </CollapsibleTrigger>

      <CollapsibleContent>
        {data === null ? (
          <div className="px-5 py-4">
            <span
              className="text-sm italic"
              style={{ color: 'rgba(212,175,55,0.35)' }}
            >
              Choghadiya data not available.
            </span>
          </div>
        ) : (
          <>
            <ChoghadiyaSubSection
              title="Day Choghadiya"
              segments={daySegments}
              tzOffsetMinutes={tzOffsetMinutes}
            />
            <ChoghadiyaSubSection
              title="Night Choghadiya"
              segments={nightSegments}
              tzOffsetMinutes={tzOffsetMinutes}
            />
          </>
        )}
      </CollapsibleContent>
    </CollapsibleRoot>
  )
}
