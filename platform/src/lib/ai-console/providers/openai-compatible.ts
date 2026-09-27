import 'server-only'
import { createOpenAI } from '@ai-sdk/openai'
import type { ProviderId } from '../types'
import { filterCatalog, safeModelId } from './catalog-policy'
import { fail, MAX_CATALOG_PAGES, object, PROBE_OUTPUT_TOKENS, PROBE_PROMPT, PROVIDER_BASE_URLS, providerJson, runtimeBinding, tokenCount, type ProviderValidationAdapter } from './types'

export type OpenAICompatibleProvider = Exclude<ProviderId, 'anthropic' | 'google'>
export function createOpenAICompatibleAdapter(providerId: OpenAICompatibleProvider): ProviderValidationAdapter {
  return Object.freeze({
    providerId,
    async discover(apiKey, signal, preflight) {
      const rows: unknown[] = []
      for (let page = 0; page < MAX_CATALOG_PAGES; page++) {
        const path = providerId === 'openrouter' ? `/models/user?limit=500&offset=${page * 500}` : '/models'
        const data = await providerJson(providerId, apiKey, path, signal, undefined, preflight)
        if (!Array.isArray(data.data)) throw fail()
        rows.push(...data.data)
        if (providerId !== 'openrouter' || data.data.length < 500) return filterCatalog(providerId, rows, apiKey)
      }
      throw fail() // A partial catalog must not tombstone models from unvisited pages.
    },
    async probe(apiKey, model, signal, preflight) {
      if (!safeModelId(model.modelId)) throw fail()
      const field = providerId === 'openai' || providerId === 'kimi' || providerId === 'openrouter' ? 'max_completion_tokens' : 'max_tokens'
      const result = await providerJson(providerId, apiKey, '/chat/completions', signal, {
        model: model.modelId, messages: [{ role: 'user', content: PROBE_PROMPT }], [field]: PROBE_OUTPUT_TOKENS, stream: false,
        ...(providerId === 'openrouter' ? { provider: { allow_fallbacks: false, require_parameters: true } } : {}),
      }, preflight)
      if (!Array.isArray(result.choices) || !result.choices.length) throw fail()
      const usage = object(result.usage)
      const outputTokens = tokenCount(usage.completion_tokens)
      if (outputTokens === null || outputTokens === 0) throw fail()
      return { inputTokens: tokenCount(usage.prompt_tokens), outputTokens }
    },
    createRuntimeBinding(apiKey, model, preflight) {
      if (!safeModelId(model.modelId)) throw fail()
      // Explicit sentinel prevents SDK env lookup; hardened fetch injects the request-owned key.
      return runtimeBinding(providerId, apiKey, model.modelId, http => createOpenAI({ apiKey: 'request-owned', baseURL: PROVIDER_BASE_URLS[providerId], fetch: http }).chat(model.modelId), preflight)
    },
  } satisfies ProviderValidationAdapter)
}
