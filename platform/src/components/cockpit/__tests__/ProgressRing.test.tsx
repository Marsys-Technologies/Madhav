import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ProgressRing } from '../ProgressRing'

describe('ProgressRing', () => {
  it('renders an SVG with data-testid progress-ring', () => {
    render(<ProgressRing progress={0.5} />)
    expect(screen.getByTestId('progress-ring')).toBeTruthy()
  })

  it('renders 0% correctly — dashoffset equals circumference', () => {
    const radius = 16
    const circumference = 2 * Math.PI * radius
    render(<ProgressRing progress={0} radius={radius} />)
    const arc = screen.getByTestId('progress-ring-arc')
    const offset = parseFloat(arc.getAttribute('stroke-dashoffset') ?? '0')
    expect(offset).toBeCloseTo(circumference, 1)
  })

  it('renders 100% correctly — dashoffset is 0', () => {
    render(<ProgressRing progress={1} />)
    const arc = screen.getByTestId('progress-ring-arc')
    const offset = parseFloat(arc.getAttribute('stroke-dashoffset') ?? '999')
    expect(offset).toBeCloseTo(0, 1)
  })

  it('renders 50% with dashoffset ≈ half circumference', () => {
    const radius = 16
    const circumference = 2 * Math.PI * radius
    render(<ProgressRing progress={0.5} radius={radius} />)
    const arc = screen.getByTestId('progress-ring-arc')
    const offset = parseFloat(arc.getAttribute('stroke-dashoffset') ?? '0')
    expect(offset).toBeCloseTo(circumference / 2, 0)
  })

  it('clamps values < 0 to 0%', () => {
    const radius = 16
    const circumference = 2 * Math.PI * radius
    render(<ProgressRing progress={-0.5} radius={radius} />)
    const arc = screen.getByTestId('progress-ring-arc')
    const offset = parseFloat(arc.getAttribute('stroke-dashoffset') ?? '0')
    expect(offset).toBeCloseTo(circumference, 1)
  })

  it('clamps values > 1 to 100%', () => {
    render(<ProgressRing progress={1.5} />)
    const arc = screen.getByTestId('progress-ring-arc')
    const offset = parseFloat(arc.getAttribute('stroke-dashoffset') ?? '999')
    expect(offset).toBeCloseTo(0, 1)
  })

  it('shows percentage text centered', () => {
    render(<ProgressRing progress={0.75} />)
    const svg = screen.getByTestId('progress-ring')
    const texts = svg.querySelectorAll('text')
    expect(texts.length).toBe(1)
    expect(texts[0].textContent).toBe('75%')
  })

  it('shows 0% text at 0 progress', () => {
    render(<ProgressRing progress={0} />)
    const svg = screen.getByTestId('progress-ring')
    expect(svg.querySelector('text')?.textContent).toBe('0%')
  })

  it('has CSS transition class on the arc for smooth animation', () => {
    render(<ProgressRing progress={0.5} />)
    const arc = screen.getByTestId('progress-ring-arc')
    const style = arc.getAttribute('style') ?? ''
    expect(style).toContain('transition')
    expect(style).toContain('stroke-dashoffset')
  })

  it('accepts custom radius prop', () => {
    render(<ProgressRing progress={0.3} radius={24} strokeWidth={4} />)
    const svg = screen.getByTestId('progress-ring')
    // SVG size should be (radius + strokeWidth) * 2 = 56
    expect(svg.getAttribute('width')).toBe('56')
    expect(svg.getAttribute('height')).toBe('56')
  })

  it('has proper aria attributes for accessibility', () => {
    render(<ProgressRing progress={0.6} />)
    const svg = screen.getByRole('progressbar')
    expect(svg.getAttribute('aria-valuenow')).toBe('60')
    expect(svg.getAttribute('aria-valuemin')).toBe('0')
    expect(svg.getAttribute('aria-valuemax')).toBe('100')
  })

  it('updates dashoffset when progress prop changes', () => {
    const radius = 16
    const circumference = 2 * Math.PI * radius
    const { rerender } = render(<ProgressRing progress={0.2} radius={radius} />)
    const arc1 = screen.getByTestId('progress-ring-arc')
    const offset1 = parseFloat(arc1.getAttribute('stroke-dashoffset') ?? '0')
    expect(offset1).toBeCloseTo(circumference * 0.8, 0)

    rerender(<ProgressRing progress={0.8} radius={radius} />)
    const arc2 = screen.getByTestId('progress-ring-arc')
    const offset2 = parseFloat(arc2.getAttribute('stroke-dashoffset') ?? '0')
    expect(offset2).toBeCloseTo(circumference * 0.2, 0)
  })
})
