/**
 * PlanetaryGrid unit tests
 * Phase: 4C-4-S2 (Item 6 / AC.4C4S2.6)
 */
import { describe, it, expect } from 'vitest'
import { render } from '@testing-library/react'
import { PlanetaryGrid } from '@/app/panchang/components/PlanetaryGrid'

// Minimal planet dict matching panchang_engine serialize.py output
const SAMPLE_PLANETS = {
  sun: {
    name: 'Sun',
    longitude_sidereal: 4.389,   // Mesha 04°23'
    sign_id: 1,
    sign_name: 'Mesha',
    nakshatra_id: 1,
    nakshatra_name: 'Ashwini',
    nakshatra_pada: 1,
    retrograde: false,
    combust: false,
  },
  moon: {
    name: 'Moon',
    longitude_sidereal: 18.85,   // Mesha 18°51'
    sign_id: 1,
    sign_name: 'Mesha',
    nakshatra_id: 2,
    nakshatra_name: 'Bharani',
    nakshatra_pada: 3,
    retrograde: false,
    combust: false,
  },
  mars: {
    name: 'Mars',
    longitude_sidereal: 72.2,    // Mithuna 12° — retrograde
    sign_id: 3,
    sign_name: 'Mithuna',
    nakshatra_id: 6,
    nakshatra_name: 'Ardra',
    nakshatra_pada: 2,
    retrograde: true,
    combust: false,
  },
  mercury: {
    name: 'Mercury',
    longitude_sidereal: 9.0,     // Mesha 09° — combust
    sign_id: 1,
    sign_name: 'Mesha',
    nakshatra_id: 1,
    nakshatra_name: 'Ashwini',
    nakshatra_pada: 3,
    retrograde: false,
    combust: true,
  },
  jupiter: {
    name: 'Jupiter',
    longitude_sidereal: 85.0,    // Mithuna 25°
    sign_id: 3,
    sign_name: 'Mithuna',
    nakshatra_id: 7,
    nakshatra_name: 'Punarvasu',
    nakshatra_pada: 1,
    retrograde: false,
    combust: false,
  },
  venus: {
    name: 'Venus',
    longitude_sidereal: 32.0,    // Vrishabha 02°
    sign_id: 2,
    sign_name: 'Vrishabha',
    nakshatra_id: 4,
    nakshatra_name: 'Rohini',
    nakshatra_pada: 2,
    retrograde: false,
    combust: false,
  },
  saturn: {
    name: 'Saturn',
    longitude_sidereal: 318.0,   // Kumbha 18° — retrograde
    sign_id: 11,
    sign_name: 'Kumbha',
    nakshatra_id: 24,
    nakshatra_name: 'Shatabhisha',
    nakshatra_pada: 3,
    retrograde: true,
    combust: false,
  },
  rahu: {
    name: 'Rahu',
    longitude_sidereal: 357.0,   // Meena 27°
    sign_id: 12,
    sign_name: 'Meena',
    nakshatra_id: 27,
    nakshatra_name: 'Revati',
    nakshatra_pada: 4,
    retrograde: false,
    combust: false,
  },
  ketu: {
    name: 'Ketu',
    longitude_sidereal: 177.0,   // Kanya 27°
    sign_id: 6,
    sign_name: 'Kanya',
    nakshatra_id: 14,
    nakshatra_name: 'Chitra',
    nakshatra_pada: 1,
    retrograde: false,
    combust: false,
  },
}

describe('PlanetaryGrid', () => {
  it('renders all 9 grahas', () => {
    const { getByLabelText } = render(<PlanetaryGrid planets={SAMPLE_PLANETS} />)
    const grahas = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']
    for (const graha of grahas) {
      // Each card has aria-label starting with the English name
      expect(getByLabelText(new RegExp(`^${graha}`))).toBeTruthy()
    }
  })

  it('shows retrograde badge for retrograde planets', () => {
    const { getAllByTitle } = render(<PlanetaryGrid planets={SAMPLE_PLANETS} />)
    const retroBadges = getAllByTitle('Retrograde')
    // Mars and Saturn are retrograde
    expect(retroBadges.length).toBe(2)
  })

  it('shows combust badge for combust planets', () => {
    const { getAllByTitle } = render(<PlanetaryGrid planets={SAMPLE_PLANETS} />)
    const combustBadges = getAllByTitle('Combust')
    // Mercury is combust
    expect(combustBadges.length).toBe(1)
  })

  it('displays sign names in graha card labels', () => {
    const { getByLabelText } = render(<PlanetaryGrid planets={SAMPLE_PLANETS} />)
    const sunCard = getByLabelText(/^Sun:/)
    expect(sunCard.getAttribute('aria-label')).toContain('Mesha')
    const saturnCard = getByLabelText(/^Saturn:/)
    expect(saturnCard.getAttribute('aria-label')).toContain('Kumbha')
  })

  it('includes zodiac glyphs in rendered output', () => {
    const { container } = render(<PlanetaryGrid planets={SAMPLE_PLANETS} />)
    // Mesha glyph ♈ should appear (multiple planets in Mesha)
    expect(container.textContent).toContain('♈')
    // Kumbha ♒ for Saturn
    expect(container.textContent).toContain('♒')
    // Meena ♓ for Rahu
    expect(container.textContent).toContain('♓')
  })

  it('renders DMS longitude within sign', () => {
    const { getByLabelText } = render(<PlanetaryGrid planets={SAMPLE_PLANETS} />)
    // Sun at Mesha 04°23' (longitude_sidereal = 4.389 → within-sign = 4.389 → DMS = 04°23')
    const sunCard = getByLabelText(/^Sun:/)
    expect(sunCard.getAttribute('aria-label')).toContain('04°23')
  })

  it('renders legend strip', () => {
    const { getByLabelText } = render(<PlanetaryGrid planets={SAMPLE_PLANETS} />)
    expect(
      getByLabelText('Legend: R equals retrograde, C equals combust')
    ).toBeTruthy()
  })

  it('handles null planets gracefully — renders all 9 card slots with empty state', () => {
    const { container } = render(<PlanetaryGrid planets={null} />)
    // 9 GrahaCards should still render (showing dash)
    const cards = container.querySelectorAll('[role="row"]')
    expect(cards.length).toBe(9)
  })

  it('handles array-shaped planet data (defensive)', () => {
    const asArray = Object.values(SAMPLE_PLANETS)
    const { getByLabelText } = render(<PlanetaryGrid planets={asArray as unknown as Record<string, never>} />)
    // Should still find Sun card
    expect(getByLabelText(/^Sun:/)).toBeTruthy()
  })
})
