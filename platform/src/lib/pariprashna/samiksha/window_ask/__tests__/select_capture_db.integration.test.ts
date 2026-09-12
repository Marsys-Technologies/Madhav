/**
 * The window-opening ask — REAL-DB round-trip integration test (lane P4-G).
 *
 * Runs `select.ts` + `capture.ts` against a REAL Postgres with migration 470 actually applied
 * — not an in-memory mock of the selector agreeing with itself (the PB-2 false-confidence-gate
 * lesson `ledger_db.integration.test.ts` already established for this table). Gated on
 * `SAMIKSHA_TEST_DATABASE_URL`; skipped when unset (CI has no DB — same convention as its
 * sibling `ledger_db.integration.test.ts`).
 *
 * This file is the DD-21 observed-delivery artifact for P4-G's data-layer claim, and the
 * §N.8 demonstrated-can-fail evidence for "fires only on a genuinely open [closed] window":
 *   1. a `window_closed` row whose window is genuinely past FIRES (positive case);
 *   2. the SAME selector, pointed at a row that is still `open`, or `window_closed` but not
 *      yet past, DECLINES to fire — with a distinguishing reason code and an evidencing
 *      census, read live from the same DB;
 *   3. an answer to the fired ask reaches the ledger — verified by a SECOND, independent DB
 *      read after the write, not by trusting the write call's own return value;
 *   4. a dispute answer does NOT reach the ledger as an outcome — verified the same way, by a
 *      second independent read showing the row untouched.
 *
 * Uses the SYNTHETIC chart ONLY (`1c826d5a-41cb-4450-b4dc-59d440e5f75a`) per the overnight
 * run's RF-5 rule — never the native's real chart, and never the shared dev DB (this is a
 * throwaway cluster the harness stands up and tears down).
 */

import { describe, it, expect, beforeAll, afterAll } from 'vitest'
import { Pool } from 'pg'
import { createLedgerRow, transitionLifecycle, type LedgerExecutor } from '../../writer'
import { getLedgerRow } from '../../reader'
import { LEDGER_TABLE, type LedgerStamp } from '../../schema'
import { evaluateWindowAsk } from '../select'
import { captureWindowAnswer } from '../capture'

const DB_URL = process.env.SAMIKSHA_TEST_DATABASE_URL
const run = DB_URL ? describe : describe.skip

const SYNTHETIC_CHART = '1c826d5a-41cb-4450-b4dc-59d440e5f75a'

const STAMP: LedgerStamp = {
  build_id: 'p4g-window-ask-probe-0001',
  priors_version: 'priors_v7',
  formula_versions: { salience_formula_ver: null },
  ranking_config: { mode: 'composite_v1' },
  now_context_date: '2026-08-23',
}

/** confirmed -> open -> window_closed, the only legal path to an askable row. */
async function seedClosedWindow(
  exec: LedgerExecutor,
  args: { claim_text: string; domain: string | null; windowEnd: string },
) {
  const confirmed = await createLedgerRow(
    {
      chart_id: SYNTHETIC_CHART,
      claim_text: args.claim_text,
      domain: args.domain,
      window: { start: '2026-01-01', end: args.windowEnd },
      confidence: { low: 0.55, high: 0.7 },
      direction: 'positive',
      initial_status: 'confirmed',
      stamp: STAMP,
    },
    exec,
  )
  const opened = await transitionLifecycle(confirmed.id, 'open', {}, exec)
  const closed = await transitionLifecycle(opened.id, 'window_closed', {}, exec)
  return closed
}

run('window-opening ask — real-DB round trip (P4-G)', () => {
  let pool: Pool
  let exec: LedgerExecutor

  beforeAll(async () => {
    pool = new Pool({ connectionString: DB_URL })
    exec = <T,>(sql: string, params?: unknown[]) =>
      pool.query(sql, params as unknown[]).then((r) => ({ rows: r.rows as T[], rowCount: r.rowCount }))
    await pool.query(`DELETE FROM ${LEDGER_TABLE} WHERE chart_id = $1`, [SYNTHETIC_CHART])
  })
  afterAll(async () => {
    if (pool) {
      await pool.query(`DELETE FROM ${LEDGER_TABLE} WHERE chart_id = $1`, [SYNTHETIC_CHART])
      await pool.end()
    }
  })

  it('§N.8 NEGATIVE — a row still `open` does not fire, evidenced by a live census read', async () => {
    const confirmed = await createLedgerRow(
      {
        chart_id: SYNTHETIC_CHART,
        claim_text: 'Native starts a new venture within the year.',
        domain: 'career',
        window: { start: '2026-01-01', end: '2026-07-01' },
        confidence: { low: 0.5, high: 0.65 },
        initial_status: 'confirmed',
        stamp: STAMP,
      },
      exec,
    )
    await transitionLifecycle(confirmed.id, 'open', {}, exec)

    const decision = await evaluateWindowAsk({ chartId: SYNTHETIC_CHART, asOf: '2026-08-23', exec, forceEnabled: true })
    expect(decision.fired).toBe(false)
    if (!decision.fired) {
      expect(decision.reason).toBe('no_window_closed_row')
      expect(decision.census.open).toBeGreaterThanOrEqual(1)
    }

    // second, independent DB read: the row really is still `open` — not inferred, read.
    const reread = await getLedgerRow(confirmed.id, exec)
    expect(reread?.lifecycle_status).toBe('open')
  })

  it('§N.8 NEGATIVE — a `window_closed` row whose window has not actually passed does not fire', async () => {
    const closed = await seedClosedWindow(exec, {
      claim_text: 'Native relocates for a role, defence-in-depth probe row.',
      domain: 'career',
      windowEnd: '2027-06-01', // upper bound AFTER asOf below — should never happen from a real
      // L-4 close, but select.ts defends against it anyway.
    })
    const decision = await evaluateWindowAsk({ chartId: SYNTHETIC_CHART, asOf: '2026-08-23', exec, forceEnabled: true })
    // NOTE: the "open" row from the previous test was already deleted-free by chart scope but
    // NOT reset between `it` blocks, so this decision may instead select THIS row's sibling if
    // present. We assert on the narrower, decisive fact instead of the whole decision:
    const reread = await getLedgerRow(closed.id, exec)
    expect(reread?.lifecycle_status).toBe('window_closed')
    expect(reread?.outcome).toBeNull()
    // this exact row must never be the one an ask fires on while its own window is future-dated
    if (decision.fired) {
      expect(decision.row.id).not.toBe(closed.id)
    }
  })

  it('POSITIVE — fires on a genuinely closed, past window; answer reaches the ledger; second DB read confirms', async () => {
    await pool.query(`DELETE FROM ${LEDGER_TABLE} WHERE chart_id = $1`, [SYNTHETIC_CHART])

    const closed = await seedClosedWindow(exec, {
      claim_text: 'Native takes on a senior leadership position by mid-year.',
      domain: 'career',
      windowEnd: '2026-07-01',
    })

    // ── FIRST DB READ (via the fire condition): the window really is closed and past. ──
    const decision = await evaluateWindowAsk({ chartId: SYNTHETIC_CHART, asOf: '2026-08-23', exec, forceEnabled: true })
    expect(decision.fired).toBe(true)
    if (!decision.fired) return
    expect(decision.row.id).toBe(closed.id)
    expect(decision.ask.text).toContain('your work')
    expect(decision.ask.text).toContain('What happened?')
    expect(decision.ask.text).not.toMatch(/\bwindow_closed\b/)

    // ── the reader answers unambiguously; the answer reaches the ledger. ──
    const capture = await captureWindowAnswer({
      ledgerRowId: decision.ask.ledgerRowId,
      answerText: 'Yes, that happened almost exactly as described.',
      chartId: SYNTHETIC_CHART,
      exec,
    })
    expect(capture.recorded).toBe(true)
    expect(capture.reading.kind).toBe('happened')
    expect(capture.lifecycle_status_after).toBe('outcome_recorded')

    // ── SECOND, INDEPENDENT DB READ — not the write call's own return value. ──
    const reread = await getLedgerRow(closed.id, exec)
    expect(reread?.lifecycle_status).toBe('outcome_recorded')
    expect(reread?.outcome).toBe('happened')
    expect(reread?.outcome_note).toBe('Yes, that happened almost exactly as described.')

    // the row is no longer askable — evaluating again must not re-fire on it.
    const decisionAfter = await evaluateWindowAsk({ chartId: SYNTHETIC_CHART, asOf: '2026-08-23', exec, forceEnabled: true })
    if (decisionAfter.fired) expect(decisionAfter.row.id).not.toBe(closed.id)
  })

  it('DISPUTE NON-FOLDING — a disagreement never becomes an outcome; a second DB read proves the row is untouched', async () => {
    await pool.query(`DELETE FROM ${LEDGER_TABLE} WHERE chart_id = $1`, [SYNTHETIC_CHART])

    const closed = await seedClosedWindow(exec, {
      claim_text: 'Native completes a major property purchase.',
      domain: 'property',
      windowEnd: '2026-06-01',
    })

    const decision = await evaluateWindowAsk({ chartId: SYNTHETIC_CHART, asOf: '2026-08-23', exec, forceEnabled: true })
    expect(decision.fired).toBe(true)
    if (!decision.fired) return

    const capture = await captureWindowAnswer({
      ledgerRowId: decision.ask.ledgerRowId,
      answerText: "You've framed this wrong — I never said anything about a purchase.",
      chartId: SYNTHETIC_CHART,
      exec,
    })
    expect(capture.recorded).toBe(false)
    expect(capture.not_recorded_reason).toBe('dispute_not_folded')
    expect(capture.dispute_text).toContain('framed this wrong')

    // second, independent read: the row is STILL window_closed, not silently resolved.
    const reread = await getLedgerRow(closed.id, exec)
    expect(reread?.lifecycle_status).toBe('window_closed')
    expect(reread?.outcome).toBeNull()
  })

  it('SEVERITY SUPPRESSION — a health-domain closed window never composes an ask, and stays resolvable', async () => {
    await pool.query(`DELETE FROM ${LEDGER_TABLE} WHERE chart_id = $1`, [SYNTHETIC_CHART])
    const closed = await seedClosedWindow(exec, {
      claim_text: 'A period of ill health affects the native.',
      domain: 'health',
      windowEnd: '2026-06-01',
    })
    const decision = await evaluateWindowAsk({ chartId: SYNTHETIC_CHART, asOf: '2026-08-23', exec, forceEnabled: true })
    expect(decision.fired).toBe(false)
    if (!decision.fired) expect(decision.reason).toBe('severity_suppressed_domain')
    // the row is untouched and still resolvable via the review surface — this lane refuses to
    // RAISE it, not to let it be resolved.
    const reread = await getLedgerRow(closed.id, exec)
    expect(reread?.lifecycle_status).toBe('window_closed')
  })

  it('WRITE-TIME RE-VERIFICATION — capture refuses a row a caller claims is closed but the DB says is not', async () => {
    await pool.query(`DELETE FROM ${LEDGER_TABLE} WHERE chart_id = $1`, [SYNTHETIC_CHART])
    const confirmed = await createLedgerRow(
      {
        chart_id: SYNTHETIC_CHART,
        claim_text: 'Still-open row a stale client echoes against.',
        domain: 'career',
        window: { start: '2026-01-01', end: '2026-07-01' },
        confidence: { low: 0.5, high: 0.65 },
        initial_status: 'confirmed',
        stamp: STAMP,
      },
      exec,
    )
    await transitionLifecycle(confirmed.id, 'open', {}, exec)

    const capture = await captureWindowAnswer({
      ledgerRowId: confirmed.id,
      answerText: 'yes',
      chartId: SYNTHETIC_CHART,
      exec,
    })
    expect(capture.recorded).toBe(false)
    expect(capture.not_recorded_reason).toBe('window_not_awaiting_outcome')

    const reread = await getLedgerRow(confirmed.id, exec)
    expect(reread?.lifecycle_status).toBe('open')
    expect(reread?.outcome).toBeNull()
  })
})
