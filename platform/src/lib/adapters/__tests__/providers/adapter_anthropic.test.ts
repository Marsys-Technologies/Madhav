import { describe, test, expect, vi, beforeEach } from 'vitest'

vi.mock('server-only', () => ({}))

const mockStreamText = vi.fn()
vi.mock('ai', () => ({ streamText: (...args: unknown[]) => mockStreamText(...args) }))
vi.mock('@ai-sdk/anthropic', () => ({ anthropic: vi.fn(() => ({ id: 'claude-model' })) }))

import { adapterAnthropic } from '../../providers/adapter_anthropic'
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
    id: 'claude-sonnet-4-6',
    label: 'Sonnet 4.6',
    hint: '',
    provider: 'anthropic',
    tier: 'mid',
    speedTier: 'balanced',
    maxOutputTokens: 64000,
    capabilities: ['tool-use', 'prompt-caching'],
    role: 'synthesis',
    costPer1MInput: 3.00,
    costPer1MOutput: 15.00,
    reasoningMode: 'none',
    quirks: {
      reasoning_via: 'none',
      streaming_required: false,
      tool_use_format: 'anthropic',
      structured_output_format: 'json_schema',
      cache_strategy: 'explicit_headers',
      system_prompt_shape: 'system_block_array',
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

describe('adapterAnthropic — cache_control', () => {
  test('explicit_headers cache strategy passes cacheControl in providerOptions', () => {
    mockStreamText.mockReturnValue(fakeResult([makeFinishPart()]))
    adapterAnthropic.stream(makeReq(), makeMeta())
    const callArgs = mockStreamText.mock.calls[0][0]
    expect(callArgs.providerOptions?.anthropic?.cacheControl?.type).toBe('ephemeral')
  })

  test('no cacheControl when cache_strategy=none', () => {
    mockStreamText.mockReturnValue(fakeResult([makeFinishPart()]))
    const meta = makeMeta()
    meta.quirks.cache_strategy = 'none'
    adapterAnthropic.stream(makeReq(), meta)
    const callArgs = mockStreamText.mock.calls[0][0]
    expect(callArgs.providerOptions).toBeUndefined()
  })
})

describe('adapterAnthropic — no reasoning emission', () => {
  test('no reasoning_delta events emitted (reasoning_via=none)', async () => {
    mockStreamText.mockReturnValue(fakeResult([
      { type: 'text-delta', text: 'answer' },
      makeFinishPart(),
    ]))
    const events = await collectEvents(adapterAnthropic.stream(makeReq(), makeMeta()))
    const reasoning = (events as Array<{ type: string }>).filter(e => e.type === 'reasoning_delta')
    expect(reasoning).toHaveLength(0)
  })

  test('no reasoning status event emitted', async () => {
    mockStreamText.mockReturnValue(fakeResult([makeFinishPart()]))
    const events = await collectEvents(adapterAnthropic.stream(makeReq(), makeMeta()))
    const statuses = (events as Array<{ type: string; status?: string }>)
      .filter(e => e.type === 'status' && e.status === 'reasoning')
    expect(statuses).toHaveLength(0)
  })
})

describe('adapterAnthropic — text emission', () => {
  test('text-delta parts become text_delta events', async () => {
    mockStreamText.mockReturnValue(fakeResult([
      { type: 'text-delta', text: 'Hello ' },
      { type: 'text-delta', text: 'world' },
      makeFinishPart(),
    ]))
    const events = await collectEvents(adapterAnthropic.stream(makeReq(), makeMeta()))
    const text = (events as Array<{ type: string; text?: string }>).filter(e => e.type === 'text_delta')
    expect(text).toHaveLength(2)
    expect(text[0].text).toBe('Hello ')
  })

  test('composing status emitted before first text_delta', async () => {
    mockStreamText.mockReturnValue(fakeResult([
      { type: 'text-delta', text: 'a' },
      makeFinishPart(),
    ]))
    const events = await collectEvents(adapterAnthropic.stream(makeReq(), makeMeta()))
    const types = (events as Array<{ type: string; status?: string; text?: string }>)
    const composingIdx = types.findIndex(e => e.type === 'status' && e.status === 'composing')
    const textIdx = types.findIndex(e => e.type === 'text_delta')
    expect(composingIdx).toBeLessThan(textIdx)
  })
})

describe('adapterAnthropic — error handling', () => {
  test('error part emits error event', async () => {
    mockStreamText.mockReturnValue(fakeResult([
      { type: 'error', error: new Error('overload') },
    ]))
    const events = await collectEvents(adapterAnthropic.stream(makeReq(), makeMeta()))
    const err = (events as Array<{ type: string; error?: { message: string } }>)
      .find(e => e.type === 'error')
    expect(err?.error?.message).toContain('overload')
  })

  test('finish event has correct modelId and provider', async () => {
    mockStreamText.mockReturnValue(fakeResult([makeFinishPart()]))
    const events = await collectEvents(adapterAnthropic.stream(makeReq(), makeMeta()))
    const finish = (events as Array<{ type: string; interaction?: { modelId: string; provider: string } }>)
      .find(e => e.type === 'finish')
    expect(finish?.interaction?.modelId).toBe('claude-sonnet-4-6')
    expect(finish?.interaction?.provider).toBe('anthropic')
  })

  test('usage from finish part reflected in interaction.usage', async () => {
    mockStreamText.mockReturnValue(fakeResult([
      makeFinishPart({ totalUsage: { inputTokens: 100, outputTokens: 200 } }),
    ]))
    const events = await collectEvents(adapterAnthropic.stream(makeReq(), makeMeta()))
    const finish = (events as Array<{ type: string; interaction?: { usage: { inputTokens: number; outputTokens: number } } }>)
      .find(e => e.type === 'finish')
    expect(finish?.interaction?.usage.inputTokens).toBe(100)
    expect(finish?.interaction?.usage.outputTokens).toBe(200)
  })
})
