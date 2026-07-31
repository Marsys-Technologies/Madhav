/**
 * PB-6 (SAMĀPTI, 2026-07-30) — regression test for two defects fixed together:
 *
 *   (1) `dock/PredictionCard.tsx` used to be its own re-implementation of the
 *       kāla-rekhā geometry, driven by pre-baked `PredictionCardData` fraction
 *       fields (`todayFractionOfSpan` etc.) whose ONLY real producer anywhere
 *       in the codebase was a hardcoded fixture literal (`0.3`). It now MOUNTS
 *       the spec-conformant `samiksha/KalaRekha` (previously dead code,
 *       imported by nothing) and computes geometry live from real ISO dates.
 *   (2) The dot was 7px (this file's own inline `<span>`); it is now the
 *       samiksha `KalaRekha` component's 3px dot (`.pp-kala-rekha__today`,
 *       samiksha.css).
 *
 * This test asserts the REAL rendered geometry off the mounted DOM (the same
 * AC-16 discipline `kala_rekha_ac16.test.tsx` uses for the bare `KalaRekha`
 * component) — not merely that `PredictionCard` renders without throwing.
 */
import { describe, it, expect, afterEach } from 'vitest'
import { render, cleanup, screen } from '@testing-library/react'
import { computeKalaRekha } from '@/lib/pariprashna/samiksha/kala_rekha'
import { PredictionCard } from '@/components/pariprashna/dock/PredictionCard'
import type { PredictionCardData } from '@/components/pariprashna/state/types'

afterEach(cleanup)

const PREDICTION: PredictionCardData = {
  id: 'pred-test-1',
  claim: 'A test claim, timed to a real window.',
  readingDate: '2026-01-01',
  windowStart: '2026-07-01',
  windowEnd: '2027-01-01',
  windowStartLabel: 'Jul 2026',
  windowEndLabel: 'Jan 2027',
  confidencePhrase: 'more likely than not',
  ref: 'PRED.TEST.001',
  lifecycle: 'window_open',
}

function parsePct(v: string | undefined): number {
  return Number(String(v).replace('%', ''))
}

describe('dock/PredictionCard mounts the spec-conformant kāla-rekhā (PB-6)', () => {
  it('renders the REAL samiksha KalaRekha (not the former 7px fixture-fed inline dot)', () => {
    render(<PredictionCard prediction={PREDICTION} />)

    // Proves KalaRekha is genuinely mounted (previously dead code, imported
    // by nothing): its distinctive test ids exist on the dock's own render.
    const root = screen.getByTestId('kala-rekha')
    const segment = screen.getByTestId('kala-rekha-segment')
    const today = screen.getByTestId('kala-rekha-today')
    expect(root).toBeTruthy()

    // The 3px dot is samiksha's `.pp-kala-rekha__today` CSS class, not the
    // old inline Tailwind `rounded-full` 7px span.
    expect(today.className).toContain('pp-kala-rekha__today')

    // Geometry is computed LIVE from real ISO dates (computeKalaRekha), not a
    // stored fraction — cross-check the rendered percentages against an
    // independent call to the same pure function with today's REAL date
    // (mirroring what the component itself reads from the clock).
    const todayIso = new Date().toISOString().slice(0, 10)
    const expected = computeKalaRekha({
      readingDate: PREDICTION.readingDate,
      windowStart: PREDICTION.windowStart,
      windowEnd: PREDICTION.windowEnd,
      today: todayIso,
    })
    expect(parsePct(segment.style.left)).toBeCloseTo(expected.segmentLeftPct, 2)
    expect(parsePct(segment.style.width)).toBeCloseTo(expected.segmentWidthPct, 2)
    expect(parsePct(today.style.left)).toBeCloseTo(expected.todayPct, 2)
    expect(Number(root.getAttribute('data-total-days'))).toBe(expected.totalDays)
  })

  it('renders the §6.9 footer row (confidence phrase + mono prediction ref)', () => {
    render(<PredictionCard prediction={PREDICTION} />)
    const footer = screen.getByTestId('prediction-card-footer')
    expect(footer.textContent).toContain(PREDICTION.confidencePhrase)
    expect(footer.textContent).toContain(PREDICTION.ref)
  })

  it('maps every dock lifecycle value to the IDENTICAL eyebrow text the former inline map produced', () => {
    const CASES: Array<[PredictionCardData['lifecycle'], string]> = [
      ['window_open', 'TIME-INDEXED READING · WINDOW OPEN'],
      ['window_closing', 'TIME-INDEXED READING · WINDOW CLOSING'],
      ['awaiting_outcome', 'TIME-INDEXED READING · AWAITING OUTCOME'],
      ['resolved_confirmed', 'TIME-INDEXED READING · RESOLVED — CONFIRMED'],
      ['resolved_missed', 'TIME-INDEXED READING · RESOLVED — MISSED'],
      ['resolved_mixed', 'TIME-INDEXED READING · RESOLVED — MIXED'],
    ]
    for (const [lifecycle, expectedEyebrow] of CASES) {
      cleanup()
      render(<PredictionCard prediction={{ ...PREDICTION, lifecycle }} />)
      expect(screen.getByTestId('prediction-card-eyebrow').textContent).toBe(expectedEyebrow)
    }
  })
})
