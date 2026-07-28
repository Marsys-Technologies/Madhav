/**
 * kāla-rekhā — the time-hairline sub-component — PB-3 lane L-2.
 *
 * Design authority: PARIPRASHNA_DESIGN_ENGINEERING_PLAN_v0_1.md §6.9.
 *
 * Renders the geometry computed by the PURE `computeKalaRekha` (lib/pariprashna/
 * samiksha/kala_rekha.ts):
 *   - a full-width 1 px `--pp-rule` hairline (the line itself)
 *   - a 2 px `--pp-gold` segment marking the prediction window
 *   - a 3 px solid gold dot marking TODAY's real date, advancing along the line
 *
 * AC-16: "the geometry is the acceptance instrument." The component reads its
 * positions from `computeKalaRekha` and writes them as inline `left`/`width`
 * percentages AND mirrors the exact numbers onto `data-*` attributes, so the
 * AC-16 test can assert the REAL rendered geometry off the DOM — not merely that
 * the component mounted.
 */

'use client'

import { computeKalaRekha, type KalaRekhaInput } from '@/lib/pariprashna/samiksha/kala_rekha'

/** Round to 4 dp for a stable, assertable inline value (sub-px is meaningless). */
function pct(n: number): string {
  return `${Number(n.toFixed(4))}%`
}

export interface KalaRekhaProps extends KalaRekhaInput {
  /** Human-facing window date caption (§6.9 microtype under the segment). */
  windowLabel?: string
}

export function KalaRekha(props: KalaRekhaProps) {
  const g = computeKalaRekha(props)

  return (
    <div
      className="pp-kala-rekha"
      role="img"
      aria-label={`Prediction timeline: window ${props.windowStart} to ${props.windowEnd}, today ${props.today}`}
      data-testid="kala-rekha"
      data-total-days={g.totalDays}
      data-segment-left-pct={g.segmentLeftPct}
      data-segment-width-pct={g.segmentWidthPct}
      data-today-pct={g.todayPct}
      data-today-within-window={g.todayWithinWindow ? 'true' : 'false'}
      data-today-after-window={g.todayAfterWindow ? 'true' : 'false'}
    >
      {/* 1 px --rule hairline — the line itself (§6.9). */}
      <div className="pp-kala-rekha__line" data-testid="kala-rekha-line" />

      {/* 2 px --gold window segment. */}
      <div
        className="pp-kala-rekha__segment"
        data-testid="kala-rekha-segment"
        style={{ left: pct(g.segmentLeftPct), width: pct(g.segmentWidthPct) }}
      />

      {/* 3 px solid gold today-dot. */}
      <div
        className="pp-kala-rekha__today"
        data-testid="kala-rekha-today"
        style={{ left: pct(g.todayPct) }}
      />

      {/* Caps microtype (§6.9): TODAY under the dot; window dates under the segment. */}
      <div className="pp-kala-rekha__caption pp-kala-rekha__caption--today" style={{ left: pct(g.todayPct) }}>
        TODAY
      </div>
      {props.windowLabel ? (
        <div
          className="pp-kala-rekha__caption pp-kala-rekha__caption--window"
          style={{ left: pct(g.segmentLeftPct + g.segmentWidthPct / 2) }}
        >
          {props.windowLabel}
        </div>
      ) : null}
    </div>
  )
}
