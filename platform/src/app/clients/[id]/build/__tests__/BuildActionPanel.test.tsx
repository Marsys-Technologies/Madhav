/**
 * Mount + interaction tests for BuildActionPanel — Stream B 2/3.
 *
 * Asserts:
 *   - Button renders with the initial label.
 *   - On click, fetch posts to /api/build/start with the chart_id + default
 *     ayanamsha_role.
 *   - On a 200 with { build_id }, an EventSource is opened against
 *     /api/build/events/<build_id>.
 *   - A 503 response surfaces the kill-switch-disabled message.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, fireEvent, screen, waitFor, act } from '@testing-library/react'

import { BuildActionPanel } from '../BuildActionPanel'

interface FakeEventSource {
  url: string
  readyState: number
  onmessage: ((ev: MessageEvent) => void) | null
  onerror: ((ev: Event) => void) | null
  close: () => void
}

const eventSources: FakeEventSource[] = []

class FakeEventSourceImpl implements FakeEventSource {
  url: string
  readyState: number = 0
  onmessage: ((ev: MessageEvent) => void) | null = null
  onerror: ((ev: Event) => void) | null = null
  closed = false
  constructor(url: string) {
    this.url = url
    this.readyState = 1
    eventSources.push(this)
  }
  close(): void {
    this.closed = true
    this.readyState = 2
  }
}

beforeEach(() => {
  eventSources.length = 0
  ;(globalThis as unknown as { EventSource: typeof FakeEventSourceImpl }).EventSource =
    FakeEventSourceImpl
})

afterEach(() => {
  vi.restoreAllMocks()
})

function mockFetch(response: { status: number; body: unknown }): ReturnType<typeof vi.fn> {
  const fn = vi.fn(async () =>
    new Response(typeof response.body === 'string' ? response.body : JSON.stringify(response.body), {
      status: response.status,
      headers: { 'content-type': 'application/json' },
    }),
  )
  globalThis.fetch = fn as unknown as typeof fetch
  return fn
}

describe('BuildActionPanel — initial render', () => {
  it('renders the trigger button', () => {
    render(<BuildActionPanel chartId="chart-1" />)
    const button = screen.getByTestId('build-action-button')
    expect(button).toBeInTheDocument()
    expect(button).toHaveTextContent(/build chart/i)
  })
})

describe('BuildActionPanel — happy path', () => {
  it('posts to /api/build/start with chart_id + default ayanamsha_role and opens EventSource', async () => {
    const fetchMock = mockFetch({ status: 200, body: { build_id: 'build-abc' } })
    render(<BuildActionPanel chartId="chart-1" />)
    const button = screen.getByTestId('build-action-button')

    await act(async () => {
      fireEvent.click(button)
    })

    expect(fetchMock).toHaveBeenCalledTimes(1)
    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(url).toBe('/api/build/start')
    expect(init.method).toBe('POST')
    const body = JSON.parse(init.body as string) as { chart_id: string; ayanamsha_role: string }
    expect(body.chart_id).toBe('chart-1')
    expect(body.ayanamsha_role).toBe('jh_true_chitra')

    await waitFor(() => {
      expect(eventSources.length).toBe(1)
    })
    expect(eventSources[0]!.url).toBe('/api/build/events/build-abc')
  })

  it('renders outer + inner progress lines when an event arrives', async () => {
    mockFetch({ status: 200, body: { build_id: 'build-xyz' } })
    render(<BuildActionPanel chartId="chart-1" />)
    await act(async () => {
      fireEvent.click(screen.getByTestId('build-action-button'))
    })
    await waitFor(() => expect(eventSources.length).toBe(1))

    const es = eventSources[0]!
    await act(async () => {
      es.onmessage?.(
        new MessageEvent('message', {
          data: JSON.stringify({
            asset: 'L1.FORENSIC',
            asset_index: 3,
            asset_total: 12,
            stage: 'persist',
            status: 'started',
            message: 'writing canonical row',
          }),
        }),
      )
    })

    expect(screen.getByTestId('build-progress-outer')).toHaveTextContent(/3 of 12/)
    expect(screen.getByTestId('build-progress-outer')).toHaveTextContent(/L1\.FORENSIC/)
    expect(screen.getByTestId('build-progress-inner')).toHaveTextContent(/persist/)
    expect(screen.getByTestId('build-progress-inner')).toHaveTextContent(/started/)
  })

  it('moves to done when a terminal status arrives', async () => {
    mockFetch({ status: 200, body: { build_id: 'build-done' } })
    render(<BuildActionPanel chartId="chart-1" />)
    await act(async () => {
      fireEvent.click(screen.getByTestId('build-action-button'))
    })
    await waitFor(() => expect(eventSources.length).toBe(1))
    const es = eventSources[0]!
    await act(async () => {
      es.onmessage?.(
        new MessageEvent('message', {
          data: JSON.stringify({ status: 'complete', stage: 'final' }),
        }),
      )
    })
    expect(screen.getByTestId('build-done')).toBeInTheDocument()
    // Button flips back to "Rebuild" — startable again.
    expect(screen.getByTestId('build-action-button')).toHaveTextContent(/rebuild/i)
  })
})

describe('BuildActionPanel — kill-switch', () => {
  it('surfaces a 503 as the disabled-by-flag message', async () => {
    mockFetch({ status: 503, body: { error: 'build_trigger_disabled' } })
    render(<BuildActionPanel chartId="chart-1" />)
    await act(async () => {
      fireEvent.click(screen.getByTestId('build-action-button'))
    })
    expect(screen.getByTestId('build-error')).toHaveTextContent(/disabled/i)
    expect(eventSources.length).toBe(0)
  })
})

describe('BuildActionPanel — failure path', () => {
  it('surfaces a non-503 error response', async () => {
    mockFetch({ status: 500, body: 'enqueue blew up' })
    render(<BuildActionPanel chartId="chart-1" />)
    await act(async () => {
      fireEvent.click(screen.getByTestId('build-action-button'))
    })
    expect(screen.getByTestId('build-error')).toHaveTextContent(/Build start failed \(500\)/)
  })
})
