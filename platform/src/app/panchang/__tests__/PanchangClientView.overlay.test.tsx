import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { act, cleanup, fireEvent, render, renderHook, screen, waitFor } from '@testing-library/react'
import { type ReactNode } from 'react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { PanchangClientView } from '../components/PanchangClientView'
import { mapSidecarResponse, usePanchangDay, type NativeContext, type PanchangDay } from '../hooks/usePanchangDay'

const { push, params, listeners, recordStrip, recordAction } = vi.hoisted(() => ({
  push: vi.fn(),
  params: new URLSearchParams(),
  listeners: new Set<(user: { uid: string } | null) => void>(),
  recordStrip: vi.fn(),
  recordAction: vi.fn(),
}))

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push }),
  useSearchParams: () => params,
}))
vi.mock('firebase/auth', () => ({
  onAuthStateChanged: (_auth: unknown, listener: (user: { uid: string } | null) => void) => {
    listeners.add(listener)
    return () => listeners.delete(listener)
  },
}))
vi.mock('@/lib/firebase/client', () => ({ auth: {} }))
vi.mock('../hooks/useChartList', () => ({
  useChartList: () => ({ charts: [{ id: 'chart-a', name: 'A' }, { id: 'chart-b', name: 'B' }], isLoading: false }),
}))
vi.mock('../components/PrimaryStrip', () => ({
  PrimaryStrip: ({ nativeContext, panchangContext }: { nativeContext: NativeContext | null; panchangContext: PanchangDay }) => {
    recordStrip(nativeContext, panchangContext)
    return <div>{nativeContext?.native_name ?? 'Calendar only'}</div>
  },
}))
vi.mock('../components/ActionBar', async () => {
  const { panchangAskHref } = await import('../components/AskMadhavLink')
  return {
    ActionBar: ({ panchangContext, fixedChartId, selectedChartId }: {
      panchangContext?: PanchangDay
      fixedChartId?: string
      selectedChartId?: string | null
    }) => {
      recordAction(panchangContext)
      return <a href={panchangAskHref({
        chartId: selectedChartId, fixedChartId, prompt: 'Calendar details', context: panchangContext,
      })}>Ask from calendar</a>
    },
  }
})

const calendar = { date: '2026-05-20', lat: 20.27, lon: 85.84, tz_offset_minutes: 330 }
const options = { date: calendar.date, lat: calendar.lat, lon: calendar.lon, tzOffsetMinutes: 330 }
const seed = mapSidecarResponse({ panchang: calendar })
const contextA = storedOverlay('chart-a', 'A')
const contextB = storedOverlay('chart-b', 'B')
const fetchMock = vi.fn<typeof fetch>()

function storedOverlay(chartId: string, suffix: string): NativeContext {
  return {
    chart_id: chartId,
    native_name: `Synthetic overlay ${suffix}`,
    birth_nakshatra_id: 8,
    birth_nakshatra_name: 'Synthetic nakshatra',
    moon_sign_id: 4,
    moon_sign_name: 'Synthetic sign',
    active_dasha_lord: null,
    ayanamsha_id: 'lahiri_chitrapaksha',
    fact_ids: {
      birth_nakshatra_id: `private-fact-${suffix}-1`,
      birth_nakshatra_name: `private-fact-${suffix}-2`,
      moon_sign_id: `private-fact-${suffix}-3`,
      moon_sign_name: `private-fact-${suffix}-4`,
    },
  }
}

function response(nativeContext: NativeContext | null = null, panchang: Record<string, unknown> = calendar) {
  return Response.json({ panchang, native_context: nativeContext, native_context_error: nativeContext ? null : 'Chart overlay unavailable' })
}

function clientHarness() {
  const client = new QueryClient({ defaultOptions: { queries: { retryDelay: 0 } } })
  function Wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={client}>{children}</QueryClientProvider>
  }
  return { client, Wrapper }
}

function pendingRequest() {
  let resolve!: (value: Response) => void
  const promise = new Promise<Response>((done) => { resolve = done })
  return { promise, resolve }
}

function request(index: number) {
  const [url, init] = fetchMock.mock.calls[index] ?? []
  expect(url).toBe('/api/panchang')
  return { body: JSON.parse(String(init?.body)), signal: init?.signal }
}

function assertPublic(value: unknown) {
  const serialized = JSON.stringify(value)
  expect(serialized).not.toContain('private-fact')
  expect(serialized).not.toContain('Synthetic overlay')
  expect(serialized).not.toContain('native_context_error')
}

function emitSession(uid: string | null) {
  act(() => listeners.forEach((listener) => listener(uid === null ? null : { uid })))
}

beforeEach(() => {
  params.set('d', calendar.date)
  params.delete('chart_id')
  localStorage.clear()
  fetchMock.mockReset()
  recordStrip.mockClear()
  recordAction.mockClear()
  vi.stubGlobal('fetch', fetchMock)
})

afterEach(() => {
  cleanup()
  listeners.clear()
  vi.unstubAllGlobals()
})

describe('Panchang public calendar and private overlay', () => {
  it('uses the exact chartless SSR seed and deduplicates a different offset in the shared cache', async () => {
    const { client, Wrapper } = clientHarness()
    const input = { ...options, initialData: seed }
    const first = renderHook(usePanchangDay, { wrapper: Wrapper, initialProps: input })
    expect(first.result.current.data).toMatchObject(calendar)
    expect(fetchMock).not.toHaveBeenCalled()

    const deferred = pendingRequest()
    fetchMock.mockReturnValueOnce(deferred.promise)
    const changed = { ...input, tzOffsetMinutes: 345 }
    first.rerender(changed)
    const second = renderHook(usePanchangDay, { wrapper: Wrapper, initialProps: changed })
    expect(first.result.current.data).toBeUndefined()
    expect(second.result.current.data).toBeUndefined()
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1))
    expect(request(0).body).toEqual({ ...calendar, tz_offset_minutes: 345 })

    deferred.resolve(response(null, { ...calendar, tz_offset_minutes: 345 }))
    await waitFor(() => expect(second.result.current.data?.tz_offset_minutes).toBe(345))
    expect(first.result.current.data?.tz_offset_minutes).toBe(345)
    expect(client.getQueryCache().getAll().map(({ queryKey }) => queryKey)).toEqual([
      ['panchang', calendar.date, calendar.lat, calendar.lon, 330],
      ['panchang', calendar.date, calendar.lat, calendar.lon, 345],
    ])
  })

  it('keeps overlapping views isolated across abort, remount and late completion', async () => {
    const { client, Wrapper } = clientHarness()
    const lateA = pendingRequest()
    const pendingB = pendingRequest()
    const freshA = pendingRequest()
    fetchMock.mockReturnValueOnce(lateA.promise).mockReturnValueOnce(pendingB.promise).mockReturnValueOnce(freshA.promise)
    const a = renderHook(() => usePanchangDay({ ...options, chartId: 'chart-a' }), { wrapper: Wrapper })
    const b = renderHook(() => usePanchangDay({ ...options, chartId: 'chart-b' }), { wrapper: Wrapper })
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2))
    expect(request(0).body).toEqual({ ...calendar, chart_id: 'chart-a' })
    expect(request(1).body).toEqual({ ...calendar, chart_id: 'chart-b' })

    a.unmount()
    expect(request(0).signal?.aborted).toBe(true)
    const remount = renderHook(() => usePanchangDay({ ...options, chartId: 'chart-a' }), { wrapper: Wrapper })
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(3))
    expect(request(2).body).toEqual({ ...calendar, chart_id: 'chart-a' })

    pendingB.resolve(response(contextB))
    await waitFor(() => expect(b.result.current.nativeContext).toEqual(contextB))
    expect(remount.result.current.data).toMatchObject(calendar)
    expect(remount.result.current.nativeContext).toBeNull()

    await act(async () => {
      lateA.resolve(response(contextA, { ...calendar, tithi: { name: 'Aborted calendar', number: 1 } }))
      await lateA.promise
    })
    expect(remount.result.current.nativeContext).toBeNull()
    expect(remount.result.current.data?.angas.tithi).toBeNull()
    expect(b.result.current.nativeContext).toEqual(contextB)

    freshA.resolve(response(contextA))
    await waitFor(() => expect(remount.result.current.nativeContext).toEqual(contextA))
    expect(b.result.current.nativeContext).toEqual(contextB)
    const cached = client.getQueryCache().getAll()
    expect(cached).toHaveLength(1)
    assertPublic(cached.map(({ state }) => state.data))
    expect(fetchMock).toHaveBeenCalledTimes(3)
  })

  it('rechecks the same chart after the offset changes and changes back', async () => {
    const { Wrapper } = clientHarness()
    const oldOffset = pendingRequest()
    const revisited = pendingRequest()
    fetchMock.mockResolvedValueOnce(response(contextA)).mockReturnValueOnce(oldOffset.promise).mockReturnValueOnce(revisited.promise)
    const hook = renderHook(({ tzOffsetMinutes }) => usePanchangDay({ ...options, tzOffsetMinutes, chartId: 'chart-a' }), {
      wrapper: Wrapper, initialProps: { tzOffsetMinutes: 330 },
    })
    await waitFor(() => expect(hook.result.current.nativeContext).toEqual(contextA))

    hook.rerender({ tzOffsetMinutes: 345 })
    expect(hook.result.current.nativeContext).toBeNull()
    expect(hook.result.current.data).toBeUndefined()
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2))
    expect(request(1).body).toEqual({ ...calendar, chart_id: 'chart-a', tz_offset_minutes: 345 })

    hook.rerender({ tzOffsetMinutes: 330 })
    expect(hook.result.current.nativeContext).toBeNull()
    expect(hook.result.current.data).toMatchObject(calendar)
    expect(request(1).signal?.aborted).toBe(true)
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(3))
    expect(request(2).body).toEqual({ ...calendar, chart_id: 'chart-a' })
    await act(async () => {
      oldOffset.resolve(response(contextA))
      await oldOffset.promise
    })
    expect(hook.result.current.nativeContext).toBeNull()

    revisited.resolve(response())
    await waitFor(() => expect(hook.result.current.isLoading).toBe(false))
    expect(hook.result.current.nativeContext).toBeNull()
  })

  it('clears on URL chart change in the first render and shares only calendar with action and deep links', async () => {
    const { Wrapper } = clientHarness()
    const deferred = pendingRequest()
    fetchMock.mockResolvedValueOnce(response(contextA)).mockReturnValueOnce(deferred.promise)
    params.set('chart_id', 'chart-a')
    const view = render(<PanchangClientView initialData={seed} initialDate={calendar.date} />, { wrapper: Wrapper })
    expect(await screen.findByText(contextA.native_name)).toBeInTheDocument()
    expect(request(0).body.chart_id).toBe('chart-a')

    const href = screen.getByRole('link', { name: 'Ask from calendar' }).getAttribute('href')!
    const forwarded = new URL(href, 'https://fixture.invalid').searchParams.get('context')
    expect(JSON.parse(forwarded!)).toMatchObject(calendar)
    assertPublic(JSON.parse(forwarded!))
    assertPublic(recordAction.mock.calls)
    assertPublic(recordStrip.mock.calls.map(([, shared]) => shared))

    recordStrip.mockClear()
    params.set('chart_id', 'chart-b')
    view.rerender(<PanchangClientView initialData={seed} initialDate={calendar.date} />)
    expect(screen.queryByText(contextA.native_name)).toBeNull()
    expect(recordStrip.mock.calls[0]?.[0]).toBeNull()
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2))
    expect(request(1).body.chart_id).toBe('chart-b')
    deferred.resolve(response(contextB))
    expect(await screen.findByText(contextB.native_name)).toBeInTheDocument()

    params.delete('chart_id')
    view.rerender(<PanchangClientView initialData={seed} initialDate={calendar.date} />)
    expect(screen.queryByText(contextB.native_name)).toBeNull()
    expect(screen.getByText('Calendar only')).toBeInTheDocument()
  })

  it('preserves the fixed chart and the server cookie path when the SDK starts signed out', async () => {
    const { Wrapper } = clientHarness()
    fetchMock.mockResolvedValueOnce(response(contextA))
    params.set('chart_id', 'chart-b')
    render(<PanchangClientView initialData={seed} initialDate={calendar.date} fixedChartId="chart-a" />, { wrapper: Wrapper })
    await waitFor(() => expect(listeners.size).toBe(1))
    emitSession(null)
    expect(await screen.findByText(contextA.native_name)).toBeInTheDocument()
    expect(request(0).body.chart_id).toBe('chart-a')
    expect(screen.getByRole('link', { name: 'Ask from calendar' })).toHaveAttribute('href', '/clients/chart-a/pariprashna')
  })

  it('discards on observed account change and sign-out without dropping the warm public day', async () => {
    const { Wrapper } = clientHarness()
    const replacement = pendingRequest()
    fetchMock.mockResolvedValueOnce(response(contextA)).mockReturnValueOnce(replacement.promise)
    const hook = renderHook(() => usePanchangDay({ ...options, chartId: 'chart-a' }), { wrapper: Wrapper })
    await waitFor(() => expect(listeners.size).toBe(1))
    emitSession('session-a')
    await waitFor(() => expect(hook.result.current.nativeContext).toEqual(contextA))
    emitSession('session-b')
    expect(hook.result.current.nativeContext).toBeNull()
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2))

    emitSession(null)
    expect(request(1).signal?.aborted).toBe(true)
    expect(hook.result.current.data).toMatchObject(calendar)
    await act(async () => {
      replacement.resolve(response(contextA))
      await replacement.promise
    })
    expect(hook.result.current.nativeContext).toBeNull()
    expect(fetchMock).toHaveBeenCalledTimes(2)
  })

  it('clears warm context during refetch and preserves calendar on the paired server generic null', async () => {
    const { Wrapper } = clientHarness()
    const deferred = pendingRequest()
    fetchMock.mockResolvedValueOnce(response(contextA)).mockReturnValueOnce(deferred.promise)
    const hook = renderHook(() => usePanchangDay({ ...options, chartId: 'chart-a' }), { wrapper: Wrapper })
    await waitFor(() => expect(hook.result.current.nativeContext).toEqual(contextA))
    act(() => { hook.result.current.refetch() })
    expect(hook.result.current.nativeContext).toBeNull()
    expect(hook.result.current.data).toMatchObject(calendar)
    deferred.resolve(response(null, { ...calendar, tithi: { name: 'Refreshed calendar', number: 1 } }))
    await waitFor(() => expect(hook.result.current.data?.angas.tithi?.name).toBe('Refreshed calendar'))
    expect(fetchMock).toHaveBeenCalledTimes(2)
    expect(hook.result.current.nativeContext).toBeNull()
    expect(hook.result.current.isError).toBe(false)
  })

  it('clears warm private context on an unauthenticated refetch and retains the calendar', async () => {
    const { Wrapper } = clientHarness()
    fetchMock.mockResolvedValueOnce(response(contextA))
      .mockResolvedValueOnce(new Response(null, { status: 401 }))
      .mockResolvedValueOnce(new Response(null, { status: 401 }))
    const hook = renderHook(() => usePanchangDay({ ...options, chartId: 'chart-a' }), { wrapper: Wrapper })
    await waitFor(() => expect(hook.result.current.nativeContext).toEqual(contextA))
    act(() => { hook.result.current.refetch() })
    expect(hook.result.current.nativeContext).toBeNull()
    await waitFor(() => expect(hook.result.current.error?.message).toBe('Panchang fetch failed: HTTP 401'), { timeout: 2500 })
    expect(hook.result.current.data).toMatchObject(calendar)
    expect(hook.result.current.nativeContext).toBeNull()
    expect(fetchMock).toHaveBeenCalledTimes(3)
  })

  it('uses one cold chartless fallback for a legacy 403 and no extra fetch when the public cache is warm', async () => {
    const { Wrapper } = clientHarness()
    fetchMock.mockResolvedValueOnce(new Response(null, { status: 403 }))
      .mockResolvedValueOnce(Response.json(calendar))
      .mockResolvedValueOnce(new Response(null, { status: 403 }))
    const hook = renderHook(({ chartId }) => usePanchangDay({ ...options, chartId }), {
      wrapper: Wrapper, initialProps: { chartId: 'chart-a' },
    })
    await waitFor(() => expect(hook.result.current.data).toMatchObject(calendar))
    expect(request(1).body).toEqual(calendar)
    expect(hook.result.current.nativeContext).toBeNull()
    expect(hook.result.current.isError).toBe(false)

    hook.rerender({ chartId: 'chart-b' })
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(3))
    await waitFor(() => expect(hook.result.current.isLoading).toBe(false))
    expect(request(2).body).toEqual({ ...calendar, chart_id: 'chart-b' })
    expect(hook.result.current.data).toMatchObject(calendar)
    expect(hook.result.current.nativeContext).toBeNull()
    expect(fetchMock).toHaveBeenCalledTimes(3)
  })

  it.each([
    ['legacy overlay', { ...contextA, fact_ids: undefined, ayanamsha_id: undefined }],
    ['wrong chart', contextB],
    ['unsupported frame', { ...contextA, ayanamsha_id: 'invariant' }],
    ['partial facts', { ...contextA, fact_ids: { ...contextA.fact_ids!, moon_sign_name: '' } }],
    ['ambiguous facts', { ...contextA, fact_ids: { ...contextA.fact_ids!, moon_sign_name: contextA.fact_ids!.moon_sign_id } }],
  ])('retains the calendar and ignores %s', async (_name, received) => {
    const { client, Wrapper } = clientHarness()
    fetchMock.mockResolvedValueOnce(response(received, { ...calendar, native_context: received, native_context_error: 'generic' }))
    const hook = renderHook(() => usePanchangDay({ ...options, chartId: 'chart-a' }), { wrapper: Wrapper })
    await waitFor(() => expect(hook.result.current.data).toMatchObject(calendar))
    expect(hook.result.current.nativeContext).toBeNull()
    assertPublic(client.getQueryCache().getAll().map(({ state }) => state.data))
  })

  it('retries a calendar failure once and retains the existing error and Retry action', async () => {
    const { Wrapper } = clientHarness()
    fetchMock.mockResolvedValueOnce(new Response(null, { status: 500 }))
      .mockResolvedValueOnce(new Response(null, { status: 500 }))
      .mockResolvedValueOnce(Response.json(calendar))
    render(<PanchangClientView initialData={null} initialDate={calendar.date} />, { wrapper: Wrapper })
    expect(await screen.findByText('Panchang fetch failed: HTTP 500')).toBeInTheDocument()
    expect(fetchMock).toHaveBeenCalledTimes(2)
    fireEvent.click(screen.getByRole('button', { name: 'Retry' }))
    expect(await screen.findByText('Calendar only')).toBeInTheDocument()
    expect(fetchMock).toHaveBeenCalledTimes(3)
    expect(request(2).body).toEqual(calendar)
  })
})
