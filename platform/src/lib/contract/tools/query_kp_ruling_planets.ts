import { z } from 'zod'
import { defineTool } from '../defineTool'

const inputSchema = z.object({
  chart_id: z.string().describe('Required chart identifier.'),
  ayanamsha_id: z.string().optional().describe(
    'Optional override for the KP ayanamsha id (default: kp_newcomb). KP-system tools default to KP_NEWCOMB per Unit 1.1.'
  ),
  as_of_datetime: z.string().optional().describe('ISO datetime for the horary moment.'),
  observer: z.object({
    lat: z.number().optional(),
    lon: z.number().optional(),
  }).optional(),
})

export const queryKpRulingPlanetsContract = defineTool({
  canonical_name: 'query_kp_ruling_planets',
  input_schema: inputSchema,
  description:
    'KP Ruling Planets (RP) at a moment: day-lord, asc star-lord/sub-lord, ' +
    'Moon star-lord/sub-lord. When to prefer: KP horary RP, prashna RP, event-timing RP. ' +
    'Operates under the KP ayanamsha (KP_NEWCOMB) — isolated from canonical/Parashari ayanamsha per Unit 1.1.',
  role: 'retrieval',
  family: 'kp',
  data_dependency: 'chart_facts',
  ayanamsha_role: 'kp',
  annotations: { surgical: true, layer: 'L1' },
})
