/**
 * V3-E — an interrupted turn's caveat paragraph unconditionally read "The
 * connection was lost partway", but `interrupted` status is reached ONLY via
 * a deliberate user Stop click (`reducer.ts` — no other action sets it); the
 * working-band label two lines above it already correctly says "Stopped —
 * kept what arrived" (`EDGE_STATE_LABELS.user_stopped`). The two adjacent
 * pieces of copy in the same settled turn attributed the interruption to two
 * contradictory causes: one honest (user pressed Stop), one invented
 * (network failure) — §N.7 item 6, an invented cause standing in for the
 * real one. LIVE-reproduced 2026-08-28 pressing Stop mid-turn on the
 * deployed synthetic-chart Portal.
 */
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Turn } from '../Turn'
import { makeInitialTurnState } from '../state/reducer'
import type { TurnState } from '../state/types'

function interruptedTurn(): TurnState {
  const turn = makeInitialTurnState('turn-1', 'Give me a comprehensive analysis of every yoga in my chart.')
  turn.status = 'interrupted'
  turn.blocks = []
  return turn
}

describe('Turn — interrupted-state caveat does not invent a network cause', () => {
  it('never claims "connection was lost" for a user-initiated Stop', () => {
    render(<Turn turn={interruptedTurn()} />)
    // The band's own honest label for this exact status (rendered twice:
    // the visible label and its sr-only aria-live twin).
    expect(screen.getAllByText(/Stopped — kept what arrived/i).length).toBeGreaterThan(0)
    // The caveat text must not contradict it by inventing a network cause.
    expect(screen.queryByText(/connection was lost/i)).not.toBeInTheDocument()
  })
})
