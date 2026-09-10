/**
 * query_signal_families — Signal Family Registry (L5 Mīmāṃsā)
 * ==============================================================
 * Queries mimamsa_signal_families (mi_kula) — global catalog, no chart_id.
 * Returns signal-family registry + negative-control battery.
 *
 * scope: 'global' — no chart_id required or meaningful.
 * emits_references: false — returns family catalog data directly.
 * Chart-agnostic: this is a global reference tool (principle #14 N/A for global scope).
 */

import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

export const querySignalFamiliesCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L5/query_signal_families',
  type:  'tool',
  layer: 'L5',
  name:  'query_signal_families',

  description: [
    'Returns the signal-family registry from mimamsa_signal_families (mi_kula).',
    'Global scope — not chart-specific. Returns all signal families.',
    'Signal families define the structural groupings (family_class: classical, msr, negative_control, etc.)',
    'with evidence_tier, soundness_basis, binding_kind, prior_weight and calibration_status.',
    'Negative-control families (family_class = negative_control) are the calibration-test baselines;',
    'the per-control battery itself lives in mimamsa_negative_controls (separate table).',
    'Used by the L5 calibration harness. No chart_id required.',
  ].join(' '),

  scope: 'global',
  archetype: 'calibration',
  traversal_level: 'L-OVERVIEW',
  tool_role: 'quality',
  emits_references: false,
  grounds_to: { l1_fact_ids: false },
  lel_capable: false,

  input_schema: {
    display_name: {
      type: 'string',
      description: 'Filter by specific family display name.',
    },
    family_class: {
      type: 'string',
      description: 'Filter by family class (e.g. classical, msr, negative_control).',
    },
    include_negative_controls: {
      type: 'boolean',
      description: "Include negative-control families (family_class = 'negative_control'); default: true.",
    },
    top_k: {
      type: 'number',
      description: 'Max families to return (default: all, max: 200).',
    },
  },

  llm_hints: {
    agentic: { cost_class: 'cheap', cacheable: true },
    bulk_context: { pre_fetch_priority: 40 },
  },

  // NIRMĀṆA L5 W3-3 (§N.6 Serving Density Principle / plan §2 D-SERVICE P8).
  // Bounded LIMIT over a clamped `top_k` with a disclosed total_matching + more_available
  // (both added this pass alongside the empty_reason the handler now emits).
  density_contract: {
    paginated: true,
    facets: ['display_name', 'family_class', 'include_negative_controls'],
    empty_reason: true,
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    const display_name        = args['display_name'] as string | undefined
    const family_class        = args['family_class'] as string | undefined
    const include_neg_ctrl    = args['include_negative_controls'] !== false
    const top_k               = Math.min(Number(args['top_k'] ?? 200), 200)

    try {
      const conds: string[] = []
      const params: unknown[] = []
      let p = 1

      if (display_name)  { conds.push(`display_name = $${p++}`); params.push(display_name) }
      if (family_class)  { conds.push(`family_class = $${p++}`); params.push(family_class) }
      if (!include_neg_ctrl) { conds.push(`family_class <> 'negative_control'`) }

      const where = conds.length > 0 ? `WHERE ${conds.join(' AND ')}` : ''
      const countParams = [...params]
      params.push(top_k)

      const sql = `
        SELECT family_id, display_name, layman_name, family_class,
               evidence_tier, soundness_basis, binding_kind, default_state,
               prior_weight, calibration_status, citation_refs, binding_spec,
               apply_point, is_active, created_at
        FROM mimamsa_signal_families
        ${where}
        ORDER BY family_class, display_name
        LIMIT $${p}
      `

      // Family size BEFORE the LIMIT, same filters as the page (§N.6 item 4 — density
      // signaling is data): a caller must be able to tell a complete catalog from a
      // truncated one without re-deriving it from the row count.
      const [result, countResult] = await Promise.all([
        query(sql, params),
        query<{ total: string }>(
          `SELECT COUNT(*)::text AS total FROM mimamsa_signal_families ${where}`,
          countParams,
        ),
      ])
      const total_matching = Number(countResult.rows[0]?.total ?? 0)

      return {
        content: {
          signal_families:  result.rows,
          family_count:     result.rows.length,
          total_matching,
          more_available:   total_matching > result.rows.length,
          // §N.6 item 3: an honest empty is reported, never served as a hollow envelope.
          ...(result.rows.length === 0
            ? {
                empty_reason:
                  `No signal families matched (display_name=${display_name ?? 'any'}, ` +
                  `family_class=${family_class ?? 'any'}, ` +
                  `include_negative_controls=${include_neg_ctrl}). mimamsa_signal_families is a ` +
                  'GLOBAL catalog, so an empty result means the filters matched nothing in the ' +
                  'registry — it is never a chart-scoping artefact.',
              }
            : {}),
          filters: { display_name, family_class, include_negative_controls: include_neg_ctrl, top_k },
          provenance: {
            tables: ['mimamsa_signal_families'],
            source: 'L5 Mīmāṃsā signal-family registry (mi_kula); global catalog, not chart-scoped.',
          },
        },
        is_error: false,
      }
    } catch (err) {
      return {
        content: { error: String(err) },
        is_error: true,
      }
    }
  },
}
