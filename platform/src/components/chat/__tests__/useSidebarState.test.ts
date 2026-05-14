import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useSidebarState } from '@/lib/hooks/useSidebarState'

// ── localStorage mock ──────────────────────────────────────────────────────────

const store: Record<string, string> = {}
const localStorageMock = {
  getItem: (k: string) => store[k] ?? null,
  setItem: (k: string, v: string) => { store[k] = v },
  removeItem: (k: string) => { delete store[k] },
  clear: () => { Object.keys(store).forEach(k => delete store[k]) },
}

beforeEach(() => {
  Object.assign(global, { localStorage: localStorageMock })
  localStorageMock.clear()
  // Default to desktop viewport
  Object.defineProperty(window, 'innerWidth', { value: 1024, writable: true })
  // Stub matchMedia to desktop
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: (query: string) => ({
      matches: query.includes('639') ? false : false,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    }),
  })
})

afterEach(() => {
  vi.restoreAllMocks()
})

// ── Desktop state machine ──────────────────────────────────────────────────────

describe('useSidebarState — desktop state machine', () => {
  // AC.CO4.2: hover transitions work at ≥640px
  it('starts in collapsed state on desktop', () => {
    const { result } = renderHook(() => useSidebarState())
    expect(result.current.state).toBe('collapsed')
  })

  it('collapsed + mouseEnter → hover-expanded', () => {
    const { result } = renderHook(() => useSidebarState())
    expect(result.current.state).toBe('collapsed')
    act(() => { result.current.onMouseEnter() })
    expect(result.current.state).toBe('hover-expanded')
  })

  it('hover-expanded + mouseLeave → collapsed', () => {
    const { result } = renderHook(() => useSidebarState())
    act(() => { result.current.onMouseEnter() })
    act(() => { result.current.onMouseLeave() })
    expect(result.current.state).toBe('collapsed')
  })

  it('collapsed + pinToggle → pinned-expanded', () => {
    const { result } = renderHook(() => useSidebarState())
    act(() => { result.current.onPinToggle() })
    expect(result.current.state).toBe('pinned-expanded')
  })

  it('pinned-expanded + pinToggle → collapsed', () => {
    const { result } = renderHook(() => useSidebarState())
    act(() => { result.current.onPinToggle() })
    act(() => { result.current.onPinToggle() })
    expect(result.current.state).toBe('collapsed')
  })

  it('hover-expanded + pinToggle → pinned-expanded', () => {
    const { result } = renderHook(() => useSidebarState())
    act(() => { result.current.onMouseEnter() })
    act(() => { result.current.onPinToggle() })
    expect(result.current.state).toBe('pinned-expanded')
  })

  it('pinned-expanded + mouseLeave does NOT collapse', () => {
    const { result } = renderHook(() => useSidebarState())
    act(() => { result.current.onPinToggle() })
    act(() => { result.current.onMouseLeave() })
    expect(result.current.state).toBe('pinned-expanded')
  })

  // isExpanded derived state
  it('isExpanded is false for collapsed state', () => {
    const { result } = renderHook(() => useSidebarState())
    expect(result.current.isExpanded).toBe(false)
  })

  it('isExpanded is true for hover-expanded state', () => {
    const { result } = renderHook(() => useSidebarState())
    act(() => { result.current.onMouseEnter() })
    expect(result.current.isExpanded).toBe(true)
  })

  it('isExpanded is true for pinned-expanded state', () => {
    const { result } = renderHook(() => useSidebarState())
    act(() => { result.current.onPinToggle() })
    expect(result.current.isExpanded).toBe(true)
  })
})

// ── Pin persistence (AC.CO4.3) ────────────────────────────────────────────────

describe('useSidebarState — pin persistence via localStorage', () => {
  it('writes pin=true to localStorage when pinning', () => {
    const { result } = renderHook(() => useSidebarState())
    act(() => { result.current.onPinToggle() })
    expect(localStorageMock.getItem('marsys.consume.sidebar.pinned')).toBe('true')
  })

  it('writes pin=false to localStorage when unpinning', () => {
    const { result } = renderHook(() => useSidebarState())
    act(() => { result.current.onPinToggle() })
    act(() => { result.current.onPinToggle() })
    expect(localStorageMock.getItem('marsys.consume.sidebar.pinned')).toBe('false')
  })

  it('restores pinned-expanded state from localStorage on mount', () => {
    localStorageMock.setItem('marsys.consume.sidebar.pinned', 'true')
    const { result } = renderHook(() => useSidebarState())
    expect(result.current.state).toBe('pinned-expanded')
  })

  it('starts collapsed when localStorage pin is false', () => {
    localStorageMock.setItem('marsys.consume.sidebar.pinned', 'false')
    const { result } = renderHook(() => useSidebarState())
    expect(result.current.state).toBe('collapsed')
  })
})

// ── Mobile (AC.CO4.4) ─────────────────────────────────────────────────────────

describe('useSidebarState — mobile state', () => {
  beforeEach(() => {
    Object.defineProperty(window, 'innerWidth', { value: 375, writable: true })
    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      value: (query: string) => ({
        matches: query.includes('639'),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
      }),
    })
  })

  it('starts in mobile-closed state on mobile viewport', () => {
    const { result } = renderHook(() => useSidebarState())
    expect(result.current.state).toBe('mobile-closed')
  })

  it('mobile-closed + mobileToggle → mobile-open', () => {
    const { result } = renderHook(() => useSidebarState())
    act(() => { result.current.onMobileToggle() })
    expect(result.current.state).toBe('mobile-open')
  })

  it('mobile-open + mobileToggle → mobile-closed', () => {
    const { result } = renderHook(() => useSidebarState())
    act(() => { result.current.onMobileToggle() })
    act(() => { result.current.onMobileToggle() })
    expect(result.current.state).toBe('mobile-closed')
  })

  it('mouseEnter ignored on mobile', () => {
    const { result } = renderHook(() => useSidebarState())
    act(() => { result.current.onMouseEnter() })
    expect(result.current.state).toBe('mobile-closed')
  })
})
