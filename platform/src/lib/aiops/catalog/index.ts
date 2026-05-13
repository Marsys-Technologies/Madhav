import type { Provider } from '@/lib/models/registry'
import type { CatalogEntry, CatalogFetchResult } from './types'
import { fetchProviderCatalog } from './fetcher'

export type { CatalogEntry, CatalogFetchResult }
export { fetchProviderCatalog }

const ALL_PROVIDERS: Provider[] = ['nvidia', 'google', 'deepseek', 'openai', 'anthropic']

/** Fetch catalogs for all providers; returns a flat cross-provider list. */
export async function getCrossProviderCatalog(): Promise<CatalogEntry[]> {
  const results = await Promise.all(ALL_PROVIDERS.map(fetchProviderCatalog))
  return results.flatMap(r => r.models)
}

/** Fetch catalog for a single provider. */
export async function getCatalog(provider: Provider): Promise<CatalogFetchResult> {
  return fetchProviderCatalog(provider)
}
