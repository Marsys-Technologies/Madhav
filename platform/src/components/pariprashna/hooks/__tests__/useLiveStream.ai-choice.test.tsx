import { act, cleanup, renderHook, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { useLiveStream } from '../useLiveStream'
import type { PariprashnaEvent } from '@/lib/pariprashna/protocol/events'
import { initialThreadState, makeInitialTurnState, threadReducer } from '../../state/reducer'
import { classifyPariprashnaError } from '@/lib/pariprashna/errors/classify'

const CONVERSATION_ID = '11111111-1111-4111-8111-111111111111'
const OTHER_CONVERSATION_ID = '22222222-2222-4222-8222-222222222222'
const selection = { kind: 'explicit', choice: {
  kind: 'provider_model', connectionId: '33333333-3333-4333-8333-333333333333', modelId: 'gpt-safe',
} } as const

function openEvent(conversationId = CONVERSATION_ID, turnId = 'server-turn'): PariprashnaEvent {
  return { type: 'turn.open', seq: 0, t: Date.now(), turn_id: turnId, conversation_id: conversationId,
    chart_id: 'chart-1', model_id: 'safe-display', reading_depth: 'auto', length_tier: 'standard' }
}

function closeEvent(seq: number, turnId = 'server-turn'): PariprashnaEvent {
  return { type: 'turn.close', seq, t: Date.now(), turn_id: turnId, status: 'ok', ms: 1 }
}

function streamResponse(events: PariprashnaEvent[]) {
  return new Response(events.map((event) => `data: ${JSON.stringify(event)}\n\n`).join(''), {
    status: 200, headers: { 'content-type': 'text/event-stream' },
  })
}

// Choice fixtures represent complete turns; truncation is tested separately.
function sse(conversationId: string, turnId: string) {
  return streamResponse([openEvent(conversationId, turnId), closeEvent(1, turnId)])
}

afterEach(() => {
  cleanup()
  vi.useRealTimers()
  vi.unstubAllEnvs()
  vi.unstubAllGlobals()
  vi.restoreAllMocks()
})

describe('useLiveStream AI choice lifecycle', () => {
  it('sends only strict ai_selection on feature-on, captures server conversation ID, and reuses it', async () => {
    const bodies: unknown[] = []
    let call = 0
    vi.stubGlobal('fetch', vi.fn(async (_url: RequestInfo | URL, init?: RequestInit) => {
      call += 1
      bodies.push(JSON.parse(String(init?.body)))
      return sse(CONVERSATION_ID, `server-turn-${call}`)
    }))
    const { result } = renderHook(() => useLiveStream('chart-1'))
    act(() => { result.current.submit('Question A', { reading_depth: 'auto', length_tier: 'standard', aiMode: { kind: 'byok', selection } }) })
    await waitFor(() => expect(result.current.conversationId).toBe(CONVERSATION_ID))
    expect(bodies[0]).toMatchObject({ ai_selection: selection })
    expect(bodies[0]).not.toHaveProperty('model_id')
    expect(bodies[0]).not.toHaveProperty('providerId')
    expect(bodies[0]).not.toHaveProperty('label')

    act(() => { result.current.submit('Question B', { reading_depth: 'auto', length_tier: 'standard', aiMode: { kind: 'byok', selection: { kind: 'default' } } }) })
    await waitFor(() => expect(bodies).toHaveLength(2))
    expect(bodies[1]).toMatchObject({ conversationId: CONVERSATION_ID, ai_selection: { kind: 'default' } })
    expect(bodies[1]).not.toHaveProperty('conversation_id')
    expect((bodies[0] as { ai_selection: unknown }).ai_selection).toEqual(selection)
  })

  it('keeps the feature-off legacy model request byte-compatible', async () => {
    let body: Record<string, unknown> = {}
    vi.stubGlobal('fetch', vi.fn(async (_url: RequestInfo | URL, init?: RequestInit) => {
      body = JSON.parse(String(init?.body))
      return sse(CONVERSATION_ID, 'legacy-turn')
    }))
    const { result } = renderHook(() => useLiveStream('chart-1'))
    act(() => { result.current.submit('Legacy', { aiMode: { kind: 'legacy', modelId: 'legacy-model' }, reading_depth: 'auto', length_tier: 'standard' }) })
    await waitFor(() => expect(body).toHaveProperty('model_id', 'legacy-model'))
    expect(body).not.toHaveProperty('ai_selection')
    expect(body).not.toHaveProperty('conversation_id')
    expect(body).not.toHaveProperty('client_request_id')
  })

  it('rejects a later mismatched server conversation ID without silently switching', async () => {
    let call = 0
    vi.stubGlobal('fetch', vi.fn(async () => {
      call += 1
      return sse(call === 1 ? CONVERSATION_ID : OTHER_CONVERSATION_ID, `server-turn-${call}`)
    }))
    const { result } = renderHook(() => useLiveStream('chart-1'))
    const signals: AbortSignal[] = []
    vi.mocked(fetch).mockImplementation(async (_url: RequestInfo | URL, init?: RequestInit) => {
      signals.push(init?.signal as AbortSignal)
      call += 1
      return sse(call === 1 ? CONVERSATION_ID : OTHER_CONVERSATION_ID, `server-turn-${call}`)
    })
    act(() => { result.current.submit('First', { aiMode: { kind: 'byok', selection } }) })
    await waitFor(() => expect(result.current.conversationId).toBe(CONVERSATION_ID))
    act(() => { result.current.submit('Second', { aiMode: { kind: 'byok', selection } }) })
    await waitFor(() => expect(result.current.state.turns.at(-1)?.status).toBe('errored'))
    expect(result.current.conversationId).toBe(CONVERSATION_ID)
    expect(signals[1]?.aborted).toBe(true)
  })

  it('aborts the old chart, resets thread identity, and never carries its conversation into the next chart', async () => {
    const bodies: Array<Record<string, unknown>> = []
    const signals: AbortSignal[] = []
    vi.stubGlobal('fetch', vi.fn(async (_url: RequestInfo | URL, init?: RequestInit) => {
      const signal = init?.signal as AbortSignal
      signals.push(signal)
      bodies.push(JSON.parse(String(init?.body)) as Record<string, unknown>)
      const index = bodies.length
      const event = { type: 'turn.open', seq: 0, t: Date.now(), turn_id: `turn-${index}`,
        conversation_id: index === 1 ? CONVERSATION_ID : OTHER_CONVERSATION_ID,
        chart_id: index === 1 ? 'chart-a' : 'chart-b', model_id: 'safe-display', reading_depth: 'auto', length_tier: 'standard' }
      const stream = new ReadableStream<Uint8Array>({
        start(controller) {
          controller.enqueue(new TextEncoder().encode(`data: ${JSON.stringify(event)}\n\n`))
          signal.addEventListener('abort', () => controller.close(), { once: true })
        },
      })
      return new Response(stream, { status: 200, headers: { 'content-type': 'text/event-stream' } })
    }))
    const { result, rerender } = renderHook(({ chartId }) => useLiveStream(chartId), { initialProps: { chartId: 'chart-a' } })
    act(() => { result.current.submit('Chart A', { aiMode: { kind: 'byok', selection } }) })
    await waitFor(() => expect(result.current.conversationId).toBe(CONVERSATION_ID))

    rerender({ chartId: 'chart-b' })
    expect(signals[0]?.aborted).toBe(true)
    expect(result.current.conversationId).toBeNull()
    expect(result.current.state.turns).toEqual([])

    act(() => { result.current.submit('Chart B', { aiMode: { kind: 'byok', selection: { kind: 'default' } } }) })
    await waitFor(() => expect(bodies).toHaveLength(2))
    expect(bodies[1]).toMatchObject({ chartId: 'chart-b', ai_selection: { kind: 'default' } })
    expect(bodies[1]).not.toHaveProperty('conversationId')
  })
})

describe('useLiveStream known-turn transport recovery', () => {
  async function flush(ms = 0) {
    await act(async () => { await vi.advanceTimersByTimeAsync(ms) })
  }

  function setup(resume: () => Promise<Response> | Response) {
    vi.useFakeTimers()
    const fetchMock = vi.fn(async (_url: RequestInfo | URL, init?: RequestInit) => {
      if (init?.method === 'POST') return streamResponse([openEvent()])
      return resume()
    })
    vi.stubGlobal('fetch', fetchMock)
    return fetchMock
  }

  it('resumes truncated HTTP 200 with the known server ID and no second POST', async () => {
    const fetchMock = setup(() => streamResponse([
      { type: 'block.commit', seq: 1, t: Date.now(), block_id: 'answer', text: 'Recovered answer' },
      closeEvent(2),
    ]))
    const { result } = renderHook(() => useLiveStream('chart-1'))
    act(() => { result.current.submit('Question') })
    await flush()
    expect(fetchMock).toHaveBeenCalledTimes(2)
    expect(fetchMock.mock.calls[0][1]?.method).toBe('POST')
    expect(fetchMock.mock.calls[1]).toEqual([
      '/api/pariprashna/resume?turn_id=server-turn&last_event_id=0',
      { method: 'GET', headers: { 'Last-Event-ID': '0' }, signal: expect.any(AbortSignal) },
    ])
    expect(result.current.state.turns[0]).toMatchObject({ status: 'settled', blocks: [{ id: 'answer', html: 'Recovered answer' }] })
    expect(result.current.conversationId).toBe(CONVERSATION_ID)
    expect(vi.getTimerCount()).toBe(0)
  })

  it('resumes another nonterminal EOF with the updated cursor and same adapter until terminal', async () => {
    let resumeCount = 0
    const fetchMock = setup(() => {
      resumeCount += 1
      if (resumeCount === 1) return streamResponse([
        { type: 'citation.define', seq: 1, t: Date.now(), index: 1, signal_id: 'known-fact', layer: 'L1', snippet: 'Grounded', grade: 'primary' },
      ])
      return streamResponse([
        { type: 'turn.commit', seq: 2, t: Date.now(), turn_id: 'server-turn', conversation_id: CONVERSATION_ID, message_id: 'saved-answer', status: 'ok', assistant_chars: 0 },
        closeEvent(3),
      ])
    })
    const { result } = renderHook(() => useLiveStream('chart-1'))
    act(() => { result.current.submit('Question') })
    await flush()
    expect(fetchMock).toHaveBeenCalledTimes(2)
    expect(result.current.state.turns[0].status).not.toBe('settled')
    await flush(999)
    expect(fetchMock).toHaveBeenCalledTimes(2)
    await flush(1)
    expect(fetchMock).toHaveBeenCalledTimes(3)
    expect(fetchMock.mock.calls[2][0]).toBe('/api/pariprashna/resume?turn_id=server-turn&last_event_id=1')
    expect(fetchMock.mock.calls[2][1]?.headers).toEqual({ 'Last-Event-ID': '1' })
    expect(fetchMock.mock.calls.map(([, init]) => init?.method)).toEqual(['POST', 'GET', 'GET'])
    expect(result.current.state.turns[0]).toMatchObject({
      status: 'settled', persistence: 'durable', persistedMessageId: 'saved-answer',
      grounding: { factorCount: 1, source: 'client_estimate' },
    })
    expect(vi.getTimerCount()).toBe(0)
  })

  it.each(['empty_eof', 'http_404', 'network_error'] as const)('bounds %s resumes and prevents visibility from restarting exhausted recovery', async (failure) => {
    const fetchMock = setup(() => {
      if (failure === 'http_404') return new Response(null, { status: 404 })
      if (failure === 'network_error') throw new TypeError('synthetic disconnected read')
      return streamResponse([])
    })
    vi.spyOn(document, 'visibilityState', 'get').mockReturnValue('visible')
    const { result } = renderHook(() => useLiveStream('chart-1'))
    act(() => { result.current.submit('Question') })
    await flush()
    expect(fetchMock).toHaveBeenCalledTimes(2)
    for (const delay of [1_000, 2_000, 4_000, 8_000]) await flush(delay)
    expect(fetchMock).toHaveBeenCalledTimes(6)
    expect(fetchMock.mock.calls.map(([, init]) => init?.method)).toEqual(['POST', 'GET', 'GET', 'GET', 'GET', 'GET'])
    expect(result.current.state.turns[0]).toMatchObject({ status: 'errored', error: { kind: 'network' } })
    act(() => { document.dispatchEvent(new Event('visibilitychange')) })
    await flush(30_000)
    expect(fetchMock).toHaveBeenCalledTimes(6)
    expect(vi.getTimerCount()).toBe(0)
  })

  it.each(['stop', 'unmount', 'chart_change', 'restore'] as const)('%s cancels backoff with no later read or generation request', async (cancel) => {
    const fetchMock = setup(() => streamResponse([]))
    const { result, unmount, rerender } = renderHook(({ chartId }) => useLiveStream(chartId), { initialProps: { chartId: 'chart-1' } })
    let turnId = ''
    act(() => { turnId = result.current.submit('Question') })
    await flush()
    expect(fetchMock).toHaveBeenCalledTimes(2)
    const resumeSignal = fetchMock.mock.calls[1][1]?.signal
    expect(resumeSignal?.aborted).toBe(false)
    expect(vi.getTimerCount()).toBe(1)
    act(() => {
      if (cancel === 'stop') result.current.stop(turnId)
      if (cancel === 'unmount') unmount()
      if (cancel === 'chart_change') rerender({ chartId: 'chart-2' })
      if (cancel === 'restore') result.current.restore(CONVERSATION_ID, [])
    })
    expect(resumeSignal?.aborted).toBe(true)
    await flush()
    expect(vi.getTimerCount()).toBe(0)
    await flush(30_000)
    expect(fetchMock).toHaveBeenCalledTimes(2)
    if (cancel === 'stop') expect(result.current.state.turns[0]).toMatchObject({ status: 'interrupted', interruptedReason: 'user_stop' })
    if (cancel === 'chart_change' || cancel === 'restore') expect(result.current.state.turns).toEqual([])
  })

  it.each(['stop', 'unmount'] as const)('%s aborts an active resumed body without reopening the turn', async (cancel) => {
    vi.useFakeTimers()
    const signals: AbortSignal[] = []
    const fetchMock = vi.fn(async (_url: RequestInfo | URL, init?: RequestInit) => {
      const signal = init?.signal as AbortSignal
      signals.push(signal)
      if (init?.method === 'POST') return streamResponse([openEvent()])
      return new Response(new ReadableStream<Uint8Array>({
        start(controller) {
          signal.addEventListener('abort', () => controller.error(new DOMException('Stopped', 'AbortError')), { once: true })
        },
      }), { status: 200 })
    })
    vi.stubGlobal('fetch', fetchMock)
    const { result, unmount } = renderHook(() => useLiveStream('chart-1'))
    let turnId = ''
    act(() => { turnId = result.current.submit('Question') })
    await flush()
    expect(fetchMock).toHaveBeenCalledTimes(2)
    act(() => { if (cancel === 'stop') result.current.stop(turnId); else unmount() })
    await flush(30_000)
    expect(signals[1].aborted).toBe(true)
    expect(fetchMock).toHaveBeenCalledTimes(2)
    expect(vi.getTimerCount()).toBe(0)
    if (cancel === 'stop') expect(result.current.state.turns[0].status).toBe('interrupted')
  })

  it.each(['stop', 'unmount'] as const)('%s preserves cancellation of the original BYOK request', async (cancel) => {
    vi.useFakeTimers()
    let signal: AbortSignal | undefined
    const fetchMock = vi.fn(async (_url: RequestInfo | URL, init?: RequestInit) => {
      signal = init?.signal as AbortSignal
      return new Response(new ReadableStream<Uint8Array>({
        start(controller) {
          controller.enqueue(new TextEncoder().encode(`data: ${JSON.stringify(openEvent())}\n\n`))
          signal?.addEventListener('abort', () => controller.close(), { once: true })
        },
      }), { status: 200 })
    })
    vi.stubGlobal('fetch', fetchMock)
    const { result, unmount } = renderHook(() => useLiveStream('chart-1'))
    let turnId = ''
    act(() => { turnId = result.current.submit('Question', { aiMode: { kind: 'byok', selection } }) })
    await flush()
    expect(result.current.conversationId).toBe(CONVERSATION_ID)
    act(() => { if (cancel === 'stop') result.current.stop(turnId); else unmount() })
    await flush(30_000)
    expect(signal?.aborted).toBe(true)
    expect(fetchMock).toHaveBeenCalledTimes(1)
    expect(vi.getTimerCount()).toBe(0)
    if (cancel === 'stop') expect(result.current.state.turns[0].status).toBe('interrupted')
  })

  it('discards a late resume response after restore without changing the restored turn', async () => {
    let resolveResume!: (response: Response) => void
    const fetchMock = setup(() => new Promise<Response>((resolve) => { resolveResume = resolve }))
    const { result } = renderHook(() => useLiveStream('chart-1'))
    act(() => { result.current.submit('Question') })
    await flush()
    expect(fetchMock).toHaveBeenCalledTimes(2)
    const resumeSignal = fetchMock.mock.calls[1][1]?.signal
    act(() => {
      result.current.restore(CONVERSATION_ID, [{ ...result.current.state.turns[0], status: 'settled' }])
    })
    const late = streamResponse([closeEvent(1)])
    const cancel = vi.spyOn(late.body!, 'cancel')
    resolveResume(late)
    await flush(30_000)
    expect(resumeSignal?.aborted).toBe(true)
    expect(cancel).toHaveBeenCalledOnce()
    expect(result.current.state.turns[0].status).toBe('settled')
    expect(fetchMock).toHaveBeenCalledTimes(2)
    expect(vi.getTimerCount()).toBe(0)
  })

  it.each(['closed', 'interrupted'] as const)('recognizes a terminal %s snapshot without requiring turn.close', async (status) => {
    const fetchMock = setup(() => streamResponse([
      { type: 'snapshot.apply', seq: 1, t: Date.now(), turn_id: 'server-turn', text: 'Preserved text', citations: [], turn_status: status },
    ]))
    const { result } = renderHook(() => useLiveStream('chart-1'))
    act(() => { result.current.submit('Question') })
    await flush(30_000)
    expect(fetchMock).toHaveBeenCalledTimes(2)
    expect(result.current.state.turns[0]).toMatchObject({
      status: status === 'closed' ? 'settling' : 'interrupted', blocks: [{ html: 'Preserved text' }],
      interruptedReason: status === 'interrupted' ? 'connection_lost' : null,
    })
    expect(vi.getTimerCount()).toBe(0)
  })

  it('keeps a terminal in-stream refusal without a retry or replacement POST', async () => {
    const fetchMock = setup(() => streamResponse([
      { type: 'error', seq: 1, t: Date.now(), code: 'FORBIDDEN', message: 'synthetic denial', retryable: false },
    ]))
    const { result } = renderHook(() => useLiveStream('chart-1'))
    act(() => { result.current.submit('Question') })
    await flush(30_000)
    expect(result.current.state.turns[0]).toMatchObject({ status: 'errored', error: { kind: 'not_authorized' } })
    expect(fetchMock).toHaveBeenCalledTimes(2)
    expect(vi.getTimerCount()).toBe(0)
  })

  it.each([200, 502])('reports zero-frame HTTP %i honestly without resubmitting or guessing a server ID', async (status) => {
    vi.useFakeTimers()
    const fetchMock = vi.fn(async () => new Response('', { status }))
    vi.stubGlobal('fetch', fetchMock)
    const { result } = renderHook(() => useLiveStream('chart-1'))
    act(() => { result.current.submit('Question') })
    await flush(30_000)
    expect(result.current.state.turns[0]).toMatchObject({ status: 'errored', error: { kind: 'network' } })
    expect(fetchMock).toHaveBeenCalledTimes(1)
    expect(vi.getTimerCount()).toBe(0)
  })
})

describe('useLiveStream durable readback after lost transport', () => {
  const chartId = '55555555-5555-4555-8555-555555555555'
  const nonce = '44444444-4444-4444-8444-444444444444'
  const serverTurnId = '66666666-6666-4666-8666-666666666666'
  const message = {
    id: '77777777-7777-4777-8777-777777777777', role: 'assistant',
    created_at: '2026-11-14T12:00:00.000Z', tagged: false, schema_version: 1,
    parts_json: [{ type: 'text', text: 'Fallback answer' }], metadata_json: {},
    canonical_parts: [
      { kind: 'text', body: { text: 'The exact saved answer' } },
      { kind: 'citation', body: { index: 1, signal_id: 'saved-fact', layer: 'L1', snippet: 'Saved citation', grade: 'primary' } },
    ],
  }
  const pending = () => Response.json({ status: 'pending', turnId: serverTurnId, conversationId: CONVERSATION_ID }, { status: 202 })
  const complete = () => Response.json({ status: 'complete', turnId: serverTurnId, conversationId: CONVERSATION_ID, message })
  const byok = { aiMode: { kind: 'byok', selection } } as const

  it('replaces only the exact client turn, rejects stale nonces, and preserves concurrent transcript turns', () => {
    let state = threadReducer(initialThreadState, { type: 'CLIENT_SUBMIT_TURN', turnId: 'first', userText: 'Original question' })
    state = threadReducer(state, { type: 'CLIENT_SUBMIT_TURN', turnId: 'other', userText: 'Other question' })
    const other = state.turns[1]
    state = threadReducer(state, { type: 'DURABLE_RECOVERY_STATUS', turnId: 'first', recovery: {
      clientRequestId: nonce, source: 'saved_answer', status: 'checking',
      originalErrorCode: 'NETWORK_HTTP_502', originalError: classifyPariprashnaError('NETWORK_HTTP_502'),
    } })
    const saved = makeInitialTurnState(message.id, '')
    saved.status = 'settled'
    saved.blocks = [{ id: message.id, kind: 'paragraph', html: 'The exact saved answer' }]
    const wrong = threadReducer(state, { type: 'DURABLE_TURN_RECOVERED', turnId: 'first', clientRequestId: 'stale-nonce', turn: saved })
    expect(wrong.turns[0]).toBe(state.turns[0])
    const restored = threadReducer(state, { type: 'DURABLE_TURN_RECOVERED', turnId: 'first', clientRequestId: nonce, turn: saved })
    expect(restored.turns[0]).toMatchObject({ id: 'first', userText: 'Original question', status: 'settled', transportRecovery: { status: 'recovered' } })
    expect(restored.turns[1]).toBe(other)
    const stopped = threadReducer(state, { type: 'CLIENT_STOP', turnId: 'first' })
    expect(threadReducer(stopped, { type: 'DURABLE_TURN_RECOVERED', turnId: 'first', clientRequestId: nonce, turn: saved }).turns[0].status).toBe('interrupted')
  })

  async function flush(ms = 0) {
    await act(async () => { await vi.advanceTimersByTimeAsync(ms) })
  }
  function setup(read: (init?: RequestInit) => Response | Promise<Response>, postStatus = 502) {
    vi.useFakeTimers()
    vi.spyOn(crypto, 'randomUUID').mockReturnValue(nonce)
    const fetchMock = vi.fn(async (_url: RequestInfo | URL, init?: RequestInit) => {
      if (init?.method === 'POST') return new Response('', { status: postStatus })
      return read(init)
    })
    vi.stubGlobal('fetch', fetchMock)
    return fetchMock
  }

  it('keeps reading past 60 seconds after HTTP 502, then restores the exact original answer with one POST', async () => {
    let started = 0
    const fetchMock = setup(() => Date.now() - started < 60_000 ? pending() : complete())
    started = Date.now()
    const { result } = renderHook(() => useLiveStream(chartId))
    let clientTurnId = ''
    act(() => { clientTurnId = result.current.submit('Original question', byok) })
    await flush(60_000)
    expect(result.current.state.turns[0].status).toBe('reconnecting')
    expect(result.current.state.turns[0].blocks).toEqual([])
    await flush(5_000)
    expect(result.current.state.turns).toHaveLength(1)
    expect(result.current.state.turns[0]).toMatchObject({
      id: clientTurnId, userText: 'Original question', status: 'settled', persistence: 'durable',
      persistedMessageId: message.id, blocks: [{ html: 'The exact saved answer' }],
      citations: { 1: { ref: 'saved-fact' } }, grounding: null,
      transportRecovery: { status: 'recovered', source: 'saved_answer', originalErrorCode: 'NETWORK_HTTP_502', originalError: { kind: 'network' } },
    })
    expect(result.current.conversationId).toBe(CONVERSATION_ID)
    const posts = fetchMock.mock.calls.filter(([, init]) => init?.method === 'POST')
    expect(posts).toHaveLength(1)
    expect(JSON.parse(String(posts[0][1]?.body))).toEqual({
      chartId, reading_depth: 'auto', length_tier: 'standard',
      ai_selection: selection, client_request_id: nonce,
      messages: [{ id: clientTurnId + '-user', role: 'user', parts: [{ type: 'text', text: 'Original question' }] }],
    })
    for (const [url, init] of fetchMock.mock.calls.slice(1)) {
      expect(url).toBe('/api/pariprashna/resume?chart_id=' + chartId + '&client_request_id=' + nonce)
      expect(init?.method).toBe('GET')
      expect(init?.cache).toBe('no-store')
      expect(init?.body).toBeUndefined()
    }
    expect(vi.getTimerCount()).toBe(0)
  })

  it('uses the same readback for a zero-frame HTTP 200 without claiming live completion', async () => {
    const fetchMock = setup(complete, 200)
    const { result } = renderHook(() => useLiveStream(chartId))
    act(() => { result.current.submit('Original question', byok) })
    await flush()
    expect(result.current.state.turns[0]).toMatchObject({
      status: 'settled', transportRecovery: { status: 'recovered', originalErrorCode: 'NETWORK_EOF' },
    })
    expect(fetchMock.mock.calls.map(([, init]) => init?.method)).toEqual(['POST', 'GET'])
  })

  it('does not apply a stale nonce response to a deliberate new turn', async () => {
    let resolveRead!: (response: Response) => void
    const fetchMock = setup(() => new Promise<Response>((resolve) => { resolveRead = resolve }))
    const { result } = renderHook(() => useLiveStream(chartId))
    act(() => { result.current.submit('Original question', byok) })
    await flush()
    const signal = fetchMock.mock.calls[1][1]?.signal
    act(() => {
      vi.mocked(crypto.randomUUID).mockReturnValue('99999999-9999-4999-8999-999999999999')
      fetchMock.mockImplementationOnce(async () => sse(CONVERSATION_ID, 'fresh-turn'))
      result.current.submit('New question', byok)
    })
    resolveRead(complete())
    await flush()
    expect(signal?.aborted).toBe(true)
    expect(result.current.state.turns).toHaveLength(2)
    expect(result.current.state.turns[0]).toMatchObject({ userText: 'Original question', status: 'errored', blocks: [] })
    expect(result.current.state.turns[1]).toMatchObject({ userText: 'New question', status: 'settled', blocks: [] })
    expect(result.current.state.turns.every((turn) => !turn.persistedMessageId)).toBe(true)
    expect(fetchMock).toHaveBeenCalledTimes(3)
    expect(vi.getTimerCount()).toBe(0)
  })

  it('uses the existing reader projection without promoting reasoning or tool payloads', async () => {
    setup(() => Response.json({ status: 'complete', turnId: serverTurnId, conversationId: CONVERSATION_ID, message: {
      ...message,
      parts_json: [...message.parts_json, { type: 'reasoning', text: 'Private reasoning' }],
      canonical_parts: [...message.canonical_parts,
        { kind: 'reasoning', body: { text: 'Private reasoning' } },
        { kind: 'tool_call', body: { call_id: 'private-call', tool_name: 'private-tool', args: {} } },
      ],
    } }))
    const { result } = renderHook(() => useLiveStream(chartId))
    act(() => { result.current.submit('Question', byok) })
    await flush()
    expect(result.current.state.turns[0]).toMatchObject({ status: 'settled', blocks: [{ html: 'The exact saved answer' }], activities: [], pendingPredictionCandidates: [] })
    expect(JSON.stringify(result.current.state.turns[0])).not.toMatch(/Private reasoning|private-call|private-tool/)
  })

  it.each(['pending', 'hung_read'] as const)('bounds %s by the 120-second recovery deadline and never re-POSTs', async (outcome) => {
    const fetchMock = setup((init) => outcome === 'pending' ? pending() : new Promise<Response>((_resolve, reject) => {
      init?.signal?.addEventListener('abort', () => reject(new DOMException('Read deadline', 'AbortError')), { once: true })
    }))
    const { result } = renderHook(() => useLiveStream(chartId))
    act(() => { result.current.submit('Question', byok) })
    await flush(120_000)
    expect(result.current.state.turns[0]).toMatchObject({ status: 'errored', transportRecovery: { status: 'unavailable' } })
    const calls = fetchMock.mock.calls.length
    expect(calls).toBeLessThanOrEqual(21)
    expect(fetchMock.mock.calls.filter(([, init]) => init?.method === 'POST')).toHaveLength(1)
    await flush(120_000)
    expect(fetchMock).toHaveBeenCalledTimes(calls)
    expect(vi.getTimerCount()).toBe(0)
  })

  it.each(['stop', 'unmount', 'chart_change', 'restore', 'new_submit'] as const)('%s cancels pending readback immediately and preserves other transcript turns', async (cancel) => {
    const fetchMock = setup(pending)
    const { result, unmount, rerender } = renderHook(({ chart }) => useLiveStream(chart), { initialProps: { chart: chartId } })
    let firstId = ''
    act(() => { firstId = result.current.submit('Original question', byok) })
    await flush()
    expect(fetchMock).toHaveBeenCalledTimes(2)
    const readSignal = fetchMock.mock.calls[1][1]?.signal
    act(() => {
      if (cancel === 'stop') result.current.stop(firstId)
      if (cancel === 'unmount') unmount()
      if (cancel === 'chart_change') rerender({ chart: '88888888-8888-4888-8888-888888888888' })
      if (cancel === 'restore') result.current.restore(OTHER_CONVERSATION_ID, [])
      if (cancel === 'new_submit') {
        vi.mocked(crypto.randomUUID).mockReturnValue('99999999-9999-4999-8999-999999999999')
        fetchMock.mockImplementationOnce(async () => sse(CONVERSATION_ID, 'fresh-turn'))
        result.current.submit('A deliberate new question', byok)
      }
    })
    await flush(120_000)
    expect(readSignal?.aborted).toBe(true)
    expect(fetchMock).toHaveBeenCalledTimes(cancel === 'new_submit' ? 3 : 2)
    expect(vi.getTimerCount()).toBe(0)
    if (cancel === 'new_submit') {
      expect(result.current.state.turns).toHaveLength(2)
      expect(result.current.state.turns[0]).toMatchObject({ id: firstId, status: 'errored', userText: 'Original question' })
      expect(result.current.state.turns[1]).toMatchObject({ userText: 'A deliberate new question', status: 'settled' })
      expect(JSON.parse(String(fetchMock.mock.calls[2][1]?.body)).client_request_id).not.toBe(nonce)
    }
  })

  it.each(['server_turn', 'conversation', 'role'] as const)('refuses wrong %s readback identity instead of replacing the current turn', async (wrong) => {
    let reads = 0
    const fetchMock = setup(() => {
      reads += 1
      if (reads === 1) return pending()
      return Response.json({ status: 'complete',
        turnId: wrong === 'server_turn' ? 'wrong-turn' : serverTurnId,
        conversationId: wrong === 'conversation' ? OTHER_CONVERSATION_ID : CONVERSATION_ID,
        message: wrong === 'role' ? { ...message, role: 'user' } : message,
      })
    })
    const { result } = renderHook(() => useLiveStream(chartId))
    act(() => { result.current.submit('Question', byok) })
    await flush(1_000)
    expect(result.current.state.turns[0]).toMatchObject({ status: 'errored', blocks: [], transportRecovery: { status: 'unavailable' } })
    expect(result.current.state.turns[0].persistedMessageId).toBeUndefined()
    expect(fetchMock).toHaveBeenCalledTimes(3)
  })

  it.each([401, 403, 404, 409, 500])('keeps readback HTTP %i as an error, never pending or a new POST', async (status) => {
    const fetchMock = setup(() => Response.json({ error: 'synthetic read failure' }, { status }))
    const { result } = renderHook(() => useLiveStream(chartId))
    act(() => { result.current.submit('Question', byok) })
    await flush(120_000)
    expect(result.current.state.turns[0]).toMatchObject({ status: 'errored', blocks: [], transportRecovery: { status: 'unavailable' } })
    expect(fetchMock).toHaveBeenCalledTimes(2)
    expect(vi.getTimerCount()).toBe(0)
  })

  it.each([401, 403, 409])('does not auto-retry a POST refusal with HTTP %i', async (status) => {
    const fetchMock = setup(complete, status)
    const { result } = renderHook(() => useLiveStream(chartId))
    act(() => { result.current.submit('Question', byok) })
    await flush(120_000)
    expect(result.current.state.turns[0].status).toBe('errored')
    expect(fetchMock).toHaveBeenCalledTimes(1)
  })
})
