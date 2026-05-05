import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent, within, act } from '@testing-library/react'

import { EventTable } from '@/lib/components/observatory/events/EventTable'
import { COLUMN_STORAGE_KEY } from '@/lib/components/observatory/events/types'
import { makeRows, makeEventsResponse } from './fixtures'

const FETCH_PARAMS = { from: '2026-04-01', to: '2026-05-01' }

beforeEach(() => {
  window.localStorage.clear()
})

describe('EventTable — virtualization', () => {
  it('renders only the visible window of rows when given 20 fixture rows', async () => {
    const rows = makeRows(20)
    const fetcher = vi.fn().mockResolvedValue(makeEventsResponse(rows, null, 20))

    await act(async () => {
      render(
        <EventTable
          fetchParams={FETCH_PARAMS}
          fetcher={fetcher}
          rowHeight={40}
          viewportHeight={200}
        />,
      )
    })

    const virtual = screen.getByTestId('event-table-virtual')
    const rendered = within(virtual).getAllByTestId(/^event-row-/)
    // 20 rows total, viewport 200/40 = 5 visible, +overscan*2=6 → ~11 max in DOM.
    // Crucial assertion: NOT all 20 are in DOM.
    expect(rendered.length).toBeLessThan(20)
    expect(rendered.length).toBeGreaterThanOrEqual(5)
  })
})

describe('EventTable — load more pagination', () => {
  it('appends the next page when "Load more" is clicked', async () => {
    const page1 = makeRows(10)
    const page2 = makeRows(10).map((r, i) => ({
      ...r,
      event_id: `evt-page2-${i}`,
    }))

    const fetcher = vi
      .fn()
      // first call (initial mount)
      .mockResolvedValueOnce(makeEventsResponse(page1, 'cursor-2', 20))
      // second call (Load more)
      .mockResolvedValueOnce(makeEventsResponse(page2, null, 20))

    await act(async () => {
      render(
        <EventTable
          fetchParams={FETCH_PARAMS}
          fetcher={fetcher}
          rowHeight={40}
          viewportHeight={2000}
        />,
      )
    })

    expect(screen.getByTestId('event-table-count')).toHaveTextContent(
      'Showing 10 of 20',
    )

    await act(async () => {
      fireEvent.click(screen.getByTestId('event-table-load-more'))
    })

    expect(fetcher).toHaveBeenCalledTimes(2)
    expect(fetcher).toHaveBeenLastCalledWith(
      expect.objectContaining({ cursor: 'cursor-2' }),
    )
    expect(screen.getByTestId('event-table-count')).toHaveTextContent(
      'Showing 20 of 20',
    )
  })
})

describe('EventTable — column visibility', () => {
  it('hides a column when toggled off and persists state across remount', async () => {
    const rows = makeRows(5)
    const fetcher = vi.fn().mockResolvedValue(makeEventsResponse(rows, null, 5))

    const { unmount } = await act(async () => {
      const r = render(
        <EventTable
          fetchParams={FETCH_PARAMS}
          fetcher={fetcher}
          rowHeight={40}
          viewportHeight={2000}
        />,
      )
      return r
    })

    // model column header is present by default
    expect(screen.getByTestId('event-table-header-model')).toBeInTheDocument()

    // Open columns panel + toggle "model" off
    await act(async () => {
      fireEvent.click(screen.getByTestId('event-table-columns-toggle'))
    })
    await act(async () => {
      fireEvent.click(screen.getByTestId('event-table-column-checkbox-model'))
    })

    expect(screen.queryByTestId('event-table-header-model')).not.toBeInTheDocument()

    // localStorage was written with the new visible set
    const stored = window.localStorage.getItem(COLUMN_STORAGE_KEY)
    expect(stored).not.toBeNull()
    expect(JSON.parse(stored!)).not.toContain('model')

    unmount()

    // Remount → state survives via localStorage
    await act(async () => {
      render(
        <EventTable
          fetchParams={FETCH_PARAMS}
          fetcher={fetcher}
          rowHeight={40}
          viewportHeight={2000}
        />,
      )
    })

    expect(screen.queryByTestId('event-table-header-model')).not.toBeInTheDocument()
  })
})

describe('EventTable — status badges', () => {
  it('renders success/error/timeout badges with their respective tones', async () => {
    const rows = [
      { ...makeRows(1)[0], event_id: 'a', status: 'success' },
      { ...makeRows(1)[0], event_id: 'b', status: 'error' },
      { ...makeRows(1)[0], event_id: 'c', status: 'timeout' },
    ]
    const fetcher = vi.fn().mockResolvedValue(makeEventsResponse(rows, null, 3))

    await act(async () => {
      render(
        <EventTable
          fetchParams={FETCH_PARAMS}
          fetcher={fetcher}
          rowHeight={40}
          viewportHeight={2000}
        />,
      )
    })

    const success = screen.getByTestId('status-badge-success')
    const error = screen.getByTestId('status-badge-error')
    const timeout = screen.getByTestId('status-badge-timeout')

    expect(success.className).toMatch(/emerald/)
    expect(error.className).toMatch(/red/)
    expect(timeout.className).toMatch(/amber/)
  })
})
