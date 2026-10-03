import 'server-only'
import { createAnthropic } from '@ai-sdk/anthropic'
import { filterCatalog, safeModelId } from './catalog-policy'
import { fail, MAX_CATALOG_PAGES, object, PROBE_OUTPUT_TOKENS, PROBE_PROMPT, PROVIDER_BASE_URLS, providerJson, runtimeBinding, tokenCount, type ProviderValidationAdapter } from './types'

// The authenticated Models API advertises these exact capability fields:
// https://platform.claude.com/docs/en/api/models/list
// Read only known boolean support flags; never infer an unseen model's effort
// levels from its family name or arbitrary keys returned by the provider.
const EFFORT_LEVELS = ['low', 'medium', 'high', 'xhigh', 'max'] as const
function advertisedEfforts(row: unknown): string[] | undefined {
  const effort = object(object(row).capabilities).effort
  if (!effort || typeof effort !== 'object' || Array.isArray(effort)) return undefined
  const support = object(effort)
  if (support.supported === false) return []
  return EFFORT_LEVELS.filter(level => object(support[level]).supported === true)
}

function anthropicCatalog(rows: unknown[], apiKey: string) {
  const efforts = new Map<string, string[] | undefined>()
  for (const row of rows) {
    const id = object(row).id
    if (safeModelId(id)) efforts.set(id, advertisedEfforts(row))
  }
  return filterCatalog('anthropic', rows, apiKey).map(model => {
    const supportedEfforts = efforts.get(model.modelId)
    return supportedEfforts === undefined ? model : { ...model, supportedEfforts, defaultEffort: null }
  })
}

export const anthropicAdapter: ProviderValidationAdapter = Object.freeze({
  providerId: 'anthropic',
  async discover(apiKey, signal, preflight, workspaceId) {
    const rows: unknown[] = []
    let cursor = ''
    for (let page = 0; page < MAX_CATALOG_PAGES; page++) {
      const data = await providerJson('anthropic', apiKey, `/models?limit=1000${cursor ? `&after_id=${encodeURIComponent(cursor)}` : ''}`, signal, undefined, preflight, workspaceId)
      if (!Array.isArray(data.data)) throw fail()
      rows.push(...data.data)
      if (data.has_more !== true) return anthropicCatalog(rows, apiKey)
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
