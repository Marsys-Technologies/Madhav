/**
 * X-S6 — Auto-Scroll Discipline
 * Amendment 2: parent-context integration tests for scroll discipline.
 *
 * Click-path: streaming → user scrolls up → auto-scroll stops → "N new" button
 *   appears → click → scrolls to bottom and resets unread count.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, act } from '@testing-library/react'
import React, { useState } from 'react'
import { ScrollToBottomButton } from '@/components/chat/ScrollToBottomButton'

// ── A2: parent-context shell simulating the V2Thread scroll viewport ──────────

function ScrollViewportShell({
  isAtBottom,
  unreadCount,
  onScrollToBottom,
}: {
  isAtBottom: boolean
  unreadCount: number
  onScrollToBottom: () => void
}) {
  return (
    <div
      data-testid="v2-thread-viewport"
      style={{ height: 400, overflow: 'auto', position: 'relative' }}
    >
      <div style={{ height: 2000 }}>message content</div>
      {/* sentinel would be here in production */}
      <ScrollToBottomButton
        visible={!isAtBottom}
        unreadCount={unreadCount}
        onClick={onScrollToBottom}
      />
    </div>
  )
}

// ── ScrollToBottomButton tests ────────────────────────────────────────────────

describe('ScrollToBottomButton — parent-context integration (Amendment 2)', () => {
  it('is hidden when isAtBottom=true (visible=false)', () => {
    const { container } = render(
      <ScrollViewportShell isAtBottom={true} unreadCount={0} onScrollToBottom={vi.fn()} />,
    )
    const btn = container.querySelector('[data-testid="v2-scroll-to-bottom-discipline"]')
    expect(btn).not.toBeNull()
    expect(btn?.className).toMatch(/opacity-0/)
  })

  it('is visible when user scrolled away (visible=true)', () => {
    const { container } = render(
      <ScrollViewportShell isAtBottom={false} unreadCount={0} onScrollToBottom={vi.fn()} />,
    )
    const btn = container.querySelector('[data-testid="v2-scroll-to-bottom-discipline"]')
    expect(btn?.className).toMatch(/opacity-100/)
  })

  it('shows unread count badge when unreadCount > 0', () => {
    const { container } = render(
      <ScrollViewportShell isAtBottom={false} unreadCount={3} onScrollToBottom={vi.fn()} />,
    )
    const badge = container.querySelector('[data-testid="v2-unread-count"]')
    expect(badge).not.toBeNull()
    expect(badge?.textContent).toContain('3')
  })

  it('does NOT show unread count badge when unreadCount is 0', () => {
    const { container } = render(
      <ScrollViewportShell isAtBottom={false} unreadCount={0} onScrollToBottom={vi.fn()} />,
    )
    const badge = container.querySelector('[data-testid="v2-unread-count"]')
    expect(badge).toBeNull()
  })

  it('transitions from hidden to visible when user scrolls away', () => {
    let setAtBottom!: (v: boolean) => void
    function ToggleShell() {
      const [atBottom, setAB] = useState(true)
      setAtBottom = setAB
      return <ScrollViewportShell isAtBottom={atBottom} unreadCount={0} onScrollToBottom={vi.fn()} />
    }
    const { container } = render(<ToggleShell />)
    let btn = container.querySelector('[data-testid="v2-scroll-to-bottom-discipline"]')
    expect(btn?.className).toMatch(/opacity-0/)

    act(() => { setAtBottom(false) })
    btn = container.querySelector('[data-testid="v2-scroll-to-bottom-discipline"]')
    expect(btn?.className).toMatch(/opacity-100/)
  })

  it('calls onScrollToBottom when button clicked', () => {
    const onScrollToBottom = vi.fn()
    const { container } = render(
      <ScrollViewportShell isAtBottom={false} unreadCount={2} onScrollToBottom={onScrollToBottom} />,
    )
    const btn = container.querySelector('[data-testid="v2-scroll-to-bottom-discipline"]') as HTMLButtonElement
    btn.click()
    expect(onScrollToBottom).toHaveBeenCalledOnce()
  })

  it('aria-label reflects unread count', () => {
    const { container } = render(
      <ScrollToBottomButton visible={true} onClick={vi.fn()} unreadCount={5} />,
    )
    const btn = container.querySelector('[data-testid="v2-scroll-to-bottom-discipline"]')
    expect(btn?.getAttribute('aria-label')).toContain('5 new')
  })

  it('aria-label is generic when unreadCount is 0', () => {
    const { container } = render(
      <ScrollToBottomButton visible={true} onClick={vi.fn()} unreadCount={0} />,
    )
    const btn = container.querySelector('[data-testid="v2-scroll-to-bottom-discipline"]')
    expect(btn?.getAttribute('aria-label')).toBe('Jump to latest')
  })
})
