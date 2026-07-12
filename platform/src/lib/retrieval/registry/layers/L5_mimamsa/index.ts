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

registerCapability(queryInsightsCapability)
registerCapability(queryCalibrationCapability)
registerCapability(queryPredictionsCapability)
registerCapability(querySignalFamiliesCapability)
registerCapability(queryManifestationGrammarCapability)
registerCapability(queryLifeEventsCapability)
