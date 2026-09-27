import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'

vi.mock('next/link', () => ({
  default: ({ href, children, ...rest }: { href: string; children: React.ReactNode } & Record<string, unknown>) => (
    <a href={href} {...rest}>{children}</a>
  ),
}))

import { CapabilityCard } from '../CapabilityCard'

describe('CapabilityCard', () => {
  it('an unavailable capability renders no link, an Unavailable state and the reason', () => {
    render(
      <CapabilityCard
        name="Paripraśna"
        description="Ask and explore this chart."
        href="/clients/c1/pariprashna"
        available={false}
        stateHint="Waiting for recomputation"
        reason="Chart recomputation is in progress."
      />,
    )
    expect(screen.queryByRole('link', { name: /paripraśna/i })).not.toBeInTheDocument()
    expect(screen.queryAllByRole('link')).toHaveLength(0)
    expect(screen.getByText('Chart recomputation is in progress.')).toBeInTheDocument()
    expect(screen.getByText('Unavailable')).toBeInTheDocument()
  })

  it('an available capability renders exactly one link with a 44px target', () => {
    render(
      <CapabilityCard
        name="Pañcāṅga"
        description="Personalised daily timing."
        href="/clients/c1/panchang"
        available
        stateHint="Today"
      />,
    )
    const links = screen.getAllByRole('link')
    expect(links).toHaveLength(1)
    expect(links[0]).toHaveAttribute('href', '/clients/c1/panchang')
    expect(links[0]).toHaveAccessibleName(/pañcāṅga/i)
    expect(links[0].className).toMatch(/min-h-11/)
    expect(links[0].className).toMatch(/focus-visible:ring/)
    expect(screen.getByText('Personalised daily timing.')).toBeInTheDocument()
    expect(screen.getByText('Today')).toBeInTheDocument()
    expect(screen.queryByText('Unavailable')).not.toBeInTheDocument()
  })
})
