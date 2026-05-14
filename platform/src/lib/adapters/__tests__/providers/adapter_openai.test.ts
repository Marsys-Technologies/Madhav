import { describe, test, expect, vi, beforeEach } from 'vitest'

vi.mock('server-only', () => ({}))

const mockStreamText = vi.fn()
vi.mock('ai', () => ({ streamText: (...args: unknown[]) => mockStreamText(...args) }))
vi.mock('@ai-sdk/openai', () => ({ openai: vi.fn(() => ({ id: 'openai-model' })) }))

import { adapterOpenai } from '../../providers/adapter_openai'
import type { QueryRequest } from '../../types'
import type { ModelMeta } from '@/lib/models/registry'

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
    id: 'gpt-4.1',
    label: 'GPT-4.1',
    hint: '',
    provider: 'openai',
    tier: 'premium',
    speedTier: 'deep',
    maxOutputTokens: 16384,
    capabilities: ['tool-use'],
    role: 'synthesis',
    costPer1MInput: 2.00,
    costPer1MOutput: 8.00,
    reasoningMode: 'none',
    quirks: {
      reasoning_via: 'none',
      streaming_required: false,
      tool_use_format: 'openai',
      structured_output_format: 'json_schema',
      cache_strategy: 'automatic',
      system_prompt_shape: 'system_message',
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

describe('adapterOpenai — structured output', () => {
  test('json_schema response_format passed when responseSchema present', () => {
    mockStreamText.mockReturnValue(fakeResult([makeFinishPart()]))
    const schema = { type: 'object', properties: { answer: { type: 'string' } } }
    adapterOpenai.stream(makeReq({ responseSchema: schema as never }), makeMeta())
    const callArgs = mockStreamText.mock.calls[0][0]
    expect(callArgs.providerOptions?.openai?.response_format?.type).toBe('json_schema')
    expect(callArgs.providerOptions?.openai?.response_format?.json_schema?.name).toBe('response')
  })

  test('no response_format when no responseSchema', () => {
    mockStreamText.mockReturnValue(fakeResult([makeFinishPart()]))
    adapterOpenai.stream(makeReq(), makeMeta())
    const callArgs = mockStreamText.mock.calls[0][0]
    expect(callArgs.providerOptions).toBeUndefined()
  })

  test('no response_format when structured_output_format is not json_schema', () => {
    mockStreamText.mockReturnValue(fakeResult([makeFinishPart()]))
    const meta = makeMeta()
    meta.quirks.structured_output_format = 'json_object'
    const schema = { type: 'object' }
    adapterOpenai.stream(makeReq({ responseSchema: schema as never }), meta)
    const callArgs = mockStreamText.mock.calls[0][0]
    expect(callArgs.providerOptions).toBeUndefined()
  })
})

describe('adapterOpenai — no reasoning emission', () => {
  test('no reasoning_delta events emitted', async () => {
    mockStreamText.mockReturnValue(fakeResult([
      { type: 'text-delta', text: 'hello' },
      makeFinishPart(),
    ]))
    const events = await collectEvents(adapterOpenai.stream(makeReq(), makeMeta()))
    expect((events as Array<{ type: string }>).filter(e => e.type === 'reasoning_delta')).toHaveLength(0)
  })
})

describe('adapterOpenai — text and event sequence', () => {
  test('text_delta events emitted for text chunks', async () => {
    mockStreamText.mockReturnValue(fakeResult([
      { type: 'text-delta', text: 'A' },
      { type: 'text-delta', text: 'B' },
      makeFinishPart(),
    ]))
    const events = await collectEvents(adapterOpenai.stream(makeReq(), makeMeta()))
    const texts = (events as Array<{ type: string; text?: string }>).filter(e => e.type === 'text_delta')
    expect(texts).toHaveLength(2)
  })

  test('queued + complete + finish are always emitted', async () => {
    mockStreamText.mockReturnValue(fakeResult([makeFinishPart()]))
    const events = await collectEvents(adapterOpenai.stream(makeReq(), makeMeta()))
    const types = (events as Array<{ type: string; status?: string }>)
    expect(types.some(e => e.type === 'status' && e.status === 'queued')).toBe(true)
    expect(types.some(e => e.type === 'status' && e.status === 'complete')).toBe(true)
    expect(types.some(e => e.type === 'finish')).toBe(true)
  })
})

describe('adapterOpenai — error handling', () => {
  test('error part in stream emits error event', async () => {
    mockStreamText.mockReturnValue(fakeResult([
      { type: 'error', error: new Error('context-length') },
    ]))
    const events = await collectEvents(adapterOpenai.stream(makeReq(), makeMeta()))
    const err = (events as Array<{ type: string; error?: { message: string } }>)
      .find(e => e.type === 'error')
    expect(err?.error?.message).toContain('context-length')
  })

  test('thrown exception emits error event', async () => {
    mockStreamText.mockImplementation(() => { throw new Error('bad request') })
    const events = await collectEvents(adapterOpenai.stream(makeReq(), makeMeta()))
    expect((events as Array<{ type: string }>).some(e => e.type === 'error')).toBe(true)
  })

  test('finish interaction has correct provider', async () => {
    mockStreamText.mockReturnValue(fakeResult([makeFinishPart()]))
    const events = await collectEvents(adapterOpenai.stream(makeReq(), makeMeta()))
    const finish = (events as Array<{ type: string; interaction?: { provider: string } }>)
      .find(e => e.type === 'finish')
    expect(finish?.interaction?.provider).toBe('openai')
  })
})
