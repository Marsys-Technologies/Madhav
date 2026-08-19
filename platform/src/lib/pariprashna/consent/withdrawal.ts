/**
 * Paripraśna consent — WITHDRAWAL → VERIFIED DELETION (§3.5.D, PPR-14).
 *
 * "Withdrawal triggers the §3.5.D verified-deletion workflow (L2+ corpus
 * destruction — compatible with §N.3 delete-then-insert; receipt snapshots
 * resolved by subject-scoped snapshot deletion with a tombstone hash so audit
 * integrity survives content deletion)."
 *
 * The sweep, per table, in one transaction:
 *   1. digest    — count + sha256 over the sorted per-row md5s (content never
 *                  enters the application; see `tombstoneDigestSql`)
 *   2. delete    — subject-scoped, `chart_id = $1`
 *   3. re-count  — the DETECTOR behind `verified_empty`. Without step 3,
 *                  "verified deletion" would be a status with no detector
 *                  behind it, which is the §N.8 defect class exactly.
 *   4. tombstone — the receipt, append-only by trigger.
 *
 * `verified_deletion_at` is stamped ONLY when every tombstone in the sweep
 * carries `verified_empty = TRUE`. A partial sweep leaves it NULL and reports
 * `status: 'partial'` — an honest incomplete, never a green-looking default.
 *
 * ── DISPUTE INTERLOCK (§3.5.D.2) ─────────────────────────────────────────────
 * If an open deletion-scope dispute exists for the chart, the sweep does NOT
 * run: the whole point of the dispute mechanism is that the scope is contested,
 * and destroying data while the argument about what to destroy is unresolved
 * would decide the dispute by fait accompli. Withdrawal is still RECORDED (the
 * consent state flips, the chain link lands) — only the destruction waits.
 */

import { assertSafeTableIdentifier, consentEntryHash, tombstoneDigestSql } from './hash_chain'
import { discoverSubjectScopedTables } from './scope'
import { isConsentEnforcementEnabled } from './flag'
import {
  ConsentFeatureDisabledError,
  type ConsentDb,
  type ConsentEventKind,
  type ConsentQueryable,
  type ConsentRow,
  type TombstoneRow,
} from './types'

export interface TombstoneSummary {
  table_name: string
  table_present: boolean
  row_count: number
  content_hash: string | null
  verified_empty: boolean
}

export interface WithdrawalResult {
  chart_id: string
  status: 'deleted' | 'partial' | 'blocked_by_dispute'
  withdrawal_event_seq: number
  tables_swept: number
  rows_deleted: number
  tombstones: TombstoneSummary[]
  verified_deletion_at: string | null
  /** Populated only for `blocked_by_dispute`. */
  blocking_dispute_ids: number[]
}

export interface WithdrawConsentArgs {
  chartId: string
  db: ConsentDb
  /** Who recorded the withdrawal (the subject, or the operator acting for them). */
  actorPrincipalId: string | null
  /** Free-text note stored on the chain link. Ids/enums only — never C1 content. */
  note?: string
}

/**
 * Record a withdrawal and run the verified-deletion sweep.
 * Throws `ConsentFeatureDisabledError` while the flag is OFF.
 */
export async function withdrawConsentAndDelete(
  args: WithdrawConsentArgs,
): Promise<WithdrawalResult> {
  if (!isConsentEnforcementEnabled()) throw new ConsentFeatureDisabledError('withdrawConsentAndDelete')
  const { chartId, db, actorPrincipalId, note } = args

  return db.withTransaction(async (tx) => {
    const { rows: consentRows } = await tx.query<ConsentRow>(
      `SELECT * FROM chart_subject_consent WHERE chart_id = $1 FOR UPDATE`,
      [chartId],
    )
    const consent = consentRows[0]
    if (!consent) {
      throw new Error(`NO_CONSENT_ROW: cannot withdraw consent that was never recorded (${chartId})`)
    }

    // 1. Record the withdrawal itself — always, even if the sweep is blocked.
    const withdrawalSeq = await appendConsentEvent(tx, {
      chartId,
      eventKind: 'withdrawn',
      actorPrincipalId,
      payload: { note: note ?? null, previous_state: consent.consent_state },
    })
    if (consent.consent_state !== 'withdrawn') {
      await tx.query(
        `UPDATE chart_subject_consent
            SET consent_state = 'withdrawn', withdrawn_at = now(), updated_at = now()
          WHERE chart_id = $1`,
        [chartId],
      )
    }

    // 2. Dispute interlock.
    const { rows: disputes } = await tx.query<{ dispute_id: number }>(
      `SELECT dispute_id FROM chart_subject_deletion_disputes
        WHERE chart_id = $1 AND status IN ('open', 'reopened', 'escalated')`,
      [chartId],
    )
    if (disputes.length > 0) {
      return {
        chart_id: chartId,
        status: 'blocked_by_dispute' as const,
        withdrawal_event_seq: withdrawalSeq,
        tables_swept: 0,
        rows_deleted: 0,
        tombstones: [],
        verified_deletion_at: null,
        // BIGSERIAL comes back from `pg` as a string; the declared type says
        // number, so coerce rather than let the two quietly disagree.
        blocking_dispute_ids: disputes.map((d) => Number(d.dispute_id)),
      }
    }

    // 3. The sweep.
    const tables = await discoverSubjectScopedTables(tx)
    const tombstones: TombstoneSummary[] = []
    let rowsDeleted = 0

    for (const table of tables) {
      assertSafeTableIdentifier(table)

      const { rows: digestRows } = await tx.query<{ row_count: number; content_hash: string }>(
        tombstoneDigestSql(table),
        [chartId],
      )
      const rowCount = Number(digestRows[0]?.row_count ?? 0)
      const contentHash = digestRows[0]?.content_hash ?? null

      await tx.query(`DELETE FROM "${table}" WHERE chart_id::text = $1`, [chartId])

      // The detector: re-count AFTER the delete. `verified_empty` means this
      // query returned zero — nothing else.
      const { rows: afterRows } = await tx.query<{ remaining: number }>(
        `SELECT count(*)::int AS remaining FROM "${table}" WHERE chart_id::text = $1`,
        [chartId],
      )
      const verifiedEmpty = Number(afterRows[0]?.remaining ?? -1) === 0

      await tx.query(
        `INSERT INTO chart_subject_deletion_tombstones
           (chart_id, withdrawal_event_seq, table_name, table_present, row_count,
            content_hash, verified_empty)
         VALUES ($1, $2, $3, TRUE, $4, $5, $6)
         ON CONFLICT (chart_id, withdrawal_event_seq, table_name) DO UPDATE
           SET row_count = EXCLUDED.row_count,
               content_hash = EXCLUDED.content_hash,
               verified_empty = EXCLUDED.verified_empty`,
        [chartId, withdrawalSeq, table, rowCount, contentHash, verifiedEmpty],
      )

      rowsDeleted += rowCount
      tombstones.push({
        table_name: table,
        table_present: true,
        row_count: rowCount,
        content_hash: contentHash,
        verified_empty: verifiedEmpty,
      })
    }

    const allVerified = tombstones.length > 0 && tombstones.every((t) => t.verified_empty)
    // A sweep that found no in-scope tables at all is `partial`, not `deleted`:
    // "nothing to delete" and "everything deleted and re-counted to zero" are
    // different claims, and only the second earns `verified_deletion_at`.
    let verifiedAt: string | null = null
    if (allVerified) {
      const { rows } = await tx.query<{ verified_deletion_at: string }>(
        `UPDATE chart_subject_consent
            SET verified_deletion_at = now(), updated_at = now()
          WHERE chart_id = $1
          RETURNING verified_deletion_at::text AS verified_deletion_at`,
        [chartId],
      )
      verifiedAt = rows[0]?.verified_deletion_at ?? null
      await appendConsentEvent(tx, {
        chartId,
        eventKind: 'deletion_verified',
        actorPrincipalId,
        payload: {
          withdrawal_event_seq: withdrawalSeq,
          tables_swept: tombstones.length,
          rows_deleted: rowsDeleted,
        },
      })
    }

    return {
      chart_id: chartId,
      status: allVerified ? ('deleted' as const) : ('partial' as const),
      withdrawal_event_seq: withdrawalSeq,
      tables_swept: tombstones.length,
      rows_deleted: rowsDeleted,
      tombstones,
      verified_deletion_at: verifiedAt,
      blocking_dispute_ids: [],
    }
  })
}

// ── Chain append ─────────────────────────────────────────────────────────────

export interface AppendConsentEventArgs {
  chartId: string
  eventKind: ConsentEventKind
  actorPrincipalId: string | null
  payload?: Record<string, unknown>
}

/**
 * Append one hash-chained link. MUST be called inside a transaction that already
 * holds a lock on the chart's consent row (or otherwise serializes writers) —
 * `seq` is derived from the current max, so two concurrent appenders without
 * that lock would race. The `(chart_id, seq)` unique constraint turns that race
 * into a loud failure rather than a forked chain, but the lock is the design.
 */
export async function appendConsentEvent(
  tx: ConsentQueryable,
  args: AppendConsentEventArgs,
): Promise<number> {
  const { chartId, eventKind, actorPrincipalId, payload = {} } = args

  const { rows: tipRows } = await tx.query<{ seq: number; entry_hash: string }>(
    `SELECT seq, entry_hash FROM chart_subject_consent_events
      WHERE chart_id = $1 ORDER BY seq DESC LIMIT 1`,
    [chartId],
  )
  const tip = tipRows[0] ?? null
  const seq = (tip?.seq ?? 0) + 1
  const prevHash = tip?.entry_hash ?? null

  // `recorded_at` is generated here rather than by `now()` so that the hashed
  // value and the stored value are the same string. A hash over a timestamp the
  // application never saw could not be re-derived, and a chain nobody can
  // re-derive is not a chain.
  const recordedAt = new Date().toISOString()

  const entryHash = consentEntryHash({
    chart_id: chartId,
    seq,
    event_kind: eventKind,
    actor_principal_id: actorPrincipalId,
    payload,
    recorded_at: recordedAt,
    prev_hash: prevHash,
  })

  await tx.query(
    `INSERT INTO chart_subject_consent_events
       (chart_id, seq, event_kind, actor_principal_id, payload, recorded_at, prev_hash, entry_hash)
     VALUES ($1, $2, $3, $4, $5::jsonb, $6::timestamptz, $7, $8)`,
    [chartId, seq, eventKind, actorPrincipalId, JSON.stringify(payload), recordedAt, prevHash, entryHash],
  )
  return seq
}

/** Load a chart's consent chain in order, for `verifyConsentChain`. */
export async function loadConsentChain(db: ConsentQueryable, chartId: string) {
  const { rows } = await db.query<{
    chart_id: string
    seq: number
    event_kind: ConsentEventKind
    actor_principal_id: string | null
    payload: Record<string, unknown>
    recorded_at: string
    prev_hash: string | null
    entry_hash: string
  }>(
    `SELECT chart_id, seq, event_kind, actor_principal_id, payload,
            to_char(recorded_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"') AS recorded_at,
            prev_hash, entry_hash
       FROM chart_subject_consent_events
      WHERE chart_id = $1
      ORDER BY seq`,
    [chartId],
  )
  return rows
}

/** Every tombstone for one chart, newest sweep first. */
export async function loadTombstones(
  db: ConsentQueryable,
  chartId: string,
): Promise<TombstoneRow[]> {
  const { rows } = await db.query<TombstoneRow>(
    `SELECT * FROM chart_subject_deletion_tombstones
      WHERE chart_id = $1
      ORDER BY withdrawal_event_seq DESC, table_name`,
    [chartId],
  )
  return rows
}
