import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { HealthPip } from '../HealthPip'

describe('HealthPip', () => {
  beforeEach(() => { vi.restoreAllMocks() })

  it('renders with role=img and a non-empty aria-label', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ rows: [] }), { status: 200 }),
    )
    render(<HealthPip modelId="test-model" />)
    const pip = screen.getByRole('img')
    expect(pip.getAttribute('aria-label')).toBeTruthy()
  })

  it('shows "Never probed" label when no health data returned', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ rows: [] }), { status: 200 }),
    )
    render(<HealthPip modelId="test-model" />)
    const pip = screen.getByRole('img')
    expect(pip.getAttribute('aria-label')).toContain('Never probed')
  })

  it('reflects pass status in aria-label when health data returns pass', async () => {
    const now = new Date().toISOString()
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({
        rows: [{ status: 'pass', latency_ms: 200, last_probe_at: now, last_error: null }],
      }), { status: 200 }),
    )
    render(<HealthPip modelId="good-model" />)
    await waitFor(() => {
      const pip = screen.getByRole('img')
      expect(pip.getAttribute('aria-label')).toContain('pass')
    })
  })

  it('reflects fail status in aria-label when health data returns fail', async () => {
    const now = new Date().toISOString()
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({
        rows: [{ status: 'fail', latency_ms: null, last_probe_at: now, last_error: 'err' }],
      }), { status: 200 }),
    )
    render(<HealthPip modelId="bad-model" />)
    await waitFor(() => {
      const pip = screen.getByRole('img')
      expect(pip.getAttribute('aria-label')).toContain('fail')
    })
  })

  it('fetches health using the correct model_id URL param', async () => {
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ rows: [] }), { status: 200 }),
    )
    render(<HealthPip modelId="gemini-2.5-pro" />)
    await waitFor(() => expect(fetchSpy).toHaveBeenCalled())
    const url = fetchSpy.mock.calls[0][0] as string
    expect(url).toContain(encodeURIComponent('gemini-2.5-pro'))
  })

  it('includes latency in aria-label when latency_ms is present', async () => {
    const now = new Date().toISOString()
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({
        rows: [{ status: 'pass', latency_ms: 350, last_probe_at: now, last_error: null }],
      }), { status: 200 }),
    )
    render(<HealthPip modelId="fast-model" />)
    await waitFor(() => {
      const pip = screen.getByRole('img')
      expect(pip.getAttribute('aria-label')).toContain('350ms')
    })
  })
})
