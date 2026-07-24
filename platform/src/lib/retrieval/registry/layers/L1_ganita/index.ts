/**
 * Layer L1_ganita — Wave 3 R2: register all L1 retrieval capabilities
 * 15 tools covering all 158 chart_facts fact_categories + dashas + divisionals + tajik table
 */
import { registerCapability } from '../../index'

import { getPositionsCapability }        from './get_positions'
import { getStrengthCapability }         from './get_strength'
import { getAshtakavargaCapability }     from './get_ashtakavarga'
import { getBhavaBalaCapability }        from './get_bhava_bala'
import { getAspectsCapability }          from './get_aspects'
import { getYogaDoshaCapability }        from './get_yoga_dosha'
import { getArgalaCapability }           from './get_argala'
import { getDispositorsCapability }      from './get_dispositors'
import { getSadeSatiCapability }         from './get_sade_sati'
import { getPanchangaCapability }        from './get_panchanga'
import { getSensitivePointsCapability }  from './get_sensitive_points'
import { getKarakasCapability }          from './get_karakas'
import { getDignityCapability }          from './get_dignity'
import { getAvasthsCapability }          from './get_avasthas'
import { getTajikCapability }            from './get_tajik'
import { getTaraChanndraBalaCapability } from './get_tara_chandra_bala'
import { getEclipseFlagsCapability }     from './get_eclipse_flags'
import { getDashasCapability }           from './get_dashas'
import { getDivisionalsCapability }      from './get_divisionals'
import { getTransitAnchorsCapability }  from './get_transit_anchors'
import { getChartHeaderCapability }      from './get_chart_header'
import { getGrahaYuddhaCapability }      from './get_graha_yuddha'
import { getChartSnapshotCapability }    from './get_chart_snapshot'
// WP-1.3(a) / F-L10-001..003 (LCA-19): computed-but-unserved L1 assets.
import { getMedicalIndicationsCapability } from './get_medical_indications'
import { getVastuDirectionsCapability }    from './get_vastu_directions'
import { getYogaFiringsCapability }        from './get_yoga_firings'
// W4-loop-1 (E-6): longevity (ga_ayurdaya) + sensitive-degree (ga_sensitive_degree)
import { getAyurdayaCapability }           from './get_ayurdaya'
import { getSensitiveDegreesCapability }   from './get_sensitive_degrees'
// Doctrine Campaign D-1 Night-1, Lane 5: judged structure (ga_vichara, Lane 2's new asset)
import { getVicharaCapability }            from './get_vichara'
// Doctrine Campaign D-1.5b, Lane B-7: B8 derived view — per-MD-lord serving capability
// (computed serving-layer aggregation over chart_dashas + chart_facts + chart_vichara).
import { getDashaLordCapabilityCapability } from './get_dasha_lord_capability'
// Doctrine Campaign D-3 (Kāla Taraṅga), Lane T-1: sign-keyed Aṣṭakavarga transit-gating
// (SAV/BAV damp/amplify per sign) + dated kakṣyā sub-windows for a transiting planet.
import { getAvTransitGatingCapability }     from './get_av_transit_gating'
// W2b Batch 3 dark-set wiring (TABLE_CONCEPT_DISPOSITIONS_v2_0.md): unified planetary-condition
// rollup + prashna-lagna serving.
import { getConditionCompositeCapability }  from './get_condition_composite'
import { getPrashnaLagnaCapability }        from './get_prashna_lagna'
// SARVA-SIDDHI W-4 lane D-4 (CR-30): dedicated first-class KP (Krishnamurti Paddhati)
// cusp/sub-lord serving face over the already-stored KP fact categories (no new computation).
import { getKpCuspsCapability }             from './get_kp_cusps'

registerCapability(getPositionsCapability)
registerCapability(getStrengthCapability)
registerCapability(getAshtakavargaCapability)
registerCapability(getBhavaBalaCapability)
registerCapability(getAspectsCapability)
registerCapability(getYogaDoshaCapability)
registerCapability(getArgalaCapability)
registerCapability(getDispositorsCapability)
registerCapability(getSadeSatiCapability)
registerCapability(getPanchangaCapability)
registerCapability(getSensitivePointsCapability)
registerCapability(getKarakasCapability)
registerCapability(getDignityCapability)
registerCapability(getAvasthsCapability)
registerCapability(getTajikCapability)
registerCapability(getTaraChanndraBalaCapability)
registerCapability(getEclipseFlagsCapability)
registerCapability(getDashasCapability)
registerCapability(getDivisionalsCapability)
registerCapability(getTransitAnchorsCapability)
registerCapability(getChartHeaderCapability)
registerCapability(getGrahaYuddhaCapability)
registerCapability(getChartSnapshotCapability)
registerCapability(getMedicalIndicationsCapability)
registerCapability(getVastuDirectionsCapability)
registerCapability(getYogaFiringsCapability)
registerCapability(getAyurdayaCapability)
registerCapability(getSensitiveDegreesCapability)
registerCapability(getVicharaCapability)
registerCapability(getDashaLordCapabilityCapability)
registerCapability(getAvTransitGatingCapability)
registerCapability(getConditionCompositeCapability)
registerCapability(getPrashnaLagnaCapability)
registerCapability(getKpCuspsCapability)
