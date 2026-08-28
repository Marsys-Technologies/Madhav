/**
 * V3-E — the settle announcement ("Reading complete. Grounded in N chart
 * factors.") is built from the raw, grade-blind citation COUNT
 * (`turn.grounding.factorCount`) and never reads the already-computed honest
 * `gradeSummaryLabel` (state/groundingRollup.ts's WELL-GROUNDED / SUPPORTED /
 * CATALOG-ONLY — UNVERIFIED / HONEST-GAP rollup, §N.7/§N.8: a fabricated
 * confident verdict is a defect even when the underlying count is accurate).
 *
 * LIVE reproduction (2026-08-27, deployed amjis-web, chart 1c826d5a): a real
 * turn's own receipt recorded evidence_grades.grade_counts = {unverified: 4},
 * hallucination_count: 4, and the pipeline's own citation_gate fired
 * `grade: "ERROR", detail: "... 0 citations ... must be grounded"` — yet the
 * settled announcement read "Reading complete. Grounded in 4 chart factors."
 * with no qualifier. This test reproduces that shape with a fixture-level
 * grounding summary instead of the live network capture.
 */
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { GroundingRegion } from '../GroundingRegion'
import { makeInitialTurnState } from '../state/reducer'
import { GRADE_SUMMARY_CATALOG_ONLY, GRADE_SUMMARY_HONEST_GAP, GRADE_SUMMARY_WELL_GROUNDED } from '../state/groundingRollup'
import type { TurnState } from '../state/types'

function settledTurnWith(gradeSummaryLabel: string, factorCount = 4): TurnState {
  const turn = makeInitialTurnState('turn-1', 'What does this period ask of my career?')
  turn.status = 'settled'
  turn.grounding = {
    factorCount,
    classicalCount: 0,
    elapsedLabel: '0:71',
    gradeSummaryLabel,
    source: 'client_estimate',
  }
  return turn
}

describe('GroundingRegion — grade-honest settle announcement', () => {
  it('discloses an unverified/catalog-only grounding set, not a bare confident count', () => {
    const turn = settledTurnWith(GRADE_SUMMARY_CATALOG_ONLY)
    render(<GroundingRegion turn={turn} />)
    const status = screen.getByRole('status')
    // The announcement must not read as an unqualified "Grounded in N chart
    // factors." when every citation is unverified/catalog-only — that is
    // exactly the confident-verdict-on-a-bare-count fabrication
    // groundingRollup.ts's own doc comment (lines 8-14) says this instrument
    // exists to prevent.
    expect(status.textContent).toMatch(/unverified|catalog-only/i)
  })

  it('still reads as a confident grounded summary when the rollup says WELL-GROUNDED', () => {
    const turn = settledTurnWith(GRADE_SUMMARY_WELL_GROUNDED)
    render(<GroundingRegion turn={turn} />)
    const status = screen.getByRole('status')
    expect(status.textContent).toMatch(/grounded/i)
    expect(status.textContent).not.toMatch(/unverified|catalog-only/i)
  })

  it('never pairs "honest gap" wording with a nonzero parenthetical factor count (independent-verifier follow-up)', () => {
    // The server-derived branch of s1LiveAdapter.ts sources factorCount from
    // the client's own citation tally and gradeSummaryLabel from the
    // server's independent grade_counts aggregate — the two CAN disagree
    // (fixtures/honest_gap.ts already models factorCount:4 alongside the
    // HONEST_GAP label). "Honest gap — silence verified... (4 chart
    // factors)." reads as self-contradictory to a screen-reader user.
    const turn = settledTurnWith(GRADE_SUMMARY_HONEST_GAP, 4)
    render(<GroundingRegion turn={turn} />)
    const status = screen.getByRole('status')
    expect(status.textContent).not.toMatch(/\(\s*4\s*chart factors\s*\)/i)
  })
})
