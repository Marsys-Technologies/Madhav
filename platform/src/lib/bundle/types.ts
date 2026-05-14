/**
 * Bundle Composer — shared type definitions
 * Stream B: Rule Composer (deterministic; no LLM calls)
 */

// ── QueryPlan ────────────────────────────────────────────────────────────────

export type QueryClass =
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

export type AudienceTier = 'super_admin' | 'acharya_reviewer' | 'client' | 'public_redacted'

export type HistoryMode = 'synthesized' | 'research'

export type OutputShape =
  | 'single_answer'
  | 'three_interpretation'
  | 'time_indexed_prediction'
  | 'structured_data'

export interface QueryPlan {
  query_plan_id: string
  query_text: string
  query_class: QueryClass
  domains: string[]
  forward_looking: boolean
  audience_tier: AudienceTier
  tools_authorized: string[]
  history_mode: HistoryMode
  panel_mode: boolean
  expected_output_shape: OutputShape
  manifest_fingerprint: string
  schema_version: '1.0'
  planets?: string[]
  houses?: number[]
  dasha_context_required?: boolean
  graph_seed_hints?: string[]
  graph_traversal_depth?: number
  bundle_directives?: {
    floor_overrides?: string[]
    conditional_overrides?: object
  }
  time_window?: { start: string; end: string }
  adjudicator_model_id?: string
  router_confidence?: number
  router_model_id?: string
}

// ── Manifest / Asset ─────────────────────────────────────────────────────────

export interface AssetEntry {
  canonical_id: string
  path: string
  version: string
  status: string
  layer: string
  expose_to_chat: boolean
  representations: string[]
  interface_version: string
  fingerprint: string
  native_id: string
  // Fields merged from overrides
  preferred_for?: string[]
  cost_weight?: number
  always_required?: boolean
  tier?: number // 1 = Tier-1, computed during merge
  // BHISMA §4.9 / GAP.A.6 — populated for high-cost assets so the budget
  // enforcer in rule_composer.ts can drop low-priority entries when context
  // is tight. Optional because not every manifest entry has been measured;
  // a missing value is treated as 0 (the same as before this field existed).
  token_count?: number
}

export interface RawManifest {
  generated_at?: string
  generator_version?: string
  entry_count: number
  fingerprint: string
  entries: AssetEntry[]
}

export interface OverrideEntry {
  path_pattern?: string
  preferred_for?: string[]
  cost_weight?: number
  always_required?: boolean
}

export interface ManifestData {
  fingerprint: string
  entries: AssetEntry[]
  /** Fast lookup by canonical_id */
  byId: Map<string, AssetEntry>
}

// ── Bundle ───────────────────────────────────────────────────────────────────

export type BundleEntryRole =
  | 'floor'
  | 'interpretive'
  | 'predictive'
  | 'discovery'
  | 'holistic'
  | 'remedial'
  | 'domain_report'
  | 'temporal_engine'
export type BundleEntrySource = 'rule_composer' | 'bundle_augmenter' | 'planner'

export interface BundleEntry {
  canonical_id: string
  version: string
  content_hash: string
  token_count: number
  role: BundleEntryRole
  source: BundleEntrySource
}

export interface Bundle {
  bundle_id: string
  query_plan_reference: string
  manifest_fingerprint: string
  mandatory_context: BundleEntry[]
  total_tokens: number
  bundle_hash: string
  schema_version: '1.0'
  retrieved_context?: RetrievedContextEntry[]
}

export interface RetrievedContextEntry {
  tool_name: string
  tool_invocation_params: object
  tool_bundle_id: string
  token_count: number
  validator_votes?: object
}
