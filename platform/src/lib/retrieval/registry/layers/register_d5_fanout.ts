/**
 * D5 Fan-Out — Capability Registration (per-wave file)
 * ======================================================
 * GATE A compliance: this is the per-wave registration file for D5.
 * It does NOT edit registry/index.ts or registry/types.ts.
 *
 * D5 registers per-asset capabilities for L2 (Bodha), L3 (Kāla),
 * L4 (Phala), and L5 (Mīmāṃsā) layers.
 *
 * Capabilities registered by D5 wave:
 *
 * L2 Bodha (5 new tools, extending the 2 existing from D4):
 *   marsys://tool/L2/query_domain_reading
 *   marsys://tool/L2/query_signals
 *   marsys://tool/L2/query_contradictions
 *   marsys://tool/L2/query_remedies
 *   marsys://tool/L2/query_quality_scorecard
 *   (Already registered by L2 index: query_ucd, traverse_chart_graph)
 *
 * L3 Kāla (11 new tools):
 *   marsys://tool/L3/query_temporal_activation   (data)
 *   marsys://tool/L3/query_convergence_windows   (data)
 *   marsys://tool/L3/query_life_arc              (data)
 *   marsys://tool/L3/query_projections           (data)
 *   marsys://tool/L3/query_obstruction_periods   (data, STUBBED-PENDING-DATA)
 *   marsys://tool/L3/query_temporal_view         (data, STUBBED-PENDING-DATA)
 *   marsys://tool/L3/call_transit_search         (service)
 *   marsys://tool/L3/call_ephemeris_at_t         (service)
 *   marsys://tool/L3/call_dasha_eligibility      (service)
 *   marsys://tool/L3/call_muhurta_score          (service)
 *   marsys://tool/L3/call_priority_ranking       (service)
 *
 * L4 Phala (9 new tools):
 *   marsys://tool/L4/query_predictive_anchors
 *   marsys://tool/L4/query_domain_result
 *   marsys://tool/L4/query_auspicious_windows
 *   marsys://tool/L4/query_spillover_cascades
 *   marsys://tool/L4/query_falsifiers
 *   marsys://tool/L4/query_anomaly_flags
 *   marsys://tool/L4/query_remedy_program
 *   marsys://tool/L4/query_cleansed_anchors
 *   marsys://tool/L4/query_rectification
 *
 * L5 Mīmāṃsā (3 new tools, extending the 2 existing):
 *   marsys://tool/L5/query_predictions
 *   marsys://tool/L5/query_signal_families
 *   marsys://tool/L5/query_manifestation_grammar
 *
 * Total D5 new capabilities: 28
 * Total L2+L3+L4+L5 capabilities after D5: 35
 *
 * Usage: import this file at application startup after registry initialization.
 */

/**
 * Register D5 capabilities at runtime startup.
 * Lazily imports the layer indexes (side effects happen on first call).
 * Call at application startup after registry is initialized.
 */
export async function registerD5FanoutCapabilities(): Promise<void> {
  // Dynamic imports avoid pulling @/lib/db/client into test environments
  // that only need the URI roster (D5_CAPABILITY_URIS).
  await import('./L2_bodha/index')
  await import('./L3_kala/index')
  await import('./L4_phala/index')
  await import('./L5_mimamsa/index')
}

/**
 * D5 capability URI roster (for Gate C reverse-citation checks and roster smoke tests).
 */
export const D5_CAPABILITY_URIS = [
  // L2 Bodha
  'marsys://tool/L2/query_domain_reading',
  'marsys://tool/L2/query_signals',
  'marsys://tool/L2/query_contradictions',
  'marsys://tool/L2/query_remedies',
  'marsys://tool/L2/query_quality_scorecard',
  // L3 Kāla — data
  'marsys://tool/L3/query_temporal_activation',
  'marsys://tool/L3/query_convergence_windows',
  'marsys://tool/L3/query_life_arc',
  'marsys://tool/L3/query_projections',
  'marsys://tool/L3/query_obstruction_periods',
  'marsys://tool/L3/query_temporal_view',
  // L3 Kāla — service wrappers
  'marsys://tool/L3/call_transit_search',
  'marsys://tool/L3/call_ephemeris_at_t',
  'marsys://tool/L3/call_dasha_eligibility',
  'marsys://tool/L3/call_muhurta_score',
  'marsys://tool/L3/call_priority_ranking',
  // L4 Phala
  'marsys://tool/L4/query_predictive_anchors',
  'marsys://tool/L4/query_domain_result',
  'marsys://tool/L4/query_auspicious_windows',
  'marsys://tool/L4/query_spillover_cascades',
  'marsys://tool/L4/query_falsifiers',
  'marsys://tool/L4/query_anomaly_flags',
  'marsys://tool/L4/query_remedy_program',
  'marsys://tool/L4/query_cleansed_anchors',
  'marsys://tool/L4/query_rectification',
  // L5 Mīmāṃsā
  'marsys://tool/L5/query_predictions',
  'marsys://tool/L5/query_signal_families',
  'marsys://tool/L5/query_manifestation_grammar',
] as const
