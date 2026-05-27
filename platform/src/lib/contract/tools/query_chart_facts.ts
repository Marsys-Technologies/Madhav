import { z } from 'zod'
import { defineTool } from '../defineTool'

const inputSchema = z.object({
  chart_id: z.string().describe(
    'Required chart identifier. The default `NATIVE_CHART_ID` is removed in Gate G4 — every per-chart call must pass an explicit chart_id.'
  ),
  ayanamsha_id: z.string().optional().describe(
    'Optional override for the canonical ayanamsha id (default: lahiri).'
  ),
  category: z.string().optional(),
  categories: z.array(z.string()).optional(),
  planet: z.string().optional(),
  house: z.number().int().min(1).max(12).optional(),
  as_of_date: z.string().optional(),
  divisional_chart: z.string().optional(),
  limit: z.number().int().min(1).max(200).optional(),
})

export const queryChartFactsContract = defineTool({
  canonical_name: 'query_chart_facts',
  input_schema: inputSchema,
  description:
    'Parametric chart-fact lookup over chart_facts (~2.7k rows × 27 categories). ' +
    'When to prefer: single fact reads ("Saturn shadbala?", "planets in house 7?"). ' +
    'Prefer holistic_bundle for synthesis. Tagged surgical: true.',
  role: 'retrieval',
  family: 'chart',
  data_dependency: 'chart_facts',
  ayanamsha_role: 'canonical',
  annotations: { surgical: true, layer: 'L1' },
})
