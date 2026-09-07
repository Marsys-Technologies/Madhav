import 'server-only'
/**
 * The window-opening ask — THE FIRE CONDITION (lane P4-G).
 *
 * The one question this module answers: *is there a real, closed prediction window on this
 * chart that the instrument should raise, right now?* The answer is read from the database.
 * It is never inferred from a timer, a heuristic, a fixture, or the shape of the conversation.
 *
 * ── §N.8: WHAT CODE PATH FAILS SO THAT "THIS WINDOW IS OPEN" CORRECTLY READS FALSE? ────────
 * The Earned-Signal Principle says a status must be computed by a detector that measures the
 * specific claim it asserts, and that the detector must be demonstrated CAPABLE of reporting
 * failure. The claim here is narrow and the detector is the SQL itself, which can fail in four
 * distinguishable ways — each one an observable, testable negative:
 *
 *   1. `no_ledger_rows`        — the chart has no ledger rows at all. Nothing to ask about.
 *   2. `no_window_closed_row`  — rows exist, but none is in `window_closed`. THE IMPORTANT ONE:
 *                                a row still `open` (window running), or already
 *                                `outcome_recorded` / `dismissed` / `lapsed`, does not fire.
 *                                This is the negative case a refuter will probe first.
 *   3. `window_not_yet_past`   — a `window_closed` row whose upper bound is somehow still in
 *                                the future. Defence in depth: the L-4 daily job should never
 *                                produce this, so if it appears, something upstream is wrong
 *                                and the instrument stays quiet rather than asking about a
 *                                window that has not actually ended.
 *   4. `flag_off`              — the feature is disarmed.
 *
 * `evaluateWindowAsk` ALWAYS returns a `census` — the chart's real lifecycle-state histogram,
 * read in the same call — so a negative is EVIDENCED rather than merely asserted. "I looked,
 * and here is exactly what I found" is a different and much stronger claim than "no".
 *
 * ── SELECTION IS TOTALLY ORDERED (§N.7 item 2) ─────────────────────────────────────────────
 * Reducing a set to one row requires a total `ORDER BY`. Here: oldest-closing window first,
 * then `id` as the tiebreak — so two windows that closed on the same day still select
 * deterministically. That determinism is load-bearing beyond tidiness: `capture.ts` relies on
 * the SAME selector returning the SAME row on a later turn.
 */

import { query as sharedQuery } from '@/lib/db/client'
import { LEDGER_TABLE, type LedgerRow } from '../schema'
import type { LedgerExecutor } from '../writer'
import { isWindowAskEnabled } from './flag'
import { composeWindowAsk, type NoComposeReason, type WindowAsk } from './compose'

const defaultExecutor: LedgerExecutor = <T,>(sql: string, params?: unknown[]) =>
  sharedQuery(sql, params as unknown[]).then((r) => ({ rows: r.rows as T[], rowCount: r.rowCount }))

/** The one lifecycle state an ask may fire against: the window ran, and it is over. */
export const ASKABLE_LIFECYCLE_STATE = 'window_closed' as const

const ASK_COLS = `
  id, chart_id, message_part_id, claim_text, domain,
  "window"::text AS window, confidence::text AS confidence, direction,
  technique_refs, grounding_fact_ids, created_from_channel, lifecycle_status,
  build_id, priors_version, formula_versions, ranking_config,
  now_context_date::text AS now_context_date, stamp_copied_at,
  outcome, outcome_value, outcome_note, outcome_recorded_at,
  confirmed_at, dismissed_reason, created_at, updated_at
`

export const NO_ASK_REASONS = [
  'flag_off',
  'no_ledger_rows',
  'no_window_closed_row',
  'window_not_yet_past',
  ...(['severity_suppressed_domain', 'claim_text_unusable', 'window_missing_or_unparseable'] as NoComposeReason[]),
] as const
export type NoAskReason = (typeof NO_ASK_REASONS)[number]

/** The chart's real lifecycle histogram at evaluation time. Evidence for a negative. */
export type LifecycleCensus = Record<string, number>

export type WindowAskDecision =
  | { fired: true; ask: WindowAsk; row: LedgerRow; census: LifecycleCensus; as_of: string }
  | { fired: false; reason: NoAskReason; detail: string; census: LifecycleCensus; as_of: string }

const AS_OF_RE = /^\d{4}-\d{2}-\d{2}$/

/** Chart-scoped lifecycle histogram. Its own read so a negative decision can show its work. */
export async function readLifecycleCensus(
  chartId: string,
  exec: LedgerExecutor = defaultExecutor,
): Promise<LifecycleCensus> {
  const { rows } = await exec<{ lifecycle_status: string; n: string }>(
    `SELECT lifecycle_status, count(*)::text AS n FROM ${LEDGER_TABLE}
      WHERE chart_id = $1 GROUP BY lifecycle_status ORDER BY lifecycle_status`,
    [chartId],
  )
  const out: LifecycleCensus = {}
  for (const r of rows) out[r.lifecycle_status] = Number(r.n)
  return out
}

/**
 * Select THE one askable window for a chart, or null.
 *
 * The predicate is the whole safety argument, so it is spelled out rather than composed:
 *   · `lifecycle_status = 'window_closed'` — not `open` (nothing has ended yet), not `detected`
 *     (never confirmed by a human), not a terminal state (already answered or abandoned);
 *   · `"window" IS NOT NULL`               — a claim with no window has no window to close;
 *   · `upper("window") <= asOf`            — the window really is in the past, re-checked here
 *     rather than trusted from the lifecycle state alone;
 *   · `outcome IS NULL`                    — belt and braces: never re-ask something answered.
 */
export async function selectAskableWindow(
  chartId: string,
  asOf: string,
  exec: LedgerExecutor = defaultExecutor,
): Promise<LedgerRow | null> {
  const { rows } = await exec<LedgerRow>(
    `SELECT ${ASK_COLS} FROM ${LEDGER_TABLE}
      WHERE chart_id = $1
        AND lifecycle_status = '${ASKABLE_LIFECYCLE_STATE}'
        AND "window" IS NOT NULL
        AND upper("window") <= $2::date
        AND outcome IS NULL
      ORDER BY upper("window") ASC, id ASC
      LIMIT 1`,
    [chartId, asOf],
  )
  return rows[0] ?? null
}

/**
 * Decide whether to raise an ask for this chart, and compose it if so.
 *
 * Returns a DECISION, never a thrown error and never a silent null: a negative always carries
 * a reason code and the census that justifies it.
 */
export async function evaluateWindowAsk(args: {
  chartId: string
  asOf: string
  exec?: LedgerExecutor
  /** Test/probe seam ONLY. Production never passes this; the flag is read from the environment. */
  forceEnabled?: boolean
}): Promise<WindowAskDecision> {
  const { chartId, asOf } = args
  if (!AS_OF_RE.test(asOf)) {
    throw new Error(`evaluateWindowAsk: asOf must be ISO yyyy-mm-dd, got ${JSON.stringify(asOf)}`)
  }
  const exec = args.exec ?? defaultExecutor
  const enabled = args.forceEnabled ?? isWindowAskEnabled()

  if (!enabled) {
    return { fired: false, reason: 'flag_off', detail: 'PARIPRASHNA_WINDOW_ASK_ENABLED is off.', census: {}, as_of: asOf }
  }

  const census = await readLifecycleCensus(chartId, exec)
  const total = Object.values(census).reduce((a, b) => a + b, 0)
  const describe = () =>
    total === 0 ? 'chart has no ledger rows' : `chart lifecycle census: ${JSON.stringify(census)}`

  if (total === 0) {
    return { fired: false, reason: 'no_ledger_rows', detail: describe(), census, as_of: asOf }
  }

  const row = await selectAskableWindow(chartId, asOf, exec)
  if (!row) {
    // Distinguish "no closed window at all" from "closed, but not yet past" — two different
    // truths, and collapsing them would hide a real upstream fault behind a routine negative.
    const { rows: futureRows } = await exec<{ n: string }>(
      `SELECT count(*)::text AS n FROM ${LEDGER_TABLE}
        WHERE chart_id = $1 AND lifecycle_status = '${ASKABLE_LIFECYCLE_STATE}'
          AND "window" IS NOT NULL AND upper("window") > $2::date`,
      [chartId, asOf],
    )
    if (Number(futureRows[0]?.n ?? 0) > 0) {
      return {
        fired: false,
        reason: 'window_not_yet_past',
        detail:
          `${futureRows[0].n} row(s) are '${ASKABLE_LIFECYCLE_STATE}' but their window upper ` +
          `bound is still after ${asOf}; staying quiet. ${describe()}`,
        census,
        as_of: asOf,
      }
    }
    return {
      fired: false,
      reason: 'no_window_closed_row',
      detail: `no row in '${ASKABLE_LIFECYCLE_STATE}' awaiting an outcome. ${describe()}`,
      census,
      as_of: asOf,
    }
  }

  const composed = composeWindowAsk(row, asOf)
  if (!composed.composed) {
    return { fired: false, reason: composed.reason, detail: composed.detail, census, as_of: asOf }
  }

  return { fired: true, ask: composed.ask, row, census, as_of: asOf }
}
