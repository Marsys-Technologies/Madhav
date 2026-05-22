/**
 * C-S1: PreTokenIndicator.test.tsx
 *
 * Tests for the pre-token thinking indicator component.
 * Covers: render conditions, a11y, timer, unmount behaviour.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, act } from '@testing-library/react'
import { PreTokenIndicator } from '../../../src/components/chat/PreTokenIndicator'

// ---------------------------------------------------------------------------
// Setup: use fake timers
// ---------------------------------------------------------------------------

beforeEach(() => {
  vi.useFakeTimers()
})

afterEach(() => {
  vi.useRealTimers()
})

// ---------------------------------------------------------------------------
// Basic render
// ---------------------------------------------------------------------------

describe('PreTokenIndicator: basic render', () => {
  it('renders when hasFirstTextDelta=false', () => {
    render(<PreTokenIndicator hasFirstTextDelta={false} hasThinking={false} />)
    expect(screen.getByRole('status')).toBeDefined()
  })

  it('returns null when hasFirstTextDelta=true', () => {
    const { container } = render(
      <PreTokenIndicator hasFirstTextDelta={true} hasThinking={false} />
    )
    expect(container.firstChild).toBeNull()
  })
})

// ---------------------------------------------------------------------------
// A11y
// ---------------------------------------------------------------------------

describe('PreTokenIndicator: a11y', () => {
  it('has role="status"', () => {
    render(<PreTokenIndicator hasFirstTextDelta={false} hasThinking={false} />)
    expect(screen.getByRole('status')).toBeDefined()
  })

  it('has aria-live="polite"', () => {
    render(<PreTokenIndicator hasFirstTextDelta={false} hasThinking={false} />)
    expect(screen.getByRole('status').getAttribute('aria-live')).toBe('polite')
  })

  it('has aria-label with "Waiting for response" for non-thinking', () => {
    render(<PreTokenIndicator hasFirstTextDelta={false} hasThinking={false} />)
    const el = screen.getByRole('status')
    expect(el.getAttribute('aria-label')).toContain('Waiting for response')
  })

  it('has aria-label with "Thinking" for thinking-capable providers', () => {
    render(<PreTokenIndicator hasFirstTextDelta={false} hasThinking={true} />)
    const el = screen.getByRole('status')
    expect(el.getAttribute('aria-label')).toContain('Thinking')
  })
})

// ---------------------------------------------------------------------------
// Thinking label
// ---------------------------------------------------------------------------

describe('PreTokenIndicator: thinking label', () => {
  it('shows "Thinking" text when hasThinking=true', () => {
    render(<PreTokenIndicator hasFirstTextDelta={false} hasThinking={true} />)
    expect(screen.getByText(/Thinking/)).toBeDefined()
  })

  it('does NOT show "Thinking" text when hasThinking=false', () => {
    render(<PreTokenIndicator hasFirstTextDelta={false} hasThinking={false} />)
    expect(screen.queryByText(/Thinking/)).toBeNull()
  })

  it('shows elapsed seconds after 1s when hasThinking=true', () => {
    render(<PreTokenIndicator hasFirstTextDelta={false} hasThinking={true} />)
    act(() => {
      vi.advanceTimersByTime(1000)
    })
    expect(screen.getByText(/1s/)).toBeDefined()
  })

  it('increments elapsed seconds each second', () => {
    render(<PreTokenIndicator hasFirstTextDelta={false} hasThinking={true} />)
    act(() => {
      vi.advanceTimersByTime(3000)
    })
    expect(screen.getByText(/3s/)).toBeDefined()
  })

  it('aria-label updates with elapsed seconds', () => {
    render(<PreTokenIndicator hasFirstTextDelta={false} hasThinking={true} />)
    act(() => {
      vi.advanceTimersByTime(5000)
    })
    const el = screen.getByRole('status')
    expect(el.getAttribute('aria-label')).toContain('5 seconds')
  })
})

// ---------------------------------------------------------------------------
// Parent-context: unmount when hasFirstTextDelta transitions to true
// ---------------------------------------------------------------------------

describe('PreTokenIndicator: unmount on first text delta', () => {
  it('unmounts (returns null) when hasFirstTextDelta prop switches to true', () => {
    const { rerender, container } = render(
      <PreTokenIndicator hasFirstTextDelta={false} hasThinking={true} />
    )
    // Initially renders
    expect(container.firstChild).not.toBeNull()

    // First text delta arrives
    rerender(<PreTokenIndicator hasFirstTextDelta={true} hasThinking={true} />)
    expect(container.firstChild).toBeNull()
  })

  it('clears the interval timer after unmount', () => {
    const clearSpy = vi.spyOn(globalThis, 'clearInterval')
    const { unmount } = render(
      <PreTokenIndicator hasFirstTextDelta={false} hasThinking={true} />
    )
    unmount()
    expect(clearSpy).toHaveBeenCalled()
  })
})
