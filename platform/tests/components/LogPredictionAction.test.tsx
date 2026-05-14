import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { LogPredictionAction } from '@/components/consume/LogPredictionAction'

// Mock sonner toast
vi.mock('sonner', () => ({ toast: { success: vi.fn(), error: vi.fn() } }))

// Mock Dialog primitives
vi.mock('@/components/ui/dialog', () => ({
  Dialog: ({ open, children }: { open: boolean; children: React.ReactNode }) =>
    open ? <div data-testid="dialog">{children}</div> : null,
  DialogContent: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="dialog-content">{children}</div>
  ),
  DialogHeader: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  DialogTitle: ({ children }: { children: React.ReactNode }) => <h2>{children}</h2>,
  DialogClose: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}))

vi.mock('@/components/ui/button', () => ({
  Button: ({ children, onClick, disabled, type }: React.ButtonHTMLAttributes<HTMLButtonElement>) => (
    <button onClick={onClick} disabled={disabled} type={type}>{children}</button>
  ),
}))

const TEXT_WITH_PREDICTION = 'By 2026 the career trajectory will show significant improvement.'
const TEXT_WITHOUT_PREDICTION = 'The chart shows strong yogas in the seventh house.'

describe('LogPredictionAction', () => {
  it('renders nothing when no prediction detected', () => {
    const { container } = render(
      <LogPredictionAction answerText={TEXT_WITHOUT_PREDICTION} />
    )
    expect(container.firstChild).toBeNull()
  })

  it('renders Log prediction button when prediction detected', () => {
    render(<LogPredictionAction answerText={TEXT_WITH_PREDICTION} />)
    expect(screen.getByText(/log prediction/i)).toBeDefined()
  })

  it('opens dialog when Log prediction clicked', async () => {
    render(<LogPredictionAction answerText={TEXT_WITH_PREDICTION} />)
    await userEvent.click(screen.getByText(/log prediction/i))
    expect(screen.getByTestId('dialog')).toBeDefined()
  })

  it('shows falsifier field as required', async () => {
    render(<LogPredictionAction answerText={TEXT_WITH_PREDICTION} />)
    await userEvent.click(screen.getByText(/log prediction/i))
    const falsifierLabel = screen.getByText(/falsifier/i)
    expect(falsifierLabel.textContent).toContain('*')
  })

  it('shows error when submitted without falsifier', async () => {
    render(<LogPredictionAction answerText={TEXT_WITH_PREDICTION} />)
    await userEvent.click(screen.getByText(/log prediction/i))
    const dialogContent = screen.getByTestId('dialog-content')
    const submitBtn = within(dialogContent).getByRole('button', { name: /log prediction/i })
    await userEvent.click(submitBtn)
    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeDefined()
    })
  })

  it('calls POST /api/lel on successful submit', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ id: 'abc123def456' }),
    })
    vi.stubGlobal('fetch', fetchMock)

    render(<LogPredictionAction answerText={TEXT_WITH_PREDICTION} queryId="q1" />)
    await userEvent.click(screen.getByText(/log prediction/i))
    const textarea = screen.getByPlaceholderText(/what observation would refute/i)
    await userEvent.type(textarea, 'No promotion received by December 2026')
    const dialogContent = screen.getByTestId('dialog-content')
    const submitBtn = within(dialogContent).getByRole('button', { name: /log prediction/i })
    await userEvent.click(submitBtn)

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith('/api/lel', expect.objectContaining({ method: 'POST' }))
    })
    vi.unstubAllGlobals()
  })
})
