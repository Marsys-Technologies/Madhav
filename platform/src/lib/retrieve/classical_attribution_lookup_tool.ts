/**
 * RetrievalTool wrapper for classical_attribution_lookup (Tool 26).
 * Wraps the L8 classical attribution lookup as a pipeline-compatible RetrievalTool.
 * M8-G-S1 (2026-05-14).
 */

import crypto from 'crypto'
import { classical_attribution_lookup } from '@/lib/tools/classical_attribution_lookup'
import type { QueryPlan, ToolBundle, ToolBundleResult, RetrievalTool } from './types'

const TOOL_NAME = 'classical_attribution_lookup'
const TOOL_VERSION = '1.0.0'

async function retrieve(plan: QueryPlan, params?: Record<string, unknown>): Promise<ToolBundle> {
  const start = Date.now()

  const signal_ids = (params?.signal_ids as string[] | undefined) ?? []
  const attribution_type = params?.attribution_type as
    | 'confirms' | 'contradicts' | 'partial' | 'extends' | 'silent' | undefined
  const confidence_tier = params?.confidence_tier as 'HIGH' | 'MEDIUM' | 'LOW' | undefined

  const output = await classical_attribution_lookup({
    signal_ids,
    attribution_type,
    confidence_tier,
  })

  const results: ToolBundleResult[] = output.attributions.map(a => ({
    content: JSON.stringify({
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
    source_canonical_id: 'CLASSICAL_ATTRIBUTIONS',
    source_version: '1.0',
    signal_id: a.msr_signal_id,
    confidence: a.confidence,
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
    invocation_params: { signal_ids, attribution_type, confidence_tier },
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
    'Structured lookup of MSR signal attributions in classical Jyotish texts. For given MSR ' +
    'signal IDs, returns which classical texts confirm/contradict/extend each signal, with ' +
    'chapter, verse_range, confidence tier, and translation cross-check status. Use when the ' +
    'query requires classical source authority for specific MSR signals or attribution evidence.',
  retrieve,
}
