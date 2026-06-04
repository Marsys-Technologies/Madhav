/**
 * Tool 25: classical_text_search
 *
 * classical_chunks, classical_texts dropped in WS-0. Stub returns empty results.
 * TODO(ws-2): repoint to brahmagyan.texts (sidecar asset) once the L0 classical
 * corpus is queryable via the platform retrieval layer.
 */

import 'server-only'

export interface ClassicalTextSearchInput {
  query: string
  schools?: string[]
  tier_max?: number
  limit?: number
}

export interface ClassicalTextSearchResult {
  chunk_id: string
  text_key: string
  chapter: string | null
  verse_range: string | null
  text: string
  confidence_baseline: number
  tier: number
  school: string | null
}

export interface ClassicalTextSearchOutput {
  results: ClassicalTextSearchResult[]
  total: number
  query_used: string
}

export async function classical_text_search(
  input: ClassicalTextSearchInput
): Promise<ClassicalTextSearchOutput> {
  return { results: [], total: 0, query_used: input.query }
}
