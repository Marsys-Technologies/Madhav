/**
 * RosterTableView — Nirmāṇa affordance access control (Phase 2B).
 *
 * When canBuild=true  → Nirmāṇa renders as a navigable link.
 * When canBuild=false → Nirmāṇa renders as a disabled button.
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
    pyramidPercent: 0,
    lastLayerActivity: null,
    buildState: null,
    layerPips: [],
    canBuild: true,
    ...overrides,
  }
}

describe('RosterTableView — Nirmāṇa affordance (Phase 2B canBuild gate)', () => {
  it('canBuild=true → Nirmāṇa is a link', () => {
    render(<RosterTableView charts={[makeChart({ canBuild: true })]} />)
    const link = screen.getByRole('link', { name: /nirmāṇa \(build\)/i })
    expect(link).toBeTruthy()
    expect((link as HTMLAnchorElement).href).toContain('/clients/chart-xyz/nirmana')
    expect(screen.queryByTestId('nirmana-disabled')).toBeNull()
  })

  it('canBuild=false → Nirmāṇa is a disabled button with tooltip', () => {
    render(<RosterTableView charts={[makeChart({ canBuild: false })]} />)
    const btn = screen.getByTestId('nirmana-disabled')
    expect(btn.tagName).toBe('BUTTON')
    expect(btn).toHaveAttribute('disabled')
    expect(btn).toHaveAttribute('title', 'View-only — build restricted')
    const links = screen.getAllByRole('link')
    const nirmanaLink = links.find((el) => (el as HTMLAnchorElement).href?.includes('nirmana'))
    expect(nirmanaLink).toBeUndefined()
  })

  it('canBuild=false → Pariprashna link still present', () => {
    render(<RosterTableView charts={[makeChart({ canBuild: false })]} />)
    const link = screen.getByRole('link', { name: /pariprashna \(consult\)/i })
    expect(link).toBeTruthy()
  })

  it('mixed roster — owner canBuild=true, grantee canBuild=false', () => {
    const charts = [
      makeChart({ id: 'owner-chart', name: 'Owner Chart', canBuild: true }),
      makeChart({ id: 'granted-chart', name: 'Granted Chart', canBuild: false }),
    ]
    render(<RosterTableView charts={charts} />)
    const disabledBtns = screen.getAllByTestId('nirmana-disabled')
    expect(disabledBtns).toHaveLength(1)
    const nirmanaLinks = screen.getAllByRole('link').filter(
      (el) => (el as HTMLAnchorElement).href?.includes('nirmana')
    )
    expect(nirmanaLinks).toHaveLength(1)
    expect((nirmanaLinks[0] as HTMLAnchorElement).href).toContain('owner-chart')
  })
})
