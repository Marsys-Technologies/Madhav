/**
 * query_life_arc — Life Arc / Biographical Chapters (L3 Kāla)
 * =============================================================
 * Queries kala_jivana_parva (ka_jivana_parva) — 739 rows per chart.
 * Returns daśā-anchored biographical chapter parvas with:
 *   - theme keywords, quality labels (building/peak/consolidating/receding/transitional)
 *   - convergence density, dominant domain
 *
 * emits_references: true (signal_id back to bo_laksana via activation link).
 * Chart-agnostic: no native chart_id defaults (principle #14).
 */

import type { CapabilityDescriptor } from '../../types'

export const queryLifeArcCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L3/query_life_arc',
  type:  'tool',
  layer: 'L3',
  name:  'query_life_arc',

  description: [
    'Returns biographical life-arc chapters (parvas) for a chart from kala_jivana_parva.',
    'Each parva is anchored to a mahadasha/antardasha period with theme keywords,',
    'quality label (building/peak/consolidating/receding/transitional), and convergence density.',
    'Total: 739 rows per chart covering the full life arc.',
    'Filter by mahadasha_lord to focus on a specific major period.',
    'Returns signal_id references into bodha_msr_signals via activation links.',
  ].join(' '),

  scope: 'per_chart',
  archetype: 'temporal',
  traversal_level: 'L-DOMAIN',
  tool_role: 'drill',
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
    mahadasha_lord: {
      type: 'string',
      description: "Filter by mahadasha lord (e.g. 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury', 'Ketu', 'Venus').",
      enum: ['Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury', 'Ketu', 'Venus'],
    },
    quality_label: {
      type: 'string',
      description: 'Filter by quality label.',
      enum: ['building', 'peak', 'consolidating', 'receding', 'transitional'],
    },
    domain: {
      type: 'string',
      description: 'Filter by dominant domain (career, wealth, relationship, health, character, spirituality, other).',
    },
    date_from: {
      type: 'string',
      description: 'Filter parvas whose period overlaps after this date (ISO 8601).',
    },
    date_to: {
      type: 'string',
      description: 'Filter parvas whose period overlaps before this date (ISO 8601).',
    },
    top_k: {
      type: 'number',
      description: 'Max parvas to return (default: 739 = all, max: 739).',
    },
  },

  llm_hints: {
    agentic: {
      cost_class: 'cheap',
      cacheable:  true,
    },
    bulk_context: {
      pre_fetch_priority: 15,
    },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    const chart_id = args['chart_id'] as string
    if (!chart_id) {
      return { content: { error: 'chart_id is required' }, is_error: true }
    }

    const ayanamsha_id   = (args['ayanamsha_id'] as string | undefined) ?? 'LAHIRI'
    const mahadasha_lord = args['mahadasha_lord'] as string | undefined
    const quality_label  = args['quality_label'] as string | undefined
    const domain         = args['domain'] as string | undefined
    const date_from      = args['date_from'] as string | undefined
    const date_to        = args['date_to'] as string | undefined
    const top_k          = Math.min(Number(args['top_k'] ?? 739), 739)

    try {
      const { db } = _ctx as { db: { query: (sql: string, params: unknown[]) => Promise<{ rows: unknown[] }> } }

      const conds: string[] = ['chart_id = $1', 'ayanamsha_id = $2']
      const params: unknown[] = [chart_id, ayanamsha_id]
      let p = 3

      if (mahadasha_lord) { conds.push(`mahadasha_lord = $${p++}`); params.push(mahadasha_lord) }
      if (quality_label)  { conds.push(`quality_label = $${p++}`);  params.push(quality_label) }
      if (domain)         { conds.push(`dominant_domain = $${p++}`); params.push(domain) }
      if (date_from)      { conds.push(`period_end >= $${p++}`);    params.push(date_from) }
      if (date_to)        { conds.push(`period_start <= $${p++}`);  params.push(date_to) }

      params.push(top_k)
      const topKPh = `$${p}`

      const sql = `
        SELECT parva_id, mahadasha_lord, antardasha_lord, pratyantar_lord,
               period_start, period_end, quality_label, dominant_domain,
               convergence_density, theme_keywords_array, signal_id_refs,
               chapter_weight, narrative_summary, ayanamsha_id
        FROM kala_jivana_parva
        WHERE ${conds.join(' AND ')}
        ORDER BY period_start
        LIMIT ${topKPh}
      `

      const result = await db.query(sql, params)

      const signalRefs = new Set<string>()
      for (const row of result.rows as Array<{ signal_id_refs?: string[] }>) {
        if (row.signal_id_refs) {
          for (const id of row.signal_id_refs) signalRefs.add(id)
        }
      }

      return {
        content: {
          chart_id,
          ayanamsha_id,
          parvas:       result.rows,
          parva_count:  result.rows.length,
          signal_id_refs: Array.from(signalRefs),
          filters: { mahadasha_lord, quality_label, domain, date_from, date_to, top_k },
          provenance: { tables: ['kala_jivana_parva'] },
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
