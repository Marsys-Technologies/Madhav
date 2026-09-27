/**
 * RosterTableView — minimal Jātaka directory table (Jātaka chart workspace, Task 2).
 *
 * Each row opens the chart workspace through one accessible name link. There
 * is no Actions column and no placeholder Current dasha column.
 */
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'

vi.mock('next/link', () => ({
  default: ({ href, children, ...rest }: { href: string; children: React.ReactNode } & Record<string, unknown>) => (
    <a href={href} {...rest}>{children}</a>
  ),
}))
vi.mock('@/lib/utils/date', () => ({
  formatDate: (d: string | null) => d ?? '—',
}))

import { RosterTableView } from '../RosterTableView'
import type { ChartWithMeta } from '@/lib/roster/types'

function makeChart(overrides: Partial<ChartWithMeta> = {}): ChartWithMeta {
  return {
    id: 'chart-xyz',
    client_id: 'c1',
    owner_id: 'o1',
    native_id: 'n1',
    name: 'Roster Chart',
    birth_date: '1984-02-05',
    birth_time: '10:43',
    birth_place: 'Bhubaneswar',
    birth_lat: null,
    birth_lng: null,
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
    layerPips: [],
    canBuild: true,
    ...overrides,
  }
}

describe('RosterTableView — minimal directory contract', () => {
  it('has exactly the truthful roster columns', () => {
    render(<RosterTableView charts={[makeChart()]} />)
    const headers = screen.getAllByRole('columnheader').map((h) => h.textContent?.replace(/[↑↓]/g, '').trim())
    expect(headers).toEqual(['Name', 'Birth details', 'Build', 'Last activity'])
    expect(screen.queryByRole('columnheader', { name: 'Actions' })).not.toBeInTheDocument()
    expect(screen.queryByRole('columnheader', { name: /current dasha/i })).not.toBeInTheDocument()
  })

  it('makes each chart name the row link to its workspace', () => {
    render(<RosterTableView charts={[makeChart()]} />)
    expect(screen.getByRole('link', { name: 'Roster Chart' })).toHaveAttribute('href', '/clients/chart-xyz')
  })

  it('renders no Nirmāṇa or Paripraśna actions for owners or grantees', () => {
    const charts = [
      makeChart({ id: 'owner-chart', name: 'Owner Chart', canBuild: true }),
      makeChart({ id: 'granted-chart', name: 'Granted Chart', canBuild: false }),
    ]
    render(<RosterTableView charts={charts} />)
    expect(screen.queryByText('Nirmāṇa')).not.toBeInTheDocument()
    expect(screen.queryByText(/pariprashna|paripraśna/i)).not.toBeInTheDocument()
    const links = screen.getAllByRole('link')
    expect(links.map((l) => l.getAttribute('href')).sort()).toEqual(['/clients/granted-chart', '/clients/owner-chart'])
  })

  it('shows the shared readiness label beside the build percentage', () => {
    render(
      <RosterTableView
        charts={[
          makeChart({
            pyramidPercent: 33,
            readiness: {
              state: 'partially-built',
              percent: 33,
              label: 'Partially built',
              layerPips: [],
              lastActivity: null,
              activeRunId: null,
              latestRunId: null,
              latestError: null,
            },
          }),
        ]}
      />,
    )
    expect(screen.getByText('33%')).toBeInTheDocument()
    expect(screen.getByText('Partially built')).toBeInTheDocument()
  })
})
