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

beforeEach(() => { mockStreamText.mockReset() })

function makeMeta(overrides: Partial<ModelMeta> = {}): ModelMeta {
  return {
    id: 'test-model',
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

describe('toolChoice — anthropic adapter', () => {
  test('toolChoice=required passed through to options', () => {
    const options = adapterAnthropic.prepareRequest(makeReq({ toolChoice: 'required' }), makeMeta())
    expect(options.toolChoice).toBe('required')
  })

  test('toolChoice=auto passed through', () => {
    const options = adapterAnthropic.prepareRequest(makeReq({ toolChoice: 'auto' }), makeMeta())
    expect(options.toolChoice).toBe('auto')
  })

  test('toolChoice=none passed through', () => {
    const options = adapterAnthropic.prepareRequest(makeReq({ toolChoice: 'none' }), makeMeta())
    expect(options.toolChoice).toBe('none')
  })

  test('toolChoice named tool passed through', () => {
    const tc = { type: 'tool' as const, toolName: 'search' }
    const options = adapterAnthropic.prepareRequest(makeReq({ toolChoice: tc }), makeMeta())
    expect(options.toolChoice).toEqual(tc)
  })

  test('toolChoice throws when tool_use_format=none', () => {
    const meta = makeMeta()
    meta.quirks.tool_use_format = 'none'
    expect(() => adapterAnthropic.prepareRequest(makeReq({ toolChoice: 'required' }), meta)).toThrow()
  })

  test('no toolChoice → toolChoice is undefined', () => {
    const options = adapterAnthropic.prepareRequest(makeReq(), makeMeta())
    expect(options.toolChoice).toBeUndefined()
  })
})

describe('toolChoice — openai adapter', () => {
  test('toolChoice=required passed through to options', () => {
    const meta = makeMeta({ provider: 'openai', id: 'gpt-4o' })
    meta.quirks.tool_use_format = 'openai'
    const options = adapterOpenai.prepareRequest(makeReq({ toolChoice: 'required' }), meta)
    expect(options.toolChoice).toBe('required')
  })

  test('toolChoice throws when tool_use_format=none', () => {
    const meta = makeMeta({ provider: 'openai', id: 'gpt-4o' })
    meta.quirks.tool_use_format = 'none'
    expect(() => adapterOpenai.prepareRequest(makeReq({ toolChoice: 'required' }), meta)).toThrow()
  })
})

describe('toolChoice — gemini adapter', () => {
  test('toolChoice=auto passed through', () => {
    const meta = makeMeta({ provider: 'google', id: 'gemini-2.5-pro' })
    meta.quirks.tool_use_format = 'gemini'
    const options = adapterGemini.prepareRequest(makeReq({ toolChoice: 'auto' }), meta)
    expect(options.toolChoice).toBe('auto')
  })

  test('toolChoice throws for gemini when tool_use_format=none', () => {
    const meta = makeMeta({ provider: 'google', id: 'gemini-nano' })
    meta.quirks.tool_use_format = 'none'
    expect(() => adapterGemini.prepareRequest(makeReq({ toolChoice: 'required' }), meta)).toThrow()
  })
})

describe('toolChoice — nim adapter', () => {
  test('toolChoice=required passed through for NIM openai format', () => {
    const meta = makeMeta({ provider: 'nvidia', id: 'nvidia/llama-3.1-8b' })
    meta.quirks.tool_use_format = 'openai'
    const options = adapterNim.prepareRequest(makeReq({ toolChoice: 'required' }), meta)
    expect(options.toolChoice).toBe('required')
  })

  test('toolChoice throws for NIM model with tool_use_format=none', () => {
    const meta = makeMeta({ provider: 'nvidia', id: 'nvidia/embedding-model' })
    meta.quirks.tool_use_format = 'none'
    expect(() => adapterNim.prepareRequest(makeReq({ toolChoice: 'required' }), meta)).toThrow()
  })
})

describe('toolChoice — deepseek adapter', () => {
  test('toolChoice=required passed through for deepseek openai format', () => {
    const meta = makeMeta({ provider: 'deepseek', id: 'deepseek-v4' })
    meta.quirks.tool_use_format = 'openai'
    const options = adapterDeepseek.prepareRequest(makeReq({ toolChoice: 'required' }), meta)
    expect(options.toolChoice).toBe('required')
  })
})
