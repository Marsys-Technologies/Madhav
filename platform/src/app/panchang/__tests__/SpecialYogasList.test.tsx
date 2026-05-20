/**
 * SpecialYogasList unit tests — AC.4C4S3.1
 *
 * Tests: active yogas render, star ratings, color coding, empty state.
 * Phase: 4C-4-S3 (Item 7)
 */
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { SpecialYogasList } from '../components/SpecialYogasList'
import type { YogaEntry } from '../components/SpecialYogasList'

// ── Test fixtures ─────────────────────────────────────────────────────────────

const AMRIT_SIDDHI: YogaEntry = {
  yoga: 'amrit_siddhi',
  start_utc: '2026-05-20T00:12:00Z', // 05:42 IST (sunrise)
  end_utc: '2026-05-20T16:45:00Z',   // 22:15 IST (nakshatra end)
  strength: 'auspicious',
  stars: 5,
}

const SARVARTHA_SIDDHI: YogaEntry = {
  yoga: 'sarvartha_siddhi',
  start_utc: '2026-05-20T00:12:00Z',
  end_utc: '2026-05-20T12:00:00Z',
  strength: 'auspicious',
  stars: 4,
}

const BHADRA: YogaEntry = {
  yoga: 'bhadra',
  start_utc: '2026-05-20T11:00:00Z',
  end_utc: '2026-05-20T16:30:00Z',
  strength: 'inauspicious',
  stars: 0,
}

const PANCHAKA: YogaEntry = {
  yoga: 'panchaka',
  start_utc: '2026-05-20T00:12:00Z',
  end_utc: '2026-05-20T16:45:00Z',
  strength: 'inauspicious',
  stars: 0,
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('SpecialYogasList', () => {
  describe('empty state', () => {
    it('shows empty message when null', () => {
      render(<SpecialYogasList specialYogas={null} />)
      expect(screen.getByText('No special yogas active today.')).toBeTruthy()
    })

    it('shows empty message when empty array', () => {
      render(<SpecialYogasList specialYogas={[]} />)
      expect(screen.getByText('No special yogas active today.')).toBeTruthy()
    })
  })

  describe('auspicious yogas', () => {
    it('renders Amrit Siddhi Yoga with 5-star rating', () => {
      render(<SpecialYogasList specialYogas={[AMRIT_SIDDHI]} tzOffsetMinutes={330} />)
      expect(screen.getByText('Amrit Siddhi Yoga')).toBeTruthy()
      // Star rating: 5 filled stars
      const starEl = screen.getByRole('img', { name: '5 out of 5 stars' })
      expect(starEl).toBeTruthy()
    })

    it('renders Sarvartha Siddhi Yoga with 4-star rating', () => {
      render(<SpecialYogasList specialYogas={[SARVARTHA_SIDDHI]} tzOffsetMinutes={330} />)
      expect(screen.getByText('Sarvartha Siddhi Yoga')).toBeTruthy()
      const starEl = screen.getByRole('img', { name: '4 out of 5 stars' })
      expect(starEl).toBeTruthy()
    })

    it('renders time window in local time (IST +5:30)', () => {
      // 00:12 UTC + 330 min = 05:42 IST; 16:45 UTC + 330 = 22:15 IST
      render(<SpecialYogasList specialYogas={[AMRIT_SIDDHI]} tzOffsetMinutes={330} />)
      expect(screen.getByText('05:42 – 22:15')).toBeTruthy()
    })

    it('renders ✓ icon for auspicious yogas', () => {
      render(<SpecialYogasList specialYogas={[AMRIT_SIDDHI]} />)
      const check = screen.getAllByText('✓')
      expect(check.length).toBeGreaterThan(0)
    })
  })

  describe('inauspicious yogas', () => {
    it('renders Bhadra with ⚠ icon and no stars', () => {
      render(<SpecialYogasList specialYogas={[BHADRA]} />)
      expect(screen.getByText('Bhadra (avoid)')).toBeTruthy()
      const warn = screen.getAllByText('⚠')
      expect(warn.length).toBeGreaterThan(0)
      // No star rating rendered for inauspicious
      expect(screen.queryByRole('img', { name: /stars/ })).toBeNull()
    })

    it('renders Panchaka Dosha', () => {
      render(<SpecialYogasList specialYogas={[PANCHAKA]} />)
      expect(screen.getByText('Panchaka Dosha')).toBeTruthy()
    })
  })

  describe('multiple yogas', () => {
    it('renders all yogas in a single day', () => {
      render(
        <SpecialYogasList
          specialYogas={[AMRIT_SIDDHI, SARVARTHA_SIDDHI, BHADRA]}
          tzOffsetMinutes={330}
        />
      )
      expect(screen.getByText('Amrit Siddhi Yoga')).toBeTruthy()
      expect(screen.getByText('Sarvartha Siddhi Yoga')).toBeTruthy()
      expect(screen.getByText('Bhadra (avoid)')).toBeTruthy()
    })

    it('renders correct counts of ✓ and ⚠ icons', () => {
      render(
        <SpecialYogasList
          specialYogas={[AMRIT_SIDDHI, SARVARTHA_SIDDHI, BHADRA, PANCHAKA]}
          tzOffsetMinutes={330}
        />
      )
      const checkmarks = screen.getAllByText('✓')
      const warnings = screen.getAllByText('⚠')
      expect(checkmarks).toHaveLength(2)   // 2 auspicious
      expect(warnings).toHaveLength(2)     // 2 inauspicious
    })
  })

  describe('unknown yoga key', () => {
    it('falls back gracefully for unknown yoga name', () => {
      const unknownYoga: YogaEntry = {
        yoga: 'some_future_yoga',
        start_utc: null,
        end_utc: null,
        strength: 'auspicious',
        stars: 3,
      }
      render(<SpecialYogasList specialYogas={[unknownYoga]} />)
      // Should render the raw key as display name
      expect(screen.getByText('some_future_yoga')).toBeTruthy()
    })
  })
})
