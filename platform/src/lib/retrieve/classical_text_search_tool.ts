/**
 * RetrievalTool wrapper for classical_text_search (Tool 25).
 * Wraps the L8 classical corpus vector search as a pipeline-compatible RetrievalTool.
 * M8-G-S1 (2026-05-14).
 */

import crypto from 'crypto'
import { classical_text_search } from '@/lib/tools/classical_text_search'
import type { QueryPlan, ToolBundle, ToolBundleResult, RetrievalTool } from './types'

const TOOL_NAME = 'classical_text_search'
const TOOL_VERSION = '1.0.0'

async function retrieve(plan: QueryPlan, params?: Record<string, unknown>): Promise<ToolBundle> {
  const start = Date.now()

  const searchQuery = (params?.query as string | undefined) ?? plan.query_text
  const schools = params?.schools as string[] | undefined
  const tier_max = params?.tier_max as number | undefined
  const limit = (params?.limit as number | undefined) ?? 5

  const output = await classical_text_search({ query: searchQuery, schools, tier_max, limit })

  const results: ToolBundleResult[] = output.results.map(r => ({
    content: JSON.stringify({
      text_key: r.text_key,
      title: r.title,
      author: r.author,
      tradition: r.tradition,
      chapter: r.chapter,
      verse_range: r.verse_range,
      content: r.content,
      confidence_baseline: r.confidence_baseline,
      similarity: r.similarity,
    }),
    source_canonical_id: 'CLASSICAL_CORPUS',
    source_version: '1.0',
    confidence: r.confidence_baseline,
    significance: r.similarity,
  }))

  const result_hash =
    'sha256:' +
    crypto
      .createHash('sha256')
      .update(JSON.stringify(results.map(r => r.content.slice(0, 80)).sort()))
      .digest('hex')

  const bundle: ToolBundle = {
    tool_bundle_id: crypto.randomUUID(),
    tool_name: TOOL_NAME,
    tool_version: TOOL_VERSION,
    invocation_params: { query: searchQuery, schools, tier_max, limit },
    results,
    served_from_cache: false,
    latency_ms: Date.now() - start,
    result_hash,
    schema_version: '1.0',
  }

  return bundle
}

export const tool: RetrievalTool = {
  name: TOOL_NAME,
  version: TOOL_VERSION,
  description:
    'Semantic search over classical Jyotish text corpus (BPHS, Phaladeepika, Saravali, etc.) ' +
    'using pgvector cosine similarity. Returns top-K chunks with chapter, verse_range, and ' +
    'confidence baseline. Use when the query requires classical textual authority, source verse ' +
    'citation, or cross-tradition validation of astrological principles.',
  retrieve,
}
