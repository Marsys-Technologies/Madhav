/**
 * kāla-rekhā geometry — PB-3 (SAMĪKṢĀ) lane L-2.
 *
 * Design authority: PARIPRASHNA_DESIGN_ENGINEERING_PLAN_v0_1.md §6.9 + AC-16.
 *
 * §6.9 (verbatim): "a full-width 1 px `--rule` hairline spanning from the
 * reading's date to the window's far edge; the prediction window is a 2 px
 * `--gold` segment on it; a 3 px solid gold dot marks today and advances along
 * the line as real time passes."
 *
 * AC-16 names "the geometry is the acceptance instrument" — so this is a PURE,
 * isomorphic function that computes the exact percentage positions the card
 * renders, with NO React/DOM dependency, so the AC-16 test can assert the real
 * computed geometry (positions/proportions), not merely that a component mounted.
 *
 * The timeline's domain is [readingDate, windowEnd] — "from the reading's date
 * to the window's far edge" (§6.9). Every position is a percentage along that
 * domain:
 *   - gold segment: from windowStart to windowEnd
 *   - today dot:    the real current date, clamped into [0,100]
 */

/** ISO `yyyy-mm-dd` → whole days since the Unix epoch (UTC, calendar-exact). */
export function isoToEpochDay(isoDate: string): number {
  const [y, m, d] = isoDate.split('-').map(Number)
  // Date.UTC is calendar-correct across month/year/leap boundaries.
  return Math.round(Date.UTC(y, m - 1, d) / 86_400_000)
}

export interface KalaRekhaInput {
  /** The reading's date (timeline left edge). ISO yyyy-mm-dd. */
  readingDate: string
  /** Prediction window lower bound (inclusive). ISO yyyy-mm-dd. */
  windowStart: string
  /** Prediction window upper bound (exclusive) — the timeline's far edge. ISO. */
  windowEnd: string
  /** Today's real date (the advancing dot). ISO yyyy-mm-dd. */
  today: string
}

export interface KalaRekhaGeometry {
  /** Left edge of the 2 px gold window segment, as % of the full line. */
  segmentLeftPct: number
  /** Width of the gold window segment, as % of the full line. */
  segmentWidthPct: number
  /** Position of the 3 px today-dot, as % of the full line (clamped to [0,100]). */
  todayPct: number
  /** True when today falls inside [windowStart, windowEnd) (dot over the gold). */
  todayWithinWindow: boolean
  /** True when today is at/after windowEnd (window elapsed). */
  todayAfterWindow: boolean
  /** True when today is before the reading date (should not normally happen). */
  todayBeforeReading: boolean
  /** Total span of the line in days (readingDate → windowEnd). */
  totalDays: number
}

function clampPct(n: number): number {
  if (n < 0) return 0
  if (n > 100) return 100
  return n
}

/**
 * Compute the kāla-rekhā geometry. Throws on a non-positive domain (windowEnd
 * must be strictly after readingDate) — a degenerate timeline is a data error,
 * not something to paper over with a fabricated layout.
 */
export function computeKalaRekha(input: KalaRekhaInput): KalaRekhaGeometry {
  const reading = isoToEpochDay(input.readingDate)
  const start = isoToEpochDay(input.windowStart)
  const end = isoToEpochDay(input.windowEnd)
  const today = isoToEpochDay(input.today)

  const totalDays = end - reading
  if (totalDays <= 0) {
    throw new Error(
      `computeKalaRekha: window end (${input.windowEnd}) must be after reading date (${input.readingDate})`,
    )
  }

  const segmentLeftPct = clampPct(((start - reading) / totalDays) * 100)
  const segmentRightPct = clampPct(((end - reading) / totalDays) * 100)
  const segmentWidthPct = segmentRightPct - segmentLeftPct
  const todayPct = clampPct(((today - reading) / totalDays) * 100)

  return {
    segmentLeftPct,
    segmentWidthPct,
    todayPct,
    todayWithinWindow: today >= start && today < end,
    todayAfterWindow: today >= end,
    todayBeforeReading: today < reading,
    totalDays,
  }
}
