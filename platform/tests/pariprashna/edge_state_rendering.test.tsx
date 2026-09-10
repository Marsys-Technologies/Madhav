/**
 * P2-G (Edge-state lexicon) — real render-level proof that the MOUNTED
 * `<WorkingBand>` shows §7.8/§7.5's exact copy for the subset of edge states
 * that have a genuine wire/reducer path today (network drop/resume,
 * user-stopped, and the six §7.5 error kinds). Every fixture here is reduced
 * through the SAME `threadReducer` and rendered through the SAME
 * `<WorkingBand>` a live turn uses — see `fixtures/edge_states.ts` for which
 * §7.8 rows have no wire path yet (and are pinned lexicon-only in
 * `edge_state_lexicon.test.ts`) and why.
 */
import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, cleanup, act } from '@testing-library/react'
import { threadReducer, initialThreadState } from '@/components/pariprashna/state/reducer'
import type { ThreadState, TurnState } from '@/components/pariprashna/state/types'
import { WorkingBand } from '@/components/pariprashna/working/WorkingBand'
import { EDGE_STATE_LABELS } from '@/lib/pariprashna/lexicon'
import {
  buildEdgeNetworkDropAndResumeFixture,
  buildEdgeUserStoppedFixture,
  buildEdgeErrorRateLimitFixture,
  buildEdgeErrorModelOverloadFixture,
  buildEdgeErrorTimeoutFixture,
  buildEdgeErrorNetworkFixture,
  buildEdgeErrorAuthFixture,
  buildEdgeErrorUnknownFixture,
} from '@/components/pariprashna/fixtures/edge_states'
import type { Fixture } from '@/components/pariprashna/fixtures/types'

afterEach(cleanup)

/** Fold the first `n` scheduled events of `fixture` through the real reducer, returning that turn's state. */
function reduceN(fixture: Fixture, n: number): TurnState {
  let state: ThreadState = initialThreadState
  for (const scheduled of fixture.events.slice(0, n)) {
    state = threadReducer(state, scheduled.event)
  }
  const turnId = (fixture.events[0].event as { turnId: string }).turnId
  const turn = state.turns.find((t) => t.id === turnId)
  if (!turn) throw new Error(`fixture turn "${turnId}" not found after reducing ${n} event(s)`)
  return turn
}

function reduceAll(fixture: Fixture): TurnState {
  return reduceN(fixture, fixture.events.length)
}

describe('WorkingBand — §7.8 network drop/resume renders the exact edge-state copy', () => {
  it('mid-drop: the band is the flat "Reconnecting…" label — not a suffix on the prior phase', () => {
    const fixture = buildEdgeNetworkDropAndResumeFixture()
    const turn = reduceN(fixture, 5) // stop right after the `reconnecting` event
    expect(turn.status).toBe('reconnecting')

    const { getAllByText } = render(<WorkingBand turn={turn} expanded={false} onToggle={() => {}} />)
    expect(getAllByText(EDGE_STATE_LABELS.network_drop)[0]).toBeTruthy()
  })

  it('on resume: a brief "Resumed — nothing lost" flash, which then self-clears', () => {
    vi.useFakeTimers()
    try {
      const fixture = buildEdgeNetworkDropAndResumeFixture()
      const reconnectingTurn = reduceN(fixture, 5)
      const resumedTurn = reduceN(fixture, 6)
      expect(resumedTurn.status).toBe('streaming')
      expect(resumedTurn.reconnectHollowCaret).toBe(false)

      const { getByText, queryByText, rerender } = render(
        <WorkingBand turn={reconnectingTurn} expanded={false} onToggle={() => {}} />
      )

      act(() => {
        rerender(<WorkingBand turn={resumedTurn} expanded={false} onToggle={() => {}} />)
      })
      expect(getByText(EDGE_STATE_LABELS.network_resumed)).toBeTruthy()

      act(() => {
        vi.advanceTimersByTime(2000)
      })
      expect(queryByText(EDGE_STATE_LABELS.network_resumed)).toBeNull()
    } finally {
      vi.useRealTimers()
    }
  })
})

describe('WorkingBand — §7.8 "User presses Stop" renders the exact edge-state copy', () => {
  it('interrupted turn shows "Stopped — kept what arrived" verbatim', () => {
    const turn = reduceAll(buildEdgeUserStoppedFixture())
    expect(turn.status).toBe('interrupted')

    const { getAllByText } = render(<WorkingBand turn={turn} expanded={false} onToggle={() => {}} />)
    expect(getAllByText(EDGE_STATE_LABELS.user_stopped)[0]).toBeTruthy()
  })
})

describe('WorkingBand — §7.5 error kinds render the exact classifier copy', () => {
  const cases: Array<{ name: string; build: () => Fixture; bandLabel: string }> = [
    { name: 'rate_limit', build: buildEdgeErrorRateLimitFixture, bandLabel: 'A moment — the provider asks us to slow' },
    { name: 'model_overload', build: buildEdgeErrorModelOverloadFixture, bandLabel: 'The model is overloaded' },
    { name: 'timeout', build: buildEdgeErrorTimeoutFixture, bandLabel: 'The reading ran long and was cut short' },
    { name: 'network (terminal)', build: buildEdgeErrorNetworkFixture, bandLabel: 'The connection was lost' },
    { name: 'auth', build: buildEdgeErrorAuthFixture, bandLabel: 'This model needs its key renewed' },
    { name: 'unknown', build: buildEdgeErrorUnknownFixture, bandLabel: 'Something failed on our side' },
  ]

  for (const { name, build, bandLabel } of cases) {
    it(`${name} → "${bandLabel}"`, () => {
      const turn = reduceAll(build())
      expect(turn.status).toBe('errored')
      expect(turn.error?.bandLabel).toBe(bandLabel)

      const { getAllByText } = render(<WorkingBand turn={turn} expanded={false} onToggle={() => {}} />)
      expect(getAllByText(bandLabel)[0]).toBeTruthy()
    })
  }
})
