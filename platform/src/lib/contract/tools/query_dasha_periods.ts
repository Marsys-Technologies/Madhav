import { z } from 'zod'
import { defineTool } from '../defineTool'

const inputSchema = z.object({
  chart_id: z.string().describe('Required chart identifier.'),
  ayanamsha_id: z.string().optional(),
  system: z.enum(['vimshottari', 'yogini', 'ashtottari']).optional().default('vimshottari'),
  level: z.enum(['mahadasha', 'antardasha', 'pratyantardasha']).optional().default('antardasha'),
  as_of_date: z.string().optional(),
  start_date: z.string().optional(),
  end_date: z.string().optional(),
})

export const queryDashaPeriodsContract = defineTool({
  canonical_name: 'query_dasha_periods',
  input_schema: inputSchema,
  description:
    'Active dasha period lookup at a date, or a windowed timeline of MD/AD/PD ' +
    'periods. When to prefer: questions about "current dasha", "what\'s next?", ' +
    'or windowed timelines. Prefer query_planetary_period_predictions for classical interpretation.',
  role: 'retrieval',
  family: 'dasha',
  data_dependency: 'chart_facts',
  ayanamsha_role: 'canonical',
  annotations: { surgical: true, layer: 'L1' },
})
