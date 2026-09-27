/**
 * ClientCard — minimal Jātaka directory card (Jātaka chart workspace, Task 2).
 *
 * The card is one semantic link to the chart workspace. It carries only the
 * name, a quiet birth line and the shared readiness bar/label. Nirmāṇa,
 * Paripraśna, edit and delete live in the workspace, never on the card.
 */
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'

vi.mock('next/link', () => ({
  default: ({ href, children, ...rest }: { href: string; children: React.ReactNode } & Record<string, unknown>) => (
    <a href={href} {...rest}>{children}</a>
  ),
}))
vi.mock('@/components/dialogs/DeleteChartDialog', () => ({
  DeleteChartDialog: () => null,
}))
vi.mock('@/lib/utils/date', () => ({
  formatDate: (d: string | null) => d ?? '—',
}))

import { ClientCard } from '../ClientCard'
import type { ChartWithMeta } from '@/lib/roster/types'

const BASE_CHART: ChartWithMeta = {
  id: 'chart-abc',
  client_id: 'client-uid',
  owner_id: 'owner-uid',
  native_id: 'nat-1',
  name: 'Test Chart',
  birth_date: '1984-02-05',
  birth_time: '10:43',
  birth_place: 'Bhubaneswar',
  birth_lat: 20.29,
  birth_lng: 85.82,
  ayanamsa: 'lahiri',
  house_system: 'whole_sign',
  created_at: '2026-01-01T00:00:00Z',
  readiness: {
    state: 'not-built',
    percent: 0,
    label: 'Not built',
    layerPips: [],
    lastActivity: null,
    activeRunId: null,
    latestRunId: null,
    latestError: null,
  },
  pyramidPercent: 0,
  lastLayerActivity: null,
  buildState: null,
  layerPips: [
    { layer: 'brahmagyan', state: 'lit' },
    { layer: 'ganita', state: 'dim' },
    { layer: 'bodha', state: 'dim' },
    { layer: 'kala', state: 'dim' },
    { layer: 'phala', state: 'dim' },
    { layer: 'mimamsa', state: 'dim' },
  ],
  canBuild: true,
}

function withReadiness(state: ChartWithMeta['readiness']['state'], label: string, percent: number): ChartWithMeta {
  return { ...BASE_CHART, readiness: { ...BASE_CHART.readiness, state, label, percent } }
}

describe('ClientCard — minimal directory contract', () => {
  it('renders exactly one link, to the chart workspace', () => {
    render(<ClientCard chart={BASE_CHART} />)
    const links = screen.getAllByRole('link')
    expect(links).toHaveLength(1)
    expect(links[0]).toHaveAttribute('href', '/clients/chart-abc')
  })

  it('renders no direct actions, overflow controls or nested interactive targets', () => {
    const { container } = render(<ClientCard chart={BASE_CHART} />)
    expect(screen.queryByText('Nirmāṇa')).not.toBeInTheDocument()
    expect(screen.queryByText('Paripraśna')).not.toBeInTheDocument()
    expect(screen.queryByText(/pariprashna/i)).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /more actions/i })).not.toBeInTheDocument()
    expect(screen.queryAllByRole('button')).toHaveLength(0)
    expect(container.querySelectorAll('a a, a button, a input, a [tabindex]')).toHaveLength(0)
  })

  it('shows the name, one birth line and the shared readiness', () => {
    render(<ClientCard chart={withReadiness('partially-built', 'Partially built', 33)} />)
    expect(screen.getByText(BASE_CHART.name)).toBeInTheDocument()
    expect(screen.getByText('1984-02-05 · Bhubaneswar')).toBeInTheDocument()
    const bar = screen.getByLabelText(/readiness/i)
    expect(bar).toHaveAttribute('role', 'progressbar')
    expect(bar).toHaveAttribute('aria-valuenow', '33')
    expect(screen.getByText(/Partially built/)).toBeInTheDocument()
  })

  it('gives the link a descriptive accessible name carrying the readiness label', () => {
    render(<ClientCard chart={withReadiness('needs-rebuild', 'Needs rebuild', 0)} />)
    expect(screen.getByRole('link', { name: 'Open Test Chart Jātaka — Needs rebuild' })).toBeInTheDocument()
  })

  it('has a visible keyboard focus treatment', () => {
    render(<ClientCard chart={BASE_CHART} />)
    expect(screen.getByRole('link').className).toMatch(/focus-visible:ring/)
  })

  it('renders the same view for owners and view-only grantees', () => {
    const owner = render(<ClientCard chart={{ ...BASE_CHART, canBuild: true }} />)
    const ownerHtml = owner.container.innerHTML
    owner.unmount()
    const grantee = render(<ClientCard chart={{ ...BASE_CHART, canBuild: false }} />)
    expect(grantee.container.innerHTML).toBe(ownerHtml)
  })
})
