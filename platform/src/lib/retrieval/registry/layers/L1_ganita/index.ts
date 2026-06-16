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
