import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { OverallProgress } from '../OverallProgress'

const BASE_PER_AYA = [
  { id: 'lahiri', complete: 10, total: 28 },
  { id: 'raman',  complete: 5,  total: 28 },
  { id: 'kp',     complete: 8,  total: 28 },
]

describe('OverallProgress', () => {
  it('renders the component with data-testid overall-progress', () => {
    render(<OverallProgress totalNodes={140} completeNodes={47} perAyanamsha={[]} />)
    expect(screen.getByTestId('overall-progress')).toBeTruthy()
  })

  it('renders the Sampurna gati label', () => {
    render(<OverallProgress totalNodes={140} completeNodes={47} perAyanamsha={[]} />)
    expect(screen.getByTestId('overall-progress-label').textContent).toContain('Sampurna gati')
  })

  it('renders complete/total node count', () => {
    render(<OverallProgress totalNodes={140} completeNodes={47} perAyanamsha={[]} />)
    const stats = screen.getByTestId('overall-progress-stats')
    expect(stats.textContent).toContain('47')
    expect(stats.textContent).toContain('140')
  })

  it('renders correct percentage (47/140 ≈ 33.6%)', () => {
    render(<OverallProgress totalNodes={140} completeNodes={47} perAyanamsha={[]} />)
    const stats = screen.getByTestId('overall-progress-stats')
    expect(stats.textContent).toContain('33.6%')
  })

  it('renders ETA when provided', () => {
    render(<OverallProgress totalNodes={140} completeNodes={47} etaSeconds={702} perAyanamsha={[]} />)
    const stats = screen.getByTestId('overall-progress-stats')
    expect(stats.textContent).toContain('ETA')
    expect(stats.textContent).toContain('11m')
  })

  it('does not render ETA when undefined', () => {
    render(<OverallProgress totalNodes={140} completeNodes={47} perAyanamsha={[]} />)
    const stats = screen.getByTestId('overall-progress-stats')
    expect(stats.textContent).not.toContain('ETA')
  })

  it('renders progress track and fill', () => {
    render(<OverallProgress totalNodes={140} completeNodes={70} perAyanamsha={[]} />)
    expect(screen.getByTestId('overall-progress-track')).toBeTruthy()
    const fill = screen.getByTestId('overall-progress-fill')
    const style = fill.getAttribute('style') ?? ''
    expect(style).toContain('width')
    // 70/140 = 50% — React normalises trailing zeros in inline styles
    expect(style).toMatch(/width:\s*50/)
  })

  it('renders 0% fill at 0 complete nodes', () => {
    render(<OverallProgress totalNodes={140} completeNodes={0} perAyanamsha={[]} />)
    const fill = screen.getByTestId('overall-progress-fill')
    const style = fill.getAttribute('style') ?? ''
    expect(style).toMatch(/width:\s*0/)
  })

  it('caps fill at 100% when complete exceeds total', () => {
    render(<OverallProgress totalNodes={10} completeNodes={15} perAyanamsha={[]} />)
    const fill = screen.getByTestId('overall-progress-fill')
    const style = fill.getAttribute('style') ?? ''
    expect(style).toMatch(/width:\s*100/)
  })

  it('renders 100% when all nodes complete', () => {
    render(<OverallProgress totalNodes={140} completeNodes={140} perAyanamsha={[]} />)
    const fill = screen.getByTestId('overall-progress-fill')
    const style = fill.getAttribute('style') ?? ''
    expect(style).toMatch(/width:\s*100/)
  })

  it('fill has CSS transition for smooth animation', () => {
    render(<OverallProgress totalNodes={140} completeNodes={50} perAyanamsha={[]} />)
    const fill = screen.getByTestId('overall-progress-fill')
    expect(fill.getAttribute('style')).toContain('transition')
  })

  it('renders per-ayanamsha sub-counts', () => {
    render(<OverallProgress totalNodes={140} completeNodes={47} perAyanamsha={BASE_PER_AYA} />)
    expect(screen.getByTestId('per-ayanamsha-counts')).toBeTruthy()
    expect(screen.getByTestId('ayanamsha-count-lahiri')).toBeTruthy()
    expect(screen.getByTestId('ayanamsha-count-raman')).toBeTruthy()
    expect(screen.getByTestId('ayanamsha-count-kp')).toBeTruthy()
  })

  it('shows correct per-ayanamsha values', () => {
    render(<OverallProgress totalNodes={140} completeNodes={47} perAyanamsha={BASE_PER_AYA} />)
    const lahiri = screen.getByTestId('ayanamsha-count-lahiri')
    expect(lahiri.textContent).toContain('10')
    expect(lahiri.textContent).toContain('28')
  })

  it('does not render per-ayanamsha section when empty', () => {
    render(<OverallProgress totalNodes={140} completeNodes={47} perAyanamsha={[]} />)
    expect(screen.queryByTestId('per-ayanamsha-counts')).toBeNull()
  })

  it('handles zero totalNodes gracefully (no divide-by-zero)', () => {
    expect(() =>
      render(<OverallProgress totalNodes={0} completeNodes={0} perAyanamsha={[]} />)
    ).not.toThrow()
    const stats = screen.getByTestId('overall-progress-stats')
    expect(stats.textContent).toContain('0.0%')
  })

  it('updates on prop change', () => {
    const { rerender } = render(
      <OverallProgress totalNodes={140} completeNodes={20} perAyanamsha={[]} />
    )
    let stats = screen.getByTestId('overall-progress-stats')
    expect(stats.textContent).toContain('20')

    rerender(<OverallProgress totalNodes={140} completeNodes={80} perAyanamsha={[]} />)
    stats = screen.getByTestId('overall-progress-stats')
    expect(stats.textContent).toContain('80')
  })
})
