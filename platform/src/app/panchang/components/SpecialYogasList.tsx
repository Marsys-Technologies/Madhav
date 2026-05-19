'use client'

/**
 * SpecialYogasList — Active special yogas for the day.
 *
 * Renders the list of special yogas from detect_all_special_yogas output:
 *   {yoga, start_utc, end_utc, strength: "auspicious"|"inauspicious", stars: int}
 *
 * Auspicious yogas (Sarvartha Siddhi, Amrit Siddhi, Ravi Pushya, Guru Pushya,
 * Tripushkar, Dwipushkar, Siddha Yoga) → success green + star rating.
 * Inauspicious (Bhadra, Panchaka) → warning red/amber + ⚠ icon + no stars.
 *
 * Empty state: "No special yogas active today."
 *
 * Phase: 4C-4-S3 (Item 1)
 */

import { StarRating } from '@/components/ui/star-rating'

// ── Data shape (from sidecar serialize.py) ────────────────────────────────────

export interface YogaEntry {
  yoga: string
  start_utc: string | null
  end_utc: string | null
  strength: 'auspicious' | 'inauspicious'
  stars: number
}

// ── Display names + Sanskrit ──────────────────────────────────────────────────

interface YogaMeta {
  display: string
  sanskrit: string
}

const YOGA_META: Record<string, YogaMeta> = {
  sarvartha_siddhi: { display: 'Sarvartha Siddhi Yoga', sanskrit: 'सर्वार्थ सिद्धि' },
  amrit_siddhi:     { display: 'Amrit Siddhi Yoga',     sanskrit: 'अमृत सिद्धि' },
  ravi_pushya:      { display: 'Ravi Pushya Yoga',      sanskrit: 'रवि पुष्य' },
  guru_pushya:      { display: 'Guru Pushya Yoga',      sanskrit: 'गुरु पुष्य' },
  tripushkar:       { display: 'Tripushkar Yoga',       sanskrit: 'त्रिपुष्कर' },
  dwipushkar:       { display: 'Dwipushkar Yoga',       sanskrit: 'द्विपुष्कर' },
  siddha_yoga:      { display: 'Siddha Yoga',           sanskrit: 'सिद्ध योग' },
  bhadra:           { display: 'Bhadra (avoid)',        sanskrit: 'भद्रा' },
  panchaka:         { display: 'Panchaka Dosha',        sanskrit: 'पञ्चक' },
}

function getMeta(yogaKey: string): YogaMeta {
  return YOGA_META[yogaKey] ?? { display: yogaKey, sanskrit: '' }
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
  return 'all day'
}

// ── Props ─────────────────────────────────────────────────────────────────────

interface SpecialYogasListProps {
  specialYogas: unknown[] | null | undefined
  /** Local timezone offset in minutes (default 330 = IST +5:30) */
  tzOffsetMinutes?: number
}

// ── Yoga row ──────────────────────────────────────────────────────────────────

function YogaRow({
  entry,
  tzOffsetMinutes,
  isLast,
}: {
  entry: YogaEntry
  tzOffsetMinutes: number
  isLast: boolean
}) {
  const meta = getMeta(entry.yoga)
  const isAuspicious = entry.strength === 'auspicious'
  const window = formatWindow(entry.start_utc, entry.end_utc, tzOffsetMinutes)

  const nameColor = isAuspicious ? 'rgba(80,200,130,0.90)' : 'rgba(220,80,60,0.90)'
  const bgTint = isAuspicious ? 'rgba(80,200,130,0.04)' : 'rgba(220,80,60,0.04)'

  return (
    <div
      className={`flex items-center justify-between px-5 py-3 ${!isLast ? 'border-b border-[rgba(212,175,55,0.06)]' : ''}`}
      style={{ background: bgTint }}
      role="row"
      aria-label={`${meta.display}: ${window}`}
    >
      {/* Left: icon + name + Sanskrit */}
      <div className="flex items-center gap-2 min-w-0">
        {isAuspicious ? (
          <span
            className="text-sm shrink-0 leading-none"
            style={{ color: 'rgba(80,200,130,0.80)' }}
            aria-hidden="true"
          >
            ✓
          </span>
        ) : (
          <span
            className="text-sm shrink-0 leading-none"
            style={{ color: 'rgba(220,80,60,0.80)' }}
            aria-hidden="true"
          >
            ⚠
          </span>
        )}
        <div className="flex flex-col min-w-0">
          <span
            className="text-sm font-medium truncate"
            style={{ color: nameColor }}
          >
            {meta.display}
          </span>
          {meta.sanskrit && (
            <span
              className="font-serif text-[11px]"
              style={{ color: 'rgba(212,175,55,0.35)' }}
              aria-hidden="true"
            >
              {meta.sanskrit}
            </span>
          )}
        </div>
      </div>

      {/* Right: time window + stars */}
      <div className="flex items-center gap-3 shrink-0 ml-2">
        <span
          className="font-mono text-xs tabular-nums"
          style={{ color: 'rgba(212,175,55,0.55)' }}
        >
          {window}
        </span>
        {isAuspicious && entry.stars > 0 && (
          <StarRating value={entry.stars} max={5} size="sm" />
        )}
      </div>
    </div>
  )
}

// ── Main component ────────────────────────────────────────────────────────────

export function SpecialYogasList({
  specialYogas,
  tzOffsetMinutes = 330,
}: SpecialYogasListProps) {
  const yogas = (Array.isArray(specialYogas) ? specialYogas : []) as YogaEntry[]

  return (
    <section
      aria-label="Active Special Yogas Today"
      className="rounded-xl border border-[rgba(212,175,55,0.14)] bg-[rgba(28,28,26,0.50)] overflow-hidden shadow-[0_0_40px_rgba(212,175,55,0.04)]"
    >
      {/* Section heading */}
      <div className="px-5 py-2 border-b border-[rgba(212,175,55,0.08)]">
        <span
          className="text-[10px] font-semibold uppercase tracking-[0.15em]"
          style={{ color: 'rgba(212,175,55,0.35)' }}
        >
          Active Special Yogas Today
        </span>
      </div>

      {yogas.length === 0 ? (
        <div className="px-5 py-4">
          <span
            className="text-sm italic"
            style={{ color: 'rgba(212,175,55,0.35)' }}
          >
            No special yogas active today.
          </span>
        </div>
      ) : (
        yogas.map((entry, i) => (
          <YogaRow
            key={`${entry.yoga}-${i}`}
            entry={entry}
            tzOffsetMinutes={tzOffsetMinutes}
            isLast={i === yogas.length - 1}
          />
        ))
      )}
    </section>
  )
}
