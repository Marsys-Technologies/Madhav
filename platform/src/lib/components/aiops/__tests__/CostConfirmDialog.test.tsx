import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { CostConfirmDialog, shouldShowCostDialog } from '../CostConfirmDialog'

describe('shouldShowCostDialog', () => {
  it('always returns true for anthropic stack', () => {
    expect(shouldShowCostDialog('anthropic')).toBe(true)
  })

  it('returns true for gpt stack (cost >= threshold)', () => {
    expect(shouldShowCostDialog('gpt')).toBe(true)
  })

  it('returns false for deepseek stack (cost < threshold)', () => {
    expect(shouldShowCostDialog('deepseek')).toBe(false)
  })

  it('returns false for nim stack (cost < threshold)', () => {
    expect(shouldShowCostDialog('nim')).toBe(false)
  })
})

describe('CostConfirmDialog', () => {
  it('renders the target stack name', () => {
    render(
      <CostConfirmDialog
        targetStack="anthropic"
        onConfirm={vi.fn()}
        onCancel={vi.fn()}
      />,
    )
    expect(screen.getByRole('heading', { name: /Anthropic/i })).toBeTruthy()
  })

  it('shows Anthropic restriction note for anthropic stack', () => {
    render(
      <CostConfirmDialog
        targetStack="anthropic"
        onConfirm={vi.fn()}
        onCancel={vi.fn()}
      />,
    )
    expect(screen.getByText(/restricted by default/i)).toBeTruthy()
  })

  it('calls onConfirm when Confirm button clicked', () => {
    const onConfirm = vi.fn()
    render(
      <CostConfirmDialog targetStack="gpt" onConfirm={onConfirm} onCancel={vi.fn()} />,
    )
    fireEvent.click(screen.getByText(/Set as default/i))
    expect(onConfirm).toHaveBeenCalledOnce()
  })

  it('calls onCancel when Cancel button clicked', () => {
    const onCancel = vi.fn()
    render(
      <CostConfirmDialog targetStack="gpt" onConfirm={vi.fn()} onCancel={onCancel} />,
    )
    fireEvent.click(screen.getByText(/Cancel/i))
    expect(onCancel).toHaveBeenCalledOnce()
  })
})
