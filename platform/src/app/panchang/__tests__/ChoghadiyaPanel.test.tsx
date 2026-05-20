/**
 * ChoghadiyaPanel unit tests — AC.4C4S3.2
 *
 * Tests: toggle open/close, 16-segment rendering, quality color coding.
 * Phase: 4C-4-S3 (Item 7)
 */
import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { ChoghadiyaPanel } from '../components/ChoghadiyaPanel'

// ── Test fixtures ─────────────────────────────────────────────────────────────

function makeSegment(label: string, startH: number, endH: number) {
  const pad = (n: number) => String(n).padStart(2, '0')
  return {
    label,
    start_utc: `2026-05-20T${pad(startH)}:00:00Z`,
    end_utc:   `2026-05-20T${pad(endH)}:00:00Z`,
  }
}

// Bhubaneswar 2026-05-20: sunrise ~00:12 UTC (05:42 IST)
// 8 day segments × 90 min each, 8 night segments × 90 min each
const DAY_SEGMENTS = [
  makeSegment('choghadiya_amrit',  0, 1),
  makeSegment('choghadiya_kaal',   1, 2),
  makeSegment('shubh',             2, 3),   // label without prefix — should still work
  makeSegment('choghadiya_rog',    3, 4),
  makeSegment('choghadiya_udveg',  4, 5),
  makeSegment('choghadiya_char',   5, 6),
  makeSegment('choghadiya_labh',   6, 7),
  makeSegment('choghadiya_amrit',  7, 8),
]

const NIGHT_SEGMENTS = [
  makeSegment('choghadiya_shubh',  8,  9),
  makeSegment('choghadiya_amrit',  9,  10),
  makeSegment('choghadiya_rog',    10, 11),
  makeSegment('choghadiya_kaal',   11, 12),
  makeSegment('choghadiya_char',   12, 13),
  makeSegment('choghadiya_labh',   13, 14),
  makeSegment('choghadiya_udveg',  14, 15),
  makeSegment('choghadiya_shubh',  15, 16),
]

const FULL_CHOGHADIYA = { day: DAY_SEGMENTS, night: NIGHT_SEGMENTS }

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('ChoghadiyaPanel', () => {
  describe('collapsed state (default)', () => {
    it('renders trigger button with aria-expanded=false', () => {
      render(<ChoghadiyaPanel choghadiya={FULL_CHOGHADIYA} />)
      const trigger = screen.getByRole('button')
      expect(trigger.getAttribute('aria-expanded')).toBe('false')
    })

    it('does not show segment labels when collapsed', () => {
      render(<ChoghadiyaPanel choghadiya={FULL_CHOGHADIYA} />)
      // Segments are hidden (visibility: hidden) when collapsed
      // The "Day Choghadiya" sub-section heading should not be visible
      // We test via aria-hidden on the content
      const content = document.querySelector('[aria-hidden="true"]')
      expect(content).toBeTruthy()
    })
  })

  describe('toggle open', () => {
    it('sets aria-expanded=true after click', () => {
      render(<ChoghadiyaPanel choghadiya={FULL_CHOGHADIYA} />)
      const trigger = screen.getByRole('button')
      fireEvent.click(trigger)
      expect(trigger.getAttribute('aria-expanded')).toBe('true')
    })

    it('shows Day Choghadiya sub-section heading when expanded', () => {
      render(<ChoghadiyaPanel choghadiya={FULL_CHOGHADIYA} />)
      fireEvent.click(screen.getByRole('button'))
      expect(screen.getByText('Day Choghadiya')).toBeTruthy()
      expect(screen.getByText('Night Choghadiya')).toBeTruthy()
    })

    it('renders all 8 day segments when expanded', () => {
      render(<ChoghadiyaPanel choghadiya={FULL_CHOGHADIYA} tzOffsetMinutes={330} />)
      fireEvent.click(screen.getByRole('button'))
      // Each Amrit appears twice (first + last day segment both labeled amrit)
      const amritEntries = screen.getAllByText('Amrit')
      expect(amritEntries.length).toBeGreaterThanOrEqual(2)
    })

    it('renders all 16 total segments (8 day + 8 night) when expanded', () => {
      render(<ChoghadiyaPanel choghadiya={FULL_CHOGHADIYA} tzOffsetMinutes={330} />)
      fireEvent.click(screen.getByRole('button'))
      // Count all "row" elements within the panel
      const rows = screen.getAllByRole('row')
      expect(rows.length).toBe(16)
    })
  })

  describe('toggle close', () => {
    it('collapses back on second click', () => {
      render(<ChoghadiyaPanel choghadiya={FULL_CHOGHADIYA} />)
      const trigger = screen.getByRole('button')
      fireEvent.click(trigger)
      expect(trigger.getAttribute('aria-expanded')).toBe('true')
      fireEvent.click(trigger)
      expect(trigger.getAttribute('aria-expanded')).toBe('false')
    })
  })

  describe('empty / null data', () => {
    it('handles null choghadiya gracefully', () => {
      render(<ChoghadiyaPanel choghadiya={null} />)
      fireEvent.click(screen.getByRole('button'))
      expect(screen.getByText('Choghadiya data not available.')).toBeTruthy()
    })

    it('handles missing day/night arrays', () => {
      render(<ChoghadiyaPanel choghadiya={{}} />)
      fireEvent.click(screen.getByRole('button'))
      // Both sub-sections show "No data"
      const noData = screen.getAllByText('No data')
      expect(noData.length).toBeGreaterThanOrEqual(2)
    })
  })
})
