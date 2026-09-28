import 'server-only'
import { createGoogleGenerativeAI } from '@ai-sdk/google'
import { filterCatalog, safeModelId } from './catalog-policy'
import { fail, MAX_CATALOG_PAGES, object, PROBE_PROMPT, PROVIDER_BASE_URLS, providerJson, runtimeBinding, tokenCount, type ProviderValidationAdapter } from './types'

export const googleAdapter: ProviderValidationAdapter = Object.freeze({
  providerId: 'google',
  async discover(apiKey, signal, preflight) {
    const rows: unknown[] = []
    let cursor = ''
    for (let page = 0; page < MAX_CATALOG_PAGES; page++) {
      const data = await providerJson('google', apiKey, `/models?pageSize=1000${cursor ? `&pageToken=${encodeURIComponent(cursor)}` : ''}`, signal, undefined, preflight)
      if (!Array.isArray(data.models)) throw fail()
      rows.push(...data.models)
      if (data.nextPageToken === undefined) return filterCatalog('google', rows, apiKey)
      if (typeof data.nextPageToken !== 'string' || !data.nextPageToken || data.nextPageToken.length > 2048 || data.nextPageToken === cursor) throw fail()
      cursor = data.nextPageToken
    }
    throw fail()
  },
  async probe(apiKey, model, signal, preflight) {
    if (!safeModelId(model.modelId) || model.modelId.includes('/')) throw fail()
    const data = await providerJson('google', apiKey, `/models/${encodeURIComponent(model.modelId)}:generateContent`, signal, {
      // Default thinking consumes this same hard output budget. 256 permits the
      // documented 128-token minimum reasoning allocation without an uncapped call.
      contents: [{ role: 'user', parts: [{ text: PROBE_PROMPT }] }], generationConfig: { maxOutputTokens: 256 },
    }, preflight)
    const usage = object(data.usageMetadata)
    const outputTokens = tokenCount(usage.candidatesTokenCount)
    const reasoningTokens = tokenCount(usage.thoughtsTokenCount)
    if ((!Array.isArray(data.candidates) || !data.candidates.length || !outputTokens) && !reasoningTokens) throw fail()
    return { inputTokens: tokenCount(usage.promptTokenCount), outputTokens, ...(reasoningTokens ? { reasoningTokens } : {}) }
  },
  createRuntimeBinding(apiKey, model, preflight) {
    if (!safeModelId(model.modelId) || model.modelId.includes('/')) throw fail()
    return runtimeBinding('google', apiKey, model.modelId, http => createGoogleGenerativeAI({ apiKey: 'request-owned', baseURL: PROVIDER_BASE_URLS.google, fetch: http })(model.modelId), preflight)
  },
} satisfies ProviderValidationAdapter)
