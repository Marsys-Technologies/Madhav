import { afterEach, describe, expect, it, vi } from 'vitest'
import { inspect } from 'node:util'
import { getProviderAdapter } from '../index'
import { filterCatalog } from '../catalog-policy'
import type { ProviderId } from '../../types'
import type { DiscoveredModel } from '../types'

const key = 'synthetic-review-secret-1234'
const signal = () => new AbortController().signal
const model: DiscoveredModel = { modelId: 'gpt-4.1-mini', displayName: 'Mini', compatibleRoles: ['synthesizer'], supportsTools: false, supportsStructuredOutput: false }
afterEach(() => { vi.unstubAllGlobals(); vi.useRealTimers() })
function row(provider: ProviderId, id: string, extra = {}) {
  return { id, name: provider === 'google' ? `models/${id}` : id, architecture: { output_modalities: ['text'] }, supportedGenerationMethods: ['generateContent'], ...extra }
}
describe('conservative capability evidence', () => {
  it.each([
    ['openai', 'gpt-4.1-unknown'], ['anthropic', 'claude-unknown'], ['google', 'gemini-unknown'],
    ['xai', 'grok-unknown'], ['deepseek', 'deepseek-unknown'], ['kimi', 'kimi-unknown'], ['openrouter', 'vendor/unknown'],
  ] as const)('%s missing capability evidence cannot gain tools or planners', (provider, id) => {
    expect(filterCatalog(provider, [row(provider, id)], key)[0]).toMatchObject({ supportsTools: false, supportsStructuredOutput: false, compatibleRoles: ['synthesizer'] })
  })
  it('retains documented GPT-4.1 mini capabilities but search-preview never becomes a Worker', () => {
    expect(filterCatalog('openai', [{ id: 'gpt-4.1-mini' }], key)[0].compatibleRoles).toEqual(['synthesizer', 'planner', 'deep_planner', 'worker'])
    expect(filterCatalog('openai', [{ id: 'gpt-4o-search-preview', supported_parameters: ['tools', 'structured_outputs'] }], key)[0]).toMatchObject({ supportsTools: false, compatibleRoles: ['synthesizer', 'planner', 'deep_planner'] })
  })
  it.each([['anthropic', 'claude-haiku-4-5'], ['google', 'gemini-2.5-flash'], ['xai', 'grok-4']] as const)('keeps explicitly documented %s model rules', (provider, id) => {
    expect(filterCatalog(provider, [row(provider, id)], key)[0].compatibleRoles).toEqual(['synthesizer', 'planner', 'deep_planner', 'worker'])
  })
  it.each([['kimi', 'kimi-k2.5'], ['deepseek', 'deepseek-flash'], ['deepseek', 'deepseek-v4-pro']] as const)('%s %s is synthesis-only despite advertised tools/schema', (provider, id) => {
    expect(filterCatalog(provider, [row(provider, id, { supported_parameters: ['tools', 'response_format', 'structured_outputs'], capabilities: { tools: true, structured_outputs: true } })], key)[0])
      .toMatchObject({ supportsTools: false, supportsStructuredOutput: false, compatibleRoles: ['synthesizer'] })
  })
  it('requires OpenRouter structured_outputs rather than generic response_format and never enables Worker', () => {
    expect(filterCatalog('openrouter', [row('openrouter', 'vendor/json', { supported_parameters: ['tools', 'response_format'] })], key)[0].compatibleRoles).toEqual(['synthesizer'])
    expect(filterCatalog('openrouter', [row('openrouter', 'vendor/schema', { supported_parameters: ['tools', 'structured_outputs'] })], key)[0].compatibleRoles).toEqual(['synthesizer', 'planner', 'deep_planner'])
  })
  it('does not let generic parameter metadata override an explicit capability denial', () => {
    expect(filterCatalog('openrouter', [row('openrouter', 'vendor/schema', { supported_parameters: ['structured_outputs'], capabilities: { structured_outputs: false } })], key)[0].compatibleRoles).toEqual(['synthesizer'])
  })
  it('emits OpenRouter single-turn json_schema exactly, with no fallback', async () => {
    const http = vi.fn().mockResolvedValue(Response.json({ choices: [{ index: 0, message: { role: 'assistant', content: '{"ok":true}' }, finish_reason: 'stop' }], usage: { prompt_tokens: 4, completion_tokens: 4 } }))
    vi.stubGlobal('fetch', http)
    const [supported] = filterCatalog('openrouter', [row('openrouter', 'vendor/schema', { supported_parameters: ['structured_outputs'] })], key)
    const binding = getProviderAdapter('openrouter').createRuntimeBinding(key, supported)
    const schema = { type: 'object' as const, properties: { ok: { type: 'boolean' as const } }, required: ['ok'], additionalProperties: false }
    await binding.model.doGenerate({ prompt: [{ role: 'user', content: [{ type: 'text', text: 'Return status' }] }], responseFormat: { type: 'json', name: 'status', schema } })
    const body = JSON.parse(http.mock.calls[0][1].body)
    expect(body.response_format).toEqual({ type: 'json_schema', json_schema: { name: 'status', schema, strict: true } })
    expect(body.provider).toEqual({ allow_fallbacks: false, require_parameters: true }); binding.dispose()
  })
})
describe('bounded machine-only billing discriminators', () => {
  it.each(['insufficient_quota', 'credit_balance_exhausted', 'organization_spend_limit_exceeded', 'project_spend_limit_exceeded', 'organization_usage_limit_exceeded'])('classifies OpenAI %s on probe and runtime without retaining bodies', async code => {
    vi.stubGlobal('fetch', vi.fn().mockImplementation(async () => Response.json({ error: { code, message: key, private: key } }, { status: 429 })))
    const adapter = getProviderAdapter('openai')
    const binding = adapter.createRuntimeBinding(key, model)
    for (const op of [() => adapter.probe(key, model, signal()), () => binding.model.doGenerate({ prompt: [] })]) {
      const error = await Promise.resolve(op()).catch(e => e)
      expect(error.code).toBe('AI_BILLING_UNAVAILABLE')
      expect(JSON.stringify(error)).not.toContain(key); expect(inspect(error)).not.toContain(key)
    }
    binding.dispose()
  })
  it('uses only documented Kimi machine types, not provider messages', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(Response.json({ error: { type: 'exceeded_current_quota_error', message: key } }, { status: 429 })))
    await expect(getProviderAdapter('kimi').probe(key, { ...model, modelId: 'kimi-k2.5' }, signal())).rejects.toMatchObject({ code: 'AI_BILLING_UNAVAILABLE' })
  })
  it.each([
    JSON.stringify({ error: { code: 'rate_limit_exceeded', message: 'insufficient_quota' } }),
    JSON.stringify({ error: { code: key } }), '{malformed',
    JSON.stringify({ error: { code: 'insufficient_quota', message: 'x'.repeat(8192) } }),
  ])('keeps ordinary/malformed/oversized 429 as rate limited and redacted', async body => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(body, { status: 429 })))
    const error = await getProviderAdapter('openai').probe(key, model, signal()).catch(e => e)
    expect(error.code).toBe('AI_RATE_LIMITED'); expect(inspect(error)).not.toContain(key)
  })
  it('reads at most the error-body cap, cancels the rest, and never parses a partial discriminator', async () => {
    let pulls = 0; const cancel = vi.fn()
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(new ReadableStream({
      pull(c) { pulls++; c.enqueue(new TextEncoder().encode('x'.repeat(1024))) }, cancel,
    }), { status: 429 })))
    await expect(getProviderAdapter('openai').probe(key, model, signal())).rejects.toMatchObject({ code: 'AI_RATE_LIMITED' })
    expect(pulls).toBeGreaterThan(1); expect(pulls).toBeLessThanOrEqual(10); expect(cancel).toHaveBeenCalled()
  })
  it('includes stalled error bodies in the same timeout budget', async () => {
    vi.useFakeTimers()
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(new ReadableStream({ start() {} }), { status: 429 })))
    const pending = getProviderAdapter('openai').probe(key, model, signal()).catch(e => e)
    await vi.advanceTimersByTimeAsync(15001)
    expect(await pending).toMatchObject({ code: 'AI_PROVIDER_UNREACHABLE' })
  })
})
describe('Gemini thinking-aware probe', () => {
  it('accepts real thinking-token evidence without fabricating visible output', async () => {
    const http = vi.fn().mockResolvedValue(Response.json({ candidates: [{ finishReason: 'MAX_TOKENS' }], usageMetadata: { promptTokenCount: 4, candidatesTokenCount: 0, thoughtsTokenCount: 128 } }))
    vi.stubGlobal('fetch', http)
    const usage = await getProviderAdapter('google').probe(key, { ...model, modelId: 'gemini-2.5-pro' }, signal())
    expect(usage).toEqual({ inputTokens: 4, outputTokens: 0, reasoningTokens: 128 })
    const cap = JSON.parse(http.mock.calls[0][1].body).generationConfig.maxOutputTokens
    expect(cap).toBeGreaterThanOrEqual(128); expect(cap).toBeLessThanOrEqual(256)
  })
  it('does not validate a genuinely empty or prompt-only response', async () => {
    for (const usageMetadata of [{ promptTokenCount: 4 }, { promptTokenCount: 4, thoughtsTokenCount: 0, candidatesTokenCount: 0 }]) {
      vi.stubGlobal('fetch', vi.fn().mockResolvedValue(Response.json({ candidates: [{ finishReason: 'MAX_TOKENS' }], usageMetadata })))
      await expect(getProviderAdapter('google').probe(key, { ...model, modelId: 'gemini-2.5-pro' }, signal())).rejects.toMatchObject({ code: 'AI_EXECUTION_FAILED' })
    }
  })
})
