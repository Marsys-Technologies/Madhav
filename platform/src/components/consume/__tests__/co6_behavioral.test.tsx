/**
 * CO.6 Behavioral Polish Tests
 * Covers: useKeyboardShortcuts, useScrollAnchor, a11y attrs, mobile viewport
 * AC.CO6.1 – AC.CO6.7 + AC.CO6.9 (≥25 tests)
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act, render, screen } from '@testing-library/react'
import { fireEvent } from '@testing-library/dom'
import { useKeyboardShortcuts } from '@/lib/hooks/useKeyboardShortcuts'

// ── Mocks ──────────────────────────────────────────────────────────────────────

vi.mock('@/lib/utils', () => ({
  cn: (...args: unknown[]) => args.filter(Boolean).join(' '),
}))

vi.mock('@/lib/models/registry', () => ({
  getModelMeta: (id: string) => {
    if (id === 'gemini-2.5-pro') {
      return { id: 'gemini-2.5-pro', label: 'Gemini 2.5 Pro', provider: 'google', quirks: { reasoning_via: 'native' } }
    }
    return null
  },
  PROVIDER_LABEL: {
    google: 'Google',
    anthropic: 'Anthropic',
    openai: 'OpenAI',
    deepseek: 'DeepSeek',
    nim: 'NIM',
  },
}))

// ── useKeyboardShortcuts — AC.CO6.3 ───────────────────────────────────────────

describe('useKeyboardShortcuts — Cmd/Ctrl bindings', () => {
  it('Cmd+K fires onCompose', () => {
    const onCompose = vi.fn()
    renderHook(() => useKeyboardShortcuts({ onCompose }))
    fireEvent.keyDown(window, { key: 'k', metaKey: true })
    expect(onCompose).toHaveBeenCalledTimes(1)
  })

  it('Ctrl+K fires onCompose (Windows/Linux)', () => {
    const onCompose = vi.fn()
    renderHook(() => useKeyboardShortcuts({ onCompose }))
    fireEvent.keyDown(window, { key: 'k', ctrlKey: true })
    expect(onCompose).toHaveBeenCalledTimes(1)
  })

  it('Cmd+/ fires onShortcutsHelp', () => {
    const onShortcutsHelp = vi.fn()
    renderHook(() => useKeyboardShortcuts({ onShortcutsHelp }))
    fireEvent.keyDown(window, { key: '/', metaKey: true })
    expect(onShortcutsHelp).toHaveBeenCalledTimes(1)
  })

  it('Cmd+Enter fires onSubmit', () => {
    const onSubmit = vi.fn()
    renderHook(() => useKeyboardShortcuts({ onSubmit }))
    fireEvent.keyDown(window, { key: 'Enter', metaKey: true })
    expect(onSubmit).toHaveBeenCalledTimes(1)
  })

  it('Cmd+Enter fires onSubmit even when a textarea is focused', () => {
    const onSubmit = vi.fn()
    renderHook(() => useKeyboardShortcuts({ onSubmit }))
    // Submit fires even from inside typing targets (composer submit behavior).
    // Fire on the textarea element itself — bubbles up to window listener.
    const textarea = document.createElement('textarea')
    document.body.appendChild(textarea)
    textarea.focus()
    fireEvent.keyDown(textarea, { key: 'Enter', metaKey: true })
    expect(onSubmit).toHaveBeenCalledTimes(1)
    document.body.removeChild(textarea)
  })

  it('Escape fires onEscape', () => {
    const onEscape = vi.fn()
    renderHook(() => useKeyboardShortcuts({ onEscape }))
    fireEvent.keyDown(window, { key: 'Escape' })
    expect(onEscape).toHaveBeenCalledTimes(1)
  })

  it('Cmd+B fires onToggleSidebar when not in typing target', () => {
    const onToggleSidebar = vi.fn()
    renderHook(() => useKeyboardShortcuts({ onToggleSidebar }))
    fireEvent.keyDown(window, { key: 'b', metaKey: true })
    expect(onToggleSidebar).toHaveBeenCalledTimes(1)
  })

  it('Cmd+Shift+O fires onNewChat', () => {
    const onNewChat = vi.fn()
    renderHook(() => useKeyboardShortcuts({ onNewChat }))
    fireEvent.keyDown(window, { key: 'o', metaKey: true, shiftKey: true })
    expect(onNewChat).toHaveBeenCalledTimes(1)
  })

  it('key without modifier does NOT fire any binding', () => {
    const onCompose = vi.fn()
    const onSubmit = vi.fn()
    renderHook(() => useKeyboardShortcuts({ onCompose, onSubmit }))
    fireEvent.keyDown(window, { key: 'k' })
    fireEvent.keyDown(window, { key: 'Enter' })
    expect(onCompose).not.toHaveBeenCalled()
    expect(onSubmit).not.toHaveBeenCalled()
  })

  it('unmount removes the keydown listener', () => {
    const onCompose = vi.fn()
    const { unmount } = renderHook(() => useKeyboardShortcuts({ onCompose }))
    unmount()
    fireEvent.keyDown(window, { key: 'k', metaKey: true })
    expect(onCompose).not.toHaveBeenCalled()
  })

  it('undefined binding does not throw when triggered', () => {
    // All bindings optional — none provided
    renderHook(() => useKeyboardShortcuts({}))
    expect(() => {
      fireEvent.keyDown(window, { key: 'k', metaKey: true })
      fireEvent.keyDown(window, { key: 'Escape' })
    }).not.toThrow()
  })

  it('Cmd+K is case-insensitive (capital K)', () => {
    const onCompose = vi.fn()
    renderHook(() => useKeyboardShortcuts({ onCompose }))
    fireEvent.keyDown(window, { key: 'K', metaKey: true })
    expect(onCompose).toHaveBeenCalledTimes(1)
  })
})

// ── A11y assertions — AC.CO6.2 / AC.CO6.6 ────────────────────────────────────

import { StatusPip } from '../lifecycle/StatusPip'
import { ReasoningSlot } from '../lifecycle/ReasoningSlot'
import { MetadataBadge } from '../lifecycle/MetadataBadge'
import { FinalAnswerSlot } from '../lifecycle/FinalAnswerSlot'
import { ToolCallChronology } from '../lifecycle/ToolCallChronology'
import type { ToolCallRecord } from '@/lib/hooks/useChatLifecycle'

describe('StatusPip — a11y', () => {
  // AC.CO6.2: aria-live polite for status transitions
  it('has aria-live="polite" when streaming', () => {
    const { container } = render(<StatusPip state="composing" />)
    const region = container.querySelector('[aria-live]')
    expect(region).not.toBeNull()
    expect(region?.getAttribute('aria-live')).toBe('polite')
  })

  it('has aria-atomic="true"', () => {
    const { container } = render(<StatusPip state="reasoning" />)
    const region = container.querySelector('[aria-atomic]')
    expect(region).not.toBeNull()
    expect(region?.getAttribute('aria-atomic')).toBe('true')
  })

  it('renders null for idle state (no false positive announcement)', () => {
    const { container } = render(<StatusPip state="idle" />)
    expect(container.firstChild).toBeNull()
  })

  it('renders null for complete state', () => {
    const { container } = render(<StatusPip state="complete" />)
    expect(container.firstChild).toBeNull()
  })
})

describe('ReasoningSlot — a11y', () => {
  it('toggle button has aria-expanded attribute', () => {
    render(
      <ReasoningSlot
        state="complete"
        reasoningText="some thoughts"
        modelId="gemini-2.5-pro"
      />,
    )
    const button = screen.queryByRole('button')
    expect(button).not.toBeNull()
    expect(button?.hasAttribute('aria-expanded')).toBe(true)
  })

  it('gold dot indicator has aria-hidden="true" (decorative)', () => {
    const { container } = render(
      <ReasoningSlot
        state="complete"
        reasoningText="thoughts"
        modelId="gemini-2.5-pro"
      />,
    )
    const hidden = container.querySelector('[aria-hidden="true"]')
    expect(hidden).not.toBeNull()
  })
})

describe('MetadataBadge — a11y', () => {
  it('expand button has aria-label describing its action', () => {
    render(
      <MetadataBadge
        modelMeta={{ modelId: 'gemini-2.5-pro', latencyMs: 1200 }}
      />,
    )
    const button = screen.queryByRole('button')
    expect(button).not.toBeNull()
    expect(button?.getAttribute('aria-label')).toBeTruthy()
  })

  it('expand button has aria-expanded attribute', () => {
    render(
      <MetadataBadge
        modelMeta={{ modelId: 'gemini-2.5-pro', latencyMs: 1200 }}
      />,
    )
    const button = screen.queryByRole('button')
    expect(button?.hasAttribute('aria-expanded')).toBe(true)
  })
})

describe('FinalAnswerSlot — a11y', () => {
  it('renders semantic paragraph elements for prose', () => {
    const { container } = render(
      <FinalAnswerSlot state="complete" finalText="Hello world" />,
    )
    expect(container.querySelector('p, .prose')).not.toBeNull()
  })
})

describe('ToolCallChronology — a11y', () => {
  const calls: ToolCallRecord[] = [
    { callId: 'tc1', name: 'search_web', args: {}, result: 'done', ts: Date.now() },
  ]

  it('outer collapse button has aria-expanded and aria-controls', () => {
    const { container } = render(<ToolCallChronology state="complete" toolCalls={calls} />)
    // The outer collapse button links to the tool-call-list via aria-controls
    const button = container.querySelector('[aria-controls="tool-call-list"]')
    expect(button).not.toBeNull()
    expect(button?.hasAttribute('aria-expanded')).toBe(true)
  })

  it('renders semantic list structure for tool calls', () => {
    const { container } = render(
      <ToolCallChronology state="complete" toolCalls={calls} />,
    )
    // ul > li structure or similar list semantics
    expect(container.querySelector('ul, ol, [role="list"]')).not.toBeNull()
  })
})

// ── useScrollAnchor re-export — AC.CO6.1 ──────────────────────────────────────

describe('useScrollAnchor lib/hooks re-export — AC.CO6.1', () => {
  it('re-exports useScrollAnchor from @/hooks/useScrollAnchor', async () => {
    const mod = await import('@/lib/hooks/useScrollAnchor')
    expect(typeof mod.useScrollAnchor).toBe('function')
  })

  it('hook returns scrollRef, isAtBottom and scrollToBottom', async () => {
    const { useScrollAnchor } = await import('@/lib/hooks/useScrollAnchor')
    const { result } = renderHook(() => useScrollAnchor())
    expect(result.current).toHaveProperty('scrollRef')
    expect(result.current).toHaveProperty('isAtBottom')
    expect(result.current).toHaveProperty('scrollToBottom')
    expect(typeof result.current.scrollToBottom).toBe('function')
  })

  it('isAtBottom starts true (default pin-to-bottom on mount)', async () => {
    const { useScrollAnchor } = await import('@/lib/hooks/useScrollAnchor')
    const { result } = renderHook(() => useScrollAnchor())
    expect(result.current.isAtBottom).toBe(true)
  })

  it('scrollToBottom does not throw when ref is unattached', async () => {
    const { useScrollAnchor } = await import('@/lib/hooks/useScrollAnchor')
    const { result } = renderHook(() => useScrollAnchor())
    expect(() => act(() => { result.current.scrollToBottom() })).not.toThrow()
  })

  it('custom thresholdPx is accepted without error', async () => {
    const { useScrollAnchor } = await import('@/lib/hooks/useScrollAnchor')
    const { result } = renderHook(() => useScrollAnchor({ thresholdPx: 200 }))
    expect(result.current.isAtBottom).toBe(true)
  })
})

// ── CO6_A11Y_AUDIT file guard — AC.CO6.5 ────────────────────────────────────

import * as fs from 'node:fs'
import * as path from 'node:path'

describe('CO6_A11Y_AUDIT.md file guard — AC.CO6.5', () => {
  const auditPath = path.resolve(
    __dirname,
    '../../../../../00_ARCHITECTURE/aiops/phase_3/CO6_A11Y_AUDIT.md',
  )

  it('CO6_A11Y_AUDIT.md exists', () => {
    expect(fs.existsSync(auditPath)).toBe(true)
  })

  it('CO6_A11Y_AUDIT.md contains OUTSTANDING: 0 (no blocking defects)', () => {
    const content = fs.readFileSync(auditPath, 'utf-8')
    // Must have at least one OUTSTANDING: 0 line (audit clean)
    expect(content).toMatch(/OUTSTANDING:\s*0/)
  })

  it('CO6_A11Y_AUDIT.md does not contain OUTSTANDING: [1-9]', () => {
    const content = fs.readFileSync(auditPath, 'utf-8')
    expect(content).not.toMatch(/OUTSTANDING:\s*[1-9]/)
  })
})
