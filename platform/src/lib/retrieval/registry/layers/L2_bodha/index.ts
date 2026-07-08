/**
 * Layer L2_bodha — D5 fan-out: register all L2 retrieval capabilities.
 *
 * Previously registered (D4 wave): query_ucd, traverse_chart_graph.
 * D5 wave adds: query_domain_reading, query_signals, query_contradictions,
 *               query_remedies, query_quality_scorecard.
 *
 * GATE A: per-wave registration — no edits to registry/index.ts or types.ts.
 */
import { registerCapability } from '../../index'

import { queryUcdCapability }              from './query_ucd'
import { traverseChartGraphCapability }    from './traverse_chart_graph'
import { queryDomainReadingCapability }    from './query_domain_reading'
import { querySignalsCapability }          from './query_signals'
import { queryContradictionsCapability }   from './query_contradictions'
import { queryRemediesCapability }         from './query_remedies'
import { queryQualityScorecardCapability } from './query_quality_scorecard'
import { grahaPortraitCapability }         from './graha_portrait'

registerCapability(queryUcdCapability)
registerCapability(traverseChartGraphCapability)
registerCapability(queryDomainReadingCapability)
registerCapability(querySignalsCapability)
registerCapability(queryContradictionsCapability)
registerCapability(queryRemediesCapability)
registerCapability(queryQualityScorecardCapability)
registerCapability(grahaPortraitCapability)
