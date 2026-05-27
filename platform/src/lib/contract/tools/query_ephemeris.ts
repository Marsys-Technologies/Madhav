import { z } from 'zod'
import { defineTool } from '../defineTool'

/**
 * query_ephemeris is NOT per-chart (no chart_id required). It is a pure
 * ayanamsha-frame ephemeris lookup. Its ayanamsha_role is `reference` — it
 * may be called from either the canonical or KP side, and the caller passes
 * the desired frame as `ayanamsha_id`.
 */
const inputSchema = z.object({
  ayanamsha_id: z.string().optional().describe(
    'Optional reference-frame ayanamsha id (default: lahiri).'
  ),
  date_range: z.object({
    start: z.string().describe('ISO date (YYYY-MM-DD) lower bound.'),
    end: z.string().describe('ISO date (YYYY-MM-DD) upper bound.'),
  }),
  planets: z.array(z.string()).optional(),
  step_days: z.number().int().min(1).optional().default(1),
})

export const queryEphemerisContract = defineTool({
  canonical_name: 'query_ephemeris',
  input_schema: inputSchema,
  description:
    'Date-indexed ephemeris lookup over a window. Returns planet positions ' +
    '(longitude, sign, nakshatra, retrograde) per step. When to prefer: ' +
    'questions about planetary positions on arbitrary dates ("Where will Saturn be on 2027-03-15?"). ' +
    'Reference ayanamsha frame — does not bind to a specific chart.',
  role: 'retrieval',
  family: 'ephemeris',
  data_dependency: 'ephemeris',
  ayanamsha_role: 'reference',
  annotations: { surgical: true, layer: 'L1' },
  per_chart: false,
})
