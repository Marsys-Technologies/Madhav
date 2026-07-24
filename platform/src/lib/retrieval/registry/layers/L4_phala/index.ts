/**
 * Layer L4_phala — D5 fan-out: register all L4 Phala retrieval capabilities.
 *
 * 9 capabilities covering 9 L4 assets:
 *   query_predictive_anchors  — ph_nimitta (phala_anchors, 150 rows)
 *   query_domain_result       — ph_phaladesa (phala_phaladesa, 7 rows — by design)
 *   query_auspicious_windows  — ph_muhurta (phala_muhurta, 100 rows)
 *   query_spillover_cascades  — ph_sankrama (phala_sankrama, 73 rows)
 *   query_falsifiers          — ph_pramana (phala_pramana, 150 rows)
 *   query_anomaly_flags       — ph_sodhana (phala_sodhana, 200 rows)
 *   query_remedy_program      — ph_pratikara (phala_mitigation, sparse)
 *   query_cleansed_anchors    — ph_suddha_sodhana (sparse)
 *   query_rectification       — ph_rectification (~185 candidates)
 *
 * GATE A: per-wave registration — no edits to registry/index.ts or types.ts.
 */
import { registerCapability } from '../../index'

import { queryPredictiveAnchorsCapability } from './query_predictive_anchors'
import { queryDomainResultCapability }      from './query_domain_result'
import {
  queryAuspiciousWindowsCapability,
  querySpilloverCascadesCapability,
  queryFalsifiersCapability,
  queryAnomalyFlagsCapability,
  queryRemedyProgramCapability,
  queryCleasedAnchorsCapability,
  queryRectificationCapability,
} from './query_phala_calibration'
import { queryMuhuratCapability } from './query_muhurat'
// SARVA-SIDDHI W-2 P-1 — read side of the LIVE prospective ledger (brahma_prospective_ledger),
// the table the Vidhi E-2 `standing_predictions_read` primitive was always meant to read (it
// had been mis-wired to phala_predictive_anchors_get). See query_prospective_ledger.ts header.
import { queryProspectiveLedgerCapability } from './query_prospective_ledger'

registerCapability(queryPredictiveAnchorsCapability)
registerCapability(queryDomainResultCapability)
registerCapability(queryAuspiciousWindowsCapability)
registerCapability(querySpilloverCascadesCapability)
registerCapability(queryFalsifiersCapability)
registerCapability(queryAnomalyFlagsCapability)
registerCapability(queryRemedyProgramCapability)
registerCapability(queryCleasedAnchorsCapability)
registerCapability(queryRectificationCapability)
// R5.1 C3 — real electional muhurta finder (replaces the query_planet_transit
// mis-mapping in tool_name_bridge.ts). See query_muhurat.ts header comment.
registerCapability(queryMuhuratCapability)
registerCapability(queryProspectiveLedgerCapability)
