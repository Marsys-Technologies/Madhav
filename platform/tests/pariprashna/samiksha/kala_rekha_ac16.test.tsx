/**
 * AC-16 — the kāla-rekhā geometry IS the acceptance instrument — PB-3 lane L-2.
 *
 * This test computes and asserts the REAL geometry two ways, per AC-16's charge
 * that the test "actually check the rendered geometry (pixel positions / relative
 * proportions), not just that the component renders":
 *
 *   (1) The PURE geometry function `computeKalaRekha` against hand-computed,
 *       first-principles day-count proportions (an independent check, not a
 *       re-derivation of the function's own arithmetic).
 *   (2) The RENDERED <KalaRekha> DOM: the actual inline `left`/`width` percentages
 *       on the gold segment and today-dot nodes, parsed back off the mounted
 *       elements and asserted against the same first-principles proportions.
 */
import { describe, it, expect, afterEach } from 'vitest'
import { render, cleanup, screen } from '@testing-library/react'
import { computeKalaRekha } from '@/lib/pariprashna/samiksha/kala_rekha'
import { KalaRekha } from '@/components/pariprashna/samiksha/KalaRekha'

afterEach(cleanup)

// ── Fixture with clean, hand-verifiable day counts (2026 is not a leap year) ──
// reading = 2026-01-01, window = [2026-07-01, 2027-01-01), today = 2026-04-01.
//   total   = 2027-01-01 − 2026-01-01 = 365 days
//   segLeft = 2026-07-01 − 2026-01-01 = 181 days → 181/365 = 49.589041%
//   segRight= 2027-01-01 − 2026-01-01 = 365 days → 100%   → width = 50.410959%
//   today   = 2026-04-01 − 2026-01-01 =  90 days →  90/365 = 24.657534%
const FIX = { readingDate: '2026-01-01', windowStart: '2026-07-01', windowEnd: '2027-01-01', today: '2026-04-01' }
const EXP_LEFT = (181 / 365) * 100
const EXP_WIDTH = (184 / 365) * 100
const EXP_TODAY = (90 / 365) * 100

function parsePct(v: string | undefined): number {
  return Number(String(v).replace('%', ''))
}

describe('AC-16 (1) pure geometry — first-principles proportions', () => {
  it('segment left/width and today-dot match hand-computed day fractions', () => {
    const g = computeKalaRekha(FIX)
    expect(g.totalDays).toBe(365)
    expect(g.segmentLeftPct).toBeCloseTo(EXP_LEFT, 4) // 49.589041…
    expect(g.segmentWidthPct).toBeCloseTo(EXP_WIDTH, 4) // 50.410959…
    expect(g.todayPct).toBeCloseTo(EXP_TODAY, 4) // 24.657534…
    // left + width must reach the far edge (window end == timeline end).
    expect(g.segmentLeftPct + g.segmentWidthPct).toBeCloseTo(100, 6)
    expect(g.todayWithinWindow).toBe(false) // Apr 1 is before the Jul window
    expect(g.todayAfterWindow).toBe(false)
  })

  it('today INSIDE the window is flagged, and sits over the gold segment', () => {
    const g = computeKalaRekha({ ...FIX, today: '2026-09-01' })
    // 2026-09-01 − 2026-01-01 = 243 days
    expect(g.todayPct).toBeCloseTo((243 / 365) * 100, 4)
    expect(g.todayWithinWindow).toBe(true)
    expect(g.todayPct).toBeGreaterThanOrEqual(g.segmentLeftPct)
    expect(g.todayPct).toBeLessThanOrEqual(g.segmentLeftPct + g.segmentWidthPct)
  })

  it('today past the window end clamps to 100 and flags after-window', () => {
    const g = computeKalaRekha({ ...FIX, today: '2027-06-01' })
    expect(g.todayPct).toBe(100)
    expect(g.todayAfterWindow).toBe(true)
  })

  it('a degenerate (non-positive) timeline throws rather than fabricating a layout', () => {
    expect(() => computeKalaRekha({ ...FIX, windowEnd: '2025-01-01' })).toThrow(/must be after/)
  })
})

describe('AC-16 (2) rendered DOM geometry', () => {
  it('the mounted segment/dot carry the real computed left/width percentages', () => {
    render(<KalaRekha {...FIX} windowLabel="Jul 2026 – Jan 2027" />)

    const segment = screen.getByTestId('kala-rekha-segment')
    const today = screen.getByTestId('kala-rekha-today')

    // Real inline geometry off the mounted nodes — not merely "it rendered".
    expect(parsePct(segment.style.left)).toBeCloseTo(EXP_LEFT, 2)
    expect(parsePct(segment.style.width)).toBeCloseTo(EXP_WIDTH, 2)
    expect(parsePct(today.style.left)).toBeCloseTo(EXP_TODAY, 2)

    // The container mirrors the geometry on data-* for a census/CI harness.
    const root = screen.getByTestId('kala-rekha')
    expect(Number(root.getAttribute('data-total-days'))).toBe(365)
    expect(Number(root.getAttribute('data-segment-left-pct'))).toBeCloseTo(EXP_LEFT, 3)
    expect(root.getAttribute('data-today-within-window')).toBe('false')

    // The three structural marks all exist (line + segment + dot).
    expect(screen.getByTestId('kala-rekha-line')).toBeTruthy()
  })

  it('the today-dot advances rightward as real time passes (geometry moves)', () => {
    const { rerender } = render(<KalaRekha {...FIX} today="2026-04-01" />)
    const early = parsePct(screen.getByTestId('kala-rekha-today').style.left)
    rerender(<KalaRekha {...FIX} today="2026-10-01" />)
    const later = parsePct(screen.getByTestId('kala-rekha-today').style.left)
    expect(later).toBeGreaterThan(early) // the dot moved right — "advances along the line"
  })
})
