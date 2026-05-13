import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { AuditRail } from '../AuditRail'

// HealthPip does its own fetch; stub it out
vi.mock('../HealthPip', () => ({
  HealthPip: () => <span data-testid="health-pip" />,
}))

// RevertConfirmDialog: spy on render but let it mount
vi.mock('../RevertConfirmDialog', () => ({
  RevertConfirmDialog: ({ onCancel, onReverted }: { onCancel: () => void; onReverted: () => void }) => (
    <div data-testid="revert-dialog">
      <button onClick={onCancel}>Cancel</button>
      <button onClick={onReverted}>Reverted</button>
    </div>
  ),
}))

const ROWS = [
  {
    id: 1,
    action: 'set_routing',
    stack: 'gemini',
    call_type: 'synthesis',
    param_name: null,
    before_value: null,
    after_value: null,
    occurred_at: new Date().toISOString(),
    actor_user_id: 'user1',
    scope: 'global',
    notes: null,
  },
  {
    id: 2,
    action: 'reset_param',
    stack: 'nim',
    call_type: 'worker',
    param_name: 'temperature',
    before_value: null,
    after_value: null,
    occurred_at: new Date().toISOString(),
    actor_user_id: 'user1',
    scope: 'global',
    notes: null,
  },
  {
    id: 3,
    action: 'non_revertible_action',
    stack: 'deepseek',
    call_type: 'planner_fast',
    param_name: null,
    before_value: null,
    after_value: null,
    occurred_at: new Date().toISOString(),
    actor_user_id: 'user1',
    scope: 'global',
    notes: null,
  },
]

describe('AuditRail', () => {
  beforeEach(() => { vi.restoreAllMocks() })

  it('renders "No changes yet." when rows are empty', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ rows: [], count: 0 }), { status: 200 }),
    )
    render(<AuditRail />)
    await waitFor(() => expect(screen.queryByText('Loading…')).toBeFalsy())
    expect(screen.getByText(/No changes yet/)).toBeTruthy()
  })

  it('renders each audit row action', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ rows: ROWS, count: ROWS.length }), { status: 200 }),
    )
    render(<AuditRail />)
    await waitFor(() => expect(screen.queryByText('Loading…')).toBeFalsy())
    expect(screen.getByText('set_routing')).toBeTruthy()
    expect(screen.getByText('reset_param')).toBeTruthy()
  })

  it('shows revert button only for revertible actions', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ rows: ROWS, count: ROWS.length }), { status: 200 }),
    )
    render(<AuditRail />)
    await waitFor(() => expect(screen.queryByText('Loading…')).toBeFalsy())
    // Two revertible + one non-revertible
    const revertButtons = screen.getAllByRole('button', { name: /Revert change/ })
    expect(revertButtons).toHaveLength(2)
  })

  it('revert button has descriptive aria-label', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ rows: [ROWS[0]], count: 1 }), { status: 200 }),
    )
    render(<AuditRail />)
    await waitFor(() => expect(screen.queryByText('Loading…')).toBeFalsy())
    const btn = screen.getByRole('button', { name: 'Revert change 1' })
    expect(btn).toBeTruthy()
  })

  it('opens RevertConfirmDialog when revert button clicked', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ rows: [ROWS[0]], count: 1 }), { status: 200 }),
    )
    render(<AuditRail />)
    await waitFor(() => expect(screen.queryByText('Loading…')).toBeFalsy())
    fireEvent.click(screen.getByRole('button', { name: /Revert change/ }))
    expect(screen.getByTestId('revert-dialog')).toBeTruthy()
  })

  it('closes dialog and reloads on onReverted', async () => {
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ rows: [ROWS[0]], count: 1 }), { status: 200 }),
    )
    render(<AuditRail />)
    await waitFor(() => expect(screen.queryByText('Loading…')).toBeFalsy())
    const callsBefore = fetchSpy.mock.calls.length
    fireEvent.click(screen.getByRole('button', { name: /Revert change/ }))
    fireEvent.click(screen.getByText('Reverted'))
    await waitFor(() => expect(fetchSpy.mock.calls.length).toBeGreaterThan(callsBefore))
    expect(screen.queryByTestId('revert-dialog')).toBeFalsy()
  })

  it('closes dialog without reload on onCancel', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ rows: [ROWS[0]], count: 1 }), { status: 200 }),
    )
    render(<AuditRail />)
    await waitFor(() => expect(screen.queryByText('Loading…')).toBeFalsy())
    fireEvent.click(screen.getByRole('button', { name: /Revert change/ }))
    fireEvent.click(screen.getByText('Cancel'))
    expect(screen.queryByTestId('revert-dialog')).toBeFalsy()
  })
})
