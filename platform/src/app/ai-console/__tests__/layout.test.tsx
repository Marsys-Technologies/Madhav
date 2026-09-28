import { beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'

const mocks = vi.hoisted(() => ({
  auth: vi.fn(), flag: vi.fn(), redirect: vi.fn((path: string) => { throw new Error(`redirect:${path}`) }),
  notFound: vi.fn(() => { throw new Error('not-found') }),
}))

vi.mock('@/lib/auth/access-control', () => ({ getServerUserWithProfile: mocks.auth }))
vi.mock('@/lib/config', () => ({ getFlag: mocks.flag }))
vi.mock('next/navigation', () => ({ redirect: mocks.redirect, notFound: mocks.notFound }))
vi.mock('@/components/shared/AppShell', () => ({ AppShell: ({ children, breadcrumb }: { children: React.ReactNode; breadcrumb: Array<{ label: string }> }) => <main data-breadcrumb={breadcrumb.map(item => item.label).join(' > ')}>{children}</main> }))
vi.mock('@/components/build/BuildHeader', () => ({ BuildHeader: () => <nav aria-label="Cockpit sections">AI Console Observatory</nav> }))
vi.mock('@/components/shared/ZoneRoot', () => ({ ZoneRoot: ({ children }: { children: React.ReactNode }) => <div>{children}</div> }))

import AiConsoleLayout from '../layout'

describe('AI Console layout gate', () => {
  beforeEach(() => { vi.clearAllMocks(); mocks.flag.mockReturnValue(true); mocks.auth.mockResolvedValue({ user: { uid: 'u1' }, profile: { role: 'guest', status: 'active' } }) })

  it('renders active guests in AppShell with the AI Console breadcrumb', async () => {
    render(await AiConsoleLayout({ children: <p>console</p> }))
    expect(screen.getByRole('main').getAttribute('data-breadcrumb')).toBe('AI Console')
    expect(screen.queryByRole('navigation', { name: 'Cockpit sections' })).not.toBeInTheDocument()
  })

  it('nests the SuperAdmin surface under Cockpit', async () => {
    mocks.auth.mockResolvedValueOnce({ user: { uid: 'u1' }, profile: { role: 'super_admin', status: 'active' } })
    render(await AiConsoleLayout({ children: <p>console</p> }))
    expect(screen.getByRole('main').getAttribute('data-breadcrumb')).toBe('Cockpit > AI Console')
    expect(screen.getByRole('navigation', { name: 'Cockpit sections' })).toBeInTheDocument()
  })

  it('redirects absent and inactive users to login', async () => {
    mocks.auth.mockResolvedValueOnce(null)
    await expect(AiConsoleLayout({ children: null })).rejects.toThrow('redirect:/login')
    mocks.auth.mockResolvedValueOnce({ user: { uid: 'u1' }, profile: { role: 'guest', status: 'disabled' } })
    await expect(AiConsoleLayout({ children: null })).rejects.toThrow('redirect:/login')
  })

  it('returns route not-found while the server feature flag is off', async () => {
    mocks.flag.mockReturnValue(false)
    await expect(AiConsoleLayout({ children: null })).rejects.toThrow('not-found')
  })
})
