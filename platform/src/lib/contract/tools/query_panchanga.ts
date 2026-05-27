import { z } from 'zod'
import { defineTool } from '../defineTool'

/**
 * query_panchanga is split-personality re ayanamsha:
 *   - tithi / karana / yoga / vara are panchang-invariant under ayanamsha
 *     choice (defined from Sun-Moon longitude differences and weekday).
 *   - moon_nakshatra IS ayanamsha-dependent.
 *
 * The contract declares `canonical` ayanamsha_role because the response
 * includes moon_nakshatra; downstream consumers can ignore the field if they
 * only need the invariant limbs. The optional `ayanamsha_id` override lets a
 * KP-style reading request the KP nakshatra. (Unit 1.1 isolation contract.)
 */
const inputSchema = z.object({
  date: z.string().describe('ISO date (YYYY-MM-DD).'),
  chart_id: z.string().describe(
    'Required chart identifier (for native overlay + observer location default).'
  ),
  ayanamsha_id: z.string().optional().describe(
    'Optional override for the canonical ayanamsha id (default: lahiri). ' +
    'Affects moon_nakshatra; tithi/vara/yoga/karana are ayanamsha-invariant.'
  ),
  observer: z.object({
    lat: z.number().optional(),
    lon: z.number().optional(),
  }).optional(),
})

export const queryPanchangaContract = defineTool({
  canonical_name: 'query_panchanga',
  input_schema: inputSchema,
  description:
    'Daily Vedic panchang: tithi, vara, nakshatra, yoga, karana, plus hora, ' +
    'choghadiya, muhurat, inauspicious periods. When to prefer: date-specific ' +
    'lookups ("today\'s nakshatra?", "when is Rahu Kalam?"). Prefer holistic_bundle ' +
    'for interpretation against the native chart.',
  role: 'retrieval',
  family: 'panchang',
  data_dependency: 'panchang_daily',
  ayanamsha_role: 'canonical',
  annotations: { surgical: true, layer: 'L1.5' },
})
