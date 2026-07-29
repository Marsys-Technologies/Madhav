/**
 * SAMĪKṢĀ "can't-tell is provably Brier-excluded" — PB-3 lane L-3 ACCEPTANCE (real Postgres).
 *
 * Gated on SAMIKSHA_TEST_DATABASE_URL. Proves the exclusion at ALL THREE enforcement layers,
 * against real seeded rows through the real DAL:
 *   1. DAL: recordOutcome({outcome:'unverifiable'}) lands lifecycle_status='unverifiable' with
 *      outcome_value forced NULL.
 *   2. DB CHECK bmpl_unverifiable_has_no_value: a raw UPDATE giving an unverifiable row a value
 *      is REJECTED by Postgres (structural guarantee, not just app logic).
 *   3. Query layer: the BRIER_ELIGIBLE_SQL predicate + isBrierEligible EXCLUDE the row from a
 *      Brier count, while a `happened` row IS included (demonstrate-can-fail: not blanket).
 */
import { describe, it, expect, beforeAll, afterAll } from 'vitest'
import { Pool } from 'pg'
import {
  createLedgerRow,
  transitionLifecycle,
  recordOutcome,
  type LedgerExecutor,
} from '@/lib/pariprashna/samiksha/writer'
import { getLedgerRow } from '@/lib/pariprashna/samiksha/reader'
import { LEDGER_TABLE, type LedgerStamp } from '@/lib/pariprashna/samiksha/schema'
import { BRIER_ELIGIBLE_SQL, isBrierEligible, isBrierExcluded } from '@/lib/pariprashna/samiksha/brier'

const DB_URL = process.env.SAMIKSHA_TEST_DATABASE_URL
const run = DB_URL ? describe : describe.skip

const STAMP: LedgerStamp = {
  build_id: 'bf2ea4ce-0000-0000-0000-000000000009',
  priors_version: 'priors_v7',
  formula_versions: { salience_formula_ver: null },
  ranking_config: { mode: 'composite_v1' },
  now_context_date: '2026-07-28',
}

run('can’t-tell is Brier-excluded (real DB)', () => {
  let pool: Pool
  let exec: LedgerExecutor
  const CHART = '11111111-2222-3333-4444-5555555500be'

  async function closedRow(claim: string) {
    const r = await createLedgerRow(
      { chart_id: CHART, claim_text: claim, confidence: { low: 0.6, high: 0.8 }, initial_status: 'confirmed', stamp: STAMP },
      exec,
    )
    await transitionLifecycle(r.id, 'open', {}, exec)
    await transitionLifecycle(r.id, 'window_closed', {}, exec)
    return r
  }

  beforeAll(async () => {
    pool = new Pool({ connectionString: DB_URL })
    exec = <T,>(sql: string, params?: unknown[]) =>
      pool.query(sql, params as unknown[]).then((r) => ({ rows: r.rows as T[], rowCount: r.rowCount }))
    await pool.query(`DELETE FROM ${LEDGER_TABLE} WHERE chart_id = $1`, [CHART])
  })
  afterAll(async () => {
    if (pool) {
      await pool.query(`DELETE FROM ${LEDGER_TABLE} WHERE chart_id = $1`, [CHART])
      await pool.end()
    }
  })

  it('layer 1 (DAL): unverifiable resolution forces outcome_value NULL', async () => {
    const r = await closedRow('cannot be judged from available evidence')
    const resolved = await recordOutcome(r.id, { outcome: 'unverifiable' }, exec)
    expect(resolved.lifecycle_status).toBe('unverifiable')
    expect(resolved.outcome).toBe('unverifiable')
    expect(resolved.outcome_value).toBeNull()
    expect(isBrierExcluded(resolved)).toBe(true)
    expect(isBrierEligible(resolved)).toBe(false)
  })

  it('layer 2 (DB CHECK): a raw UPDATE giving an unverifiable row a value is REJECTED', async () => {
    const r = await closedRow('another unjudgeable claim')
    await recordOutcome(r.id, { outcome: 'unverifiable' }, exec)
    await expect(
      pool.query(`UPDATE ${LEDGER_TABLE} SET outcome_value = 0.5 WHERE id = $1`, [r.id]),
    ).rejects.toThrow() // bmpl_unverifiable_has_no_value CHECK
    const after = await getLedgerRow(r.id, exec)
    expect(after?.outcome_value).toBeNull() // still excluded
  })

  it('layer 3 (query): BRIER_ELIGIBLE_SQL counts the happened row, excludes the unverifiable one', async () => {
    const happened = await closedRow('this one clearly happened')
    await recordOutcome(happened.id, { outcome: 'happened', outcome_value: 1 }, exec)
    const cantTell = await closedRow('this one cannot be told')
    await recordOutcome(cantTell.id, { outcome: 'unverifiable' }, exec)

    const { rows } = await pool.query<{ id: string }>(
      `SELECT id FROM ${LEDGER_TABLE} WHERE chart_id = $1 AND ${BRIER_ELIGIBLE_SQL}`,
      [CHART],
    )
    const eligibleIds = rows.map((x) => x.id)
    expect(eligibleIds).toContain(happened.id) // demonstrate-can-fail: scorable rows ARE counted
    expect(eligibleIds).not.toContain(cantTell.id) // can’t-tell is excluded
  })
})
