/**
 * MARSYS-JIS Stream B — Tool: divisional_query (M2-C.4)
 *
 * Queries chart_facts for divisional chart (varga) placements.
 * Covers D1 through D60 — filtered by divisional_chart column.
 *
 * Categories covered: house (149 rows across all vargas)
 */

import crypto from 'crypto'
import { getStorageClient } from '@/lib/storage'
import { writeToolExecutionLog } from '@/lib/db/monitoring-write'
import type { QueryPlan, ToolBundle, ToolBundleResult, RetrievalTool } from './types'

const TOOL_NAME = 'divisional_query'
const TOOL_VERSION = '1.0'

export type VargaCode =
  | 'D1' | 'D2' | 'D3' | 'D4' | 'D7' | 'D9' | 'D10'
  | 'D12' | 'D16' | 'D20' | 'D24' | 'D27' | 'D30'
  | 'D40' | 'D45' | 'D60' | 'BIRTH'

export interface DivisionalQueryInput {
  varga: VargaCode
  planet?: string
  house?: number
  category?: 'house' | 'planet' | 'both'
}

interface ChartFactsRow {
  fact_id: string
  category: string
  divisional_chart: string
  value_text: string | null
  value_json: Record<string, unknown> | null
  source_section: string
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
  const input = params as DivisionalQueryInput | undefined

  const varga: VargaCode = input?.varga ?? 'D9'

  // VARGA-ETL-FULL-S1-CPA D6: expanded category list. After v1.1 YAML migration,
  // D-tagged rows include arudha occupancy, yogas, aspects (§16 tagged to D9
  // where applicable), and sensitive_point rows — wider whitelist surfaces them.
  const categories =
    input?.category === 'house' ? ['house']
    : input?.category === 'planet' ? ['planet']
    : [
        'house', 'planet', 'strength', 'strength_extra', 'chalit_shift',
        'arudha', 'arudha_occupancy', 'yoga', 'aspect', 'sensitive_point',
      ]

  const conditions: string[] = [
    `divisional_chart = $1`,
    `category = ANY($2)`,
    `is_stale = false`,
  ]
  const queryParams: unknown[] = [varga, categories]
  let idx = 3

  if (input?.planet) {
    conditions.push(
      `(value_json->>'planet' ILIKE $${idx} OR fact_id ILIKE $${idx})`
    )
    queryParams.push(`%${input.planet}%`)
    idx++
  }

  if (input?.house !== undefined) {
    conditions.push(`(value_json->>'house')::int = $${idx}`)
    queryParams.push(input.house)
    idx++
  }

  const sql = `
    SELECT fact_id, category, divisional_chart, value_text, value_json, source_section
    FROM chart_facts
    WHERE ${conditions.join(' AND ')}
    ORDER BY category, fact_id
    LIMIT 200
  `.trim()

  const { rows } = await getStorageClient().query<ChartFactsRow>(sql, queryParams)

  const results: ToolBundleResult[] = rows.map(row => ({
    content: JSON.stringify({
      fact_id: row.fact_id,
      category: row.category,
      varga,
      value_text: row.value_text,
      placement: row.value_json,
      source: row.source_section,
    }),
    source_canonical_id: 'FORENSIC',
    source_version: '8.0',
    confidence: 1.0,
    significance: 0.85,
  }))

  const result_hash =
    'sha256:' +
    crypto
      .createHash('sha256')
      .update(JSON.stringify(results.map(r => r.content.slice(0, 50)).sort()))
      .digest('hex')

  const latency_ms = Date.now() - start

  const bundle: ToolBundle = {
    tool_bundle_id: crypto.randomUUID(),
    tool_name: TOOL_NAME,
    tool_version: TOOL_VERSION,
    invocation_params: {
      varga,
      planet: input?.planet,
      house: input?.house,
      category: input?.category ?? 'both',
    },
    results,
    served_from_cache: false,
    latency_ms,
    result_hash,
    schema_version: '1.0',
  }

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
  description:
    'Divisional chart (varga) placement lookup. Returns house positions and planet ' +
    'placements in any divisional chart: D1 (rashi), D9 (navamsha), D10 (dasamsha), ' +
    'D7 (saptamsha), D2 (hora), D12 (dwadasamsha), D3 (drekkana), D60 (shashtiamsha), etc. ' +
    'Use when the query involves a specific varga chart or requires varga confirmation of D1 placements.',
  retrieve,
}
