/**
 * X-S2 — Recall Last Prompt (ArrowUp in empty composer)
 * Amendment 2: parent-context test (useLastPrompt with real localStorage).
 *
 * Click-path: Chat V2 → send a message → clear composer → press ArrowUp →
 *   previous message text appears in the composer.
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useLastPrompt } from '@/hooks/useChatPreferences'

// ── localStorage mock ─────────────────────────────────────────────────────────
// jsdom provides a functional localStorage in the test environment.

const CONV_ID = 'conv-test-abc-123'
const KEY = `marsys_chat_v2_last_prompt_${CONV_ID}`
const KEY_NULL = 'marsys_chat_v2_last_prompt___new__'

beforeEach(() => {
  localStorage.clear()
  vi.restoreAllMocks()
})

// ── useLastPrompt hook tests ──────────────────────────────────────────────────

describe('useLastPrompt — per-conversation localStorage cache', () => {
  it('returns empty string when no prior prompt saved', () => {
    const { result } = renderHook(() => useLastPrompt(CONV_ID))
    const [lastPrompt] = result.current
    expect(lastPrompt).toBe('')
  })

  it('saveLastPrompt persists to localStorage', () => {
    const { result } = renderHook(() => useLastPrompt(CONV_ID))
    act(() => {
      result.current[1]('What is the dasha period?')
    })
    expect(localStorage.getItem(KEY)).toBe('What is the dasha period?')
  })

  it('saveLastPrompt updates the returned lastPrompt', () => {
    const { result } = renderHook(() => useLastPrompt(CONV_ID))
    act(() => {
      result.current[1]('Tell me about Saturn')
    })
    expect(result.current[0]).toBe('Tell me about Saturn')
  })

  it('ignores empty or whitespace-only strings (empty guard)', () => {
    const { result } = renderHook(() => useLastPrompt(CONV_ID))
    act(() => {
      result.current[1]('First message')
    })
    act(() => {
      result.current[1]('')         // should not overwrite
      result.current[1]('   ')     // whitespace only — should not overwrite
    })
    expect(result.current[0]).toBe('First message')
    expect(localStorage.getItem(KEY)).toBe('First message')
  })

  it('restores from localStorage on mount (page refresh simulation)', () => {
    // Pre-populate localStorage
    localStorage.setItem(KEY, 'Restored from previous session')
    const { result } = renderHook(() => useLastPrompt(CONV_ID))
    expect(result.current[0]).toBe('Restored from previous session')
  })

  it('keys are per-conversation — different conversationId does not cross-bleed', () => {
    const { result: r1 } = renderHook(() => useLastPrompt('conv-A'))
    const { result: r2 } = renderHook(() => useLastPrompt('conv-B'))

    act(() => { r1.current[1]('Message for A') })
    act(() => { r2.current[1]('Message for B') })

    expect(r1.current[0]).toBe('Message for A')
    expect(r2.current[0]).toBe('Message for B')
    expect(r1.current[0]).not.toBe(r2.current[0])
  })

  it('null conversationId uses __new__ key (first turn before conversation created)', () => {
    const { result } = renderHook(() => useLastPrompt(null))
    act(() => {
      result.current[1]('First ever message')
    })
    expect(localStorage.getItem(KEY_NULL)).toBe('First ever message')
  })

  it('switches localStorage key when conversationId changes', () => {
    const { result, rerender } = renderHook(
      ({ cid }: { cid: string | null }) => useLastPrompt(cid),
      { initialProps: { cid: 'conv-X' } }
    )
    act(() => { result.current[1]('Message X') })
    expect(result.current[0]).toBe('Message X')

    // Switch to different conversation
    localStorage.setItem('marsys_chat_v2_last_prompt_conv-Y', 'Message Y')
    rerender({ cid: 'conv-Y' })
    expect(result.current[0]).toBe('Message Y')
  })
})
