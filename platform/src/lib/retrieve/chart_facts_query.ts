/**
 * MARSYS-JIS Stream B — Tool: chart_facts_query (M2-C.1)
 *
 * Parametric retrieval over chart_facts. Primary gateway for all quantitative
 * chart-fact queries: strengths, BAV bindus, placements, sahams, yogas,
 * aspects, longevity indicators, and more.
 *
 * 795 rows across 37 categories (post Wave 2–4 ETL). No migrations needed.
 */

import crypto from 'crypto'
import { getStorageClient } from '@/lib/storage'
import { validate } from '@/lib/schemas'
import { telemetry } from '@/lib/telemetry'
import { writeToolExecutionLog } from '@/lib/db/monitoring-write'
import type { QueryPlan, ToolBundle, ToolBundleResult, RetrievalTool } from './types'

const TOOL_NAME = 'chart_facts_query'
const TOOL_VERSION = '1.0.0'

export type ChartFactsCategory =
  | 'house' | 'dasha_chara' | 'planet' | 'dasha_vimshottari' | 'saham'
  | 'sensitive_point' | 'birth_metadata' | 'strength_extra' | 'yoga'
  | 'dasha_yogini' | 'deity_assignment' | 'shadbala' | 'ashtakavarga_sav'
  | 'kp_cusp' | 'navatara' | 'panchang' | 'cusp' | 'arudha_occupancy'
  | 'bhava_bala' | 'chandra_placement' | 'mrityu_bhaga' | 'longevity_indicator'
  | 'arudha' | 'aspect' | 'chalit_shift' | 'kp_planet' | 'special_lagna'
  | 'strength' | 'upagraha' | 'ashtakavarga_bav' | 'kakshya_zone'
  | 'mercury_convergence' | 'ashtakavarga_pinda' | 'ishta_kashta'
  | 'kp_significator' | 'varshphal' | 'avastha'

// rank_by keys map to SQL ORDER BY expressions in buildOrderBy()
export type RankBy =
  | 'value_number'     // generic numeric column
  | 'total_rupas'      // shadbala: SBL.TOTAL rows use forensic_rupas in value_json
  | 'total_bindus'     // ashtakavarga BAV: value_json->>'total_bindus'
  | 'bhava_bala'       // bhava_bala: BVB rows use jh_rupas in value_json
  | 'pinda'            // ashtakavarga pinda: value_json->>'pinda'

export interface ChartFactsQueryInput {
  category?: ChartFactsCategory | ChartFactsCategory[]
  planet?: string
  house?: number
  sign?: string
  nakshatra?: string
  nakshatra_pada?: 1 | 2 | 3 | 4
  divisional_chart?: string
  keyword?: string
  rank_by?: RankBy
  limit?: number
  /** If true, restrict to rows whose value_json->>'vargottama' = 'true'. Surfaces vargottama Mercury (and any other vargottama planet) across all vargas. */
  vargottama_only?: boolean
  /** ISO date (YYYY-MM-DD). For dasha categories: returns rows where start_date <= d < end_date. */
  as_of_date?: string
  /** ISO date. For dasha categories: returns rows where end_date >= from_date. */
  from_date?: string
  /** ISO date. For dasha categories: returns rows where start_date <= to_date. */
  to_date?: string
  /**
   * MCPT v3.2 P4b: When true, the response result item is grouped by category as
   * { rows_by_category: { [category]: ChartFactRow[] } } instead of a flat rows array.
   * Used by the MCP query_chart_facts tool when the `categories` array param is provided.
   */
  batched?: boolean
  /**
   * UDA-Q-S3: When true, appends a category_counts object showing how many rows each
   * category has (including zero-count categories). Each result also carries a
   * populated_count field showing the total number of non-null value_json rows for the
   * queried category. When false (default), only returns categories that have at least
   * one row, each annotated with populated_count.
   */
  include_empty_counts?: boolean
}

interface ChartFactsRow {
  fact_id: string
  category: string
  divisional_chart: string
  value_text: string | null
  value_number: number | null
  value_json: Record<string, unknown> | null
  source_section: string
}

function buildWhereClause(p: ChartFactsQueryInput): { where: string; args: unknown[] } {
  const conditions: string[] = ['is_stale = false']
  const args: unknown[] = []
  let idx = 1

  if (p.category) {
    const cats = Array.isArray(p.category) ? p.category : [p.category]
    conditions.push(`category = ANY($${idx}::text[])`)
    args.push(cats)
    idx++
  }

  if (p.planet) {
    conditions.push(
      `(value_json->>'planet' ILIKE $${idx} OR fact_id ILIKE $${idx + 1})`
    )
    args.push(`%${p.planet}%`, `%${p.planet}%`)
    idx += 2
  }

  if (p.house !== undefined) {
    conditions.push(`(value_json->>'house')::int = $${idx}`)
    args.push(p.house)
    idx++
  }

  if (p.sign) {
    conditions.push(`value_json->>'sign' ILIKE $${idx}`)
    args.push(`%${p.sign}%`)
    idx++
  }

  if (p.nakshatra) {
    conditions.push(`value_json->>'nakshatra' ILIKE $${idx}`)
    args.push(`%${p.nakshatra}%`)
    idx++
  }

  // nakshatra_pada populated by W4-R1 for planet rows
  if (p.nakshatra_pada !== undefined) {
    conditions.push(`(value_json->>'nakshatra_pada')::int = $${idx}`)
    args.push(p.nakshatra_pada)
    idx++
  }

  if (p.divisional_chart) {
    conditions.push(`divisional_chart = $${idx}`)
    args.push(p.divisional_chart)
    idx++
  }

  if (p.keyword) {
    conditions.push(
      `(value_text ILIKE $${idx} OR fact_id ILIKE $${idx + 1} OR value_json::text ILIKE $${idx + 2})`
    )
    args.push(`%${p.keyword}%`, `%${p.keyword}%`, `%${p.keyword}%`)
    idx += 3
  }

  if (p.vargottama_only === true) {
    conditions.push(`(value_json->>'vargottama')::boolean = true`)
  }

  if (p.as_of_date) {
    conditions.push(
      `(value_json->>'start_date')::date <= $${idx}::date AND ` +
      `(value_json->>'end_date')::date > $${idx + 1}::date`
    )
    args.push(p.as_of_date, p.as_of_date)
    idx += 2
  }
  if (p.from_date) {
    conditions.push(`(value_json->>'end_date')::date >= $${idx}::date`)
    args.push(p.from_date)
    idx++
  }
  if (p.to_date) {
    conditions.push(`(value_json->>'start_date')::date <= $${idx}::date`)
    args.push(p.to_date)
    idx++
  }

  return { where: conditions.join(' AND '), args }
}

function buildOrderBy(rank_by?: RankBy): string {
  // Maps brief's rank_by names to the actual SQL expressions for each category's JSON shape.
  // shadbala totals (SBL.TOTAL.*) store the total as forensic_rupas; BAV uses total_bindus;
  // bhava_bala rows (BVB.*) store the score as jh_rupas; pinda rows use pinda.
  const map: Record<RankBy, string> = {
    value_number: 'ORDER BY value_number DESC NULLS LAST, fact_id',
    total_rupas:  "ORDER BY (value_json->>'forensic_rupas')::numeric DESC NULLS LAST, fact_id",
    total_bindus: "ORDER BY (value_json->>'total_bindus')::numeric DESC NULLS LAST, fact_id",
    bhava_bala:   "ORDER BY (value_json->>'jh_rupas')::numeric DESC NULLS LAST, fact_id",
    pinda:        "ORDER BY (value_json->>'pinda')::numeric DESC NULLS LAST, fact_id",
  }
  return rank_by ? (map[rank_by] ?? 'ORDER BY category, fact_id') : 'ORDER BY category, fact_id'
}

async function retrieve(plan: QueryPlan, params?: Record<string, unknown>): Promise<ToolBundle> {
  const start = Date.now()
  try {
    return await retrieveImpl(plan, params, start)
  } catch (err) {
    void writeToolExecutionLog({
      query_id: plan.query_plan_id,
      tool_name: TOOL_NAME,
      params_json: (params ?? null) as Record<string, unknown> | null,
      status: 'error',
      rows_returned: 0,
      latency_ms: Date.now() - start,
      token_estimate: 0,
      data_asset_id: 'FORENSIC',
      error_code: err instanceof Error ? err.message : String(err),
      served_from_cache: false,
      fallback_used: false,
    })
    throw err
  }
}

async function retrieveImpl(
  plan: QueryPlan,
  params: Record<string, unknown> | undefined,
  start: number,
): Promise<ToolBundle> {
  // Merge plan-embedded params with direct params (direct params take precedence)
  const embedded = (plan as unknown as Record<string, unknown>).chart_facts_query as ChartFactsQueryInput | undefined
  const p: ChartFactsQueryInput = { ...embedded, ...(params as ChartFactsQueryInput | undefined) }

  const limit = Math.min(p.limit ?? 20, 100)
  const { where, args } = buildWhereClause(p)
  const orderBy = buildOrderBy(p.rank_by)

  const sql = `
    SELECT
      fact_id,
      category,
      divisional_chart,
      value_text,
      value_number,
      value_json,
      source_section
    FROM chart_facts
    WHERE ${where}
    ${orderBy}
    LIMIT ${limit}
  `.trim()

  const storage = getStorageClient()
  const { rows } = await storage.query<ChartFactsRow>(sql, args)

  // UDA-Q-S3: Compute populated_count — total non-null value_json rows for the queried
  // category (using the same WHERE clause but without LIMIT and counting only non-null rows).
  const { where: countWhere, args: countArgs } = buildWhereClause(p)
  const countSql = `SELECT COUNT(*) AS cnt FROM chart_facts WHERE ${countWhere} AND value_json IS NOT NULL`
  const countResult = await storage.query<{ cnt: string }>(countSql, countArgs)
  const populated_count = parseInt(countResult.rows[0]?.cnt ?? '0', 10)

  // UDA-Q-S3: When include_empty_counts=true, fetch per-category counts for all known
  // categories so callers can see inventory across the whole table.
  let category_counts: Record<string, number> | undefined
  if (p.include_empty_counts === true) {
    const catCountSql = `
      SELECT category, COUNT(*) AS cnt
      FROM chart_facts
      WHERE is_stale = false
      GROUP BY category
      ORDER BY category
    `.trim()
    const catCountResult = await storage.query<{ category: string; cnt: string }>(catCountSql, [])
    const countMap: Record<string, number> = {}
    for (const r of catCountResult.rows) {
      countMap[r.category] = parseInt(r.cnt, 10)
    }
    // Ensure all known categories appear even if they have 0 rows
    const allCategories: ChartFactsCategory[] = [
      'house', 'dasha_chara', 'planet', 'dasha_vimshottari', 'saham',
      'sensitive_point', 'birth_metadata', 'strength_extra', 'yoga',
      'dasha_yogini', 'deity_assignment', 'shadbala', 'ashtakavarga_sav',
      'kp_cusp', 'navatara', 'panchang', 'cusp', 'arudha_occupancy',
      'bhava_bala', 'chandra_placement', 'mrityu_bhaga', 'longevity_indicator',
      'arudha', 'aspect', 'chalit_shift', 'kp_planet', 'special_lagna',
      'strength', 'upagraha', 'ashtakavarga_bav', 'kakshya_zone',
      'mercury_convergence', 'ashtakavarga_pinda', 'ishta_kashta',
      'kp_significator', 'varshphal', 'avastha',
    ]
    category_counts = {}
    for (const cat of allCategories) {
      category_counts[cat] = countMap[cat] ?? 0
    }
  }

  // MCPT v3.2 P4b: When batched=true, group rows by category and emit a single
  // result item with { rows_by_category: { [category]: row[] } } for one-round-trip
  // multi-category retrieval. Single-category path (batched=false/undefined) unchanged.
  let results: ToolBundleResult[]
  if (p.batched === true) {
    const grouped: Record<string, unknown[]> = {}
    for (const row of rows) {
      const cat = row.category
      if (!grouped[cat]) grouped[cat] = []
      grouped[cat].push({
        fact_id: row.fact_id,
        category: row.category,
        divisional_chart: row.divisional_chart,
        value_text: row.value_text,
        value_number: row.value_number,
        data: row.value_json,
        source: row.source_section,
      })
    }
    const payload: Record<string, unknown> = {
      rows_by_category: grouped,
      populated_count,
    }
    if (category_counts !== undefined) {
      payload['category_counts'] = category_counts
    }
    results = [{
      content: JSON.stringify(payload),
      source_canonical_id: 'FORENSIC',
      source_version: '8.0',
      confidence: 1.0,
      significance: 0.9,
    }]
  } else {
    const basePayload = (row: ChartFactsRow): Record<string, unknown> => ({
      fact_id: row.fact_id,
      category: row.category,
      divisional_chart: row.divisional_chart,
      value_text: row.value_text,
      value_number: row.value_number,
      data: row.value_json,
      source: row.source_section,
    })
    if (rows.length > 0) {
      // Annotate the first result with populated_count (and category_counts if requested);
      // remaining rows are plain fact rows without the meta fields.
      const [firstRow, ...restRows] = rows
      const firstPayload: Record<string, unknown> = {
        ...basePayload(firstRow!),
        populated_count,
      }
      if (category_counts !== undefined) {
        firstPayload['category_counts'] = category_counts
      }
      results = [
        {
          content: JSON.stringify(firstPayload),
          source_canonical_id: 'FORENSIC',
          source_version: '8.0',
          confidence: 1.0,
          significance: 0.9,
        },
        ...restRows.map((row) => ({
          content: JSON.stringify(basePayload(row)),
          source_canonical_id: 'FORENSIC',
          source_version: '8.0',
          confidence: 1.0,
          significance: 0.9,
        })),
      ]
    } else {
      // Zero rows: emit a single summary-only result with populated_count
      const summaryPayload: Record<string, unknown> = { populated_count }
      if (category_counts !== undefined) {
        summaryPayload['category_counts'] = category_counts
      }
      results = [{
        content: JSON.stringify(summaryPayload),
        source_canonical_id: 'FORENSIC',
        source_version: '8.0',
        confidence: 1.0,
        significance: 0.9,
      }]
    }
  }

  const result_hash =
    'sha256:' +
    crypto
      .createHash('sha256')
      .update(JSON.stringify(results.map(r => r.content.slice(0, 80)).sort()))
      .digest('hex')

  const latency_ms = Date.now() - start

  const bundle: ToolBundle = {
    tool_bundle_id: crypto.randomUUID(),
    tool_name: TOOL_NAME,
    tool_version: TOOL_VERSION,
    invocation_params: {
      category: p.category,
      planet: p.planet,
      house: p.house,
      sign: p.sign,
      nakshatra: p.nakshatra,
      nakshatra_pada: p.nakshatra_pada,
      divisional_chart: p.divisional_chart,
      keyword: p.keyword,
      rank_by: p.rank_by,
      vargottama_only: p.vargottama_only,
      as_of_date: p.as_of_date,
      from_date: p.from_date,
      to_date: p.to_date,
      limit,
    },
    results,
    served_from_cache: false,
    latency_ms,
    result_hash,
    schema_version: '1.0',
  }

  const validation = validate('tool_bundle', bundle)
  if (!validation.valid) {
    throw new Error(
      `chart_facts_query: ToolBundle schema validation failed: ${JSON.stringify(validation.errors)}`
    )
  }

  telemetry.recordLatency(TOOL_NAME, 'retrieve', latency_ms)

  void writeToolExecutionLog({
    query_id: plan.query_plan_id,
    tool_name: TOOL_NAME,
    params_json: bundle.invocation_params as Record<string, unknown>,
    status: results.length === 0 ? 'zero_rows' : 'ok',
    rows_returned: results.length,
    latency_ms,
    token_estimate: Math.ceil(JSON.stringify(results).length / 4),
    data_asset_id: 'FORENSIC',
    error_code: null,
    served_from_cache: false,
    fallback_used: false,
    raw_result_count: rows.length,
    kept_result_count: results.length,
    dropped_items: [],
    kept_items: results.slice(0, 200).map(r => ({
      item_id: r.signal_id ?? r.source_canonical_id,
      score: r.confidence ?? null,
      contribution_tokens: null,
    })),
    tool_input_payload: bundle.invocation_params,
    error_class: 'OK',
  })

  return bundle
}

export const tool: RetrievalTool = {
  name: TOOL_NAME,
  version: TOOL_VERSION,
  retrieve,
}
