/**
 * MARSYS-JIS Stream B — Tool: query_varshaphala (M3-W3-C2)
 *
 * Reads from the varshaphala table for a given chart_id and target year
 * (or year range), returning the annual Tajika chart's planet positions
 * and Ascendant as a ToolBundle.
 *
 * Source schema: platform/migrations/025_varshaphala.sql
 * Engine:        platform/scripts/temporal/compute_varshaphala.py
 * Cross-check:   05_TEMPORAL_ENGINES/varshaphala/CROSSCHECK_v1_0.md
 *                (WITHIN_TOLERANCE_PENDING_REVIEW; full PASS pending JH-export
 *                 comparison at M3-D held-out work)
 *
 * Year-lord (Varshesha) and Muntha are NOT included in the engine output
 * substrate; they live at the synthesis layer (Muntha is year-of-life
 * arithmetic from FORENSIC §22; Varshesha requires the M3-W3-C3 strength
 * engine for Pancha-Vargiya selection).
 */

import crypto from 'crypto'
import { getStorageClient } from '@/lib/storage'
import { writeToolExecutionLog } from '@/lib/db/monitoring-write'
import { requireChartId } from './chart_context'
import type { QueryPlan, ToolBundle, ToolBundleResult, RetrievalTool } from './types'

const TOOL_NAME = 'query_varshaphala'
const TOOL_VERSION = '1.0'

export interface QueryVarshaphalaInput {
  chart_id?: string
  year?: number
  year_start?: number
  year_end?: number
  ayanamsha?: string
}

interface VarshaphalaDbRow {
  chart_id: string
  year: number
  solar_return_utc: string
  ascendant_sidereal: string | number | null
  ascendant_sign: string | null
  planet_positions: Record<string, { sidereal_lon: number; sign: string; nakshatra: string }>
  ayanamsha: string
  computed_by: string
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
      data_asset_id: 'VARSHAPHALA',
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
  const input = (params ?? {}) as QueryVarshaphalaInput
  const chartId = requireChartId(input.chart_id)
  const ayanamsha = input.ayanamsha ?? 'lahiri'

  const conditions: string[] = ['chart_id = $1', 'ayanamsha = $2']
  const queryParams: unknown[] = [chartId, ayanamsha]
  let idx = 3

  let yearStart = input.year_start
  let yearEnd = input.year_end
  if (input.year !== undefined) {
    yearStart = input.year
    yearEnd = input.year
  }
  // Fallback to plan.time_window if no explicit year(s) provided.
  if (yearStart === undefined && plan.time_window?.start) {
    const y = parseInt(plan.time_window.start.slice(0, 4), 10)
    if (!isNaN(y)) yearStart = y
  }
  if (yearEnd === undefined && plan.time_window?.end) {
    const y = parseInt(plan.time_window.end.slice(0, 4), 10)
    if (!isNaN(y)) yearEnd = y
  }

  if (yearStart !== undefined) {
    conditions.push(`year >= $${idx}`)
    queryParams.push(yearStart)
    idx++
  }
  if (yearEnd !== undefined) {
    conditions.push(`year <= $${idx}`)
    queryParams.push(yearEnd)
    idx++
  }

  const sql = `
    SELECT chart_id, year, solar_return_utc, ascendant_sidereal, ascendant_sign,
           planet_positions, ayanamsha, computed_by
    FROM varshaphala
    WHERE ${conditions.join(' AND ')}
    ORDER BY year ASC
    LIMIT 100
  `.trim()

  const { rows } = await getStorageClient().query<VarshaphalaDbRow>(sql, queryParams)

  const results: ToolBundleResult[] = rows.map(row => ({
    content: JSON.stringify({
      year: row.year,
      solar_return_utc: row.solar_return_utc,
      ascendant: {
        sidereal_lon:
          row.ascendant_sidereal !== null ? Number(row.ascendant_sidereal) : null,
        sign: row.ascendant_sign,
      },
      planets: row.planet_positions,
      ayanamsha: row.ayanamsha,
      computed_by: row.computed_by,
    }),
    source_canonical_id: 'VARSHAPHALA_RAW',
    source_version: '1.0',
    confidence: 0.9,
    significance: 0.75,
  }))

  const result_hash =
    'sha256:' +
    crypto
      .createHash('sha256')
      .update(JSON.stringify(results.map(r => r.content).sort()))
      .digest('hex')

  const latency_ms = Date.now() - start

  const bundle: ToolBundle = {
    tool_bundle_id: crypto.randomUUID(),
    tool_name: TOOL_NAME,
    tool_version: TOOL_VERSION,
    invocation_params: {
      chart_id: chartId,
      year: input.year,
      year_start: yearStart,
      year_end: yearEnd,
      ayanamsha,
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
    data_asset_id: 'VARSHAPHALA',
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
    'Varshaphala (Tajika) annual-chart lookup. Returns the Solar Return UTC, Ascendant, ' +
    'and 9-graha sidereal positions for one year (param: year), a year range (param: ' +
    'year_start/year_end), or the years implied by plan.time_window. Substrate is engine-' +
    'computed via pyswisseph + Lahiri; covers 1984-2061 for the native chart. Year-lord ' +
    '(Varshesha) and Muntha are NOT included — they live at the synthesis layer.',
  retrieve,
}
