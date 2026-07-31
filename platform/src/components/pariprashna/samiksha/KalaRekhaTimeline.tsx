import type { ParsedDateWindow } from './format'
import { kalaRekhaGeometry, windowLabel } from './format'

/**
 * kāla-rekhā-timeline — the review surface's time hairline (§6.9). A 1px rule
 * spanning the domain `[readingDate, windowEnd]` — "from the reading's date
 * to the window's far edge" (§6.9, verbatim) — a 2px gold window segment, and
 * a today-dot positioned from a REAL injected `nowIso` (never a stub).
 * Mirrors the geometry the dock `PredictionCard`'s own `KalaRekha` component
 * uses (lib/pariprashna/samiksha/kala_rekha.ts's `computeKalaRekha`) but is a
 * distinct component reading from this module's own `format.ts` geometry
 * helper, extracted so the review Open/Resolve sections share ONE
 * implementation. Presentational; the numeric window label is rendered as
 * text alongside so the meaning is not conveyed by the graphic alone (a11y:
 * not color/position-only).
 *
 * PB-6 (SAMĀPTI, 2026-07-30): domain corrected from a window-padded span
 * (no reading-date anchor) to `[readingDate, windowEnd]` to match §6.9. The
 * start/end date captions now sit at their true window-segment fractions
 * (`geo.windowStartFraction` / `geo.windowEndFraction`) instead of the
 * container's 0%/100% edges — previously correct only by coincidence when
 * the window happened to fill the whole (wrong) padded domain; with a real
 * `readingDate` the window start in particular is very rarely at 0%.
 *
 * Named `KalaRekhaTimeline` (not `KalaRekha`) to avoid colliding with the dock card's own
 * `KalaRekha` component — the two render the same design element for two different call sites
 * (dock card vs. review-tab sections) and were kept as separate, independently-tested
 * implementations rather than merged at integration time.
 */
export function KalaRekhaTimeline({
  window,
  nowIso,
  readingDateIso,
}: {
  window: ParsedDateWindow | null
  nowIso: string
  /** ISO yyyy-mm-dd — the reading's date, the timeline's left edge (§6.9). */
  readingDateIso: string
}) {
  const geo = kalaRekhaGeometry(window, nowIso, readingDateIso)
  const label = windowLabel(window)

  return (
    <div>
      <div
        className="relative"
        style={{ height: '14px' }}
        role="img"
        aria-label={`Window ${label}${geo ? '' : ' (not scaled — open-ended)'}`}
      >
        <span
          className="absolute"
          aria-hidden="true"
          style={{ top: 6, left: 0, right: 0, height: 1, background: 'var(--pp-rule, rgba(201,162,76,0.25))' }}
        />
        {geo && (
          <>
            <span
              className="absolute"
              aria-hidden="true"
              style={{
                top: 5.5,
                left: `${geo.windowStartFraction * 100}%`,
                width: `${(geo.windowEndFraction - geo.windowStartFraction) * 100}%`,
                height: 2,
                background: 'var(--pp-gold, #C9A24C)',
              }}
            />
            <span
              className="absolute rounded-full"
              aria-hidden="true"
              style={{
                top: 3,
                left: `${geo.todayFraction * 100}%`,
                width: 7,
                height: 7,
                marginLeft: -3.5,
                background: 'var(--pp-gold, #C9A24C)',
              }}
            />
          </>
        )}
      </div>
      {geo ? (
        // Absolutely positioned under their TRUE window-segment fractions —
        // not the container's 0%/100% edges, which only label the domain
        // (readingDate .. windowEnd), not the window itself.
        <div className="relative" style={{ height: '10px' }} aria-hidden="true">
          <span
            className="absolute"
            style={{
              left: `${geo.windowStartFraction * 100}%`,
              transform: geo.windowStartFraction > 0.85 ? 'translateX(-100%)' : 'translateX(0%)',
              fontSize: '8px',
              color: 'var(--pp-gold-tertiary, #7A5A1F)',
              fontFamily: 'var(--pp-font-mono, monospace)',
              whiteSpace: 'nowrap',
            }}
          >
            {window?.start ?? '—'}
          </span>
          <span
            className="absolute"
            style={{
              left: `${geo.windowEndFraction * 100}%`,
              transform: 'translateX(-100%)',
              fontSize: '8px',
              color: 'var(--pp-gold-tertiary, #7A5A1F)',
              fontFamily: 'var(--pp-font-mono, monospace)',
              whiteSpace: 'nowrap',
            }}
          >
            {window?.end ?? '—'}
          </span>
        </div>
      ) : (
        <div
          className="flex justify-between"
          style={{ fontSize: '8px', color: 'var(--pp-gold-tertiary, #7A5A1F)', fontFamily: 'var(--pp-font-mono, monospace)' }}
          aria-hidden="true"
        >
          <span>{window?.start ?? '—'}</span>
          <span>{window?.end ?? '—'}</span>
        </div>
      )}
    </div>
  )
}
