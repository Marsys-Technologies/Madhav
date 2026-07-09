/**
 * D6 Synergy Layer — Types
 * ========================
 * Types for the whole-corpus synergy orchestration.
 *
 * The synergy layer composes the umbrella + graph + grounding spine into
 * Whole-Chart-Read answers: convergence + contradiction surfacing across
 * domains/layers (CDLM + CGM), layered hydration (L2→L1→L0).
 *
 * Source: CLAUDECODE_BRIEF_RETRIEVAL_D6_D7_CHANNELS_v1_1.md §1
 */

// ── Query class ───────────────────────────────────────────────────────────────

export type SynergyQueryClass =
  | 'factual'
  | 'interpretive'
  | 'predictive'
  | 'cross_domain'
  | 'discovery'
  | 'holistic'
  | 'remedial'
  | 'classical_grounding'

// ── Step 1: UCD orientation digest ───────────────────────────────────────────

export interface UcdDigest {
  chart_id: string
  ayanamsha_id: string
  msr_signal_count: number
  yoga_count: number | null
  dosha_count: number | null
  avg_salience: number | null
  max_salience: number | null
  contradiction_count: number
  weakest_graha: string | null
  top_priority_class: string | null
  trap1_count: number | null
  top_signals: SignalRef[]
  convergence_domains: ConvergenceDomainRow[]
  /** Drill children declared by the umbrella */
  drill_children: string[]
}

export interface SignalRef {
  signal_id: string
  signal_type_id?: string
  signal_type_class?: string
  computed_salience?: number
  domains_affected_array?: string[]
  /** F1: reference — not restated content */
  emits_reference: true
}

export interface ConvergenceDomainRow {
  domain: string
  convergence_count: number
  convergence_score: number
  cross_tradition_count?: number
  salience_weighted_sum?: number
  contradiction_count?: number
}

// ── Step 2: Domain reading ────────────────────────────────────────────────────

export interface DomainReadingResult {
  domain: string
  chart_id: string
  ayanamsha_id: string
  /** CDLM cell for domain pair */
  cdlm_cells: CdlmCell[]
  /** Domain lens (bo_drishti) */
  question_lenses: QuestionLens[]
  /** Signal IDs in this domain — F1 references */
  signal_refs: SignalRef[]
  /** Multi-vantage perspectives: house, kāraka, varga */
  vantage_perspectives: VantagePerspective[]
}

export interface CdlmCell {
  source_domain: string
  target_domain: string
  link_type: string
  strength: number | null
  valence: string
  key_finding: string
}

export interface QuestionLens {
  lens_id: string
  lens_domain: string
  question_text: string | null
}

export interface VantagePerspective {
  vantage_type: 'house' | 'karaka' | 'varga'
  label: string
  signal_refs: SignalRef[]
}

// ── Step 3: Signal ranking ────────────────────────────────────────────────────

export interface SignalRankResult {
  chart_id: string
  ayanamsha_id: string
  /** Ranked by computed_salience DESC. signature_tier's degeneracy is re-derived live
   *  (E-2 freshness contract) — do not assume any historical distribution figure. */
  signals: RankedSignal[]
  total_available: number
  filters_applied: Record<string, unknown>
  /**
   * DEFECT-001 status, live-derived (E-2 freshness contract, R5.1 C2 item 1) — see
   * `platform/src/lib/retrieval/provenance/freshness_notes.ts`. `defect_001_note` is a
   * plain-text mirror of `defect_001.note` retained for callers of the prior wave's shape.
   * Never hardcode a historical orphan-rate figure here again.
   */
  defect_001_note: string
  defect_001?: import('../provenance/freshness_notes').FreshnessNote
}

export interface RankedSignal {
  signal_id: string
  signal_headline_text?: string
  signal_summary_text?: string
  computed_salience: number
  /** May be empty — orphan rate is re-derived live, see SignalRankResult.defect_001 */
  constituent_facts_array: string[]
  classical_sources_jsonb: unknown
  domains_affected_array: string[]
  lel_origin: boolean
  /** F1: reference */
  emits_reference: true
}

// ── Step 4: Graph traversal ───────────────────────────────────────────────────

export interface GraphTraversalResult {
  chart_id: string
  seed_signal_ids: string[]
  mode: 'neighbors' | 'paths' | 'cluster'
  depth: number
  nodes: GraphNode[]
  edges: GraphEdge[]
  /** Note: relationship_basis is 100% NULL in current data */
  relationship_basis_note: string
}

export interface GraphNode {
  node_id: string
  node_type: string
  label: string
  centrality?: number
  domain?: string
  msr_signal_id?: string
}

export interface GraphEdge {
  edge_id: string
  source_node_id: string
  target_node_id: string
  edge_type: string
  weight: number
  /** Will be null in current data — see relationship_basis_note */
  relationship_basis: string | null
}

// ── Step 5: Contradictions + discoveries ─────────────────────────────────────

export interface ContradictionResult {
  chart_id: string
  /** Currently 0 rows — graceful-empty */
  contradictions: ContradictionRow[]
  /** 1,505 rows, novelty-ranked */
  discoveries: DiscoveryRow[]
  graceful_empty_note?: string
}

export interface ContradictionRow {
  contradiction_id: string
  signal_a_id: string
  signal_b_id: string
  domain: string
  description: string | null
}

export interface DiscoveryRow {
  discovery_id: string
  novelty_score: number
  description: string | null
  domain: string | null
  signal_refs: string[]
}

// ── Step 6: Temporal enrichment ───────────────────────────────────────────────

export interface TemporalEnrichmentResult {
  chart_id: string
  query_class: SynergyQueryClass
  activations: TemporalActivation[]
  convergence_windows: TemporalConvergenceWindow[]
  life_arc_segments: LifeArcSegment[]
}

export interface TemporalActivation {
  activation_id: string
  period_start: string
  period_end: string
  dasha_lord: string | null
  strength_score: number | null
  domain: string | null
}

export interface TemporalConvergenceWindow {
  window_start: string
  window_end: string
  convergence_score: number
  indicator_count: number
  valence: 'favorable' | 'challenging' | 'mixed'
}

export interface LifeArcSegment {
  segment_id: string
  label: string
  start_date: string | null
  end_date: string | null
  domain: string | null
}

// ── Step 7: Quality scorecard ─────────────────────────────────────────────────

export interface QualityScorecardResult {
  chart_id: string
  scorecards: ScorecardRow[]
  /**
   * The stored unresolved_constituent_facts_count on the scorecard row may be stale
   * (computed pre-L1-rebuild). Re-derive DEFECT-001 live (E-2 freshness contract) via
   * `deriveDefect001Note` rather than restating any historical orphan-rate figure here.
   */
  defect_001_false_pass_warning: string
}

export interface ScorecardRow {
  scorecard_id: string
  dimension: string
  score: number
  notes: string | null
}

// ── Whole-Chart-Read result ───────────────────────────────────────────────────

/**
 * The unified output of the D6 synergy orchestration.
 * De-duplicated, cited, multi-vantage Whole-Chart-Read answer.
 *
 * Every claim traces: signal_id → fact_id (via constituent_facts_array)
 * → citation_id (via classical_sources_jsonb). DEFECT-001's orphan rate is
 * re-derived live per call (E-2 freshness contract) — see `signals.defect_001`.
 * Handle gracefully regardless of current rate (empty join = empty provenance).
 */
export interface WholeChartReadResult {
  chart_id: string
  query_class: SynergyQueryClass
  query_text?: string

  /** Step 1: Orientation digest */
  ucd_digest: UcdDigest

  /** Steps 2-3: Domain readings (one per top convergence domain) */
  domain_readings: DomainReadingResult[]

  /**
   * Step 3: De-duplicated signal ranking across all domains.
   * F1: de-duplication by signal_id across all tool results before synthesis.
   */
  signals: SignalRankResult

  /** Step 4: CGM graph traversal (seed = top signal_ids from UCD) */
  graph: GraphTraversalResult

  /** Step 5: Contradictions + discoveries */
  contradictions: ContradictionResult

  /** Step 6: Temporal enrichment (predictive/holistic queries only) */
  temporal?: TemporalEnrichmentResult

  /** Step 7: Quality scorecard (on request) */
  quality?: QualityScorecardResult

  /** Execution metadata */
  meta: WholeChartReadMeta
}

export interface WholeChartReadMeta {
  executed_at: string
  steps_executed: string[]
  signal_ids_deduped: number
  /** True if DEFECT-001 empty joins were encountered */
  defect_001_empty_joins_encountered: boolean
  lel_enabled: boolean
}
