/**
 * Mount integration test for ConstellationCanvas — H-01 scaffold.
 *
 * Asserts:
 *   - Component renders without crash
 *   - data-testid="constellation-canvas" is present
 *   - chartId prop (string) is accepted
 */

import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import ConstellationCanvas from '../ConstellationCanvas'

describe('ConstellationCanvas — scaffold mount', () => {
  it('renders without crash', () => {
    expect(() => render(<ConstellationCanvas chartId="chart-abc" />)).not.toThrow()
  })

  it('has data-testid="constellation-canvas"', () => {
    render(<ConstellationCanvas chartId="chart-abc" />)
    expect(screen.getByTestId('constellation-canvas')).toBeInTheDocument()
  })

  it('accepts chartId as string prop', () => {
    render(<ConstellationCanvas chartId="chart-xyz" />)
    const el = screen.getByTestId('constellation-canvas')
    expect(el).toBeInTheDocument()
  })

  it('renders heading text', () => {
    render(<ConstellationCanvas chartId="chart-abc" />)
    expect(screen.getByText('Build Constellation')).toBeInTheDocument()
  })
})
