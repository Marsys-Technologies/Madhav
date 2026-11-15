import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, expect, it, vi } from 'vitest'
import { PratikrutiClient } from '../PratikrutiClient'
const native = '482012f1-710e-4a25-994a-93821f5871aa'
const empty = { open_windows: [], pending_followups: [], pending_cosign: [] }
afterEach(() => { cleanup(); vi.unstubAllGlobals() })
async function submit(chartId: string) {
  const rendered = render(<PratikrutiClient chartId={chartId} canWrite />)
  await userEvent.click(await screen.findByRole('button', { name: /expand/i }))
  fireEvent.change(screen.getByPlaceholderText('EVT.2026.001'), { target: { value: 'EVT.SYNTHETIC.001' } })
  fireEvent.change(rendered.container.querySelector('input[type="date"]')!, { target: { value: '2026-01-01' } })
  await userEvent.click(screen.getByRole('button', { name: 'Append to LEL' }))
}
it('shows the native-only rejection without presenting an append success', async () => {
  const request = vi.fn().mockResolvedValueOnce(Response.json(empty))
    .mockResolvedValueOnce(Response.json({ error: 'Life event intake is available only for the native chart.' }, { status: 403 }))
  vi.stubGlobal('fetch', request)
  await submit('synthetic-other-chart')
  expect(await screen.findByRole('alert')).toHaveTextContent('Life event intake is available only for the native chart.')
  expect(screen.queryByText(/life event appended/i)).not.toBeInTheDocument()
  expect(request).toHaveBeenCalledTimes(2)
})
it('shows append success while explicitly leaving provenance completion unconfirmed and offering no duplicate append retry', async () => {
  const request = vi.fn().mockResolvedValueOnce(Response.json(empty))
    .mockResolvedValueOnce(Response.json({ ok: true, event_id: 'EVT.SYNTHETIC.001', next: 'Life event appended; provenance resync completion is unconfirmed.' }))
  vi.stubGlobal('fetch', request)
  await submit(native)
  expect(await screen.findByText('Life event appended to LEL. Provenance resync completion is unconfirmed.')).toBeInTheDocument()
  expect(screen.queryByRole('button', { name: /append to lel|retry/i })).not.toBeInTheDocument()
  expect(request).toHaveBeenCalledTimes(2)
})
