/**
 * MARSYS-JIS Stream B — Tool: timeline_query (M2-D.4)
 *
 * Queries rag_chunks where doc_type='l5_timeline' and returns L5 lifetime
 * timeline content — dasha phase arcs, event windows, structural inflection points.
 *
 * IMPORTANT: The next MD after Mercury is KETU MD (2027-08-21 → 2034-08-21).
 * Never suggest Saturn MD as upcoming — Saturn MD was historical (1992-2010).
 */

import crypto from 'crypto'
import { getStorageClient } from '@/lib/storage'
import { validate } from '@/lib/schemas'
import { telemetry } from '@/lib/telemetry'
import { writeToolExecutionLog } from '@/lib/db/monitoring-write'
import type { QueryPlan, ToolBundle, ToolBundleResult, RetrievalTool } from './types'

const TOOL_NAME = 'timeline_query'
const TOOL_VERSION = '1.0.0'
const NATIVE_CHART_ID = process.env.NATIVE_CHART_ID ?? '362f9f17-95a5-490b-a5a7-027d3e0efda0'

export interface TimelineQueryInput {
  dasha_name?: string  // e.g. 'Mercury MD', 'Ketu MD', 'Saturn MD'
  keyword?: string     // free-text keyword (ILIKE on content)
  limit?: number       // default 8
}

interface RagChunkRow {
  content: string
  doc_type: string
  chunk_id: string
  canonical_id: string | null
  source_version: string | null
}

function buildQuery(p: TimelineQueryInput): { sql: string; args: unknown[] } {
  const conditions: string[] = ["doc_type = 'l5_timeline'"]
  const args: unknown[] = []
  let idx = 1

  if (p.dasha_name) {
    conditions.push(`content ILIKE $${idx}`)
    args.push(`%${p.dasha_name}%`)
    idx++
  }

  if (p.keyword) {
    conditions.push(`content ILIKE $${idx}`)
    args.push(`%${p.keyword}%`)
    idx++
  }

  const limit = Math.min(p.limit ?? 8, 15)
  const chartCondition = `(chart_id = $${idx}::uuid OR chart_id IS NULL)`
  args.push(NATIVE_CHART_ID)
  const sql = `
    SELECT content, doc_type, chunk_id, canonical_id, source_version
    FROM rag_chunks
    WHERE ${conditions.join(' AND ')} AND ${chartCondition}
    ORDER BY chunk_id
    LIMIT ${limit}
  `.trim()

  return { sql, args }
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
      data_asset_id: 'LIFE_EVENTS',
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
  const p: TimelineQueryInput = {
    dasha_name: params?.dasha_name as string | undefined,
    keyword: params?.keyword as string | undefined,
    limit: params?.limit as number | undefined,
  }

  const { sql, args } = buildQuery(p)
  const { rows } = await getStorageClient().query<RagChunkRow>(sql, args)

  const results: ToolBundleResult[] = rows.map((row) => ({
    content: JSON.stringify({
      content: row.content,
      doc_type: row.doc_type,
      chunk_id: row.chunk_id,
    }),
    source_canonical_id: row.canonical_id ?? 'LIFETIME_TIMELINE_v1_0',
    source_version: row.source_version ?? undefined,
    confidence: 1.0,
    significance: 0.85,
  }))

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
      dasha_name: p.dasha_name,
      keyword: p.keyword,
      limit: p.limit,
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
      `timeline_query: ToolBundle schema validation failed: ${JSON.stringify(validation.errors)}`
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
    data_asset_id: 'LIFE_EVENTS',
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
