import { afterEach, describe, expect, it, vi } from 'vitest'
import { inspect } from 'node:util'
import { getProviderAdapter } from '../index'
import { PROVIDER_IDS, type ProviderId } from '../../types'
import { normalizeAiError } from '../../errors'
import type { LanguageModelV3 } from '@ai-sdk/provider'

const key = 'synthetic-credential-only-for-tests'
const signal = () => new AbortController().signal
const ids: Record<ProviderId, string> = { openai: 'gpt-4.1-mini', anthropic: 'claude-haiku-4-5', google: 'gemini-2.5-flash', xai: 'grok-4', deepseek: 'deepseek-chat', kimi: 'kimi-k2.5', openrouter: 'example/text-model' }
function catalog(provider: ProviderId) {
  const id = ids[provider]
  if (provider === 'google') return { models: [{ name: `models/${id}`, displayName: 'Text model', supportedGenerationMethods: ['generateContent'], inputTokenLimit: 1000, outputTokenLimit: 200 }] }
  return { data: [{ id, display_name: 'Text model', name: 'Text model', context_length: 1000,
    architecture: { input_modalities: ['text'], output_modalities: ['text'] }, supported_parameters: ['tools', 'response_format', 'max_tokens'] }] }
}
function completion(provider: ProviderId) {
  if (provider === 'anthropic') return { type: 'message', content: [{ type: 'text', text: 'discard this probe text' }], usage: { input_tokens: 4, output_tokens: 1 } }
  if (provider === 'google') return { candidates: [{ content: { parts: [{ text: 'discard this probe text' }] } }], usageMetadata: { promptTokenCount: 4, candidatesTokenCount: 1 } }
  return { choices: [{ message: { content: 'discard this probe text' }, finish_reason: 'length' }], usage: { prompt_tokens: 4, completion_tokens: 1 } }
}
const hosts: Record<ProviderId, string> = { openai: 'api.openai.com', anthropic: 'api.anthropic.com', google: 'generativelanguage.googleapis.com', xai: 'api.x.ai', deepseek: 'api.deepseek.com', kimi: 'api.moonshot.ai', openrouter: 'openrouter.ai' }
afterEach(() => { vi.unstubAllGlobals(); vi.unstubAllEnvs(); vi.useRealTimers() })

describe.each(PROVIDER_IDS)('%s authenticated provider contract', provider => {
  it('redacts SDK parse errors from malformed successful runtime responses', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(Response.json({ error: key })))
    const binding = getProviderAdapter(provider).createRuntimeBinding(key, { modelId: ids[provider], displayName: 'Text', compatibleRoles: ['synthesizer'], supportsTools: true, supportsStructuredOutput: true })
    const error = await Promise.resolve((binding.model as LanguageModelV3).doGenerate({ prompt: [{ role: 'user', content: [{ type: 'text', text: 'Hi' }] }] })).catch(e => e)
    expect(error.code).toBe('AI_EXECUTION_FAILED')
    expect(inspect(error)).not.toContain(key)
    expect(JSON.stringify(error)).not.toContain(key)
    binding.dispose()
  })
  it('executes the native SDK model with only its owned key and the verified output-limit field', async () => {
    vi.stubEnv('OPENAI_API_KEY', 'never-use-shared')
    const response = provider === 'anthropic' ? { id: 'test-id', type: 'message', role: 'assistant', model: ids[provider], content: [{ type: 'text', text: 'OK' }], stop_reason: 'end_turn', stop_sequence: null, usage: { input_tokens: 4, output_tokens: 1 } }
      : provider === 'google' ? { candidates: [{ content: { role: 'model', parts: [{ text: 'OK' }] }, finishReason: 'STOP' }], usageMetadata: { promptTokenCount: 4, candidatesTokenCount: 1 } }
        : { id: 'test-id', created: 0, model: ids[provider], choices: [{ index: 0, message: { role: 'assistant', content: 'OK' }, finish_reason: 'stop' }], usage: { prompt_tokens: 4, completion_tokens: 1 } }
    const http = vi.fn().mockImplementation(async () => Response.json(response)); vi.stubGlobal('fetch', http)
    const binding = getProviderAdapter(provider).createRuntimeBinding(key, { modelId: ids[provider], displayName: 'Text', compatibleRoles: ['synthesizer'], supportsTools: true, supportsStructuredOutput: true })
    const model = binding.model as LanguageModelV3
    const result = await model.doGenerate({ prompt: [{ role: 'user', content: [{ type: 'text', text: 'Hi' }] }], maxOutputTokens: 16 })
    expect(result.content).toContainEqual({ type: 'text', text: 'OK' })
    const request = http.mock.calls[0][1]
    const body = JSON.parse(request.body)
    const field = ['openai', 'kimi', 'openrouter'].includes(provider) ? 'max_completion_tokens' : 'max_tokens'
    if (provider === 'google') expect(body.generationConfig.maxOutputTokens).toBe(16)
    else expect(body[field]).toBe(16)
    expect(new Headers(request.headers).get(provider === 'google' ? 'x-goog-api-key' : provider === 'anthropic' ? 'x-api-key' : 'authorization')).toBe(provider === 'google' || provider === 'anthropic' ? key : `Bearer ${key}`)
    binding.dispose()
    await expect(model.doGenerate({ prompt: [{ role: 'user', content: [{ type: 'text', text: 'Hi' }] }] })).rejects.toBeDefined()
    expect(http).toHaveBeenCalledTimes(1)
  })
  it('discovers compatible models, authenticates, caps the fixed probe, and returns usage only', async () => {
    const http = vi.fn().mockResolvedValueOnce(Response.json(catalog(provider))).mockResolvedValueOnce(Response.json(completion(provider)))
    vi.stubGlobal('fetch', http)
    const adapter = getProviderAdapter(provider)
    const models = await adapter.discover(key, signal())
    expect(models).toHaveLength(1)
    expect(models[0].modelId).toBe(ids[provider])
    expect(models[0].compatibleRoles).toContain('synthesizer')
    expect(await adapter.probe(key, models[0], signal())).toEqual({ inputTokens: 4, outputTokens: 1 })
    for (const [url, init] of http.mock.calls) {
      expect(new URL(String(url)).hostname).toBe(hosts[provider])
      expect(init.redirect).toBe('error')
      expect(init.cache).toBe('no-store')
      expect(init.signal).toBeInstanceOf(AbortSignal)
      const headers = new Headers(init.headers)
      expect(headers.get(provider === 'anthropic' ? 'x-api-key' : provider === 'google' ? 'x-goog-api-key' : 'authorization')).toBe(provider === 'anthropic' || provider === 'google' ? key : `Bearer ${key}`)
      expect(String(url)).not.toContain(key)
    }
    const body = JSON.parse(http.mock.calls[1][1].body)
    const cap = provider === 'google' ? body.generationConfig.maxOutputTokens : body.max_completion_tokens ?? body.max_tokens
    expect(cap).toBeGreaterThan(0)
    expect(cap).toBeLessThanOrEqual(16)
    if (provider === 'openrouter') expect(body.provider.allow_fallbacks).toBe(false)
    expect(body.stream).not.toBe(true)
  })
  it.each([[401, 'AI_CONNECTION_INVALID'], [402, 'AI_BILLING_UNAVAILABLE'], [403, 'AI_PERMISSION_DENIED'], [429, 'AI_RATE_LIMITED'], [404, 'AI_MODEL_UNAVAILABLE'], [503, 'AI_PROVIDER_UNREACHABLE']])('redacts HTTP %s failure from discovery and probe', async (status, code) => {
    vi.stubGlobal('fetch', vi.fn().mockImplementation(() => Promise.resolve(Response.json({ error: { message: key } }, { status: Number(status) }))))
    const adapter = getProviderAdapter(provider)
    for (const op of [() => adapter.discover(key, signal()), () => adapter.probe(key, { modelId: ids[provider], displayName: 'Text', compatibleRoles: ['synthesizer'], supportsTools: false, supportsStructuredOutput: false }, signal())]) {
      const error = await op().catch(e => e)
      expect(normalizeAiError(error, { source: 'provider' }).code).toBe(code)
      expect(JSON.stringify(error)).not.toContain(key)
      expect(inspect(error)).not.toContain(key)
    }
  })
  it('returns no compatible models from embedding-only catalogs', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(Response.json(provider === 'google' ? { models: [{ name: 'models/text-embedding', supportedGenerationMethods: ['embedContent'] }] } : { data: [{ id: 'text-embedding-only', architecture: { output_modalities: ['embeddings'] } }] })))
    expect(await getProviderAdapter(provider).discover(key, signal())).toEqual([])
  })
  it('normalizes network errors and timeout; never retries automatically', async () => {
    const http = vi.fn().mockRejectedValue(new TypeError(key))
    vi.stubGlobal('fetch', http)
    await expect(getProviderAdapter(provider).discover(key, signal())).rejects.toMatchObject({ code: 'AI_PROVIDER_UNREACHABLE' })
    expect(http).toHaveBeenCalledTimes(1)
    vi.useFakeTimers()
    http.mockImplementation((_url, init) => new Promise((_resolve, reject) => init.signal.addEventListener('abort', () => reject(new Error(key)))))
    const check = getProviderAdapter(provider).discover(key, signal())
    const rejection = expect(check).rejects.toMatchObject({ code: 'AI_PROVIDER_UNREACHABLE' })
    await vi.advanceTimersByTimeAsync(15_001)
    await rejection
  })
  it('fails closed on malformed success, redirect and oversized bodies', async () => {
    for (const response of [Response.json({ unexpected: key }), new Response(null, { status: 302, headers: { location: 'https://example.com' } }), new Response('x'.repeat(2_097_153))]) {
      vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response))
      await expect(getProviderAdapter(provider).discover(key, signal())).rejects.toMatchObject({ code: 'AI_EXECUTION_FAILED' })
    }
  })
  it('rejects impossible keys before any request and hides disposable runtime bindings', async () => {
    const http = vi.fn().mockResolvedValue(Response.json(catalog(provider)))
    vi.stubGlobal('fetch', http)
    await expect(getProviderAdapter(provider).discover(' \n', signal())).rejects.toMatchObject({ code: 'AI_CONNECTION_INVALID' })
    expect(http).not.toHaveBeenCalled()
    const [model] = await getProviderAdapter(provider).discover(key, signal())
    const binding = getProviderAdapter(provider).createRuntimeBinding(key, model)
    expect(() => JSON.stringify(binding)).toThrow()
    expect(Object.keys(binding)).not.toContain('model')
    expect(inspect(binding)).not.toContain(key)
    expect(binding.model).toBeDefined()
    binding.dispose()
    expect(() => binding.model).toThrow()
  })
})

it('rejects unsupported provider IDs instead of accepting a base URL', () => {
  expect(() => getProviderAdapter('https://example.com' as ProviderId)).toThrow()
})
