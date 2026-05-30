/**
 * catalog.ts — MCPT v3.2 Phase 4c (UDA-0-S3, updated UDA-2-S9): Tool description catalog for lint testing.
 *
 * Exports an array of { name, description } entries for all 57 registered MCP tools.
 * Used by test/tool_descriptions.test.ts to enforce the Phase 3 lint gate:
 *   - every description starts with a disambiguator sentence
 *   - every description contains "When to prefer:"
 *   - every description is ≤ 1200 characters
 */

// Tier 1: super-endpoint
import { CHART_SUMMARY_DESCRIPTION } from './chart_summary.js'

// Tier 2: composite bundles
import { HOLISTIC_BUNDLE_DESCRIPTION } from './holistic_bundle_tool.js'
import { MULTI_SCHOOL_BUNDLE_DESCRIPTION } from './multi_school_bundle_tool.js'

// Tier 3: surgical primitives
import { QUERY_CHART_FACTS_DESCRIPTION } from './query_chart_facts.js'
import { QUERY_SIGNALS_DESCRIPTION } from './query_signals.js'
import { QUERY_DASHA_PERIODS_DESCRIPTION } from './query_dasha_periods.js'
import { QUERY_PANCHANGA_DESCRIPTION } from './query_panchanga.js'
import { QUERY_EPHEMERIS_DESCRIPTION } from './query_ephemeris.js'
import { QUERY_TRANSIT_EVENT_DESCRIPTION } from './query_transit_event.js'
import { LEL_QUERY_DESCRIPTION } from './lel_query.js'
import { VECTOR_SEARCH_DESCRIPTION } from './vector_search.js'
import { GET_CGM_SUBGRAPH_DESCRIPTION } from './get_cgm_subgraph.js'
import { CROSS_SCHOOL_LOOKUP_DESCRIPTION } from './cross_school_lookup.js'
import { MUHURTA_FINDER_DESCRIPTION } from './muhurta_finder.js'
import { TARA_BALAM_DESCRIPTION } from './tara_balam_for_native.js'
import { CHANDRA_BALAM_DESCRIPTION } from './chandra_balam_for_native.js'
import { QUERY_TRANSITS_OVER_NATAL_DESCRIPTION } from './query_transits_over_natal.js'
import { QUERY_YOGAS_ACTIVE_NOW_DESCRIPTION } from './query_yogas_active_now.js'
import { INTERPRET_CURRENT_DASHA_DESCRIPTION } from './interpret_current_dasha.js'
import { LIST_CANONICAL_ARTIFACT_VERSIONS_DESCRIPTION } from './list_canonical_artifact_versions.js'
import { QUERY_JAIMINI_CHARA_DASHA_DESCRIPTION } from './query_jaimini_chara_dasha.js'
import { QUERY_PLANETARY_PERIOD_PREDICTIONS_DESCRIPTION } from './query_planetary_period_predictions.js'
import { QUERY_ECLIPSE_TRANSITS_DESCRIPTION } from './query_eclipse_transits.js'
import { QUERY_PLANET_WAR_DESCRIPTION } from './query_planet_war.js'
import { LIST_ASSETS_DESCRIPTION } from './list_assets.js'

// Tier 3: UDA-2 additions (S1–S8)
import { MSR_SQL_DESCRIPTION } from './msr_sql.js'
import { TEMPORAL_DESCRIPTION } from './temporal.js'
import { KP_QUERY_DESCRIPTION } from './kp_query.js'
import { QUERY_KP_RULING_PLANETS_DESCRIPTION } from './query_kp_ruling_planets.js'
import { PATTERN_REGISTER_DESCRIPTION } from './pattern_register.js'
import { RESONANCE_REGISTER_DESCRIPTION } from './resonance_register.js'
import { CLUSTER_ATLAS_DESCRIPTION } from './cluster_atlas.js'
import { CONTRADICTION_REGISTER_DESCRIPTION } from './contradiction_register.js'
import { QUERY_UCN_WALK_DESCRIPTION } from './query_ucn_walk.js'
import { QUERY_CDLM_LOOKUP_DESCRIPTION } from './query_cdlm_lookup.js'
import { QUERY_RM_WALK_DESCRIPTION } from './query_rm_walk.js'
import { QUERY_JAIMINI_DRISHTI_DESCRIPTION } from './query_jaimini_drishti.js'
import { TIMELINE_QUERY_DESCRIPTION } from './timeline_query.js'
import { QUERY_SIGNAL_STATE_DESCRIPTION } from './query_signal_state.js'

// Tier 4: raw-asset reads
import { READ_ASSET_DESCRIPTION } from './read_asset.js'
import { READ_CLASSICAL_TEXT_DESCRIPTION } from './read_classical_text.js'

// Tier 5: observability + perf
import { GET_TRACE_DESCRIPTION } from './get_trace.js'
import { LIST_RECENT_QUERIES_DESCRIPTION } from './list_recent_queries.js'
import { TOOL_HEALTH_DESCRIPTION } from './tool_health.js'
import { DATA_COVERAGE_DESCRIPTION } from './data_coverage.js'

// Tier 6: write tools
import { LOG_PREDICTION_DESCRIPTION } from './log_prediction.js'
import { RECORD_OUTCOME_DESCRIPTION } from './record_outcome.js'
import { FLAG_DISAGREEMENT_DESCRIPTION } from './flag_disagreement.js'

export interface ToolCatalogEntry {
  name: string
  description: string
}

/**
 * CATALOG — all 57 MCP tools with their current descriptions.
 * Order mirrors server.ts tool registration order.
 */
export const CATALOG: ToolCatalogEntry[] = [
  // Tier 1: super-endpoint
  { name: 'chart_summary', description: CHART_SUMMARY_DESCRIPTION },

  // Tier 2: bundles
  { name: 'holistic_bundle', description: HOLISTIC_BUNDLE_DESCRIPTION },
  { name: 'multi_school_bundle', description: MULTI_SCHOOL_BUNDLE_DESCRIPTION },

  // Tier 3: surgical primitives
  { name: 'query_chart_facts', description: QUERY_CHART_FACTS_DESCRIPTION },
  { name: 'query_signals', description: QUERY_SIGNALS_DESCRIPTION },
  { name: 'query_dasha_periods', description: QUERY_DASHA_PERIODS_DESCRIPTION },
  { name: 'query_panchanga', description: QUERY_PANCHANGA_DESCRIPTION },
  { name: 'query_ephemeris', description: QUERY_EPHEMERIS_DESCRIPTION },
  { name: 'query_transit_event', description: QUERY_TRANSIT_EVENT_DESCRIPTION },
  { name: 'lel_query', description: LEL_QUERY_DESCRIPTION },
  { name: 'vector_search', description: VECTOR_SEARCH_DESCRIPTION },
  { name: 'get_cgm_subgraph', description: GET_CGM_SUBGRAPH_DESCRIPTION },
  { name: 'cross_school_lookup', description: CROSS_SCHOOL_LOOKUP_DESCRIPTION },
  { name: 'query_varshphal', description: 'Returns Varshaphala annual chart data. When to prefer: use for annual chart positions, varshesha, muntha, and year-lord questions.' },
  { name: 'query_divisional_chart', description: 'Returns divisional chart positions (D1–D60). When to prefer: use for varga-specific placements such as D9 navamsha or D10 dasamsha raw positions.' },
  { name: 'query_remedial_mantras', description: 'Returns remedial mantra corpus results. When to prefer: use when the user asks for a mantra or stotra for a specific planet, deity, or affliction.' },
  { name: 'muhurta_finder', description: MUHURTA_FINDER_DESCRIPTION },
  { name: 'tara_balam_for_native', description: TARA_BALAM_DESCRIPTION },
  { name: 'chandra_balam_for_native', description: CHANDRA_BALAM_DESCRIPTION },
  { name: 'query_transits_over_natal', description: QUERY_TRANSITS_OVER_NATAL_DESCRIPTION },
  { name: 'query_yogas_active_now', description: QUERY_YOGAS_ACTIVE_NOW_DESCRIPTION },
  { name: 'get_planet_avastha', description: 'Returns planetary avastha (experiential state) from chart_facts. When to prefer: use for avastha questions such as "What is Jupiter\'s avastha?" or "Is Venus agitated?".' },
  { name: 'get_shadbala_full', description: 'Returns full Shadbala roll-up with classical minimum rupa checks. When to prefer: use for "Is Saturn shadbala-sufficient?" or "What is Jupiter\'s total Shadbala?" questions.' },
  { name: 'interpret_current_dasha', description: INTERPRET_CURRENT_DASHA_DESCRIPTION },
  { name: 'list_canonical_artifact_versions', description: LIST_CANONICAL_ARTIFACT_VERSIONS_DESCRIPTION },
  { name: 'query_drekkana_drishti', description: 'Returns Jaimini Drekkana Drishti aspects from chart_facts. When to prefer: use for Jaimini special aspect questions involving the drekkana (D3) varga.' },
  { name: 'query_jaimini_chara_dasha', description: QUERY_JAIMINI_CHARA_DASHA_DESCRIPTION },
  { name: 'query_planetary_period_predictions', description: QUERY_PLANETARY_PERIOD_PREDICTIONS_DESCRIPTION },
  { name: 'query_dasamsha_career', description: 'Returns D10 Dasamsha career analysis from chart_facts. When to prefer: use for career and profession questions requiring D10 positions and yogas.' },
  { name: 'query_shashtiamsha', description: 'Returns D60 Shashtiamsha karma analysis from chart_facts. When to prefer: use for past-karma and D60 divisional chart questions.' },
  { name: 'query_eclipse_transits', description: QUERY_ECLIPSE_TRANSITS_DESCRIPTION },
  { name: 'query_planet_war', description: QUERY_PLANET_WAR_DESCRIPTION },
  { name: 'query_remedies_prescribed', description: 'Returns remedial prescription cross-reference from remedies table. When to prefer: use when retrieving previously prescribed remedies for specific afflictions or planets.' },

  // Tier 3: UDA-2 additions (S1–S8) — portal-only → MCP parity
  { name: 'msr_sql', description: MSR_SQL_DESCRIPTION },
  { name: 'temporal', description: TEMPORAL_DESCRIPTION },
  { name: 'kp_query', description: KP_QUERY_DESCRIPTION },
  { name: 'query_kp_ruling_planets', description: QUERY_KP_RULING_PLANETS_DESCRIPTION },
  { name: 'pattern_register', description: PATTERN_REGISTER_DESCRIPTION },
  { name: 'resonance_register', description: RESONANCE_REGISTER_DESCRIPTION },
  { name: 'cluster_atlas', description: CLUSTER_ATLAS_DESCRIPTION },
  { name: 'contradiction_register', description: CONTRADICTION_REGISTER_DESCRIPTION },
  { name: 'query_ucn_walk', description: QUERY_UCN_WALK_DESCRIPTION },
  { name: 'query_cdlm_lookup', description: QUERY_CDLM_LOOKUP_DESCRIPTION },
  { name: 'query_rm_walk', description: QUERY_RM_WALK_DESCRIPTION },
  { name: 'query_jaimini_drishti', description: QUERY_JAIMINI_DRISHTI_DESCRIPTION },
  { name: 'timeline_query', description: TIMELINE_QUERY_DESCRIPTION },
  { name: 'query_signal_state', description: QUERY_SIGNAL_STATE_DESCRIPTION },

  // Tier 4: raw-asset reads
  { name: 'list_assets', description: LIST_ASSETS_DESCRIPTION },
  { name: 'read_asset', description: READ_ASSET_DESCRIPTION },
  { name: 'read_classical_text', description: READ_CLASSICAL_TEXT_DESCRIPTION },

  // Tier 5: observability + perf
  { name: 'get_trace', description: GET_TRACE_DESCRIPTION },
  { name: 'list_recent_queries', description: LIST_RECENT_QUERIES_DESCRIPTION },
  { name: 'tool_health', description: TOOL_HEALTH_DESCRIPTION },
  { name: 'data_coverage', description: DATA_COVERAGE_DESCRIPTION },

  // Tier 6: write tools
  { name: 'log_prediction', description: LOG_PREDICTION_DESCRIPTION },
  { name: 'record_outcome', description: RECORD_OUTCOME_DESCRIPTION },
  { name: 'flag_disagreement', description: FLAG_DISAGREEMENT_DESCRIPTION },
]
