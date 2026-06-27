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

registerCapability(callTransitSearchCapability)
registerCapability(callEphemerisAtTCapability)
registerCapability(callDashaEligibilityCapability)
registerCapability(callMuhurtaScoreCapability)
registerCapability(callPriorityRankingCapability)
