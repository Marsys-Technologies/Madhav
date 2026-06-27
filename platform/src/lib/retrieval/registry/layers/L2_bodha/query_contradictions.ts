/**
 * query_contradictions — Contradiction & Discovery Query (L2 Bodha)
 * ==================================================================
 * Surfaces contradictions and discoveries from two sources:
 *   - bodha_contradictions (bo_sangati): 0 rows currently — graceful-empty expected
 *   - bodha_discoveries (bo_anveshana): 1,505 rows
 *   - bodha_anomalies (bo_anveshana): 4,265 rows
 *
 * The 0-row state in bodha_contradictions is the CURRENT EXPECTED STATE (V12b).
 * This tool MUST NOT error on empty contradictions — return empty array + note.
 *
 * Chart-agnostic: no native chart_id defaults (principle #14).
 */

import type { CapabilityDescriptor } from '../../types'

export const queryContradictionsCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L2/query_contradictions',
  type:  'tool',
  layer: 'L2',
  name:  'query_contradictions',

  description: [
    'Returns synthesis contradictions and discovery findings for a chart.',
    'Sources: bodha_contradictions (formal contradiction pairs), bodha_discoveries (synthesis discoveries),',
    'and bodha_anomalies (quality anomalies surfaced during L2 build).',
    'NOTE: bodha_contradictions currently contains 0 rows for all charts — this is expected state',
    '(contradiction writer pending rebuild). Returns empty array, not error.',
    'bodha_discoveries: 1,505 rows ranked by novelty_score.',
    'bodha_anomalies: 4,265 rows covering 5 detector types.',
    'emits_references: returns signal_id pairs from contradiction pairs as reference list.',
  ].join(' '),

  scope: 'per_chart',
  archetype: 'cross_domain',
  traversal_level: 'L-SIGNAL',
  tool_role: 'leaf',
  emits_references: true,
  grounds_to: { l1_fact_ids: true },
  lel_capable: false,

  required_inputs: ['chart_id'],

  input_schema: {
    chart_id: {
      type: 'string',
      description: 'Chart UUID (<chart_uuid>). Required.',
      required: true,
    },
    ayanamsha_id: {
      type: 'string',
      description: "Ayanamsha filter (default: 'LAHIRI').",
    },
    include_discoveries: {
      type: 'boolean',
      description: 'Include bodha_discoveries rows (default: true).',
    },
    include_anomalies: {
      type: 'boolean',
      description: 'Include bodha_anomalies rows (default: false).',
    },
    top_k_discoveries: {
      type: 'number',
      description: 'Max discoveries to return (default: 20, max: 200).',
    },
    min_novelty: {
      type: 'number',
      description: 'Minimum novelty_score for discoveries (0..1, default: 0).',
    },
  },

  llm_hints: {
    agentic: {
      cost_class: 'cheap',
      cacheable:  true,
    },
    bulk_context: {
      pre_fetch_priority: 20,
    },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    const chart_id = args['chart_id'] as string
    if (!chart_id) {
      return { content: { error: 'chart_id is required' }, is_error: true }
    }

    const ayanamsha_id        = (args['ayanamsha_id'] as string | undefined) ?? 'LAHIRI'
    const include_discoveries  = args['include_discoveries'] !== false
    const include_anomalies    = Boolean(args['include_anomalies'] ?? false)
    const top_k_discoveries    = Math.min(Number(args['top_k_discoveries'] ?? 20), 200)
    const min_novelty          = Number(args['min_novelty'] ?? 0)

    try {
      const { db } = _ctx as { db: { query: (sql: string, params: unknown[]) => Promise<{ rows: unknown[] }> } }

      // Contradictions (expected 0 rows — graceful-empty)
      const contraSql = `
        SELECT contradiction_id, signal_a_id, signal_b_id,
               tension_class, domains_affected_array, combined_salience,
               resolution_approach, resolution_status, ayanamsha_id
        FROM bodha_contradictions
        WHERE chart_id = $1 AND ayanamsha_id = $2
        ORDER BY combined_salience DESC NULLS LAST
      `

      const promises: Array<Promise<{ rows: unknown[] }>> = [
        db.query(contraSql, [chart_id, ayanamsha_id]),
      ]

      // Discoveries
      if (include_discoveries) {
        const discoveryFilters = ['chart_id = $1', 'ayanamsha_id = $2']
        const discParams: unknown[] = [chart_id, ayanamsha_id]
        let dp = 3
        if (min_novelty > 0) {
          discoveryFilters.push(`novelty_score >= $${dp++}`)
          discParams.push(min_novelty)
        }
        discParams.push(top_k_discoveries)
        const discSql = `
          SELECT discovery_id, discovery_type, domain, pattern_description,
                 novelty_score, confidence_score, signal_id_refs,
                 supporting_evidence_jsonb, created_at
          FROM bodha_discoveries
          WHERE ${discoveryFilters.join(' AND ')}
          ORDER BY novelty_score DESC NULLS LAST
          LIMIT $${dp}
        `
        promises.push(db.query(discSql, discParams))
      }

      // Anomalies
      if (include_anomalies) {
        const anomSql = `
          SELECT anomaly_id, anomaly_type, severity, description,
                 signal_id_ref, detection_source, created_at
          FROM bodha_anomalies
          WHERE chart_id = $1 AND ayanamsha_id = $2
          ORDER BY severity DESC, created_at DESC
          LIMIT 100
        `
        promises.push(db.query(anomSql, [chart_id, ayanamsha_id]))
      }

      const results = await Promise.all(promises)
      const contraRows = results[0].rows as Array<{ signal_a_id?: string; signal_b_id?: string }>

      // Collect signal refs from contradiction pairs
      const signalRefs = new Set<string>()
      for (const row of contraRows) {
        if (row.signal_a_id) signalRefs.add(row.signal_a_id)
        if (row.signal_b_id) signalRefs.add(row.signal_b_id)
      }

      return {
        content: {
          chart_id,
          ayanamsha_id,
          contradictions:         contraRows,
          contradiction_count:    contraRows.length,
          contradictions_note:    contraRows.length === 0
            ? 'bodha_contradictions contains 0 rows — expected state; contradiction writer rebuild pending.'
            : undefined,
          discoveries:            include_discoveries ? results[1]?.rows ?? [] : undefined,
          discovery_count:        include_discoveries ? (results[1]?.rows?.length ?? 0) : undefined,
          anomalies:              include_anomalies ? results[include_discoveries ? 2 : 1]?.rows ?? [] : undefined,
          signal_id_refs:         Array.from(signalRefs),
          filters: { ayanamsha_id, include_discoveries, include_anomalies, top_k_discoveries, min_novelty },
        },
        is_error: false,
      }
    } catch (err) {
      return {
        content: { error: String(err), chart_id },
        is_error: true,
      }
    }
  },
}
