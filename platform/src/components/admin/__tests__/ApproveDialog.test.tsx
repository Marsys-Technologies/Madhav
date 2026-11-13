import '@testing-library/jest-dom/vitest'
import type { ReactNode } from 'react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { ApproveDialog } from '../ApproveDialog'
import type { AdminAccessRequest } from '../types'

const mocks = vi.hoisted(() => ({ fetch: vi.fn(), approved: vi.fn(), success: vi.fn(), error: vi.fn() }))
vi.mock('sonner', () => ({ toast: { success: mocks.success, error: mocks.error } }))
// Real component/form state and DOM; dialog focus/portal behavior is outside this response contract.
vi.mock('@/components/ui/dialog', () => ({
  Dialog: ({ open, children }: { open: boolean; children: ReactNode }) => open ? <div>{children}</div> : null,
  DialogContent: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  DialogDescription: ({ children }: { children: ReactNode }) => <p>{children}</p>,
  DialogHeader: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  DialogTitle: ({ children }: { children: ReactNode }) => <h2>{children}</h2>,
}))

const request: AdminAccessRequest = {
  id: 'synthetic-request', full_name: 'Synthetic Request', email: 'fixture@example.invalid',
  reason: null, status: 'pending', requested_at: '2026-01-01T00:00:00Z', reviewed_at: null,
  approved_user_id: null, approved_username: null, approved_name: null,
}
const link = 'https://example.invalid/synthetic-account-setup'

beforeEach(() => { vi.resetAllMocks(); vi.stubGlobal('fetch', mocks.fetch) })
afterEach(() => { cleanup(); vi.unstubAllGlobals() })

async function approve(body: unknown, status = 200) {
  mocks.fetch.mockResolvedValue({ ok: status >= 200 && status < 300, json: async () => body })
  render(<ApproveDialog request={request} open onOpenChange={vi.fn()} onApproved={mocks.approved} />)
  fireEvent.submit(screen.getByRole('button', { name: /Approve & create user/ }).closest('form')!)
  await waitFor(() => expect(mocks.approved).toHaveBeenCalledTimes(status === 200 ? 1 : 0))
  if (status === 200) await screen.findByRole('button', { name: 'Done' })
}

describe('ApproveDialog account setup result', () => {
  it('intentional absence: existing password can sign in, without a false failure or recovery demand', async () => {
    await approve({ ok: true, reset_link: null, setup_link_status: 'not_required' })
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
    expect(screen.getByText(/already has a password/)).toBeInTheDocument()
    expect(screen.queryByLabelText('Account setup link')).not.toBeInTheDocument()
    expect(screen.queryByText(/could not be generated/)).not.toBeInTheDocument()
    expect(mocks.success).toHaveBeenCalledWith('Request approved.')
    expect(mocks.fetch).toHaveBeenCalledExactlyOnceWith('/api/admin/access-requests/synthetic-request/approve', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ role: 'guest' }),
    })
  })
  it('generation unavailable preserves the explicit manual recovery instruction', async () => {
    await approve({ ok: true, reset_link: null, setup_link_status: 'unavailable' })
    expect(screen.getByRole('alert')).toHaveTextContent(/setup link could not be generated/)
    expect(screen.getByRole('alert')).toHaveTextContent(/Account Recovery/)
    expect(screen.getByRole('alert')).toHaveTextContent(/No email has been sent automatically/)
    expect(mocks.success).toHaveBeenCalledWith('Request approved.')
  })
  it.each(['available', undefined, 'unknown'])('preserves the exact available link and established copy (status=%s)', async setup_link_status => {
    await approve({ ok: true, reset_link: link, setup_link_status })
    expect(screen.getByLabelText('Account setup link')).toHaveValue(link)
    expect(screen.getByText(/This link is not emailed automatically/)).toBeInTheDocument()
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })
  it.each([undefined, 'unknown', 'available'])('null link without a reliable discriminator is neutral (status=%s)', async setup_link_status => {
    await approve({ ok: true, reset_link: null, setup_link_status })
    expect(screen.getByText(/No account-setup link was returned/)).toBeInTheDocument()
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
    expect(screen.queryByText(/could not be generated/)).not.toBeInTheDocument()
  })
  it('does not render a malformed link object as an account setup link', async () => {
    await approve({ ok: true, reset_link: { synthetic_private_marker: 'must-not-display' }, setup_link_status: 'available' })
    expect(screen.queryByLabelText('Account setup link')).not.toBeInTheDocument()
    expect(screen.getByText(/No account-setup link was returned/)).toBeInTheDocument()
    expect(document.body).not.toHaveTextContent('must-not-display')
  })
  it('HTTP refusal stays on the form and never reports approval', async () => {
    await approve({ error: { message: 'Synthetic refusal' } }, 403)
    await waitFor(() => expect(mocks.error).toHaveBeenCalledWith('Synthetic refusal'))
    expect(mocks.approved).not.toHaveBeenCalled()
    expect(mocks.success).not.toHaveBeenCalled()
    expect(screen.queryByRole('button', { name: 'Done' })).not.toBeInTheDocument()
  })
  it('network failure leaves retry available and never reports approval', async () => {
    mocks.fetch.mockRejectedValue(new Error('Synthetic network failure'))
    render(<ApproveDialog request={request} open onOpenChange={vi.fn()} onApproved={mocks.approved} />)
    fireEvent.submit(screen.getByRole('button', { name: /Approve & create user/ }).closest('form')!)
    await waitFor(() => expect(mocks.error).toHaveBeenCalledWith('Network error.'))
    expect(mocks.approved).not.toHaveBeenCalled()
    expect(screen.getByRole('button', { name: /Approve & create user/ })).toBeEnabled()
  })
})
