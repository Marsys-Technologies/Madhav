/**
 * MARSYS-JIS Stream C — Retrieval layer shared types
 * schema_version: 1.0
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
  audience_tier: 'super_admin' | 'acharya_reviewer' | 'client' | 'public_redacted'
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
  /** Filter applied to vector_search retrieval — narrows by doc_type/layer/varga/section_id. */
  vector_search_filter?: {
    doc_type?: string[]
    layer?: string
    /** Filter to chunks whose metadata->>'varga' matches this varga code (e.g. "D9", "D10", "CSI"). */
    varga?: string
    /** Filter to chunks whose metadata->>'section_id' starts with this prefix (e.g. "§3.5"). */
    section_id_prefix?: string
  }
  bundle_directives?: {
    floor_overrides?: string[]
    conditional_overrides?: object
  }
  adjudicator_model_id?: string
  router_confidence?: number
  router_model_id?: string
  // Temporal extension flags (W5-R1)
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
  cache_key?: string  // omit when no cache is in play; schema treats as optional string
  latency_ms: number
  result_hash: string // 'sha256:' + hex
  schema_version: '1.0'
}

export interface MsrSqlInput {
  /** Filter to specific signal_type values (e.g. ['yoga', 'aspect']). */
  signal_type?: string[]
  /**
   * Filter to specific temporal_activation values.
   * Accepts a single value ('natal' | 'transit' | 'dasha') or an array of
   * values (e.g. ['natal-permanent']) for backward-compatible multi-value use.
   */
  temporal_activation?: 'natal' | 'transit' | 'dasha' | string | string[]
  /**
   * Filter to specific valence values.
   * Accepts a single value ('positive' | 'negative' | 'mixed') or an array of
   * values (e.g. ['benefic', 'mixed']) for backward-compatible multi-value use.
   */
  valence?: 'positive' | 'negative' | 'mixed' | string | string[]
  /** Filter to signals whose entities_involved array contains any of these entity IDs. */
  entities_involved_any?: string[]
  /**
   * Filter to signals activated by the given dasha lord(s).
   * Values are dasha lord names (e.g. ["Ketu", "Mercury"]); the retriever
   * prepends "DSH.MD." to convert to entity IDs and merges with entities_involved_any.
   */
  dasha_activation?: string[]
  /**
   * Filter to signals where dasha_activations JSON array contains this planet lord.
   * Single-value scalar convenience — e.g. "Saturn", "Ketu".
   * Merged with dasha_activation[] if both are provided.
   */
  dasha_lord?: string
}

export interface RetrievalTool {
  name: string
  version: string
  description?: string
  retrieve(plan: QueryPlan, params?: Record<string, unknown>): Promise<ToolBundle>
  secondary?: boolean  // extension — mark as secondary in registry
}
