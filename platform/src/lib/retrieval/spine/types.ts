/** spine/types.ts — shared shapes for the spine bundle mechanism. */

export interface SpineSignalEntry {
  signal_id: string
  signal_headline_text: string | null
  signal_summary_text: string | null
  computed_salience: number | null
  domains_affected_array: string[] | null
  valence: string | null
  /** kala_activation window_families for this signal (from query_temporal_activation). */
  activation_windows: Array<Record<string, unknown>>
  /** phala_anchors rows whose signal_id matches this signal. */
  phala_anchors: Array<Record<string, unknown>>
}

export interface SpineCalibration {
  /** mimamsa_calibration verdict distribution (chart-level; not domain-scoped upstream). */
  verdict_distribution: Array<Record<string, unknown>>
  /** mimamsa_reliability rows (chart-level). */
  reliability: Array<Record<string, unknown>>
  /**
   * mimamsa_multipliers rows in scope for this bundle's domain: rows whose `domain`
   * matches, PLUS rows whose `domain` is NULL (global scope — they apply to every
   * domain). Same reading of the NULL as query_calibration.ts's deliberate
   * no-filter stance; see compute_spine_bundle.ts for the full note.
   */
  multipliers: Array<Record<string, unknown>>
  /** Total mimamsa_multipliers rows for this chart, BEFORE domain scoping (measured). */
  multipliers_total: number
  /** How many of those rows carry a non-NULL `domain` label (measured coverage). */
  multipliers_with_domain: number
  /** Honest reason `multipliers` is empty; null when it is populated (§N.6 item 3). */
  multipliers_empty_reason: string | null
  qa_fail_count: number
}

/**
 * The deterministic content of one spine bundle — a pure function of the four
 * underlying tables' current rows for (chart_id, ayanamsha_id, domain). Contains
 * NO wall-clock/request-scoped fields (no computed_at, no request_id) so that two
 * calls against identical underlying data produce a byte-identical JSON.stringify.
 */
export interface SpineBundleContent {
  chart_id: string
  ayanamsha_id: string
  domain: string
  top_k: number
  signal_count: number
  signals: SpineSignalEntry[]
  calibration: SpineCalibration
  empty_reason: string | null
  provenance: {
    tables: string[]
    composed_from_capabilities: string[]
  }
}
