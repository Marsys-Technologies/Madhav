import 'server-only'
import type { Queryable } from '@/lib/build/runPreparation'

/**
 * Chart-context staleness marking (Jātaka chart workspace, Phase-A2/Phase-A3
 * item 2).
 *
 * Invariant: data created from former birth details remains available as
 * historical evidence but cannot be treated as current chart truth. A birth-
 * details correction (recomputeChart.ts) preserves five kinds of rows that no
 * rebuild regenerates on its own schedule:
 *   - `event_chart_state_index` (migration 1122) — its only writer is a manual
 *     CLI seed, never the build DAG;
 *   - `mimamsa_predictions` (migration 1122) rows whose lifecycle has moved
 *     past `pending`/`due` (real, native-verified outcomes mi_bhavisya's own
 *     rebuild never destroys — see its DELETE-scope guard);
 *   - `brahma_mimamsa_prediction_ledger` (migration 1123) — Samīkṣā's own
 *     human-review ledger; a correction never regenerates it, only the sweep
 *     and human confirmation ever transition it;
 *   - `brahma_prospective_ledger` (migration 1123) — the standing-predictions
 *     ledger;
 *   - `mimamsa_calibration_snapshot` (migration 1123) — no build-DAG asset
 *     clears it today (mi_gunanaka's own registered clear target is
 *     mimamsa_multipliers, a different table).
 * This module marks all five kinds stale — orthogonal metadata that is never a
 * lifecycle/outcome/claim value, so the fact itself is preserved exactly as
 * computed and only an additive marker says it is no longer current.
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

/**
 * Every preserved surface a birth-details correction marks stale instead of
 * deleting: migration 1122's event_chart_state_index/mimamsa_predictions, and
 * migration 1123's three deferred surfaces (Phase-A3) —
 * brahma_mimamsa_prediction_ledger (Samīkṣā's own ledger; the new columns sit
 * outside migration 470's trg_bmpl_freeze_confirmed equality check, so marking
 * a confirmed row stale never conflicts with its freeze), brahma_prospective_ledger,
 * and mimamsa_calibration_snapshot (confirmed chart-scoped — one chart_id per
 * row, no cross-chart aggregation — before this surface was added).
 */
const STALE_MARKED_TABLES = [
  'event_chart_state_index',
  'mimamsa_predictions',
  'brahma_mimamsa_prediction_ledger',
  'brahma_prospective_ledger',
  'mimamsa_calibration_snapshot',
] as const

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
  return STALE_MARKED_TABLES.map(stale)
}

export async function markChartContextStale(args: { db: Queryable; chartId: string; runId: string }): Promise<void> {
  for (const statement of staleMarkingStatements(args.chartId, args.runId)) {
    await args.db.query(statement.sql, statement.params)
  }
}
