/**
 * V3-E-012a (Paripraśna v3 assurance, stream S1): `PariprashnaApp`'s sidebar
 * `threads` must merge the live session's own thread with real fetched
 * history (`GET /api/conversations?readingsOnly=true`), and selecting a
 * fetched (non-live) row must show an honest "not openable yet" notice
 * rather than silently doing nothing (Native Surrogate ruling B4, decision
 * event `f3b88219-432f-4096-999c-07f6700f6406`).
 *
 * Every sibling region (Composer, RightDock, ThreadHeader, Transcript,
 * EmptyState, ArrivalLine, OverlayLayer) is stubbed to isolate the
 * shell-composition logic under test (S1's own territory) from those
 * regions' own rendering (S2's territory, covered by their own suites).
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, cleanup, fireEvent, waitFor } from '@testing-library/react'

vi.mock('../ThreadHeader', () => ({ ThreadHeader: () => null }))
vi.mock('../Transcript', () => ({ Transcript: () => null }))
vi.mock('../EmptyState', () => ({ EmptyState: () => null }))
vi.mock('../ArrivalLine', () => ({ ArrivalLine: () => null }))
vi.mock('../composer/Composer', () => ({ Composer: () => null }))
vi.mock('../dock/RightDock', () => ({ RightDock: () => null }))
vi.mock('../overlay/OverlayLayer', () => ({ OverlayLayer: () => null }))
vi.mock('../dock/DockController', () => ({
  DockControllerProvider: ({ children }: { children: React.ReactNode }) => children,
}))
vi.mock('../hooks/useVisualViewport', () => ({ useVisualViewport: () => ({ supported: false, height: null }) }))

const { mockUseLiveStream } = vi.hoisted(() => ({
  mockUseLiveStream: vi.fn(() => ({
    state: { turns: [], surfaceStatus: 'idle' },
    submit: vi.fn(),
    stop: vi.fn(),
  })),
}))
vi.mock('../hooks/useLiveStream', () => ({ useLiveStream: mockUseLiveStream }))

import { PariprashnaApp } from '../PariprashnaApp'

const CHART_PIN = { name: 'Abhinandan Mohanty', bornLine: '02 Mar 1985 · 09:40 · Bhubaneswar, Odisha, India' }

beforeEach(() => {
  vi.stubEnv('NEXT_PUBLIC_PARIPRASHNA_LIVE', '1')
  mockUseLiveStream.mockReturnValue({ state: { turns: [], surfaceStatus: 'idle' }, submit: vi.fn(), stop: vi.fn() })
})

afterEach(() => {
  cleanup()
  vi.unstubAllEnvs()
  vi.restoreAllMocks()
})

describe('PariprashnaApp history merge (V3-E-012a)', () => {
  it('renders fetched past readings in the sidebar once GET /api/conversations resolves', async () => {
    const fetchMock = vi.spyOn(global, 'fetch').mockResolvedValue({
      ok: true,
      json: async () => ({
        conversations: [
          {
            id: 'conv-past-1',
            chart_id: 'c-1',
            title: null,
            first_message_snippet: 'What does this period ask of my career?',
            updated_at: '2026-08-20T00:00:00Z',
            created_at: '2026-08-20T00:00:00Z',
          },
        ],
      }),
    } as Response)

    render(<PariprashnaApp chartPin={CHART_PIN} chartId="c-1" />)

    await waitFor(() => expect(screen.getAllByTestId('pp-sidebar-row')).toHaveLength(1))
    expect(screen.getByText('What does this period ask of my career?')).toBeInTheDocument()

    const [url] = fetchMock.mock.calls[0]
    expect(String(url)).toContain('readingsOnly=true')
    expect(String(url)).toContain('chartId=c-1')
  })

  it('shows an honest "not openable yet" notice on selecting a fetched historical row, not a silent no-op', async () => {
    vi.spyOn(global, 'fetch').mockResolvedValue({
      ok: true,
      json: async () => ({
        conversations: [
          { id: 'conv-past-1', chart_id: 'c-1', title: 'Old reading', first_message_snippet: null, updated_at: '2026-08-20T00:00:00Z', created_at: '2026-08-20T00:00:00Z' },
        ],
      }),
    } as Response)

    render(<PariprashnaApp chartPin={CHART_PIN} chartId="c-1" />)
    await waitFor(() => expect(screen.getAllByTestId('pp-sidebar-row')).toHaveLength(1))

    expect(screen.queryByTestId('pp-sidebar-select-unavailable')).not.toBeInTheDocument()
    fireEvent.click(screen.getByTestId('pp-sidebar-row'))
    expect(screen.getByTestId('pp-sidebar-select-unavailable')).toBeInTheDocument()
  })

  it('renaming a fetched historical row shows the honest notice and does NOT relabel the live thread (regression: rename ignored the row id)', async () => {
    vi.spyOn(global, 'fetch').mockResolvedValue({
      ok: true,
      json: async () => ({
        conversations: [
          { id: 'conv-past-1', chart_id: 'c-1', title: 'Old reading', first_message_snippet: null, updated_at: '2026-08-20T00:00:00Z', created_at: '2026-08-20T00:00:00Z' },
        ],
      }),
    } as Response)

    render(<PariprashnaApp chartPin={CHART_PIN} chartId="c-1" />)
    await waitFor(() => expect(screen.getAllByTestId('pp-sidebar-row')).toHaveLength(1))

    // Double-click the fetched (historical) row's title to enter rename mode,
    // then commit — this must NOT silently retitle anything else, and must
    // surface the same honest notice as selecting a historical row.
    fireEvent.doubleClick(screen.getByText('Old reading'))
    const input = screen.getByDisplayValue('Old reading')
    fireEvent.change(input, { target: { value: 'Renamed by mistake' } })
    fireEvent.keyDown(input, { key: 'Enter' })

    expect(screen.getByTestId('pp-sidebar-select-unavailable')).toBeInTheDocument()
    // Still exactly one row (the fetched one) — no live thread was spawned
    // or relabeled as a side effect.
    expect(screen.getAllByTestId('pp-sidebar-row')).toHaveLength(1)
  })

  it('does not fetch on the fixture host (no chartId / live flag off)', () => {
    vi.stubEnv('NEXT_PUBLIC_PARIPRASHNA_LIVE', '0')
    const fetchMock = vi.spyOn(global, 'fetch').mockResolvedValue({ ok: true, json: async () => ({ conversations: [] }) } as Response)
    render(<PariprashnaApp chartPin={CHART_PIN} />)
    expect(fetchMock).not.toHaveBeenCalled()
  })
})
