/**
 * query_life_arc — Life Arc / Biographical Chapters (L3 Kāla)
 * =============================================================
 * Queries kala_jivana_parva (ka_jivana_parva) — 739 rows per chart.
 * Returns daśā-anchored biographical chapter parvas with:
 *   - theme keywords, quality labels (building/peak/consolidating/receding/transitional)
 *   - high-convergence count, dominant signal class
 *
 * Chart-agnostic: no native chart_id defaults (principle #14).
 */

import { query } from '@/lib/db/client'
import type { CapabilityDescriptor } from '../../types'

export const queryLifeArcCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L3/query_life_arc',
  type:  'tool',
  layer: 'L3',
  name:  'query_life_arc',

  description: [
    'Returns biographical life-arc chapters (parvas) for a chart from kala_jivana_parva.',
    'Each parva is anchored to a dasha period (dasha_planet) with theme keywords,',
    'quality label (building/peak/consolidating/receding/transitional), and high-convergence count.',
    'Total: 739 rows per chart covering the full life arc.',
    'Filter by mahadasha_lord (matches dasha_planet) to focus on a specific major period.',
  ].join(' '),

  scope: 'per_chart',
  archetype: 'temporal',
  traversal_level: 'L-DOMAIN',
  tool_role: 'drill',
  emits_references: false,
  grounds_to: { l1_fact_ids: true },
  lel_capable: false,
  // PB-1/S-2: reader-facing working-band label — closed lexicon, never a bespoke string.
  register: { reader_label: 'Consulting the chart — Daśā structure' },

  required_inputs: ['chart_id'],

  input_schema: {
    chart_id: {
      type: 'string',
      description: 'Chart UUID (<chart_uuid>). Required.',
      required: true,
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
    offset: {
      type: 'number',
      description: 'Pagination offset (default: 0). Applied after ORDER BY parva_index.',
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

    const mahadasha_lord = args['mahadasha_lord'] as string | undefined
    const quality_label  = args['quality_label'] as string | undefined
    const domain         = args['domain'] as string | undefined
    const date_from      = args['date_from'] as string | undefined
    const date_to        = args['date_to'] as string | undefined
    const top_k          = Math.min(Number(args['top_k'] ?? 739), 739)
    const offset         = Math.max(Number(args['offset'] ?? 0), 0)

    // kala_jivana_parva models the period as integer life years (start_year/end_year),
    // not dates. Map any ISO date filters to their year component for overlap filtering.
    const year_from = date_from ? new Date(date_from).getUTCFullYear() : undefined
    const year_to   = date_to ? new Date(date_to).getUTCFullYear() : undefined

    try {
      const conds: string[] = ['chart_id = $1']
      const params: unknown[] = [chart_id]
      let p = 2

      // mahadasha_lord → dasha_planet; quality_label → parva_quality;
      // domain → dominant_signal_class (closest real column on this table).
      if (mahadasha_lord)         { conds.push(`dasha_planet = $${p++}`);          params.push(mahadasha_lord) }
      if (quality_label)          { conds.push(`parva_quality = $${p++}`);         params.push(quality_label) }
      if (domain)                 { conds.push(`dominant_signal_class = $${p++}`); params.push(domain) }
      if (year_from !== undefined) { conds.push(`end_year >= $${p++}`);            params.push(year_from) }
      if (year_to !== undefined)   { conds.push(`start_year <= $${p++}`);          params.push(year_to) }

      params.push(top_k)
      const topKPh = `$${p++}`
      params.push(offset)
      const offsetPh = `$${p}`

      const sql = `
        SELECT id, parva_index, dasha_planet, dominant_signal_class,
               start_year, end_year, parva_quality, theme_keywords,
               high_convergence_count, avg_effective_score,
               narrative, source_citation, computed_at
        FROM kala_jivana_parva
        WHERE ${conds.join(' AND ')}
        ORDER BY parva_index
        LIMIT ${topKPh} OFFSET ${offsetPh}
      `

      const result = await query(sql, params)

      return {
        content: {
          chart_id,
          parvas:       result.rows,
          parva_count:  result.rows.length,
          filters: { mahadasha_lord, quality_label, domain, date_from, date_to, top_k, offset },
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
