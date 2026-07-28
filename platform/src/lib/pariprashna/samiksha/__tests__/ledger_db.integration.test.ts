/**
 * SAMĪKṢĀ ledger DAL — REAL-DB integration test — PB-3 lane L-1.
 *
 * Runs the writer/reader DAL against a REAL Postgres with migration 470 actually applied (NOT
 * an in-memory mock of the writer agreeing with itself — the PB-2 false-confidence-gate
 * lesson). Gated on SAMIKSHA_TEST_DATABASE_URL; skipped in CI (no DB). Run locally via the
 * lane's throwaway-DB harness, which applies the migration then points this env var at it.
 *
 * Proves the two DAL acceptance criteria with evidence that CAN fail:
 *   - Illegal transitions are rejected (detected→outcome_recorded throws; row unchanged in DB).
 *   - Stamp-immutability is green: the DB trigger blocks UPDATE of a stamp/settled-claim field
 *     on a confirmed row, WHILE still allowing the legal lifecycle + outcome updates (so the
 *     trigger isn't just blanket-blocking everything — that distinction is what makes it real).
 */

import { describe, it, expect, beforeAll, afterAll } from 'vitest'
import { Pool } from 'pg'
import {
  createLedgerRow,
  confirmDetectedRow,
  transitionLifecycle,
  recordOutcome,
  countLedgerRows,
  type LedgerExecutor,
} from '../writer'
import { getLedgerRow } from '../reader'
import { IllegalTransitionError } from '../transitions'
import { LEDGER_TABLE, type LedgerStamp } from '../schema'

const DB_URL = process.env.SAMIKSHA_TEST_DATABASE_URL
const run = DB_URL ? describe : describe.skip

const STAMP: LedgerStamp = {
  build_id: 'bf2ea4ce-0000-0000-0000-000000000001',
  priors_version: 'priors_v7',
  formula_versions: { salience_formula_ver: null },
  ranking_config: { mode: 'composite_v1' },
  now_context_date: '2026-07-28',
}

run('SAMĪKṢĀ ledger DAL against a real migrated Postgres', () => {
  let pool: Pool
  let exec: LedgerExecutor
  const CHART = '482012f1-710e-4a25-994a-93821f5871aa' // canonical chart
  const testChart = '11111111-2222-3333-4444-555555550001' // isolated per-run scope

  beforeAll(async () => {
    pool = new Pool({ connectionString: DB_URL })
    exec = <T,>(sql: string, params?: unknown[]) =>
      pool.query(sql, params as unknown[]).then((r) => ({ rows: r.rows as T[], rowCount: r.rowCount }))
    await pool.query(`DELETE FROM ${LEDGER_TABLE} WHERE chart_id = $1`, [testChart])
  })
  afterAll(async () => {
    if (pool) {
      await pool.query(`DELETE FROM ${LEDGER_TABLE} WHERE chart_id = $1`, [testChart])
      await pool.end()
    }
  })

  it('inserts a confirmed row with the D-16 stamp COPIED into columns', async () => {
    const row = await createLedgerRow(
      {
        chart_id: CHART,
        claim_text: 'Native transitions to a leadership role by end of 2026.',
        domain: 'career',
        window: { start: '2026-07-01', end: '2027-01-01' },
        confidence: { low: 0.55, high: 0.7 },
        direction: 'positive',
        technique_refs: ['vimshottari_dasha', 'transit_saturn'],
        grounding_fact_ids: ['PLN.SAT', 'HSE.10'],
        initial_status: 'confirmed',
        stamp: STAMP,
      },
      exec,
    )
    expect(row.lifecycle_status).toBe('confirmed')
    expect(row.build_id).toBe(STAMP.build_id)
    expect(row.priors_version).toBe('priors_v7')
    expect(row.now_context_date).toBe('2026-07-28')
    expect(row.confidence).toBe('[0.55,0.7)')
    expect(row.window).toBe('[2026-07-01,2027-01-01)')
    expect(row.technique_refs).toEqual(['vimshottari_dasha', 'transit_saturn'])
    expect(row.confirmed_at).not.toBeNull()
    expect(row.stamp_copied_at).not.toBeNull()
  })

  it('REJECTS an illegal transition (detected → outcome_recorded) and leaves the row unchanged', async () => {
    const row = await createLedgerRow(
      { chart_id: testChart, claim_text: 'candidate claim', initial_status: 'detected' },
      exec,
    )
    await expect(transitionLifecycle(row.id, 'outcome_recorded', {}, exec)).rejects.toBeInstanceOf(
      IllegalTransitionError,
    )
    const after = await getLedgerRow(row.id, exec)
    expect(after?.lifecycle_status).toBe('detected') // unchanged — the reject was real
  })

  it('stamp-immutability: DB blocks UPDATE of a stamp field on a confirmed row', async () => {
    const row = await createLedgerRow(
      {
        chart_id: testChart,
        claim_text: 'immutable claim',
        initial_status: 'confirmed',
        stamp: STAMP,
      },
      exec,
    )
    // Attempt to mutate a stamp field directly (bypassing the DAL) → trigger must RAISE.
    await expect(
      pool.query(`UPDATE ${LEDGER_TABLE} SET build_id = 'tampered' WHERE id = $1`, [row.id]),
    ).rejects.toThrow(/immutable once/)
    // And a settled-claim field is equally frozen.
    await expect(
      pool.query(`UPDATE ${LEDGER_TABLE} SET claim_text = 'rewritten' WHERE id = $1`, [row.id]),
    ).rejects.toThrow(/immutable once/)
    const after = await getLedgerRow(row.id, exec)
    expect(after?.build_id).toBe(STAMP.build_id) // untouched
    expect(after?.claim_text).toBe('immutable claim')
  })

  it('immutability trigger still ALLOWS legal lifecycle + outcome updates (not blanket-blocking)', async () => {
    const row = await createLedgerRow(
      {
        chart_id: testChart,
        claim_text: 'resolvable claim',
        window: { start: '2026-01-01', end: '2026-06-01' },
        confidence: { low: 0.6, high: 0.8 },
        initial_status: 'confirmed',
        stamp: STAMP,
      },
      exec,
    )
    const opened = await transitionLifecycle(row.id, 'open', {}, exec)
    expect(opened.lifecycle_status).toBe('open')
    const closed = await transitionLifecycle(row.id, 'window_closed', {}, exec)
    expect(closed.lifecycle_status).toBe('window_closed')
    const resolved = await recordOutcome(
      row.id,
      { outcome: 'happened', outcome_value: 1.0, outcome_note: 'promoted in March' },
      exec,
    )
    expect(resolved.lifecycle_status).toBe('outcome_recorded')
    expect(resolved.outcome).toBe('happened')
    expect(Number(resolved.outcome_value)).toBe(1.0)
    expect(resolved.outcome_recorded_at).not.toBeNull()
  })

  it('unverifiable resolution is Brier-excluded (outcome_value forced null)', async () => {
    const row = await createLedgerRow(
      { chart_id: testChart, claim_text: 'unverifiable claim', initial_status: 'confirmed', stamp: STAMP },
      exec,
    )
    await transitionLifecycle(row.id, 'open', {}, exec)
    await transitionLifecycle(row.id, 'window_closed', {}, exec)
    const resolved = await recordOutcome(row.id, { outcome: 'unverifiable' }, exec)
    expect(resolved.lifecycle_status).toBe('unverifiable')
    expect(resolved.outcome).toBe('unverifiable')
    expect(resolved.outcome_value).toBeNull() // Brier-excluded
  })

  it('detected → confirmed copies the stamp during the transition (edit-then-confirm path)', async () => {
    const row = await createLedgerRow(
      { chart_id: testChart, claim_text: 'shadow candidate', initial_status: 'detected' },
      exec,
    )
    expect(row.build_id).toBeNull()
    const confirmed = await confirmDetectedRow(row.id, STAMP, exec)
    expect(confirmed.lifecycle_status).toBe('confirmed')
    expect(confirmed.build_id).toBe(STAMP.build_id)
    expect(confirmed.confirmed_at).not.toBeNull()
  })

  it('countLedgerRows returns the chart-scoped count (the §N.4 count_sql, as a function)', async () => {
    const n = await countLedgerRows(testChart, exec)
    expect(n).toBeGreaterThanOrEqual(3)
  })
})
