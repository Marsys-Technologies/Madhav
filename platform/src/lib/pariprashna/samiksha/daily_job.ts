/**
 * SAMĪKṢĀ consolidated daily job — PB-3 (SAMĪKṢĀ) lane L-4.
 *
 * ONE scheduled run doing all three things §14.5 lists, NOT three cron entries. T-3 binds
 * (BRIEF_PB-3 §F1 L-4: "every always-on subsystem is a future 2 a.m. debugging problem"), so
 * everything below is a single pass:
 *
 *   (a) open AND window_end < asOf   → transition to `window_closed` (via the L-1 DAL's
 *       legal-transition matrix — NEVER raw SQL that bypasses it). The rows left in
 *       `window_closed` ARE the resolution queue: L-3's Resolve tab picks them up. There is no
 *       separate queue table (the brief does not imply one — the lifecycle state is the queue).
 *   (b) closing_soon at window_end − `closingSoonDays` (default 14): a DERIVED, non-persisted
 *       condition (the 9-state lifecycle has no `closing_soon` state — verified against
 *       schema.ts LIFECYCLE_STATES / migration 470's CHECK). The job detects it and includes
 *       those rows in the digest; it writes no new state for them.
 *   (c) ONE consolidated digest, dispatched only when non-empty, per-day idempotent (via the
 *       DigestJournal), with an `asOf` simulated clock. Transport is W-5 log-only stub by default.
 *
 * Idempotency (the honesty-standard requirement, proven by re-running against real data):
 *   - transitions are idempotent by construction — a second run finds no `open` row past its
 *     window (they are already `window_closed`), so it performs zero further transitions;
 *   - the digest is gated by the journal — a second run for the same `asOf` sees `hasSent` true
 *     and dispatches nothing.
 */

import { query as sharedQuery } from '@/lib/db/client'
import { transitionLifecycle, type LedgerExecutor } from './writer'
import { LEDGER_TABLE, type LedgerRow } from './schema'
import {
  renderDigest,
  toDigestItem,
  digestIsEmpty,
  LogOnlyTransport,
  type DigestPayload,
  type DigestTransport,
} from './digest'
import { FileDigestJournal, type DigestJournal, type DigestSentRecord } from './digest_journal'

const defaultExecutor: LedgerExecutor = <T,>(sql: string, params?: unknown[]) =>
  sharedQuery(sql, params as unknown[]).then((r) => ({ rows: r.rows as T[], rowCount: r.rowCount }))

const AS_OF_RE = /^\d{4}-\d{2}-\d{2}$/

const READ_COLS = `
  id, chart_id, message_part_id, claim_text, domain,
  "window"::text AS window, confidence::text AS confidence, direction,
  technique_refs, grounding_fact_ids, created_from_channel, lifecycle_status,
  build_id, priors_version, formula_versions, ranking_config,
  now_context_date::text AS now_context_date, stamp_copied_at,
  outcome, outcome_value, outcome_note, outcome_recorded_at,
  confirmed_at, dismissed_reason, created_at, updated_at
`

export interface DailyJobOptions {
  /** The run's notion of "now" — ISO yyyy-mm-dd. The `--as-of` simulated clock. Required. */
  asOf: string
  /** Optional chart scope; when omitted the job sweeps ALL charts. */
  chartId?: string
  /** Runway (days) for the closing-soon window. Default 14 (BRIEF_PB-3 §F1 L-4). */
  closingSoonDays?: number
  /** Injectable DB executor (tests point this at a real throwaway Postgres). */
  exec?: LedgerExecutor
  /** Per-day digest idempotency store. Default: FileDigestJournal. */
  journal?: DigestJournal
  /** Digest transport. Default: LogOnlyTransport (W-5 stub). */
  transport?: DigestTransport
}

export interface DailyJobResult {
  as_of: string
  /** Ids transitioned open → window_closed THIS run. */
  closed_row_ids: string[]
  /** Ids detected as closing-soon (state unchanged). */
  closing_soon_row_ids: string[]
  /** True iff a digest was dispatched to the transport this run. */
  digest_dispatched: boolean
  /** Why no digest was dispatched: 'empty' (nothing to report) or 'already_sent' (idempotent skip). */
  digest_skipped_reason: 'empty' | 'already_sent' | null
  /** Transport identity used, when a digest was dispatched. */
  transport_mode: string | null
  /** Whether the transport really delivered (false for the W-5 stub). */
  real_delivery: boolean
  /** The digest payload built this run (present whenever non-empty, even if send was skipped). */
  digest: DigestPayload | null
}

async function fetchRowsByIds(ids: string[], exec: LedgerExecutor): Promise<LedgerRow[]> {
  if (ids.length === 0) return []
  const { rows } = await exec<LedgerRow>(
    `SELECT ${READ_COLS} FROM ${LEDGER_TABLE} WHERE id = ANY($1::uuid[]) ORDER BY upper("window"), id`,
    [ids],
  )
  return rows
}

/**
 * Select the ids of `open` rows whose window has passed (window_end < asOf). window_end is the
 * exclusive upper bound of the daterange, matching migration 470's GIST-index intent
 * (`upper("window") < now()`) and the brief's "window_end < now()".
 */
async function selectCloseableIds(
  asOf: string,
  chartId: string | undefined,
  exec: LedgerExecutor,
): Promise<string[]> {
  const params: unknown[] = [asOf]
  let scope = ''
  if (chartId) {
    params.push(chartId)
    scope = ` AND chart_id = $${params.length}`
  }
  const { rows } = await exec<{ id: string }>(
    `SELECT id FROM ${LEDGER_TABLE}
      WHERE lifecycle_status = 'open'
        AND "window" IS NOT NULL
        AND upper("window") < $1::date${scope}
      ORDER BY upper("window"), id`,
    params,
  )
  return rows.map((r) => r.id)
}

/**
 * Select `open` rows that are closing soon: window not yet passed (upper >= asOf) AND within the
 * runway (upper <= asOf + closingSoonDays). Disjoint from the closeable set by construction, so
 * order relative to the transitions does not matter.
 */
async function selectClosingSoon(
  asOf: string,
  closingSoonDays: number,
  chartId: string | undefined,
  exec: LedgerExecutor,
): Promise<LedgerRow[]> {
  const params: unknown[] = [asOf, closingSoonDays]
  let scope = ''
  if (chartId) {
    params.push(chartId)
    scope = ` AND chart_id = $${params.length}`
  }
  const { rows } = await exec<LedgerRow>(
    `SELECT ${READ_COLS} FROM ${LEDGER_TABLE}
      WHERE lifecycle_status = 'open'
        AND "window" IS NOT NULL
        AND upper("window") >= $1::date
        AND upper("window") <= ($1::date + $2::int)${scope}
      ORDER BY upper("window"), id`,
    params,
  )
  return rows
}

/**
 * Run the one consolidated daily job. Deterministic given (asOf, DB state, journal state).
 */
export async function runDailyJob(opts: DailyJobOptions): Promise<DailyJobResult> {
  if (!AS_OF_RE.test(opts.asOf)) {
    throw new Error(`runDailyJob: asOf must be ISO yyyy-mm-dd, got "${opts.asOf}"`)
  }
  const asOf = opts.asOf
  const closingSoonDays = opts.closingSoonDays ?? 14
  if (!Number.isInteger(closingSoonDays) || closingSoonDays < 0) {
    throw new Error(`runDailyJob: closingSoonDays must be a non-negative integer, got ${closingSoonDays}`)
  }
  const exec = opts.exec ?? defaultExecutor
  const journal = opts.journal ?? new FileDigestJournal()
  const transport = opts.transport ?? new LogOnlyTransport()

  // ── (a) close windows via the legal-transition DAL (never raw UPDATE) ──
  const closeableIds = await selectCloseableIds(asOf, opts.chartId, exec)
  const closedRowIds: string[] = []
  for (const id of closeableIds) {
    // transitionLifecycle re-reads status + applies the optimistic guard: a row already moved
    // (e.g. a concurrent run) is skipped rather than double-transitioned.
    try {
      await transitionLifecycle(id, 'window_closed', {}, exec)
      closedRowIds.push(id)
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err)
      if (/changed concurrently/.test(msg)) continue // someone else closed it — fine, idempotent
      throw err
    }
  }

  // ── (b) detect closing-soon (derived; no state written) ──
  const closingSoonRows = await selectClosingSoon(asOf, closingSoonDays, opts.chartId, exec)

  // ── build the digest payload ──
  const closedRows = await fetchRowsByIds(closedRowIds, exec)
  const payload: DigestPayload = {
    as_of: asOf,
    closed: closedRows.map(toDigestItem),
    closing_soon: closingSoonRows.map(toDigestItem),
    closing_soon_days: closingSoonDays,
    generated_at: new Date().toISOString(),
  }

  const base: DailyJobResult = {
    as_of: asOf,
    closed_row_ids: closedRowIds,
    closing_soon_row_ids: closingSoonRows.map((r) => r.id),
    digest_dispatched: false,
    digest_skipped_reason: null,
    transport_mode: null,
    real_delivery: false,
    digest: null,
  }

  // ── (c) dispatch exactly one digest, only when non-empty and not already sent today ──
  if (digestIsEmpty(payload)) {
    return { ...base, digest_skipped_reason: 'empty' }
  }
  if (await journal.hasSent(asOf)) {
    // Idempotent skip: a digest was already dispatched for this asOf. Return the payload so the
    // caller can see WHAT would have been sent, but do not dispatch again.
    return { ...base, digest: payload, digest_skipped_reason: 'already_sent' }
  }

  const rendered = renderDigest(payload)
  const tr = await transport.send({ subject: rendered.subject, text: rendered.text, payload })

  if (tr.ok) {
    const record: DigestSentRecord = {
      as_of: asOf,
      sent_at: new Date().toISOString(),
      closed_count: payload.closed.length,
      closing_soon_count: payload.closing_soon.length,
      transport_mode: tr.mode,
      real_delivery: tr.realDelivery,
    }
    await journal.markSent(asOf, record)
  }

  return {
    ...base,
    digest: payload,
    digest_dispatched: tr.ok,
    transport_mode: tr.mode,
    real_delivery: tr.realDelivery,
  }
}
