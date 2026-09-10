/**
 * P2-F (PPR-19) §9.3: "Working-band label changes announce via a separate
 * throttled polite region (≥5s between announcements); elapsed-counter
 * ticks are aria-hidden."
 *
 * Unit-level (WorkingBand directly, no DockController needed — it doesn't
 * consume that context) with fake timers, proving the throttle is real: an
 * announcement text change inside the 5s window does NOT reach the live
 * region immediately, and DOES reach it once the window elapses.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { act, cleanup, render, screen } from '@testing-library/react'
import { WorkingBand } from '@/components/pariprashna/working/WorkingBand'
import { makeInitialTurnState } from '@/components/pariprashna/state/reducer'
import type { TurnState } from '@/components/pariprashna/state/types'

function turnWithLabel(label: string): TurnState {
  const t = makeInitialTurnState('t1', 'question')
  return { ...t, status: 'thinking', phaseLabel: label }
}

beforeEach(() => {
  vi.useFakeTimers()
})

afterEach(() => {
  cleanup()
  vi.useRealTimers()
})

describe('WorkingBand aria-live throttle + aria-hidden ticks (§9.3)', () => {
  it('elapsed-counter tick is aria-hidden', () => {
    render(<WorkingBand turn={turnWithLabel('Reading the chart…')} expanded={false} onToggle={() => {}} />)
    const tick = screen.getByTestId('pp-band-elapsed')
    expect(tick).toHaveAttribute('aria-hidden')
  })

  it('the visible label region itself stays aria-live="off" (it swaps too often to announce every change)', () => {
    const { container } = render(<WorkingBand turn={turnWithLabel('Reading the chart…')} expanded={false} onToggle={() => {}} />)
    const visible = container.querySelector('.pp-band-label')
    expect(visible).toHaveAttribute('aria-live', 'off')
  })

  it('throttles: a label change inside the 5s window does not reach the live region immediately, but does after the window elapses', () => {
    const { container, rerender } = render(<WorkingBand turn={turnWithLabel('Reading the question…')} expanded={false} onToggle={() => {}} />)
    const live = () => container.querySelector('[role="status"][aria-live="polite"]')
    expect(live()?.textContent).toContain('Reading the question…')

    // A label change 1s later — well inside the 5s throttle window.
    act(() => vi.advanceTimersByTime(1000))
    rerender(<WorkingBand turn={turnWithLabel('Cross-referencing the daśā…')} expanded={false} onToggle={() => {}} />)
    // Still the OLD text — the throttle has not released yet.
    expect(live()?.textContent).toContain('Reading the question…')

    // Advance past the remaining throttle window (5000ms total since the
    // first announcement) and flush the hook's own scheduled setTimeout.
    act(() => vi.advanceTimersByTime(4200))
    expect(live()?.textContent).toContain('Cross-referencing the daśā…')
  })
})
