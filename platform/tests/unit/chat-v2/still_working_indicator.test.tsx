/**
 * X-S4 — Still-Working Indicator (25s streaming silence threshold)
 * Amendment 2: parent-context integration test with fake timers.
 *
 * Click-path: send complex query → still streaming after 25s → indicator
 *   appears with "Still working…" → streaming ends → indicator disappears.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, act } from '@testing-library/react'
import React, { useState } from 'react'
import { StillWorkingIndicator } from '@/components/chat/StillWorkingIndicator'

// ── A2: parent-context wrapper that holds isStreaming state ───────────────────

function StreamingShell({ children }: { children: (isStreaming: boolean, setIsStreaming: (v: boolean) => void) => React.ReactNode }) {
  const [isStreaming, setIsStreaming] = useState(false)
  return <>{children(isStreaming, setIsStreaming)}</>
}

describe('StillWorkingIndicator — parent-context integration (Amendment 2)', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('does NOT render when not streaming', () => {
    const { container } = render(
      <StreamingShell>
        {(isStreaming) => <StillWorkingIndicator isStreaming={isStreaming} />}
      </StreamingShell>,
    )
    expect(container.querySelector('[data-testid="v2-still-working"]')).toBeNull()
  })

  it('does NOT render when streaming but elapsed < 25s', () => {
    let setStreaming!: (v: boolean) => void
    const { container } = render(
      <StreamingShell>
        {(isStreaming, set) => {
          setStreaming = set
          return <StillWorkingIndicator isStreaming={isStreaming} />
        }}
      </StreamingShell>,
    )

    act(() => { setStreaming(true) })
    act(() => { vi.advanceTimersByTime(10_000) }) // only 10s
    expect(container.querySelector('[data-testid="v2-still-working"]')).toBeNull()
  })

  it('renders when streaming AND elapsed > 25s', () => {
    let setStreaming!: (v: boolean) => void
    const { container } = render(
      <StreamingShell>
        {(isStreaming, set) => {
          setStreaming = set
          return <StillWorkingIndicator isStreaming={isStreaming} />
        }}
      </StreamingShell>,
    )

    act(() => { setStreaming(true) })
    act(() => { vi.advanceTimersByTime(26_000) })
    expect(container.querySelector('[data-testid="v2-still-working"]')).not.toBeNull()
  })

  it('disappears when streaming ends (auto-hide)', () => {
    let setStreaming!: (v: boolean) => void
    const { container } = render(
      <StreamingShell>
        {(isStreaming, set) => {
          setStreaming = set
          return <StillWorkingIndicator isStreaming={isStreaming} />
        }}
      </StreamingShell>,
    )

    act(() => { setStreaming(true) })
    act(() => { vi.advanceTimersByTime(26_000) })
    expect(container.querySelector('[data-testid="v2-still-working"]')).not.toBeNull()

    act(() => { setStreaming(false) })
    expect(container.querySelector('[data-testid="v2-still-working"]')).toBeNull()
  })

  it('has aria-live="polite" for accessibility', () => {
    let setStreaming!: (v: boolean) => void
    const { container } = render(
      <StreamingShell>
        {(isStreaming, set) => {
          setStreaming = set
          return <StillWorkingIndicator isStreaming={isStreaming} />
        }}
      </StreamingShell>,
    )

    act(() => { setStreaming(true) })
    act(() => { vi.advanceTimersByTime(26_000) })
    const el = container.querySelector('[data-testid="v2-still-working"]')
    expect(el?.getAttribute('aria-live')).toBe('polite')
  })

  it('respects custom thresholdMs parameter', () => {
    let setStreaming!: (v: boolean) => void
    const { container } = render(
      <StreamingShell>
        {(isStreaming, set) => {
          setStreaming = set
          return <StillWorkingIndicator isStreaming={isStreaming} thresholdMs={5_000} />
        }}
      </StreamingShell>,
    )

    act(() => { setStreaming(true) })
    act(() => { vi.advanceTimersByTime(6_000) })
    expect(container.querySelector('[data-testid="v2-still-working"]')).not.toBeNull()
  })
})

// ── Timer cleanup test ────────────────────────────────────────────────────────

describe('StillWorkingIndicator — timer cleanup', () => {
  beforeEach(() => { vi.useFakeTimers() })
  afterEach(() => { vi.useRealTimers() })

  it('clears interval on unmount (no memory leak)', () => {
    const clearIntervalSpy = vi.spyOn(globalThis, 'clearInterval')
    const { unmount } = render(<StillWorkingIndicator isStreaming={true} />)
    act(() => { vi.advanceTimersByTime(1_000) })
    unmount()
    expect(clearIntervalSpy).toHaveBeenCalled()
  })
})
