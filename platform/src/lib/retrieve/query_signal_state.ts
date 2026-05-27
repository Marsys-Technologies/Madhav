/**
 * MARSYS-JIS Retrieval tool — query_signal_state (M3-B)
 *
 * Surfaces date-indexed signal lit/dormant/ripening rows from the
 * signal_states table (migration 023). Populated by
 * platform/scripts/temporal/signal_activator.py.
 *
 * Always-on (no feature flag). Degrades gracefully when the table is empty
 * (signal_activator has not yet been run for the requested chart/date) — the
 * tool returns an empty results array and a diagnostic content row so callers
 * can detect the empty state without crashing.
 */

import crypto from 'crypto'
import { getStorageClient } from '@/lib/storage'
import { validate } from '@/lib/schemas'
import { telemetry } from '@/lib/telemetry'
import { writeToolExecutionLog } from '@/lib/db/monitoring-write'
import { getActiveChartIdOrNull, requireChartId } from './chart_context'
import type { QueryPlan, ToolBundle, ToolBundleResult, RetrievalTool } from './types'

const TOOL_NAME = 'query_signal_state'
const TOOL_VERSION = '1.0.0'

export type SignalState = 'lit' | 'dormant' | 'ripening'

export interface QuerySignalStateInput {
  /** Optional override; defaults to the native chart id. */
  chart_id?: string
  /** Single date OR start of a range (YYYY-MM-DD). Defaults to today UTC. */
  query_date?: string
  /** End of date range (YYYY-MM-DD); when set, query_date is treated as the start. */
  end_date?: string
  /** Restrict to specific signal IDs (e.g. ['SIG.MSR.001', 'SIG.MSR.002']). */
  signal_ids?: string[]
  /** Restrict to specific states (e.g. ['lit', 'ripening']). */
  states?: SignalState[]
  /** Restrict to a specific dasha_system (e.g. 'vimshottari'). */
  dasha_system?: string
  /** Maximum rows to return; clamped to [1, 500]. */
  limit?: number
}

interface SignalStateRow {
  signal_id: string
  query_date: string  // pg DATE returns string
  state: SignalState
  confidence: number | null
  dasha_system: string | null
  computed_by: string
  ayanamsha: string
}

function buildWhere(p: QuerySignalStateInput): { where: string; args: unknown[] } {
  const conditions: string[] = []
  const args: unknown[] = []
  let idx = 1

  conditions.push(`chart_id = $${idx}`)
  args.push(requireChartId(p.chart_id))
  idx++

  if (p.end_date) {
    conditions.push(`query_date >= $${idx}::date`)
    args.push(p.query_date ?? new Date().toISOString().slice(0, 10))
    idx++
    conditions.push(`query_date <= $${idx}::date`)
    args.push(p.end_date)
    idx++
  } else if (p.query_date) {
    conditions.push(`query_date = $${idx}::date`)
    args.push(p.query_date)
    idx++
  } else {
    conditions.push(`query_date = CURRENT_DATE`)
  }

  if (p.signal_ids && p.signal_ids.length > 0) {
    conditions.push(`signal_id = ANY($${idx}::text[])`)
    args.push(p.signal_ids)
    idx++
  }

  if (p.states && p.states.length > 0) {
    conditions.push(`state = ANY($${idx}::text[])`)
    args.push(p.states)
    idx++
  }

  if (p.dasha_system) {
    conditions.push(`dasha_system = $${idx}`)
    args.push(p.dasha_system)
    idx++
  }

  return { where: conditions.join(' AND '), args }
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
      data_asset_id: 'SIGNAL_STATES',
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
  const embedded = (plan as unknown as Record<string, unknown>).query_signal_state as
    | QuerySignalStateInput
    | undefined
  const p: QuerySignalStateInput = { ...embedded, ...(params as QuerySignalStateInput | undefined) }

  const limit = Math.min(Math.max(p.limit ?? 100, 1), 500)
  const { where, args } = buildWhere(p)

  const sql = `
    SELECT signal_id, query_date::text AS query_date, state, confidence,
           dasha_system, computed_by, ayanamsha
    FROM signal_states
    WHERE ${where}
    ORDER BY query_date, signal_id
    LIMIT ${limit}
  `.trim()

  let rows: SignalStateRow[] = []
  let degraded_reason: string | null = null
  try {
    const result = await getStorageClient().query<SignalStateRow>(sql, args)
    rows = result.rows
  } catch (err) {
    // Graceful degradation: surface as empty result + diagnostic, do not throw.
    degraded_reason =
      err instanceof Error ? `signal_states query failed: ${err.message}` : 'signal_states query failed'
  }

  const results: ToolBundleResult[] = rows.map((r) => ({
    content: JSON.stringify({
      signal_id: r.signal_id,
      query_date: r.query_date,
      state: r.state,
      confidence: r.confidence,
      dasha_system: r.dasha_system,
      computed_by: r.computed_by,
      ayanamsha: r.ayanamsha,
    }),
    source_canonical_id: 'SIGNAL_STATES',
    source_version: '1.0',
    confidence: r.confidence ?? (
      r.state === 'lit'      ? 0.85 :
      r.state === 'ripening' ? 0.65 :
      r.state === 'dormant'  ? 0.35 : 0.5
    ),
    significance: r.state === 'lit' ? 0.9 : r.state === 'ripening' ? 0.6 : 0.3,
    signal_id: r.signal_id,
  }))

  if (results.length === 0) {
    results.push({
      content: JSON.stringify({
        note: degraded_reason
          ? degraded_reason
          : 'signal_states empty for the requested chart/date — run signal_activator.py to populate',
        chart_id: getActiveChartIdOrNull(p.chart_id),
        query_date: p.query_date ?? null,
        end_date: p.end_date ?? null,
      }),
      source_canonical_id: 'SIGNAL_STATES',
      source_version: '1.0',
      confidence: 0,
      significance: 0,
    })
  }

  const result_hash =
    'sha256:' +
    crypto
      .createHash('sha256')
      .update(JSON.stringify(results.map((r) => r.content.slice(0, 80)).sort()))
      .digest('hex')

  const latency_ms = Date.now() - start

  const bundle: ToolBundle = {
    tool_bundle_id: crypto.randomUUID(),
    tool_name: TOOL_NAME,
    tool_version: TOOL_VERSION,
    invocation_params: {
      chart_id: getActiveChartIdOrNull(p.chart_id),
      query_date: p.query_date,
      end_date: p.end_date,
      signal_ids: p.signal_ids,
      states: p.states,
      dasha_system: p.dasha_system,
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
      `query_signal_state: ToolBundle schema validation failed: ${JSON.stringify(validation.errors)}`
    )
  }

  telemetry.recordLatency(TOOL_NAME, 'retrieve', latency_ms)

  void writeToolExecutionLog({
    query_id: plan.query_plan_id,
    tool_name: TOOL_NAME,
    params_json: bundle.invocation_params as Record<string, unknown>,
    status: rows.length === 0 ? 'zero_rows' : 'ok',
    rows_returned: rows.length,
    latency_ms,
    token_estimate: Math.ceil(JSON.stringify(results).length / 4),
    data_asset_id: 'SIGNAL_STATES',
    error_code: degraded_reason,
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
