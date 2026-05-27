import { z } from 'zod'
import { defineTool } from '../defineTool'

const inputSchema = z.object({
  chart_id: z.string().describe('Required chart identifier.'),
  ayanamsha_id: z.string().optional(),
  varga: z.string().describe('Divisional chart code (e.g. "D1", "D9", "D10", "D60").'),
  planet: z.string().optional(),
  house: z.number().int().min(1).max(12).optional(),
})

export const queryDivisionalChartContract = defineTool({
  canonical_name: 'query_divisional_chart',
  input_schema: inputSchema,
  description:
    'Divisional chart (varga) positions: D1–D60 raw planet/house placements. ' +
    'When to prefer: varga-specific reads ("Jupiter in D9?", "D10 10th lord?"). ' +
    'Prefer query_dasamsha_career for D10 career synthesis, query_shashtiamsha for D60 karma.',
  role: 'retrieval',
  family: 'chart',
  data_dependency: 'chart_facts',
  ayanamsha_role: 'canonical',
  annotations: { surgical: true, layer: 'L1' },
})
