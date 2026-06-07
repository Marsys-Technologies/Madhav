import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, fireEvent } from '@testing-library/react'
import { AppShell } from '@/components/shared/AppShell'

// AppShellRail uses Next.js navigation hooks and Firebase — mock at module level.
vi.mock('next/navigation', () => ({
  usePathname: () => '/dashboard',
  useRouter: () => ({ push: vi.fn(), refresh: vi.fn() }),
}))

vi.mock('@/lib/firebase/client', () => ({
  auth: {},
}))

vi.mock('firebase/auth', () => ({
  signOut: vi.fn(),
}))

// Sigil is an SVG component — stub it out to avoid canvas/SVG setup.
vi.mock('@/components/brand/Sigil', () => ({
  Sigil: () => <svg data-testid="sigil" />,
}))

// Stub framer-motion — cache inside factory so React sees stable component identity
// across renders; avoids proxy returning a new reference on every access.
vi.mock('framer-motion', () => {
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  const React = require('react') as typeof import('react')
  const cache: Record<string, unknown> = {}
  const makeMotion = (tag: string) => {
    if (!cache[tag]) {
      cache[tag] = React.forwardRef(
        function Motion(
          { children, animate, initial, exit, transition, whileHover, layoutId, ...rest }:
            Record<string, unknown>,
          ref: unknown
        ) {
          void animate; void initial; void exit; void transition; void whileHover; void layoutId
          return React.createElement(tag as string, { ...(rest as object), ref }, children as React.ReactNode)
        }
      )
    }
    return cache[tag]
  }
  return {
    motion: new Proxy({}, { get: (_t, tag: string) => makeMotion(tag) }),
    AnimatePresence: ({ children }: { children: React.ReactNode }) =>
      React.createElement(React.Fragment, null, children),
    useReducedMotion: () => false,
  }
})

// Stub DropdownMenu primitives (Radix) — not needed for shell structure tests.
vi.mock('@/components/ui/dropdown-menu', () => ({
  DropdownMenu: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  DropdownMenuTrigger: ({ children, ...props }: React.HTMLAttributes<HTMLButtonElement>) => (
    <button {...props}>{children}</button>
  ),
  DropdownMenuContent: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  DropdownMenuSeparator: () => <hr />,
  DropdownMenuItem: ({ children, onClick }: { children: React.ReactNode; onClick?: () => void }) => (
    <button onClick={onClick}>{children}</button>
  ),
}))

const BASE_USER = { uid: 'u1', email: 'test@example.com' }
const BASE_PROFILE = { role: 'super_admin' as const }

describe('AppShell', () => {
  it('renders children inside main', () => {
    const { getByRole } = render(
      <AppShell user={BASE_USER} profile={BASE_PROFILE}>
        <p>page content</p>
      </AppShell>
    )
    expect(getByRole('main')).toBeTruthy()
    expect(getByRole('main').textContent).toContain('page content')
  })

  it('renders primary navigation rail', () => {
    const { getByRole } = render(
      <AppShell user={BASE_USER} profile={BASE_PROFILE} />
    )
    expect(getByRole('navigation', { name: 'Primary navigation' })).toBeTruthy()
  })

  it('renders breadcrumb nav when segments provided', () => {
    const { getByRole } = render(
      <AppShell
        user={BASE_USER}
        profile={BASE_PROFILE}
        breadcrumb={[{ label: 'Roster', current: true }]}
      />
    )
    expect(getByRole('navigation', { name: 'Breadcrumb' })).toBeTruthy()
  })

  it('omits breadcrumb nav when no segments', () => {
    const { queryByRole } = render(
      <AppShell user={BASE_USER} profile={BASE_PROFILE} breadcrumb={[]} />
    )
    expect(queryByRole('navigation', { name: 'Breadcrumb' })).toBeNull()
  })

  it('shows Jātakas nav link for all roles', () => {
    const { getByRole } = render(
      <AppShell user={BASE_USER} profile={{ role: 'client' }} />
    )
    expect(getByRole('link', { name: 'Jātakas' })).toBeTruthy()
  })

  it('shows Cockpit link for super_admin', () => {
    const { getByRole } = render(
      <AppShell user={BASE_USER} profile={{ role: 'super_admin' }} />
    )
    expect(getByRole('link', { name: 'Cockpit' })).toBeTruthy()
  })

  it('hides Cockpit link for client role', () => {
    const { container } = render(
      <AppShell user={BASE_USER} profile={{ role: 'client' }} />
    )
    const cockpitLink = container.querySelector('a[href="/cockpit"]')
    expect(cockpitLink).toBeNull()
  })

  it('displays user initial in avatar trigger', () => {
    const { getByRole } = render(
      <AppShell user={{ uid: 'u1', email: 'alice@example.com' }} profile={BASE_PROFILE} />
    )
    const trigger = getByRole('button', { name: 'User menu' })
    expect(trigger.textContent).toBe('A')
  })

  it('nav items have aria-label in collapsed state', () => {
    const { getByRole } = render(
      <AppShell user={BASE_USER} profile={BASE_PROFILE} />
    )
    expect(getByRole('link', { name: 'Jātakas' })).toBeTruthy()
    expect(getByRole('link', { name: 'Cockpit' })).toBeTruthy()
    expect(getByRole('link', { name: 'Audit' })).toBeTruthy()
  })

  it('shows nav labels when sidebar is hovered', () => {
    const { getByRole, getByText } = render(
      <AppShell user={BASE_USER} profile={BASE_PROFILE} />
    )
    const nav = getByRole('navigation', { name: 'Primary navigation' })
    fireEvent.mouseEnter(nav)
    expect(getByText('Jātakas')).toBeTruthy()
    expect(getByText('Cockpit')).toBeTruthy()
  })

  it('hides nav labels after sidebar hover ends', () => {
    const { getByRole, getByText, queryByText } = render(
      <AppShell user={BASE_USER} profile={BASE_PROFILE} />
    )
    const nav = getByRole('navigation', { name: 'Primary navigation' })
    fireEvent.mouseEnter(nav)
    expect(getByText('Jātakas')).toBeTruthy()  // confirm labels appeared
    fireEvent.mouseLeave(nav)
    expect(queryByText('Jātakas')).toBeNull()
  })

  it('shows full Performance label when expanded', () => {
    const { getByRole, getByText } = render(
      <AppShell user={BASE_USER} profile={BASE_PROFILE} />
    )
    const nav = getByRole('navigation', { name: 'Primary navigation' })
    fireEvent.mouseEnter(nav)
    expect(getByText('Performance')).toBeTruthy()
  })

  it('shows username in avatar row when expanded', () => {
    const { getByRole, getByText } = render(
      <AppShell
        user={{ uid: 'u1', email: 'test@example.com', name: 'Abhisek' }}
        profile={BASE_PROFILE}
      />
    )
    const nav = getByRole('navigation', { name: 'Primary navigation' })
    fireEvent.mouseEnter(nav)
    expect(getByText('Abhisek')).toBeTruthy()
  })
})
