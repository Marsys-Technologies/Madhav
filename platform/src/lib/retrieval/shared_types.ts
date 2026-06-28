/**
 * shared_types.ts — Shared retrieval types (D7 Step 4: migrated from lib/retrieve/types.ts)
 * ===========================================================================================
 * Canonical home for ToolBundle, ToolBundleResult, QueryPlan, RetrievalTool, MsrSqlInput
 * after lib/retrieve/ was retired in D7 Step 4 (2026-06-28).
 *
 * audience_tier STRIPPED from QueryPlan per DG1 ruling — all retrieval is universal-access.
 * The field is removed here; callers that need a tier signal must use serve-time auth.
 *
 * Import path: '@/lib/retrieval/shared_types'
 */

export interface QueryPlan {
  query_plan_id: string
  query_text: string
  query_class:
    | 'factual'
    | 'interpretive'
    | 'predictive'
    | 'cross_domain'
    | 'discovery'
    | 'holistic'
    | 'remedial'
    | 'cross_native'
    | 'classical_grounding'
    | 'multi_school_triangulation'
  domains: string[]
  forward_looking: boolean
  /** audience_tier removed (DG1 ruling — registry is universal-access; no tier gating in retrieval layer) */
  tools_authorized: string[]
  history_mode: 'synthesized' | 'research'
  panel_mode: boolean
  expected_output_shape:
    | 'single_answer'
    | 'three_interpretation'
    | 'time_indexed_prediction'
    | 'structured_data'
  manifest_fingerprint: string
  schema_version: '1.0'
  planets?: string[]
  houses?: number[]
  dasha_context_required?: boolean
  graph_seed_hints?: string[]
  graph_traversal_depth?: number
  /** Filter applied to vector_search retrieval */
  vector_search_filter?: {
    doc_type?: string[]
    layer?: string
    varga?: string
    section_id_prefix?: string
  }
  bundle_directives?: {
    floor_overrides?: string[]
    conditional_overrides?: object
  }
  adjudicator_model_id?: string
  router_confidence?: number
  router_model_id?: string
  time_window?: { start: string; end: string }
  sade_sati_query?: boolean
  eclipse_query?: boolean
  retrograde_query?: boolean
  retrograde_planet?: string
}

export interface ToolBundleResult {
  content: string
  source_canonical_id?: string
  source_version?: string
  confidence?: number
  significance?: number
  signal_id?: string
}

export interface ToolBundle {
  tool_bundle_id: string // uuid
  tool_name: string
  tool_version: string
  invocation_params: object
  results: ToolBundleResult[]
  served_from_cache: boolean
  cache_key?: string
  latency_ms: number
  result_hash: string // 'sha256:' + hex
  schema_version: '1.0'
}

export interface MsrSqlInput {
  signal_type?: string[]
  temporal_activation?: 'natal' | 'transit' | 'dasha' | string | string[]
  valence?: 'positive' | 'negative' | 'mixed' | string | string[]
  entities_involved_any?: string[]
  dasha_activation?: string[]
  dasha_lord?: string
}

export interface RetrievalTool {
  name: string
  version: string
  description?: string
  retrieve(plan: QueryPlan, params?: Record<string, unknown>): Promise<ToolBundle>
  secondary?: boolean
}
