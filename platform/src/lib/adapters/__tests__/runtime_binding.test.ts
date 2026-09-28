import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { LanguageModelV3 } from '@ai-sdk/provider'

vi.mock('server-only', () => ({}))

const mocks = vi.hoisted(() => ({
  streamText: vi.fn(),
  getModelMeta: vi.fn(),
  openai: vi.fn(),
  anthropic: vi.fn(),
  google: vi.fn(),
  deepseek: vi.fn(),
}))

vi.mock('ai', () => ({
  streamText: mocks.streamText,
  stepCountIs: vi.fn(), smoothStream: vi.fn(), jsonSchema: vi.fn(value => value),
  Output: { object: vi.fn(value => value) },
}))
vi.mock('@ai-sdk/openai', () => ({ openai: mocks.openai, createOpenAI: vi.fn() }))
vi.mock('@ai-sdk/anthropic', () => ({ anthropic: mocks.anthropic }))
vi.mock('@ai-sdk/google', () => ({ google: mocks.google }))
vi.mock('@ai-sdk/deepseek', () => ({ deepseek: mocks.deepseek }))
vi.mock('@/lib/models/nvidia', () => ({
  isNimCompatibilityError: vi.fn(() => false),
  PlannerCompatibilityError: class PlannerCompatibilityError extends Error {},
}))
vi.mock('@/lib/models/registry', () => ({
  getModelMeta: mocks.getModelMeta,
  DEFAULT_STACK_ID: 'gemini', DEFAULT_MODEL_ID: 'shared-default',
  STACK_ROUTING: { gemini: { synthesis: { primary: 'shared-default' } } },
}))

import { streamAdapterRaw } from '../raw'
import type { QueryRequest, RuntimeAdapterBinding, SafeRuntimeModelDescriptor } from '../types'

const connectionId = '00000000-0000-4000-8000-000000000008'
const model = { specificationVersion: 'v3', provider: 'test', modelId: 'dynamic-model' } as LanguageModelV3

function descriptor(providerId: SafeRuntimeModelDescriptor['providerId'] = 'openai'): SafeRuntimeModelDescriptor {
  return Object.freeze({ providerId, connectionId, modelId: 'dynamic-model' })
}

function binding(providerId: SafeRuntimeModelDescriptor['providerId'] = 'openai'): RuntimeAdapterBinding {
  const value = Object.create(null)
  Object.defineProperties(value, {
    providerId: { value: providerId, enumerable: true },
    connectionId: { value: connectionId, enumerable: true },
    modelId: { value: 'dynamic-model', enumerable: true },
    model: { value: model, enumerable: false },
    toJSON: { value: () => { throw new Error('not serializable') } },
  })
  return Object.freeze(value) as RuntimeAdapterBinding
}

function request(providerId: SafeRuntimeModelDescriptor['providerId'] = 'openai'): QueryRequest {
  return {
    callType: 'synthesis', systemPrompt: 'system', messages: [{ role: 'user', content: 'hello' }],
    runtimeBinding: binding(providerId), runtimeDescriptor: descriptor(providerId),
  }
}

describe('streamAdapterRaw injected runtime binding', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mocks.streamText.mockReturnValue({ fullStream: (async function* () {})() })
    for (const key of ['OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'GOOGLE_GENERATIVE_AI_API_KEY', 'DEEPSEEK_API_KEY']) {
      vi.stubEnv(key, 'shared-key-must-not-be-used')
    }
  })

  it.each(['openai', 'anthropic', 'google', 'deepseek', 'xai', 'kimi', 'openrouter'] as const)(
    'uses the exact injected %s model without registry, SDK factory, stack, or environment lookup', providerId => {
      const result = streamAdapterRaw(request(providerId))

      expect(mocks.getModelMeta).not.toHaveBeenCalled()
      expect(mocks.openai).not.toHaveBeenCalled()
      expect(mocks.anthropic).not.toHaveBeenCalled()
      expect(mocks.google).not.toHaveBeenCalled()
      expect(mocks.deepseek).not.toHaveBeenCalled()
      expect(mocks.streamText).toHaveBeenCalledOnce()
      expect(mocks.streamText.mock.calls[0][0].model).toBe(model)
      expect(mocks.streamText.mock.calls[0][0].maxRetries).toBe(0)
      expect(result.descriptor).toEqual(descriptor(providerId))
      expect(result.descriptor!.providerId).toBe(providerId)
    },
  )

  it('accepts an authenticated dynamic model that is absent from the static registry', () => {
    mocks.getModelMeta.mockReturnValue(undefined)
    expect(() => streamAdapterRaw(request('openrouter'))).not.toThrow()
    expect(mocks.getModelMeta).not.toHaveBeenCalled()
  })

  it.each(['openai', 'anthropic', 'google', 'deepseek'] as const)(
    'passes JSON-schema output through the AI SDK for an injected %s model', providerId => {
      const req = request(providerId)
      req.responseSchema = { type: 'object', properties: { ok: { type: 'boolean' } }, required: ['ok'] }
      streamAdapterRaw(req)
      expect(mocks.streamText.mock.calls[0][0].output).toEqual({ schema: req.responseSchema })
    },
  )

  it('uses a conservative output limit unless the exact request supplies one', () => {
    streamAdapterRaw(request())
    expect(mocks.streamText.mock.calls[0][0].maxOutputTokens).toBe(4096)
    mocks.streamText.mockClear()
    const explicit = request(); explicit.maxOutputTokens = 1200
    streamAdapterRaw(explicit)
    expect(mocks.streamText.mock.calls[0][0].maxOutputTokens).toBe(1200)
  })

  it.each([
    ['providerId', { providerId: 'anthropic' }],
    ['modelId', { modelId: 'other-model' }],
    ['connectionId', { connectionId: '00000000-0000-4000-8000-000000000009' }],
  ] as const)('fails closed on a %s mismatch without an alternate lookup', (_field, change) => {
    const req = request()
    req.runtimeDescriptor = Object.freeze({ ...descriptor(), ...change }) as SafeRuntimeModelDescriptor
    expect(() => streamAdapterRaw(req)).toThrow()
    expect(mocks.getModelMeta).not.toHaveBeenCalled()
    expect(mocks.streamText).not.toHaveBeenCalled()
  })

  it('requires the binding and safe descriptor together', () => {
    const onlyBinding = request(); delete onlyBinding.runtimeDescriptor
    expect(() => streamAdapterRaw(onlyBinding)).toThrow()
    const onlyDescriptor = request(); delete onlyDescriptor.runtimeBinding
    expect(() => streamAdapterRaw(onlyDescriptor)).toThrow()
    expect(mocks.getModelMeta).not.toHaveBeenCalled()
  })
})
