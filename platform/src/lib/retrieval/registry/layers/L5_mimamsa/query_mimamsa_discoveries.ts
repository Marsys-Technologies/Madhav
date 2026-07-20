/**
 * query_mimamsa_discoveries — L5 Mīmāṃsā research-value discoveries (mimamsa_discoveries)
 * ===============================================================================================
 * W2b Batch 4 dark-set wiring (TABLE_CONCEPT_DISPOSITIONS_v2_0.md SERVE-gap set,
 * `mimamsa_discoveries`, migration 351_mimamsa_pariksha.sql). Emergent laws / contradiction
 * dominance patterns / temporal rhythms / residual candidates the L5 calibration system has
 * surfaced — directly relevant to CLAUDE.md §A's "research tool for astrology as a
 * discipline" goal.
 *
 * NOTE: distinct from the already-served L2 `bodha_discoveries` (see
 * `query_discoveries.ts` in L2_bodha, confirmed via TABLE_CONCEPT_DISPOSITIONS_v2_0.md §6
 * — do not conflate; hence this file/capability is named `query_mimamsa_discoveries`, not
 * `query_discoveries`, to avoid any symbol/URI collision with the L2 capability).
 *
 * Chart-scoped. Bounded serving with disclosed total.
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

const MAX_LIMIT = 50

export const queryMimamsaDiscoveriesCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L5/query_mimamsa_discoveries',
  type:  'tool',
  layer: 'L5',
  name:  'query_mimamsa_discoveries',

  description: [
    'Retrieve L5 research-value discoveries from mimamsa_discoveries (mi_pariksha) —',
    'NOT the L2 bodha_discoveries table (a different concept; see bodha_discoveries_get',
    'for that). Each row: discovery_class (emergent_law|contradiction_dominance|',
    'temporal_rhythm|residual_candidate), statement, evidence_refs, strength, n_support,',
    'confidence_band, activation_status (candidate|supported|promoted), citation_ref.',
    'Filters: discovery_class, activation_status.',
    `Bounded to ${MAX_LIMIT} rows with a disclosed total.`,
  ].join(' '),

  input_schema: {
    chart_id:          { type: 'string', description: 'Chart UUID. Required.', required: true },
    discovery_class:    { type: 'string', description: 'Filter by discovery_class (emergent_law|contradiction_dominance|temporal_rhythm|residual_candidate). Omit for all.', enum: ['emergent_law', 'contradiction_dominance', 'temporal_rhythm', 'residual_candidate'] },
    activation_status:  { type: 'string', description: 'Filter by activation_status (candidate|supported|promoted). Omit for all.', enum: ['candidate', 'supported', 'promoted'] },
    limit:              { type: 'number', description: `Max rows (default ${MAX_LIMIT}, max ${MAX_LIMIT}).` },
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
    bulk_context: { pre_fetch_priority: 25, always_include: false },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    void _ctx
    const chart_id = args['chart_id'] ? String(args['chart_id']) : ''
    if (!chart_id) return { content: { error: 'chart_id is required' }, is_error: true }

    const discoveryClass   = args['discovery_class'] ? String(args['discovery_class']) : null
    const activationStatus = args['activation_status'] ? String(args['activation_status']) : null
    const limit = Math.min(Math.max(Number(args['limit'] ?? MAX_LIMIT), 1), MAX_LIMIT)

    const filters: string[] = ['chart_id = $1']
    const params: unknown[] = [chart_id]
    let p = 2
    if (discoveryClass)   { filters.push(`discovery_class = $${p++}`); params.push(discoveryClass) }
    if (activationStatus) { filters.push(`activation_status = $${p++}`); params.push(activationStatus) }
    const where = filters.join(' AND ')

    const sql = `
      SELECT discovery_id, discovery_class, statement, evidence_refs, strength, n_support,
             confidence_band, activation_status, citation_required, citation_ref,
             discovery_formula_ver
      FROM mimamsa_discoveries
      WHERE ${where}
      ORDER BY strength DESC NULLS LAST
      LIMIT $${p}`

    try {
      const [rowsRes, countRes] = await Promise.all([
        query(sql, [...params, limit]),
        query<{ total: string }>(`SELECT COUNT(*)::text AS total FROM mimamsa_discoveries WHERE ${where}`, params),
      ])
      const total_matching = Number(countRes.rows[0]?.total ?? 0)
      return {
        content: {
          chart_id,
          rows: rowsRes.rows,
          count: rowsRes.rows.length,
          total_matching,
          more_available: total_matching > rowsRes.rows.length,
          filters: { discovery_class: discoveryClass, activation_status: activationStatus, limit },
          ...(rowsRes.rows.length === 0
            ? { empty_reason: `No L5 discovery rows matched (discovery_class=${discoveryClass ?? 'any'}, activation_status=${activationStatus ?? 'any'}).` }
            : {}),
          provenance: { tables: ['mimamsa_discoveries'], source: 'L5 Mīmāṃsā research-value discoveries (mi_pariksha), distinct from L2 bodha_discoveries; served chart-scoped.' },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err), chart_id }, is_error: true }
    }
  },
}
