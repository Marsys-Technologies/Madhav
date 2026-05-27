/**
 * MARSYS-JIS Stream B — Tool: query_kp_ruling_planets (M3-W3-C2)
 *
 * Reads from the kp_sublords table for a given chart_id and returns the
 * star lord / sub lord / sub-sub lord chains for the 9 grahas as a
 * ToolBundle.
 *
 * Distinct from kp_query.ts (which reads chart_facts category=kp_*):
 *   - kp_query.ts        → FORENSIC §4 KP authoritative values (chart_facts)
 *   - this tool          → engine-computed sub-lord substrate (kp_sublords),
 *                          produced by platform/scripts/temporal/compute_kp.py
 *
 * Both tools coexist; consumers prefer chart_facts when chart_id matches a
 * FORENSIC-anchored native. This tool is the substrate for non-FORENSIC
 * charts and for forward-looking transit-time KP queries (when later
 * extended to time-indexed lookups).
 *
 * Schema reference: platform/migrations/024_kp_sublords.sql
 * Cross-check:      05_TEMPORAL_ENGINES/kp/CROSSCHECK_v1_0.md
 */

import crypto from 'crypto'
import { getStorageClient } from '@/lib/storage'
import { writeToolExecutionLog } from '@/lib/db/monitoring-write'
import { requireChartId } from './chart_context'
import type { QueryPlan, ToolBundle, ToolBundleResult, RetrievalTool } from './types'

const TOOL_NAME = 'query_kp_ruling_planets'
const TOOL_VERSION = '1.0'

export interface QueryKpRulingPlanetsInput {
  chart_id?: string
  planet?: string
  ayanamsha?: string
}

interface KpSublordsRow {
  chart_id: string
  planet: string
  sidereal_lon: string | number
  sign: string
  nakshatra: string
  nakshatra_lord: string
  sub_lord: string
  sub_sub_lord: string
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
      data_asset_id: 'KP_SUBLORDS',
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
  const input = (params ?? {}) as QueryKpRulingPlanetsInput
  const chartId = requireChartId(input.chart_id)
  const ayanamsha = input.ayanamsha ?? 'lahiri'

  const conditions: string[] = ['chart_id = $1', 'ayanamsha = $2']
  const queryParams: unknown[] = [chartId, ayanamsha]
  let idx = 3

  if (input.planet) {
    conditions.push(`planet ILIKE $${idx}`)
    queryParams.push(input.planet)
    idx++
  }

  const sql = `
    SELECT chart_id, planet, sidereal_lon, sign, nakshatra,
           nakshatra_lord, sub_lord, sub_sub_lord, ayanamsha, computed_by
    FROM kp_sublords
    WHERE ${conditions.join(' AND ')}
    ORDER BY
      CASE planet
        WHEN 'Sun'     THEN 1
        WHEN 'Moon'    THEN 2
        WHEN 'Mars'    THEN 3
        WHEN 'Mercury' THEN 4
        WHEN 'Jupiter' THEN 5
        WHEN 'Venus'   THEN 6
        WHEN 'Saturn'  THEN 7
        WHEN 'Rahu'    THEN 8
        WHEN 'Ketu'    THEN 9
        ELSE 10
      END
    LIMIT 50
  `.trim()

  const { rows } = await getStorageClient().query<KpSublordsRow>(sql, queryParams)

  const results: ToolBundleResult[] = rows.map(row => ({
    content: JSON.stringify({
      planet: row.planet,
      sidereal_lon: Number(row.sidereal_lon),
      sign: row.sign,
      nakshatra: row.nakshatra,
      star_lord: row.nakshatra_lord,
      sub_lord: row.sub_lord,
      sub_sub_lord: row.sub_sub_lord,
      ayanamsha: row.ayanamsha,
      computed_by: row.computed_by,
    }),
    source_canonical_id: 'KP_SUBLORDS_RAW',
    source_version: '1.0',
    confidence: 0.95,
    significance: 0.8,
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
      planet: input.planet,
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
    data_asset_id: 'KP_SUBLORDS',
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
    'Engine-computed KP (Krishnamurti Paddhati) ruling-planet table from kp_sublords. ' +
    'Returns star lord / sub lord / sub-sub lord chain for each of the 9 grahas at the ' +
    'native chart moment. Distinct from kp_query (which reads FORENSIC §4 chart_facts); ' +
    'this tool is the swisseph-Lahiri substrate. Use either tool for KP queries; consumers ' +
    'prefer kp_query when chart_id is FORENSIC-anchored.',
  retrieve,
}
