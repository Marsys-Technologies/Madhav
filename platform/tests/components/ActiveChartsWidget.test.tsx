import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'

// Mock getActiveCharts so the component doesn't hit the DB.
vi.mock('@/lib/build/dataSource', () => ({
  getActiveCharts: vi.fn(),
}))

// Mock next/link as a plain anchor.
vi.mock('next/link', () => ({
  default: ({ href, children, ...props }: React.AnchorHTMLAttributes<HTMLAnchorElement> & { href: string }) => (
    <a href={href} {...props}>{children}</a>
  ),
}))

import { getActiveCharts } from '@/lib/build/dataSource'
import { ActiveChartsWidget } from '@/components/build/ActiveChartsWidget'
import type { ActiveChartEntry } from '@/lib/build/dataSource'

const FIXTURE: ActiveChartEntry[] = [
  { id: 'c1', client_id: 'cl1', name: 'Abhisek Mohanty', build_pct: 72, last_activity: new Date(Date.now() - 2 * 86_400_000).toISOString(), health: 'green' },
  { id: 'c2', client_id: 'cl2', name: 'Priya Sharma',    build_pct: 35, last_activity: new Date(Date.now() - 15 * 86_400_000).toISOString(), health: 'amber' },
  { id: 'c3', client_id: 'cl3', name: 'Rahul Gupta',     build_pct: 0,  last_activity: null, health: 'red' },
  { id: 'c4', client_id: 'cl4', name: 'Ananya Nair',     build_pct: 90, last_activity: new Date(Date.now() - 1 * 86_400_000).toISOString(), health: 'green' },
  { id: 'c5', client_id: 'cl5', name: 'Vikram Patel',    build_pct: 55, last_activity: new Date(Date.now() - 8 * 86_400_000).toISOString(), health: 'amber' },
]

const mockedGetActiveCharts = vi.mocked(getActiveCharts)

describe('ActiveChartsWidget', () => {
  beforeEach(() => {
    mockedGetActiveCharts.mockResolvedValue(FIXTURE)
  })

  it('renders heading and all 5 chart rows', async () => {
    const jsx = await ActiveChartsWidget()
    render(jsx)
    expect(screen.getByText('Active charts')).toBeTruthy()
    expect(screen.getAllByRole('listitem')).toHaveLength(5)
  })

  it('renders chart names', async () => {
    render(await ActiveChartsWidget())
    expect(screen.getByText('Abhisek Mohanty')).toBeTruthy()
    expect(screen.getByText('Priya Sharma')).toBeTruthy()
  })

  it('first row links to /clients/{client_id}', async () => {
    render(await ActiveChartsWidget())
    const link = screen.getByRole('link', { name: /Abhisek Mohanty/i })
    expect(link.getAttribute('href')).toBe('/clients/cl1')
  })

  it('shows build percentage text for each row', async () => {
    render(await ActiveChartsWidget())
    expect(screen.getByText('72%')).toBeTruthy()
    expect(screen.getByText('35%')).toBeTruthy()
  })

  it('renders empty state when no charts returned', async () => {
    mockedGetActiveCharts.mockResolvedValueOnce([])
    render(await ActiveChartsWidget())
    expect(screen.getByText('No charts yet.')).toBeTruthy()
  })

  it('renders health dot with aria-label for first row', async () => {
    render(await ActiveChartsWidget())
    const dots = screen.getAllByLabelText(/Health:/)
    expect(dots[0].getAttribute('aria-label')).toBe('Health: green')
  })
})
