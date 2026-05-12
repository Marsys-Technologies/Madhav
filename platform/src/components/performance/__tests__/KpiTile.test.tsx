import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'

import { KpiTile } from '../KpiTile'

// recharts ResponsiveContainer needs explicit width/height in jsdom; stub it.
vi.mock('recharts', async () => {
  const actual = await vi.importActual<typeof import('recharts')>('recharts')
  return {
    ...actual,
    ResponsiveContainer: ({ children }: { children: React.ReactNode }) => (
      <div style={{ width: 200, height: 50 }}>{children}</div>
    ),
  }
})

describe('KpiTile', () => {
  const baseProps = {
    bundle: 'pipeline_correctness' as const,
    title: 'Pipeline correctness',
    description: 'Plan accuracy + citations.',
    headline: { label: 'recall', value: '97.0%' },
    secondary: [
      { label: 'precision', value: '95.0%' },
      { label: 'n', value: '42' },
    ],
    sparkline: [
      { t: '2026-05-01T00:00:00Z', v: 0.95 },
      { t: '2026-05-02T00:00:00Z', v: 0.97 },
    ],
  }

  it('renders the headline value, label, and secondary metrics', () => {
    render(<KpiTile {...baseProps} delta={null} />)
    expect(screen.getByText('Pipeline correctness')).toBeInTheDocument()
    expect(screen.getByText('97.0%')).toBeInTheDocument()
    expect(screen.getByText('recall')).toBeInTheDocument()
    expect(screen.getByText('95.0%')).toBeInTheDocument()
  })

  it('renders a green arrow for positive delta', () => {
    render(<KpiTile {...baseProps} delta={0.05} />)
    const arrow = screen.getByLabelText(/better/i)
    expect(arrow).toHaveTextContent('↑')
    expect(arrow.className).toContain('emerald')
  })

  it('renders a red arrow for negative delta', () => {
    render(<KpiTile {...baseProps} delta={-0.05} />)
    const arrow = screen.getByLabelText(/worse/i)
    expect(arrow).toHaveTextContent('↓')
    expect(arrow.className).toContain('rose')
  })

  it('renders an em-dash arrow when delta is null (insufficient data)', () => {
    render(<KpiTile {...baseProps} delta={null} />)
    const arrow = screen.getByLabelText(/no comparison/i)
    expect(arrow).toHaveTextContent('—')
  })

  it('shows an empty-state message when sparkline is empty', () => {
    render(<KpiTile {...baseProps} delta={null} sparkline={[]} />)
    expect(screen.getByText(/no data in window/i)).toBeInTheDocument()
  })
})
