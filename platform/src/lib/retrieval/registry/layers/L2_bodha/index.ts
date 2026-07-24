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
// WP-1.3(a) / F-L10-004..007 (LCA-19): computed-but-unserved L2 CDLM/CGM/gestalt assets.
import { queryCdlmSummaryCapability }      from './query_cdlm_summary'
import { queryCgmMotifsCapability }        from './query_cgm_motifs'
import { queryCgmPathsCapability }         from './query_cgm_paths'
import { queryChartGestaltCapability }     from './query_chart_gestalt'
// WP-1.3j / F-0129..0137,0156,0161,0165,0174,0176 (W1-FOLLOWUP): populated-but-unserved
// L2 Bodha assets with real rows + no writer needed — surgical serving surfaces added.
import { queryDiscoveriesCapability }      from './query_discoveries'
import { queryPratijnaCapability }         from './query_pratijna'
import { queryQuestionLensesCapability }   from './query_question_lenses'
import { queryRmPrescriptionsCapability }  from './query_rm_prescriptions'
import { queryRmResonancesCapability }     from './query_rm_resonances'
// W2b Batch 3 dark-set wiring (TABLE_CONCEPT_DISPOSITIONS_v2_0.md SERVE-gap set):
// remaining Remedial Matrix siblings, previously written but never registered.
import { queryRmChartSummaryCapability }             from './query_rm_chart_summary'
import { queryRmDashaWindowedPrescriptionsCapability } from './query_rm_dasha_windowed_prescriptions'
import { queryRmPatternRemediesCapability }          from './query_rm_pattern_remedies'
import { queryRmDoshaRemedyBundlesCapability }       from './query_rm_dosha_remedy_bundles'
import { queryTriangulationCapability }              from './query_triangulation'
// SARVA-SIDDHI W-4 / CR-24: bodha_mechanisms (bo_yantra_mechanism) first-class serving face —
// named, valenced chain/circuit mechanisms, previously reachable only via traverse_chart_graph.
import { queryMechanismsCapability }                 from './query_mechanisms'

registerCapability(queryUcdCapability)
registerCapability(traverseChartGraphCapability)
registerCapability(queryDomainReadingCapability)
registerCapability(querySignalsCapability)
registerCapability(queryContradictionsCapability)
registerCapability(queryRemediesCapability)
registerCapability(queryQualityScorecardCapability)
registerCapability(grahaPortraitCapability)
registerCapability(queryCdlmSummaryCapability)
registerCapability(queryCgmMotifsCapability)
registerCapability(queryCgmPathsCapability)
registerCapability(queryChartGestaltCapability)
registerCapability(queryDiscoveriesCapability)
registerCapability(queryPratijnaCapability)
registerCapability(queryQuestionLensesCapability)
registerCapability(queryRmPrescriptionsCapability)
registerCapability(queryRmResonancesCapability)
registerCapability(queryRmChartSummaryCapability)
registerCapability(queryRmDashaWindowedPrescriptionsCapability)
registerCapability(queryRmPatternRemediesCapability)
registerCapability(queryRmDoshaRemedyBundlesCapability)
registerCapability(queryTriangulationCapability)
registerCapability(queryMechanismsCapability)
