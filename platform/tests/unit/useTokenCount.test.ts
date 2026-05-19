import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useTokenCount } from '../../src/hooks/useTokenCount'

vi.mock('gpt-tokenizer', () => ({
  encode: (text: string) => text.split(' '),
}))

vi.mock('../../src/lib/models/registry', () => ({
  stackPicker: () => [
    {
      stack: 'default',
      label: 'Default',
      synthesisModelId: 'model-1',
      synthesisContextWindow: 128000,
      isDefault: true,
    },
  ],
}))

beforeEach(() => {
  vi.useFakeTimers()
})

afterEach(() => {
  vi.useRealTimers()
  vi.clearAllMocks()
})

describe('useTokenCount', () => {
  it('returns null tokenCount before tokenizer loads', () => {
    const { result } = renderHook(() => useTokenCount('hello world'))
    expect(result.current.tokenCount).toBeNull()
    expect(result.current.pctUsed).toBeNull()
  })

  it('returns correct contextWindowTokens from stackPicker', () => {
    const { result } = renderHook(() => useTokenCount(''))
    expect(result.current.contextWindowTokens).toBe(128000)
  })

  it('computes token count after module loads and 200ms debounce fires', async () => {
    const { result } = renderHook(() => useTokenCount('hello world'))

    // Resolve the dynamic import (sets encodeFn state)
    await act(async () => {
      await Promise.resolve()
    })

    // Advance timers past 200ms debounce
    act(() => {
      vi.advanceTimersByTime(200)
    })

    expect(result.current.tokenCount).toBe(2) // 'hello world' splits to 2 words
  })

  it('uses 500ms debounce for inputs longer than 50000 chars', async () => {
    const longInput = 'a '.repeat(25001) // > 50000 chars
    const { result } = renderHook(() => useTokenCount(longInput))

    await act(async () => {
      await Promise.resolve()
    })

    // Advance only 200ms — should NOT fire yet
    act(() => {
      vi.advanceTimersByTime(200)
    })
    expect(result.current.tokenCount).toBeNull()

    // Advance remaining 300ms (total 500ms) — should fire now
    act(() => {
      vi.advanceTimersByTime(300)
    })
    expect(result.current.tokenCount).not.toBeNull()
  })

  it('pctUsed is null when tokenCount is null', () => {
    const { result } = renderHook(() => useTokenCount('test'))
    expect(result.current.pctUsed).toBeNull()
  })
})
