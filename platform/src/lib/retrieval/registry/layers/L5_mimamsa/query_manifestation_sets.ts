/**
 * query_manifestation_sets — L5 Mīmāṃsā prediction-manifestation channels (mimamsa_manifestation_sets)
 * ============================================================================================================
 * W2b Batch 4 dark-set wiring (TABLE_CONCEPT_DISPOSITIONS_v2_0.md SERVE-gap set,
 * `mimamsa_manifestation_sets`, migration 347_mimamsa_bhavisya.sql). Records which
 * channel/domain a frozen prediction manifested through, with a citation_ref and an
 * is_literal flag. DISTINCT from `mimamsa_manifestation_grammar` (mi_sambandha, already
 * served via `query_manifestation_grammar.ts` / `marsys://tool/L5/query_manifestation_grammar`)
 * — that table is per-native channel-propensity grammar; this one is per-prediction
 * manifestation-channel record. Confirmed distinct tables via migration DDL (347 vs a
 * different migration entirely) before writing this capability, to avoid conflating the two.
 * Not read by query_predictions.ts or any other outcome tool checked.
 *
 * Chart-scoped. Bounded serving with disclosed total.
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

const MAX_LIMIT = 100

export const queryManifestationSetsCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L5/query_manifestation_sets',
  type:  'tool',
  layer: 'L5',
  name:  'query_manifestation_sets',

  description: [
    'Retrieve prediction-manifestation-channel records from mimamsa_manifestation_sets',
    '(mi_bhavisya) — NOT mimamsa_manifestation_grammar (a different table; see',
    'query_manifestation_grammar for that). Each row: prediction_id, channel_id, domain,',
    'source, citation_ref, is_literal (whether the manifestation was literal vs symbolic),',
    'frozen_at. Answers "through which channel(s) did this frozen prediction actually',
    `manifest?" Filters: prediction_id, domain, channel_id. Bounded to ${MAX_LIMIT} rows`,
    'with a disclosed total.',
  ].join(' '),

  input_schema: {
    chart_id:      { type: 'string', description: 'Chart UUID. Required.', required: true },
    prediction_id: { type: 'string', description: 'Filter by prediction_id. Omit for all.' },
    domain:        { type: 'string', description: 'Filter by domain. Omit for all.' },
    channel_id:    { type: 'string', description: 'Filter by channel_id. Omit for all.' },
    limit:         { type: 'number', description: `Max rows (default ${MAX_LIMIT}, max ${MAX_LIMIT}).` },
  },

  required_inputs: ['chart_id'],
  scope: 'per_chart',
  archetype: 'calibration',
  traversal_level: 'L-DOMAIN',
  tool_role: 'quality',
  emits_references: true,
  grounds_to: { l1_fact_ids: false },
  lel_capable: false,
  llm_hints: {
    agentic: { cost_class: 'cheap', cacheable: true },
    bulk_context: { pre_fetch_priority: 20, always_include: false },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    void _ctx
    const chart_id = args['chart_id'] ? String(args['chart_id']) : ''
    if (!chart_id) return { content: { error: 'chart_id is required' }, is_error: true }

    const predictionId = args['prediction_id'] ? String(args['prediction_id']) : null
    const domain       = args['domain'] ? String(args['domain']) : null
    const channelId    = args['channel_id'] ? String(args['channel_id']) : null
    const limit = Math.min(Math.max(Number(args['limit'] ?? MAX_LIMIT), 1), MAX_LIMIT)

    const filters: string[] = ['chart_id = $1']
    const params: unknown[] = [chart_id]
    let p = 2
    if (predictionId) { filters.push(`prediction_id = $${p++}`); params.push(predictionId) }
    if (domain)       { filters.push(`domain = $${p++}`); params.push(domain) }
    if (channelId)    { filters.push(`channel_id = $${p++}`); params.push(channelId) }
    const where = filters.join(' AND ')

    const sql = `
      SELECT prediction_id, channel_id, domain, source, citation_ref, is_literal,
             to_char(frozen_at, 'YYYY-MM-DD"T"HH24:MI:SSZ') AS frozen_at
      FROM mimamsa_manifestation_sets
      WHERE ${where}
      ORDER BY frozen_at DESC
      LIMIT $${p}`

    try {
      const [rowsRes, countRes] = await Promise.all([
        query(sql, [...params, limit]),
        query<{ total: string }>(`SELECT COUNT(*)::text AS total FROM mimamsa_manifestation_sets WHERE ${where}`, params),
      ])
      const total_matching = Number(countRes.rows[0]?.total ?? 0)
      return {
        content: {
          chart_id,
          rows: rowsRes.rows,
          count: rowsRes.rows.length,
          total_matching,
          more_available: total_matching > rowsRes.rows.length,
          filters: { prediction_id: predictionId, domain, channel_id: channelId, limit },
          ...(rowsRes.rows.length === 0
            ? { empty_reason: `No manifestation-set rows matched (prediction_id=${predictionId ?? 'any'}, domain=${domain ?? 'any'}, channel_id=${channelId ?? 'any'}).` }
            : {}),
          provenance: { tables: ['mimamsa_manifestation_sets'], source: 'L5 Mīmāṃsā prediction-manifestation-channel records (mi_bhavisya), distinct from mimamsa_manifestation_grammar; served chart-scoped.' },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err), chart_id }, is_error: true }
    }
  },
}
