/**
 * PanchangHeader unit tests — AC.4C4S1.9
 *
 * Tests: date controls, location switch, URL param persistence.
 * Navigation (router.push) is mocked; we verify the calls rather than
 * rendering a full Next.js router.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { PanchangHeader, PRESET_LOCATIONS, resolveDate, resolveLocation } from '../components/PanchangHeader'

// Mock next/navigation
const mockPush = vi.fn()
const mockSearchParams = new URLSearchParams()

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush }),
  useSearchParams: () => mockSearchParams,
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
    // Reset mocked search params
    mockSearchParams.delete('d')
    mockSearchParams.delete('loc')
    mockSearchParams.delete('lat')
    mockSearchParams.delete('lon')
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

  it('Personalise button is present and disabled (4C-5 scope)', () => {
    render(<PanchangHeader {...defaultProps} />)
    const btn = screen.getByLabelText('Personalise (coming soon)')
    expect(btn).toBeInTheDocument()
    expect(btn).toBeDisabled()
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
