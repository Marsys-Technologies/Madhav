import type { Provider } from '@/lib/models/registry'
import type { CatalogFetchResult, RawModelEntry } from './types'
import { fetchNimCatalog } from './fetcher_nim'
import { fetchGeminiCatalog } from './fetcher_gemini'
import { fetchDeepseekCatalog } from './fetcher_deepseek'
import { fetchOpenaiCatalog } from './fetcher_openai'
import { fetchAnthropicCatalog } from './fetcher_anthropic'
import { augmentEntries } from './augment'
import { getCached, setCached, makeStaleResult } from './cache'

/** Dispatches to the correct provider fetcher and augments results. */
export async function fetchProviderCatalog(provider: Provider): Promise<CatalogFetchResult> {
  // Return from cache if fresh
  const cached = getCached(provider)
  if (cached) {
    return { status: 'ok', models: cached.models, raw: null, fetched_at: cached.fetched_at }
  }

  // Dispatch to per-provider fetcher
  let raw: CatalogFetchResult
  switch (provider) {
    case 'nvidia':    raw = await fetchNimCatalog();       break
    case 'google':    raw = await fetchGeminiCatalog();    break
    case 'deepseek':  raw = await fetchDeepseekCatalog();  break
    case 'openai':    raw = await fetchOpenaiCatalog();    break
    case 'anthropic': raw = await fetchAnthropicCatalog(); break
    default: {
      const _never: never = provider
      void _never
      return { status: 'error', models: [], raw: null, fetched_at: new Date().toISOString() }
    }
  }

  if (raw.status !== 'ok') {
    return makeStaleResult(provider, raw)
  }

  // Augment raw entries with metadata
  const augmented = augmentEntries(raw.models as unknown as RawModelEntry[], provider)
  setCached(provider, augmented, raw.fetched_at)

  return { ...raw, models: augmented }
}
