/**
 * MARSYS-JIS Retrieval Tool: lel_query (M5-A)
 *
 * Queries the life_events table — 36 ground-truth events from
 * LIFE_EVENT_LOG_v1_2.md (canonical_id: LEL), each with Swiss Ephemeris
 * chart_state snapshots.
 *
 * WHY THIS TOOL EXISTS:
 *   - timeline_query surfaces dasha arcs from rag_chunks (structural, L5).
 *   - lel_query surfaces ACTUAL RECORDED EVENTS — dates, categories, and
 *     Swiss Ephemeris chart state at the moment of each event (L1 ground truth).
 *   - Without lel_query, the synthesis model fabricates predictions for events
 *     that have already occurred (e.g. inferring marriage from dasha windows
 *     instead of reading the recorded marriage date).
 *
 * Use when the query involves: recorded life events, known outcomes,
 * relationship/marriage/career event history, ground-truth dates,
 * or retroactive validation of astrological patterns.
 */

import crypto from 'crypto'
import { getStorageClient } from '@/lib/storage'
import { validate } from '@/lib/schemas'
import { telemetry } from '@/lib/telemetry'
import { writeToolExecutionLog } from '@/lib/db/monitoring-write'
import type { QueryPlan, ToolBundle, ToolBundleResult, RetrievalTool } from './types'

const TOOL_NAME = 'lel_query'
const TOOL_VERSION = '1.0.0'

export interface LelQueryInput {
  /** Filter events on or after this date (YYYY-MM-DD). */
  start_date?: string
  /** Filter events on or before this date (YYYY-MM-DD). */
  end_date?: string
  /** Filter by life event category. */
  category?:
    | 'career'
    | 'health'
    | 'family'
    | 'relationship'
    | 'spiritual'
    | 'travel'
    | 'finance'
    | 'education'
    | 'residential'
    | 'creative'
    | 'loss'
    | 'other'
  /** Filter by significance level. */
  significance?: 'major' | 'moderate' | 'minor'
  /** Maximum rows to return (default 50, max 50). */
  limit?: number
}

interface LifeEventRow {
  event_id: string
  event_date: string
  category: string
  description: string
  significance: string
  chart_state: unknown
  source_section: string | null
}

function buildQuery(p: LelQueryInput): { sql: string; args: unknown[] } {
  const conditions: string[] = []
  const args: unknown[] = []
  let idx = 1

  if (p.start_date) {
    conditions.push(`event_date >= $${idx++}`)
    args.push(p.start_date)
  }
  if (p.end_date) {
    conditions.push(`event_date <= $${idx++}`)
    args.push(p.end_date)
  }
  if (p.category) {
    conditions.push(`category = $${idx++}`)
    args.push(p.category)
  }
  if (p.significance) {
    conditions.push(`significance = $${idx++}`)
    args.push(p.significance)
  }

  const where = conditions.length > 0 ? `WHERE ${conditions.join(' AND ')}` : ''
  const limit = Math.min(p.limit ?? 50, 50)

  const sql = `
    SELECT event_id, event_date, category, description, significance,
           chart_state, source_section
    FROM life_events
    ${where}
    ORDER BY event_date ASC
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
      data_asset_id: 'LEL',
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
  const p: LelQueryInput = {
    start_date: params?.start_date as string | undefined,
    end_date: params?.end_date as string | undefined,
    category: params?.category as LelQueryInput['category'],
    significance: params?.significance as LelQueryInput['significance'],
    limit: params?.limit as number | undefined,
  }

  const { sql, args } = buildQuery(p)
  const { rows } = await getStorageClient().query<LifeEventRow>(sql, args)

  const results: ToolBundleResult[] = rows.map((row) => ({
    content: JSON.stringify({
      event_id: row.event_id,
      event_date: row.event_date,
      category: row.category,
      description: row.description,
      significance: row.significance,
      chart_state: row.chart_state,
      source_section: row.source_section,
    }),
    source_canonical_id: 'LEL',
    source_version: '1.6',
    confidence: 1.0,      // Ground-truth recorded events — confidence is always 1.0
    significance: 1.0,    // LEL events are definitionally significant L1 facts
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
      start_date: p.start_date,
      end_date: p.end_date,
      category: p.category,
      significance: p.significance,
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
      `lel_query: ToolBundle schema validation failed: ${JSON.stringify(validation.errors)}`
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
    data_asset_id: 'LEL',
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
    'Retrieves ground-truth life events from LIFE_EVENT_LOG_v1_2.md (LEL). ' +
    'Returns recorded event dates, categories, descriptions, significance, and Swiss Ephemeris ' +
    'chart_state at the time of each event. Use for: known marriage/relationship dates, career ' +
    'transitions, health events, family events, travel, and any factual outcome validation. ' +
    'This is L1 ground truth — always prefer over timeline_query for known historical events.',
  retrieve,
}
