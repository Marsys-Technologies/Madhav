import { describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen } from '@testing-library/react'

vi.mock('next/link', () => ({
  default: ({ href, children, ...rest }: { href: string; children: React.ReactNode } & Record<string, unknown>) => (
    <a href={href} {...rest}>{children}</a>
  ),
}))
vi.mock('next/navigation', () => ({ useRouter: () => ({ push: vi.fn(), refresh: vi.fn() }) }))
vi.mock('@/components/dialogs/DeleteChartDialog', () => ({
  DeleteChartDialog: ({ open, chartName }: { open: boolean; chartName: string }) =>
    open ? <div role="dialog" aria-label={`Delete ${chartName}`} /> : null,
}))

import { ChartActionsMenu } from '../ChartActionsMenu'

const BASE = { chartId: 'c1', chartName: 'Test Chart', canBuild: true, isSuperAdmin: false, canShare: false }

function open() {
  fireEvent.click(screen.getByRole('button', { name: /chart actions/i }))
}

describe('ChartActionsMenu', () => {
  it('is collapsed until opened and exposes its state', () => {
    render(<ChartActionsMenu {...BASE} />)
    const trigger = screen.getByRole('button', { name: /chart actions/i })
    expect(trigger).toHaveAttribute('aria-expanded', 'false')
    expect(screen.queryByRole('link', { name: /edit chart details/i })).not.toBeInTheDocument()
    open()
    expect(trigger).toHaveAttribute('aria-expanded', 'true')
  })

  it('offers Edit and a separated Delete to owners', () => {
    render(<ChartActionsMenu {...BASE} />)
    open()
    expect(screen.getByRole('link', { name: /edit chart details/i })).toHaveAttribute('href', '/clients/c1/edit')
    const del = screen.getByRole('button', { name: /delete chart/i })
    fireEvent.click(del)
    expect(screen.getByRole('dialog', { name: 'Delete Test Chart' })).toBeInTheDocument()
  })

  it('never gives a caller without build authority edit or delete controls', () => {
    render(<ChartActionsMenu {...BASE} canBuild={false} canShare />)
    open()
    expect(screen.getByRole('link', { name: /sharing/i })).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: /edit chart details/i })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /delete chart/i })).not.toBeInTheDocument()
  })

  it('renders nothing at all when the caller has no secondary action', () => {
    const { container } = render(<ChartActionsMenu {...BASE} canBuild={false} />)
    expect(container).toBeEmptyDOMElement()
  })

  it('shows Sharing only where authorised and Audit only for super admin', () => {
    const { unmount } = render(<ChartActionsMenu {...BASE} />)
    open()
    expect(screen.queryByRole('link', { name: /sharing/i })).not.toBeInTheDocument()
    expect(screen.queryByRole('link', { name: /audit/i })).not.toBeInTheDocument()
    unmount()
    render(<ChartActionsMenu {...BASE} canShare isSuperAdmin />)
    open()
    expect(screen.getByRole('link', { name: /sharing/i })).toHaveAttribute('href', '#sharing')
    expect(screen.getByRole('link', { name: /audit/i })).toHaveAttribute('href', '/cockpit/audit?chart=c1')
  })

  it('Escape closes the menu and returns focus to the trigger', () => {
    render(<ChartActionsMenu {...BASE} />)
    const trigger = screen.getByRole('button', { name: /chart actions/i })
    open()
    fireEvent.keyDown(screen.getByRole('link', { name: /edit chart details/i }), { key: 'Escape' })
    expect(trigger).toHaveAttribute('aria-expanded', 'false')
    expect(document.activeElement).toBe(trigger)
  })
})
