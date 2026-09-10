/**
 * V3-E-024 fast-follow (flagged by the independent verifier of the
 * turn.close fix): a settled turn with `grounding: null` — a clarification-
 * only turn is the live case, now newly reachable at `'settled'` since the
 * turn.close broadening — previously rendered
 * `renderSealCompleteLabel(0, ...)` = "Grounded in 0 sources · Ts",
 * conflating "grounding was never computed for this turn" with "grounding
 * was computed and found nothing" (§N.7 item 6: an invented judgment
 * standing in for an honest null).
 */
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { WorkingBand } from '../WorkingBand'
import { makeInitialTurnState } from '../../state/reducer'
import type { TurnState } from '../../state/types'

function settledTurn(grounding: TurnState['grounding']): TurnState {
  const turn = makeInitialTurnState('turn-1', 'Is it a good time?')
  turn.status = 'settled'
  turn.grounding = grounding
  return turn
}

describe('WorkingBand — sealed label with no grounding computed', () => {
  it('never says "Grounded in 0 sources" for a turn that never computed grounding (e.g. clarification)', () => {
    render(<WorkingBand turn={settledTurn(null)} expanded={false} onToggle={() => {}} />)
    expect(screen.queryAllByText(/Grounded in 0 sources/i).length).toBe(0)
    expect(screen.getAllByText(/^Answered/i).length).toBeGreaterThan(0)
  })

  it('still shows the real grounded-sources label when grounding was actually computed', () => {
    render(
      <WorkingBand
        turn={settledTurn({ factorCount: 4, classicalCount: 0, elapsedLabel: '0:10', gradeSummaryLabel: 'x', source: 'client_estimate' })}
        expanded={false}
        onToggle={() => {}}
      />,
    )
    expect(screen.getAllByText(/Grounded in 4 sources/i).length).toBeGreaterThan(0)
  })
})
