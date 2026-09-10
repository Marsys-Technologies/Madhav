/**
 * P2-F (PPR-19) §9.2: "composer pinned via `visualViewport` (never `100vh`
 * guesses)." Unit test for the hook itself (`useVisualViewport`) and an
 * integration check that `PariprashnaApp`'s shell actually consumes it —
 * with a fake `window.visualViewport` standing in for the real mobile
 * keyboard-open resize event jsdom cannot itself produce (no layout
 * engine), the same substitution the hook's own unsupported-browser
 * fallback path exists to handle honestly.
 */
import { afterEach, describe, expect, it } from 'vitest'
import { act, cleanup, render, renderHook } from '@testing-library/react'
import { useVisualViewport } from '@/components/pariprashna/hooks/useVisualViewport'
import { PariprashnaApp } from '@/components/pariprashna/PariprashnaApp'

type Listener = () => void

class FakeVisualViewport {
  height = 800
  offsetTop = 0
  private listeners: Record<string, Listener[]> = { resize: [], scroll: [] }
  addEventListener(type: string, fn: Listener) {
    this.listeners[type]?.push(fn)
  }
  removeEventListener(type: string, fn: Listener) {
    this.listeners[type] = (this.listeners[type] ?? []).filter((l) => l !== fn)
  }
  fire(type: string) {
    for (const fn of this.listeners[type] ?? []) fn()
  }
}

afterEach(() => {
  cleanup()
  // @ts-expect-error test-only teardown of a property jsdom doesn't define natively
  delete window.visualViewport
})

describe('useVisualViewport', () => {
  it('reports unsupported (null height) when window.visualViewport is absent — jsdom default', () => {
    const { result } = renderHook(() => useVisualViewport())
    expect(result.current.supported).toBe(false)
    expect(result.current.height).toBeNull()
  })

  it('tracks a fake visualViewport and reacts to a simulated keyboard-open resize', () => {
    const fake = new FakeVisualViewport()
    fake.height = 844 // full 390x844 viewport, keyboard closed
    // @ts-expect-error assigning the test double for the duration of this test
    window.visualViewport = fake

    const { result } = renderHook(() => useVisualViewport())
    expect(result.current.supported).toBe(true)
    expect(result.current.height).toBe(844)

    // Keyboard opens: the visual viewport shrinks (the layout viewport /
    // `100vh` would NOT shrink to match — the exact defect this hook exists
    // to route around).
    act(() => {
      fake.height = 420
      fake.fire('resize')
    })
    expect(result.current.height).toBe(420)
  })
})

describe('PariprashnaApp shell consumes the hook (not a static 100vh)', () => {
  it('falls back to 100dvh (never a bare 100vh) when visualViewport is unsupported', () => {
    const { container } = render(<PariprashnaApp chartPin={{ name: 'Test Native', bornLine: '05 Feb 1984' }} />)
    const shell = container.querySelector('.pp-root') as HTMLElement
    expect(shell).not.toBeNull()
    expect(shell.getAttribute('data-vh-source')).toBe('fallback')
    expect(shell.style.height).toBe('100dvh')
    expect(shell.style.height).not.toBe('100vh')
  })

  it('pins to the live visualViewport height when supported, and updates on keyboard-open resize', () => {
    const fake = new FakeVisualViewport()
    fake.height = 844
    // @ts-expect-error test double
    window.visualViewport = fake

    const { container } = render(<PariprashnaApp chartPin={{ name: 'Test Native', bornLine: '05 Feb 1984' }} />)
    const shell = container.querySelector('.pp-root') as HTMLElement
    expect(shell.getAttribute('data-vh-source')).toBe('visual-viewport')
    expect(shell.style.height).toBe('844px')

    act(() => {
      fake.height = 360 // keyboard open on a 390x844 device
      fake.fire('resize')
    })
    expect(shell.style.height).toBe('360px')
  })
})
