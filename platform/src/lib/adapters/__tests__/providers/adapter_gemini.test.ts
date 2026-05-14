import { describe, test, expect, vi, beforeEach } from 'vitest'

vi.mock('server-only', () => ({}))

const mockStreamText = vi.fn()
vi.mock('ai', () => ({ streamText: (...args: unknown[]) => mockStreamText(...args) }))
vi.mock('@ai-sdk/google', () => ({ google: vi.fn(() => ({ id: 'gemini-model' })) }))

import { adapterGemini } from '../../providers/adapter_gemini'
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
    id: 'gemini-2.5-pro',
    label: 'Gemini 2.5 Pro',
    hint: '',
    provider: 'google',
    tier: 'premium',
    speedTier: 'deep',
    maxOutputTokens: 65536,
    capabilities: ['tool-use'],
    role: 'synthesis',
    costPer1MInput: 1.25,
    costPer1MOutput: 10.00,
    reasoningMode: 'native',
    quirks: {
      reasoning_via: 'native',
      streaming_required: false,
      tool_use_format: 'gemini',
      structured_output_format: 'gemini_response_schema',
      cache_strategy: 'context_caching',
      system_prompt_shape: 'system_message',
      request_transforms: { safety_filter: 'block_none', thinking_budget: 32768 },
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

describe('adapterGemini — safety settings always included', () => {
  test('safetySettings with BLOCK_NONE passed in providerOptions', () => {
    mockStreamText.mockReturnValue(fakeResult([makeFinishPart()]))
    adapterGemini.stream(makeReq(), makeMeta())
    const callArgs = mockStreamText.mock.calls[0][0]
    const safety = callArgs.providerOptions?.google?.safetySettings
    expect(Array.isArray(safety)).toBe(true)
    expect(safety.length).toBe(5)
    expect(safety.every((s: { threshold: string }) => s.threshold === 'BLOCK_NONE')).toBe(true)
  })

  test('thinkingBudget from quirks passed to providerOptions', () => {
    mockStreamText.mockReturnValue(fakeResult([makeFinishPart()]))
    adapterGemini.stream(makeReq(), makeMeta())
    const callArgs = mockStreamText.mock.calls[0][0]
    expect(callArgs.providerOptions?.google?.thinkingConfig?.thinkingBudget).toBe(32768)
  })

  test('thinkingBudget set to 0 when reasoning=disable', () => {
    mockStreamText.mockReturnValue(fakeResult([makeFinishPart()]))
    adapterGemini.stream(makeReq({ reasoning: 'disable' }), makeMeta())
    const callArgs = mockStreamText.mock.calls[0][0]
    expect(callArgs.providerOptions?.google?.thinkingConfig?.thinkingBudget).toBe(0)
  })
})

describe('adapterGemini — native reasoning emission', () => {
  test('reasoning-delta parts become reasoning_delta events', async () => {
    mockStreamText.mockReturnValue(fakeResult([
      { type: 'reasoning-delta', text: 'Step 1' },
      { type: 'reasoning-delta', text: ' Step 2' },
      makeFinishPart(),
    ]))
    const events = await collectEvents(adapterGemini.stream(makeReq(), makeMeta()))
    const reasoning = (events as Array<{ type: string; text?: string }>)
      .filter(e => e.type === 'reasoning_delta')
    expect(reasoning).toHaveLength(2)
    expect(reasoning[0].text).toBe('Step 1')
  })

  test('reasoning status emitted before first reasoning_delta', async () => {
    mockStreamText.mockReturnValue(fakeResult([
      { type: 'reasoning-delta', text: 'thinking' },
      makeFinishPart(),
    ]))
    const events = await collectEvents(adapterGemini.stream(makeReq(), makeMeta()))
    const statuses = (events as Array<{ type: string; status?: string }>).filter(e => e.type === 'status')
    const reasoningStatus = statuses.find(e => e.status === 'reasoning')
    expect(reasoningStatus).toBeDefined()
  })

  test('no reasoning_delta when reasoning_via=none even if reasoning parts arrive', async () => {
    mockStreamText.mockReturnValue(fakeResult([
      { type: 'reasoning-delta', text: 'hidden' },
      makeFinishPart(),
    ]))
    const meta = makeMeta()
    meta.quirks.reasoning_via = 'none'
    const events = await collectEvents(adapterGemini.stream(makeReq(), meta))
    const reasoning = (events as Array<{ type: string }>).filter(e => e.type === 'reasoning_delta')
    expect(reasoning).toHaveLength(0)
  })
})

describe('adapterGemini — text emission', () => {
  test('text-delta parts become text_delta events', async () => {
    mockStreamText.mockReturnValue(fakeResult([
      { type: 'text-delta', text: 'answer' },
      makeFinishPart(),
    ]))
    const events = await collectEvents(adapterGemini.stream(makeReq(), makeMeta()))
    const text = (events as Array<{ type: string; text?: string }>).filter(e => e.type === 'text_delta')
    expect(text[0].text).toBe('answer')
  })
})

describe('adapterGemini — error handling', () => {
  test('error part in fullStream emits error event', async () => {
    mockStreamText.mockReturnValue(fakeResult([
      { type: 'error', error: new Error('safety block') },
    ]))
    const events = await collectEvents(adapterGemini.stream(makeReq(), makeMeta()))
    const err = (events as Array<{ type: string; error?: { message: string } }>)
      .find(e => e.type === 'error')
    expect(err?.error?.message).toContain('safety block')
  })

  test('thrown exception emits error event', async () => {
    mockStreamText.mockImplementation(() => { throw new Error('timeout') })
    const events = await collectEvents(adapterGemini.stream(makeReq(), makeMeta()))
    const err = (events as Array<{ type: string; error?: { message: string } }>)
      .find(e => e.type === 'error')
    expect(err?.error?.message).toContain('timeout')
  })

  test('finish event has correct modelId and provider', async () => {
    mockStreamText.mockReturnValue(fakeResult([makeFinishPart()]))
    const events = await collectEvents(adapterGemini.stream(makeReq(), makeMeta()))
    const finish = (events as Array<{ type: string; interaction?: { modelId: string; provider: string } }>)
      .find(e => e.type === 'finish')
    expect(finish?.interaction?.modelId).toBe('gemini-2.5-pro')
    expect(finish?.interaction?.provider).toBe('google')
  })
})
