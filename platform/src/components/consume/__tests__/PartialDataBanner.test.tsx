import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { PartialDataBanner, useChartDataReadiness } from '../PartialDataBanner'

const A = '00000000-0000-4000-8000-000000000001'
const B = '00000000-0000-4000-8000-000000000002'
const href = (id: string) => `/clients/${id}/nirmana`

function ready(chartId = A, status = 'partial', assets = ['asset-ready'], missing = ['asset-pending']) {
  return { chart_id: chartId, build_status: status, ready: assets, missing,
    partial_count: assets.length, total_count: assets.length + missing.length }
}

function Surface({ chartId, preparationHref }: { chartId: string; preparationHref?: string }) {
  const readiness = useChartDataReadiness(chartId)
  return <>
    <PartialDataBanner chartId={chartId} readiness={readiness} buildPreparationHref={preparationHref} />
    <output data-testid="ready-assets">{readiness.status === 'available' ? readiness.data.ready.join(',') : ''}</output>
  </>
}

function response(body: unknown, status = 200) {
  return { ok: status >= 200 && status < 300, status, json: vi.fn(async () => body) } as unknown as Response
}

function deferred<T>() {
  let resolve!: (value: T) => void
  const promise = new Promise<T>(done => { resolve = done })
  return { promise, resolve }
}

afterEach(() => { cleanup(); vi.unstubAllGlobals() })

describe('current Consult preparation status and navigation', () => {
  it('opens the exact preparation route using a link and performs only the readiness GET', async () => {
    const fetcher = vi.fn<typeof fetch>(async () => response(ready()))
    vi.stubGlobal('fetch', fetcher)
    render(<Surface chartId={A} preparationHref={href(A)} />)
    const link = await screen.findByRole('link', { name: 'Open Chart Preparation' })
    expect(link.getAttribute('href')).toBe(href(A))
    const followed: string[] = []
    link.addEventListener('click', event => { event.preventDefault(); followed.push(link.getAttribute('href')!) })
    fireEvent.click(link)
    expect(followed).toEqual([href(A)])
    expect(fetcher).toHaveBeenCalledTimes(1)
    expect(fetcher.mock.calls[0]).toEqual([`/api/build/data-readiness?chart_id=${A}`, expect.objectContaining({ signal: expect.any(AbortSignal) })])
    expect(screen.getByTestId('ready-assets').textContent).toBe('asset-ready')
  })

  it.each([undefined, href(B), 'https://example.invalid/preparation'])(
    'shows partial status without a preparation action for ineligible or mismatched href %s', async preparationHref => {
      vi.stubGlobal('fetch', vi.fn(async () => response(ready())))
      render(<Surface chartId={A} preparationHref={preparationHref} />)
      await screen.findByText('Chart partially built.')
      expect(screen.queryByRole('link')).toBeNull()
    },
  )

  it.each([401, 403, 404, 500])('discloses unavailable status for HTTP %s without consuming its error body', async status => {
    const result = response({ error: 'private diagnostic' }, status)
    vi.stubGlobal('fetch', vi.fn(async () => result))
    render(<Surface chartId={A} preparationHref={href(A)} />)
    await screen.findByText('Chart preparation status is unavailable.')
    expect(result.json).not.toHaveBeenCalled()
    expect(screen.queryByRole('link')).toBeNull()
    expect(screen.queryByText('private diagnostic')).toBeNull()
    expect(screen.getByTestId('ready-assets').textContent).toBe('')
  })

  it.each([
    null, [], {}, { ...ready(), chart_id: B }, { ...ready(), ready: 'asset-ready' },
    { ...ready(), missing: [1] }, { ...ready(), total_count: 200 },
    { ...ready(), partial_count: 9 }, { ...ready(), build_status: 'unknown' },
    { ...ready(), build_status: 'complete' },
  ])('refuses malformed or misbound readiness %#', async body => {
    vi.stubGlobal('fetch', vi.fn(async () => response(body)))
    render(<Surface chartId={A} preparationHref={href(A)} />)
    await screen.findByText('Chart preparation status is unavailable.')
    expect(screen.queryByRole('link')).toBeNull()
    expect(screen.getByTestId('ready-assets').textContent).toBe('')
  })

  it.each(['none', 'failed'])('displays incomplete status honestly for %s', async status => {
    vi.stubGlobal('fetch', vi.fn(async () => response(ready(A, status, [], ['asset-pending']))))
    render(<Surface chartId={A} preparationHref={href(A)} />)
    await screen.findByText('Chart preparation is incomplete.')
    expect(screen.getByTestId('ready-assets').textContent).toBe('')
  })

  it('keeps the no-banner result and publishes ready assets for valid complete status', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => response(ready(A, 'complete', ['asset-ready'], []))))
    render(<Surface chartId={A} preparationHref={href(A)} />)
    await waitFor(() => expect(screen.getByTestId('ready-assets').textContent).toBe('asset-ready'))
    expect(document.querySelector('[role="status"]')).toBeNull()
  })

  it('shows unavailable after network or invalid JSON failure', async () => {
    const fetcher = vi.fn().mockRejectedValueOnce(new Error('offline')).mockResolvedValueOnce({ ok: true, json: async () => { throw new SyntaxError('invalid') } })
    vi.stubGlobal('fetch', fetcher)
    const view = render(<Surface chartId={A} />)
    await screen.findByText('Chart preparation status is unavailable.')
    view.rerender(<Surface chartId={B} />)
    await waitFor(() => expect(fetcher).toHaveBeenCalledTimes(2))
    await screen.findByText('Chart preparation status is unavailable.')
  })

  it('binds response and suggestions to each request during A to B to A, including delayed JSON', async () => {
    const oldBody = deferred<unknown>()
    const b = deferred<Response>()
    const freshA = deferred<Response>()
    const fetcher = vi.fn().mockResolvedValueOnce({ ok: true, json: () => oldBody.promise })
      .mockReturnValueOnce(b.promise).mockReturnValueOnce(freshA.promise)
    vi.stubGlobal('fetch', fetcher)
    const view = render(<Surface chartId={A} preparationHref={href(A)} />)
    await waitFor(() => expect(fetcher).toHaveBeenCalledTimes(1))
    view.rerender(<Surface chartId={B} preparationHref={href(B)} />)
    expect(screen.getByTestId('ready-assets').textContent).toBe('')
    expect(fetcher.mock.calls[0][1]?.signal?.aborted).toBe(true)
    await act(async () => { b.resolve(response(ready(B, 'partial', ['asset-B'], ['pending-B']))) })
    expect(screen.getByTestId('ready-assets').textContent).toBe('asset-B')
    view.rerender(<Surface chartId={A} preparationHref={href(A)} />)
    expect(screen.getByTestId('ready-assets').textContent).toBe('')
    await act(async () => { oldBody.resolve(ready(A, 'partial', ['obsolete-A'], ['obsolete-pending'])) })
    expect(screen.getByTestId('ready-assets').textContent).toBe('')
    await act(async () => { freshA.resolve(response(ready(A, 'partial', ['fresh-A'], ['pending-A']))) })
    expect(screen.getByTestId('ready-assets').textContent).toBe('fresh-A')
    expect(screen.getByRole('link').getAttribute('href')).toBe(href(A))
  })

  it('aborts an unmounted request and ignores its late body', async () => {
    const body = deferred<unknown>()
    const fetcher = vi.fn<typeof fetch>(async () => ({ ok: true, json: () => body.promise }) as unknown as Response)
    vi.stubGlobal('fetch', fetcher)
    const view = render(<Surface chartId={A} />)
    await waitFor(() => expect(fetcher).toHaveBeenCalledTimes(1))
    view.unmount()
    expect(fetcher.mock.calls[0][1]?.signal?.aborted).toBe(true)
    await act(async () => { body.resolve(ready()) })
    expect(document.querySelector('[role="status"]')).toBeNull()
  })
})
