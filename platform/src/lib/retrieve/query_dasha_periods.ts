/**
 * MARSYS-JIS Retrieval tool — query_dasha_periods (Phase 5A)
 *
 * Surgical dasha-schedule lookup. Reads chart_facts rows where category is
 * one of the three dasha categories (vimshottari / yogini / chara) and
 * value_json carries {md_lord, ad_lord, start_date, end_date}.
 *
 * 50 dasha_vimshottari rows (1984-02-05 → 2060-08-21). Coverage: Jupiter
 * MD (partial first) → Saturn MD → Mercury MD (current) → Ketu MD (next) →
 * Venus MD → Sun MD.
 *
 * Default empty params returns: today's active row (start_date <= today <
 * end_date) PLUS the next 3 MD-transition rows. This is the "what's my dasha
 * situation?" one-tool-call answer.
 *
 * Distinct from chart_facts_query: chart_facts_query handles 37 categories
 * including dasha; this tool is semantically dasha-only with helpers for
 * next_count / prev_count / active-chain shortcuts that the planner can
 * compose without needing date arithmetic.
 *
 * Distinct from temporal.dasha_context_required: that calls /dasha_chain
 * sidecar which returns the active 5-level chain at ONE date only. This
 * tool returns the schedule from the canonical chart_facts table, with
 * full upcoming + historical visibility.
 */

import crypto from 'crypto'
import { getStorageClient } from '@/lib/storage'
import { writeToolExecutionLog } from '@/lib/db/monitoring-write'
import type { QueryPlan, ToolBundle, ToolBundleResult, RetrievalTool } from './types'

const TOOL_NAME = 'query_dasha_periods'
const TOOL_VERSION = '1.0.0'

type DashaSystem = 'vimshottari' | 'yogini' | 'chara'
type DashaLevel = 'M' | 'A' | 'P' | 'all'

const SYSTEM_CATEGORY: Record<DashaSystem, string> = {
  vimshottari: 'dasha_vimshottari',
  yogini: 'dasha_yogini',
  chara: 'dasha_chara',
}

export interface QueryDashaPeriodsInput {
  /** Defaults to 'vimshottari'. */
  system?: DashaSystem
  /** Default 'all'. 'M' deduplicates to one row per MD cluster (the AD row where ad_lord == md_lord). */
  level?: DashaLevel
  /** ISO date (YYYY-MM-DD). Returns rows whose start_date <= d < end_date. */
  as_of_date?: string
  /** If set, returns next N MD-transition rows after as_of_date (or today). */
  next_count?: number
  /** If set, returns prev N MD-transition rows before as_of_date (or today). */
  prev_count?: number
  /** Filter to MD lord (canonical name; case-insensitive ILIKE). */
  md_lord?: string
  /** Filter to AD lord. */
  ad_lord?: string
  /** Range start — end_date >= from_date. */
  from_date?: string
  /** Range end — start_date <= to_date. */
  to_date?: string
  /** Max rows. Default 30, max 100. */
  limit?: number
}

interface DashaRow {
  fact_id: string
  category: string
  value_json: {
    md_lord: string
    ad_lord: string
    start_date: string
    end_date: string
  }
  source_section: string | null
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
      data_asset_id: 'CHART_FACTS_DASHA',
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
  const input = (params ?? {}) as QueryDashaPeriodsInput
  const system: DashaSystem = input.system ?? 'vimshottari'
  const category = SYSTEM_CATEGORY[system]
  const limit = Math.max(1, Math.min(100, input.limit ?? 30))
  const today = new Date().toISOString().slice(0, 10)

  const conditions: string[] = ['is_stale = false', 'category = $1']
  const args: unknown[] = [category]
  let idx = 2

  if (input.as_of_date) {
    conditions.push(
      `(value_json->>'start_date')::date <= $${idx}::date AND ` +
      `(value_json->>'end_date')::date > $${idx + 1}::date`
    )
    args.push(input.as_of_date, input.as_of_date)
    idx += 2
  }

  if (input.md_lord) {
    conditions.push(`value_json->>'md_lord' ILIKE $${idx}`)
    args.push(`%${input.md_lord}%`)
    idx++
  }

  if (input.ad_lord) {
    conditions.push(`value_json->>'ad_lord' ILIKE $${idx}`)
    args.push(`%${input.ad_lord}%`)
    idx++
  }

  // next_count / prev_count: anchor date filter
  let anchorDate: string | undefined
  if (input.from_date) {
    conditions.push(`(value_json->>'end_date')::date >= $${idx}::date`)
    args.push(input.from_date)
    idx++
  } else if (input.next_count) {
    anchorDate = input.as_of_date ?? today
    conditions.push(`(value_json->>'start_date')::date >= $${idx}::date`)
    args.push(anchorDate)
    idx++
  } else if (input.prev_count) {
    anchorDate = input.as_of_date ?? today
    conditions.push(`(value_json->>'end_date')::date <= $${idx}::date`)
    args.push(anchorDate)
    idx++
  }

  if (input.to_date) {
    conditions.push(`(value_json->>'start_date')::date <= $${idx}::date`)
    args.push(input.to_date)
    idx++
  }

  // Default empty-params: return today's active row + next 3 MDs
  const isDefaultQuery =
    !input.as_of_date && !input.next_count && !input.prev_count &&
    !input.md_lord && !input.ad_lord && !input.from_date && !input.to_date

  if (isDefaultQuery) {
    // Add start_date >= (today - 1 year) as a loose lower bound to avoid returning
    // all historical rows; default will include today's active row + upcoming
    conditions.push(`(value_json->>'end_date')::date >= $${idx}::date`)
    args.push(today)
    idx++
  }

  const orderDir = input.prev_count ? 'DESC' : 'ASC'
  let actualLimit = limit
  if (input.next_count) actualLimit = Math.min(limit, input.next_count * 9)
  if (input.prev_count) actualLimit = Math.min(limit, input.prev_count * 9)

  const sql = `
    SELECT fact_id, category, value_json, source_section
    FROM chart_facts
    WHERE ${conditions.join(' AND ')}
    ORDER BY (value_json->>'start_date')::date ${orderDir}
    LIMIT ${actualLimit}
  `

  const storage = getStorageClient()
  const result = await storage.query<DashaRow>(sql, args)
  const rows = result.rows

  // Level='M' dedup: keep only the row where ad_lord == md_lord (MD-start row)
  let filteredRows = rows
  if (input.level === 'M') {
    const seenMd = new Set<string>()
    filteredRows = rows.filter(r => {
      if (r.value_json.ad_lord === r.value_json.md_lord) {
        const key = `${r.value_json.md_lord}-${r.value_json.start_date.slice(0, 4)}`
        if (seenMd.has(key)) return false
        seenMd.add(key)
        return true
      }
      return false
    })
  }

  // Cap next_count / prev_count to N MD clusters (each ~9 AD rows)
  if (input.next_count) {
    const clusters = new Set<string>()
    filteredRows = filteredRows.filter(r => {
      const k = `${r.value_json.md_lord}-${r.value_json.start_date.slice(0, 4)}`
      clusters.add(k)
      return clusters.size <= input.next_count!
    })
  }
  if (input.prev_count) {
    const clusters = new Set<string>()
    // rows are DESC; cap to prev_count clusters, then reverse for presentation
    const capped = filteredRows.filter(r => {
      const k = `${r.value_json.md_lord}-${r.value_json.start_date.slice(0, 4)}`
      clusters.add(k)
      return clusters.size <= input.prev_count!
    })
    filteredRows = capped.reverse()
  }

  const results: ToolBundleResult[] = filteredRows.length > 0
    ? filteredRows.map(r => ({
        content: JSON.stringify({
          fact_id: r.fact_id,
          system,
          level: r.value_json.ad_lord === r.value_json.md_lord ? 'M_start' : 'A',
          md_lord: r.value_json.md_lord,
          ad_lord: r.value_json.ad_lord,
          start_date: r.value_json.start_date,
          end_date: r.value_json.end_date,
          source_section: r.source_section,
        }),
        source_canonical_id: 'FORENSIC',
        source_version: '8.0',
        confidence: 1.0,
        significance: 1.0,
      }))
    : [{
        content: JSON.stringify({
          note: `No ${category} rows match the given filters. Available date range: 1984-02-05 to 2060-08-21.`,
          params: input,
        }),
        source_canonical_id: 'CHART_FACTS_DASHA',
        source_version: '1.0',
        confidence: 0,
        significance: 0,
      }]

  const result_hash =
    'sha256:' +
    crypto
      .createHash('sha256')
      .update(JSON.stringify(results.map(r => r.content.slice(0, 80)).sort()))
      .digest('hex')

  const bundle: ToolBundle = {
    tool_bundle_id: crypto.randomUUID(),
    tool_name: TOOL_NAME,
    tool_version: TOOL_VERSION,
    invocation_params: { ...input, system, limit: actualLimit },
    results,
    served_from_cache: false,
    latency_ms: Date.now() - start,
    result_hash,
    schema_version: '1.0',
  }

  void writeToolExecutionLog({
    query_id: plan.query_plan_id,
    tool_name: TOOL_NAME,
    params_json: input as Record<string, unknown>,
    status: filteredRows.length === 0 ? 'zero_rows' : 'ok',
    rows_returned: filteredRows.length,
    latency_ms: bundle.latency_ms,
    token_estimate: Math.ceil(JSON.stringify(results).length / 4),
    data_asset_id: 'CHART_FACTS_DASHA',
    error_code: null,
    served_from_cache: false,
    fallback_used: filteredRows.length === 0,
  })

  return bundle
}

export const tool: RetrievalTool = {
  name: TOOL_NAME,
  version: TOOL_VERSION,
  description:
    'Surgical Vimshottari / Yogini / Chara dasha schedule lookup. Reads ' +
    'chart_facts dasha rows (50 Vimshottari rows covering 1984-02-05 → ' +
    '2060-08-21) with semantic helpers for active-chain / next-N / prev-N / ' +
    "specific-lord queries. Default empty params returns today's active " +
    'row plus next 3 MDs.',
  retrieve,
}
