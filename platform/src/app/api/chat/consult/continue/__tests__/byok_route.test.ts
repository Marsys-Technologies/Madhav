import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('server-only', () => ({}))
const mocks = vi.hoisted(() => ({
  prepare: vi.fn(), release: vi.fn(), stream: vi.fn(), cancelled: vi.fn(),
  byok: { on: true }, loadMessages: vi.fn(), streamText: vi.fn(), getEffectiveModel: vi.fn(),
  resolveModel: vi.fn(), realWire: { on: false },
}))
vi.mock('ai', async importOriginal => {
  const actual = await importOriginal<typeof import('ai')>()
  return {
    ...actual,
    createUIMessageStream: (args: Parameters<typeof actual.createUIMessageStream>[0]) => mocks.realWire.on
      ? actual.createUIMessageStream(args) : { execute: args.execute },
    createUIMessageStreamResponse: (args: Parameters<typeof actual.createUIMessageStreamResponse>[0]) =>
      mocks.realWire.on ? actual.createUIMessageStreamResponse(args) : { stream: args.stream },
    streamText: mocks.streamText,
  }
})
vi.mock('@/lib/firebase/server', () => ({ getServerUser: vi.fn(async () => ({ uid: 'alice' })) }))
vi.mock('@/lib/db/client', () => ({ query: vi.fn(async () => ({ rows: [{ role: 'guest', status: 'active' }] })) }))
vi.mock('@/lib/conversations', () => ({ getConversation: vi.fn(async () => ({ chart_id: crypto.randomUUID() })) }))
vi.mock('@/lib/charts/readingGate', () => ({ checkReadingReadiness: vi.fn(async () => ({ ok: true })) }))
vi.mock('@/lib/persistence/conversation_writer', () => ({ loadConversationMessagesV2: mocks.loadMessages }))
vi.mock('@/lib/errors', () => ({
  errorResponse: vi.fn((code: string, message: string, status: number, extra?: object) =>
    Response.json({ code, message, ...extra }, { status })),
  res: {
    unauthenticated: vi.fn(), badRequest: vi.fn(), dbError: vi.fn(), notFound: vi.fn(),
  },
}))
vi.mock('@/lib/config', () => ({ configService: { getFlag: () => mocks.byok.on } }))
vi.mock('@/lib/ai-console/repository', () => ({ getConversationSelection: vi.fn(async () => ({ kind: 'default' })) }))
vi.mock('@/lib/pariprashna/pipeline/byok_preflight', () => ({ prepareByokTurn: mocks.prepare }))
vi.mock('@/lib/models/runtime_config', () => ({ getEffectiveModel: mocks.getEffectiveModel }))
vi.mock('@/lib/models/resolver', () => ({ resolveModel: mocks.resolveModel }))

import { POST } from '../route'
import { AiConsoleError } from '@/lib/ai-console/errors'

describe('consult continuation BYOK lifecycle', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mocks.byok.on = true
    mocks.realWire.on = false
    mocks.loadMessages.mockResolvedValue([
      { id: 'user-1', role: 'user', parts: [{ type: 'text', text: 'Continue this reading' }] },
    ])
    mocks.stream.mockImplementation((request: unknown) => {
      expect(request).toMatchObject({ maxOutputTokens: 16_384 })
      return new ReadableStream({
        start(controller) { controller.enqueue({ type: 'text_delta', text: 'continued' }) },
        cancel: mocks.cancelled,
      })
    })
    mocks.prepare.mockResolvedValue({
      kind: 'byok', releaseAdmission: mocks.release,
      executors: { synthesizer: { stream: mocks.stream } },
    })
  })

  it.each([
    ['stale or broken selection', new AiConsoleError('AI_CHOICE_BROKEN'), 400, 'AI_CHOICE_BROKEN'],
    ['snapshot failure', new AiConsoleError('AI_EXECUTION_FAILED'), 400, 'AI_EXECUTION_FAILED'],
    ['admission refusal', new AiConsoleError('AI_RATE_LIMITED'), 429, 'AI_RATE_LIMITED'],
  ] as const)('returns a safe zero-call response for %s', async (_label, failure, status, code) => {
    mocks.prepare.mockRejectedValueOnce(failure)

    const response = await POST(new Request('http://local/api/chat/consult/continue', {
      method: 'POST', body: JSON.stringify({ conversation_id: crypto.randomUUID(), last_message_id: crypto.randomUUID() }),
    }))

    expect(response.status).toBe(status)
    expect(await response.json()).toMatchObject({ code })
    expect(mocks.stream).not.toHaveBeenCalled()
    expect(mocks.release).not.toHaveBeenCalled()
  })

  it('cancels an unfinished reader and releases once when the writer fails mid-stream', async () => {
    let resolveCleanup!: () => void
    const cleanup = new Promise<void>(resolve => { resolveCleanup = resolve })
    mocks.cancelled.mockReturnValueOnce(cleanup)
    const response = await POST(new Request('http://local/api/chat/consult/continue', {
      method: 'POST', body: JSON.stringify({ conversation_id: crypto.randomUUID(), last_message_id: crypto.randomUUID() }),
    })) as unknown as { stream: { execute(args: { writer: { write(event: unknown): void } }): Promise<void> } }
    let writes = 0
    const executing = response.stream.execute({ writer: { write: () => {
      writes++
      if (writes === 3) throw new Error('writer failed')
    } } })
    await vi.waitFor(() => expect(mocks.cancelled).toHaveBeenCalledOnce())
    expect(mocks.release).not.toHaveBeenCalled()
    resolveCleanup()
    await executing
    expect(mocks.cancelled).toHaveBeenCalledOnce()
    expect(mocks.release).toHaveBeenCalledOnce()
  })

  it('makes actual response-reader cancellation wait for deferred executor cleanup before release', async () => {
    mocks.realWire.on = true
    let resolveCleanup!: () => void
    const cleanup = new Promise<void>(resolve => { resolveCleanup = resolve })
    let invocationSignal: AbortSignal | undefined
    mocks.stream.mockImplementationOnce((input: { abortSignal?: AbortSignal }) => {
      invocationSignal = input.abortSignal
      return new ReadableStream({ cancel: () => cleanup })
    })

    const response = await POST(new Request('http://local/api/chat/consult/continue', {
      method: 'POST', body: JSON.stringify({ conversation_id: crypto.randomUUID(), last_message_id: crypto.randomUUID() }),
    }))
    const reader = response.body!.getReader()
    await reader.read()
    await vi.waitFor(() => expect(mocks.stream).toHaveBeenCalledOnce())
    let settled = false
    const cancelling = reader.cancel().then(() => { settled = true })
    await vi.waitFor(() => expect(invocationSignal?.aborted).toBe(true))
    expect(settled).toBe(false)
    expect(mocks.release).not.toHaveBeenCalled()
    resolveCleanup()
    await cancelling
    expect(mocks.release).toHaveBeenCalledOnce()
  })

  it('rejects oversized persisted assistant/tool history before selection, snapshot, or admission', async () => {
    mocks.loadMessages.mockResolvedValueOnce([
      { id: 'assistant-1', role: 'assistant', parts: [
        { type: 'reasoning', text: 'r'.repeat(1_100_000) },
        { type: 'dynamic-tool', toolName: 'fixture', toolCallId: 'call-1', state: 'output-available',
          input: { query: 'q'.repeat(500_000) }, output: { text: 'o'.repeat(500_000) } },
      ] },
    ])
    const response = await POST(new Request('http://local/api/chat/consult/continue', {
      method: 'POST', body: JSON.stringify({ conversation_id: crypto.randomUUID(), last_message_id: crypto.randomUUID() }),
    }))
    expect(response.status).toBe(400)
    expect(await response.json()).toMatchObject({ code: 'AI_EXECUTION_FAILED' })
    expect(mocks.prepare).not.toHaveBeenCalled()
    expect(mocks.stream).not.toHaveBeenCalled()
  })

  it('preserves the flag-off model request and UI stream merge contract', async () => {
    mocks.byok.on = false
    const model = { id: 'legacy-model' }
    const legacyWire = new ReadableStream()
    mocks.getEffectiveModel.mockResolvedValueOnce('legacy-model')
    mocks.resolveModel.mockReturnValueOnce(model)
    mocks.streamText.mockReturnValueOnce({ toUIMessageStream: () => legacyWire })
    const response = await POST(new Request('http://local/api/chat/consult/continue', {
      method: 'POST', body: JSON.stringify({ conversation_id: crypto.randomUUID(), last_message_id: crypto.randomUUID() }),
    })) as unknown as { stream: { execute(args: { writer: { merge(stream: unknown): void } }): Promise<void> } }
    const merge = vi.fn()
    await response.stream.execute({ writer: { merge } })

    expect(mocks.prepare).not.toHaveBeenCalled()
    expect(mocks.streamText).toHaveBeenCalledWith({
      model,
      system: 'Continue exactly from where the previous response was cut off. Do not repeat any content. Begin mid-sentence if needed.',
      messages: [{ role: 'user', content: 'Continue this reading' }],
      abortSignal: expect.any(AbortSignal),
    })
    expect(merge).toHaveBeenCalledWith(legacyWire)
  })
})
