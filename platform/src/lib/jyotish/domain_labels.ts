/**
 * domain_labels.ts — Gate III foundation.
 *
 * User-facing translations for internal canonical assets, query classes,
 * and pipeline step names. NEVER leak internal IDs (MSR, FORENSIC, CGM,
 * UCN, CDLM, RM, LEL, pgvector, cosine, embedding) into the UI; route
 * every display through this map.
 */

export const ASSET_LABELS: Record<string, string> = {
  FORENSIC: 'Birth Chart',
  MSR: 'Astrological Signals',
  UCN: 'Cross-Domain Patterns',
  CDLM: 'Domain Linkages',
  RM: 'Remedies Matrix',
  CGM: 'Concept Graph',
  LEL: 'Life Events',
}

export type QueryClass =
  | 'factual'
  | 'interpretive'
  | 'predictive'
  | 'cross_domain'
  | 'discovery'
  | 'holistic'
  | 'remedial'
  | 'cross_native'

export const QUERY_CLASS_LABELS: Record<QueryClass, string> = {
  factual: 'Factual',
  interpretive: 'Interpretive',
  predictive: 'Predictive',
  cross_domain: 'Cross-Domain',
  discovery: 'Discovery',
  holistic: 'Holistic',
  remedial: 'Remedial',
  cross_native: 'Cross-Native',
}

/**
 * Pipeline step → astrological-domain narration. Used by LiveReasoningCard
 * during the pre-synthesis phase. Step names mirror the trace step_name
 * values emitted by route.ts and pipeline_planner.ts.
 */
export const PIPELINE_STEP_NARRATION: Record<string, string> = {
  // Planner / classification
  classify: 'Reading the question',
  llm_planner: 'Planning the approach',
  plan: 'Planning the approach',

  // Bundle + retrieval
  compose_bundle: 'Gathering classical sources',
  context_assembly: 'Assembling the context for synthesis',

  // Retrieval tools (canonical names from the manifest)
  vector_search: 'Searching classical sources',
  cgm_graph_walk: 'Following conceptual links across principles',
  msr_sql: 'Reviewing astrological signals',
  query_msr_aggregate: 'Reviewing astrological signal patterns',
  query_signal_state: 'Checking signal alignment',
  pattern_register: 'Consulting recurring patterns',
  resonance_register: 'Checking dasha and transit resonance',
  cluster_atlas: 'Identifying thematic clusters',
  contradiction_register: 'Surfacing classical contradictions',
  chart_facts_query: 'Looking up chart placements',
  divisional_query: 'Examining divisional charts',
  kp_query: 'Consulting KP system',
  manifest_query: 'Cross-referencing canonical artifacts',
  query_kp_ruling_planets: 'Consulting KP ruling planets',
  query_varshaphala: 'Reviewing annual chart',
  saham_query: 'Reviewing Sahams',
  temporal: 'Tracing the temporal arc',
  timeline_query: 'Tracing the timeline',
  remedial_codex_query: 'Consulting the remedies codex',
  domain_report_query: 'Reviewing the domain report',
  cross_varga_dignity_query: 'Cross-checking divisional dignity',

  // Synthesis + post
  synthesis: 'Reasoning through the question',
  synthesis_start: 'Reasoning through the question',
  validator: 'Checking the answer for consistency',
  audit: 'Recording the trace',
  citation_warn: 'Flagging citation coverage',
  citation_error: 'Citation gate blocked the answer',
}

export type TechnicalTagKind =
  | 'vector_score'
  | 'graph_depth'
  | 'latency'
  | 'token_count'
  | 'model_name'
  | 'cache_hit'
  | 'cost_usd'
  | 'finish_reason'

export function formatTechnicalTag(kind: TechnicalTagKind, value: number | string): string {
  switch (kind) {
    case 'vector_score':
      return `≈${Number(value).toFixed(2)} cosine`
    case 'graph_depth':
      return `depth ${value}`
    case 'latency':
      return typeof value === 'number'
        ? value >= 1000
          ? `${(value / 1000).toFixed(1)}s`
          : `${Math.round(value)}ms`
        : String(value)
    case 'token_count':
      return `${typeof value === 'number' ? value.toLocaleString() : value} tokens`
    case 'model_name':
      return String(value)
    case 'cache_hit':
      return value ? 'cache hit' : 'fresh'
    case 'cost_usd':
      return typeof value === 'number' ? `$${value.toFixed(4)}` : String(value)
    case 'finish_reason':
      return String(value)
  }
}

/** Banned tokens — any reasoning step / narration containing these is a leak. */
export const BANNED_INTERNAL_TOKENS: readonly string[] = [
  'MSR',
  'FORENSIC',
  'CGM',
  'UCN',
  'CDLM',
  'LEL',
  'pgvector',
  'cosine',
  'embedding',
  'chunk_id',
  'SIG.MSR',
] as const

/** Lightweight assertion helper — used in tests and dev guards. */
export function containsBannedToken(text: string): string | null {
  for (const tok of BANNED_INTERNAL_TOKENS) {
    if (text.includes(tok)) return tok
  }
  return null
}

type LookupCategory = 'asset' | 'class' | 'step'

let _missLogged = new Set<string>()
function logMiss(category: LookupCategory, key: string): void {
  const sig = `${category}:${key}`
  if (_missLogged.has(sig)) return
  _missLogged.add(sig)
  if (typeof console !== 'undefined' && process.env.NODE_ENV !== 'production') {
    console.warn(`[domain_labels] no translation for ${category}=${JSON.stringify(key)}; falling back`)
  }
}

export function labelFor(category: LookupCategory, key: string): string {
  if (!key) return key
  if (category === 'asset') {
    const v = ASSET_LABELS[key]
    if (v) return v
    logMiss(category, key)
    return key
  }
  if (category === 'class') {
    const v = QUERY_CLASS_LABELS[key as QueryClass]
    if (v) return v
    logMiss(category, key)
    return key
  }
  if (category === 'step') {
    const v = PIPELINE_STEP_NARRATION[key]
    if (v) return v
    logMiss(category, key)
    // Final fallback: titlecase the snake-case step name. Never internal-leak.
    return key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
  }
  return key
}

/** Test helper — reset miss-cache between test cases. */
export function __resetMissCacheForTests(): void {
  _missLogged = new Set()
}
