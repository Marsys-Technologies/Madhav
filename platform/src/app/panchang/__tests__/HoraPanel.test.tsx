/**
 * HoraPanel unit tests — AC.4C4S3.3
 *
 * Tests: toggle open/close, 24-hora data, Chaldean order starting from vara lord.
 * Phase: 4C-4-S3 (Item 7)
 */
import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { HoraPanel } from '../components/HoraPanel'

// ── Test fixtures ─────────────────────────────────────────────────────────────

function makeHora(planet: string, startH: number, endH: number) {
  const pad = (n: number) => String(n).padStart(2, '0')
  const startHour = startH % 24
  const endHour = endH % 24
  return {
    label: `hora_${planet}`,
    start_utc: `2026-05-20T${pad(startHour)}:00:00Z`,
    end_utc:   `2026-05-20T${pad(endHour)}:00:00Z`,
  }
}

// Tuesday (Mangalavara = Mars day). Hora sequence starts with Mars (vara lord),
// then follows Chaldean: Mars → Sun → Venus → Mercury → Moon → Saturn → Jupiter → (repeat)
// 24 horas × 60 min each
const HORA_SEQUENCE_TUESDAY = [
  makeHora('mars',    0,  1),
  makeHora('sun',     1,  2),
  makeHora('venus',   2,  3),
  makeHora('mercury', 3,  4),
  makeHora('moon',    4,  5),
  makeHora('saturn',  5,  6),
  makeHora('jupiter', 6,  7),
  makeHora('mars',    7,  8),
  makeHora('sun',     8,  9),
  makeHora('venus',   9,  10),
  makeHora('mercury', 10, 11),
  makeHora('moon',    11, 12),
  makeHora('saturn',  12, 13),
  makeHora('jupiter', 13, 14),
  makeHora('mars',    14, 15),
  makeHora('sun',     15, 16),
  makeHora('venus',   16, 17),
  makeHora('mercury', 17, 18),
  makeHora('moon',    18, 19),
  makeHora('saturn',  19, 20),
  makeHora('jupiter', 20, 21),
  makeHora('mars',    21, 22),
  makeHora('sun',     22, 23),
  makeHora('venus',   23, 0),
]

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('HoraPanel', () => {
  describe('collapsed state (default)', () => {
    it('renders trigger button with aria-expanded=false', () => {
      render(<HoraPanel hora={HORA_SEQUENCE_TUESDAY} />)
      const trigger = screen.getByRole('button')
      expect(trigger.getAttribute('aria-expanded')).toBe('false')
    })

    it('shows segment count in trigger subtitle when collapsed', () => {
      render(<HoraPanel hora={HORA_SEQUENCE_TUESDAY} />)
      expect(screen.getByText('24 planetary hours (Chaldean order)')).toBeTruthy()
    })
  })

  describe('toggle open', () => {
    it('sets aria-expanded=true after click', () => {
      render(<HoraPanel hora={HORA_SEQUENCE_TUESDAY} />)
      const trigger = screen.getByRole('button')
      fireEvent.click(trigger)
      expect(trigger.getAttribute('aria-expanded')).toBe('true')
    })

    it('renders 24 hora rows when expanded', () => {
      render(<HoraPanel hora={HORA_SEQUENCE_TUESDAY} tzOffsetMinutes={330} />)
      fireEvent.click(screen.getByRole('button'))
      const rows = screen.getAllByRole('row')
      expect(rows).toHaveLength(24)
    })

    it('first hora is Mars (Tuesday vara lord)', () => {
      render(<HoraPanel hora={HORA_SEQUENCE_TUESDAY} tzOffsetMinutes={330} />)
      fireEvent.click(screen.getByRole('button'))
      // First row aria-label starts with "Hora 1: Mars"
      const firstRow = screen.getByRole('row', { name: /Hora 1: Mars/ })
      expect(firstRow).toBeTruthy()
    })

    it('second hora is Sun (Chaldean order after Mars)', () => {
      render(<HoraPanel hora={HORA_SEQUENCE_TUESDAY} tzOffsetMinutes={330} />)
      fireEvent.click(screen.getByRole('button'))
      const secondRow = screen.getByRole('row', { name: /Hora 2: Sun/ })
      expect(secondRow).toBeTruthy()
    })

    it('renders correct planet names in Sanskrit', () => {
      render(<HoraPanel hora={HORA_SEQUENCE_TUESDAY} tzOffsetMinutes={330} />)
      fireEvent.click(screen.getByRole('button'))
      // Mars Sanskrit
      const marsRows = screen.getAllByText('मंगल')
      expect(marsRows.length).toBeGreaterThan(0)
    })
  })

  describe('toggle close', () => {
    it('collapses on second click', () => {
      render(<HoraPanel hora={HORA_SEQUENCE_TUESDAY} />)
      const trigger = screen.getByRole('button')
      fireEvent.click(trigger)
      fireEvent.click(trigger)
      expect(trigger.getAttribute('aria-expanded')).toBe('false')
    })
  })

  describe('empty / null data', () => {
    it('handles null hora gracefully', () => {
      render(<HoraPanel hora={null} />)
      fireEvent.click(screen.getByRole('button'))
      expect(screen.getByText('Hora data not available.')).toBeTruthy()
    })

    it('handles empty array', () => {
      render(<HoraPanel hora={[]} />)
      fireEvent.click(screen.getByRole('button'))
      expect(screen.getByText('Hora data not available.')).toBeTruthy()
    })
  })
})
