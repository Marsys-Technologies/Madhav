/**
 * P2-F (PPR-19) — one end-to-end smoke test through the REAL wiring
 * (`PariprashnaApp` → `useFixtureStream` → real `setTimeout`-scheduled
 * events → real reducer → real render), not the reducer-folding shortcut
 * `state_fixtures.ts` uses elsewhere in this battery. This is the one test
 * that proves the actual submit path — not just the reducer + renderer in
 * isolation — reaches a settled, accessible state, using real timers (no
 * fake-timer substitution) so it's honest about what actually runs.
 */
import { afterEach, describe, expect, it } from 'vitest'
import { cleanup, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import axe from 'axe-core'
import { PariprashnaApp } from '@/components/pariprashna/PariprashnaApp'

afterEach(cleanup)

describe('real submit → settle wiring (real timers, real components)', () => {
  it('single-pass fixture reaches a settled, axe-clean turn via the actual dev-picker submit path', async () => {
    render(<PariprashnaApp chartPin={{ name: 'Test Native', bornLine: '05 Feb 1984' }} />)

    const singlePassButton = screen.getByRole('button', { name: /single pass/i })
    await userEvent.click(singlePassButton)

    const turn = await waitFor(
      () => {
        const el = screen.getByTestId('pp-turn')
        expect(el).toHaveAttribute('data-turn-status', 'settled')
        return el
      },
      { timeout: 10000 },
    )

    const results = await axe.run(turn as HTMLElement, {
      runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'] },
    })
    const blocking = results.violations.filter((v) => v.impact === 'critical' || v.impact === 'serious')
    expect(blocking, blocking.map((v) => `${v.id}: ${v.help}`).join('\n')).toHaveLength(0)
  }, 15000)
})
