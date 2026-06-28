/**
 * classical_attribution_lookup_tool.ts — RetrievalTool wrapper for classical_attribution_lookup
 *
 * Wraps the Tool 26 implementation (src/lib/tools/classical_attribution_lookup.ts)
 * as a RetrievalTool conforming to the unified retrieve interface.
 *
 * M8/Brahmagyan delta build 2026-06-03.
 * D7 Step 4 (2026-06-28): moved from lib/retrieve/ to lib/retrieval/tools/ on lib/retrieve retirement.
 */

import { createHash } from 'crypto'
import type { RetrievalTool, ToolBundle, ToolBundleResult, QueryPlan } from '@/lib/retrieval/shared_types'
import { classical_attribution_lookup } from '@/lib/tools/classical_attribution_lookup'

function sha256(data: string): string {
  return 'sha256:' + createHash('sha256').update(data).digest('hex')
}

export const tool: RetrievalTool = {
  name: 'classical_attribution_lookup',
  version: '1.0',
  description: 'MSR signal × classical text chunk attribution lookup by signal_id.',

  async retrieve(
    _plan: QueryPlan,
    params: Record<string, unknown> = {}
  ): Promise<ToolBundle> {
    const startMs = Date.now()

    const signal_ids = Array.isArray(params.signal_ids) ? (params.signal_ids as string[]) : []
    const attribution_type = typeof params.attribution_type === 'string'
      ? params.attribution_type as 'confirms' | 'contradicts' | 'partial' | 'extends' | 'silent'
      : undefined
    const confidence_tier = typeof params.confidence_tier === 'string'
      ? params.confidence_tier as 'HIGH' | 'MEDIUM' | 'LOW'
      : undefined

    const output = await classical_attribution_lookup({ signal_ids, attribution_type, confidence_tier })

    const results: ToolBundleResult[] = output.attributions.map(a => ({
      content: JSON.stringify({
        attribution_id: a.attribution_id,
        msr_signal_id: a.msr_signal_id,
        text_key: a.text_key,
        title: a.title,
        author: a.author,
        chapter: a.chapter,
        verse_range: a.verse_range,
        content: a.content,
        attribution_type: a.attribution_type,
        confidence: a.confidence,
        confidence_tier: a.confidence_tier,
        derivation_notes: a.derivation_notes,
        translation_cross_checked: a.translation_cross_checked,
      }),
      signal_id: a.msr_signal_id,
      confidence: a.confidence,
    }))

    const resultJson = JSON.stringify(results)

    return {
      tool_bundle_id: crypto.randomUUID(),
      tool_name: 'classical_attribution_lookup',
      tool_version: '1.0',
      invocation_params: { signal_ids, attribution_type, confidence_tier },
      results,
      served_from_cache: false,
      latency_ms: Date.now() - startMs,
      result_hash: sha256(resultJson),
      schema_version: '1.0',
    }
  },
}
