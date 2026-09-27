import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import type { ChartReadiness, ChartReadinessState } from '@/lib/charts/readiness'

vi.mock('next/link', () => ({
  default: ({ href, children, ...rest }: { href: string; children: React.ReactNode } & Record<string, unknown>) => (
    <a href={href} {...rest}>{children}</a>
  ),
}))

import { ChartReadinessBand } from '../ChartReadinessBand'

const LABELS: Record<ChartReadinessState, string> = {
  'not-built': 'Not built',
  building: 'Building',
  'partially-built': 'Partially built',
  ready: 'Ready',
  failed: 'Failed',
  'needs-rebuild': 'Needs rebuild',
}

function fixture(overrides: Partial<ChartReadiness> & { state: ChartReadinessState }): ChartReadiness {
  return {
    percent: 0,
    label: LABELS[overrides.state],
    layerPips: [
      { layer: 'brahmagyan', state: 'lit' },
      { layer: 'ganita', state: 'lit' },
      { layer: 'bodha', state: 'building' },
      { layer: 'kala', state: 'dim' },
      { layer: 'phala', state: 'dim' },
      { layer: 'mimamsa', state: 'dim' },
    ],
    lastActivity: null,
    activeRunId: null,
    latestRunId: null,
    latestError: null,
    ...overrides,
  }
}

describe('ChartReadinessBand', () => {
  it('shows Needs rebuild with a zero progressbar and retry copy', () => {
    render(<ChartReadinessBand readiness={fixture({ state: 'needs-rebuild' })} />)
    expect(screen.getByText('Needs rebuild')).toBeInTheDocument()
    expect(screen.getByText('Gaṇita')).toBeInTheDocument()
    expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '0')
    expect(screen.getByText(/retry in nirmāṇa/i)).toBeInTheDocument()
  })

  it('links the retry path to Nirmāṇa only for users who can build', () => {
    const { unmount } = render(
      <ChartReadinessBand readiness={fixture({ state: 'needs-rebuild' })} chartId="c1" canBuild />,
    )
    expect(screen.getByRole('link', { name: /retry in nirmāṇa/i })).toHaveAttribute('href', '/clients/c1/nirmana')
    unmount()
    render(<ChartReadinessBand readiness={fixture({ state: 'needs-rebuild' })} chartId="c1" canBuild={false} />)
    expect(screen.queryByRole('link')).not.toBeInTheDocument()
    expect(screen.getByText(/retry in nirmāṇa/i)).toBeInTheDocument()
  })

  it.each(Object.entries(LABELS))('renders the %s state label as text', (state, label) => {
    render(<ChartReadinessBand readiness={fixture({ state: state as ChartReadinessState, percent: 50 })} />)
    expect(screen.getByText(label)).toBeInTheDocument()
    expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '50')
  })

  it('names all six Brahma layers and states each layer in text, not colour alone', () => {
    render(<ChartReadinessBand readiness={fixture({ state: 'building' })} />)
    for (const name of ['Brahmagyan', 'Gaṇita', 'Bodha', 'Kāla', 'Phala', 'Mīmāṃsā']) {
      expect(screen.getByText(name)).toBeInTheDocument()
    }
    expect(screen.getByLabelText('Gaṇita: built')).toBeInTheDocument()
    expect(screen.getByLabelText('Bodha: building')).toBeInTheDocument()
    expect(screen.getByLabelText('Kāla: not built')).toBeInTheDocument()
  })

  it('shows active run context while building', () => {
    render(<ChartReadinessBand readiness={fixture({ state: 'building', activeRunId: 'abcdef12-3456' })} />)
    expect(screen.getByText(/build run abcdef12 in progress/i)).toBeInTheDocument()
  })

  it('shows last activity when available', () => {
    render(<ChartReadinessBand readiness={fixture({ state: 'ready', lastActivity: '2026-09-05T10:00:00Z' })} />)
    expect(screen.getByText(/last built/i)).toBeInTheDocument()
  })

  it('does not print raw error text for an ordinary failure', () => {
    render(<ChartReadinessBand readiness={fixture({ state: 'failed', latestError: 'psycopg.errors.X at line 9' })} />)
    expect(screen.queryByText(/psycopg/)).not.toBeInTheDocument()
  })
})
