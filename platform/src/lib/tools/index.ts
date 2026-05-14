/**
 * Classical tools registry — M8 additions (tools 25 + 26).
 * Tools 1-24 are the structured query tools registered in build-tools.ts
 * and the pipeline's tool_calls registry.
 *
 * Tool 25: classical_text_search
 * Tool 26: classical_attribution_lookup
 */

export {
  classical_text_search,
  type ClassicalTextSearchInput,
  type ClassicalTextSearchOutput,
  type ClassicalTextSearchResult,
} from './classical_text_search'

export {
  classical_attribution_lookup,
  type ClassicalAttributionLookupInput,
  type ClassicalAttributionLookupOutput,
  type ClassicalAttributionRecord,
} from './classical_attribution_lookup'

export const CLASSICAL_TOOL_REGISTRY = [
  {
    tool_number: 25,
    tool_name: 'classical_text_search',
    description: 'Semantic search over classical Jyotish text corpus using pgvector cosine similarity. Returns top-K chunks from Tier 1/2/3 texts with chapter, verse_range, and confidence baseline.',
    layer: 'L8',
    status: 'STUB_M8A', // → ACTIVE after M8-E-S1
  },
  {
    tool_number: 26,
    tool_name: 'classical_attribution_lookup',
    description: 'Structured lookup of MSR signal attributions in classical_attributions JOIN classical_chunks JOIN classical_texts. Returns all attributions grouped by text for given signal IDs.',
    layer: 'L8',
    status: 'STUB_M8A', // → ACTIVE after M8-E-S1
  },
] as const
