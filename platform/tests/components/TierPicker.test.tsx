import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { TierPicker } from '@/components/consume/TierPicker'

// Updated 2026-05-06 (GANGA-OVERNIGHT-S1 P4 D.4.2): TierPicker tier labels
// renamed Internal/Peer/Reading → Deep/Study/Brief; active state changed
// from solid gold background to charcoal-with-gold-ring.

describe('TierPicker', () => {
  it('renders three buttons with labels Deep / Study / Brief in that order', () => {
    render(<TierPicker tier="client" onChange={() => {}} />)
    const buttons = screen.getAllByRole('button')
    expect(buttons).toHaveLength(3)
    // Each button now contains an icon + label, so check textContent contains the label.
    expect(buttons[0].textContent).toContain('Deep')
    expect(buttons[1].textContent).toContain('Study')
    expect(buttons[2].textContent).toContain('Brief')
  })

  it("calls onChange with 'super_admin' when Deep is clicked", async () => {
    const onChange = vi.fn()
    render(<TierPicker tier="client" onChange={onChange} />)
    await userEvent.click(screen.getByText('Deep'))
    expect(onChange).toHaveBeenCalledWith('super_admin')
  })

  it("calls onChange with 'acharya_reviewer' when Study is clicked", async () => {
    const onChange = vi.fn()
    render(<TierPicker tier="client" onChange={onChange} />)
    await userEvent.click(screen.getByText('Study'))
    expect(onChange).toHaveBeenCalledWith('acharya_reviewer')
  })

  it("calls onChange with 'client' when Brief is clicked", async () => {
    const onChange = vi.fn()
    render(<TierPicker tier="super_admin" onChange={onChange} />)
    await userEvent.click(screen.getByText('Brief'))
    expect(onChange).toHaveBeenCalledWith('client')
  })

  it("active tier carries gold accent — when tier='client', Brief has aria-pressed=true and gold ring class", () => {
    render(<TierPicker tier="client" onChange={() => {}} />)
    const briefBtn = screen.getByText('Brief').closest('button')!
    expect(briefBtn.getAttribute('aria-pressed')).toBe('true')
    expect(briefBtn.className).toContain('brand-gold')
  })

  it('has accessible group label', () => {
    render(<TierPicker tier="client" onChange={() => {}} />)
    expect(screen.getByRole('group', { name: /audience tier/i })).toBeDefined()
  })
})
