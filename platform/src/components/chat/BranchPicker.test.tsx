import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BranchPicker } from './BranchPicker'

describe('BranchPicker', () => {
  it('renders current/total label', () => {
    const { container } = render(<BranchPicker currentBranch={2} totalBranches={3} onPrev={vi.fn()} onNext={vi.fn()} />)
    // Check the label span contains both numbers
    expect(container.textContent).toContain('2')
    expect(container.textContent).toContain('3')
  })

  it('has correct aria-labels', () => {
    render(<BranchPicker currentBranch={2} totalBranches={3} onPrev={vi.fn()} onNext={vi.fn()} />)
    expect(screen.getByRole('button', { name: 'Previous branch' })).toBeTruthy()
    expect(screen.getByRole('button', { name: 'Next branch' })).toBeTruthy()
  })

  it('disables prev on first branch', () => {
    render(<BranchPicker currentBranch={1} totalBranches={3} onPrev={vi.fn()} onNext={vi.fn()} />)
    const prev = screen.getByRole('button', { name: 'Previous branch' })
    expect(prev).toHaveAttribute('disabled')
    expect(screen.getByRole('button', { name: 'Next branch' })).not.toHaveAttribute('disabled')
  })

  it('disables next on last branch', () => {
    render(<BranchPicker currentBranch={3} totalBranches={3} onPrev={vi.fn()} onNext={vi.fn()} />)
    const next = screen.getByRole('button', { name: 'Next branch' })
    expect(next).toHaveAttribute('disabled')
    expect(screen.getByRole('button', { name: 'Previous branch' })).not.toHaveAttribute('disabled')
  })

  it('neither disabled in middle branch', () => {
    render(<BranchPicker currentBranch={2} totalBranches={3} onPrev={vi.fn()} onNext={vi.fn()} />)
    expect(screen.getByRole('button', { name: 'Previous branch' })).not.toHaveAttribute('disabled')
    expect(screen.getByRole('button', { name: 'Next branch' })).not.toHaveAttribute('disabled')
  })

  it('calls onPrev when prev clicked', async () => {
    const onPrev = vi.fn()
    render(<BranchPicker currentBranch={2} totalBranches={3} onPrev={onPrev} onNext={vi.fn()} />)
    await userEvent.click(screen.getByRole('button', { name: 'Previous branch' }))
    expect(onPrev).toHaveBeenCalledOnce()
  })

  it('calls onNext when next clicked', async () => {
    const onNext = vi.fn()
    render(<BranchPicker currentBranch={2} totalBranches={3} onPrev={vi.fn()} onNext={onNext} />)
    await userEvent.click(screen.getByRole('button', { name: 'Next branch' }))
    expect(onNext).toHaveBeenCalledOnce()
  })
})
