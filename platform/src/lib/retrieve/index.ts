/**
 * MARSYS-JIS Retrieval tool registry
 *
 * Exports all retrieval tools and the RETRIEVAL_TOOLS registry array.
 * Phase 2: msr_sql, pattern_register, resonance_register, cluster_atlas,
 *           contradiction_register, temporal, query_msr_aggregate (7 tools)
 * Phase 9: cgm_graph_walk, manifest_query, vector_search (3 tools; vector_search is secondary)
 * Wave 4 M2-C234: kp_query, saham_query, divisional_query (3 tools)
 * Wave 4 M2-C1: chart_facts_query (1 tool)
 * Wave 5 M2-D234: domain_report_query, remedial_codex_query, timeline_query (3 tools)
 * M5-A: lel_query — LEL ground-truth life events from life_events table (1 tool)
 * Phase 4A: query_ephemeris — date-indexed ephemeris lookup (1 tool; closes ephemeris-accessibility gap)
 * Phase 4C: query_panchanga — sunrise-anchored daily panchanga (1 tool; 28th total)
 * Phase 4D: query_transit_event — transit event search: when does X happen? (1 tool; 29th total)
 * COV-S4: query_muhurat, query_jaimini_drishti, query_v7_additions — sidecar wrappers (tools 31-33)
 * COV-S5: query_ucn_walk, query_cdlm_lookup, query_rm_walk — L2.5 structural graph tools (tools 34-36)
 */

import * as msrSql from './msr_sql'
import * as patternRegister from './pattern_register'
import * as resonanceRegister from './resonance_register'
import * as clusterAtlas from './cluster_atlas'
import * as contradictionRegister from './contradiction_register'
import * as temporal from './temporal'
import * as queryMsrAggregate from './query_msr_aggregate'
import * as cgmGraphWalk from './cgm_graph_walk'
import * as manifestQuery from './manifest_query'
import * as vectorSearch from './vector_search'

// Wave 4 additions — M2-C234-BUNDLE
import * as kpQuery from './kp_query'
import * as sahamQuery from './saham_query'
import * as divisionalQuery from './divisional_query'

// Wave 4 — M2-C1-CHART-FACTS-QUERY
import * as chartFactsQuery from './chart_facts_query'

// VARGA-ETL-FULL-S1-CPA D8 — §3.15 CSI cross-divisional dignity surface
import * as crossVargaDignityQuery from './cross_varga_dignity_query'

// Wave 5 additions — M2-D234-BUNDLE
import * as domainReportQuery from './domain_report_query'
import * as remedialCodexQuery from './remedial_codex_query'
import * as timelineQuery from './timeline_query'

// M3-B — signal state surface
import * as querySignalState from './query_signal_state'

// M3-W3-C2 — KP sub-lord substrate + Varshaphala annual chart
import * as queryKpRulingPlanets from './query_kp_ruling_planets'
import * as queryVarshaphala from './query_varshaphala'

// M5-A — LEL ground-truth life events (fixes LEL retrieval gap)
import * as lelQuery from './lel_query'

// M8-G — classical corpus tools (tools 25+26)
import * as classicalTextSearchTool from './classical_text_search_tool'
import * as classicalAttributionLookupTool from './classical_attribution_lookup_tool'

// M9 — multi-school triangulation (tools 25+26)
import * as multiSchoolSignalLookupTool from './multi_school_signal_lookup_tool'
import * as convergenceScoreLookupTool from './convergence_score_lookup_tool'

// Phase 4A — date-indexed ephemeris lookup (closes ephemeris-accessibility gap)
import * as queryEphemeris from './query_ephemeris'

// Phase 4C — sunrise-anchored daily panchanga (5 limbs of Vedic time)
import * as queryPanchanga from './query_panchanga'

// Phase 4D — transit event search: when does X happen? (29th tool)
import * as queryTransitEvent from './query_transit_event'

// Phase 5A — surgical dasha schedule lookup (30th tool)
import * as queryDashaPeriods from './query_dasha_periods'

// COV-S4 — sidecar wrappers for three orphaned endpoints (tools 31-33)
import * as queryMuhurat from './query_muhurat'
import * as queryJaiminiDrishti from './query_jaimini_drishti'
import * as queryV7Additions from './query_v7_additions'

// COV-S5 — L2.5 structural graph retrieval tools (tools 34-36)
import * as queryUcnWalk from './query_ucn_walk'
import * as queryCdlmLookup from './query_cdlm_lookup'
import * as queryRmWalk from './query_rm_walk'

export * from './types'
import type { RetrievalTool } from './types'

export const RETRIEVAL_TOOLS: RetrievalTool[] = [
  msrSql.tool,
  patternRegister.tool,
  resonanceRegister.tool,
  clusterAtlas.tool,
  contradictionRegister.tool,
  temporal.tool,
  queryMsrAggregate.tool,
  cgmGraphWalk.tool,
  manifestQuery.tool,
  vectorSearch.tool,
  kpQuery.tool,
  sahamQuery.tool,
  divisionalQuery.tool,
  chartFactsQuery.tool,
  crossVargaDignityQuery.tool,
  domainReportQuery.tool,
  remedialCodexQuery.tool,
  timelineQuery.tool,
  querySignalState.tool,
  queryKpRulingPlanets.tool,
  queryVarshaphala.tool,
  lelQuery.tool,
  classicalTextSearchTool.tool,
  classicalAttributionLookupTool.tool,
  multiSchoolSignalLookupTool.tool,
  convergenceScoreLookupTool.tool,
  queryEphemeris.tool,
  queryPanchanga.tool,
  queryTransitEvent.tool,
  queryDashaPeriods.tool,
  queryMuhurat.tool,
  queryJaiminiDrishti.tool,
  queryV7Additions.tool,
  queryUcnWalk.tool,
  queryCdlmLookup.tool,
  queryRmWalk.tool,
]

export function getTool(name: string): RetrievalTool | undefined {
  return RETRIEVAL_TOOLS.find(t => t.name === name)
}
