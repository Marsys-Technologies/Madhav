/**
 * Layer L5_mimamsa — Mīmāṃsā calibration surface capabilities.
 * Registered after L5 build completes (mi_pramana → mi_darshana).
 */
import { registerCapability } from '../../index'

import { queryInsightsCapability }    from './query_insights'
import { queryCalibrationCapability } from './query_calibration'

registerCapability(queryInsightsCapability)
registerCapability(queryCalibrationCapability)
