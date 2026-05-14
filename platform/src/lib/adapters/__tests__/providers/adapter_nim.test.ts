import { describe, test, expect, vi, beforeEach } from 'vitest'

vi.mock('server-only', () => ({}))

const mockStreamText = vi.fn()
vi.mock('ai', () => ({ streamText: (...args: unknown[]) => mockStreamText(...args) }))

const mockChat = vi.fn(() => ({ id: 'nim-model' }))
vi.mock('@ai-sdk/openai', () => ({
  createOpenAI: vi.fn(() => ({ chat: mockChat })),
}))

vi.mock('@/lib/models/nvidia', () => ({
  isNimCompatibilityError: vi.fn((err: unknown) =>
    err instanceof Error && /does not support tool.?choice/i.test(err.message)
  ),
  PlannerCompatibilityError: class PlannerCompatibilityError extends Error {
    readonly isCompatibilityError = true
    constructor(message: string, cause?: unknown) {
      super(message)
      this.name = 'PlannerCompatibilityError'
      if (cause) this.cause = cause
    }
  },
}))

import { adapterNim } from '../../providers/adapter_nim'
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
    id: 'nvidia/llama-3.1-nemotron-ultra-253b-v1',
    label: 'Nemotron Ultra',
    hint: '',
    provider: 'nvidia',
    tier: 'premium',
    speedTier: 'deep',
    maxOutputTokens: 32768,
    capabilities: ['tool-use'],
    role: 'planner',
    costPer1MInput: 0.99,
    costPer1MOutput: 3.96,
    reasoningMode: 'none',
    quirks: {
      reasoning_via: 'none',
      streaming_required: true,
      tool_use_format: 'openai',
      structured_output_format: 'json_schema',
      cache_strategy: 'none',
      system_prompt_shape: 'system_message',
    },
    ...overrides,
  }
}

function makeReq(overrides: Partial<QueryRequest> = {}): QueryRequest {
  return {
    callType: 'planner_fast',
    systemPrompt: 'sys',
    messages: [{ role: 'user', content: 'plan' }],
    ...overrides,
  }
}

beforeEach(() => { mockStreamText.mockReset() })

describe('adapterNim — basic event sequence', () => {
  test('queued status emitted first', async () => {
    mockStreamText.mockReturnValue(fakeResult([makeFinishPart()]))
    const events = await collectEvents(adapterNim.stream(makeReq(), makeMeta()))
    expect((events[0] as { type: string; status: string }).status).toBe('queued')
  })

  test('text_delta emitted for text chunks (no-reasoning model)', async () => {
    mockStreamText.mockReturnValue(fakeResult([
      { type: 'text-delta', text: 'plan output' },
      makeFinishPart(),
    ]))
    const events = await collectEvents(adapterNim.stream(makeReq(), makeMeta()))
    const text = (events as Array<{ type: string; text?: string }>).filter(e => e.type === 'text_delta')
    expect(text[0].text).toBe('plan output')
  })

  test('no reasoning_delta for reasoning_via=none', async () => {
    mockStreamText.mockReturnValue(fakeResult([
      { type: 'text-delta', text: 'output' },
      makeFinishPart(),
    ]))
    const events = await collectEvents(adapterNim.stream(makeReq(), makeMeta()))
    expect((events as Array<{ type: string }>).filter(e => e.type === 'reasoning_delta')).toHaveLength(0)
  })
})

describe('adapterNim — marker-based reasoning (DeepSeek-on-NIM)', () => {
  test('reasoning_delta emitted when reasoning_via=markers and <think> in text', async () => {
    mockStreamText.mockReturnValue(fakeResult([
      { type: 'text-delta', text: '<think>chain of thought</think>answer' },
      makeFinishPart(),
    ]))
    const meta = makeMeta({ quirks: { ...makeMeta().quirks, reasoning_via: 'markers' } })
    const events = await collectEvents(adapterNim.stream(makeReq(), meta))
    const reasoning = (events as Array<{ type: string; text?: string }>)
      .filter(e => e.type === 'reasoning_delta')
    expect(reasoning.length).toBeGreaterThan(0)
    expect(reasoning.map(e => e.text).join('')).toBe('chain of thought')
  })
})

describe('adapterNim — error handling', () => {
  test('generic error emits error event', async () => {
    mockStreamText.mockImplementation(() => { throw new Error('NIM queue full') })
    const events = await collectEvents(adapterNim.stream(makeReq(), makeMeta()))
    const err = (events as Array<{ type: string; error?: { message: string } }>)
      .find(e => e.type === 'error')
    expect(err?.error?.message).toContain('NIM queue full')
  })

  test('NIM toolChoice compatibility error emits error event with code', async () => {
    mockStreamText.mockImplementation(() => {
      throw new Error('does not support tool_choice for this model')
    })
    const events = await collectEvents(adapterNim.stream(makeReq(), makeMeta()))
    const err = (events as Array<{ type: string; error?: { message: string; code?: string } }>)
      .find(e => e.type === 'error')
    expect(err).toBeDefined()
    expect(err?.error?.code).toBe('NIM_COMPAT_ERROR')
  })

  test('error part in fullStream emits error event', async () => {
    mockStreamText.mockReturnValue(fakeResult([
      { type: 'error', error: new Error('stream error') },
    ]))
    const events = await collectEvents(adapterNim.stream(makeReq(), makeMeta()))
    const err = (events as Array<{ type: string; error?: { message: string } }>)
      .find(e => e.type === 'error')
    expect(err?.error?.message).toContain('stream error')
  })

  test('finish interaction has provider=nvidia', async () => {
    mockStreamText.mockReturnValue(fakeResult([makeFinishPart()]))
    const events = await collectEvents(adapterNim.stream(makeReq(), makeMeta()))
    const finish = (events as Array<{ type: string; interaction?: { provider: string } }>)
      .find(e => e.type === 'finish')
    expect(finish?.interaction?.provider).toBe('nvidia')
  })
})
