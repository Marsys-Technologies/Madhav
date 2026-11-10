/**
 * PanchangHeader unit tests — AC.4C4S1.9 / AC.4C5.4
 *
 * Tests: date controls, location switch, URL param persistence, personalise dropdown.
 * Navigation (router.push) is mocked; we verify the calls rather than
 * rendering a full Next.js router.
 * useChartList is mocked to return the loaded chart choices for each case.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { PanchangHeader, PRESET_LOCATIONS, resolveDate, resolveLocation } from '../components/PanchangHeader'
import { PanchangClientView } from '../components/PanchangClientView'
import type { ChartSummary } from '../hooks/useChartList'

// Mock next/navigation
const mockPush = vi.fn()
const mockSearchParams = new URLSearchParams()
let mockCharts: ChartSummary[] = []
const mockPanchangDay = vi.hoisted(() => vi.fn(() => ({
  data: null,
  isLoading: false,
  isError: false,
  refetch: vi.fn(),
})))

vi.mock('../hooks/usePanchangDay', () => ({ usePanchangDay: mockPanchangDay }))
vi.mock('../components/ActionBar', () => ({ ActionBar: () => null }))

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush }),
  useSearchParams: () => mockSearchParams,
}))

vi.mock('../hooks/useChartList', () => ({
  useChartList: () => ({ charts: mockCharts, isLoading: false, error: null }),
}))

// Mock date-fns format to make today deterministic
vi.mock('date-fns', async (importOriginal) => {
  const actual = await importOriginal<typeof import('date-fns')>()
  return {
    ...actual,
    // keep real implementations; just ensure tests can control "today" via searchParams
  }
})

describe('PanchangHeader', () => {
  const defaultProps = {
    initialDate: '2026-05-20',
    initialLocation: PRESET_LOCATIONS[0], // Bhubaneswar
  }

  beforeEach(() => {
    vi.clearAllMocks()
    mockCharts = []
    localStorage.clear()
    // Reset mocked search params
    mockSearchParams.delete('d')
    mockSearchParams.delete('loc')
    mockSearchParams.delete('lat')
    mockSearchParams.delete('lon')
    mockSearchParams.delete('chart_id')
  })

  it('renders the date navigation controls', () => {
    render(<PanchangHeader {...defaultProps} />)
    expect(screen.getByLabelText('Previous day')).toBeInTheDocument()
    expect(screen.getByLabelText('Next day')).toBeInTheDocument()
    expect(screen.getByLabelText('Select date')).toBeInTheDocument()
  })

  it('renders the location selector with all presets', () => {
    render(<PanchangHeader {...defaultProps} />)
    const select = screen.getByLabelText('Location')
    expect(select).toBeInTheDocument()
    for (const loc of PRESET_LOCATIONS) {
      expect(screen.getByRole('option', { name: loc.label })).toBeInTheDocument()
    }
    expect(screen.getByRole('option', { name: 'Custom…' })).toBeInTheDocument()
  })

  it('clicking Previous day calls router.push with decremented date', () => {
    mockSearchParams.set('d', '2026-05-20')
    render(<PanchangHeader {...defaultProps} />)
    fireEvent.click(screen.getByLabelText('Previous day'))
    expect(mockPush).toHaveBeenCalledOnce()
    expect(mockPush.mock.calls[0][0]).toContain('d=2026-05-19')
  })

  it('clicking Next day calls router.push with incremented date', () => {
    mockSearchParams.set('d', '2026-05-20')
    render(<PanchangHeader {...defaultProps} />)
    fireEvent.click(screen.getByLabelText('Next day'))
    expect(mockPush).toHaveBeenCalledOnce()
    expect(mockPush.mock.calls[0][0]).toContain('d=2026-05-21')
  })

  it('changing location to New Delhi calls router.push with loc=new_delhi', () => {
    render(<PanchangHeader {...defaultProps} />)
    const select = screen.getByLabelText('Location')
    fireEvent.change(select, { target: { value: 'new_delhi' } })
    expect(mockPush).toHaveBeenCalledOnce()
    expect(mockPush.mock.calls[0][0]).toContain('loc=new_delhi')
  })

  it('selecting Custom… shows lat/lon inputs and Apply button', () => {
    render(<PanchangHeader {...defaultProps} />)
    const select = screen.getByLabelText('Location')
    fireEvent.change(select, { target: { value: 'custom' } })
    expect(screen.getByLabelText('Latitude')).toBeInTheDocument()
    expect(screen.getByLabelText('Longitude')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Apply' })).toBeInTheDocument()
  })

  it.each([
    ['no URL date', null, '2026-05-20'],
    ['an invalid URL date', 'not-a-date', '2026-05-20'],
    ['a valid URL date', '2026-05-22', '2026-05-22'],
  ])('keeps the displayed and requested chart date in sync for %s', (_label, urlDate, expected) => {
    if (urlDate) mockSearchParams.set('d', urlDate)
    mockSearchParams.set('chart_id', 'other-chart')
    render(<PanchangClientView initialData={null} initialDate={defaultProps.initialDate} fixedChartId="allowed-chart" />)
    expect(screen.getByLabelText('Select date')).toHaveValue(expected)
    expect(mockPanchangDay).toHaveBeenLastCalledWith(expect.objectContaining({
      date: expected,
      chartId: 'allowed-chart',
      tzOffsetMinutes: 330,
    }))
  })

  it('keeps navigation on the authorized chart and drops any chart override', () => {
    mockSearchParams.set('d', '2026-05-20')
    mockSearchParams.set('chart_id', 'other-chart')
    render(<PanchangHeader {...defaultProps} fixedChartId="allowed-chart" />)
    expect(screen.queryByLabelText('Personalise view')).not.toBeInTheDocument()
    fireEvent.change(screen.getByLabelText('Location'), { target: { value: 'new_delhi' } })
    expect(mockPush).toHaveBeenCalledWith('/clients/allowed-chart/panchang?d=2026-05-20&loc=new_delhi')
  })

  it('Personalise select is present with Generic Panchang default and enabled when charts loaded', () => {
    render(<PanchangHeader {...defaultProps} />)
    const sel = screen.getByLabelText('Personalise view')
    expect(sel).toBeInTheDocument()
    expect(sel).not.toBeDisabled()
    expect(sel).toHaveValue('generic')
  })

  it('uses the granted stored selection and falls back to generic if the grant is removed', () => {
    mockCharts = [{ id: 'granted-chart', name: 'Granted chart', birth_date: '1990-01-01' }]
    localStorage.setItem('panchang.personalise.chart_id', 'granted-chart')
    const view = <PanchangClientView initialData={null} initialDate={defaultProps.initialDate} />
    const { rerender } = render(view)

    expect(screen.getByLabelText('Personalise view')).toHaveValue('granted-chart')
    expect(mockPanchangDay).toHaveBeenLastCalledWith(expect.objectContaining({ chartId: 'granted-chart' }))

    mockSearchParams.set('chart_id', 'denied-chart')
    rerender(<PanchangClientView initialData={null} initialDate={defaultProps.initialDate} />)

    expect(screen.getByLabelText('Personalise view')).toHaveValue('generic')
    expect(mockPanchangDay).toHaveBeenLastCalledWith(expect.objectContaining({ chartId: null }))
    expect(mockPanchangDay).not.toHaveBeenCalledWith(expect.objectContaining({ chartId: 'denied-chart' }))

    mockSearchParams.delete('chart_id')
    mockCharts = []
    rerender(<PanchangClientView initialData={null} initialDate={defaultProps.initialDate} />)

    expect(screen.getByLabelText('Personalise view')).toHaveValue('generic')
    expect(mockPanchangDay).toHaveBeenLastCalledWith(expect.objectContaining({ chartId: null }))
  })

  it('clears a stored chart even when the current URL has no chart parameter', () => {
    mockCharts = [{ id: 'granted-chart', name: 'Granted chart', birth_date: '1990-01-01' }]
    localStorage.setItem('panchang.personalise.chart_id', 'granted-chart')
    render(<PanchangClientView initialData={null} initialDate={defaultProps.initialDate} />)
    const picker = screen.getByLabelText('Personalise view')
    expect(picker).toHaveValue('granted-chart')

    fireEvent.change(picker, { target: { value: 'generic' } })

    expect(localStorage.getItem('panchang.personalise.chart_id')).toBeNull()
    expect(picker).toHaveValue('generic')
    expect(mockPanchangDay).toHaveBeenLastCalledWith(expect.objectContaining({ chartId: null }))
  })
})

describe('resolveDate', () => {
  it('returns the d param when valid ISO date', () => {
    const p = new URLSearchParams('d=2026-01-15')
    expect(resolveDate(p)).toBe('2026-01-15')
  })

  it('returns today when d param is missing', () => {
    const p = new URLSearchParams()
    const result = resolveDate(p)
    expect(result).toMatch(/^\d{4}-\d{2}-\d{2}$/)
  })

  it('returns today when d param is invalid', () => {
    const p = new URLSearchParams('d=not-a-date')
    const result = resolveDate(p)
    expect(result).toMatch(/^\d{4}-\d{2}-\d{2}$/)
  })
})

describe('resolveLocation', () => {
  it('returns Bhubaneswar by default', () => {
    const p = new URLSearchParams()
    const loc = resolveLocation(p)
    expect(loc.id).toBe('bhubaneswar')
    expect(loc.lat).toBe(20.27)
  })

  it('returns preset location when loc param matches', () => {
    const p = new URLSearchParams('loc=mumbai')
    const loc = resolveLocation(p)
    expect(loc.id).toBe('mumbai')
    expect(loc.label).toBe('Mumbai')
  })

  it('returns custom location when loc=custom with lat/lon', () => {
    const p = new URLSearchParams('loc=custom&lat=51.5&lon=-0.12')
    const loc = resolveLocation(p)
    expect(loc.id).toBe('custom')
    expect(loc.lat).toBe(51.5)
    expect(loc.lon).toBe(-0.12)
  })

  it('falls back to Bhubaneswar for unknown loc id', () => {
    const p = new URLSearchParams('loc=unknown_city')
    const loc = resolveLocation(p)
    expect(loc.id).toBe('bhubaneswar')
  })
})
