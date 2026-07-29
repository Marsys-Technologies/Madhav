import type { ParsedDateWindow } from './format'
import { kalaRekhaGeometry, windowLabel } from './format'

/**
 * kāla-rekhā-timeline — the review surface's time hairline (§6.9). A 1px rule spanning the padded
 * time-span, a 2px gold window segment, and a today-dot positioned from a REAL injected `nowIso`
 * (never a stub). Mirrors the geometry the dock `PredictionCard`'s own `KalaRekha` component uses
 * (lib/pariprashna/samiksha/kala_rekha.ts's `computeKalaRekha`) but is a distinct component reading
 * from this module's own `format.ts` geometry helper, extracted so the review Open/Resolve
 * sections share ONE implementation. Presentational; the numeric window label is rendered as text
 * alongside so the meaning is not conveyed by the graphic alone (a11y: not color/position-only).
 *
 * Named `KalaRekhaTimeline` (not `KalaRekha`) to avoid colliding with the dock card's own
 * `KalaRekha` component — the two render the same design element for two different call sites
 * (dock card vs. review-tab sections) and were kept as separate, independently-tested
 * implementations rather than merged at integration time.
 */
export function KalaRekhaTimeline({ window, nowIso }: { window: ParsedDateWindow | null; nowIso: string }) {
  const geo = kalaRekhaGeometry(window, nowIso)
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
      <div
        className="flex justify-between"
        style={{ fontSize: '8px', color: 'var(--pp-gold-tertiary, #7A5A1F)', fontFamily: 'var(--pp-font-mono, monospace)' }}
        aria-hidden="true"
      >
        <span>{window?.start ?? '—'}</span>
        <span>{window?.end ?? '—'}</span>
      </div>
    </div>
  )
}
