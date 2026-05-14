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
function makeFinishPart() {
  return { type: 'finish', finishReason: 'stop', totalUsage: { inputTokens: 10, outputTokens: 20 } }
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
    capabilities: ['tool-use'],
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

beforeEach(() => {
  mockStreamText.mockReset()
  mockStepCountIs.mockClear()
  mockSmoothStream.mockClear()
})

describe('prepareRequest — multiStep.maxSteps passed to stopWhen', () => {
  test('anthropic: multiStep=3 yields stopWhen from stepCountIs(3)', () => {
    mockStreamText.mockReturnValue(fakeResult([makeFinishPart()]))
    adapterAnthropic.prepareRequest(makeReq({ multiStep: { maxSteps: 3 } }), makeMeta())
    expect(mockStepCountIs).toHaveBeenCalledWith(3)
  })

  test('deepseek: multiStep=5 yields stopWhen from stepCountIs(5)', () => {
    const meta = makeMeta({ provider: 'deepseek', id: 'deepseek-v4' })
    meta.quirks.tool_use_format = 'openai'
    adapterDeepseek.prepareRequest(makeReq({ multiStep: { maxSteps: 5 } }), meta)
    expect(mockStepCountIs).toHaveBeenCalledWith(5)
  })

  test('gemini: multiStep=2 yields stopWhen from stepCountIs(2)', () => {
    const meta = makeMeta({ provider: 'google', id: 'gemini-2.5-pro' })
    meta.quirks.tool_use_format = 'gemini'
    adapterGemini.prepareRequest(makeReq({ multiStep: { maxSteps: 2 } }), meta)
    expect(mockStepCountIs).toHaveBeenCalledWith(2)
  })

  test('openai: multiStep=10 yields stopWhen from stepCountIs(10)', () => {
    const meta = makeMeta({ provider: 'openai', id: 'gpt-4o' })
    meta.quirks.tool_use_format = 'openai'
    adapterOpenai.prepareRequest(makeReq({ multiStep: { maxSteps: 10 } }), meta)
    expect(mockStepCountIs).toHaveBeenCalledWith(10)
  })

  test('nim: multiStep=1 yields stopWhen from stepCountIs(1)', () => {
    const meta = makeMeta({ provider: 'nvidia', id: 'nvidia/llama-3.1-8b' })
    meta.quirks.tool_use_format = 'openai'
    adapterNim.prepareRequest(makeReq({ multiStep: { maxSteps: 1 } }), meta)
    expect(mockStepCountIs).toHaveBeenCalledWith(1)
  })

  test('no multiStep → stopWhen is undefined', () => {
    const options = adapterAnthropic.prepareRequest(makeReq(), makeMeta())
    expect(options.stopWhen).toBeUndefined()
    expect(mockStepCountIs).not.toHaveBeenCalled()
  })
})

describe('prepareRequest — multiStep stopWhen is present in returned options', () => {
  test('anthropic: stopWhen is set in returned options when multiStep provided', () => {
    const options = adapterAnthropic.prepareRequest(makeReq({ multiStep: { maxSteps: 4 } }), makeMeta())
    expect(options.stopWhen).toBeDefined()
  })

  test('openai: stopWhen is absent when multiStep not provided', () => {
    const meta = makeMeta({ provider: 'openai', id: 'gpt-4o' })
    meta.quirks.tool_use_format = 'openai'
    const options = adapterOpenai.prepareRequest(makeReq(), meta)
    expect(options.stopWhen).toBeUndefined()
  })
})

describe('stream() — tool_call and tool_result events emitted in multi-step context', () => {
  test('tool-call part emits tool_call event', async () => {
    mockStreamText.mockReturnValue(fakeResult([
      { type: 'tool-call', toolName: 'search', input: { q: 'test' }, toolCallId: 'call_1' },
      makeFinishPart(),
    ]))
    const stream = adapterAnthropic.stream(
      makeReq({ multiStep: { maxSteps: 3 } }),
      makeMeta(),
    )
    const reader = stream.getReader()
    const events: unknown[] = []
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      events.push(value)
    }
    const toolCall = (events as Array<{ type: string; name?: string }>).find(e => e.type === 'tool_call')
    expect(toolCall).toBeDefined()
    expect((toolCall as { name: string }).name).toBe('search')
  })
})
