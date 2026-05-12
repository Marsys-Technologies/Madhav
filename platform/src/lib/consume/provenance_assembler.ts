/**
 * provenance_assembler.ts — Gate III.
 *
 * Aggregates pipeline observations into a `ProvenanceEvent` payload suitable
 * for attachment to the UI message `finish` metadata. The route hands in raw
 * model/tool/cost data; this module translates internal asset IDs into
 * user-facing labels (via `domain_labels.ts`) and produces a clean,
 * UI-shaped object.
 */

import {
  ASSET_LABELS,
  formatTechnicalTag,
  labelFor,
} from '@/lib/jyotish/domain_labels'
import type {
  ProvenanceEvent,
  ProvenanceModel,
  ProvenanceAstrologicalSource,
  ProvenanceSourceItem,
  ProvenanceTechnicalTag,
} from '@/types/sse_events'

export interface ToolBundleLike {
  tool_name: string
  results: Array<{
    signal_id?: string
    source_canonical_id?: string
    content: string
    significance?: number
    confidence?: number
  }>
}

export interface ProvenanceInput {
  models: Array<{
    stage: string
    role?: string
    model_id: string
    latency_ms?: number
    tokens?: number
  }>
  toolResults: ToolBundleLike[]
  assetsUsed?: string[]
  totalLatencyMs?: number
  topVectorScore?: number
  cacheHit?: boolean
}

/**
 * Map internal asset / tool names to a small set of user-facing source
 * buckets. The bucketing collapses several internal tools into the same
 * astrological-domain label so the user sees "Astrological Signals" instead
 * of msr_sql + query_msr_aggregate + query_signal_state.
 */
const TOOL_TO_BUCKET: Record<string, string> = {
  msr_sql: 'MSR',
  query_msr_aggregate: 'MSR',
  query_signal_state: 'MSR',
  pattern_register: 'MSR',
  cluster_atlas: 'MSR',
  resonance_register: 'RM',
  contradiction_register: 'MSR',
  cgm_graph_walk: 'CGM',
  vector_search: 'FORENSIC',
  chart_facts_query: 'FORENSIC',
  divisional_query: 'FORENSIC',
  cross_varga_dignity_query: 'FORENSIC',
  kp_query: 'FORENSIC',
  manifest_query: 'FORENSIC',
  query_kp_ruling_planets: 'FORENSIC',
  query_varshaphala: 'FORENSIC',
  saham_query: 'FORENSIC',
  temporal: 'LEL',
  timeline_query: 'LEL',
  remedial_codex_query: 'RM',
  domain_report_query: 'CDLM',
}

function bucketFor(toolName: string): string {
  return TOOL_TO_BUCKET[toolName] ?? 'FORENSIC'
}

function itemLabelFor(signalId: string | undefined, sourceCanonicalId: string | undefined, toolName: string): string {
  const raw = signalId ?? sourceCanonicalId ?? toolName
  // For MSR signals (SIG.MSR.NNN), drop the prefix in the displayed label.
  if (/^SIG\.MSR\.\d+$/i.test(raw)) return raw.replace(/^SIG\.MSR\./i, 'Signal ')
  if (/^F\./i.test(raw) || /^FORENSIC\./i.test(raw)) return raw.replace(/^F(?:ORENSIC)?\./i, 'Chart fact ')
  return raw
}

const ROLE_BY_STAGE: Record<string, string> = {
  planner: 'Question reader',
  llm_planner: 'Question reader',
  classify: 'Question reader',
  retrieval: 'Source retriever',
  synthesis: 'Synthesizer',
  synthesize: 'Synthesizer',
  validator: 'Consistency checker',
  title: 'Title summarizer',
}

export function assembleProvenance(input: ProvenanceInput): ProvenanceEvent {
  const models: ProvenanceModel[] = input.models.map(m => ({
    stage: m.stage,
    role: m.role ?? ROLE_BY_STAGE[m.stage] ?? m.stage,
    model_id: m.model_id,
    latency_ms: m.latency_ms,
    tokens: m.tokens,
  }))

  // Bucket tool results by asset.
  const buckets = new Map<string, Map<string, ProvenanceSourceItem>>()
  for (const tb of input.toolResults) {
    const bucket = bucketFor(tb.tool_name)
    if (!buckets.has(bucket)) buckets.set(bucket, new Map())
    const itemsMap = buckets.get(bucket)!
    for (const r of tb.results) {
      const id = r.signal_id ?? r.source_canonical_id ?? `${tb.tool_name}:item-${itemsMap.size}`
      if (!itemsMap.has(id)) {
        itemsMap.set(id, {
          id,
          label: itemLabelFor(r.signal_id, r.source_canonical_id, tb.tool_name),
        })
      }
    }
  }

  // Ensure every asset_used appears even if no tool returned items.
  for (const asset of input.assetsUsed ?? []) {
    if (!buckets.has(asset)) buckets.set(asset, new Map())
  }

  const astrological: ProvenanceAstrologicalSource[] = []
  for (const [asset, itemsMap] of buckets) {
    astrological.push({
      asset,
      label: labelFor('asset', asset),
      items: Array.from(itemsMap.values()).slice(0, 50),
    })
  }
  // Stable ordering: most-items-first.
  astrological.sort((a, b) => b.items.length - a.items.length)

  // Technical tags.
  const technical: ProvenanceTechnicalTag[] = []
  if (typeof input.totalLatencyMs === 'number') {
    technical.push({
      kind: 'latency',
      label: 'Total time',
      value: formatTechnicalTag('latency', input.totalLatencyMs),
    })
  }
  if (typeof input.topVectorScore === 'number' && input.topVectorScore > 0) {
    technical.push({
      kind: 'vector_score',
      label: 'Top retrieval score',
      value: formatTechnicalTag('vector_score', input.topVectorScore),
    })
  }
  if (typeof input.cacheHit === 'boolean') {
    technical.push({
      kind: 'cache_hit',
      label: 'Retrieval cache',
      value: formatTechnicalTag('cache_hit', input.cacheHit ? 1 : 0),
    })
  }
  for (const m of models) {
    if (typeof m.latency_ms === 'number') {
      technical.push({
        kind: 'latency',
        label: `${m.role} (${m.model_id})`,
        value: formatTechnicalTag('latency', m.latency_ms),
      })
    }
    if (typeof m.tokens === 'number') {
      technical.push({
        kind: 'token_count',
        label: `${m.role} tokens`,
        value: formatTechnicalTag('token_count', m.tokens),
      })
    }
  }

  // Surface ASSET_LABELS map presence — for tests + audits.
  void ASSET_LABELS

  return {
    type: 'provenance',
    models,
    sources: { astrological, technical },
  }
}
