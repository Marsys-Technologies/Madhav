import 'server-only'
/**
 * SAMĪKṢĀ prediction-ledger reader DAL — PB-3 lane L-1.
 *
 * Read half for `brahma_mimamsa_prediction_ledger`. Shares the injectable executor with the
 * writer (writer.ts) so reads can be exercised against the same real throwaway DB in tests.
 */

import { query as sharedQuery } from '@/lib/db/client'
import { LEDGER_TABLE, type LedgerRow, type LifecycleState } from './schema'
import type { LedgerExecutor } from './writer'

const defaultExecutor: LedgerExecutor = <T,>(sql: string, params?: unknown[]) =>
  sharedQuery(sql, params as unknown[]).then((r) => ({ rows: r.rows as T[], rowCount: r.rowCount }))

const SELECT_COLS = `
  id, chart_id, message_part_id, claim_text, domain,
  "window"::text AS window, confidence::text AS confidence, direction,
  technique_refs, grounding_fact_ids, created_from_channel, lifecycle_status,
  build_id, priors_version, formula_versions, ranking_config,
  now_context_date::text AS now_context_date, stamp_copied_at,
  outcome, outcome_value, outcome_note, outcome_recorded_at,
  confirmed_at, dismissed_reason, created_at, updated_at
`

export async function getLedgerRow(
  id: string,
  exec: LedgerExecutor = defaultExecutor,
): Promise<LedgerRow | null> {
  const { rows } = await exec<LedgerRow>(
    `SELECT ${SELECT_COLS} FROM ${LEDGER_TABLE} WHERE id = $1`,
    [id],
  )
  return rows[0] ?? null
}

export async function listLedgerRowsForChart(
  chartId: string,
  opts: { status?: LifecycleState } = {},
  exec: LedgerExecutor = defaultExecutor,
): Promise<LedgerRow[]> {
  const params: unknown[] = [chartId]
  let where = 'chart_id = $1'
  if (opts.status) {
    where += ' AND lifecycle_status = $2'
    params.push(opts.status)
  }
  const { rows } = await exec<LedgerRow>(
    `SELECT ${SELECT_COLS} FROM ${LEDGER_TABLE} WHERE ${where} ORDER BY created_at DESC`,
    params,
  )
  return rows
}
