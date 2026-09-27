import 'server-only'
import { createGoogleGenerativeAI } from '@ai-sdk/google'
import { filterCatalog, safeModelId } from './catalog-policy'
import { fail, MAX_CATALOG_PAGES, object, PROBE_OUTPUT_TOKENS, PROBE_PROMPT, PROVIDER_BASE_URLS, providerJson, runtimeBinding, tokenCount, type ProviderValidationAdapter } from './types'

export const googleAdapter: ProviderValidationAdapter = Object.freeze({
  providerId: 'google',
  async discover(apiKey, signal) {
    const rows: unknown[] = []
    let cursor = ''
    for (let page = 0; page < MAX_CATALOG_PAGES; page++) {
      const data = await providerJson('google', apiKey, `/models?pageSize=1000${cursor ? `&pageToken=${encodeURIComponent(cursor)}` : ''}`, signal)
      if (!Array.isArray(data.models)) throw fail()
      rows.push(...data.models)
      if (data.nextPageToken === undefined) return filterCatalog('google', rows, apiKey)
      if (typeof data.nextPageToken !== 'string' || !data.nextPageToken || data.nextPageToken.length > 2048 || data.nextPageToken === cursor) throw fail()
      cursor = data.nextPageToken
    }
    throw fail()
  },
  async probe(apiKey, model, signal) {
    if (!safeModelId(model.modelId) || model.modelId.includes('/')) throw fail()
    const data = await providerJson('google', apiKey, `/models/${encodeURIComponent(model.modelId)}:generateContent`, signal, {
      contents: [{ role: 'user', parts: [{ text: PROBE_PROMPT }] }], generationConfig: { maxOutputTokens: PROBE_OUTPUT_TOKENS },
    })
    const usage = object(data.usageMetadata)
    const outputTokens = tokenCount(usage.candidatesTokenCount)
    if (!Array.isArray(data.candidates) || !data.candidates.length || !outputTokens) throw fail()
    return { inputTokens: tokenCount(usage.promptTokenCount), outputTokens }
  },
  createRuntimeBinding(apiKey, model) {
    if (!safeModelId(model.modelId) || model.modelId.includes('/')) throw fail()
    return runtimeBinding('google', apiKey, model.modelId, http => createGoogleGenerativeAI({ apiKey: 'request-owned', baseURL: PROVIDER_BASE_URLS.google, fetch: http })(model.modelId))
  },
} satisfies ProviderValidationAdapter)
