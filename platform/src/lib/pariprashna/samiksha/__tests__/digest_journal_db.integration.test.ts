/**
 * SAMĪKṢĀ digest journal — REAL-DB integration test — P4-I (DD-21).
 *
 * Runs `DbDigestJournal` against a REAL Postgres with migration 588
 * (`588_samiksha_digest_journal.sql`) actually applied — NOT an in-memory mock of the journal
 * agreeing with itself (the PB-2 false-confidence-gate lesson `ledger_db.integration.test.ts`
 * already documents for this codebase).
 *
 * THE DD-21 PROOF this test exists to carry: before any write, a read for the test's `as_of`
 * returns zero rows (the honest "log-only, nothing durable" baseline). After `markSent`, the
 * SAME read returns exactly one row carrying the real rendered subject/body + structured
 * payload — read back from the database, not asserted against the in-process object that wrote
 * it. It also proves the UPSERT-on-`as_of` idempotency contract and the unique-constraint-backed
 * `hasSent` transition false → true.
 *
 * Gated on SAMIKSHA_TEST_DATABASE_URL; skipped where no DB is provided (same pattern as
 * ledger_db.integration.test.ts and samiksha_daily_job.integration.test.ts). This migration has
 * no dependency on any other pariprashna migration (see 588's own header), so it is applied
 * standalone here rather than requiring the full migration chain.
 */

import { describe, it, expect, beforeAll, afterAll, beforeEach } from 'vitest'
import { Pool } from 'pg'
import { readFileSync } from 'fs'
import { resolve } from 'path'
import {
  DbDigestJournal,
  DIGEST_JOURNAL_TABLE,
  type DigestSentRecord,
} from '../digest_journal'
import type { DigestPayload } from '../digest'
import type { LedgerExecutor } from '../writer'

const DB_URL = process.env.SAMIKSHA_TEST_DATABASE_URL
const run = DB_URL ? describe : describe.skip

const MIGRATION_588 = resolve(
  __dirname,
  '../../../../../supabase/migrations/588_samiksha_digest_journal.sql',
)

// Synthetic chart only — never the native's real chart (482012f1-…).
const SYNTHETIC_CHART = '1c826d5a-41cb-4450-b4dc-59d440e5f75a'

function payload(asOf: string): DigestPayload {
  return {
    as_of: asOf,
    closed: [
      {
        id: '11111111-1111-1111-1111-111111111111',
        chart_id: SYNTHETIC_CHART,
        claim_text: 'DD-21 proof: a synthetic closed-window claim.',
        domain: 'career',
        window: '[2026-01-01,2026-08-01)',
        confidence: '[0.55,0.7)',
        direction: 'positive',
        window_end: '2026-08-01',
      },
    ],
    closing_soon: [],
    closing_soon_days: 14,
    generated_at: `${asOf}T03:00:00.000Z`,
  }
}

function record(asOf: string): DigestSentRecord {
  const p = payload(asOf)
  return {
    as_of: asOf,
    sent_at: `${asOf}T03:00:01.000Z`,
    closed_count: p.closed.length,
    closing_soon_count: p.closing_soon.length,
    transport_mode: 'log-only-stub',
    real_delivery: false,
    subject: `[Samīkṣā] ${p.closed.length} window(s) closed, ${p.closing_soon.length} closing soon — as of ${asOf}`,
    body_text: `SAMĪKṢĀ prediction digest — as of ${asOf}\n(DD-21 real-DB integration test content)`,
    payload: p,
  }
}

run('DbDigestJournal against a real migrated Postgres (migration 588)', () => {
  let pool: Pool
  let exec: LedgerExecutor
  const AS_OF = '2026-08-23'

  beforeAll(async () => {
    pool = new Pool({ connectionString: DB_URL })
    exec = <T,>(sql: string, params?: unknown[]) =>
      pool.query(sql, params as unknown[]).then((r) => ({ rows: r.rows as T[], rowCount: r.rowCount }))
    // Apply migration 588 verbatim — proves the file itself applies cleanly, not a hand-copied
    // paraphrase of its DDL (§N.4: verify the migration actually applied).
    const sql = readFileSync(MIGRATION_588, 'utf-8')
    await pool.query(sql)
  })
  afterAll(async () => {
    if (pool) {
      await pool.query(`DELETE FROM ${DIGEST_JOURNAL_TABLE} WHERE as_of = $1::date`, [AS_OF])
      await pool.end()
    }
  })
  beforeEach(async () => {
    await pool.query(`DELETE FROM ${DIGEST_JOURNAL_TABLE} WHERE as_of = $1::date`, [AS_OF])
  })

  it('BEFORE: a query for a fresh as_of returns zero rows — the honest log-only baseline', async () => {
    const { rows } = await pool.query(`SELECT * FROM ${DIGEST_JOURNAL_TABLE} WHERE as_of = $1::date`, [AS_OF])
    expect(rows).toHaveLength(0)
    const j = new DbDigestJournal(exec)
    expect(await j.hasSent(AS_OF)).toBe(false)
  })

  it('AFTER: markSent writes a real row; hasSent flips true; readByAsOf reads back the real content', async () => {
    const j = new DbDigestJournal(exec, SYNTHETIC_CHART)
    const rec = record(AS_OF)

    await j.markSent(AS_OF, rec)

    // Read back via a RAW query (not the journal's own reader) — the row genuinely exists in
    // the table, independent of the object that wrote it.
    const raw = await pool.query(
      `SELECT as_of::text, run_chart_id, closed_count, closing_soon_count, transport_mode,
              real_delivery, subject, body_text, payload
         FROM ${DIGEST_JOURNAL_TABLE} WHERE as_of = $1::date`,
      [AS_OF],
    )
    expect(raw.rows).toHaveLength(1)
    expect(raw.rows[0].as_of).toBe(AS_OF)
    expect(raw.rows[0].run_chart_id).toBe(SYNTHETIC_CHART)
    expect(raw.rows[0].closed_count).toBe(1)
    expect(raw.rows[0].subject).toBe(rec.subject)
    expect(raw.rows[0].body_text).toBe(rec.body_text)
    expect(raw.rows[0].payload).toEqual(rec.payload) // joinable content, not just a marker

    // Read back via the journal's own typed reader too.
    const viaJournal = await j.readByAsOf(AS_OF)
    expect(viaJournal?.subject).toBe(rec.subject)
    expect(viaJournal?.payload).toEqual(rec.payload)

    expect(await j.hasSent(AS_OF)).toBe(true) // flips false → true, DB-verified
  })

  it('markSent is idempotent (UPSERT on as_of): a second call overwrites, never duplicates', async () => {
    const j = new DbDigestJournal(exec)
    await j.markSent(AS_OF, record(AS_OF))
    const updated = record(AS_OF)
    updated.closed_count = 2
    updated.subject = 'updated subject line'
    await j.markSent(AS_OF, updated)

    const { rows } = await pool.query(`SELECT closed_count, subject FROM ${DIGEST_JOURNAL_TABLE} WHERE as_of = $1::date`, [AS_OF])
    expect(rows).toHaveLength(1) // still exactly one row for this as_of — no duplicate
    expect(rows[0].closed_count).toBe(2)
    expect(rows[0].subject).toBe('updated subject line')
  })

  it('the unique (as_of, run_chart_id) constraint is real, NULLS NOT DISTINCT: a raw duplicate all-charts INSERT (bypassing the UPSERT) is rejected', async () => {
    const j = new DbDigestJournal(exec) // chartId undefined → run_chart_id NULL (all-charts row)
    await j.markSent(AS_OF, record(AS_OF))
    // §N.8 detector: this proves the constraint the whole idempotency story leans on actually
    // exists in the schema, not just in application-code discipline — AND that NULLS NOT
    // DISTINCT really does treat two NULL run_chart_id rows as colliding (Postgres's default
    // NULL semantics would NOT reject this without the explicit NULLS NOT DISTINCT clause).
    await expect(
      pool.query(
        `INSERT INTO ${DIGEST_JOURNAL_TABLE}
           (as_of, sent_at, closed_count, closing_soon_count, transport_mode, real_delivery,
            subject, body_text, payload)
         VALUES ($1::date, now(), 0, 0, 'log-only-stub', false, 'dup', 'dup', '{}'::jsonb)`,
        [AS_OF],
      ),
    ).rejects.toThrow(/duplicate key|unique constraint/i)
  })

  it('two DIFFERENT charts scoped to the SAME as_of do NOT collide — the live bug this migration/class fix closes', async () => {
    // This is the exact scenario an independent refuter reproduced live against the pre-fix
    // schema (UNIQUE (as_of) alone, hasSent() not scoped by run_chart_id): chart A's digest
    // silently shadowed chart B's — B's window closed, B's digest was suppressed, nothing
    // recorded it, exit code 0. Both migration 588's key and DbDigestJournal.hasSent/markSent/
    // readByAsOf's chart-scoping were fixed together before either went live.
    const CHART_A = '1c826d5a-41cb-4450-b4dc-59d440e5f75a' // synthetic chart (RF-5)
    const CHART_B = '2c826d5a-41cb-4450-b4dc-59d440e5f75a' // distinct synthetic id, same as_of
    await pool.query(`DELETE FROM ${DIGEST_JOURNAL_TABLE} WHERE as_of = $1::date`, [AS_OF])

    const jA = new DbDigestJournal(exec, CHART_A)
    const jB = new DbDigestJournal(exec, CHART_B)

    expect(await jA.hasSent(AS_OF)).toBe(false)
    expect(await jB.hasSent(AS_OF)).toBe(false)

    const recA = record(AS_OF)
    recA.subject = 'chart A digest'
    await jA.markSent(AS_OF, recA)

    // The defect this closes: pre-fix, jB.hasSent(AS_OF) would now read TRUE off chart A's row.
    expect(await jA.hasSent(AS_OF)).toBe(true)
    expect(await jB.hasSent(AS_OF)).toBe(false) // chart B's own send is still owed

    const recB = record(AS_OF)
    recB.subject = 'chart B digest'
    await jB.markSent(AS_OF, recB)

    expect(await jB.hasSent(AS_OF)).toBe(true)

    // Both rows genuinely exist, independently, in the DB — not one shadowing the other.
    const { rows } = await pool.query(
      `SELECT run_chart_id, subject FROM ${DIGEST_JOURNAL_TABLE} WHERE as_of = $1::date ORDER BY subject`,
      [AS_OF],
    )
    expect(rows).toHaveLength(2)
    expect(rows.map((r) => r.subject)).toEqual(['chart A digest', 'chart B digest'])

    expect((await jA.readByAsOf(AS_OF))?.subject).toBe('chart A digest')
    expect((await jB.readByAsOf(AS_OF))?.subject).toBe('chart B digest')

    await pool.query(`DELETE FROM ${DIGEST_JOURNAL_TABLE} WHERE as_of = $1::date`, [AS_OF])
  })
})
