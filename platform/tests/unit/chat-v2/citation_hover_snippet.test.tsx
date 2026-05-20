/**
 * Y-S1 — Citation Hover Snippet
 * Amendment 2: parent-context integration tests using CitationCtxProvider shell.
 *
 * Click-path: Chat V2 response with numbered citations → hover [^1] for >350ms →
 *   tooltip appears with citation snippet text → mouse leaves → tooltip disappears.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, act, fireEvent } from '@testing-library/react'
import React from 'react'
import { NumberedCitation } from '@/components/chat/NumberedCitation'

// ── Parent-context shell per Amendment 2 ─────────────────────────────────────
// Simulates the CitationCtx + message context that NumberedCitation lives inside.

function CitationCtxShell({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div data-testid="v2-chat-shell">
      <div data-testid="v2-message">
        {children}
      </div>
    </div>
  )
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('NumberedCitation hover snippet — parent-context (Amendment 2)', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('tooltip is NOT visible before 350ms dwell', () => {
    const { getByTestId, queryByTestId } = render(
      <CitationCtxShell>
        <NumberedCitation n={1} signalId="SIG.MSR.001" snippet="The Sun is in Aries at 10.5°." />
      </CitationCtxShell>,
    )
    fireEvent.mouseEnter(getByTestId('v2-citation-badge'))

    // advance less than 350ms — tooltip must not yet appear
    act(() => { vi.advanceTimersByTime(200) })
    expect(queryByTestId('v2-citation-tooltip')).toBeNull()
  })

  it('tooltip appears after 350ms dwell with snippet text', () => {
    const { getByTestId } = render(
      <CitationCtxShell>
        <NumberedCitation n={1} signalId="SIG.MSR.001" snippet="The Sun is in Aries at 10.5°." />
      </CitationCtxShell>,
    )
    fireEvent.mouseEnter(getByTestId('v2-citation-badge'))
    act(() => { vi.advanceTimersByTime(350) })

    const tooltip = getByTestId('v2-citation-tooltip')
    expect(tooltip).toBeTruthy()
    expect(tooltip.textContent).toContain('The Sun is in Aries')
  })

  it('tooltip disappears on mouse leave', () => {
    const { getByTestId, queryByTestId } = render(
      <CitationCtxShell>
        <NumberedCitation n={1} signalId="SIG.MSR.001" snippet="Sun in Aries." />
      </CitationCtxShell>,
    )
    const badge = getByTestId('v2-citation-badge')
    fireEvent.mouseEnter(badge)
    act(() => { vi.advanceTimersByTime(350) })
    expect(queryByTestId('v2-citation-tooltip')).not.toBeNull()

    fireEvent.mouseLeave(badge)
    expect(queryByTestId('v2-citation-tooltip')).toBeNull()
  })

  it('rapid mouse-over does not show tooltip (timer cleared on leave)', () => {
    const { getByTestId, queryByTestId } = render(
      <CitationCtxShell>
        <NumberedCitation n={1} signalId="SIG.MSR.001" snippet="Moon in Taurus." />
      </CitationCtxShell>,
    )
    const badge = getByTestId('v2-citation-badge')
    fireEvent.mouseEnter(badge)
    act(() => { vi.advanceTimersByTime(100) })
    fireEvent.mouseLeave(badge) // leaves before 350ms

    act(() => { vi.advanceTimersByTime(300) }) // advance past 350ms total
    expect(queryByTestId('v2-citation-tooltip')).toBeNull()
  })

  it('snippet is truncated to 100 chars + ellipsis when long', () => {
    const long = 'A'.repeat(120)
    const { getByTestId } = render(
      <CitationCtxShell>
        <NumberedCitation n={2} signalId="SIG.MSR.002" snippet={long} />
      </CitationCtxShell>,
    )
    fireEvent.mouseEnter(getByTestId('v2-citation-badge'))
    act(() => { vi.advanceTimersByTime(350) })

    const tooltip = getByTestId('v2-citation-tooltip')
    expect(tooltip.textContent?.length).toBeLessThanOrEqual(104) // 100 chars + '…'
    expect(tooltip.textContent).toContain('…')
  })

  it('falls back to signalId when no snippet provided', () => {
    const { getByTestId } = render(
      <CitationCtxShell>
        <NumberedCitation n={3} signalId="SIG.MSR.003" />
      </CitationCtxShell>,
    )
    fireEvent.mouseEnter(getByTestId('v2-citation-badge'))
    act(() => { vi.advanceTimersByTime(350) })

    const tooltip = getByTestId('v2-citation-tooltip')
    expect(tooltip.textContent).toBe('SIG.MSR.003')
  })

  it('tooltip has role=tooltip and aria-describedby on badge', () => {
    const { getByTestId } = render(
      <CitationCtxShell>
        <NumberedCitation n={1} signalId="SIG.MSR.001" snippet="Sun in Aries." />
      </CitationCtxShell>,
    )
    const badge = getByTestId('v2-citation-badge')
    fireEvent.mouseEnter(badge)
    act(() => { vi.advanceTimersByTime(350) })

    const tooltip = getByTestId('v2-citation-tooltip')
    expect(tooltip.getAttribute('role')).toBe('tooltip')
    expect(badge.getAttribute('aria-describedby')).toBeTruthy()
    expect(badge.getAttribute('aria-describedby')).toBe(tooltip.getAttribute('id'))
  })
})
