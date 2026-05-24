/**
 * MuhuratFinderModal + MuhuratResultsList unit tests — AC.4C6S3.7
 *
 * Tests:
 *   - Modal renders with correct initial form state
 *   - Modal closes on backdrop click / X button
 *   - Form submit triggers useMuhuratFinder.search() with correct params
 *   - Personalise checkbox: disabled when no chartId; auto-checked when chartId present
 *   - Results list: renders windows sorted by score, star ratings, breakdown badges
 *   - Results list: loading skeleton state
 *   - Results list: error state
 *   - Results list: empty state (no windows)
 *   - Inline actions: Calendar Export disabled with 4C-7 hint
 *   - Inline actions: Ask-Madhav generates correct URL params
 *
 * Phase: 4C-6-S3 (Item 7)
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MuhuratFinderModal } from '../components/MuhuratFinderModal'
import { MuhuratResultsList } from '../components/MuhuratResultsList'
import type { MuhuratWindow } from '../hooks/useMuhuratFinder'

// ── Mocks ─────────────────────────────────────────────────────────────────────

const mockPush = vi.fn()
const mockSearchParams = new URLSearchParams('loc=bhubaneswar')

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush }),
  useSearchParams: () => mockSearchParams,
}))

// Stub useMuhuratFinder — return controllable state
const mockSearch = vi.fn()
let mockWindows: MuhuratWindow[] | null = null
let mockIsLoading = false
let mockError: string | null = null

vi.mock('../hooks/useMuhuratFinder', () => ({
  useMuhuratFinder: () => ({
    windows: mockWindows,
    isLoading: mockIsLoading,
    error: mockError,
    search: mockSearch,
  }),
}))

// ── Test fixtures ─────────────────────────────────────────────────────────────

const WINDOW_HIGH: MuhuratWindow = {
  event: 'vivah',
  start_utc: '2026-06-05T01:00:00Z',   // 06:30 IST
  end_utc:   '2026-06-05T12:30:00Z',   // 18:00 IST
  star_rating: 5,
  score: 3.85,
  breakdown: {
    tithi:    0.60,
    nakshatra: 0.95,
    vara:     0.80,
    yoga:     0.85,
    planet:   0.65,
  },
}

const WINDOW_LOW: MuhuratWindow = {
  event: 'vivah',
  start_utc: '2026-06-12T01:30:00Z',
  end_utc:   '2026-06-12T12:00:00Z',
  star_rating: 3,
  score: 2.10,
  breakdown: {
    tithi:    0.40,
    nakshatra: 0.50,
    vara:     0.40,
    avoid:    -0.20,
  },
}

const WINDOW_WITH_NEGATIVE: MuhuratWindow = {
  event: 'vivah',
  start_utc: '2026-06-20T02:00:00Z',
  end_utc:   '2026-06-20T12:30:00Z',
  star_rating: 2,
  score: 1.50,
  breakdown: {
    tithi:    0.30,
    avoid:    -0.50,
  },
}

// ── Default props ─────────────────────────────────────────────────────────────

const DEFAULT_MODAL_PROPS = {
  onClose: vi.fn(),
  lat: 20.27,
  lon: 85.84,
  tzOffsetMinutes: 330,
}

// ── MuhuratFinderModal tests ──────────────────────────────────────────────────

describe('MuhuratFinderModal', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockWindows = null
    mockIsLoading = false
    mockError = null
  })

  it('renders modal with heading and form', () => {
    render(<MuhuratFinderModal {...DEFAULT_MODAL_PROPS} />)
    expect(screen.getByRole('dialog', { name: /muhurat finder/i })).toBeTruthy()
    expect(screen.getByLabelText('Event')).toBeTruthy()
    expect(screen.getByLabelText('From')).toBeTruthy()
    expect(screen.getByLabelText('To')).toBeTruthy()
    expect(screen.getByLabelText('Latitude')).toBeTruthy()
    expect(screen.getByLabelText('Longitude')).toBeTruthy()
  })

  it('pre-fills lat/lon from props', () => {
    render(<MuhuratFinderModal {...DEFAULT_MODAL_PROPS} lat={28.61} lon={77.21} />)
    const latInput = screen.getByLabelText('Latitude') as HTMLInputElement
    const lonInput = screen.getByLabelText('Longitude') as HTMLInputElement
    expect(latInput.value).toBe('28.61')
    expect(lonInput.value).toBe('77.21')
  })

  it('has 6 MVP event options', () => {
    render(<MuhuratFinderModal {...DEFAULT_MODAL_PROPS} />)
    const select = screen.getByLabelText('Event') as HTMLSelectElement
    expect(select.options.length).toBe(6)
  })

  it('defaults to Vivah as first event', () => {
    render(<MuhuratFinderModal {...DEFAULT_MODAL_PROPS} />)
    const select = screen.getByLabelText('Event') as HTMLSelectElement
    expect(select.value).toBe('vivah')
  })

  it('calls onClose when backdrop clicked', () => {
    const onClose = vi.fn()
    render(<MuhuratFinderModal {...DEFAULT_MODAL_PROPS} onClose={onClose} />)
    const backdrop = screen.getByRole('dialog', { name: /muhurat finder/i })
    fireEvent.click(backdrop)
    expect(onClose).toHaveBeenCalled()
  })

  it('calls onClose when X button clicked', () => {
    const onClose = vi.fn()
    render(<MuhuratFinderModal {...DEFAULT_MODAL_PROPS} onClose={onClose} />)
    fireEvent.click(screen.getByLabelText('Close Muhurat Finder'))
    expect(onClose).toHaveBeenCalled()
  })

  describe('personalise checkbox', () => {
    it('is disabled and unchecked when no chartId', () => {
      const { container } = render(<MuhuratFinderModal {...DEFAULT_MODAL_PROPS} chartId={null} />)
      // The custom div checkbox has role=checkbox and aria-checked
      const divCheckbox = container.querySelector('div[role="checkbox"]')
      expect(divCheckbox).toBeTruthy()
      expect(divCheckbox!.getAttribute('aria-checked')).toBe('false')
    })

    it('is auto-checked when chartId present', () => {
      const { container } = render(<MuhuratFinderModal {...DEFAULT_MODAL_PROPS} chartId="chart_abc123" />)
      const divCheckbox = container.querySelector('div[role="checkbox"]')
      expect(divCheckbox).toBeTruthy()
      expect(divCheckbox!.getAttribute('aria-checked')).toBe('true')
    })

    it('shows chart-not-selected hint when no chartId', () => {
      render(<MuhuratFinderModal {...DEFAULT_MODAL_PROPS} chartId={null} />)
      expect(
        screen.getByText(/select a chart on the panchang page/i)
      ).toBeTruthy()
    })

    it('shows tara bala hint when chartId present', () => {
      render(<MuhuratFinderModal {...DEFAULT_MODAL_PROPS} chartId="chart_abc123" />)
      expect(
        screen.getByText(/tara bala \+ chandra bala/i)
      ).toBeTruthy()
    })
  })

  describe('form submission', () => {
    it('calls search() with correct params on submit', () => {
      render(<MuhuratFinderModal {...DEFAULT_MODAL_PROPS} />)
      const submitBtn = screen.getByRole('button', { name: /find muhurat/i })
      fireEvent.click(submitBtn)
      expect(mockSearch).toHaveBeenCalledOnce()
      const args = mockSearch.mock.calls[0][0] as Record<string, unknown>
      expect(args.event).toBe('vivah')
      expect(args.lat).toBe(20.27)
      expect(args.lon).toBe(85.84)
      expect(args.tz_offset_minutes).toBe(330)
      expect(args.top_n).toBe(10)
      expect(args.chart_id).toBe(null)  // no chartId
    })

    it('includes chart_id when personalise checked and chartId present', () => {
      render(
        <MuhuratFinderModal {...DEFAULT_MODAL_PROPS} chartId="chart_abc123" />
      )
      const submitBtn = screen.getByRole('button', { name: /find muhurat/i })
      fireEvent.click(submitBtn)
      const args = mockSearch.mock.calls[0][0] as Record<string, unknown>
      expect(args.chart_id).toBe('chart_abc123')
    })

    it('shows results panel after first submit', () => {
      mockWindows = [WINDOW_HIGH]
      render(<MuhuratFinderModal {...DEFAULT_MODAL_PROPS} />)
      const submitBtn = screen.getByRole('button', { name: /find muhurat/i })
      fireEvent.click(submitBtn)
      // After submit, results header appears
      expect(screen.getByText(/results for vivah/i)).toBeTruthy()
    })
  })
})

// ── MuhuratResultsList tests ──────────────────────────────────────────────────

describe('MuhuratResultsList', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('returns null when windows is null (not yet searched)', () => {
    const { container } = render(
      <MuhuratResultsList windows={null} isLoading={false} error={null} event="vivah" />
    )
    expect(container.firstChild).toBeNull()
  })

  it('shows empty state when windows is empty array', () => {
    render(
      <MuhuratResultsList windows={[]} isLoading={false} error={null} event="vivah" />
    )
    expect(screen.getByText(/no auspicious windows found/i)).toBeTruthy()
  })

  it('shows loading skeleton when isLoading', () => {
    const { container } = render(
      <MuhuratResultsList windows={null} isLoading={true} error={null} event="vivah" />
    )
    // Loading container has aria-busy="true" and skeleton rows
    expect(container.querySelector('[aria-busy="true"]')).toBeTruthy()
  })

  it('shows error message when error present', () => {
    render(
      <MuhuratResultsList
        windows={null}
        isLoading={false}
        error="Muhurat engine unreachable"
        event="vivah"
      />
    )
    expect(screen.getByText('Muhurat engine unreachable')).toBeTruthy()
  })

  it('renders result rows for each window', () => {
    render(
      <MuhuratResultsList
        windows={[WINDOW_HIGH, WINDOW_LOW]}
        isLoading={false}
        error={null}
        event="vivah"
        tzOffsetMinutes={330}
      />
    )
    // Two result rows — identified by rank badges
    expect(screen.getByText(/#1/)).toBeTruthy()
    expect(screen.getByText(/#2/)).toBeTruthy()
  })

  it('sorts windows by score descending', () => {
    // Pass windows in wrong order — WINDOW_LOW first
    render(
      <MuhuratResultsList
        windows={[WINDOW_LOW, WINDOW_HIGH]}
        isLoading={false}
        error={null}
        event="vivah"
        tzOffsetMinutes={330}
      />
    )
    const ranks = Array.from(
      document.querySelectorAll('[class*="font-mono"]')
    ).map((el) => el.textContent ?? '')
    // First rank badge should be #1 with higher score
    expect(ranks[0]).toMatch(/#1/)
    expect(ranks[0]).toContain('3.85')
  })

  it('renders star ratings for each window', () => {
    render(
      <MuhuratResultsList
        windows={[WINDOW_HIGH]}
        isLoading={false}
        error={null}
        event="vivah"
        tzOffsetMinutes={330}
      />
    )
    // StarRating renders aria-label "X out of 5 stars"
    expect(screen.getByRole('img', { name: '5 out of 5 stars' })).toBeTruthy()
  })

  it('renders positive breakdown badges', () => {
    render(
      <MuhuratResultsList
        windows={[WINDOW_HIGH]}
        isLoading={false}
        error={null}
        event="vivah"
        tzOffsetMinutes={330}
      />
    )
    expect(screen.getByText(/nakshatra \+0\.95/i)).toBeTruthy()
    expect(screen.getByText(/special yoga \+0\.85/i)).toBeTruthy()
  })

  it('renders avoid/negative breakdown badge', () => {
    render(
      <MuhuratResultsList
        windows={[WINDOW_WITH_NEGATIVE]}
        isLoading={false}
        error={null}
        event="vivah"
        tzOffsetMinutes={330}
      />
    )
    // avoid badge should be present
    expect(screen.getByText(/inauspicious penalty/i)).toBeTruthy()
  })

  describe('inline actions', () => {
    // Note: Calendar Export button was enabled in 4C-7 (the 4C-7 hint + disabled state
    // tests are retired; export is now active). 4C-8 adds panchangContext threading.
    it('Calendar Export button is enabled (4C-7 live)', () => {
      render(
        <MuhuratResultsList
          windows={[WINDOW_HIGH]}
          isLoading={false}
          error={null}
          event="vivah"
          tzOffsetMinutes={330}
        />
      )
      const exportBtn = screen.getByLabelText(/export.*muhurat to calendar/i)
      // Should NOT be disabled — export is live in 4C-7
      expect(exportBtn.getAttribute('disabled')).toBeNull()
    })

    it('Calendar Export button has correct aria-label', () => {
      render(
        <MuhuratResultsList
          windows={[WINDOW_HIGH]}
          isLoading={false}
          error={null}
          event="vivah"
          tzOffsetMinutes={330}
        />
      )
      expect(screen.getByLabelText(/export.*muhurat to calendar/i)).toBeInTheDocument()
    })

    it('Ask Madhav button navigates with prompt containing event and rank', () => {
      render(
        <MuhuratResultsList
          windows={[WINDOW_HIGH]}
          isLoading={false}
          error={null}
          event="vivah"
          tzOffsetMinutes={330}
        />
      )
      const askBtn = screen.getByLabelText(/ask madhav about/i)
      fireEvent.click(askBtn)
      expect(mockPush).toHaveBeenCalledOnce()
      const url = mockPush.mock.calls[0][0] as string
      expect(url).toContain('/clients/362f9f17-95a5-490b-a5a7-027d3e0efda0/consume')
      expect(url).toContain('prompt=')
      expect(decodeURIComponent(url)).toContain('#1')
      expect(decodeURIComponent(url)).toContain('vivah')
    })
  })
})
