/**
 * query_life_arc — Life Arc / Biographical Chapters (L3 Kāla)
 * =============================================================
 * Queries kala_jivana_parva (ka_jivana_parva) — 739 rows per chart.
 * Returns daśā-anchored biographical chapter parvas with:
 *   - theme keywords, quality labels (building/peak/consolidating/receding/transitional)
 *   - high-convergence count, dominant signal class
 *
 * Chart-agnostic: no native chart_id defaults (principle #14).
 *
 * shad-darshana/parva-dedup: dedupes rows by (span, level) before pagination — the
 * underlying writer double-emits the antardasha sitting exactly on a mahadasha boundary
 * (see the inline comment on the query below for the root cause).
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

      // shad-darshana/parva-dedup: the ka_jivana_parva writer (python-sidecar) double-emits
      // the boundary antardasha at every mahadasha transition — once (wrongly) as the
      // trailing AD of the outgoing MD, once (correctly) as the leading AD of the incoming
      // MD. This happens because the writer's MD-span filter is inclusive on both ends
      // (`md_start <= d.start_date <= md_end_actual`) and Vimshottari's own-lord-first rule
      // means every MD's first antardasha shares the MD's own lord, so that boundary AD's
      // start_date lands on BOTH adjoining MD spans, producing two rows with the identical
      // (start_year, end_year, dasha_planet) span at the identical AD level (live-confirmed:
      // kala_jivana_parva, charts 482012f1 / 1c826d5a / cb73cd3d, one duplicate pair per
      // MD boundary). Fixing the writer is out of scope for this lane (serving-side fix
      // per SHAD_DARSHANA_BRIEF_v2_0.md §0.5: "dedup by span+level" at serving). `parva_level`
      // is derived from source_citation's MD=/AD=/PD= marker (the table carries no explicit
      // level column) so an MD-level chapter and an AD-level sub-chapter that happen to
      // share a span (e.g. a 1-year terminal MD coinciding with its own last AD) are kept
      // distinct — only true same-span-same-level duplicates collapse. DISTINCT ON retains
      // the highest parva_index per (span, level) group: the later-inserted row is always
      // the correctly-attributed one (the AD nested under its own rightful MD).
      const sql = `
        WITH leveled AS (
          SELECT id, parva_index, dasha_planet, dominant_signal_class,
                 start_year, end_year, parva_quality, theme_keywords,
                 high_convergence_count, avg_effective_score,
                 narrative, source_citation, computed_at,
                 CASE
                   WHEN source_citation ~ ':AD=' THEN 'AD'
                   WHEN source_citation ~ ':PD=' THEN 'PD'
                   ELSE 'MD'
                 END AS parva_level
          FROM kala_jivana_parva
          WHERE ${conds.join(' AND ')}
        ),
        deduped AS (
          SELECT DISTINCT ON (start_year, end_year, dasha_planet, parva_level)
                 id, parva_index, dasha_planet, dominant_signal_class,
                 start_year, end_year, parva_quality, theme_keywords,
                 high_convergence_count, avg_effective_score,
                 narrative, source_citation, computed_at
          FROM leveled
          ORDER BY start_year, end_year, dasha_planet, parva_level, parva_index DESC
        )
        SELECT id, parva_index, dasha_planet, dominant_signal_class,
               start_year, end_year, parva_quality, theme_keywords,
               high_convergence_count, avg_effective_score,
               narrative, source_citation, computed_at
        FROM deduped
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
