import { beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ClientRoster } from '../ClientRoster'
import type { ChartWithMeta } from '@/lib/roster/types'

const { useSearchParams } = vi.hoisted(() => ({ useSearchParams: vi.fn() }))

vi.mock('next/navigation', () => ({
  useRouter: () => ({ replace: vi.fn() }),
  usePathname: () => '/dashboard',
  useSearchParams,
}))

const chart: ChartWithMeta = {
  id: 'q1-chart',
  client_id: 'q1-admin',
  owner_id: 'q1-admin',
  native_id: 'q1-native',
  name: 'Fictional Chart',
  birth_date: '1992-04-03',
  birth_time: '09:30',
  birth_place: 'Cuttack',
  birth_lat: null,
  birth_lng: null,
  ayanamsa: 'lahiri',
  house_system: 'whole_sign',
  created_at: '2026-11-10T00:00:00Z',
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
  canBuild: false,
}

const emptyStats = {
  total: 0,
  inActiveBuild: 0,
  consumedToday: 0,
  predictionsOverdue: 0,
}

describe('ClientRoster empty states', () => {
  beforeEach(() => {
    useSearchParams.mockReturnValue(new URLSearchParams())
  })

  it('tells an empty guest to ask an administrator for chart access', () => {
    render(<ClientRoster charts={[]} stats={emptyStats} canCreateChart={false} />)

    expect(screen.getByRole('heading', { name: 'No charts available' })).toBeInTheDocument()
    expect(screen.getByText(/ask a madhav administrator to share a chart with you/i)).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: /add first chart/i })).not.toBeInTheDocument()
  })

  it('keeps the first-chart creation link for an administrator', () => {
    render(<ClientRoster charts={[]} stats={emptyStats} canCreateChart />)

    expect(screen.getByRole('link', { name: /add first chart/i })).toHaveAttribute('href', '/clients/new')
  })

  it('keeps the no-matches state for a guest whose chart was filtered out', () => {
    useSearchParams.mockReturnValue(new URLSearchParams('q=missing'))
    render(<ClientRoster charts={[chart]} stats={{ ...emptyStats, total: 1 }} canCreateChart={false} />)

    expect(screen.getByText('No charts match the current filters.')).toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: 'No charts available' })).not.toBeInTheDocument()
  })
})
