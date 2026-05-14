import { describe, test, expect, vi, beforeEach } from 'vitest'

vi.mock('server-only', () => ({}))

const mockStreamText = vi.fn()
vi.mock('ai', () => ({ streamText: (...args: unknown[]) => mockStreamText(...args) }))
vi.mock('@ai-sdk/deepseek', () => ({ deepseek: vi.fn(() => ({ id: 'deepseek-model' })) }))

import { adapterDeepseek } from '../../providers/adapter_deepseek'
import type { QueryRequest } from '../../types'
import type { ModelMeta } from '@/lib/models/registry'

// ─── helpers ────────────────────────────────────────────────────────────────

async function* makeStream(parts: unknown[]) {
  for (const p of parts) yield p
}

function fakeResult(parts: unknown[]) {
  return { fullStream: makeStream(parts) }
}

function makeFinishPart(overrides: Record<string, unknown> = {}) {
  return {
    type: 'finish',
    finishReason: 'stop',
    totalUsage: { inputTokens: 10, outputTokens: 20 },
    ...overrides,
  }
}

async function collectEvents(stream: ReadableStream) {
  const reader = stream.getReader()
  const events: unknown[] = []
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    events.push(value)
  }
  return events
}

function makeMeta(overrides: Partial<ModelMeta> = {}): ModelMeta {
  return {
    id: 'deepseek-v4-pro',
    label: 'DS V4 Pro',
    hint: '',
    provider: 'deepseek',
    tier: 'premium',
    speedTier: 'deep',
    maxOutputTokens: 32768,
    capabilities: [],
    role: 'synthesis',
    costPer1MInput: 1.74,
    costPer1MOutput: 3.48,
    reasoningMode: 'none',
    quirks: {
      reasoning_via: 'none',
      streaming_required: false,
      tool_use_format: 'openai',
      structured_output_format: 'json_object',
      cache_strategy: 'none',
      system_prompt_shape: 'system_message',
      request_transforms: { thinking_mode: 'toggle' },
    },
    ...overrides,
  }
}

function makeReq(overrides: Partial<QueryRequest> = {}): QueryRequest {
  return {
    callType: 'synthesis',
    systemPrompt: 'sys',
    messages: [{ role: 'user', content: 'hi' }],
    ...overrides,
  }
}

beforeEach(() => { mockStreamText.mockReset() })

// ─── tests ──────────────────────────────────────────────────────────────────

describe('adapterDeepseek — event sequence', () => {
  test('emits queued status first, complete + finish last', async () => {
    mockStreamText.mockReturnValue(fakeResult([makeFinishPart()]))
    const events = await collectEvents(adapterDeepseek.stream(makeReq(), makeMeta()))
    const types = (events as Array<{ type: string }>).map(e => e.type)
    expect(types[0]).toBe('status')
    expect((events[0] as { status: string }).status).toBe('queued')
    expect(types.at(-2)).toBe('status')
    expect((events.at(-2) as { status: string }).status).toBe('complete')
    expect(types.at(-1)).toBe('finish')
  })

  test('text_delta events emitted for plain text chunks', async () => {
    mockStreamText.mockReturnValue(fakeResult([
      { type: 'text-delta', text: 'hello ' },
      { type: 'text-delta', text: 'world' },
      makeFinishPart(),
    ]))
    const events = await collectEvents(adapterDeepseek.stream(makeReq(), makeMeta()))
    const deltas = (events as Array<{ type: string; text?: string }>).filter(e => e.type === 'text_delta')
    expect(deltas).toHaveLength(2)
    expect(deltas[0].text).toBe('hello ')
    expect(deltas[1].text).toBe('world')
  })

  test('composing status emitted before first text_delta', async () => {
    mockStreamText.mockReturnValue(fakeResult([
      { type: 'text-delta', text: 'hi' },
      makeFinishPart(),
    ]))
    const events = await collectEvents(adapterDeepseek.stream(makeReq(), makeMeta()))
    const statusEvents = (events as Array<{ type: string; status?: string }>)
      .filter(e => e.type === 'status')
    const composingIdx = statusEvents.findIndex(e => e.status === 'composing')
    expect(composingIdx).toBeGreaterThanOrEqual(0)
  })
})

describe('adapterDeepseek — thinking mode', () => {
  test('thinking enabled when reasoning=auto and thinking_mode=toggle', () => {
    mockStreamText.mockReturnValue(fakeResult([makeFinishPart()]))
    adapterDeepseek.stream(makeReq({ reasoning: 'auto' }), makeMeta())
    const callArgs = mockStreamText.mock.calls[0][0]
    expect(callArgs.providerOptions?.deepseek?.thinking?.type).toBe('enabled')
  })

  test('thinking NOT set when reasoning=disable', () => {
    mockStreamText.mockReturnValue(fakeResult([makeFinishPart()]))
    adapterDeepseek.stream(makeReq({ reasoning: 'disable' }), makeMeta())
    const callArgs = mockStreamText.mock.calls[0][0]
    expect(callArgs.providerOptions).toBeUndefined()
  })

  test('thinking NOT set when no thinking_mode in request_transforms', () => {
    mockStreamText.mockReturnValue(fakeResult([makeFinishPart()]))
    const meta = makeMeta()
    meta.quirks.request_transforms = {}
    adapterDeepseek.stream(makeReq({ reasoning: 'auto' }), meta)
    const callArgs = mockStreamText.mock.calls[0][0]
    expect(callArgs.providerOptions).toBeUndefined()
  })
})

describe('adapterDeepseek — reasoning_via: none suppresses reasoning_delta', () => {
  test('no reasoning_delta events when reasoning_via=none (even with <think> in stream)', async () => {
    mockStreamText.mockReturnValue(fakeResult([
      { type: 'text-delta', text: '<think>internal</think>answer' },
      makeFinishPart(),
    ]))
    const events = await collectEvents(adapterDeepseek.stream(makeReq(), makeMeta()))
    const reasoning = (events as Array<{ type: string }>).filter(e => e.type === 'reasoning_delta')
    expect(reasoning).toHaveLength(0)
    const text = (events as Array<{ type: string; text?: string }>).filter(e => e.type === 'text_delta')
    expect(text[0].text).toBe('answer')
  })
})

describe('adapterDeepseek — tool events', () => {
  test('tool_call parts become tool_call events', async () => {
    mockStreamText.mockReturnValue(fakeResult([
      { type: 'tool-call', toolName: 'search', toolCallId: 'c1', input: { q: 'x' } },
      makeFinishPart(),
    ]))
    const events = await collectEvents(adapterDeepseek.stream(makeReq(), makeMeta()))
    const toolCall = (events as Array<{ type: string; name?: string; callId?: string; args?: unknown }>)
      .find(e => e.type === 'tool_call')
    expect(toolCall?.name).toBe('search')
    expect(toolCall?.callId).toBe('c1')
    expect(toolCall?.args).toEqual({ q: 'x' })
  })
})

describe('adapterDeepseek — error handling', () => {
  test('error part in stream emits error event and closes', async () => {
    mockStreamText.mockReturnValue(fakeResult([
      { type: 'error', error: new Error('rate-limited') },
    ]))
    const events = await collectEvents(adapterDeepseek.stream(makeReq(), makeMeta()))
    const err = (events as Array<{ type: string; error?: { message: string } }>)
      .find(e => e.type === 'error')
    expect(err?.error?.message).toBe('rate-limited')
  })

  test('thrown exception during streamText emits error event', async () => {
    mockStreamText.mockImplementation(() => { throw new Error('network fail') })
    const events = await collectEvents(adapterDeepseek.stream(makeReq(), makeMeta()))
    const err = (events as Array<{ type: string; error?: { message: string } }>)
      .find(e => e.type === 'error')
    expect(err?.error?.message).toContain('network fail')
  })

  test('finish event contains modelId and provider', async () => {
    mockStreamText.mockReturnValue(fakeResult([makeFinishPart()]))
    const events = await collectEvents(adapterDeepseek.stream(makeReq(), makeMeta()))
    const finish = (events as Array<{ type: string; interaction?: { modelId: string; provider: string } }>)
      .find(e => e.type === 'finish')
    expect(finish?.interaction?.modelId).toBe('deepseek-v4-pro')
    expect(finish?.interaction?.provider).toBe('deepseek')
  })
})
