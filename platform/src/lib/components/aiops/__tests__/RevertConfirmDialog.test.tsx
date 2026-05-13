import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { RevertConfirmDialog } from '../RevertConfirmDialog'

const ENTRY = {
  id:           42,
  action:       'set_routing',
  stack:        'gemini',
  call_type:    'synthesis',
  param_name:   null,
  before_value: { primary: 'gemini-2.5-pro' },
  after_value:  { primary: 'gemini-2.0-flash' },
}

describe('RevertConfirmDialog', () => {
  beforeEach(() => { vi.restoreAllMocks() })

  it('renders action and scope', () => {
    render(<RevertConfirmDialog entry={ENTRY} onReverted={vi.fn()} onCancel={vi.fn()} />)
    expect(screen.getByText('set_routing')).toBeTruthy()
    expect(screen.getAllByText(/gemini/).length).toBeGreaterThan(0)
    expect(screen.getAllByText(/synthesis/).length).toBeGreaterThan(0)
  })

  it('shows before and after values in diff block', () => {
    render(<RevertConfirmDialog entry={ENTRY} onReverted={vi.fn()} onCancel={vi.fn()} />)
    expect(screen.getByText(/gemini-2\.5-pro/)).toBeTruthy()
    expect(screen.getByText(/gemini-2\.0-flash/)).toBeTruthy()
  })

  it('calls onCancel when Cancel button clicked', () => {
    const onCancel = vi.fn()
    render(<RevertConfirmDialog entry={ENTRY} onReverted={vi.fn()} onCancel={onCancel} />)
    fireEvent.click(screen.getByText('Cancel'))
    expect(onCancel).toHaveBeenCalledOnce()
  })

  it('calls onCancel when Escape key pressed', () => {
    const onCancel = vi.fn()
    render(<RevertConfirmDialog entry={ENTRY} onReverted={vi.fn()} onCancel={onCancel} />)
    fireEvent.keyDown(window, { key: 'Escape' })
    expect(onCancel).toHaveBeenCalledOnce()
  })

  it('POSTs to correct revert URL on confirm', async () => {
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ reverted: 42 }), { status: 200 }),
    )
    const onReverted = vi.fn()
    render(<RevertConfirmDialog entry={ENTRY} onReverted={onReverted} onCancel={vi.fn()} />)
    fireEvent.click(screen.getByText('Confirm Revert'))
    await waitFor(() => expect(onReverted).toHaveBeenCalledOnce())
    expect(fetchSpy).toHaveBeenCalledWith('/api/admin/aiops/audit/42/revert', { method: 'POST' })
  })

  it('shows error message when fetch fails', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ error: { message: 'DB error' } }), { status: 500 }),
    )
    render(<RevertConfirmDialog entry={ENTRY} onReverted={vi.fn()} onCancel={vi.fn()} />)
    fireEvent.click(screen.getByText('Confirm Revert'))
    await waitFor(() => expect(screen.getByRole('alert')).toBeTruthy())
    expect(screen.getByRole('alert').textContent).toContain('DB error')
  })

  it('shows network error message when fetch throws', async () => {
    vi.spyOn(globalThis, 'fetch').mockRejectedValue(new Error('network down'))
    render(<RevertConfirmDialog entry={ENTRY} onReverted={vi.fn()} onCancel={vi.fn()} />)
    fireEvent.click(screen.getByText('Confirm Revert'))
    await waitFor(() => expect(screen.getByRole('alert')).toBeTruthy())
    expect(screen.getByRole('alert').textContent).toContain('Network error')
  })

  it('has role=dialog and aria-modal', () => {
    render(<RevertConfirmDialog entry={ENTRY} onReverted={vi.fn()} onCancel={vi.fn()} />)
    const dialog = screen.getByRole('dialog')
    expect(dialog.getAttribute('aria-modal')).toBe('true')
  })

  it('dialog is labelled by its title element', () => {
    render(<RevertConfirmDialog entry={ENTRY} onReverted={vi.fn()} onCancel={vi.fn()} />)
    const dialog = screen.getByRole('dialog')
    const labelledBy = dialog.getAttribute('aria-labelledby')
    expect(labelledBy).toBeTruthy()
    const title = document.getElementById(labelledBy!)
    expect(title?.textContent).toContain('Revert')
  })
})
