import { z } from 'zod'
import { defineTool } from '../defineTool'

const inputSchema = z.object({
  chart_id: z.string().describe('Required chart identifier.'),
  ayanamsha_id: z.string().optional(),
  cusp: z.number().int().min(1).max(12).optional(),
  planet: z.string().optional(),
  level: z.enum(['star_lord', 'sub_lord', 'sub_sub_lord']).optional(),
})

export const kpQueryContract = defineTool({
  canonical_name: 'kp_query',
  input_schema: inputSchema,
  description:
    'KP cuspal sub-lord lookup + planet-cusp significator table. ' +
    'When to prefer: "Which planet rules the 7th cusp?", "What is Jupiter\'s sub-lord?". ' +
    'Operates under the KP ayanamsha — isolated from canonical/Parashari ayanamsha per Unit 1.1.',
  role: 'retrieval',
  family: 'kp',
  data_dependency: 'chart_facts',
  ayanamsha_role: 'kp',
  annotations: { surgical: true, layer: 'L1' },
})
