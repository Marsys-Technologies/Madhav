import { act, renderHook, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { useLiveStream } from '../useLiveStream'

const CONVERSATION_ID = '11111111-1111-4111-8111-111111111111'
const OTHER_CONVERSATION_ID = '22222222-2222-4222-8222-222222222222'
const selection = { kind: 'explicit', choice: {
  kind: 'provider_model', connectionId: '33333333-3333-4333-8333-333333333333', modelId: 'gpt-safe',
} } as const

function sse(conversationId: string, turnId: string) {
  const event = { type: 'turn.open', seq: 0, t: Date.now(), turn_id: turnId, conversation_id: conversationId,
    chart_id: 'chart-1', model_id: 'safe-display', reading_depth: 'auto', length_tier: 'standard' }
  return new Response(`data: ${JSON.stringify(event)}\n\n`, { status: 200, headers: { 'content-type': 'text/event-stream' } })
}

afterEach(() => { vi.unstubAllEnvs(); vi.unstubAllGlobals(); vi.restoreAllMocks() })

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
