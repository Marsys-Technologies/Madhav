import 'server-only'
import { createAnthropic } from '@ai-sdk/anthropic'
import { filterCatalog, safeModelId } from './catalog-policy'
import { fail, MAX_CATALOG_PAGES, object, PROBE_OUTPUT_TOKENS, PROBE_PROMPT, PROVIDER_BASE_URLS, providerJson, runtimeBinding, tokenCount, type ProviderValidationAdapter } from './types'

export const anthropicAdapter: ProviderValidationAdapter = Object.freeze({
  providerId: 'anthropic',
  async discover(apiKey, signal, preflight, workspaceId) {
    const rows: unknown[] = []
    let cursor = ''
    for (let page = 0; page < MAX_CATALOG_PAGES; page++) {
      const data = await providerJson('anthropic', apiKey, `/models?limit=1000${cursor ? `&after_id=${encodeURIComponent(cursor)}` : ''}`, signal, undefined, preflight, workspaceId)
      if (!Array.isArray(data.data)) throw fail()
      rows.push(...data.data)
      if (data.has_more !== true) return filterCatalog('anthropic', rows, apiKey)
      if (!safeModelId(data.last_id) || data.last_id === cursor) throw fail()
      cursor = data.last_id
    }
    throw fail()
  },
  async probe(apiKey, model, signal, preflight, workspaceId) {
    if (!safeModelId(model.modelId)) throw fail()
    const data = await providerJson('anthropic', apiKey, '/messages', signal, {
      model: model.modelId, messages: [{ role: 'user', content: PROBE_PROMPT }], max_tokens: PROBE_OUTPUT_TOKENS, stream: false,
    }, preflight, workspaceId)
    const usage = object(data.usage)
    const outputTokens = tokenCount(usage.output_tokens)
    if (data.type !== 'message' || !Array.isArray(data.content) || !data.content.length || !outputTokens) throw fail()
    return { inputTokens: tokenCount(usage.input_tokens), outputTokens }
  },
  createRuntimeBinding(apiKey, model, preflight, workspaceId) {
    if (!safeModelId(model.modelId)) throw fail()
    return runtimeBinding('anthropic', apiKey, model.modelId, http => createAnthropic({ apiKey: 'request-owned', baseURL: PROVIDER_BASE_URLS.anthropic, fetch: http })(model.modelId), preflight, workspaceId)
  },
} satisfies ProviderValidationAdapter)
