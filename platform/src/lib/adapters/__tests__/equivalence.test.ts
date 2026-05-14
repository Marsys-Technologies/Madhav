/**
 * Regression guard: verify that for a request with NONE of the new AD.3.5
 * fields set (multiStep / toolChoice / smoothStream / onStepFinish / onFinish),
 * the stream() output from each adapter is identical to what AD.3 produced.
 */
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
vi.mock('@ai-sdk/openai', () => ({
  openai: vi.fn(() => ({ id: 'gpt-model' })),
  createOpenAI: vi.fn(() => ({ chat: vi.fn(() => ({ id: 'nim-model' })) })),
}))
vi.mock('@/lib/models/nvidia', () => ({
  isNimCompatibilityError: vi.fn(() => false),
  PlannerCompatibilityError: class PlannerCompatibilityError extends Error {},
}))
vi.mock('../buffer', () => ({
  MarkerBuffer: vi.fn(function (this: unknown) {
    return {
      feed: vi.fn((text: string) => ({ text, reasoning: '' })),
      flush: vi.fn(() => ({ text: '', reasoning: '', unclosed: false })),
    }
  }),
}))

import { adapterAnthropic } from '../providers/adapter_anthropic'
import { adapterDeepseek } from '../providers/adapter_deepseek'
import { adapterGemini } from '../providers/adapter_gemini'
import { adapterOpenai } from '../providers/adapter_openai'
import { adapterNim } from '../providers/adapter_nim'
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
    totalUsage: { inputTokens: 100, outputTokens: 200 },
    ...overrides,
  }
}

async function collectEvents(stream: ReadableStream): Promise<unknown[]> {
  const reader = stream.getReader()
  const events: unknown[] = []
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    events.push(value)
  }
  return events
}

function makeAnthropicMeta(overrides: Partial<ModelMeta> = {}): ModelMeta {
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

const BASELINE_PARTS = [
  { type: 'text-delta', text: 'Hello ' },
  { type: 'text-delta', text: 'world' },
  makeFinishPart(),
]

beforeEach(() => {
  mockStreamText.mockReset()
  mockStepCountIs.mockClear()
  mockSmoothStream.mockClear()
})

describe('equivalence — AD.3-shaped requests produce the same event sequence (regression guard)', () => {
  test('anthropic: produces queued → composing → text_delta × 2 → complete → finish', async () => {
    mockStreamText.mockReturnValue(fakeResult(BASELINE_PARTS))
    const events = await collectEvents(adapterAnthropic.stream(makeReq(), makeAnthropicMeta()))
    const types = (events as Array<{ type: string; status?: string }>).map(e =>
      e.type === 'status' ? `${e.type}:${e.status}` : e.type,
    )
    expect(types).toEqual([
      'status:queued',
      'status:composing',
      'text_delta',
      'text_delta',
      'status:complete',
      'finish',
    ])
  })

  test('anthropic: no stopWhen when multiStep not set', () => {
    mockStreamText.mockReturnValue(fakeResult([makeFinishPart()]))
    adapterAnthropic.stream(makeReq(), makeAnthropicMeta())
    const callArgs = mockStreamText.mock.calls[0][0]
    expect(callArgs.stopWhen).toBeUndefined()
    expect(mockStepCountIs).not.toHaveBeenCalled()
  })

  test('anthropic: no experimental_transform when smoothStream not set', () => {
    mockStreamText.mockReturnValue(fakeResult([makeFinishPart()]))
    adapterAnthropic.stream(makeReq(), makeAnthropicMeta())
    const callArgs = mockStreamText.mock.calls[0][0]
    expect(callArgs.experimental_transform).toBeUndefined()
    expect(mockSmoothStream).not.toHaveBeenCalled()
  })

  test('deepseek: no stopWhen when multiStep not set', async () => {
    mockStreamText.mockReturnValue(fakeResult([makeFinishPart()]))
    const meta = makeAnthropicMeta({ provider: 'deepseek', id: 'deepseek-v4' })
    await collectEvents(adapterDeepseek.stream(makeReq(), meta))
    const callArgs = mockStreamText.mock.calls[0][0]
    expect(callArgs.stopWhen).toBeUndefined()
  })

  test('gemini: no stopWhen when multiStep not set', () => {
    mockStreamText.mockReturnValue(fakeResult([makeFinishPart()]))
    const meta = makeAnthropicMeta({ provider: 'google', id: 'gemini-2.5-pro' })
    adapterGemini.stream(makeReq(), meta)
    const callArgs = mockStreamText.mock.calls[0][0]
    expect(callArgs.stopWhen).toBeUndefined()
  })

  test('openai: no stopWhen when multiStep not set', () => {
    mockStreamText.mockReturnValue(fakeResult([makeFinishPart()]))
    const meta = makeAnthropicMeta({ provider: 'openai', id: 'gpt-4o' })
    meta.quirks.tool_use_format = 'openai'
    adapterOpenai.stream(makeReq(), meta)
    const callArgs = mockStreamText.mock.calls[0][0]
    expect(callArgs.stopWhen).toBeUndefined()
  })

  test('nim: no stopWhen when multiStep not set', () => {
    mockStreamText.mockReturnValue(fakeResult([makeFinishPart()]))
    const meta = makeAnthropicMeta({ provider: 'nvidia', id: 'nvidia/llama-3.1' })
    adapterNim.stream(makeReq(), meta)
    const callArgs = mockStreamText.mock.calls[0][0]
    expect(callArgs.stopWhen).toBeUndefined()
  })

  test('anthropic: finish event still includes correct usage', async () => {
    mockStreamText.mockReturnValue(fakeResult([makeFinishPart({ totalUsage: { inputTokens: 50, outputTokens: 75 } })]))
    const events = await collectEvents(adapterAnthropic.stream(makeReq(), makeAnthropicMeta()))
    const finish = (events as Array<{ type: string; interaction?: { usage: { inputTokens: number; outputTokens: number } } }>)
      .find(e => e.type === 'finish')
    expect(finish?.interaction?.usage.inputTokens).toBe(50)
    expect(finish?.interaction?.usage.outputTokens).toBe(75)
  })

  test('anthropic: no toolChoice in options when not specified', () => {
    mockStreamText.mockReturnValue(fakeResult([makeFinishPart()]))
    adapterAnthropic.stream(makeReq(), makeAnthropicMeta())
    const callArgs = mockStreamText.mock.calls[0][0]
    expect(callArgs.toolChoice).toBeUndefined()
  })

  test('gemini: finish event has correct provider', async () => {
    mockStreamText.mockReturnValue(fakeResult([makeFinishPart()]))
    const meta = makeAnthropicMeta({ provider: 'google', id: 'gemini-2.5-pro' })
    const events = await collectEvents(adapterGemini.stream(makeReq(), meta))
    const finish = (events as Array<{ type: string; interaction?: { provider: string } }>).find(e => e.type === 'finish')
    expect(finish?.interaction?.provider).toBe('google')
  })

  test('openai: finish event has correct provider', async () => {
    mockStreamText.mockReturnValue(fakeResult([makeFinishPart()]))
    const meta = makeAnthropicMeta({ provider: 'openai', id: 'gpt-4o' })
    const events = await collectEvents(adapterOpenai.stream(makeReq(), meta))
    const finish = (events as Array<{ type: string; interaction?: { provider: string } }>).find(e => e.type === 'finish')
    expect(finish?.interaction?.provider).toBe('openai')
  })
})
