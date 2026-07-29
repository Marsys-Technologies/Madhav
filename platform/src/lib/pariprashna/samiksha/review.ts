import 'server-only'
/**
 * SAMĪKṢĀ review-surface reads — PB-3 (SAMĪKṢĀ) lane L-3.
 *
 * Server-side data assembly for `/clients/[id]/samiksha`'s three sections (§14.4):
 *   • Awaiting confirmation — `detected` candidates (one-tap confirm/edit/dismiss).
 *   • Open               — `open` predictions, live timeline (window running).
 *   • Resolve            — `window_closed` predictions (resolve happened/didn't/partial/can't-tell).
 * Plus the W-2 non-shameful coverage statistic and the read-only deep-link turn anchors.
 *
 * All reads go through the injectable executor (same seam as the L-1 DAL) so the surface's data
 * layer is testable against a real migrated throwaway Postgres.
 */

import { query as sharedQuery } from '@/lib/db/client'
import { LEDGER_TABLE, type LedgerRow } from './schema'
import { listLedgerRowsForChart } from './reader'
import type { LedgerExecutor } from './writer'
import type { TurnDeepLinkTarget } from './deepLink'

const defaultExecutor: LedgerExecutor = <T,>(sql: string, params?: unknown[]) =>
  sharedQuery(sql, params as unknown[]).then((r) => ({ rows: r.rows as T[], rowCount: r.rowCount }))

/**
 * Coverage — reported as a NEUTRAL statistic (W-2): no red counters, no "you failed to
 * resolve X" framing. `resolvedCount` + `unverifiableCount` are both "attended to"; `lapsed`
 * is simply the not-yet-resolved remainder, never styled as a debt.
 */
export interface CoverageStats {
  /** window_closed rows resolved with a scorable outcome. */
  resolvedCount: number
  /** window_closed rows resolved as can't-tell (unverifiable — Brier-excluded honesty metric). */
  unverifiableCount: number
  /** window_closed rows that lapsed unresolved (W-2: a neutral coverage gap, not a failure). */
  lapsedCount: number
  /** predictions currently open (window running — nothing to do yet). */
  openCount: number
  /** detected candidates awaiting confirmation. */
  awaitingCount: number
  /**
   * Coverage fraction in [0,1]: of the windows that have CLOSED and reached a terminal
   * resolution or lapse, how many were attended to (resolved OR marked unverifiable). Null when
   * no window has closed yet (nothing to take a fraction of — an honest null, not 0 or 1).
   */
  coverageFraction: number | null
}

export interface ReviewData {
  awaiting: LedgerRow[]
  open: LedgerRow[]
  resolvable: LedgerRow[]
  coverage: CoverageStats
  /** message_part_id → read-only deep-link target, for rows whose claim resolves to a turn. */
  turnAnchors: Record<string, TurnDeepLinkTarget>
}

/** Chart-scoped lifecycle-state census (single grouped read) → the coverage statistic. */
export async function getCoverageStats(
  chartId: string,
  exec: LedgerExecutor = defaultExecutor,
): Promise<CoverageStats> {
  const { rows } = await exec<{ lifecycle_status: string; n: string }>(
    `SELECT lifecycle_status, count(*)::text AS n FROM ${LEDGER_TABLE}
      WHERE chart_id = $1 GROUP BY lifecycle_status`,
    [chartId],
  )
  const by: Record<string, number> = {}
  for (const r of rows) by[r.lifecycle_status] = Number(r.n)

  const resolvedCount = by['outcome_recorded'] ?? 0
  const unverifiableCount = by['unverifiable'] ?? 0
  const lapsedCount = by['lapsed'] ?? 0
  const openCount = by['open'] ?? 0
  const awaitingCount = by['detected'] ?? 0

  const attended = resolvedCount + unverifiableCount
  const closedTerminal = attended + lapsedCount
  const coverageFraction = closedTerminal === 0 ? null : attended / closedTerminal

  return { resolvedCount, unverifiableCount, lapsedCount, openCount, awaitingCount, coverageFraction }
}

/**
 * Resolve read-only deep-link turn anchors for a set of ledger rows. Reads message_parts →
 * conversation_messages to derive each part's thread (conversation) id and 1-based turn
 * ordinal (assistant turns, chronological). PURE READ — a SELECT with a window function; it
 * cannot mutate a turn (P1 holds by construction). Rows with no `message_part_id` (W-6 scripted
 * / backfilled claims) simply have no anchor.
 */
export async function resolveTurnAnchors(
  chartId: string,
  rows: Pick<LedgerRow, 'message_part_id'>[],
  exec: LedgerExecutor = defaultExecutor,
): Promise<Record<string, TurnDeepLinkTarget>> {
  const partIds = Array.from(
    new Set(rows.map((r) => r.message_part_id).filter((v): v is string => !!v)),
  )
  if (partIds.length === 0) return {}

  const { rows: resolved } = await exec<{
    message_part_id: string
    conversation_id: string
    turn_ordinal: string
  }>(
    `WITH ordered AS (
       SELECT cm.id AS message_id, cm.conversation_id,
              row_number() OVER (PARTITION BY cm.conversation_id ORDER BY cm.created_at, cm.id) AS turn_ordinal
         FROM conversation_messages cm
        WHERE cm.role = 'assistant'
     )
     SELECT mp.id AS message_part_id, o.conversation_id, o.turn_ordinal::text AS turn_ordinal
       FROM message_parts mp
       JOIN ordered o ON o.message_id = mp.message_id
      WHERE mp.id = ANY($1)`,
    [partIds],
  )

  const out: Record<string, TurnDeepLinkTarget> = {}
  for (const r of resolved) {
    out[r.message_part_id] = {
      chartId,
      conversationId: r.conversation_id,
      turnOrdinal: Number(r.turn_ordinal),
    }
  }
  return out
}

/** Assemble everything the review surface renders, for one chart. */
export async function getReviewData(
  chartId: string,
  exec: LedgerExecutor = defaultExecutor,
): Promise<ReviewData> {
  const [awaiting, open, resolvable, coverage] = await Promise.all([
    listLedgerRowsForChart(chartId, { status: 'detected' }, exec),
    listLedgerRowsForChart(chartId, { status: 'open' }, exec),
    listLedgerRowsForChart(chartId, { status: 'window_closed' }, exec),
    getCoverageStats(chartId, exec),
  ])
  const turnAnchors = await resolveTurnAnchors(chartId, [...awaiting, ...open, ...resolvable], exec)
  return { awaiting, open, resolvable, coverage, turnAnchors }
}
