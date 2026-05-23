/**
 * catalog.ts — MCPT v3.2 Phase 3: Tool description catalog for lint testing.
 *
 * Exports an array of { name, description } entries for all 21 registered MCP tools.
 * Used by test/tool_descriptions.test.ts to enforce the Phase 3 lint gate:
 *   - every description starts with a disambiguator sentence
 *   - every description contains "When to prefer:"
 *   - every description is ≤ 1200 characters
 */

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
 * CATALOG — all 21 MCP tools with their current descriptions.
 * Order mirrors server.ts tool registration order.
 */
export const CATALOG: ToolCatalogEntry[] = [
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

  // Tier 4: raw-asset reads
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
