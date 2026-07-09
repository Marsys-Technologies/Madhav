/**
 * retrieval/registry/layers/L4_phala/query_muhurat.ts
 *
 * Tool: marsys://tool/L4/query_muhurat — R5.1 C3 (CLAUDECODE_BRIEF_R5_1_MCP_CONSUME_v1_0.md).
 *
 * The REAL backing capability for the MCP `muhurta_finder` tool (per_chart electional
 * auspicious-window finder). Calls the sidecar's already-built PH-4-4 endpoint
 * POST /api/compute/phala/muhurta_finder (brahmagyan/phala/muhurta.py — action_types
 * marriage|travel|business|medical|education|property|general, 48-hour windows,
 * score = panchanga_quality(40%) + dasha_quality(30%) + transit_quality(20%) +
 * signal_activation(10%)), which reads REAL rows from `panchanga_daily` (migration
 * 427_panchanga_daily_reprovision.sql) for its panchanga_quality sub-score.
 *
 * Prior state (found during R5.1 C3 investigation): `query_muhurat` in
 * tool_name_bridge.ts pointed at `marsys://tool/L0/query_planet_transit` — the WRONG
 * capability, entirely unrelated to muhurta search (it requires a `planet` param
 * muhurta_finder never supplies). This capability replaces that mapping so the MCP
 * `muhurta_finder` tool actually reaches the real electional engine.
 *
 * Empty-with-reason: for a date_range fully outside panchanga_daily's populated
 * rolling +12-month window, the sidecar returns `{windows: [], empty_reason: "..."}`
 * — surfaced verbatim here, never fabricated.
 */
import type { CapabilityDescriptor } from '../../types'

const SIDECAR_URL = process.env['PYTHON_SIDECAR_URL'] ?? 'http://localhost:8001'
const SIDECAR_KEY = process.env['PYTHON_SIDECAR_API_KEY'] ?? ''

const VALID_ACTION_TYPES = [
  'marriage', 'travel', 'business', 'medical', 'education', 'property', 'general',
] as const

export const queryMuhuratCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L4/query_muhurat',
  type:  'tool',
  layer: 'L4',
  name:  'query_muhurat',

  description: [
    'Electional auspicious time-window finder (phala.muhurta / PH-4-4). Inverts the',
    'prediction engine: instead of "what will happen?", asks "WHEN is best to act?".',
    'For each 48-hour window in the requested date range (max 90 days), computes',
    'score = panchanga_quality(40%) + dasha_quality(30%) + transit_quality(20%) +',
    'signal_activation(10%), using REAL panchanga_daily rows (tithi/vara/nakshatra/yoga)',
    'for the rolling +12-month populated window. action_types: marriage | travel |',
    'business | medical | education | property | general. Returns windows ranked by',
    'score DESC with source_citation on every window (B.3). For dates outside the',
    'populated panchanga_daily window, returns empty windows + an explicit empty_reason',
    '— never fabricated data.',
  ].join(' '),

  scope: 'per_chart',
  archetype: 'temporal',
  traversal_level: 'L-SIGNAL',
  tool_role: 'temporal',
  emits_references: false,
  grounds_to: { l1_fact_ids: false },
  lel_capable: false,

  required_inputs: ['chart_id', 'action_type', 'date_range'],

  input_schema: {
    chart_id: {
      type: 'string',
      description: 'Chart UUID. Required.',
      required: true,
    },
    action_type: {
      type: 'string',
      description: `One of: ${VALID_ACTION_TYPES.join(' | ')}. Required.`,
      enum: [...VALID_ACTION_TYPES],
      required: true,
    },
    date_range: {
      type: 'object',
      description: "Search range {start, end} (ISO date YYYY-MM-DD). Max 90 days. Required.",
      required: true,
    },
    min_score: {
      type: 'number',
      description: 'Minimum auspiciousness_score [0.0, 1.0]. Default 0.0.',
    },
    limit: {
      type: 'number',
      description: 'Maximum windows to return (default 20, max 45).',
    },
  },

  llm_hints: {
    agentic: { cost_class: 'medium' },
    bulk_context: { pre_fetch_priority: 25 },
  },

  async handler(args: Record<string, unknown>, _ctx?: unknown) {
    const chart_id = args['chart_id'] as string | undefined
    const action_type = args['action_type'] as string | undefined
    const date_range = args['date_range'] as { start?: string; end?: string } | undefined

    if (!chart_id) {
      return { content: { ok: false, error: 'chart_id is required' }, is_error: true }
    }
    if (!action_type || !(VALID_ACTION_TYPES as readonly string[]).includes(action_type)) {
      return {
        content: {
          ok: false,
          error: `action_type must be one of: ${VALID_ACTION_TYPES.join(', ')}`,
        },
        is_error: true,
      }
    }
    if (!date_range?.start || !date_range?.end) {
      return { content: { ok: false, error: 'date_range.start and date_range.end are required' }, is_error: true }
    }

    const body: Record<string, unknown> = {
      chart_id,
      action_type,
      date_range: { start: date_range.start, end: date_range.end },
    }
    if (typeof args['min_score'] === 'number') body['min_score'] = args['min_score']
    if (typeof args['limit'] === 'number') body['limit'] = args['limit']

    try {
      const resp = await fetch(`${SIDECAR_URL}/api/compute/phala/muhurta_finder`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'x-api-key': SIDECAR_KEY },
        body: JSON.stringify(body),
      })
      if (!resp.ok) {
        const errText = await resp.text().catch(() => resp.statusText)
        return {
          content: { ok: false, error: `sidecar ${resp.status}: ${errText.slice(0, 500)}` },
          is_error: true,
        }
      }
      const data = await resp.json()
      return { content: data, is_error: false }
    } catch (err) {
      return { content: { ok: false, error: String(err) }, is_error: true }
    }
  },
}
