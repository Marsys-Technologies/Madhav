/**
 * SSE route fallback behaviour.
 *
 * Actual route/ReadableStream lifecycle with only auth, SQL and SDK transport mocked.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { NextRequest } from 'next/server'

// ─── hoisted mocks (must precede vi.mock calls) ───────────────────────────────

const { mockCreateSubscription, mockClientClose, MockPubSub } = vi.hoisted(() => {
  const mockCreateSubscription = vi.fn()
  const mockClientClose = vi.fn()
  // Must use `function`, not an arrow, so `new MockPubSub()` works.
  const MockPubSub = vi.fn().mockImplementation(function () {
    return {
      topic: vi.fn().mockReturnValue({
        createSubscription: mockCreateSubscription,
      }),
      close: mockClientClose,
    }
  })
  return { mockCreateSubscription, mockClientClose, MockPubSub }
})

vi.mock('@google-cloud/pubsub', () => ({ PubSub: MockPubSub }))

const mockQuery = vi.fn()
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

const mockGetServerUser = vi.fn()
vi.mock('@/lib/firebase/server', () => ({ getServerUser: mockGetServerUser }))

// ─── helpers ──────────────────────────────────────────────────────────────────

const CHART_ID = 'test-chart-abc'
const SUPER_ADMIN = { uid: 'admin-1' }

function makeRequest(chartId = CHART_ID, signal?: AbortSignal): NextRequest {
  return new NextRequest(`http://localhost/api/cockpit/sse?chart_id=${chartId}&session_id=11111111-1111-4111-8111-111111111111&session_started_at=${Date.now()}`, { signal })
}

function makeSubscription() {
  return {
    on: vi.fn(),
    removeAllListeners: vi.fn(),
    close: vi.fn().mockResolvedValue(undefined),
    delete: vi.fn().mockResolvedValue(undefined),
  }
}

function deferred<T>() {
  let resolve!: (value: T) => void
  let reject!: (reason: Error) => void
  const promise = new Promise<T>((res, rej) => { resolve = res; reject = rej })
  return { promise, resolve, reject }
}

async function cancelAndSettle(reader: ReadableStreamDefaultReader<Uint8Array>): Promise<void> {
  const cancellation = reader.cancel()
  await vi.advanceTimersByTimeAsync(35_000)
  await cancellation
}

async function readFirstFrame(response: Response): Promise<string> {
  const reader = response.body!.getReader()
  const { value } = await reader.read()
  await cancelAndSettle(reader)
  return new TextDecoder().decode(value)
}

// ─── tests ────────────────────────────────────────────────────────────────────

describe('GET /api/cockpit/sse', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    vi.clearAllMocks()
    mockCreateSubscription.mockReset()
    mockClientClose.mockReset().mockResolvedValue(undefined)
    vi.stubEnv('GOOGLE_CLOUD_PROJECT', 'madhav-astrology')
    vi.stubEnv('PUBSUB_DISABLED', '')

    mockGetServerUser.mockResolvedValue(SUPER_ADMIN)
    mockQuery.mockResolvedValue({ rows: [{ role: 'super_admin' }] })
  })

  afterEach(() => {
    vi.clearAllTimers()
    vi.useRealTimers()
    vi.restoreAllMocks()
    vi.unstubAllEnvs()
  })

  it('falls back to pollingStream (not heartbeat-only) when subscription creation throws', async () => {
    mockCreateSubscription.mockRejectedValue(new Error('PERMISSION_DENIED: subscription create failed'))

    const { GET } = await import('../route')
    const res = await GET(makeRequest())

    expect(res.status).toBe(200)
    expect(res.headers.get('Content-Type')).toBe('text/event-stream')

    const firstFrame = await readFirstFrame(res)

    // Both paths now emit a named hello event: `event: hello\ndata: {...}\n\n`
    expect(firstFrame).toMatch(/^event: hello\n/)
    expect(firstFrame).toContain(CHART_ID)
    expect(mockClientClose).toHaveBeenCalledTimes(1)
    expect(vi.getTimerCount()).toBe(0)
  })

  it('uses Pub/Sub stream when subscription creation succeeds', async () => {
    const mockSub = makeSubscription()
    mockCreateSubscription.mockResolvedValue([mockSub])

    const { GET } = await import('../route')
    const res = await GET(makeRequest())

    expect(res.status).toBe(200)
    expect(Object.fromEntries(res.headers)).toEqual({
      'cache-control': 'no-cache, no-transform',
      connection: 'keep-alive',
      'content-type': 'text/event-stream',
      'x-accel-buffering': 'no',
    })

    const firstFrame = await readFirstFrame(res)

    // pubsubStream emits a named hello event
    expect(firstFrame).toMatch(/^event: hello\n/)
    expect(firstFrame).toContain(CHART_ID)
    expect(mockCreateSubscription).toHaveBeenCalledExactlyOnceWith(expect.stringMatching(/^cockpit-sse-/), {
      expirationPolicy: { ttl: { seconds: 86400 } },
      filter: `attributes.chart_id = "${CHART_ID}"`,
      messageRetentionDuration: { seconds: 600 },
      gaxOpts: { timeout: 5000, retry: null, maxRetries: 0 },
    })
    expect(mockSub.removeAllListeners).toHaveBeenCalledTimes(1)
    expect(mockSub.close).toHaveBeenCalledTimes(1)
    expect(mockSub.delete).toHaveBeenCalledTimes(1)
    expect(mockClientClose).toHaveBeenCalledTimes(1)
    expect(vi.getTimerCount()).toBe(0)
  })

  it.each([false, true])('emits a browser-visible named heartbeat and removes its timer (polling=%s)', async (polling) => {
    vi.stubEnv('PUBSUB_DISABLED', polling ? '1' : '')
    mockCreateSubscription.mockResolvedValue([makeSubscription()])
    const { GET } = await import('../route')
    const res = await GET(makeRequest())
    const reader = res.body!.getReader()
    await reader.read()
    await vi.advanceTimersByTimeAsync(10_000)
    const frame = await reader.read()
    expect(new TextDecoder().decode(frame.value)).toBe('event: heartbeat\ndata: {}\n\n')
    await cancelAndSettle(reader)
    expect(vi.getTimerCount()).toBe(0)
  })

  it.each([false, true])('closes at the deterministic nominal 20s deadline without an abort signal (polling=%s)', async (polling) => {
    vi.stubEnv('PUBSUB_DISABLED', polling ? '1' : '')
    const sub = makeSubscription()
    mockCreateSubscription.mockResolvedValue([sub])
    const { GET } = await import('../route')
    const reader = (await GET(makeRequest())).body!.getReader()
    await reader.read()
    await vi.advanceTimersByTimeAsync(20_000)
    let heartbeats = 0
    while (true) {
      const frame = await reader.read()
      if (frame.done) break
      expect(new TextDecoder().decode(frame.value)).toContain('event: heartbeat')
      heartbeats += 1
    }
    expect(heartbeats).toBe(1)
    expect(sub.delete).toHaveBeenCalledTimes(polling ? 0 : 1)
    expect(vi.getTimerCount()).toBe(0)
  })

  it.each(['missing', 'future', 'expired', 'malformed'] as const)('rejects %s sessions before SDK allocation', async (kind) => {
    const req = makeRequest()
    if (kind === 'missing') req.nextUrl.searchParams.delete('session_id')
    if (kind === 'future') req.nextUrl.searchParams.set('session_started_at', String(Date.now() + 5001))
    if (kind === 'expired') req.nextUrl.searchParams.set('session_started_at', String(Date.now() - 35_000))
    if (kind === 'malformed') req.nextUrl.searchParams.set('session_id', 'not-a-uuid')
    const { GET } = await import('../route')
    expect((await GET(req)).status).toBe(kind === 'expired' ? 204 : 400)
    expect(MockPubSub).not.toHaveBeenCalled()
    expect(vi.getTimerCount()).toBe(0)
  })

  it('does not attach to or delete a deterministic subscription owned by another request', async () => {
    const first = makeSubscription()
    mockCreateSubscription.mockResolvedValueOnce([first]).mockRejectedValueOnce(Object.assign(new Error('already exists'), { code: 6 }))
    const { GET } = await import('../route')
    const res = await GET(makeRequest())
    expect((await GET(makeRequest())).status).toBe(204)
    expect(mockCreateSubscription.mock.calls[0][0]).toBe(mockCreateSubscription.mock.calls[1][0])
    expect(first.delete).not.toHaveBeenCalled()
    expect(first.on).toHaveBeenCalledTimes(2)
    await cancelAndSettle(res.body!.getReader())
    expect(first.delete).toHaveBeenCalledTimes(1)
    expect(vi.getTimerCount()).toBe(0)
  })

  it.each(['resolve', 'reject'] as const)('ends a pending creation at the session deadline and cleans up a late %s', async settlement => {
    const pending = deferred<ReturnType<typeof makeSubscription>[]>()
    mockCreateSubscription.mockReturnValue(pending.promise)
    const { GET } = await import('../route')
    const response = GET(makeRequest())
    await vi.waitFor(() => expect(mockCreateSubscription).toHaveBeenCalledTimes(1))
    await vi.advanceTimersByTimeAsync(35_000)
    expect(await (await response).text()).toBe('')
    const sub = makeSubscription()
    if (settlement === 'resolve') pending.resolve([sub])
    else pending.reject(new Error('late failed create'))
    await vi.waitFor(() => expect(mockClientClose).toHaveBeenCalledTimes(1))
    expect(sub.delete).toHaveBeenCalledTimes(settlement === 'resolve' ? 1 : 0)
    expect(sub.on).not.toHaveBeenCalled()
    expect(vi.getTimerCount()).toBe(0)
  })

  it('attempts deletion independently of hung subscriber close and bounds cleanup waiting', async () => {
    const sub = makeSubscription()
    sub.close.mockReturnValue(new Promise(() => {}))
    mockCreateSubscription.mockResolvedValue([sub])
    const error = vi.spyOn(console, 'error').mockImplementation(() => {})
    const { GET } = await import('../route')
    const res = await GET(makeRequest())
    const cancellation = res.body!.cancel()
    expect(sub.delete).not.toHaveBeenCalled()
    await vi.advanceTimersByTimeAsync(35_000)
    await cancellation
    expect(mockClientClose).toHaveBeenCalledTimes(1)
    expect(error).toHaveBeenCalledWith('[sse] subscription close failed:', expect.any(String), expect.stringContaining('unverified'))
    expect(vi.getTimerCount()).toBe(0)
  })

  it('preserves deadline/no-retry options through the installed SDK without a provider transport', async () => {
    const { PubSub } = await vi.importActual<typeof import('@google-cloud/pubsub')>('@google-cloud/pubsub')
    const client = new PubSub({ projectId: 'offline-fixture' })
    const request = vi.spyOn(client, 'request').mockImplementation((config, callback) => {
      callback(null, [])
    })
    const gaxOpts = { timeout: 5000, retry: null, maxRetries: 0 }
    const [subscription] = await client.topic('fixture-topic').createSubscription('test-session', { gaxOpts })
    expect(request.mock.calls[0][0]).toMatchObject({ method: 'createSubscription', gaxOpts })
    await subscription.delete(gaxOpts)
    expect(request.mock.calls[1][0]).toMatchObject({ method: 'deleteSubscription', gaxOpts })
    await subscription.close()
    await client.close()
  })

  it('accepts bounded positive clock skew while preserving a maximum 35s admission lifetime', async () => {
    const req = makeRequest()
    req.nextUrl.searchParams.set('session_started_at', String(Date.now() + 5000))
    const sub = makeSubscription()
    mockCreateSubscription.mockResolvedValue([sub])
    const { GET } = await import('../route')
    const response = await GET(req)
    expect(response.status).toBe(200)
    await vi.advanceTimersByTimeAsync(24_999)
    expect(sub.delete).not.toHaveBeenCalled()
    await vi.advanceTimersByTimeAsync(1)
    expect(sub.delete).toHaveBeenCalledTimes(1)
    expect((await GET(new NextRequest(req.url))).status).toBe(204)
    expect(mockCreateSubscription).toHaveBeenCalledTimes(1)
    expect(vi.getTimerCount()).toBe(0)
  })

  it('reserves the owned name after early cancellation, rejects duplicates, then rejects expired replays before allocation', async () => {
    let exists = false
    const sub = makeSubscription()
    sub.delete.mockImplementation(async () => { exists = false })
    mockCreateSubscription.mockImplementation(async () => {
      if (exists) throw Object.assign(new Error('already exists'), { code: 6 })
      exists = true
      return [sub]
    })
    const req = makeRequest()
    const { GET } = await import('../route')
    const response = await GET(req)
    const canceled = response.body!.cancel()
    expect(sub.close).toHaveBeenCalledTimes(1)
    expect(sub.delete).not.toHaveBeenCalled()
    await vi.advanceTimersByTimeAsync(19_999)
    expect((await GET(new NextRequest(req.url))).status).toBe(204)
    expect(sub.delete).not.toHaveBeenCalled()
    expect(sub.on).toHaveBeenCalledTimes(2)
    await vi.advanceTimersByTimeAsync(1)
    await canceled
    expect(sub.delete).toHaveBeenCalledTimes(1)
    expect((await GET(new NextRequest(req.url))).status).toBe(204)
    expect(mockCreateSubscription).toHaveBeenCalledTimes(2)
    expect(exists).toBe(false)
    expect(vi.getTimerCount()).toBe(0)
  })

  it('keeps normal-expiry response alive for bounded deletion then reports an ambiguous timeout', async () => {
    const sub = makeSubscription()
    sub.delete.mockReturnValue(new Promise(() => {}))
    mockCreateSubscription.mockResolvedValue([sub])
    const error = vi.spyOn(console, 'error').mockImplementation(() => {})
    const { GET } = await import('../route')
    const response = await GET(makeRequest())
    let ended = false
    const body = response.text().then(() => { ended = true })
    await vi.advanceTimersByTimeAsync(20_000)
    expect(sub.delete).toHaveBeenCalledTimes(1)
    expect(ended).toBe(false)
    await vi.advanceTimersByTimeAsync(4_999)
    expect(ended).toBe(false)
    await vi.advanceTimersByTimeAsync(1)
    await body
    expect(error).toHaveBeenCalledWith('[sse] subscription delete failed:', expect.any(String), expect.stringContaining('unverified'))
    expect(vi.getTimerCount()).toBe(0)
  })

  it('ends within 35s even with +5s clock skew and all cleanup operations hung', async () => {
    const sub = makeSubscription()
    sub.close.mockReturnValue(new Promise(() => {}))
    sub.delete.mockReturnValue(new Promise(() => {}))
    mockClientClose.mockReturnValue(new Promise(() => {}))
    mockCreateSubscription.mockResolvedValue([sub])
    vi.spyOn(console, 'error').mockImplementation(() => {})
    const req = makeRequest()
    req.nextUrl.searchParams.set('session_started_at', String(Date.now() + 5000))
    const { GET } = await import('../route')
    let ended = false
    const response = await GET(req)
    const body = response.text().then(() => { ended = true })
    await vi.advanceTimersByTimeAsync(34_999)
    expect(ended).toBe(false)
    await vi.advanceTimersByTimeAsync(1)
    await body
    expect(sub.delete).toHaveBeenCalledTimes(1)
    expect(mockClientClose).toHaveBeenCalledTimes(1)
    expect(vi.getTimerCount()).toBe(0)
  })

  it('returns 200 + poll path when PUBSUB_DISABLED is set', async () => {
    process.env.PUBSUB_DISABLED = '1'

    const { GET } = await import('../route')
    const res = await GET(makeRequest())

    expect(res.status).toBe(200)
    const firstFrame = await readFirstFrame(res)
    expect(firstFrame).toMatch(/^event: hello\n/)
    expect(vi.getTimerCount()).toBe(0)
  })

  it('returns 403 for unauthenticated requests', async () => {
    mockGetServerUser.mockResolvedValue(null)

    const { GET } = await import('../route')
    const res = await GET(makeRequest())

    expect(res.status).toBe(403)
  })

  it('returns 400 when chart_id is missing', async () => {
    const { GET } = await import('../route')
    const res = await GET(new NextRequest('http://localhost/api/cockpit/sse'))

    expect(res.status).toBe(400)
  })

  it.each([false, true])('does no stream work for an already aborted request (polling=%s)', async (polling) => {
    vi.stubEnv('PUBSUB_DISABLED', polling ? '1' : '')
    const controller = new AbortController()
    controller.abort()
    const { GET } = await import('../route')
    mockCreateSubscription.mockResolvedValue([makeSubscription()])
    const res = await GET(makeRequest(CHART_ID, controller.signal))

    expect(MockPubSub).not.toHaveBeenCalled()
    expect(mockQuery.mock.calls.filter(([sql]) => /FROM build_runs/.test(sql))).toHaveLength(0)
    expect(vi.getTimerCount()).toBe(0)
    await res.body?.cancel()
  })

  it.each(['resolve', 'reject'] as const)('does not open a stream/fallback when aborted during create then %s', async (settlement) => {
    const pending = deferred<ReturnType<typeof makeSubscription>[]>()
    mockCreateSubscription.mockReturnValue(pending.promise)
    const controller = new AbortController()
    const { GET } = await import('../route')
    const response = GET(makeRequest(CHART_ID, controller.signal))
    // Drain auth/permission/import microtasks until the SDK request is outstanding.
    await vi.waitFor(() => expect(mockCreateSubscription).toHaveBeenCalledTimes(1))
    controller.abort()
    const sub = makeSubscription()
    if (settlement === 'resolve') pending.resolve([sub])
    else pending.reject(new Error('creation failed after abort'))
    await vi.advanceTimersByTimeAsync(35_000)
    const res = await response

    expect(sub.on).not.toHaveBeenCalled()
    expect(sub.close).toHaveBeenCalledTimes(settlement === 'resolve' ? 1 : 0)
    expect(sub.delete).toHaveBeenCalledTimes(settlement === 'resolve' ? 1 : 0)
    expect(mockClientClose).toHaveBeenCalledTimes(1)
    expect(mockQuery.mock.calls.filter(([sql]) => /FROM build_runs/.test(sql))).toHaveLength(0)
    expect(vi.getTimerCount()).toBe(0)
    expect(await res.text()).toBe('')
  })

  it('joins abort and body cancellation into one cleanup and closes the body before SDK deletion settles', async () => {
    const deletion = deferred<void>()
    const sub = makeSubscription()
    sub.delete.mockReturnValue(deletion.promise)
    mockCreateSubscription.mockResolvedValue([sub])
    const controller = new AbortController()
    const { GET } = await import('../route')
    const res = await GET(makeRequest(CHART_ID, controller.signal))
    const reader = res.body!.getReader()
    await reader.read()
    controller.abort()
    expect(await reader.read()).toEqual({ done: true, value: undefined })
    await cancelAndSettle(reader)
    deletion.resolve()
    await vi.waitFor(() => expect(mockClientClose).toHaveBeenCalledTimes(1))
    expect(sub.close).toHaveBeenCalledTimes(1)
    expect(sub.delete).toHaveBeenCalledTimes(1)
    expect(sub.removeAllListeners).toHaveBeenCalledTimes(1)
    expect(vi.getTimerCount()).toBe(0)
  })

  it.each([5, 7])('contains delete failure code %s, releases client and reports only genuine cleanup failure', async (code) => {
    const sub = makeSubscription()
    sub.delete.mockRejectedValue(Object.assign(new Error('delete outcome'), { code }))
    mockCreateSubscription.mockResolvedValue([sub])
    const error = vi.spyOn(console, 'error').mockImplementation(() => {})
    const { GET } = await import('../route')
    await readFirstFrame(await GET(makeRequest()))
    expect(sub.close).toHaveBeenCalledTimes(1)
    expect(mockClientClose).toHaveBeenCalledTimes(1)
    expect(error.mock.calls.filter(([label]) => String(label).includes('delete failed'))).toHaveLength(code === 5 ? 0 : 1)
    expect(vi.getTimerCount()).toBe(0)
  })

  it('still deletes and closes the client if closing the subscriber fails', async () => {
    const sub = makeSubscription()
    sub.close.mockRejectedValue(new Error('subscriber close failed'))
    mockCreateSubscription.mockResolvedValue([sub])
    vi.spyOn(console, 'error').mockImplementation(() => {})
    const { GET } = await import('../route')
    await readFirstFrame(await GET(makeRequest()))
    expect(sub.delete).toHaveBeenCalledTimes(1)
    expect(mockClientClose).toHaveBeenCalledTimes(1)
  })

  it('preserves named Pub/Sub payload forwarding and acknowledgment', async () => {
    const sub = makeSubscription()
    mockCreateSubscription.mockResolvedValue([sub])
    const { GET } = await import('../route')
    const res = await GET(makeRequest())
    const reader = res.body!.getReader()
    await reader.read()
    const raw = JSON.stringify({ type: 'asset.substep', chart_id: CHART_ID, asset_id: 'ga_positions', index: 1, total: 2 })
    const message = { data: Buffer.from(raw), ack: vi.fn(), nack: vi.fn() }
    sub.on.mock.calls.find(([event]) => event === 'message')![1](message)
    const frame = await reader.read()
    expect(new TextDecoder().decode(frame.value)).toBe(`event: asset.substep\ndata: ${raw}\n\n`)
    expect(message.ack).toHaveBeenCalledTimes(1)
    expect(message.nack).not.toHaveBeenCalled()
    await cancelAndSettle(reader)
  })

  it.each(['cancel', 'abort'])('stops polling on %s and suppresses a late query without issuing progress SQL', async (termination) => {
    vi.stubEnv('PUBSUB_DISABLED', '1')
    const pending = deferred<{ rows: { id: string; state: string }[] }>()
    let runReads = 0
    mockQuery.mockImplementation((sql: string) => {
      if (/FROM build_runs/.test(sql)) {
        runReads += 1
        return runReads === 1 ? Promise.resolve({ rows: [{ id: 'run-1', state: 'running' }] }) : pending.promise
      }
      return Promise.resolve({ rows: [{ role: 'super_admin' }] })
    })
    const { GET } = await import('../route')
    const controller = new AbortController()
    const res = await GET(makeRequest(CHART_ID, controller.signal))
    const reader = res.body!.getReader()
    await reader.read()
    vi.advanceTimersByTime(2_000)
    expect(runReads).toBe(2)
    if (termination === 'cancel') await cancelAndSettle(reader)
    else controller.abort()
    const callCount = mockQuery.mock.calls.length
    pending.resolve({ rows: [{ id: 'run-1', state: 'running' }] })
    await vi.advanceTimersByTimeAsync(60_000)
    expect(mockQuery).toHaveBeenCalledTimes(callCount)
    expect(vi.getTimerCount()).toBe(0)
  })
})
