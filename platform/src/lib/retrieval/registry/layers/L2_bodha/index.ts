/**
 * Layer L2_bodha — Wave 4 B4: register all L2 retrieval capabilities.
 * Registered after bo_samvada creates vw_chart_digest.
 */
import { registerCapability } from '../../index'

import { queryUcdCapability } from './query_ucd'

registerCapability(queryUcdCapability)
