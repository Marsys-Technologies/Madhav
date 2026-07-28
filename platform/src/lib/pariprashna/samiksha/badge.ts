import 'server-only'
/**
 * SAMĪKṢĀ dashboard badge count — PB-3 (SAMĪKṢĀ) lane L-3.
 *
 * The ONE production source of the "needs your attention" badge numeral. BRIEF_PB-3 §F1
 * (Lane L-3): the badge counts `detected` + `window_closed` rows — the two lifecycle states
 * that are genuinely waiting on a HUMAN act (a `detected` candidate awaits confirmation; a
 * `window_closed` prediction awaits resolution). It deliberately does NOT count `open`
 * (nothing to do yet — the window is still running) nor any terminal state.
 *
 * DESIGN RULE (§10.2 / W-2): this numeral is rendered in `--pp-gold-dim`, NEVER red, and is
 * never framed as a debt/shame counter. A badge of 5 means "five items you could act on",
 * not "five failures". The count itself is a neutral statistic; see coverage stats in
 * review.ts for the non-shameful lapsed reporting.
 *
 * count_sql (canonical, chart-scoped — mirrors the table COMMENT in migration 470):
 *   SELECT count(*) FROM brahma_mimamsa_prediction_ledger
 *    WHERE chart_id = $1 AND lifecycle_status = ANY($2)
 *
 * Injectable executor (same seam as the L-1 writer/reader) so the "badge equals SQL truth"
 * acceptance test drives THIS exact function against a real migrated throwaway Postgres — not
 * a re-implementation that could agree with itself while both are wrong (the PB-2
 * false-confidence-gate lesson, FOLLOWUP_PB-2_BYTE_EQUALITY_FIXTURE_COVERAGE.md).
 */

import { query as sharedQuery } from '@/lib/db/client'
import { LEDGER_TABLE, type LifecycleState } from './schema'
import type { LedgerExecutor } from './writer'

/**
 * The two lifecycle states that put a row on the badge: something a human must do next.
 * `detected` → awaiting confirmation; `window_closed` → awaiting resolution. Exported so the
 * acceptance test asserts against the SAME set the production count uses (no drift).
 */
export const BADGE_LIFECYCLE_STATES: readonly LifecycleState[] = ['detected', 'window_closed'] as const

const defaultExecutor: LedgerExecutor = <T,>(sql: string, params?: unknown[]) =>
  sharedQuery(sql, params as unknown[]).then((r) => ({ rows: r.rows as T[], rowCount: r.rowCount }))

/**
 * The badge numeral for a chart: count of rows in a badge lifecycle state. This is the single
 * production computation the rendered `<SamiksaBadge>` displays. Returns a plain integer.
 */
export async function countBadge(
  chartId: string,
  exec: LedgerExecutor = defaultExecutor,
): Promise<number> {
  const { rows } = await exec<{ count: string }>(
    `SELECT count(*)::text AS count FROM ${LEDGER_TABLE}
      WHERE chart_id = $1 AND lifecycle_status = ANY($2)`,
    [chartId, BADGE_LIFECYCLE_STATES as unknown as string[]],
  )
  return Number(rows[0]?.count ?? 0)
}
