import { render, screen, within } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

vi.mock('next/navigation', () => ({
  usePathname: () => '/cockpit',
  useRouter: () => ({ refresh: vi.fn() }),
}))

import { BuildHeader } from '../BuildHeader'

describe('BuildHeader navigation', () => {
  it('places AI Console immediately before Observatory when the feature is enabled', () => {
    render(<BuildHeader showAiConsole />)

    const navigation = screen.getByRole('navigation')
    const headings = within(navigation).getAllByRole('link').map((link) => link.textContent)
    expect(headings).toEqual(['AI Console', 'Observatory'])
  })

  it('keeps the feature-gated link hidden while retaining Observatory', () => {
    render(<BuildHeader showAiConsole={false} />)

    const navigation = screen.getByRole('navigation')
    expect(within(navigation).queryByRole('link', { name: 'AI Console' })).not.toBeInTheDocument()
    const observatory = within(navigation).getByRole('link', { name: 'Observatory' })
    expect(observatory).toHaveAttribute('href', '/observatory')
  })
})
