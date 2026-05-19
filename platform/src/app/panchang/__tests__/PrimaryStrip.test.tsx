/**
 * PrimaryStrip unit tests — AC.4C4S1.9
 *
 * Tests: renders all 6 rows, displays anga names, handles missing data gracefully,
 * shows ends_at times correctly, handles second karana.
 */
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { PrimaryStrip } from '../components/PrimaryStrip'
import type { PanchangAngas } from '../hooks/usePanchangDay'

const FULL_ANGAS: PanchangAngas = {
  tithi: { name: 'Chaturthi', number: 4, ends_at_local: '2026-05-20T12:30:00Z' },
  nakshatra: { name: 'Rohini', number: 4, ends_at_local: '2026-05-20T18:45:00Z' },
  yoga: { name: 'Shiva', number: 11, ends_at_local: '2026-05-20T20:00:00Z' },
  karana_first: { name: 'Bava', number: 1, ends_at_local: '2026-05-20T12:30:00Z' },
  karana_second: { name: 'Balava', number: 2, ends_at_local: '2026-05-20T23:59:00Z' },
  vara: { name: 'Wednesday', number: 4 },
  paksha: 'Shukla Paksha',
}

const EMPTY_ANGAS: PanchangAngas = {
  tithi: null,
  nakshatra: null,
  yoga: null,
  karana_first: null,
  karana_second: null,
  vara: null,
  paksha: null,
}

describe('PrimaryStrip', () => {
  it('renders section with correct aria-label', () => {
    render(<PrimaryStrip angas={FULL_ANGAS} date="2026-05-20" />)
    expect(screen.getByRole('region', { name: /Five Angas.*Primary Panchang Strip/i })).toBeInTheDocument()
  })

  it('renders all 6 anga rows', () => {
    render(<PrimaryStrip angas={FULL_ANGAS} date="2026-05-20" />)
    expect(screen.getByRole('row', { name: /Tithi/i })).toBeInTheDocument()
    expect(screen.getByRole('row', { name: /Nakshatra/i })).toBeInTheDocument()
    expect(screen.getByRole('row', { name: /Yoga/i })).toBeInTheDocument()
    expect(screen.getByRole('row', { name: /Karana/i })).toBeInTheDocument()
    expect(screen.getByRole('row', { name: /Vara/i })).toBeInTheDocument()
    expect(screen.getByRole('row', { name: /Paksha/i })).toBeInTheDocument()
  })

  it('displays tithi name with ordinal', () => {
    render(<PrimaryStrip angas={FULL_ANGAS} date="2026-05-20" />)
    expect(screen.getByText(/Chaturthi \(4th\)/)).toBeInTheDocument()
  })

  it('displays nakshatra name', () => {
    render(<PrimaryStrip angas={FULL_ANGAS} date="2026-05-20" />)
    expect(screen.getByText('Rohini')).toBeInTheDocument()
  })

  it('displays yoga name', () => {
    render(<PrimaryStrip angas={FULL_ANGAS} date="2026-05-20" />)
    expect(screen.getByText('Shiva')).toBeInTheDocument()
  })

  it('displays vara name', () => {
    render(<PrimaryStrip angas={FULL_ANGAS} date="2026-05-20" />)
    expect(screen.getByText('Wednesday')).toBeInTheDocument()
  })

  it('displays paksha value', () => {
    render(<PrimaryStrip angas={FULL_ANGAS} date="2026-05-20" />)
    expect(screen.getByText('Shukla Paksha')).toBeInTheDocument()
  })

  it('converts UTC ends_at to IST local time correctly', () => {
    // tithi ends_at_local: 2026-05-20T12:30:00Z → IST 18:00
    render(<PrimaryStrip angas={FULL_ANGAS} date="2026-05-20" tzOffsetMinutes={330} />)
    const endsBadges = screen.getAllByText(/^ends \d{2}:\d{2}$/)
    // Tithi: 12:30Z + 330min = 18:00 IST
    expect(endsBadges.some(el => el.textContent === 'ends 18:00')).toBe(true)
  })

  it('shows second karana when present', () => {
    render(<PrimaryStrip angas={FULL_ANGAS} date="2026-05-20" />)
    expect(screen.getByText('Balava')).toBeInTheDocument()
    expect(screen.getByText('Karana 2')).toBeInTheDocument()
  })

  it('does not show second karana when absent', () => {
    const noSecondKarana: PanchangAngas = { ...FULL_ANGAS, karana_second: null }
    render(<PrimaryStrip angas={noSecondKarana} date="2026-05-20" />)
    expect(screen.queryByText('Karana 2')).not.toBeInTheDocument()
  })

  it('renders gracefully with all-null angas (missing data)', () => {
    render(<PrimaryStrip angas={EMPTY_ANGAS} date="2026-05-20" />)
    // All 6 rows should still render (with — placeholder)
    expect(screen.getByRole('row', { name: /Tithi.*unavailable/i })).toBeInTheDocument()
    expect(screen.getByRole('row', { name: /Nakshatra.*unavailable/i })).toBeInTheDocument()
    expect(screen.getByRole('row', { name: /Vara.*unavailable/i })).toBeInTheDocument()
    expect(screen.getByRole('row', { name: /Paksha.*unavailable/i })).toBeInTheDocument()
    // No ends_at badges
    expect(screen.queryByText(/^ends /)).not.toBeInTheDocument()
  })

  it('does not show ends_at for vara (spans full day)', () => {
    render(<PrimaryStrip angas={FULL_ANGAS} date="2026-05-20" />)
    const varaRow = screen.getByRole('row', { name: /Vara/i })
    // Vara row should not contain an "ends" badge
    expect(varaRow.textContent).not.toContain('ends')
  })

  it('shows the date in the footer', () => {
    render(<PrimaryStrip angas={FULL_ANGAS} date="2026-05-20" />)
    expect(screen.getByText(/2026-05-20/)).toBeInTheDocument()
  })
})
