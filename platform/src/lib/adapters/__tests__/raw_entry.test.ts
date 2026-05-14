import { describe, test, expect, vi, beforeEach } from 'vitest'

vi.mock('server-only', () => ({}))

// Use vi.hoisted to avoid TDZ — vi.mock factories are hoisted before const declarations
const { mockStreamText, mockStreamTextResult } = vi.hoisted(() => {
  const mockStreamTextResult = {
    fullStream: (async function* () {})(),
    toUIMessageStreamResponse: vi.fn(),
  }
  const mockStreamText = vi.fn(() => mockStreamTextResult)
  return { mockStreamText, mockStreamTextResult }
})

vi.mock('ai', () => ({
  streamText: mockStreamText,
  stepCountIs: vi.fn((n: number) => ({ __stepCountIs: n })),
  smoothStream: vi.fn(),
  jsonSchema: vi.fn((s: unknown) => ({ __jsonSchema: s })),
  extractReasoningMiddleware: vi.fn(() => ({})),
  wrapLanguageModel: vi.fn((m: unknown) => m),
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
      feed: vi.fn(() => ({ text: '', reasoning: '' })),
      flush: vi.fn(() => ({ text: '', reasoning: '', unclosed: false })),
    }
  }),
}))

const mockGetModelMeta = vi.fn()
vi.mock('@/lib/models/registry', () => ({
  getModelMeta: (...args: unknown[]) => mockGetModelMeta(...args),
  DEFAULT_STACK_ID: 'gemini',
  DEFAULT_MODEL_ID: 'gemini-2.5-pro',
  STACK_ROUTING: {
    gemini: { synthesis: { primary: 'gemini-2.5-pro', fallback: 'deepseek-v4-pro' } },
  },
}))

import { streamAdapterRaw } from '../raw'
import type { QueryRequest } from '../types'
import type { ModelMeta } from '@/lib/models/registry'

beforeEach(() => {
  mockStreamText.mockClear()
  mockGetModelMeta.mockReset()
})

function makeGeminiMeta(): ModelMeta {
  return {
    id: 'gemini-2.5-pro',
    label: 'Gemini 2.5 Pro',
    hint: '',
    provider: 'google',
    tier: 'premium',
    speedTier: 'balanced',
    maxOutputTokens: 65536,
    capabilities: ['tool-use'],
    role: 'synthesis',
    costPer1MInput: 1.25,
    costPer1MOutput: 5.00,
    reasoningMode: 'native',
    quirks: {
      reasoning_via: 'native',
      streaming_required: false,
      tool_use_format: 'gemini',
      structured_output_format: 'gemini_response_schema',
      cache_strategy: 'context_caching',
      system_prompt_shape: 'system_message',
    },
  }
}

function makeAnthropicMeta(): ModelMeta {
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

describe('streamAdapterRaw — result and meta shape', () => {
  test('returns { result, meta } with meta from getModelMeta', () => {
    const meta = makeGeminiMeta()
    mockGetModelMeta.mockReturnValue(meta)
    const { result, meta: returnedMeta } = streamAdapterRaw(makeReq({ modelOverride: { modelId: 'gemini-2.5-pro' } }))
    expect(result).toBeDefined()
    expect(returnedMeta).toBe(meta)
  })

  test('throws if getModelMeta returns null (unknown model)', () => {
    mockGetModelMeta.mockReturnValue(null)
    expect(() => streamAdapterRaw(makeReq({ modelOverride: { modelId: 'nonexistent-model' } }))).toThrow(
      'unknown model nonexistent-model',
    )
  })

  test('result is the streamText return value', () => {
    const meta = makeGeminiMeta()
    mockGetModelMeta.mockReturnValue(meta)
    const { result } = streamAdapterRaw(makeReq({ modelOverride: { modelId: 'gemini-2.5-pro' } }))
    expect(result).toBe(mockStreamTextResult)
  })

  test('calls streamText exactly once', () => {
    const meta = makeAnthropicMeta()
    mockGetModelMeta.mockReturnValue(meta)
    streamAdapterRaw(makeReq({ modelOverride: { modelId: 'claude-sonnet-4-6' } }))
    expect(mockStreamText).toHaveBeenCalledOnce()
  })

  test('resolves model via STACK_ROUTING when no modelOverride', () => {
    const meta = makeGeminiMeta()
    mockGetModelMeta.mockReturnValue(meta)
    streamAdapterRaw(makeReq())
    expect(mockGetModelMeta).toHaveBeenCalledWith('gemini-2.5-pro')
  })

  test('meta.id and provider are correct from getModelMeta', () => {
    const meta = makeAnthropicMeta()
    mockGetModelMeta.mockReturnValue(meta)
    const { meta: returnedMeta } = streamAdapterRaw(makeReq({ modelOverride: { modelId: 'claude-sonnet-4-6' } }))
    expect(returnedMeta.id).toBe('claude-sonnet-4-6')
    expect(returnedMeta.provider).toBe('anthropic')
  })
})
