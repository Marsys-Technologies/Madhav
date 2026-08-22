/**
 * SAMĪKṢĀ daily-job REAL-DB integration test — PB-3 lane L-4.
 *
 * Runs the consolidated daily job against a REAL Postgres with migration 470 applied, using the
 * REAL FileDigestJournal (a temp dir) — NOT an in-memory mock of the job agreeing with itself
 * (the PB-2 false-confidence-gate lesson, FOLLOWUP_PB-2_BYTE_EQUALITY_FIXTURE_COVERAGE.md).
 *
 * The honesty-standard test: it seeds real rows, runs the job TWICE against the SAME `--as-of`
 * date, and asserts the SECOND run performs ZERO additional transitions and dispatches ZERO
 * additional digests — proven by real DB state + a RecordingTransport's send count, not by
 * inspecting the code.
 *
 * N8-WIRING (P4-I remediation, DD-21): every test above injects `opts.journal` explicitly
 * (`FileDigestJournal`), so none of them ever exercises `runDailyJob`'s own DEFAULT
 * (`opts.journal ?? new DbDigestJournal(exec, opts.chartId)`) — the actual production wiring
 * this whole lane's thesis rests on. Proven by §N.8's own test: an independent refuter reverted
 * `DbDigestJournal` back to `FileDigestJournal` (undoing the lane's central claim) and the full
 * suite stayed green, because nothing called `runDailyJob` without a `journal` override. The
 * 'DEFAULT journal (no override)' test below is the one caller in this repo that omits
 * `journal` entirely — see its own header for the RED-under-revert / GREEN-after-revert proof.
 *
 * Gated on SAMIKSHA_TEST_DATABASE_URL; skipped where no DB is provided (same pattern as L-1's
 * ledger_db.integration.test.ts).
 */

import { describe, it, expect, beforeAll, afterAll, beforeEach } from 'vitest'
import { Pool } from 'pg'
import { promises as fs } from 'fs'
import os from 'os'
import path from 'path'
import { readFileSync } from 'fs'
import { resolve } from 'path'
import { runDailyJob } from '@/lib/pariprashna/samiksha/daily_job'
import { FileDigestJournal, DIGEST_JOURNAL_TABLE } from '@/lib/pariprashna/samiksha/digest_journal'
import { RecordingTransport, LogOnlyTransport } from '@/lib/pariprashna/samiksha/digest'
import { createLedgerRow, transitionLifecycle, type LedgerExecutor } from '@/lib/pariprashna/samiksha/writer'
import { listLedgerRowsForChart } from '@/lib/pariprashna/samiksha/reader'
import { LEDGER_TABLE, type LedgerStamp } from '@/lib/pariprashna/samiksha/schema'

const DB_URL = process.env.SAMIKSHA_TEST_DATABASE_URL
const run = DB_URL ? describe : describe.skip

// Migration 588 (the digest journal table `runDailyJob`'s DEFAULT journal writes to) has no
// dependency on any other pariprashna migration (see its own header) — applied standalone here,
// same pattern digest_journal_db.integration.test.ts already uses, so this file's DB does not
// have to assume 588 was already applied out-of-band. Idempotent (CREATE TABLE/INDEX IF NOT
// EXISTS) — safe to re-run against a DB where it is already applied.
const MIGRATION_588 = resolve(__dirname, '../../../supabase/migrations/588_samiksha_digest_journal.sql')

const STAMP: LedgerStamp = {
  build_id: 'bf2ea4ce-0000-0000-0000-000000000009',
  priors_version: 'priors_v7',
  formula_versions: { salience_formula_ver: null },
  ranking_config: { mode: 'composite_v1' },
  now_context_date: '2026-07-15',
}

/** Seed one row born `confirmed` (stamp copied) then advance it to `open`, returning its id. */
async function seedOpenRow(
  exec: LedgerExecutor,
  chartId: string,
  claim: string,
  window: { start: string; end: string } | null,
): Promise<string> {
  const row = await createLedgerRow(
    {
      chart_id: chartId,
      claim_text: claim,
      domain: 'career',
      window: window ?? undefined,
      confidence: { low: 0.5, high: 0.7 },
      direction: 'positive',
      initial_status: 'confirmed',
      stamp: STAMP,
    },
    exec,
  )
  await transitionLifecycle(row.id, 'open', {}, exec)
  return row.id
}

run('SAMĪKṢĀ consolidated daily job against a real migrated Postgres', () => {
  let pool: Pool
  let exec: LedgerExecutor
  let stateDir: string
  const CHART = '11111111-2222-3333-4444-5555555540a4' // isolated per-run scope
  const AS_OF = '2026-07-15'

  beforeAll(async () => {
    pool = new Pool({ connectionString: DB_URL })
    exec = <T,>(sql: string, params?: unknown[]) =>
      pool.query(sql, params as unknown[]).then((r) => ({ rows: r.rows as T[], rowCount: r.rowCount }))
    stateDir = await fs.mkdtemp(path.join(os.tmpdir(), 'samiksha-journal-'))
    // Apply migration 588 verbatim (idempotent) so the DEFAULT-journal test below has a real
    // pariprashna_samiksha_digest_journal table to write to, whether or not this test DB already
    // had 588 applied out-of-band.
    await pool.query(readFileSync(MIGRATION_588, 'utf-8'))
  })
  afterAll(async () => {
    if (pool) {
      await pool.query(`DELETE FROM ${LEDGER_TABLE} WHERE chart_id = $1`, [CHART])
      await pool.query(`DELETE FROM ${DIGEST_JOURNAL_TABLE} WHERE run_chart_id = $1::uuid`, [CHART])
      await pool.end()
    }
    if (stateDir) await fs.rm(stateDir, { recursive: true, force: true })
  })
  beforeEach(async () => {
    await pool.query(`DELETE FROM ${LEDGER_TABLE} WHERE chart_id = $1`, [CHART])
    await pool.query(`DELETE FROM ${DIGEST_JOURNAL_TABLE} WHERE run_chart_id = $1::uuid`, [CHART])
    // fresh journal dir per test so idempotency state does not leak across cases
    await fs.rm(stateDir, { recursive: true, force: true })
    await fs.mkdir(stateDir, { recursive: true })
  })

  it('run twice on the same --as-of: closes passed windows once, sends exactly one digest, idempotent', async () => {
    // A: window ended before AS_OF → should close.
    const idClose = await seedOpenRow(exec, CHART, 'A: leadership role by mid-2026', {
      start: '2026-01-01',
      end: '2026-06-01',
    })
    // B: window ends within 14d of AS_OF → closing_soon (still open, not closed).
    const idSoon = await seedOpenRow(exec, CHART, 'B: relocation window', {
      start: '2026-07-10',
      end: '2026-07-20',
    })
    // C: window far in the future → neither.
    const idFar = await seedOpenRow(exec, CHART, 'C: long-horizon claim', {
      start: '2026-07-01',
      end: '2027-06-01',
    })
    // D: no window → neither (excluded from both sweeps).
    const idNoWin = await seedOpenRow(exec, CHART, 'D: undated claim', null)

    const journal = new FileDigestJournal(stateDir)
    const transport = new RecordingTransport(new LogOnlyTransport({ info: () => {} }))

    // ── RUN 1 ──
    const r1 = await runDailyJob({ asOf: AS_OF, chartId: CHART, exec, journal, transport })
    expect(r1.closed_row_ids).toEqual([idClose]) // only A closed
    expect(r1.closing_soon_row_ids).toEqual([idSoon]) // only B closing soon
    expect(r1.closing_soon_row_ids).not.toContain(idFar)
    expect(r1.closing_soon_row_ids).not.toContain(idNoWin)
    expect(r1.digest_dispatched).toBe(true)
    expect(r1.real_delivery).toBe(false) // W-5 stub — never a real send
    expect(transport.sent).toHaveLength(1) // exactly one digest

    // DB truth after run 1
    const closedRows = await listLedgerRowsForChart(CHART, { status: 'window_closed' }, exec)
    expect(closedRows.map((r) => r.id)).toEqual([idClose])
    const openRows = await listLedgerRowsForChart(CHART, { status: 'open' }, exec)
    expect(new Set(openRows.map((r) => r.id))).toEqual(new Set([idSoon, idFar, idNoWin]))

    // ── RUN 2 (same as-of, same journal + transport) — must be a no-op ──
    const r2 = await runDailyJob({ asOf: AS_OF, chartId: CHART, exec, journal, transport })
    expect(r2.closed_row_ids).toEqual([]) // ZERO additional transitions
    expect(r2.digest_dispatched).toBe(false)
    expect(r2.digest_skipped_reason).toBe('already_sent') // idempotent skip
    expect(transport.sent).toHaveLength(1) // STILL one — no duplicate digest

    // DB unchanged: still exactly one window_closed row, same open set.
    const closedAfter = await listLedgerRowsForChart(CHART, { status: 'window_closed' }, exec)
    expect(closedAfter.map((r) => r.id)).toEqual([idClose])
  })

  it('sends NO digest when there is nothing to report (empty is not sent)', async () => {
    // Only a far-future open row → nothing closes, nothing closing soon.
    await seedOpenRow(exec, CHART, 'far-future only', { start: '2026-07-01', end: '2028-01-01' })
    const journal = new FileDigestJournal(stateDir)
    const transport = new RecordingTransport(new LogOnlyTransport({ info: () => {} }))

    const r = await runDailyJob({ asOf: AS_OF, chartId: CHART, exec, journal, transport })
    expect(r.closed_row_ids).toEqual([])
    expect(r.closing_soon_row_ids).toEqual([])
    expect(r.digest_dispatched).toBe(false)
    expect(r.digest_skipped_reason).toBe('empty')
    expect(transport.sent).toHaveLength(0) // no empty email
  })

  it('closes on a later --as-of even if an earlier run sent a digest for a different date', async () => {
    const idSoon = await seedOpenRow(exec, CHART, 'B: relocation window', {
      start: '2026-07-10',
      end: '2026-07-20',
    })
    const journal = new FileDigestJournal(stateDir)
    const transport = new RecordingTransport(new LogOnlyTransport({ info: () => {} }))

    // as-of 2026-07-15: B is closing_soon (upper 07-20 not yet passed) → digest sent, no close.
    const early = await runDailyJob({ asOf: '2026-07-15', chartId: CHART, exec, journal, transport })
    expect(early.closed_row_ids).toEqual([])
    expect(early.closing_soon_row_ids).toEqual([idSoon])
    expect(transport.sent).toHaveLength(1)

    // as-of 2026-07-25: B's window has passed (upper 07-20 < 07-25) → now it closes; new date → new digest.
    const later = await runDailyJob({ asOf: '2026-07-25', chartId: CHART, exec, journal, transport })
    expect(later.closed_row_ids).toEqual([idSoon])
    expect(later.digest_dispatched).toBe(true)
    expect(transport.sent).toHaveLength(2) // a distinct as-of gets its own single digest
  })

  // ── N8-WIRING (P4-I remediation) ──────────────────────────────────────────────────────────
  // Every test above passes `journal` explicitly. This is the ONE caller in the repo that omits
  // it, so it is the only test that can ever observe `runDailyJob`'s own default expression
  // (`opts.journal ?? new DbDigestJournal(exec, opts.chartId)`) actually running. Before this
  // test existed, an independent refuter reverted `DbDigestJournal` back to `FileDigestJournal`
  // in daily_job.ts — undoing this lane's entire thesis — and the full suite (134 tests) stayed
  // green, because nothing exercised the default. That is the §N.8 defect: a status
  // ("DbDigestJournal is now the production default") with no code path that could read false.
  //
  // RED-under-revert / GREEN-after-revert proof (verbatim command outputs) is carried in the
  // PR body / commit message for this test, not restated here — this comment documents WHY the
  // test is shaped this way; the test itself is the detector.
  it('DEFAULT journal (no journal option): runDailyJob writes a real row to pariprashna_samiksha_digest_journal', async () => {
    // A closing-soon row (window end within 14d of AS_OF, still `open`) rather than a closed
    // one: closing_soon is a DERIVED, non-persisted condition (daily_job.ts's own header), so it
    // is detected identically on every re-run — unlike a closed row, which stops appearing in
    // the payload after its one transition and would make the SECOND call's digest empty for an
    // unrelated reason (the 'empty' skip path), never reaching the journal gate this test exists
    // to exercise.
    await seedOpenRow(exec, CHART, 'E: default-journal proof claim', {
      start: '2026-07-10',
      end: '2026-07-20',
    })
    const transport = new RecordingTransport(new LogOnlyTransport({ info: () => {} }))

    // NOTE: no `journal` key at all. `exec` is still injected (points at this test's real
    // throwaway Postgres, never the shared dev/prod DB — RF-5) so the default DbDigestJournal
    // that runDailyJob constructs internally writes through THIS pool, not the shared one.
    const r = await runDailyJob({ asOf: AS_OF, chartId: CHART, exec, transport })
    expect(r.digest_dispatched).toBe(true)
    expect(transport.sent).toHaveLength(1)

    // The DD-21 proof: read back via a RAW query, independent of the object that wrote it.
    const { rows } = await pool.query(
      `SELECT as_of::text, run_chart_id, closing_soon_count, subject, body_text, payload
         FROM ${DIGEST_JOURNAL_TABLE}
        WHERE as_of = $1::date AND run_chart_id = $2::uuid`,
      [AS_OF, CHART],
    )
    expect(rows).toHaveLength(1)
    expect(rows[0].closing_soon_count).toBe(1)
    expect(rows[0].subject).toContain('closing soon')
    expect(rows[0].body_text.length).toBeGreaterThan(0)
    expect(rows[0].payload.closing_soon).toHaveLength(1)

    // Re-run with the same asOf, again with NO journal override: the same closing-soon row is
    // detected again (still `open`, derived condition), so the digest is non-empty again — this
    // time the default DbDigestJournal's own hasSent() must see its own prior write and skip,
    // proving the default is not just write-only but actually gates on itself.
    const r2 = await runDailyJob({ asOf: AS_OF, chartId: CHART, exec, transport })
    expect(r2.digest_dispatched).toBe(false)
    expect(r2.digest_skipped_reason).toBe('already_sent')
    expect(transport.sent).toHaveLength(1) // still one — no duplicate

    const { rows: afterRerun } = await pool.query(
      `SELECT count(*)::int AS n FROM ${DIGEST_JOURNAL_TABLE} WHERE as_of = $1::date AND run_chart_id = $2::uuid`,
      [AS_OF, CHART],
    )
    expect(afterRerun[0].n).toBe(1) // no duplicate row
  })
})
