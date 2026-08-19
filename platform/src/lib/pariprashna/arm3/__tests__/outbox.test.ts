/**
 * P1 G1-C — unit suite for the arm-3 outbox + drain (no database).
 *
 * These prove the SHAPE of arm-3: what the queue accepts, what it refuses, and
 * that a failing intent is recorded rather than swallowed. The real ledger
 * behaviour is proven against a live Postgres in `roles_rls.db.test.ts`; this
 * file deliberately does not claim to cover that.
 */

import { describe, expect, it } from 'vitest'

import { applyIntent, drainOutbox } from '../drain'
import {
  LedgerIntentSchema,
  OUTBOX_TABLE,
  chartIdOf,
  enqueueLedgerIntent,
  type OutboxDb,
  type OutboxRow,
} from '../outbox'

const CHART = '11111111-2222-3333-4444-555555555555'
const OTHER = '99999999-8888-7777-6666-555555555555'
const PART = 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee'

/** Records every statement, answers with whatever the test queued up. */
function fakeDb(answers: Array<{ rows: unknown[] }> = []) {
  const calls: Array<{ sql: string; params?: unknown[] }> = []
  let i = 0
  const db: OutboxDb = {
    async query(sql: string, params?: unknown[]) {
      calls.push({ sql, params })
      const a = answers[i++] ?? { rows: [] }
      return { rows: a.rows as never[], rowCount: a.rows.length }
    },
  }
  return { db, calls }
}

describe('LedgerIntentSchema', () => {
  it('accepts a well-formed create_detected intent', () => {
    const parsed = LedgerIntentSchema.parse({
      op: 'create_detected',
      payload: { chart_id: CHART, message_part_id: PART, claim_text: 'a claim' },
    })
    expect(parsed.op).toBe('create_detected')
    expect(chartIdOf(parsed)).toBe(CHART)
  })

  it('applies the documented defaults rather than leaving arrays undefined', () => {
    const parsed = LedgerIntentSchema.parse({
      op: 'create_detected',
      payload: { chart_id: CHART, claim_text: 'a claim' },
    })
    const p = parsed.payload as Record<string, unknown>
    expect(p.technique_refs).toEqual([])
    expect(p.grounding_fact_ids).toEqual([])
    expect(p.created_from_channel).toBe('pariprashna')
  })

  it('REFUSES a confidence band on create_detected (W-1 no-auto-promotion)', () => {
    // The queue must not be a channel for writing a probability no human
    // committed. `.strict()` is what enforces it, and this is the test that
    // would fail if someone relaxed it.
    expect(() =>
      LedgerIntentSchema.parse({
        op: 'create_detected',
        payload: { chart_id: CHART, claim_text: 'a claim', confidence: { lo: 0.6, hi: 0.8 } },
      }),
    ).toThrow()
  })

  it('REFUSES a lifecycle_status smuggled into the payload', () => {
    expect(() =>
      LedgerIntentSchema.parse({
        op: 'create_detected',
        payload: { chart_id: CHART, claim_text: 'a claim', lifecycle_status: 'confirmed' },
      }),
    ).toThrow()
  })

  it('REFUSES an unknown op', () => {
    expect(() =>
      LedgerIntentSchema.parse({ op: 'drop_everything', payload: { chart_id: CHART } }),
    ).toThrow()
  })

  it('REFUSES a non-uuid chart_id', () => {
    expect(() =>
      LedgerIntentSchema.parse({
        op: 'create_detected',
        payload: { chart_id: 'not-a-uuid', claim_text: 'x' },
      }),
    ).toThrow()
  })

  it('REFUSES an out-of-range outcome_value', () => {
    expect(() =>
      LedgerIntentSchema.parse({
        op: 'record_outcome',
        payload: { chart_id: CHART, ledger_row_id: PART, outcome: 'happened', outcome_value: 1.5 },
      }),
    ).toThrow()
  })
})

describe('enqueueLedgerIntent', () => {
  it('writes to the outbox, never to the ledger', async () => {
    const { db, calls } = fakeDb([{ rows: [{ id: '7' }] }])
    const id = await enqueueLedgerIntent(
      { op: 'create_detected', payload: { chart_id: CHART, claim_text: 'a claim' } },
      db,
    )
    expect(id).toBe('7')
    expect(calls).toHaveLength(1)
    expect(calls[0].sql).toContain(OUTBOX_TABLE)
    expect(calls[0].sql).not.toContain('brahma_mimamsa_prediction_ledger')
  })

  it('scopes the outbox row from the payload, not a separate argument', async () => {
    const { db, calls } = fakeDb([{ rows: [{ id: '1' }] }])
    await enqueueLedgerIntent(
      { op: 'create_detected', payload: { chart_id: CHART, claim_text: 'x' } },
      db,
    )
    expect(calls[0].params?.[0]).toBe(CHART)
  })
})

describe('applyIntent', () => {
  const row = (over: Partial<OutboxRow> = {}): OutboxRow => ({
    id: '1',
    chart_id: CHART,
    op: 'create_detected',
    payload: { chart_id: CHART, claim_text: 'a claim' },
    attempts: 1,
    ...over,
  })

  it('writes a detected ledger row', async () => {
    const { db, calls } = fakeDb([{ rows: [{ id: 'ledger-1' }] }])
    await expect(applyIntent(row(), db)).resolves.toBe('ledger-1')
    expect(calls[0].sql).toContain('INSERT INTO brahma_mimamsa_prediction_ledger')
    expect(calls[0].sql).toContain("'detected'")
  })

  it('REFUSES when the outbox scope and the payload scope disagree', async () => {
    // If these ever diverge, one of them was rewritten. Picking a winner would
    // mean writing a ledger row into a chart nobody authorized.
    const { db, calls } = fakeDb()
    await expect(
      applyIntent(row({ chart_id: OTHER }), db),
    ).rejects.toThrow(/ARM3_CHART_MISMATCH/)
    expect(calls).toHaveLength(0)
  })

  it('re-validates the payload after dequeue (the producer is untrusted)', async () => {
    const { db } = fakeDb()
    await expect(
      applyIntent(row({ payload: { chart_id: CHART } }), db), // claim_text missing
    ).rejects.toThrow()
  })

  it('fails loudly on the reserved-but-unbuilt create_confirmed op', async () => {
    const { db } = fakeDb()
    await expect(
      applyIntent(
        row({ op: 'create_confirmed', payload: { chart_id: CHART } }),
        db,
      ),
    ).rejects.toThrow(/ARM3_OP_NOT_IMPLEMENTED/)
  })
})

describe('drainOutbox', () => {
  it('reports nothing when the queue is empty', async () => {
    const { db } = fakeDb([{ rows: [] }])
    const r = await drainOutbox(db)
    expect(r).toEqual({ claimed: 0, applied: 0, failed: 0, errors: [] })
  })

  it('one poisoned intent does not stall the rest of the batch', async () => {
    const { db } = fakeDb([
      // claim
      {
        rows: [
          { id: '1', chart_id: CHART, op: 'create_detected', payload: { chart_id: CHART }, attempts: 1 },
          {
            id: '2',
            chart_id: CHART,
            op: 'create_detected',
            payload: { chart_id: CHART, claim_text: 'good' },
            attempts: 1,
          },
        ],
      },
      { rows: [] }, // markIntentFailed for #1
      { rows: [{ id: 'ledger-2' }] }, // insert for #2
      { rows: [] }, // markIntentApplied for #2
    ])
    const r = await drainOutbox(db)
    expect(r.claimed).toBe(2)
    expect(r.applied).toBe(1)
    expect(r.failed).toBe(1)
    expect(r.errors).toHaveLength(1)
    expect(r.errors[0].outbox_id).toBe('1')
  })
})
