/**
 * SAMĪKṢĀ outcome recorder — REAL-DB integration test — PB-3 lane L-5.
 *
 * Drives recordConversationalOutcome() against a REAL Postgres with migration 470 actually
 * applied (NOT a mock of the recorder agreeing with itself — the PB-2 false-confidence
 * lesson). Gated on SAMIKSHA_TEST_DATABASE_URL; skipped where absent (CI has no DB). Run
 * locally via the L-5 throwaway-DB harness (scripts/samiksha_l5_roundtrip.sh), which spins up
 * a throwaway cluster, applies migration 470, and points this env var at it.
 *
 * Proves the round-trip the brief's acceptance names, with evidence that CAN fail:
 *   - a real window_closed ledger row → recordConversationalOutcome → the row is
 *     outcome_recorded in the DB with the correct co-located outcome_value, and the returned
 *     Brier + CalibrationWriteIntent (source_citation = the ledger row id) are correct;
 *   - the unverifiable path resolves Brier-EXCLUDED (outcome_value NULL, brier null);
 *   - recording on a non-window_closed row is REJECTED (the guard is real).
 */

import { describe, it, expect, beforeAll, afterAll } from 'vitest'
import { Pool } from 'pg'
import { createLedgerRow, transitionLifecycle, type LedgerExecutor } from '@/lib/pariprashna/samiksha/writer'
import { getLedgerRow } from '@/lib/pariprashna/samiksha/reader'
import { recordConversationalOutcome } from '@/lib/pariprashna/samiksha/outcome_recorder'
import { LEDGER_TABLE, type LedgerStamp } from '@/lib/pariprashna/samiksha/schema'

const DB_URL = process.env.SAMIKSHA_TEST_DATABASE_URL
const run = DB_URL ? describe : describe.skip

const STAMP: LedgerStamp = {
  build_id: 'bf2ea4ce-0000-0000-0000-0000000000a5',
  priors_version: 'priors_v7',
  formula_versions: { salience_formula_ver: null },
  ranking_config: { mode: 'composite_v1' },
  now_context_date: '2026-07-28',
}

run('SAMĪKṢĀ L-5 recordConversationalOutcome against a real migrated Postgres', () => {
  let pool: Pool
  let exec: LedgerExecutor
  const testChart = '11111111-2222-3333-4444-5555555550a5'

  async function newWindowClosedRow(confidence: { low: number; high: number }): Promise<string> {
    const row = await createLedgerRow(
      {
        chart_id: testChart,
        claim_text: 'Native transitions to a leadership role by end of 2026.',
        domain: 'career',
        window: { start: '2026-01-01', end: '2026-06-01' },
        confidence,
        direction: 'positive',
        technique_refs: ['vimshottari_dasha', 'transit_saturn'],
        grounding_fact_ids: ['PLN.SAT', 'HSE.10'],
        initial_status: 'confirmed',
        stamp: STAMP,
      },
      exec,
    )
    await transitionLifecycle(row.id, 'open', {}, exec)
    await transitionLifecycle(row.id, 'window_closed', {}, exec)
    return row.id
  }

  beforeAll(async () => {
    pool = new Pool({ connectionString: DB_URL })
    exec = <T,>(sql: string, params?: unknown[]) =>
      pool.query(sql, params as unknown[]).then((r) => ({ rows: r.rows as T[], rowCount: r.rowCount }))
    await pool.query(`DELETE FROM ${LEDGER_TABLE} WHERE chart_id = $1`, [testChart])
  })
  afterAll(async () => {
    if (pool) {
      // SAMIKSHA_KEEP leaves the rows behind for manual psql inspection of the real persisted
      // outcome (evidence capture); unset (the default / CI) cleans up.
      if (!process.env.SAMIKSHA_KEEP) {
        await pool.query(`DELETE FROM ${LEDGER_TABLE} WHERE chart_id = $1`, [testChart])
      }
      await pool.end()
    }
  })

  it('happened: round-trips to outcome_recorded with Brier + ledger-cited calibration intent', async () => {
    const id = await newWindowClosedRow({ low: 0.55, high: 0.7 }) // point 0.625
    const result = await recordConversationalOutcome(id, { outcome: 'happened', outcome_note: 'promoted in March' }, exec)

    // The ledger row was really transitioned + persisted (read it back independently).
    const persisted = await getLedgerRow(id, exec)
    expect(persisted?.lifecycle_status).toBe('outcome_recorded')
    expect(persisted?.outcome).toBe('happened')
    expect(Number(persisted?.outcome_value)).toBe(1.0)
    expect(persisted?.outcome_note).toBe('promoted in March')
    expect(persisted?.outcome_recorded_at).not.toBeNull()

    // The computed Brier: (0.625 − 1)² = 0.140625.
    expect(result.brier).toBeCloseTo(0.140625, 10)
    expect(result.confidence_point).toBeCloseTo(0.625, 10)

    // The calibration intent cites the LEDGER ROW, not mimamsa_predictions/phala_anchors.
    expect(result.calibration_intent.source_citation).toBe(id)
    expect(result.calibration_intent.prediction_ledger_row_id).toBe(id)
    expect(result.calibration_intent.chart_id).toBe(testChart)
    expect(result.calibration_intent.brier).toBeCloseTo(0.140625, 10)
    expect(result.calibration_intent.brier_excluded).toBe(false)

    // Persistence into mimamsa_calibration is PARKED (not silently claimed).
    expect(result.calibration_persisted).toBe(false)
    expect(result.calibration_park_reason).toMatch(/PARKED/)
  })

  it('did_not_happen: high-confidence miss scores a high Brier', async () => {
    // Band {0.9,1.0} → midpoint 0.95; did_not_happen value 0 → Brier (0.95)² = 0.9025.
    // (A degenerate {1,1} band is intentionally avoided here — see the empty-range test below.)
    const id = await newWindowClosedRow({ low: 0.9, high: 1.0 })
    const result = await recordConversationalOutcome(id, { outcome: 'did_not_happen' }, exec)
    expect(result.confidence_point).toBeCloseTo(0.95, 10)
    expect(result.brier).toBeCloseTo(0.9025, 10)
    const persisted = await getLedgerRow(id, exec)
    expect(persisted?.lifecycle_status).toBe('outcome_recorded')
    expect(Number(persisted?.outcome_value)).toBe(0.0)
  })

  it('degenerate [x,x) band serializes to Postgres empty → honest-null Brier (no fabricated score)', async () => {
    // L-1's writer stores confidence as the numrange literal [low,high); a point band {x,x}
    // is [x,x) = EMPTY in Postgres. The recorder must NOT invent a confidence: it resolves the
    // ledger row (outcome still persisted) but reports brier null, brier_excluded true.
    const id = await newWindowClosedRow({ low: 1, high: 1 })
    const result = await recordConversationalOutcome(id, { outcome: 'did_not_happen' }, exec)
    expect(result.confidence_point).toBeNull()
    expect(result.brier).toBeNull()
    expect(result.calibration_intent.brier_excluded).toBe(true)
    const persisted = await getLedgerRow(id, exec)
    expect(persisted?.lifecycle_status).toBe('outcome_recorded')
    expect(Number(persisted?.outcome_value)).toBe(0.0)
  })

  it('unverifiable: resolves Brier-EXCLUDED (outcome_value NULL, brier null)', async () => {
    const id = await newWindowClosedRow({ low: 0.6, high: 0.8 })
    const result = await recordConversationalOutcome(id, { outcome: 'unverifiable' }, exec)
    expect(result.brier).toBeNull()
    expect(result.outcome_value).toBeNull()
    expect(result.calibration_intent.brier_excluded).toBe(true)
    const persisted = await getLedgerRow(id, exec)
    expect(persisted?.lifecycle_status).toBe('unverifiable')
    expect(persisted?.outcome_value).toBeNull()
  })

  it('REJECTS recording an outcome on a row that is not window_closed', async () => {
    const row = await createLedgerRow(
      { chart_id: testChart, claim_text: 'still open claim', initial_status: 'confirmed', stamp: STAMP },
      exec,
    )
    await transitionLifecycle(row.id, 'open', {}, exec) // open, NOT window_closed
    await expect(recordConversationalOutcome(row.id, { outcome: 'happened' }, exec)).rejects.toThrow(
      /not\s+'window_closed'/,
    )
    const after = await getLedgerRow(row.id, exec)
    expect(after?.lifecycle_status).toBe('open') // unchanged — the reject was real
  })
})
