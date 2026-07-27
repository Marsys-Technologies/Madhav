/**
 * query_projections — Forward Projections (L3 Kāla)
 * ===================================================
 * Queries kala_bhavishya (ka_bhavishya_lekha) — up to ~100 rows per chart.
 * Returns probabilistic forward projections with domain labels,
 * peak_date / window bounds, falsifiability hooks, and source chains.
 *
 * Chart-agnostic: no native chart_id defaults (principle #14).
 *
 * MC-015/026 (ŚODHANA T8): the raw `projections` rows are frequently MANY rows
 * sharing the exact same resolved (window_start, window_end, domain) — e.g. a
 * chart can carry ~87 "general"-domain rows all spanning the same single window,
 * one real finding served dozens of times. `projection_families` collapses rows
 * sharing an identical (window_start, window_end, domain) key into one entry with
 * bounded member refs (member_ids, member_signal_ids) — copying
 * query_temporal_activation's `window_families` structural pattern.
 */

import { query } from '@/lib/db/client'
import type { CapabilityDescriptor } from '../../types'

interface ProjectionFamilyRow {
  window_start: string | null
  window_end: string | null
  domain: string | null
  member_count: string | number
  member_ids: string[] | null
  member_signal_ids: string[] | null
  probability_tier: string | null
  max_effective_score: string | number | null
  narrative: unknown
  source_citation: string | null
}

export const queryProjectionsCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L3/query_projections',
  type:  'tool',
  layer: 'L3',
  name:  'query_projections',

  description: [
    'Returns probabilistic forward projections for a chart from kala_bhavishya.',
    'Source: kala_bhavishya (50 rows — spanning multiple years and domains).',
    'Each projection carries: domain, probability_tier, peak_date, window_start/window_end,',
    'falsifiability hook, source_chain, effective_score, and narrative.',
    'Filter by probability_tier: tier_1_high (≥0.65), tier_2_moderate (0.40–0.65),',
    'tier_3_speculative (<0.40).',
    'emits_references: returns signal_id references linkable to bo_laksana / ph_pramana (L4).',
    'MC-015/026: the raw `projections` array frequently repeats the SAME resolved window many',
    'times (one per contributing signal) — e.g. dozens of rows can share one (window_start,',
    'window_end, domain) triple. Prefer `projection_families` — one entry per distinct',
    '(window_start, window_end, domain), with member_count and bounded member_ids/',
    'member_signal_ids — copying query_temporal_activation\'s window_families pattern.',
  ].join(' '),

  scope: 'per_chart',
  archetype: 'temporal',
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
    horizon_years: {
      type: 'number',
      description: 'Filter projections whose peak_date falls within this many years from today (default: 3).',
    },
    probability_tier: {
      type: 'string',
      description: 'Filter by probability tier.',
      enum: ['tier_1_high', 'tier_2_moderate', 'tier_3_speculative'],
    },
    domain: {
      type: 'string',
      description: 'Filter by domain (career, wealth, relationship, health, character, spirituality, other).',
    },
    limit: {
      type: 'number',
      description: 'Max projection rows to return (default: 50 = all, max: 50). Applied after ORDER BY.',
    },
  },

  llm_hints: {
    agentic: {
      cost_class: 'cheap',
      cacheable:  true,
    },
    bulk_context: {
      pre_fetch_priority: 18,
    },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    const chart_id = args['chart_id'] as string
    if (!chart_id) {
      return { content: { error: 'chart_id is required' }, is_error: true }
    }

    const horizon_years   = Number(args['horizon_years'] ?? 3)
    const probability_tier = args['probability_tier'] as string | undefined
    const domain          = args['domain'] as string | undefined
    const limit           = Math.min(Number(args['limit'] ?? 50), 50)

    const horizon_date = new Date()
    horizon_date.setFullYear(horizon_date.getFullYear() + horizon_years)

    try {
      const conds: string[] = ['chart_id = $1']
      const params: unknown[] = [chart_id]
      let p = 2

      // The projection's temporal anchor is peak_date (kala_bhavishya has no
      // projection_date / horizon_years columns).
      if (horizon_years > 0) {
        conds.push(`peak_date <= $${p++}`)
        params.push(horizon_date.toISOString().split('T')[0])
      }
      if (probability_tier) { conds.push(`probability_tier = $${p++}`); params.push(probability_tier) }
      if (domain)           { conds.push(`domain = $${p++}`);           params.push(domain) }

      const where = conds.join(' AND ')
      const limitPh = `$${p}`

      // WP-1.5 F-DATE-TZ: peak_date/window_start/window_end are DATE columns → to_char to
      // 'YYYY-MM-DD' (raw return → IST-midnight → UTC off-by-one). computed_at is a
      // timestamptz and is correctly left as an ISO instant.
      const sql = `
        SELECT id, projection_rank, domain, probability_tier, effective_score,
               to_char(peak_date, 'YYYY-MM-DD')    AS peak_date,
               to_char(window_start, 'YYYY-MM-DD') AS window_start,
               to_char(window_end, 'YYYY-MM-DD')   AS window_end,
               narrative,
               falsifiability, convergence_id, signal_id, source_chain,
               outcome_recorded, outcome_notes, source_citation, computed_at
        FROM kala_bhavishya
        WHERE ${where}
        ORDER BY probability_tier, projection_rank
        LIMIT ${limitPh}
      `

      // MC-015/026: family-collapse aggregate — one row per DISTINCT (window_start,
      // window_end, domain), computed server-side over the FULL matching set (not just the
      // bounded `projections` page above), since the duplication ratio (e.g. 87 rows -> 1
      // window) means a JS-side collapse of only the bounded page could undercount
      // member_count once the page is smaller than a single family. Mirrors
      // query_temporal_activation's window_families pattern.
      const familySql = `
        SELECT to_char(window_start, 'YYYY-MM-DD') AS window_start,
               to_char(window_end, 'YYYY-MM-DD')   AS window_end,
               domain,
               COUNT(*) AS member_count,
               (array_agg(id::text ORDER BY projection_rank ASC NULLS LAST))[1:10]        AS member_ids,
               (array_agg(signal_id::text ORDER BY projection_rank ASC NULLS LAST))[1:10] AS member_signal_ids,
               (array_agg(probability_tier ORDER BY projection_rank ASC NULLS LAST))[1]    AS probability_tier,
               MAX(effective_score)                                                       AS max_effective_score,
               (array_agg(narrative ORDER BY projection_rank ASC NULLS LAST))[1]           AS narrative,
               (array_agg(source_citation ORDER BY projection_rank ASC NULLS LAST))[1]     AS source_citation
        FROM kala_bhavishya
        WHERE ${where}
        GROUP BY window_start, window_end, domain
        ORDER BY MAX(effective_score) DESC NULLS LAST, MIN(projection_rank) ASC
        LIMIT ${limitPh}
      `

      const [result, familyResult] = await Promise.all([
        query(sql, [...params, limit]),
        query<ProjectionFamilyRow>(familySql, [...params, limit]),
      ])

      // signal_id is a scalar per row (not an array); collect distinct refs.
      const signalRefs = new Set<string>()
      for (const row of result.rows as Array<{ signal_id?: string }>) {
        if (row.signal_id) signalRefs.add(row.signal_id)
      }

      const projection_families = familyResult.rows.map(f => ({
        window_start: f.window_start,
        window_end: f.window_end,
        domain: f.domain,
        member_count: Number(f.member_count ?? 0),
        member_ids: f.member_ids ?? [],
        member_signal_ids: f.member_signal_ids ?? [],
        probability_tier: f.probability_tier,
        max_effective_score: f.max_effective_score,
        narrative: f.narrative,
        source_citation: f.source_citation,
      }))

      return {
        content: {
          chart_id,
          projections:      result.rows,
          projection_count: result.rows.length,
          // MC-015/026: window-family collapse — one entry per DISTINCT (window_start,
          // window_end, domain) instead of the raw (often heavily duplicate-windowed)
          // `projections` array above. `projections` is kept for existing consumers; new
          // callers should prefer `projection_families`.
          projection_families,
          projection_family_count: projection_families.length,
          signal_id_refs:   Array.from(signalRefs),
          filters: { horizon_years, probability_tier, domain, limit },
          provenance: { tables: ['kala_bhavishya'] },
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
