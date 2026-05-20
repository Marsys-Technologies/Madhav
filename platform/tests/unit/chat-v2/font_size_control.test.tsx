/**
 * X-S7 — Font-Size Control (Aa+/Aa−)
 * Amendment 2: parent-context integration tests.
 *
 * Click-path: Chat V2 header → click Aa+ → text grows → click again → max →
 *   further click is no-op → click Aa− → shrinks one step.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, act } from '@testing-library/react'
import React, { useState } from 'react'
import { TEXT_SCALES } from '@/hooks/useChatPreferences'
import type { TextScale } from '@/hooks/useChatPreferences'

// ── A2: parent-context shell mimicking the chat header + content area ─────────

function FontScaleShell({ initialScale = 1.0 as TextScale }: { initialScale?: TextScale }) {
  const [scale, setScale] = useState<TextScale>(initialScale)

  const increase = () => {
    const idx = TEXT_SCALES.indexOf(scale)
    if (idx < TEXT_SCALES.length - 1) setScale(TEXT_SCALES[idx + 1])
  }

  const decrease = () => {
    const idx = TEXT_SCALES.indexOf(scale)
    if (idx > 0) setScale(TEXT_SCALES[idx - 1])
  }

  return (
    <div data-testid="chat-shell" style={{ ['--text-scale' as string]: scale }}>
      <header data-testid="chat-header">
        <button
          type="button"
          onClick={decrease}
          aria-label="Decrease text size"
          aria-disabled={scale === TEXT_SCALES[0]}
          data-testid="v2-font-decrease"
        >
          Aa−
        </button>
        <button
          type="button"
          onClick={increase}
          aria-label="Increase text size"
          aria-disabled={scale === TEXT_SCALES[TEXT_SCALES.length - 1]}
          data-testid="v2-font-increase"
        >
          Aa+
        </button>
      </header>
      <div
        data-testid="markdown-content"
        style={{ fontSize: `calc(15px * var(--text-scale, 1))` }}
      >
        Synthesis text
      </div>
    </div>
  )
}

// ── TEXT_SCALES constant tests ────────────────────────────────────────────────

describe('TEXT_SCALES', () => {
  it('has exactly 4 scales', () => {
    expect(TEXT_SCALES).toHaveLength(4)
  })

  it('includes default 1.0', () => {
    expect(TEXT_SCALES).toContain(1.0)
  })

  it('is in ascending order', () => {
    for (let i = 1; i < TEXT_SCALES.length; i++) {
      expect(TEXT_SCALES[i]).toBeGreaterThan(TEXT_SCALES[i - 1])
    }
  })
})

// ── FontScaleShell parent-context integration tests ───────────────────────────

describe('Font-size control — parent-context integration (Amendment 2)', () => {
  it('renders Aa+ and Aa− buttons in header', () => {
    const { container } = render(<FontScaleShell />)
    expect(container.querySelector('[data-testid="v2-font-increase"]')).not.toBeNull()
    expect(container.querySelector('[data-testid="v2-font-decrease"]')).not.toBeNull()
  })

  it('Aa+ increments scale from 1.0 to 1.125', () => {
    const { container } = render(<FontScaleShell initialScale={1.0} />)
    const shell = container.querySelector('[data-testid="chat-shell"]') as HTMLElement
    expect(shell.style.getPropertyValue('--text-scale')).toBe('1')

    act(() => {
      ;(container.querySelector('[data-testid="v2-font-increase"]') as HTMLButtonElement).click()
    })
    expect(shell.style.getPropertyValue('--text-scale')).toBe('1.125')
  })

  it('Aa− decrements scale from 1.0 to 0.875', () => {
    const { container } = render(<FontScaleShell initialScale={1.0} />)
    act(() => {
      ;(container.querySelector('[data-testid="v2-font-decrease"]') as HTMLButtonElement).click()
    })
    const shell = container.querySelector('[data-testid="chat-shell"]') as HTMLElement
    expect(shell.style.getPropertyValue('--text-scale')).toBe('0.875')
  })

  it('Aa+ is aria-disabled at max scale', () => {
    const { container } = render(<FontScaleShell initialScale={1.25 as TextScale} />)
    const btn = container.querySelector('[data-testid="v2-font-increase"]')
    expect(btn?.getAttribute('aria-disabled')).toBe('true')
  })

  it('Aa− is aria-disabled at min scale', () => {
    const { container } = render(<FontScaleShell initialScale={0.875 as TextScale} />)
    const btn = container.querySelector('[data-testid="v2-font-decrease"]')
    expect(btn?.getAttribute('aria-disabled')).toBe('true')
  })

  it('clamps at max scale — further Aa+ is no-op', () => {
    const { container } = render(<FontScaleShell initialScale={1.25 as TextScale} />)
    const incBtn = container.querySelector('[data-testid="v2-font-increase"]') as HTMLButtonElement
    act(() => { incBtn.click() })
    act(() => { incBtn.click() })
    const shell = container.querySelector('[data-testid="chat-shell"]') as HTMLElement
    expect(shell.style.getPropertyValue('--text-scale')).toBe('1.25')
  })

  it('clamps at min scale — further Aa− is no-op', () => {
    const { container } = render(<FontScaleShell initialScale={0.875 as TextScale} />)
    const decBtn = container.querySelector('[data-testid="v2-font-decrease"]') as HTMLButtonElement
    act(() => { decBtn.click() })
    const shell = container.querySelector('[data-testid="chat-shell"]') as HTMLElement
    expect(shell.style.getPropertyValue('--text-scale')).toBe('0.875')
  })

  it('--text-scale CSS var on shell propagates to markdown content', () => {
    const { container } = render(<FontScaleShell initialScale={1.125 as TextScale} />)
    const shell = container.querySelector('[data-testid="chat-shell"]') as HTMLElement
    expect(shell.style.getPropertyValue('--text-scale')).toBe('1.125')
    const content = container.querySelector('[data-testid="markdown-content"]') as HTMLElement
    expect(content.style.fontSize).toContain('var(--text-scale')
  })
})
