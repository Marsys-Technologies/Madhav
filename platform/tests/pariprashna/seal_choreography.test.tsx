/**
 * The Seal (§5.3 `settling`, BRIEF_PB-4 Lane F-2) — fixture-based render
 * assertions at its defined trigger conditions. Two of its six steps are
 * this lane's additions and get direct coverage:
 *   (4) the right dock's per-turn ledger fades in (`.pp-dock-seal-in`) the
 *       instant a turn reaches `settling`/`settled`, not while merely
 *       `streaming` with citations already defined;
 *   (5) the closing rule (`.pp-closing-rule`) draws beneath the answer
 *       region only once a turn is fully `settled` — never while
 *       `streaming` or `settling`.
 * The band-flip (step 3) and composer-restore (step 6) already have
 * coverage elsewhere in this suite (WorkingBand / PariprashnaApp); this
 * file only covers what this lane added.
 */
import { describe, it, expect, afterEach } from 'vitest'
import { render, screen, cleanup } from '@testing-library/react'
import { Turn } from '@/components/pariprashna/Turn'
import { RightDock } from '@/components/pariprashna/dock/RightDock'
import { DockControllerProvider } from '@/components/pariprashna/dock/DockController'
import { makeInitialTurnState } from '@/components/pariprashna/state/reducer'
import type { TurnState } from '@/components/pariprashna/state/types'

afterEach(cleanup)

function baseTurn(status: TurnState['status']): TurnState {
  const t = makeInitialTurnState('turn-1', 'What does this period ask of my career?')
  return {
    ...t,
    status,
    blocks: [{ id: 'b1', kind: 'paragraph', html: 'A settled paragraph.' }],
    citations: { 1: { n: 1, title: 'Daśā spine', sourceClass: 'chart_factor', relevance: 'career timing', ref: 'fact-42', grade: 'confirmed' } },
    grounding: status === 'settled' || status === 'settling' ? { factorCount: 1, classicalCount: 0, elapsedLabel: '0:12', gradeSummaryLabel: 'Core claim: well-grounded' } : null,
  }
}

describe('The Seal — closing rule (step 5)', () => {
  it('does not draw while streaming', () => {
    render(<Turn turn={baseTurn('streaming')} />)
    expect(document.querySelector('.pp-closing-rule')).toBeNull()
  })

  it('does not draw while settling (mid-choreography)', () => {
    render(<Turn turn={baseTurn('settling')} />)
    expect(document.querySelector('.pp-closing-rule')).toBeNull()
  })

  it('draws once the turn is fully settled', () => {
    render(<Turn turn={baseTurn('settled')} />)
    const rule = document.querySelector('.pp-closing-rule')
    expect(rule).not.toBeNull()
    expect(rule).toHaveAttribute('aria-hidden', 'true')
  })
})

describe('The Seal — right dock ledger fade (step 4)', () => {
  it('marks the sealed turn block with the seal-in class once settling begins', () => {
    render(
      <DockControllerProvider defaultOpen={true}>
        <RightDock turns={[baseTurn('settling')]} />
      </DockControllerProvider>,
    )
    expect(document.querySelector('.pp-dock-seal-in')).not.toBeNull()
  })

  it('does NOT mark a still-streaming turn (grounding accrues live per ruling 8a, but the coordinated fade is a settle-only event)', () => {
    render(
      <DockControllerProvider defaultOpen={true}>
        <RightDock turns={[baseTurn('streaming')]} />
      </DockControllerProvider>,
    )
    // The citation still renders live (accrual across passes, ruling 8a) —
    // only the fade-in class is settle-gated.
    expect(screen.getByText('Daśā spine')).toBeInTheDocument()
    expect(document.querySelector('.pp-dock-seal-in')).toBeNull()
  })

  it('stays marked once fully settled', () => {
    render(
      <DockControllerProvider defaultOpen={true}>
        <RightDock turns={[baseTurn('settled')]} />
      </DockControllerProvider>,
    )
    expect(document.querySelector('.pp-dock-seal-in')).not.toBeNull()
  })
})
