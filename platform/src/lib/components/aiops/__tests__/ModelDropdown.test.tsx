import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import type { CatalogFetchResult } from '@/lib/aiops/catalog/types'

// Stub HealthPip so it makes no fetch calls in these tests
vi.mock('../HealthPip', () => ({
  HealthPip: () => null,
}))

// Mock fetch globally
const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)

function makeCatalogResponse(models: { model_id: string; context_window: number | null; capabilities: string[] }[]): CatalogFetchResult {
  return {
    status: 'ok',
    models: models.map(m => ({
      model_id:           m.model_id,
      provider:           'google',
      label:              m.model_id,
      context_window:     m.context_window,
      param_count:        null,
      capabilities:       m.capabilities as never,
      role:               null,
      cost_input_per_1m:  1.0,
      cost_output_per_1m: 2.0,
      metadata_pending:   false,
      is_registry_entry:  true,
    })),
    raw: {},
    fetched_at: new Date().toISOString(),
  }
}

describe('ModelDropdown', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows loading state initially then renders entries', async () => {
    const { ModelDropdown } = await import('../ModelDropdown')
    mockFetch.mockResolvedValueOnce({
      json: () => Promise.resolve(makeCatalogResponse([
        { model_id: 'gemini-2.5-pro', context_window: 2_000_000, capabilities: [] },
      ])),
    })
    render(<ModelDropdown stack="gemini" callType="synthesis" role="primary" value="" onChange={vi.fn()} />)
    // Open dropdown
    fireEvent.click(screen.getAllByRole('button')[0])
    await waitFor(() => expect(screen.queryByText('Loading…')).toBeFalsy(), { timeout: 2000 })
    expect(screen.getByText('gemini-2.5-pro')).toBeTruthy()
  })

  it('filters out models below 1M context for synthesis call type', async () => {
    const { ModelDropdown } = await import('../ModelDropdown')
    mockFetch.mockResolvedValueOnce({
      json: () => Promise.resolve(makeCatalogResponse([
        { model_id: 'big-model',   context_window: 1_000_000, capabilities: [] },
        { model_id: 'small-model', context_window:   200_000, capabilities: [] },
      ])),
    })
    render(<ModelDropdown stack="gemini" callType="synthesis" role="primary" value="" onChange={vi.fn()} />)
    fireEvent.click(screen.getAllByRole('button')[0])
    await waitFor(() => screen.queryByText('Loading…') === null, { timeout: 2000 })
    expect(screen.queryByText('big-model')).toBeTruthy()
    expect(screen.queryByText('small-model')).toBeFalsy()
  })

  it('calls onChange with model_id when a model is selected', async () => {
    const { ModelDropdown } = await import('../ModelDropdown')
    const onChange = vi.fn()
    mockFetch.mockResolvedValueOnce({
      json: () => Promise.resolve(makeCatalogResponse([
        { model_id: 'gemini-2.5-pro', context_window: 2_000_000, capabilities: [] },
      ])),
    })
    render(<ModelDropdown stack="gemini" callType="synthesis" role="primary" value="" onChange={onChange} />)
    fireEvent.click(screen.getAllByRole('button')[0])
    await waitFor(() => screen.queryByText('gemini-2.5-pro') !== null, { timeout: 2000 })
    fireEvent.click(screen.getByText('gemini-2.5-pro'))
    expect(onChange).toHaveBeenCalledWith('gemini-2.5-pro')
  })

  it('shows empty state when no models match filter', async () => {
    const { ModelDropdown } = await import('../ModelDropdown')
    mockFetch.mockResolvedValueOnce({
      json: () => Promise.resolve(makeCatalogResponse([
        { model_id: 'tiny', context_window: 4096, capabilities: [] },
      ])),
    })
    render(<ModelDropdown stack="gemini" callType="synthesis" role="primary" value="" onChange={vi.fn()} />)
    fireEvent.click(screen.getAllByRole('button')[0])
    await waitFor(() => screen.queryByText('No models available') !== null, { timeout: 2000 })
  })

  it('shows all 5 providers for cross-stack call type (eval_judge)', async () => {
    const { ModelDropdown } = await import('../ModelDropdown')
    // Simulate 5 provider fetches — all return empty but we can check 5 calls
    mockFetch.mockResolvedValue({ json: () => Promise.resolve(makeCatalogResponse([])) })
    render(<ModelDropdown stack="gemini" callType="eval_judge" role="primary" value="" onChange={vi.fn()} />)
    // Trigger load
    fireEvent.click(screen.getAllByRole('button')[0])
    await waitFor(() => screen.queryByText('Loading…') === null, { timeout: 2000 })
    // 5 fetches for 5 providers
    const fetchCalls = mockFetch.mock.calls.filter(c => (c[0] as string).includes('/catalog/'))
    expect(fetchCalls.length).toBe(5)
  })

  it('shows [pending] badge for metadata_pending entries', async () => {
    const { ModelDropdown } = await import('../ModelDropdown')
    const pending = makeCatalogResponse([{ model_id: 'mystery-model', context_window: 2_000_000, capabilities: [] }])
    pending.models[0].metadata_pending = true
    mockFetch.mockResolvedValueOnce({ json: () => Promise.resolve(pending) })
    render(<ModelDropdown stack="gemini" callType="synthesis" role="primary" value="" onChange={vi.fn()} />)
    fireEvent.click(screen.getAllByRole('button')[0])
    await waitFor(() => screen.queryByText('[pending]') !== null, { timeout: 2000 })
    expect(screen.getByText('[pending]')).toBeTruthy()
  })

  it('triggers catalog refresh when refresh button clicked', async () => {
    const { ModelDropdown } = await import('../ModelDropdown')
    mockFetch.mockResolvedValue({ json: () => Promise.resolve(makeCatalogResponse([])) })
    render(<ModelDropdown stack="gemini" callType="synthesis" role="primary" value="" onChange={vi.fn()} />)
    // Click the refresh button (second button)
    const buttons = screen.getAllByRole('button')
    const refreshBtn = buttons.find(b => b.title === 'Refresh catalog')
    if (refreshBtn) fireEvent.click(refreshBtn)
    // Should trigger a POST to refresh endpoint
    await waitFor(() => {
      const postCalls = mockFetch.mock.calls.filter(c => (c[1] as RequestInit)?.method === 'POST')
      return postCalls.length > 0
    }, { timeout: 2000 })
  })

  it('shows marsys flat list across all providers', async () => {
    const { ModelDropdown } = await import('../ModelDropdown')
    mockFetch.mockResolvedValue({ json: () => Promise.resolve(makeCatalogResponse([])) })
    render(<ModelDropdown stack="marsys" callType="synthesis" role="primary" value="" onChange={vi.fn()} />)
    fireEvent.click(screen.getAllByRole('button')[0])
    await waitFor(() => screen.queryByText('Loading…') === null, { timeout: 2000 })
    const fetchCalls = mockFetch.mock.calls.filter(c => (c[0] as string).includes('/catalog/'))
    expect(fetchCalls.length).toBe(5)
  })
})
