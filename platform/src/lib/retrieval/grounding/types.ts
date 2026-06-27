/**
 * D3 Grounding Spine — Type Definitions
 * ========================================
 * Types for the grounding layer that resolves retrieved L2 signals back to L1 facts.
 *
 * Design principles enforced here:
 *   - §N.5 (L1 authority): signals REFERENCE fact_ids; they never restate L1 values.
 *   - F3 (layer-resolution-DOWN): grounded results carry both signal refs and L1 citations.
 *   - Principle #3 (cite-don't-regenerate): every numeric claim resolves via the resolver,
 *     not via LLM recomputation.
 *   - Principle #2 (empty-on-missing): missing data returns EMPTY/ERROR, never fabricated.
 *   - chart-agnostic (#14): chart_id is always required; no native defaults.
 */

// ── Primitive identity types ──────────────────────────────────────────────────

/** UUID string identifying a bodha_msr_signals row */
export type SignalId = string

/** Text key identifying a chart_facts row (hex string like "74c69ff0acb926aa") */
export type FactId = string

/** UUID string identifying a chart */
export type ChartId = string

/** Ayanamsha identifier (e.g. 'LAHIRI', 'KRISHNAMURTI') */
export type AyanamshaId = string

// ── L1 citation (the atom of grounding) ─────────────────────────────────────

/**
 * A single L1 fact row, returned by the grounding spine.
 * Values are copied from chart_facts — the spine is the ONLY place that reads
 * these values; callers consume the GroundedResult and do not re-derive them.
 */
export interface L1Fact {
  /** The unique fact identifier (text key, e.g. "74c69ff0acb926aa") */
  fact_id: FactId
  /** chart this fact belongs to — always present, enforces chart isolation */
  chart_id: ChartId
  /** Ayanamsha under which this fact was computed */
  ayanamsha_id: AyanamshaId
  /** Semantic category (e.g. 'graha_position', 'yoga_dosha', 'dignity') */
  fact_category: string
  /** Subject identifier within the category (e.g. 'SUN', 'MOON') */
  fact_subject: string
  /** Specific key within the category+subject (e.g. 'longitude_deg', 'rashi') */
  fact_key: string
  /** Text value (null if numeric or JSON) */
  fact_value_text: string | null
  /** Numeric value (null if text or JSON) */
  fact_value_num: number | null
  /** JSON value (null if text or numeric) */
  fact_value_jsonb: Record<string, unknown> | null
  /** Units for numeric values (e.g. 'deg', 'rpm') */
  unit: string | null
  /** Machine-readable citation reference */
  citation_ref: string
  /** Human-readable citation string */
  citation_human: string
  /** How this fact was computed (e.g. 'swisseph/pyjhora') */
  source_calculation: string
  /** Verification pass status */
  verification_pass_status: string
}

// ── Governed metric vocabulary ────────────────────────────────────────────────

/**
 * The governed vocabulary of numeric metrics the grounding spine resolves.
 * An LLM may only request metrics from this set — any out-of-vocabulary
 * request returns a GroundingError with error_code OUT_OF_VOCAB.
 *
 * Principle #3 / §N.5: the LLM selects from this vocabulary; the resolver
 * returns the deterministic value. The LLM never recomputes these numbers.
 */
export type GovernedMetric =
  | 'computed_salience'         // bodha_msr_signals.computed_salience
  | 'dignity_score'             // bodha_msr_signals.dignity_score
  | 'shadbala_norm'             // bodha_msr_signals.shadbala_norm
  | 'deterministic_strength'    // bodha_msr_signals.deterministic_strength
  | 'orb_tightness'             // bodha_msr_signals.orb_tightness
  | 'top_k_salience_rank'       // bodha_msr_signals.top_k_salience_rank
  | 'verification_certainty'    // bodha_msr_signals.verification_certainty
  | 'house_weight_multiplier'   // bodha_msr_signals.house_weight_multiplier
  | 'ashtakavarga_support_multiplier' // bodha_msr_signals.ashtakavarga_support_multiplier
  | 'vargottama_amplification'  // bodha_msr_signals.vargottama_amplification
  | 'argala_modifier'           // bodha_msr_signals.argala_modifier
  | 'neechabhanga_modifier'     // bodha_msr_signals.neechabhanga_modifier
  | 'cross_ayanamsha_consistency_score' // bodha_msr_signals.cross_ayanamsha_consistency_score
  | 'fact_value_num'            // chart_facts.fact_value_num (for a specific fact_id)

/**
 * The set of all valid governed metrics (for runtime membership checks).
 */
export const GOVERNED_METRICS: ReadonlySet<GovernedMetric> = new Set<GovernedMetric>([
  'computed_salience',
  'dignity_score',
  'shadbala_norm',
  'deterministic_strength',
  'orb_tightness',
  'top_k_salience_rank',
  'verification_certainty',
  'house_weight_multiplier',
  'ashtakavarga_support_multiplier',
  'vargottama_amplification',
  'argala_modifier',
  'neechabhanga_modifier',
  'cross_ayanamsha_consistency_score',
  'fact_value_num',
])

/**
 * A resolved numeric metric value.
 * The resolver returned this — the caller must not re-derive it.
 */
export interface ResolvedMetric {
  /** The metric that was requested */
  metric: GovernedMetric
  /** The resolved numeric value (null means the column was NULL in the DB) */
  value: number | null
  /** Source identifier for the resolved value */
  source_id: SignalId | FactId
  /** Table from which this value was read */
  source_table: 'bodha_msr_signals' | 'chart_facts'
  /** Human-readable citation for the metric value */
  citation: string
}

// ── Grounded result shapes ───────────────────────────────────────────────────

/**
 * A signal with its L1 facts resolved.
 * This is the core output type of the grounding spine.
 *
 * The spine does NOT restate fact values in the signal summary —
 * it bundles the L1 facts as resolved_facts. Callers read values from there.
 */
export interface GroundedSignal {
  /** Signal identifier — the primary reference */
  signal_id: SignalId
  /** chart scope — always present; spine is chart-scoped */
  chart_id: ChartId
  /** Ayanamsha context for this signal */
  ayanamsha_id: AyanamshaId
  /** Signal type identifier */
  signal_type_id: string
  /** Signal class (yoga, dosha, karaka_alignment, etc.) */
  signal_type_class: string
  /** Human-readable signal summary — from DB, NOT regenerated by LLM */
  signal_summary_text: string | null
  /** Computed salience from the DB */
  computed_salience: number | null
  /** The L1 fact_ids this signal is built on (from constituent_facts_array) */
  constituent_fact_ids: FactId[]
  /** The resolved L1 facts (one per fact_id in constituent_fact_ids) */
  resolved_facts: L1Fact[]
  /** Which fact_ids from constituent_facts_array did NOT resolve in chart_facts */
  orphan_fact_ids: FactId[]
  /** L0 citation references from classical_sources_jsonb */
  l0_citation_refs: string[]
}

/**
 * The complete result of a grounding operation for a set of signals.
 * Always scoped to exactly one chart.
 */
export interface GroundedResult {
  /** chart scope for this result batch */
  chart_id: ChartId
  /** Ayanamsha used for this grounding run */
  ayanamsha_id: AyanamshaId
  /** Grounded signals (in the same order as signal_ids requested) */
  signals: GroundedSignal[]
  /** signal_ids that were not found in bodha_msr_signals */
  not_found_signal_ids: SignalId[]
  /** Whether any §N.5 violations were found (orphan fact_ids) */
  has_n5_violations: boolean
  /** Total number of orphan fact_id references across all signals */
  orphan_fact_count: number
  /** ISO timestamp of this grounding operation */
  grounded_at: string
}

// ── Error types ───────────────────────────────────────────────────────────────

/**
 * Error codes from the grounding spine.
 * Principle #2: missing data errors, never fabricated values.
 */
export type GroundingErrorCode =
  | 'MISSING_CHART_ID'        // chart_id not provided
  | 'EMPTY_SIGNAL_IDS'        // no signal_ids provided to resolve
  | 'SIGNAL_NOT_FOUND'        // signal_id not in bodha_msr_signals for this chart
  | 'FACT_NOT_FOUND'          // fact_id in constituent_facts_array not in chart_facts
  | 'N5_VIOLATION'            // §N.5: a signal's computed value disagrees with cited L1 fact
  | 'OUT_OF_VOCAB'            // requested metric not in GOVERNED_METRICS vocabulary
  | 'DB_ERROR'                // database query error
  | 'CHART_SCOPE_MISMATCH'    // signal's chart_id != requested chart_id

/**
 * A grounding error — always returned instead of fabricated data.
 */
export interface GroundingError {
  error_code: GroundingErrorCode
  message: string
  /** Which signal_id triggered this error (if applicable) */
  signal_id?: SignalId
  /** Which fact_id triggered this error (if applicable) */
  fact_id?: FactId
  /** The requested metric (for OUT_OF_VOCAB errors) */
  requested_metric?: string
}

/**
 * Result of a metric resolution request.
 * One of: resolved value, or grounding error.
 */
export type MetricResolutionResult =
  | { ok: true; metric: ResolvedMetric }
  | { ok: false; error: GroundingError }

/**
 * Result of a full signal grounding operation.
 * One of: grounded result, or grounding error.
 */
export type GroundingOperationResult =
  | { ok: true; result: GroundedResult }
  | { ok: false; error: GroundingError }
