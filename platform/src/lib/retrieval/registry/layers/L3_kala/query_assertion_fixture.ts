/** K0a rehearsal only. Serving published generations remains on existing tools. */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

// Also executed against real Postgres by the K0a-4 DB oracle suite.
export const ASSERTION_FIXTURE_SQL = `
SELECT d.assertion_id, d.generation, d.candidate_effective_state,
       d.source_assertion_ids, d.assertion->'roots'->'record_ids' AS record_ids,
       d.assertion, d.interval_start, d.interval_end
FROM kala_darshana d
JOIN kala_layer_candidate c ON c.chart_id = d.chart_id AND c.generation = d.generation
WHERE d.chart_id = $1 AND d.generation = $2
  AND c.conventions->>'fixture' = 'true'
  AND EXISTS (
    SELECT 1 FROM kala_obstruction o
    WHERE o.chart_id = d.chart_id AND o.generation = d.generation
      AND o.assertion_id = d.assertion_id AND o.effective_state = d.candidate_effective_state
  )
  AND jsonb_array_length(d.assertion->'roots'->'record_ids') > 0
  AND NOT EXISTS (
    SELECT 1 FROM jsonb_array_elements_text(d.assertion->'roots'->'record_ids') root(id)
    WHERE NOT EXISTS (
      SELECT 1 FROM kala_gochara_windows w
      WHERE w.id::text = root.id AND w.chart_id = d.chart_id AND w.generation = d.generation
        AND w.source = 'fixture'
    )
  )
ORDER BY d.assertion_id
`

export const queryAssertionFixtureCapability: CapabilityDescriptor = {
  uri: 'marsys://tool/L3/query_kala_assertion_fixture',
  type: 'tool', layer: 'L3', name: 'query_kala_assertion_fixture',
  description: 'Flag-gated K0a rehearsal: returns a pinned fixture candidate assertion with effective state and source ids.',
  scope: 'per_chart', archetype: 'temporal', traversal_level: 'L-SIGNAL', tool_role: 'temporal',
  emits_references: true, grounds_to: { l1_fact_ids: false }, lel_capable: false,
  required_inputs: ['chart_id', 'generation'],
  input_schema: {
    chart_id: { type: 'string', required: true, description: 'Explicit rehearsal chart UUID.' },
    generation: { type: 'string', required: true, description: 'Explicit fixture candidate generation; no default.' },
  },
  async handler(args) {
    if (process.env.KALA_ASSERTION_FIXTURE_ENABLED !== '1') {
      return { content: { error: 'K0a fixture capability is disabled' }, is_error: true }
    }
    const chart = typeof args.chart_id === 'string' ? args.chart_id.trim() : ''
    const generation = typeof args.generation === 'string' ? args.generation.trim() : ''
    if (!chart || !generation) {
      return { content: { error: 'chart_id and generation are required' }, is_error: true }
    }
    try {
      const result = await query(ASSERTION_FIXTURE_SQL, [chart, generation])
      return { content: { chart_id: chart, generation, assertions: result.rows, rehearsal: true }, is_error: false }
    } catch {
      return { content: { error: 'Fixture assertion query failed' }, is_error: true }
    }
  },
}
