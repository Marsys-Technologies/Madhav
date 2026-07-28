/**
 * SAMĪKṢĀ "badge equals SQL truth" — PB-3 lane L-3 ACCEPTANCE (real migrated Postgres).
 *
 * Gated on SAMIKSHA_TEST_DATABASE_URL (skipped in CI; run via the throwaway-DB harness). This
 * is the anti-false-confidence design the FOLLOWUP_PB-2 memo demands: the badge value is
 * compared against SQL truth computed by GENUINELY DIFFERENT logic — never two copies of the
 * same query that would agree even if both were wrong:
 *   • production path:  countBadge() → `count(*) WHERE lifecycle_status = ANY(['detected','window_closed'])`
 *   • oracle A (literal): the KNOWN seeded composition (3 detected + 2 window_closed = 5)
 *   • oracle B (SQL, different shape): two separate scalar counts summed
 *   • oracle C (JS): fetch ALL rows, filter in JavaScript by the two states
 *   • the rendered <SamiksaBadge> shows exactly that number.
 * Rows are seeded through the REAL lifecycle DAL (createLedgerRow + transitions), not hand-
 * forced states. A negative assertion proves `open` rows exist yet are NOT counted, and a
 * demonstrate-can-fail step adds one detected row and shows the badge tracks to 6.
 */
import { describe, it, expect, beforeAll, afterAll } from 'vitest'
import { render, cleanup } from '@testing-library/react'
import { Pool } from 'pg'
import {
  createLedgerRow,
  transitionLifecycle,
  recordOutcome,
  type LedgerExecutor,
} from '@/lib/pariprashna/samiksha/writer'
import { listLedgerRowsForChart } from '@/lib/pariprashna/samiksha/reader'
import { countBadge, BADGE_LIFECYCLE_STATES } from '@/lib/pariprashna/samiksha/badge'
import { LEDGER_TABLE, type LedgerStamp } from '@/lib/pariprashna/samiksha/schema'
import { SamiksaBadge } from '@/components/pariprashna/samiksha/SamiksaBadge'

const DB_URL = process.env.SAMIKSHA_TEST_DATABASE_URL
const run = DB_URL ? describe : describe.skip

const STAMP: LedgerStamp = {
  build_id: 'bf2ea4ce-0000-0000-0000-000000000001',
  priors_version: 'priors_v7',
  formula_versions: { salience_formula_ver: null },
  ranking_config: { mode: 'composite_v1' },
  now_context_date: '2026-07-28',
}

run('badge equals SQL truth (real DB)', () => {
  let pool: Pool
  let exec: LedgerExecutor
  const CHART = '11111111-2222-3333-4444-5555555500b3'

  async function seedDetected() {
    return createLedgerRow({ chart_id: CHART, claim_text: 'detected candidate', initial_status: 'detected' }, exec)
  }
  async function seedInState(state: 'open' | 'window_closed' | 'outcome_recorded' | 'dismissed') {
    if (state === 'dismissed') {
      const r = await createLedgerRow({ chart_id: CHART, claim_text: 'to dismiss', initial_status: 'detected' }, exec)
      await transitionLifecycle(r.id, 'dismissed', { dismissed_reason: 'noise' }, exec)
      return r
    }
    const r = await createLedgerRow(
      { chart_id: CHART, claim_text: `seed ${state}`, initial_status: 'confirmed', stamp: STAMP },
      exec,
    )
    await transitionLifecycle(r.id, 'open', {}, exec)
    if (state === 'open') return r
    await transitionLifecycle(r.id, 'window_closed', {}, exec)
    if (state === 'window_closed') return r
    await recordOutcome(r.id, { outcome: 'happened', outcome_value: 1 }, exec)
    return r
  }

  beforeAll(async () => {
    pool = new Pool({ connectionString: DB_URL })
    exec = <T,>(sql: string, params?: unknown[]) =>
      pool.query(sql, params as unknown[]).then((r) => ({ rows: r.rows as T[], rowCount: r.rowCount }))
    await pool.query(`DELETE FROM ${LEDGER_TABLE} WHERE chart_id = $1`, [CHART])

    // KNOWN composition — the literal oracle.
    await Promise.all([seedDetected(), seedDetected(), seedDetected()]) // 3 detected  → on badge
    await seedInState('window_closed') // window_closed → on badge
    await seedInState('window_closed') // window_closed → on badge
    await seedInState('open') // open → NOT on badge
    await seedInState('open')
    await seedInState('open')
    await seedInState('open')
    await seedInState('dismissed') // NOT on badge
    await seedInState('outcome_recorded') // NOT on badge
  })
  afterAll(async () => {
    cleanup()
    if (pool) {
      await pool.query(`DELETE FROM ${LEDGER_TABLE} WHERE chart_id = $1`, [CHART])
      await pool.end()
    }
  })

  it('production countBadge equals the literal known truth (5)', async () => {
    expect(await countBadge(CHART, exec)).toBe(5)
  })

  it('equals oracle B — two separate scalar counts summed (different SQL shape)', async () => {
    const badge = await countBadge(CHART, exec)
    const { rows } = await pool.query<{ total: string }>(
      `SELECT (
         (SELECT count(*) FROM ${LEDGER_TABLE} WHERE chart_id = $1 AND lifecycle_status = 'detected')
       + (SELECT count(*) FROM ${LEDGER_TABLE} WHERE chart_id = $1 AND lifecycle_status = 'window_closed')
       )::text AS total`,
      [CHART],
    )
    expect(Number(rows[0].total)).toBe(badge)
  })

  it('equals oracle C — all rows fetched, filtered in JavaScript', async () => {
    const badge = await countBadge(CHART, exec)
    const all = await listLedgerRowsForChart(CHART, {}, exec)
    const jsCount = all.filter((r) => BADGE_LIFECYCLE_STATES.includes(r.lifecycle_status)).length
    expect(jsCount).toBe(badge)
  })

  it('the rendered badge displays exactly the SQL-true count', async () => {
    const badge = await countBadge(CHART, exec)
    const { container } = render(<SamiksaBadge count={badge} />)
    expect(container.querySelector('.samiksa-badge')?.textContent).toBe('5')
  })

  it('open rows exist but are NOT counted (badge is 5, not 9)', async () => {
    const { rows } = await pool.query<{ n: string }>(
      `SELECT count(*)::text AS n FROM ${LEDGER_TABLE} WHERE chart_id = $1 AND lifecycle_status = 'open'`,
      [CHART],
    )
    expect(Number(rows[0].n)).toBe(4) // the four open rows are really there
    expect(await countBadge(CHART, exec)).toBe(5) // yet the badge excludes them
  })

  it('demonstrate-can-fail: adding one detected row moves the badge to 6', async () => {
    await seedDetected()
    expect(await countBadge(CHART, exec)).toBe(6)
  })
})
