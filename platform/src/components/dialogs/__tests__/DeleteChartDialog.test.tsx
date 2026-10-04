import { afterEach, describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { DeleteChartDialog } from '../DeleteChartDialog'

afterEach(() => vi.unstubAllGlobals())

function setup(response: { ok: boolean; status: number; body: unknown }) {
  const fetchMock = vi.fn().mockResolvedValue({
    ok: response.ok,
    status: response.status,
    json: async () => response.body,
  })
  vi.stubGlobal('fetch', fetchMock)
  const props = { chartId: 'c1', chartName: 'Test Native', open: true, onClose: vi.fn(), onDeleted: vi.fn() }
  render(<DeleteChartDialog {...props} />)
  fireEvent.change(screen.getByLabelText(/to confirm deletion/i), { target: { value: 'Test Native' } })
  fireEvent.click(screen.getByRole('button', { name: /delete permanently/i }))
  return { fetchMock, props }
}

describe('DeleteChartDialog — deletion unavailable (503 CHART_DELETION_UNAVAILABLE)', () => {
  it('shows the server message, does not report success, and does not close', async () => {
    const { props } = setup({
      ok: false,
      status: 503,
      body: { error: 'Chart deletion is temporarily unavailable. Nothing was deleted.', code: 'CHART_DELETION_UNAVAILABLE' },
    })
    expect(await screen.findByRole('alert')).toHaveTextContent(/chart deletion is temporarily unavailable/i)
    await waitFor(() => expect(screen.getByRole('button', { name: /delete permanently/i })).toBeEnabled())
    expect(props.onDeleted).not.toHaveBeenCalled()
  })

  it('still reports success on a 200', async () => {
    const { props } = setup({ ok: true, status: 200, body: { deleted: true } })
    await waitFor(() => expect(props.onDeleted).toHaveBeenCalledTimes(1))
  })
})
