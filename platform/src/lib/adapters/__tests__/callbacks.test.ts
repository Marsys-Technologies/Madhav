import { describe, test, expect, vi, beforeEach } from 'vitest'

vi.mock('server-only', () => ({}))

const mockStreamText = vi.fn()
const mockStepCountIs = vi.fn((n: number) => ({ __stepCountIs: n }))
const mockSmoothStream = vi.fn()
const mockJsonSchema = vi.fn((s: unknown) => ({ __jsonSchema: s }))

vi.mock('ai', () => ({
  streamText: (...args: unknown[]) => mockStreamText(...args),
  stepCountIs: (n: number) => mockStepCountIs(n),
  smoothStream: () => mockSmoothStream(),
  jsonSchema: (s: unknown) => mockJsonSchema(s),
}))
vi.mock('@ai-sdk/anthropic', () => ({ anthropic: vi.fn(() => ({ id: 'claude-model' })) }))
vi.mock('@ai-sdk/deepseek', () => ({ deepseek: vi.fn(() => ({ id: 'deepseek-model' })) }))
vi.mock('@ai-sdk/google', () => ({ google: vi.fn(() => ({ id: 'gemini-model' })) }))
vi.mock('@ai-sdk/openai', () => ({ openai: vi.fn(() => ({ id: 'gpt-model' })), createOpenAI: vi.fn(() => ({ chat: vi.fn(() => ({ id: 'nim-model' })) })) }))
vi.mock('@/lib/models/nvidia', () => ({
  isNimCompatibilityError: vi.fn(() => false),
  PlannerCompatibilityError: class PlannerCompatibilityError extends Error {},
}))
vi.mock('../buffer', () => ({
  MarkerBuffer: vi.fn().mockImplementation(() => ({
    feed: vi.fn(() => ({ text: '', reasoning: '' })),
    flush: vi.fn(() => ({ text: '', reasoning: '', unclosed: false })),
  })),
}))

import { adapterAnthropic } from '../providers/adapter_anthropic'
import { adapterGemini } from '../providers/adapter_gemini'
import { adapterOpenai } from '../providers/adapter_openai'
import type { QueryRequest } from '../types'
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

async function collectStream(stream: ReadableStream): Promise<unknown[]> {
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
    label: 'Test',
    hint: '',
    provider: 'anthropic',
    tier: 'mid',
    speedTier: 'balanced',
    maxOutputTokens: 64000,
    capabilities: [],
    role: 'synthesis',
    costPer1MInput: 3.00,
    costPer1MOutput: 15.00,
    reasoningMode: 'none',
    quirks: {
      reasoning_via: 'none',
      streaming_required: false,
      tool_use_format: 'anthropic',
      structured_output_format: 'json_schema',
      cache_strategy: 'none',
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

describe('onStepFinish — wired into prepareRequest options', () => {
  test('anthropic: onStepFinish is passed through to prepareRequest options', () => {
    const stepCb = vi.fn()
    const options = adapterAnthropic.prepareRequest(makeReq({ onStepFinish: stepCb }), makeMeta())
    expect(options.onStepFinish).toBeDefined()
  })

  test('anthropic: onStepFinish absent → options.onStepFinish is undefined', () => {
    const options = adapterAnthropic.prepareRequest(makeReq(), makeMeta())
    expect(options.onStepFinish).toBeUndefined()
  })

  test('openai: onStepFinish is passed through to prepareRequest options', () => {
    const meta = makeMeta({ provider: 'openai', id: 'gpt-4o' })
    meta.quirks.tool_use_format = 'openai'
    const stepCb = vi.fn()
    const options = adapterOpenai.prepareRequest(makeReq({ onStepFinish: stepCb }), meta)
    expect(options.onStepFinish).toBeDefined()
  })

  test('gemini: onStepFinish is passed through to prepareRequest options', () => {
    const meta = makeMeta({ provider: 'google', id: 'gemini-2.5-pro' })
    const stepCb = vi.fn()
    const options = adapterGemini.prepareRequest(makeReq({ onStepFinish: stepCb }), meta)
    expect(options.onStepFinish).toBeDefined()
  })
})

describe('onFinish — called after finish event emitted by stream()', () => {
  test('onFinish is called with the assembled ModelInteraction', async () => {
    mockStreamText.mockReturnValue(fakeResult([makeFinishPart()]))
    const finishCb = vi.fn()
    await collectStream(adapterAnthropic.stream(makeReq({ onFinish: finishCb }), makeMeta()))
    expect(finishCb).toHaveBeenCalledOnce()
    const arg = finishCb.mock.calls[0][0]
    expect(arg).toMatchObject({ modelId: 'claude-sonnet-4-6', provider: 'anthropic' })
  })

  test('onFinish is called once and finish event appears in stream', async () => {
    mockStreamText.mockReturnValue(fakeResult([makeFinishPart()]))
    const finishCb = vi.fn()
    const events = await collectStream(adapterAnthropic.stream(makeReq({ onFinish: finishCb }), makeMeta()))
    expect(finishCb).toHaveBeenCalledOnce()
    const hasFinishEvent = events.some((e: unknown) => (e as { type: string }).type === 'finish')
    expect(hasFinishEvent).toBe(true)
  })

  test('onFinish is not called when absent', async () => {
    mockStreamText.mockReturnValue(fakeResult([makeFinishPart()]))
    const events = await collectStream(adapterAnthropic.stream(makeReq(), makeMeta()))
    expect(events.some((e: unknown) => (e as { type: string }).type === 'finish')).toBe(true)
  })

  test('async onFinish is awaited before stream closes', async () => {
    mockStreamText.mockReturnValue(fakeResult([makeFinishPart()]))
    let resolved = false
    const finishCb = vi.fn(async () => {
      await new Promise(r => setTimeout(r, 0))
      resolved = true
    })
    await collectStream(adapterAnthropic.stream(makeReq({ onFinish: finishCb }), makeMeta()))
    expect(resolved).toBe(true)
  })
})

describe('gemini adapter — onFinish wiring', () => {
  test('gemini onFinish receives ModelInteraction with correct provider', async () => {
    mockStreamText.mockReturnValue(fakeResult([makeFinishPart()]))
    const finishCb = vi.fn()
    const meta = makeMeta({ provider: 'google', id: 'gemini-2.5-pro' })
    await collectStream(adapterGemini.stream(makeReq({ onFinish: finishCb }), meta))
    expect(finishCb).toHaveBeenCalledOnce()
    expect(finishCb.mock.calls[0][0].provider).toBe('google')
  })
})
