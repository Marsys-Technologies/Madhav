/**
 * V3-E-023 — an interrupted turn's caveat paragraph unconditionally read
 * "The connection was lost partway", regardless of cause. An independent
 * verifier disproved this session's first pass (which assumed `interrupted`
 * was reached ONLY via a deliberate user Stop click): `snapshot.apply`
 * (reducer.ts) also sets `status: 'interrupted'` for a genuine stale-
 * connection/server-died timeout (`ring_buffer.ts`'s
 * `finalizeInterruptedIfStale`, forwarded by `resume/route.ts`) — a real
 * connection-loss case that must keep its own honest wording. The two
 * causes are now distinguished via `TurnState.interruptedReason`
 * ('user_stop' | 'connection_lost'), and the working-band label + this
 * caveat both branch on it rather than assuming a single cause for either.
 */
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Turn } from '../Turn'
import { makeInitialTurnState } from '../state/reducer'
import type { TurnState } from '../state/types'

function interruptedTurn(reason: TurnState['interruptedReason']): TurnState {
  const turn = makeInitialTurnState('turn-1', 'Give me a comprehensive analysis of every yoga in my chart.')
  turn.status = 'interrupted'
  turn.interruptedReason = reason
  turn.blocks = []
  return turn
}

describe('Turn — interrupted-state caveat matches the ACTUAL cause', () => {
  it('user_stop: never claims "connection was lost" for a deliberate Stop click', () => {
    render(<Turn turn={interruptedTurn('user_stop')} />)
    expect(screen.getAllByText(/Stopped — kept what arrived/i).length).toBeGreaterThan(0)
    expect(screen.queryByText(/connection was lost/i)).not.toBeInTheDocument()
  })

  it('connection_lost: DOES disclose the real network cause for a stale-timeout interruption', () => {
    render(<Turn turn={interruptedTurn('connection_lost')} />)
    expect(screen.getAllByText(/Connection lost — kept what arrived/i).length).toBeGreaterThan(0)
    expect(screen.getByText(/connection was lost partway/i)).toBeInTheDocument()
    // Must not ALSO claim the deliberate-stop label for a real failure.
    expect(screen.queryByText(/^Stopped — kept what arrived$/i)).not.toBeInTheDocument()
  })
})
