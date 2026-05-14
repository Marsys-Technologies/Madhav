import { describe, test, expect, vi, beforeEach } from 'vitest'

vi.mock('server-only', () => ({}))

const mockStreamText = vi.fn()
const mockStepCountIs = vi.fn((n: number) => ({ __stepCountIs: n }))
const mockSmoothStreamResult = { __smoothStream: true }
const mockSmoothStream = vi.fn(() => mockSmoothStreamResult)
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
import { adapterOpenai } from '../providers/adapter_openai'
import { adapterNim } from '../providers/adapter_nim'
import type { QueryRequest } from '../types'
import type { ModelMeta } from '@/lib/models/registry'

beforeEach(() => {
  mockStreamText.mockReset()
  mockSmoothStream.mockClear()
})

function makeMeta(overrides: Partial<ModelMeta> = {}): ModelMeta {
  return {
    id: 'test-model',
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

describe('smoothStream — prepareRequest options', () => {
  test('anthropic: smoothStream=true → experimental_transform is set', () => {
    const options = adapterAnthropic.prepareRequest(makeReq({ smoothStream: true }), makeMeta())
    expect(options.experimental_transform).toBeDefined()
    expect(mockSmoothStream).toHaveBeenCalledOnce()
  })

  test('anthropic: smoothStream=false → experimental_transform is undefined', () => {
    const options = adapterAnthropic.prepareRequest(makeReq({ smoothStream: false }), makeMeta())
    expect(options.experimental_transform).toBeUndefined()
    expect(mockSmoothStream).not.toHaveBeenCalled()
  })

  test('anthropic: no smoothStream field → experimental_transform is undefined', () => {
    const options = adapterAnthropic.prepareRequest(makeReq(), makeMeta())
    expect(options.experimental_transform).toBeUndefined()
  })

  test('deepseek: smoothStream=true → experimental_transform is set', () => {
    const meta = makeMeta({ provider: 'deepseek', id: 'deepseek-v4' })
    const options = adapterDeepseek.prepareRequest(makeReq({ smoothStream: true }), meta)
    expect(options.experimental_transform).toBeDefined()
    expect(mockSmoothStream).toHaveBeenCalledOnce()
  })

  test('openai: smoothStream=true → experimental_transform is set', () => {
    const meta = makeMeta({ provider: 'openai', id: 'gpt-4o' })
    meta.quirks.tool_use_format = 'openai'
    const options = adapterOpenai.prepareRequest(makeReq({ smoothStream: true }), meta)
    expect(options.experimental_transform).toBeDefined()
  })

  test('nim: smoothStream=true → experimental_transform is set', () => {
    const meta = makeMeta({ provider: 'nvidia', id: 'nvidia/llama-3.1' })
    meta.quirks.tool_use_format = 'openai'
    const options = adapterNim.prepareRequest(makeReq({ smoothStream: true }), meta)
    expect(options.experimental_transform).toBeDefined()
  })
})
