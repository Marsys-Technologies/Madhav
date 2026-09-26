import { render, screen, within } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

vi.mock('next/navigation', () => ({
  usePathname: () => '/cockpit',
  useRouter: () => ({ refresh: vi.fn() }),
}))

import { BuildHeader } from '../BuildHeader'

describe('BuildHeader navigation', () => {
  it('keeps Observatory as the only Cockpit section heading', () => {
    render(<BuildHeader />)

    const navigation = screen.getByRole('navigation')
    const headings = within(navigation).getAllByRole('link').map((link) => link.textContent)
    expect(headings).toEqual(['Observatory'])
  })

  it('offers Observatory as a Cockpit heading', () => {
    render(<BuildHeader />)

    const navigation = screen.getByRole('navigation')
    const observatory = within(navigation).getByRole('link', { name: 'Observatory' })
    expect(observatory).toHaveAttribute('href', '/observatory')
  })
})
