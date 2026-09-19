/**
 * query_contradictions — Contradiction & Discovery Query (L2 Bodha)
 * ==================================================================
 * Surfaces contradictions and discoveries from two sources:
 *   - bodha_contradictions (bo_karanajala): populated — 1,034–1,100 rows per ayanamsha per chart
 *   - bodha_discoveries (bo_anveshana): rows ranked by composite_discovery_rank
 *   - bodha_anomalies (bo_anveshana): rows covering detector types
 *
 * Chart-agnostic: no native chart_id defaults (principle #14).
 */

import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'
import { sourceQueryAvailabilityRequirement } from '../../knowledge/source_query_availability'

const DEFAULT_DISCOVERY_LIMIT = 20
const MAX_DISCOVERY_LIMIT = 200

function normalizeDiscoveryLimit(value: unknown): number {
  const parsed = typeof value === 'number' ? value : Number(value)
  if (!Number.isFinite(parsed)) return DEFAULT_DISCOVERY_LIMIT
  const normalized = Math.floor(parsed)
  return normalized >= 1 ? Math.min(normalized, MAX_DISCOVERY_LIMIT) : DEFAULT_DISCOVERY_LIMIT
}

function normalizeMinimumNovelty(value: unknown): number {
  const parsed = typeof value === 'number' ? value : Number(value)
  if (!Number.isFinite(parsed)) return 0
  return Math.min(Math.max(parsed, 0), 1)
}

function rowsMatchSelectedBuild(rows: readonly unknown[], buildId: string): boolean {
  return rows.every((row) => typeof row === 'object' && row !== null
    && !Array.isArray(row) && (row as Record<string, unknown>)['build_id'] === buildId)
}

export const queryContradictionsCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L2/query_contradictions',
  type:  'tool',
  layer: 'L2',
  name:  'query_contradictions',

  description: [
    'Returns synthesis contradictions and discovery findings for a chart.',
    'Sources: bodha_contradictions (formal yoga-vs-dosha tension pairs), bodha_discoveries (synthesis discoveries),',
    'and bodha_anomalies (quality anomalies surfaced during L2 build).',
    'bodha_contradictions: populated — a moderate row count per ayanamsha per chart (built by bo_karanajala).',
    'bodha_discoveries: rows ranked by composite_discovery_rank (non_obviousness_score gated).',
    'bodha_anomalies: rows covering detector types.',
    'Graceful-empty: when a chart/ayanamsha combination has no qualifying contradictions, discoveries, or anomalies, this returns 0 rows for that source rather than erroring — an honest empty state, not a fault.',
    'emits_references: returns signal_id pairs from contradiction pairs as reference list.',
  ].join(' '),

  scope: 'per_chart',
  archetype: 'cross_domain',
  traversal_level: 'L-SIGNAL',
  tool_role: 'leaf',
  emits_references: true,
  grounds_to: { l1_fact_ids: true },
  lel_capable: false,
  // PB-1/S-2: reader-facing working-band label — closed lexicon, never a bespoke string.
  // Band phase 4 ("Reading the whole chart") — B.11 whole-chart-read (CDLM contradictions).
  register: { reader_label: 'Reading the whole chart' },

  semantic_capabilities: [{
    scu_id: 'scu.catalog.query_contradictions',
    version: 1,
    label: 'Chart contradiction evidence',
    description: 'Retrieve formal chart-scoped contradiction pairs. Discoveries and anomalies are supplemental and do not satisfy contradiction closure.',
    kind: 'contradiction',
    domains: ['cross_domain'],
    concepts: ['query_contradictions', 'contradiction', 'tension', 'evidence_reconciliation'],
    intents: ['assess', 'reconcile', 'verify'],
    horizons: ['natal', 'current'],
    scope: 'chart',
    inputs: ['chart_id', 'ayanamsha_id?', 'include_discoveries?', 'include_anomalies?', 'top_k_discoveries?', 'min_novelty?'],
    outputs: ['contradictions', 'contradiction_count', 'signal_id_refs', 'build_id', 'generation_provenance'],
    primary_binding_uri: 'marsys://tool/L2/query_contradictions',
    primary_binding_details: {
      pagination: 'none',
      pagination_contract: {
        result_collection_path: 'content.contradictions',
        deterministic_order: ['combined_salience DESC NULLS LAST', 'contradiction_id ASC'],
      },
      route_evidence: 'platform/src/lib/retrieval/registry/layers/L2_bodha/query_contradictions.ts:156-269',
    },
    provenance_requirements: ['chart_id', 'build_id', 'formula_or_writer_version'],
    freshness_policy: 'Requires a source query against the selected chart and active completed build context.',
    entitlement: 'native',
    safety_notes: ['Read-only evidence surface; planner must not interpret returned chart facts.'],
    known_gaps: [
      'Discoveries and anomalies are supplemental result legs; their caps and empty states do not prove contradiction exhaustion or closure.',
      'No public MCP alias is asserted by this declaration.',
    ],
    availability_contracts: [{
      binding_id: 'registry:marsys://tool/L2/query_contradictions',
      requirements: [sourceQueryAvailabilityRequirement('source-query:query-contradictions:v1')!],
    }],
    editorial: true,
  }],

  required_inputs: ['chart_id'],

  input_schema: {
    chart_id: {
      type: 'string',
      description: 'Chart UUID (<chart_uuid>). Required.',
      required: true,
    },
    ayanamsha_id: {
      type: 'string',
      description: "Ayanamsha filter (default: 'lahiri_chitrapaksha').",
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
      description: 'Minimum non_obviousness_score for discoveries (0..1, default: 0).',
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

    const ayanamsha_id        = (args['ayanamsha_id'] as string | undefined) ?? 'lahiri_chitrapaksha'
    const include_discoveries  = args['include_discoveries'] !== false
    const include_anomalies    = Boolean(args['include_anomalies'] ?? false)
    const top_k_discoveries    = normalizeDiscoveryLimit(args['top_k_discoveries'] ?? DEFAULT_DISCOVERY_LIMIT)
    const min_novelty          = normalizeMinimumNovelty(args['min_novelty'] ?? 0)

    void _ctx
    try {
      const activeBuildResult = await query<{ build_id: string }>(`
        SELECT id::text AS build_id
          FROM build_runs
         WHERE chart_id = $1::uuid AND state = 'completed'
         ORDER BY ended_at DESC NULLS LAST, id DESC
         LIMIT 1
      `, [chart_id])
      const build_id = activeBuildResult.rows[0]?.build_id
      if (!build_id) {
        return {
          content: {
            code: 'active_completed_build_unavailable',
            error: 'No active completed build is available for this chart; contradiction evidence cannot be selected safely.',
            chart_id,
          },
          is_error: true,
        }
      }

      const contraSql = `
        SELECT contradiction_id, signal_a_id, signal_b_id,
               tension_class, domains_affected_array, combined_salience,
               resolution_hint_jsonb, ayanamsha_id, build_id
        FROM bodha_contradictions
        WHERE chart_id = $1 AND ayanamsha_id = $2 AND build_id = $3::uuid
        ORDER BY combined_salience DESC NULLS LAST, contradiction_id ASC
      `

      const promises: Array<Promise<{ rows: unknown[] }>> = [
        query<Record<string, unknown>>(contraSql, [chart_id, ayanamsha_id, build_id]),
      ]

      // Discoveries
      if (include_discoveries) {
        const discoveryFilters = ['chart_id = $1', 'ayanamsha_id = $2', 'build_id = $3::uuid']
        const discParams: unknown[] = [chart_id, ayanamsha_id, build_id]
        let dp = 4
        if (min_novelty > 0) {
          discoveryFilters.push(`non_obviousness_score >= $${dp++}`)
          discParams.push(min_novelty)
        }
        discParams.push(top_k_discoveries)
        const discSql = `
          SELECT discovery_id, discovery_class, discovery_subsystem,
                 affected_domains_array, hypothesis_text,
                 non_obviousness_score, consequence_score,
                 composite_discovery_rank, constituent_refs_jsonb, computed_at, build_id
          FROM bodha_discoveries
          WHERE ${discoveryFilters.join(' AND ')}
          ORDER BY composite_discovery_rank DESC NULLS LAST
          LIMIT $${dp}
        `
        promises.push(query<Record<string, unknown>>(discSql, discParams))
      }

      // Anomalies
      if (include_anomalies) {
        const anomSql = `
          SELECT anomaly_id, anomaly_type, discovery_subsystem,
                 subject_ref_jsonb, anomaly_metric, anomaly_value,
                 chart_baseline_value, sigma_from_baseline,
                 meaningfulness_gate_result, computed_at, build_id
          FROM bodha_anomalies
          WHERE chart_id = $1 AND ayanamsha_id = $2 AND build_id = $3::uuid
          ORDER BY sigma_from_baseline DESC NULLS LAST, computed_at DESC
          LIMIT 100
        `
        promises.push(query<Record<string, unknown>>(anomSql, [chart_id, ayanamsha_id, build_id]))
      }

      const results = await Promise.all(promises)
      const contraRows = results[0].rows as Array<{ signal_a_id?: string; signal_b_id?: string }>
      const selectedRows = [
        contraRows,
        ...(include_discoveries ? [results[1]?.rows ?? []] : []),
        ...(include_anomalies ? [results[include_discoveries ? 2 : 1]?.rows ?? []] : []),
      ]
      if (!selectedRows.every((rows) => rowsMatchSelectedBuild(rows, build_id))) {
        return {
          content: {
            code: 'active_build_provenance_mismatch',
            error: 'A contradiction source row did not match the selected active completed build.',
            chart_id,
            build_id,
          },
          is_error: true,
        }
      }

      // Collect signal refs from contradiction pairs
      const signalRefs = new Set<string>()
      for (const row of contraRows) {
        if (row.signal_a_id) signalRefs.add(row.signal_a_id)
        if (row.signal_b_id) signalRefs.add(row.signal_b_id)
      }

      return {
        content: {
          chart_id,
          build_id,
          generation_provenance: { build_id, relation_scope: 'selected_active_completed_build' },
          ayanamsha_id,
          contradictions:         contraRows,
          contradiction_count:    contraRows.length,
          contradictions_note:    contraRows.length === 0
            ? `bodha_contradictions: 0 rows for chart_id=${chart_id} ayanamsha_id=${ayanamsha_id}. Verify the chart has been built (bo_karanajala) and ayanamsha_id is correct.`
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
