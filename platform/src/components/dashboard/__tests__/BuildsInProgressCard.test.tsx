import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

// ── Mock ProgressBar (external build component) ────────────────────────────
vi.mock('@/components/build/ProgressBar', () => ({
  ProgressBar: ({ percent, tone }: { percent: number; tone?: string }) => (
    <div
      data-testid="progress-bar"
      data-percent={percent}
      data-tone={tone ?? 'default'}
      role="progressbar"
      aria-valuenow={percent}
    />
  ),
}))

// ── Import after mocks ─────────────────────────────────────────────────────
import BuildsInProgressCard, { type ActiveBuild } from '../BuildsInProgressCard'

// ── Helpers ────────────────────────────────────────────────────────────────
function mockFetch(response: ActiveBuild[] | null, ok = true) {
  global.fetch = vi.fn().mockResolvedValue({
    ok,
    json: async () => response ?? [],
  })
}

const FAKE_BUILD: ActiveBuild = {
  build_id: 'build-001',
  chart_id: 'chart-abc',
  chart_name: 'Arjuna Sharma',
  ayanamshas: ['lahiri', 'kp'],
  status: 'running',
  queued_at: new Date(Date.now() - 120_000).toISOString(),
  started_at: new Date(Date.now() - 90_000).toISOString(),
  steps_complete: 3,
  steps_total: 10,
  progress_pct: 30,
}

const QUEUED_BUILD: ActiveBuild = {
  ...FAKE_BUILD,
  build_id: 'build-002',
  chart_name: 'Priya Nair',
  status: 'queued',
  ayanamshas: ['raman', 'surya_siddhanta', 'true_chitra'],
  steps_complete: 0,
  steps_total: 10,
  progress_pct: 0,
}

const CANCELLING_BUILD: ActiveBuild = {
  ...FAKE_BUILD,
  build_id: 'build-003',
  chart_name: null, // Unknown chart test case
  status: 'cancelling',
  ayanamshas: [],
  steps_complete: 5,
  steps_total: 10,
  progress_pct: 50,
}

// ── Tests ──────────────────────────────────────────────────────────────────
describe('BuildsInProgressCard', () => {
  beforeEach(() => {
    // Use fake timers but keep async (Promise/microtask) resolution real.
    // Without this, vi.useFakeTimers() swallows the setInterval in the component
    // and also freezes waitFor's internal polling timeout.
    vi.useFakeTimers({ shouldAdvanceTime: true })
  })

  afterEach(() => {
    vi.restoreAllMocks()
    vi.useRealTimers()
  })

  // 1. Loading state while fetching
  it('shows loading state initially before fetch resolves', () => {
    global.fetch = vi.fn().mockReturnValue(new Promise(() => {})) // never resolves
    render(<BuildsInProgressCard />)
    expect(screen.getByTestId('builds-loading')).toBeTruthy()
  })

  // 2. Empty state when no builds
  it('shows empty state when API returns an empty array', async () => {
    mockFetch([])
    render(<BuildsInProgressCard />)
    await waitFor(() => {
      expect(screen.getByTestId('builds-empty')).toBeTruthy()
    })
    expect(screen.getByText('No builds running')).toBeTruthy()
  })

  // 3. Card renders with builds present
  it('renders the card with builds-in-progress-card testid', async () => {
    mockFetch([FAKE_BUILD])
    render(<BuildsInProgressCard />)
    await waitFor(() => {
      expect(screen.getByTestId('builds-in-progress-card')).toBeTruthy()
    })
  })

  // 4. Shows chart name for a running build
  it('displays chart name for an active build', async () => {
    mockFetch([FAKE_BUILD])
    render(<BuildsInProgressCard />)
    await waitFor(() => {
      expect(screen.getByTestId(`build-chart-name-${FAKE_BUILD.build_id}`)).toBeTruthy()
    })
    expect(screen.getByText('Arjuna Sharma')).toBeTruthy()
  })

  // 5. Falls back to "Unknown chart" when chart_name is null
  it('shows "Unknown chart" when chart_name is null', async () => {
    mockFetch([CANCELLING_BUILD])
    render(<BuildsInProgressCard />)
    await waitFor(() => {
      expect(screen.getByText('Unknown chart')).toBeTruthy()
    })
  })

  // 6. Status badge is displayed with correct text
  it('renders status badge for running build', async () => {
    mockFetch([FAKE_BUILD])
    render(<BuildsInProgressCard />)
    await waitFor(() => {
      expect(screen.getByTestId(`build-status-${FAKE_BUILD.build_id}`)).toBeTruthy()
    })
    expect(screen.getByTestId(`build-status-${FAKE_BUILD.build_id}`).textContent).toBe('running')
  })

  // 7. Ayanamsha badges are rendered with short codes
  it('renders ayanamsha short-code badges', async () => {
    mockFetch([FAKE_BUILD])
    render(<BuildsInProgressCard />)
    await waitFor(() => {
      expect(screen.getByTestId(`build-ayanamshas-${FAKE_BUILD.build_id}`)).toBeTruthy()
    })
    const container = screen.getByTestId(`build-ayanamshas-${FAKE_BUILD.build_id}`)
    expect(container.textContent).toContain('L')   // lahiri
    expect(container.textContent).toContain('KP')  // kp
  })

  // 8. Multiple ayanamsha codes rendered for queued build
  it('renders multiple ayanamsha badges for queued build', async () => {
    mockFetch([QUEUED_BUILD])
    render(<BuildsInProgressCard />)
    await waitFor(() => {
      expect(screen.getByTestId(`build-ayanamshas-${QUEUED_BUILD.build_id}`)).toBeTruthy()
    })
    const container = screen.getByTestId(`build-ayanamshas-${QUEUED_BUILD.build_id}`)
    expect(container.textContent).toContain('R')   // raman
    expect(container.textContent).toContain('SS')  // surya_siddhanta
    expect(container.textContent).toContain('TC')  // true_chitra
  })

  // 9. Progress bar rendered with correct percent
  it('renders a progress bar with the correct percent value', async () => {
    mockFetch([FAKE_BUILD])
    render(<BuildsInProgressCard />)
    await waitFor(() => {
      expect(screen.getByRole('progressbar')).toBeTruthy()
    })
    expect(screen.getByRole('progressbar').getAttribute('aria-valuenow')).toBe('30')
  })

  // 10. Steps count shown correctly
  it('shows steps_complete/steps_total label', async () => {
    mockFetch([FAKE_BUILD])
    render(<BuildsInProgressCard />)
    await waitFor(() => {
      expect(screen.getByTestId(`build-steps-${FAKE_BUILD.build_id}`)).toBeTruthy()
    })
    expect(screen.getByTestId(`build-steps-${FAKE_BUILD.build_id}`).textContent).toContain('3/10')
  })

  // 11. Cancel button is visible for a running build
  it('renders cancel button for running build', async () => {
    mockFetch([FAKE_BUILD])
    render(<BuildsInProgressCard />)
    await waitFor(() => {
      expect(screen.getByTestId(`build-cancel-${FAKE_BUILD.build_id}`)).toBeTruthy()
    })
  })

  // 12. Cancel button is disabled for cancelling build
  it('cancel button is disabled when build status is cancelling', async () => {
    mockFetch([CANCELLING_BUILD])
    render(<BuildsInProgressCard />)
    await waitFor(() => {
      const btn = screen.getByTestId(`build-cancel-${CANCELLING_BUILD.build_id}`)
      expect((btn as HTMLButtonElement).disabled).toBe(true)
    })
  })

  // 13. Cancel button triggers confirmation dialog and calls API
  it('calls cancel API when cancel is confirmed', async () => {
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime.bind(vi) })
    mockFetch([FAKE_BUILD])
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true)
    render(<BuildsInProgressCard />)
    await waitFor(() => {
      expect(screen.getByTestId(`build-cancel-${FAKE_BUILD.build_id}`)).toBeTruthy()
    })
    await user.click(screen.getByTestId(`build-cancel-${FAKE_BUILD.build_id}`))
    expect(confirmSpy).toHaveBeenCalledWith('Cancel this build?')
    expect(global.fetch).toHaveBeenCalledWith(
      `/api/build/cancel/${FAKE_BUILD.build_id}`,
      { method: 'POST' }
    )
  })

  // 14. Build count badge shows number of active builds
  it('shows count badge with number of active builds', async () => {
    mockFetch([FAKE_BUILD, QUEUED_BUILD])
    render(<BuildsInProgressCard />)
    await waitFor(() => {
      expect(screen.getByTestId('builds-count')).toBeTruthy()
    })
    expect(screen.getByTestId('builds-count').textContent).toBe('2')
  })

  // 15. Polls every 5 seconds
  it('re-fetches after 5 second polling interval', async () => {
    mockFetch([FAKE_BUILD])
    render(<BuildsInProgressCard />)
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledTimes(1)
    })
    await act(async () => {
      vi.advanceTimersByTime(5000)
      await Promise.resolve()
    })
    expect((global.fetch as ReturnType<typeof vi.fn>).mock.calls.length).toBeGreaterThanOrEqual(2)
  })
})
