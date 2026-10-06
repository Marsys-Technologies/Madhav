import { afterEach, describe, expect, it, vi } from 'vitest'
import { cleanup, render, screen } from '@testing-library/react'
const evidence = vi.hoisted(() => ({ pending: true, error: false, charts: [] }))
vi.mock('next/navigation', () => ({ useRouter: () => ({ push: vi.fn(), replace: vi.fn() }), useSearchParams: () => new URLSearchParams('guest=guest-2') }))
vi.mock('@tanstack/react-query', () => ({
  useQuery: () => ({ data: evidence.pending ? undefined : { charts: evidence.charts }, isPending: evidence.pending, isError: evidence.error, refetch: vi.fn() }),
  useQueryClient: () => ({ setQueryData: vi.fn() }),
}))
import { ChartsTab } from './ChartsTab'
const users = [{ id: 'guest-2', name: 'Biren Sen', username: 'biren', email: 'biren@example.test', role: 'guest' as const, status: 'active' as const, created_at: '2026-10-01', approved_at: null }]
afterEach(() => { cleanup(); evidence.pending = true; evidence.error = false })
describe('ChartsTab source states', () => {
  it('keeps a bookmarked guest and reports pending evidence without empty or zero counts', () => {
    render(<ChartsTab users={users} onGrantMutated={vi.fn()} />)
    expect(screen.getByText("biren's chart access")).toBeInTheDocument()
    expect(screen.getByRole('status')).toHaveTextContent('Loading chart grants…')
    expect(screen.queryByText('No charts on the platform yet.')).toBeNull()
    expect(screen.queryByText('0 of 0 charts shared')).toBeNull()
  })
  it('shows unavailable rather than an empty platform on read failure', () => {
    evidence.pending = false; evidence.error = true
    render(<ChartsTab users={users} onGrantMutated={vi.fn()} />)
    expect(screen.getByRole('alert')).toHaveTextContent('Chart access unavailable.')
    expect(screen.getByText('Chart counts unavailable')).toBeInTheDocument()
    expect(screen.queryByText('No charts on the platform yet.')).toBeNull()
  })
  it('reports a successfully recorded empty chart set', () => {
    evidence.pending = false
    render(<ChartsTab users={users} onGrantMutated={vi.fn()} />)
    expect(screen.getByText('No charts on the platform yet.')).toBeInTheDocument()
    expect(screen.getByText('0 of 0 charts shared')).toBeInTheDocument()
  })
})
