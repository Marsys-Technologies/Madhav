/**
 * X-S3 — Citation Star Persistence
 * Tests useStarredCitations hook with parent-context (localStorage).
 *
 * Click-path: Chat V2 → receive response with citations → open citation panel →
 *   click star on a citation → refresh page → reopen panel → star is still active.
 */
import { describe, it, expect, beforeEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useStarredCitations } from '@/hooks/useStarredCitations'

const CONV_ID = 'conv-x-s3-test'
const KEY = `marsys_chat_v2_starred_${CONV_ID}`
const KEY_NULL = 'marsys_chat_v2_starred___new__'

beforeEach(() => {
  localStorage.clear()
})

describe('useStarredCitations — localStorage persistence', () => {
  it('returns empty Set when no citations starred', () => {
    const { result } = renderHook(() => useStarredCitations(CONV_ID))
    expect(result.current[0].size).toBe(0)
  })

  it('toggleStar adds a citation index to the starred set', () => {
    const { result } = renderHook(() => useStarredCitations(CONV_ID))
    act(() => { result.current[1](3) })
    expect(result.current[0].has(3)).toBe(true)
  })

  it('toggleStar removes a citation index when already starred (toggle behavior)', () => {
    const { result } = renderHook(() => useStarredCitations(CONV_ID))
    act(() => { result.current[1](5) })
    act(() => { result.current[1](5) })
    expect(result.current[0].has(5)).toBe(false)
  })

  it('toggleStar persists to localStorage', () => {
    const { result } = renderHook(() => useStarredCitations(CONV_ID))
    act(() => { result.current[1](7) })
    const stored = JSON.parse(localStorage.getItem(KEY) ?? '[]') as number[]
    expect(stored).toContain(7)
  })

  it('restores starred set from localStorage on mount (refresh simulation)', () => {
    localStorage.setItem(KEY, JSON.stringify([2, 4, 6]))
    const { result } = renderHook(() => useStarredCitations(CONV_ID))
    expect(result.current[0].has(2)).toBe(true)
    expect(result.current[0].has(4)).toBe(true)
    expect(result.current[0].has(6)).toBe(true)
  })

  it('null conversationId uses __new__ key', () => {
    const { result } = renderHook(() => useStarredCitations(null))
    act(() => { result.current[1](1) })
    const stored = JSON.parse(localStorage.getItem(KEY_NULL) ?? '[]') as number[]
    expect(stored).toContain(1)
  })

  it('different conversationIds do not cross-bleed', () => {
    const { result: r1 } = renderHook(() => useStarredCitations('conv-A'))
    const { result: r2 } = renderHook(() => useStarredCitations('conv-B'))
    act(() => { r1.current[1](10) })
    expect(r1.current[0].has(10)).toBe(true)
    expect(r2.current[0].has(10)).toBe(false)
  })

  it('switches to new conversationId set when key changes', () => {
    localStorage.setItem('marsys_chat_v2_starred_conv-old', JSON.stringify([99]))
    localStorage.setItem('marsys_chat_v2_starred_conv-new', JSON.stringify([88]))

    const { result, rerender } = renderHook(
      ({ cid }: { cid: string | null }) => useStarredCitations(cid),
      { initialProps: { cid: 'conv-old' } }
    )
    expect(result.current[0].has(99)).toBe(true)

    rerender({ cid: 'conv-new' })
    expect(result.current[0].has(88)).toBe(true)
    expect(result.current[0].has(99)).toBe(false)
  })

  it('handles corrupted localStorage gracefully (no error)', () => {
    localStorage.setItem(KEY, 'not-valid-json{{{')
    expect(() => {
      renderHook(() => useStarredCitations(CONV_ID))
    }).not.toThrow()
  })

  it('un-starring removes index from localStorage', () => {
    const { result } = renderHook(() => useStarredCitations(CONV_ID))
    act(() => { result.current[1](3) })
    act(() => { result.current[1](3) }) // un-star
    const stored = JSON.parse(localStorage.getItem(KEY) ?? '[]') as number[]
    expect(stored).not.toContain(3)
  })
})
