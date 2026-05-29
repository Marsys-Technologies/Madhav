import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render } from '@testing-library/react'

// ── Mock sonner toast ──────────────────────────────────────────────────────
const mockToastSuccess = vi.fn()
const mockToastError = vi.fn()

vi.mock('sonner', () => ({
  toast: {
    success: mockToastSuccess,
    error: mockToastError,
  },
}))

// ── Import after mocks ─────────────────────────────────────────────────────
import BuildCompleteToast, { type RecentBuild } from '../BuildCompleteToast'

// ── Helpers ────────────────────────────────────────────────────────────────
const SEEN_KEY = 'marsys_seen_builds'

function mockFetch(response: RecentBuild[] | null, ok = true) {
  global.fetch = vi.fn().mockResolvedValue({
    ok,
    json: async () => response ?? [],
  })
}

function clearLocalStorage() {
  localStorage.removeItem(SEEN_KEY)
}

function setSeen(ids: string[]) {
  localStorage.setItem(SEEN_KEY, JSON.stringify(ids))
}

function getSeenIds(): string[] {
  try {
    return JSON.parse(localStorage.getItem(SEEN_KEY) ?? '[]') as string[]
  } catch {
    return []
  }
}

const COMPLETE_BUILD: RecentBuild = {
  build_id: 'build-001',
  chart_id: 'chart-abc',
  chart_name: 'Arjuna Sharma',
  status: 'complete',
  finished_at: new Date(Date.now() - 5_000).toISOString(),
  ayanamshas: ['lahiri', 'kp'],
  error_summary: null,
}

const FAILED_BUILD: RecentBuild = {
  build_id: 'build-002',
  chart_id: 'chart-xyz',
  chart_name: 'Priya Nair',
  status: 'failed',
  finished_at: new Date(Date.now() - 10_000).toISOString(),
  ayanamshas: ['raman'],
  error_summary: 'Ephemeris lookup timeout',
}

const NULL_NAME_BUILD: RecentBuild = {
  ...COMPLETE_BUILD,
  build_id: 'build-003',
  chart_name: null,
  ayanamshas: [],
}

// ── Tests ──────────────────────────────────────────────────────────────────
describe('BuildCompleteToast', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    clearLocalStorage()
    mockToastSuccess.mockClear()
    mockToastError.mockClear()
  })

  afterEach(() => {
    vi.restoreAllMocks()
    vi.useRealTimers()
    clearLocalStorage()
  })

  // 1. Component renders nothing (null output)
  it('renders nothing into the DOM', () => {
    mockFetch([])
    const { container } = render(<BuildCompleteToast />)
    expect(container.firstChild).toBeNull()
  })

  // 2. Does NOT show toast when API returns empty array
  it('does not fire any toast when no recent builds exist', async () => {
    mockFetch([])
    render(<BuildCompleteToast />)
    await vi.runAllTimersAsync()
    expect(mockToastSuccess).not.toHaveBeenCalled()
    expect(mockToastError).not.toHaveBeenCalled()
  })

  // 3. Shows success toast for an unseen completed build
  it('fires toast.success for an unseen completed build', async () => {
    mockFetch([COMPLETE_BUILD])
    render(<BuildCompleteToast />)
    await vi.runAllTimersAsync()
    expect(mockToastSuccess).toHaveBeenCalledOnce()
    const [message] = mockToastSuccess.mock.calls[0] as [string, unknown]
    expect(message).toContain('Arjuna Sharma')
    expect(message).toContain('build complete')
  })

  // 4. Shows error toast for an unseen failed build
  it('fires toast.error for an unseen failed build', async () => {
    mockFetch([FAILED_BUILD])
    render(<BuildCompleteToast />)
    await vi.runAllTimersAsync()
    expect(mockToastError).toHaveBeenCalledOnce()
    const [message] = mockToastError.mock.calls[0] as [string, unknown]
    expect(message).toContain('Priya Nair')
    expect(message).toContain('build failed')
  })

  // 5. Does NOT show toast for a build already in localStorage seen list
  it('suppresses toast for builds already marked as seen', async () => {
    setSeen([COMPLETE_BUILD.build_id])
    mockFetch([COMPLETE_BUILD])
    render(<BuildCompleteToast />)
    await vi.runAllTimersAsync()
    expect(mockToastSuccess).not.toHaveBeenCalled()
  })

  // 6. Marks unseen builds as seen in localStorage after showing
  it('persists shown build_ids to localStorage', async () => {
    mockFetch([COMPLETE_BUILD])
    render(<BuildCompleteToast />)
    await vi.runAllTimersAsync()
    const seen = getSeenIds()
    expect(seen).toContain(COMPLETE_BUILD.build_id)
  })

  // 7. Success toast message includes ayanamsha list
  it('includes ayanamsha names in the success toast message', async () => {
    mockFetch([COMPLETE_BUILD])
    render(<BuildCompleteToast />)
    await vi.runAllTimersAsync()
    const [message] = mockToastSuccess.mock.calls[0] as [string, unknown]
    expect(message).toContain('lahiri')
    expect(message).toContain('kp')
  })

  // 8. Uses "Chart" fallback when chart_name is null
  it('falls back to "Chart" label when chart_name is null', async () => {
    mockFetch([NULL_NAME_BUILD])
    render(<BuildCompleteToast />)
    await vi.runAllTimersAsync()
    expect(mockToastSuccess).toHaveBeenCalledOnce()
    const [message] = mockToastSuccess.mock.calls[0] as [string, unknown]
    expect(message).toContain('Chart')
    expect(message).toContain('build complete')
  })

  // 9. toast.success called with action containing View label
  it('provides a View action on the success toast', async () => {
    mockFetch([COMPLETE_BUILD])
    render(<BuildCompleteToast />)
    await vi.runAllTimersAsync()
    const [, options] = mockToastSuccess.mock.calls[0] as [
      string,
      { action?: { label: string } },
    ]
    expect(options?.action?.label).toBe('View')
  })

  // 10. toast.error called with action containing View label
  it('provides a View action on the error toast', async () => {
    mockFetch([FAILED_BUILD])
    render(<BuildCompleteToast />)
    await vi.runAllTimersAsync()
    const [, options] = mockToastError.mock.calls[0] as [
      string,
      { action?: { label: string } },
    ]
    expect(options?.action?.label).toBe('View')
  })

  // 11. toast.error carries error_summary as description
  it('passes error_summary as toast description for failed builds', async () => {
    mockFetch([FAILED_BUILD])
    render(<BuildCompleteToast />)
    await vi.runAllTimersAsync()
    const [, options] = mockToastError.mock.calls[0] as [
      string,
      { description?: string },
    ]
    expect(options?.description).toBe('Ephemeris lookup timeout')
  })

  // 12. Each build triggers its own individual toast call (multiple builds)
  it('fires one toast per unseen build when multiple are returned', async () => {
    mockFetch([COMPLETE_BUILD, FAILED_BUILD])
    render(<BuildCompleteToast />)
    await vi.runAllTimersAsync()
    expect(mockToastSuccess).toHaveBeenCalledOnce()
    expect(mockToastError).toHaveBeenCalledOnce()
  })

  // 13. Silently does nothing when fetch returns a non-ok response
  it('does not throw and fires no toast when API returns non-ok', async () => {
    mockFetch(null, false)
    expect(() => {
      render(<BuildCompleteToast />)
    }).not.toThrow()
    await vi.runAllTimersAsync()
    expect(mockToastSuccess).not.toHaveBeenCalled()
    expect(mockToastError).not.toHaveBeenCalled()
  })

  // 14. Silently does nothing when fetch throws a network error
  it('does not throw when fetch rejects (network error)', async () => {
    global.fetch = vi.fn().mockRejectedValue(new Error('Network failure'))
    expect(() => {
      render(<BuildCompleteToast />)
    }).not.toThrow()
    await vi.runAllTimersAsync()
    expect(mockToastSuccess).not.toHaveBeenCalled()
    expect(mockToastError).not.toHaveBeenCalled()
  })

  // 15. toast.success is called with the build_id as the toast id
  it('uses build_id as the sonner toast id to deduplicate', async () => {
    mockFetch([COMPLETE_BUILD])
    render(<BuildCompleteToast />)
    await vi.runAllTimersAsync()
    const [, options] = mockToastSuccess.mock.calls[0] as [
      string,
      { id?: string },
    ]
    expect(options?.id).toBe(COMPLETE_BUILD.build_id)
  })
})
