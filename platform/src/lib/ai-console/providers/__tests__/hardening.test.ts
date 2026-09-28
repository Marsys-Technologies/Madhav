import { afterEach, describe, expect, it, vi } from 'vitest'
import { getProviderAdapter } from '../index'
import { filterCatalog } from '../catalog-policy'
import { boundedFetch, runtimeBinding } from '../types'
import type { LanguageModelV3 } from '@ai-sdk/provider'

const key = 'synthetic-user-key-1234'
const signal = () => new AbortController().signal
afterEach(() => { vi.unstubAllGlobals(); vi.unstubAllEnvs(); vi.useRealTimers() })
describe('catalog protocol policy', () => {
  it('excludes retired, nontext, unsupported, traversal and malicious labels while preserving capability limits', () => {
    expect(filterCatalog('openai', [
      { id: 'gpt-4.1', retired: true }, { id: 'gpt-4o-audio' }, { id: 'gpt-4.1-image' }, { id: 'gpt-4.1/../unsafe' },
      { id: 'gpt-4.1-dead', expiration_date: '2020-01-01' }, { id: 'gpt-4.1-video', output_modalities: ['video'] },
      { id: 'gpt-4.1-mini', display_name: key, context_length: 1000, max_output_tokens: 40, supported_parameters: [] },
    ], key)).toEqual([{ modelId: 'gpt-4.1-mini', displayName: 'gpt-4.1-mini', compatibleRoles: ['synthesizer'], supportsTools: false, supportsStructuredOutput: false, contextWindow: 1000, outputLimit: 40 }])
  })
  it('never infers tool support for Gemini models explicitly lacking function-call capability', () => {
    expect(filterCatalog('google', [{ name: 'models/gemini-2.5-flash', supportedGenerationMethods: ['generateContent'], capabilities: { tools: false, structured_outputs: { supported: false } } }], key)[0].compatibleRoles).toEqual(['synthesizer'])
  })
  it('rejects routing aliases even when a catalog advertises text', () => {
    expect(filterCatalog('openrouter', ['openrouter/auto', 'openrouter/free', 'vendor/model:online', 'vendor/model:nitro'].map(id => ({ id, architecture: { output_modalities: ['text'] } })), key)).toEqual([])
  })
})
describe('bounded authenticated pagination', () => {
  it('does not forward arbitrary upstream header values into SDK response metadata', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('{}', { headers: { 'content-type': `application/json; private=${key}`, 'x-secret': key } })))
    const response = await boundedFetch('https://api.openai.com/v1/models', { method: 'GET' }, 1000, 100)
    await response.json()
    expect(JSON.stringify([...response.headers])).not.toContain(key)
    expect(response.headers.get('content-type')).toBe('application/json')
  })
  it('follows Anthropic cursors without moving hosts or losing authentication', async () => {
    const http = vi.fn().mockResolvedValueOnce(Response.json({ data: [{ id: 'claude-haiku-4-5' }], has_more: true, last_id: 'claude/haiku' })).mockResolvedValueOnce(Response.json({ data: [{ id: 'claude-sonnet-4-5' }], has_more: false }))
    vi.stubGlobal('fetch', http)
    expect(await getProviderAdapter('anthropic').discover(key, signal())).toHaveLength(2)
    expect(String(http.mock.calls[1][0])).toContain('after_id=claude%2Fhaiku')
    expect(new Headers(http.mock.calls[1][1].headers).get('x-api-key')).toBe(key)
  })
  it('follows Gemini tokens with header authentication, and rejects nonterminating pagination', async () => {
    const http = vi.fn().mockImplementation(async () => Response.json({ models: [{ name: 'models/gemini-2.5-flash', supportedGenerationMethods: ['generateContent'] }], nextPageToken: 'token/?' }))
    vi.stubGlobal('fetch', http)
    await expect(getProviderAdapter('google').discover(key, signal())).rejects.toMatchObject({ code: 'AI_EXECUTION_FAILED' })
    expect(String(http.mock.calls[1][0])).toContain('pageToken=token%2F%3F')
    expect(http.mock.calls.length).toBeLessThanOrEqual(10)
  })
  it('uses OpenRouter user-filtered pagination and refuses a truncated catalog', async () => {
    const http = vi.fn().mockImplementation(async () => Response.json({ data: Array.from({ length: 500 }, (_, i) => ({ id: `vendor/model-${i}`, architecture: { output_modalities: ['text'] } })) }))
    vi.stubGlobal('fetch', http)
    await expect(getProviderAdapter('openrouter').discover(key, signal())).rejects.toMatchObject({ code: 'AI_EXECUTION_FAILED' })
    expect(http).toHaveBeenCalledTimes(10)
    expect(String(http.mock.calls[1][0])).toBe('https://openrouter.ai/api/v1/models/user?limit=500&offset=500')
  })
  it('aborts stalled response bodies as well as stalled headers', async () => {
    vi.useFakeTimers()
    const cancel = vi.fn()
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(new ReadableStream({ start() {}, cancel }))))
    const pending = getProviderAdapter('openai').discover(key, signal())
    const assertion = expect(pending).rejects.toMatchObject({ code: 'AI_PROVIDER_UNREACHABLE' })
    await vi.advanceTimersByTimeAsync(15_001); await assertion
    expect(cancel).toHaveBeenCalled()
  })
  it('honors caller cancellation without making a request or echoing its reason', async () => {
    const http = vi.fn(); vi.stubGlobal('fetch', http)
    const controller = new AbortController(); controller.abort(key)
    await expect(getProviderAdapter('openai').discover(key, controller.signal)).rejects.toMatchObject({ code: 'AI_EXECUTION_FAILED' })
    expect(http).not.toHaveBeenCalled()
  })
})
describe('request-owned runtime transport', () => {
  it('enforces exact Gemini paths (a dot is not a wildcard), fixed host, and POST only', async () => {
    let transport!: typeof fetch
    const binding = runtimeBinding('google', key, 'gemini-2.5-flash', http => { transport = http; return {} as LanguageModelV3 })
    const http = vi.fn(); vi.stubGlobal('fetch', http)
    for (const url of ['https://generativelanguage.googleapis.com/v1beta/models/gemini-2X5-flash:generateContent', 'https://example.com/v1beta/models/gemini-2.5-flash:generateContent']) {
      await expect(transport(url, { method: 'POST' })).rejects.toMatchObject({ code: 'AI_EXECUTION_FAILED' })
    }
    expect(http).not.toHaveBeenCalled(); binding.dispose()
  })
  it('replaces env/shared credentials, disables OpenRouter fallbacks, and revokes extracted SDK transport', async () => {
    vi.stubEnv('OPENAI_API_KEY', 'never-use-shared')
    let transport!: typeof fetch
    const binding = runtimeBinding('openrouter', key, 'vendor/exact', http => { transport = http; return {} as LanguageModelV3 })
    const http = vi.fn().mockResolvedValue(Response.json({ ok: true })); vi.stubGlobal('fetch', http)
    const response = await transport('https://openrouter.ai/api/v1/chat/completions', { method: 'POST', headers: { authorization: 'Bearer never-use-shared' }, body: JSON.stringify({ model: 'auto', models: ['other'], provider: { allow_fallbacks: true } }) })
    await response.json()
    expect(new Headers(http.mock.calls[0][1].headers).get('authorization')).toBe(`Bearer ${key}`)
    expect(JSON.parse(http.mock.calls[0][1].body)).toEqual({ model: 'vendor/exact', provider: { allow_fallbacks: false, require_parameters: true } })
    binding.dispose()
    await expect(transport('https://openrouter.ai/api/v1/chat/completions', { method: 'POST' })).rejects.toMatchObject({ code: 'AI_EXECUTION_FAILED' })
    expect(http).toHaveBeenCalledTimes(1)
  })
  it('normalizes streaming error events without retaining SDK body/cause metadata', async () => {
    const binding = runtimeBinding('openai', key, 'gpt-4.1', () => ({
      specificationVersion: 'v3', provider: 'openai', modelId: 'gpt-4.1', supportedUrls: {},
      doGenerate: vi.fn(), doStream: async () => ({ stream: new ReadableStream({ start(c) { c.enqueue({ type: 'error', error: { status: 403, body: key } }); c.close() } }) }),
    }))
    const result = await (binding.model as LanguageModelV3).doStream({ prompt: [] })
    const event = await result.stream.getReader().read()
    expect(event.value).toMatchObject({ type: 'error', error: { code: 'AI_PERMISSION_DENIED' } })
    expect(JSON.stringify(event.value)).not.toContain(key)
    binding.dispose()
  })
})
