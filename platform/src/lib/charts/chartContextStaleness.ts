import 'server-only'
import type { Queryable } from '@/lib/build/runPreparation'

/**
 * Chart-context staleness marking (Jātaka chart workspace, Phase-A2 item 2).
 *
 * Invariant: data created from former birth details remains available as
 * historical evidence but cannot be treated as current chart truth. A birth-
 * details correction (recomputeChart.ts) preserves two kinds of rows that no
 * rebuild regenerates on its own schedule: `event_chart_state_index` (its only
 * writer is a manual CLI seed, never the build DAG) and `mimamsa_predictions`
 * rows whose lifecycle has moved past `pending`/`due` (real, native-verified
 * outcomes mi_bhavisya's own rebuild never destroys — see its DELETE-scope
 * guard). This module marks BOTH kinds stale — orthogonal metadata (migration
 * 1122) that is never a lifecycle/outcome value, so the fact itself is
 * preserved exactly as computed and only an additive marker says it is no
 * longer current.
 *
 * Marks every row for the chart, not only rows of a particular status: at the
 * moment of correction (before the dispatched rebuild has run) even a
 * `pending` prediction reflects the former birth details, and stays stale in
 * the window until the rebuild's own delete-then-insert replaces it.
 *
 * Idempotent per row (`WHERE chart_context_stale_at IS NULL`): a row already
 * staled by an earlier correction keeps that correction's stamp — the
 * originally superseding run, not the latest one that happened to touch the
 * chart again before a rebuild ever cleared it.
 */

export function staleMarkingStatements(chartId: string, runId: string): Array<{ sql: string; params: unknown[] }> {
  const params = [chartId, runId]
  const stale = (table: string) => ({
    sql: `UPDATE ${table}
             SET chart_context_stale_at = NOW(),
                 chart_context_stale_reason = 'chart_details_changed',
                 chart_context_superseded_by_run_id = $2
           WHERE chart_id = $1
             AND chart_context_stale_at IS NULL`,
    params,
  })
  return [stale('event_chart_state_index'), stale('mimamsa_predictions')]
}

export async function markChartContextStale(args: { db: Queryable; chartId: string; runId: string }): Promise<void> {
  for (const statement of staleMarkingStatements(args.chartId, args.runId)) {
    await args.db.query(statement.sql, statement.params)
  }
}
