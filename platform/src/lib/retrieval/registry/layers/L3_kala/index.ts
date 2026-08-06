/**
 * Layer L3_kala — D5 fan-out: register all L3 Kāla retrieval capabilities.
 *
 * Data tools (6):
 *   query_temporal_activation  — ka_kalasutra + ka_yojaka (activation + predicates)
 *   query_convergence_windows  — ka_sangam (kala_convergence)
 *   query_life_arc             — ka_jivana_parva (biographical chapters)
 *   query_projections          — ka_bhavishya_lekha (forward projections)
 *   query_obstruction_periods  — ka_vighnakara (STUBBED-PENDING-DATA, 0 rows)
 *   query_temporal_view        — ka_kala_darshana (STUBBED-PENDING-DATA, 0 rows)
 *   query_kota_chakra          — ka_kota_chakra (W3 item 16, fort chart)
 *   query_sudarshana_varsha    — ka_sudarshana_varsha (W3 item 17, year-wheel)
 *   query_moorti_nirnaya       — ka_moorti_nirnaya (W3 item 4, moorti-nirṇaya)
 *   query_vedha_gochara        — ka_vedha_gochara (W3 item 5, vedha + sarvatobhadra; closes R-19)
 *   query_tithi_pravesha       — ka_tithi_pravesha (W3 item 13, lunar-return annual chart)
 *
 * Service wrappers (5):
 *   call_transit_search        — ka_gochara
 *   call_ephemeris_at_t        — ka_graha_sancara
 *   call_dasha_eligibility     — ka_dasha_kala
 *   call_muhurta_score         — ka_muhurta_seva
 *   call_priority_ranking      — ka_tulana
 *
 * GATE A: per-wave registration — no edits to registry/index.ts or types.ts.
 */
import { registerCapability } from '../../index'

import { queryTemporalActivationCapability }  from './query_temporal_activation'
import { queryConvergenceWindowsCapability }  from './query_convergence_windows'
import { queryLifeArcCapability }             from './query_life_arc'
import { queryProjectionsCapability }         from './query_projections'
import { queryObstructionPeriodsCapability }  from './query_obstruction_periods'
import { queryTemporalViewCapability }        from './query_temporal_view'
// WP-1.3(a) / F-L10-009,015 (LCA-19): computed-but-unserved L3 assets.
import { queryDashaDossierCapability }        from './query_dasha_dossier'
import { queryActivationWaveformCapability }  from './query_activation_waveform'
// EL-33 (Elevation v2.1, γ.F): point-in-time active-dasha convenience face across all systems.
import { queryActiveDashasCapability }        from './query_active_dashas'
// ṢAḌ-DARŚANA W3 Lane w3-kota-sudarshana, registry items 16/17.
import { queryKotaChakraCapability }          from './query_kota_chakra'
import { querySudarshanaVarshaCapability }    from './query_sudarshana_varsha'
// ṢAḌ-DARŚANA W3 lane-w3rit, registry item 37 — paddhati convention profile capability.
// Closes the documented gap: kala_sky_pattern.ts called query_kala_paddhati_profile but
// it was never registered (SHAD_DARSHANA_STATE.md Night-3 close, "Item 37 partial").
import { queryKalaPaddhatiProfileCapability } from './query_kala_paddhati_profile'
// ṢAḌ-DARŚANA W3 Lane w3-moorti-vedha, registry items 4/5 (item 5 closes R-19).
import { queryMoortiNirnayaCapability }       from './query_moorti_nirnaya'
import { queryVedhaGocharaCapability }        from './query_vedha_gochara'
// ṢAḌ-DARŚANA W3 Lane w3-tithi-pravesha, registry item 13 (lunar-return annual chart).
import { queryTithiPraveshaCapability }       from './query_tithi_pravesha'
import {
  callTransitSearchCapability,
  callEphemerisAtTCapability,
  callDashaEligibilityCapability,
  callMuhurtaScoreCapability,
  callPriorityRankingCapability,
} from './call_service_wrappers'

registerCapability(queryTemporalActivationCapability)
registerCapability(queryConvergenceWindowsCapability)
registerCapability(queryLifeArcCapability)
registerCapability(queryProjectionsCapability)
registerCapability(queryObstructionPeriodsCapability)
registerCapability(queryTemporalViewCapability)
registerCapability(queryDashaDossierCapability)
registerCapability(queryActivationWaveformCapability)
registerCapability(queryActiveDashasCapability)
registerCapability(queryKotaChakraCapability)
registerCapability(querySudarshanaVarshaCapability)
registerCapability(queryKalaPaddhatiProfileCapability)
registerCapability(queryMoortiNirnayaCapability)
registerCapability(queryVedhaGocharaCapability)
registerCapability(queryTithiPraveshaCapability)

registerCapability(callTransitSearchCapability)
registerCapability(callEphemerisAtTCapability)
registerCapability(callDashaEligibilityCapability)
registerCapability(callMuhurtaScoreCapability)
registerCapability(callPriorityRankingCapability)
