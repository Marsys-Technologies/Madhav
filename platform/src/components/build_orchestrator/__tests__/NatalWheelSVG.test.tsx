/**
 * Unit + mount tests for NatalWheelSVG — H-02 natal wheel.
 *
 * Asserts:
 *   1. Renders SVG element with data-testid
 *   2. Exactly 12 segments are rendered
 *   3. All 12 house labels (1–12) are present
 *   4. Default state is idle (data-state attribute)
 *   5. Complete state renders with green fill (STATE_COLORS.complete)
 *   6. Failed state renders with red fill (STATE_COLORS.failed)
 *   7. Building state renders with blue fill and animation child
 *   8. Center "Build" label is present
 *   9. Idle subtitle shown when no activeAyanamshas
 *  10. Active ayanamsha count shown in subtitle
 *  11. Custom segments override defaults
 *  12. size prop changes viewBox attribute
 */

import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import NatalWheelSVG, { type WheelSegment } from '../NatalWheelSVG'

// ─── helpers ────────────────────────────────────────────────────────────────

function makeSegments(state: WheelSegment['state']): WheelSegment[] {
  return Array.from({ length: 12 }, (_, i) => ({
    house: i + 1,
    sign: 'Aries',
    startAngle: i * 30 - 90,
    state,
  }))
}

// ─── tests ───────────────────────────────────────────────────────────────────

describe('NatalWheelSVG', () => {
  // 1. SVG element renders with testid
  it('renders an SVG element with data-testid="natal-wheel-svg"', () => {
    render(<NatalWheelSVG />)
    const svg = screen.getByTestId('natal-wheel-svg')
    expect(svg).toBeInTheDocument()
    expect(svg.tagName.toLowerCase()).toBe('svg')
  })

  // 2. Exactly 12 segments rendered
  it('renders exactly 12 house segments', () => {
    render(<NatalWheelSVG />)
    const segments = screen.getAllByTestId(/^wheel-segment-\d+$/)
    expect(segments).toHaveLength(12)
  })

  // 3. House labels 1–12 all present
  it('renders house number labels 1 through 12', () => {
    render(<NatalWheelSVG />)
    for (let h = 1; h <= 12; h++) {
      const label = screen.getByTestId(`wheel-label-${h}`)
      expect(label).toBeInTheDocument()
      expect(label.textContent).toBe(String(h))
    }
  })

  // 4. Default state is idle
  it('all segments default to idle state', () => {
    render(<NatalWheelSVG />)
    for (let h = 1; h <= 12; h++) {
      const seg = screen.getByTestId(`wheel-segment-${h}`)
      expect(seg).toHaveAttribute('data-state', 'idle')
    }
  })

  // 5. Complete state — segment path fill is green (#16A34A)
  it('renders complete state with green fill', () => {
    const segments = makeSegments('complete')
    render(<NatalWheelSVG segments={segments} />)
    const seg = screen.getByTestId('wheel-segment-1')
    expect(seg).toHaveAttribute('data-state', 'complete')
    const path = seg.querySelector('path')
    expect(path).not.toBeNull()
    expect(path!.getAttribute('fill')).toBe('#16A34A')
  })

  // 6. Failed state — segment path fill is red (#DC2626)
  it('renders failed state with red fill', () => {
    const segments = makeSegments('failed')
    render(<NatalWheelSVG segments={segments} />)
    const seg = screen.getByTestId('wheel-segment-1')
    expect(seg).toHaveAttribute('data-state', 'failed')
    const path = seg.querySelector('path')
    expect(path).not.toBeNull()
    expect(path!.getAttribute('fill')).toBe('#DC2626')
  })

  // 7. Building state — segment fill is blue and animate element present
  it('renders building state with blue fill and CSS animation child', () => {
    const segments = makeSegments('building')
    render(<NatalWheelSVG segments={segments} />)
    const seg = screen.getByTestId('wheel-segment-1')
    expect(seg).toHaveAttribute('data-state', 'building')
    const path = seg.querySelector('path')
    expect(path).not.toBeNull()
    expect(path!.getAttribute('fill')).toBe('#2563EB')
    // Should contain an <animate> child for pulse
    const animate = path!.querySelector('animate')
    expect(animate).not.toBeNull()
  })

  // 8. Center "Build" title present
  it('renders center "Build" title label', () => {
    render(<NatalWheelSVG />)
    const title = screen.getByTestId('wheel-center-title')
    expect(title).toBeInTheDocument()
    expect(title.textContent).toBe('Build')
  })

  // 9. Idle subtitle shown when activeAyanamshas is empty
  it('shows "Idle" in subtitle when no activeAyanamshas provided', () => {
    render(<NatalWheelSVG activeAyanamshas={[]} />)
    const subtitle = screen.getByTestId('wheel-center-subtitle')
    expect(subtitle).toBeInTheDocument()
    expect(subtitle.textContent).toBe('Idle')
  })

  // 10. Active ayanamsha count shown in subtitle
  it('shows ayanamsha count in subtitle when activeAyanamshas provided', () => {
    render(<NatalWheelSVG activeAyanamshas={['Lahiri', 'Raman', 'KP']} />)
    const subtitle = screen.getByTestId('wheel-center-subtitle')
    expect(subtitle.textContent).toContain('3')
    expect(subtitle.textContent).toContain('ayanamshas')
  })

  // 11. Singular "ayanamsha" (no 's') for count of 1
  it('uses singular "ayanamsha" label for a single active ayanamsha', () => {
    render(<NatalWheelSVG activeAyanamshas={['Lahiri']} />)
    const subtitle = screen.getByTestId('wheel-center-subtitle')
    expect(subtitle.textContent).toBe('1 ayanamsha')
  })

  // 12. Custom segments override defaults — segment 1 can be 'complete'
  it('respects custom segment state overrides', () => {
    const custom: WheelSegment[] = [
      { house: 1, sign: 'Aries', startAngle: -90, state: 'complete' },
      ...Array.from({ length: 11 }, (_, i) => ({
        house: i + 2,
        sign: 'Taurus',
        startAngle: (i + 1) * 30 - 90,
        state: 'idle' as const,
      })),
    ]
    render(<NatalWheelSVG segments={custom} />)
    expect(screen.getByTestId('wheel-segment-1')).toHaveAttribute('data-state', 'complete')
    expect(screen.getByTestId('wheel-segment-2')).toHaveAttribute('data-state', 'idle')
  })

  // 13. size prop changes SVG viewBox
  it('applies custom size via viewBox attribute', () => {
    render(<NatalWheelSVG size={600} />)
    const svg = screen.getByTestId('natal-wheel-svg')
    expect(svg).toHaveAttribute('viewBox', '0 0 600 600')
  })

  // 14. Center circle is present
  it('renders the center circle element', () => {
    render(<NatalWheelSVG />)
    expect(screen.getByTestId('wheel-center')).toBeInTheDocument()
  })
})
