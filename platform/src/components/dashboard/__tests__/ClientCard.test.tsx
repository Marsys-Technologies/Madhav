/**
 * ClientCard — Nirmāṇa affordance access control (Phase 2B).
 *
 * When canBuild=true  → Nirmāṇa renders as a navigable link.
 * When canBuild=false → Nirmāṇa renders as a disabled button with
 *                       title="View-only — build restricted".
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

describe('ClientCard — Nirmāṇa affordance (Phase 2B canBuild gate)', () => {
  it('canBuild=true → Nirmāṇa is a link to /nirmana', () => {
    render(<ClientCard chart={{ ...BASE_CHART, canBuild: true }} />)
    const link = screen.getByRole('link', { name: /nirmāṇa \(build\)/i })
    expect(link).toBeTruthy()
    expect((link as HTMLAnchorElement).href).toContain('/clients/chart-abc/nirmana')
    expect(screen.queryByTestId('nirmana-disabled')).toBeNull()
  })

  it('canBuild=false → Nirmāṇa is a disabled button (not a link)', () => {
    render(<ClientCard chart={{ ...BASE_CHART, canBuild: false }} />)
    const btn = screen.getByTestId('nirmana-disabled')
    expect(btn.tagName).toBe('BUTTON')
    expect(btn).toHaveAttribute('disabled')
    expect(btn).toHaveAttribute('title', 'View-only — build restricted')
    // No navigable link for nirmana
    const links = screen.getAllByRole('link')
    const nirmanaLink = links.find((el) => (el as HTMLAnchorElement).href?.includes('nirmana'))
    expect(nirmanaLink).toBeUndefined()
  })

  it('canBuild=false → Pariprashna (consult) link is still present', () => {
    render(<ClientCard chart={{ ...BASE_CHART, canBuild: false }} />)
    const link = screen.getByRole('link', { name: /pariprashna \(consult\)/i })
    expect(link).toBeTruthy()
    expect((link as HTMLAnchorElement).href).toContain('/clients/chart-abc/pariprashna')
  })
})
