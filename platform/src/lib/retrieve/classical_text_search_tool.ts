/**
 * classical_text_search_tool.ts — RetrievalTool wrapper for classical_text_search
 *
 * Wraps the Tool 25 implementation (src/lib/tools/classical_text_search.ts)
 * as a RetrievalTool conforming to the unified retrieve interface.
 *
 * M8/Brahmagyan delta build 2026-06-03
 */

import { createHash } from 'crypto'
import type { RetrievalTool, ToolBundle, ToolBundleResult, QueryPlan } from './types'
import { classical_text_search } from '@/lib/tools/classical_text_search'

function sha256(data: string): string {
  return 'sha256:' + createHash('sha256').update(data).digest('hex')
}

export const tool: RetrievalTool = {
  name: 'classical_text_search',
  version: '1.0',
  description: 'Semantic search over classical Jyotish corpus (BPHS, Jaimini, KP, Tajaka).',

  async retrieve(
    _plan: QueryPlan,
    params: Record<string, unknown> = {}
  ): Promise<ToolBundle> {
    const startMs = Date.now()

    const query = typeof params.query === 'string' ? params.query : ''
    const schools = Array.isArray(params.schools) ? (params.schools as string[]) : undefined
    const tier_max = typeof params.tier_max === 'number' ? params.tier_max : undefined
    const limit = typeof params.limit === 'number' ? params.limit : undefined

    const output = await classical_text_search({ query, schools, tier_max, limit })

    const results: ToolBundleResult[] = output.results.map(r => ({
      content: JSON.stringify({
        chunk_id: r.chunk_id,
        text_key: r.text_key,
        chapter: r.chapter,
        verse_range: r.verse_range,
        text: r.text,
        confidence_baseline: r.confidence_baseline,
        tier: r.tier,
        school: r.school,
      }),
      confidence: r.confidence_baseline,
    }))

    const resultJson = JSON.stringify(results)

    return {
      tool_bundle_id: crypto.randomUUID(),
      tool_name: 'classical_text_search',
      tool_version: '1.0',
      invocation_params: { query, schools, tier_max, limit },
      results,
      served_from_cache: false,
      latency_ms: Date.now() - startMs,
      result_hash: sha256(resultJson),
      schema_version: '1.0',
    }
  },
}
