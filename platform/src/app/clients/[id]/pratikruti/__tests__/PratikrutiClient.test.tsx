import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, expect, it, vi } from 'vitest'
import { PratikrutiClient } from '../PratikrutiClient'

const fixture = {
  open_windows: [{
    prediction_id: 'q1-prediction',
    domain: 'career',
    summary: 'Fictional prediction',
    window_end: '2026-10-05',
    composite_verdict: 'UNRESOLVED',
  }],
  pending_followups: [{
    prediction_id: 'q1-followup',
    domain: 'career',
    follow_up_prompt: 'Fictional follow-up',
    fructification_date: '2026-10-06',
  }],
  pending_cosign: [{
    snapshot_id: 'q1-snapshot',
    formula_version: 'q1-formula',
    publication_status: 'proposed',
    created_at: '2026-10-07',
    cells_jsonb: {},
  }],
}

afterEach(() => vi.unstubAllGlobals())

it('shows records without offering writes to a view-only guest', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(Response.json(fixture)))
  render(<PratikrutiClient chartId="fictional-chart" canWrite={false} />)

  expect(await screen.findByText('Fictional prediction')).toBeInTheDocument()
  expect(screen.getByText('Fictional follow-up')).toBeInTheDocument()
  expect(screen.getByText(/proposed snapshot.*q1-formula/i)).toBeInTheDocument()
  expect(screen.queryAllByRole('button', { name: /happened|approve|revoke|expand/i })).toHaveLength(0)
  expect(screen.queryByText('Resonance Feedback')).not.toBeInTheDocument()
})

it('keeps existing eligible controls for full chart access', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(Response.json(fixture)))
  render(<PratikrutiClient chartId="fictional-chart" canWrite />)

  expect(await screen.findByRole('button', { name: 'Approve' })).toBeInTheDocument()
  expect(screen.getByRole('button', { name: /expand/i })).toBeInTheDocument()
})

it('distinguishes a failed read from an empty result and retries', async () => {
  const request = vi.fn()
    .mockRejectedValueOnce(new Error('test failure'))
    .mockResolvedValueOnce(Response.json({ open_windows: [], pending_followups: [], pending_cosign: [] }))
  vi.stubGlobal('fetch', request)
  render(<PratikrutiClient chartId="fictional-chart" canWrite={false} />)

  expect(await screen.findByRole('alert')).toHaveTextContent('Learning activity could not be loaded.')
  expect(screen.queryByText(/all caught up/i)).not.toBeInTheDocument()
  await userEvent.click(screen.getByRole('button', { name: 'Retry' }))
  expect(await screen.findByText(/all caught up/i)).toBeInTheDocument()
  expect(screen.getByRole('region', { name: 'Learning activity' })).toHaveFocus()
  expect(request).toHaveBeenCalledTimes(2)
})
