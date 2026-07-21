/**
 * Layer L5_mimamsa — D5 fan-out: register all L5 Mīmāṃsā retrieval capabilities.
 *
 * Previously registered: query_insights (mi_darshana), query_calibration (mi_pramana, STUBBED).
 * D5 wave adds:
 *   query_predictions         — mi_bhavisya (mimamsa_predictions, 50 rows sparse)
 *   query_signal_families     — mi_kula (global, no chart_id)
 *   query_manifestation_grammar — mi_sambandha (per_chart, count unknown)
 *
 * GATE A: per-wave registration — no edits to registry/index.ts or types.ts.
 */
import { registerCapability } from '../../index'

import { queryInsightsCapability }           from './query_insights'
import { queryCalibrationCapability }        from './query_calibration'
import { queryPredictionsCapability }        from './query_predictions'
import { querySignalFamiliesCapability }     from './query_signal_families'
import { queryManifestationGrammarCapability } from './query_manifestation_grammar'
// WP-1.3(d) / F-L10-021: lel_query — the LEL intake serving surface (life_events table).
import { queryLifeEventsCapability }         from './query_life_events'
// DOCTRINE-WAVES D-4b Lane B-5 (= BRIEF_D4.md v2.0 Lane C-6): mechanism_retrodiction
// surface — LEL events joined to the classical dasha-lord/house-activation mechanism,
// served as CONFIRMATION ONLY (never prediction input).
import { queryMechanismRetrodictionCapability } from './query_mechanism_retrodiction'
// W2b Batch 4 dark-set wiring (TABLE_CONCEPT_DISPOSITIONS_v2_0.md SERVE-gap set): 6
// research/explainability L5 items, deliberately distinct from the GATED calibration-
// overlay tables (mimamsa_fact_adjustment/mimamsa_signal_adjustment/
// mimamsa_convergence_adjustment/mimamsa_anchor_adjustment) — see each file's header.
import { queryAttributionCapability }        from './query_attribution'
import { queryMimamsaDiscoveriesCapability } from './query_mimamsa_discoveries'
import { queryInsightEmbeddingsCapability }  from './query_insight_embeddings'
import { queryJournalCapability }            from './query_journal'
import { queryLoadBearingCapability }        from './query_load_bearing'
import { queryManifestationSetsCapability }  from './query_manifestation_sets'

registerCapability(queryInsightsCapability)
registerCapability(queryCalibrationCapability)
registerCapability(queryPredictionsCapability)
registerCapability(querySignalFamiliesCapability)
registerCapability(queryManifestationGrammarCapability)
registerCapability(queryLifeEventsCapability)
registerCapability(queryMechanismRetrodictionCapability)
registerCapability(queryAttributionCapability)
registerCapability(queryMimamsaDiscoveriesCapability)
registerCapability(queryInsightEmbeddingsCapability)
registerCapability(queryJournalCapability)
registerCapability(queryLoadBearingCapability)
registerCapability(queryManifestationSetsCapability)
