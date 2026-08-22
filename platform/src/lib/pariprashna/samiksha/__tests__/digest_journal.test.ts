/**
 * SAMĪKṢĀ digest journal UNIT tests — P4-I (DD-21).
 *
 * DB-free coverage of `DbDigestJournal` against a FAKE `LedgerExecutor` (the same DI seam
 * `writer.ts`/`daily_job.ts` use) — proves the SQL shape (as_of-keyed UPSERT, EXISTS-based
 * hasSent, typed read-back) AND, per §N.8, that a real DB failure PROPAGATES rather than being
 * swallowed: a throwing exec must make `markSent`/`hasSent` reject, not silently succeed. The
 * genuine end-to-end proof (a real row written and read back from a real Postgres with migration
 * 588 applied) is `digest_journal_db.integration.test.ts`, gated on `SAMIKSHA_TEST_DATABASE_URL` —
 * this file is the fast, DB-free complement, not a substitute for it (the PB-2
 * false-confidence-gate lesson: a fake exec agreeing with itself proves the call shape, not that
 * the real table accepts it).
 */

import { describe, it, expect, vi } from 'vitest'
import { DbDigestJournal, DIGEST_JOURNAL_TABLE, type DigestSentRecord } from '../digest_journal'
import type { DigestPayload } from '../digest'
import type { LedgerExecutor } from '../writer'

function payload(over: Partial<DigestPayload> = {}): DigestPayload {
  return {
    as_of: '2026-08-23',
    closed: [
      {
        id: '11111111-1111-1111-1111-111111111111',
        chart_id: '1c826d5a-41cb-4450-b4dc-59d440e5f75a',
        claim_text: 'A synthetic claim.',
        domain: 'career',
        window: '[2026-01-01,2026-08-01)',
        confidence: '[0.55,0.7)',
        direction: 'positive',
        window_end: '2026-08-01',
      },
    ],
    closing_soon: [],
    closing_soon_days: 14,
    generated_at: '2026-08-23T03:00:00.000Z',
    ...over,
  }
}

function record(over: Partial<DigestSentRecord> = {}): DigestSentRecord {
  return {
    as_of: '2026-08-23',
    sent_at: '2026-08-23T03:00:01.000Z',
    closed_count: 1,
    closing_soon_count: 0,
    transport_mode: 'log-only-stub',
    real_delivery: false,
    subject: '[Samīkṣā] 1 window(s) closed, 0 closing soon — as of 2026-08-23',
    body_text: 'SAMĪKṢĀ prediction digest — as of 2026-08-23',
    payload: payload(),
    ...over,
  }
}

describe('DbDigestJournal.hasSent', () => {
  it('issues an EXISTS query scoped by as_of and returns the boolean it gets back', async () => {
    const exec = vi.fn(async () => ({ rows: [{ exists: true }] })) as unknown as LedgerExecutor
    const j = new DbDigestJournal(exec)
    const result = await j.hasSent('2026-08-23')
    expect(result).toBe(true)
    expect(exec).toHaveBeenCalledTimes(1)
    const [sql, params] = (exec as ReturnType<typeof vi.fn>).mock.calls[0]
    expect(sql).toContain(DIGEST_JOURNAL_TABLE)
    expect(sql).toContain('EXISTS')
    expect(params).toEqual(['2026-08-23'])
  })

  it('returns false when the query reports no row', async () => {
    const exec = vi.fn(async () => ({ rows: [{ exists: false }] })) as unknown as LedgerExecutor
    const j = new DbDigestJournal(exec)
    expect(await j.hasSent('2026-08-23')).toBe(false)
  })

  it('rejects a malformed as_of before touching the DB', async () => {
    const exec = vi.fn(async () => ({ rows: [] })) as unknown as LedgerExecutor
    const j = new DbDigestJournal(exec)
    await expect(j.hasSent('08/23/2026')).rejects.toThrow(/yyyy-mm-dd/)
    expect(exec).not.toHaveBeenCalled()
  })

  it('§N.8 — PROPAGATES a real DB failure instead of swallowing it', async () => {
    const exec = vi.fn(async () => {
      throw new Error('SIMULATED: connection terminated unexpectedly')
    }) as unknown as LedgerExecutor
    const j = new DbDigestJournal(exec)
    // This is the detector: if this ever resolves instead of rejecting, hasSent() is silently
    // swallowing a real DB error and the "journalled" signal would be unearned per §N.8.
    await expect(j.hasSent('2026-08-23')).rejects.toThrow(/SIMULATED/)
  })
})

describe('DbDigestJournal.markSent', () => {
  it('UPSERTs on as_of, carrying the full rendered content + payload as parameters', async () => {
    const exec = vi.fn(async () => ({ rows: [], rowCount: 1 })) as unknown as LedgerExecutor
    const j = new DbDigestJournal(exec, '1c826d5a-41cb-4450-b4dc-59d440e5f75a')
    await j.markSent('2026-08-23', record())
    expect(exec).toHaveBeenCalledTimes(1)
    const [sql, params] = (exec as ReturnType<typeof vi.fn>).mock.calls[0]
    expect(sql).toContain(`INSERT INTO ${DIGEST_JOURNAL_TABLE}`)
    expect(sql).toContain('ON CONFLICT (as_of) DO UPDATE')
    expect(params?.[0]).toBe('2026-08-23')
    expect(params?.[1]).toBe('1c826d5a-41cb-4450-b4dc-59d440e5f75a') // run_chart_id scope
    expect(params?.[7]).toBe(record().subject)
    expect(params?.[8]).toBe(record().body_text)
    expect(JSON.parse(params?.[9] as string)).toEqual(payload()) // payload serialized as jsonb text
  })

  it('run_chart_id is NULL when no chart scope is given (the default, all-charts sweep)', async () => {
    const exec = vi.fn(async () => ({ rows: [], rowCount: 1 })) as unknown as LedgerExecutor
    const j = new DbDigestJournal(exec)
    await j.markSent('2026-08-23', record())
    const params = (exec as ReturnType<typeof vi.fn>).mock.calls[0][1]
    expect(params?.[1]).toBeNull()
  })

  it('§N.8 — PROPAGATES a real DB failure (e.g. a constraint violation) instead of swallowing it', async () => {
    const exec = vi.fn(async () => {
      throw new Error('SIMULATED: duplicate key value violates unique constraint')
    }) as unknown as LedgerExecutor
    const j = new DbDigestJournal(exec)
    await expect(j.markSent('2026-08-23', record())).rejects.toThrow(/SIMULATED/)
  })
})

describe('DbDigestJournal.readByAsOf', () => {
  it('returns the row when one exists', async () => {
    const row = { id: 1, run_chart_id: null, ...record(), created_at: '2026-08-23T03:00:02.000Z' }
    const exec = vi.fn(async () => ({ rows: [row] })) as unknown as LedgerExecutor
    const j = new DbDigestJournal(exec)
    const result = await j.readByAsOf('2026-08-23')
    expect(result).toEqual(row)
  })

  it('returns null when no digest was journalled for that date', async () => {
    const exec = vi.fn(async () => ({ rows: [] })) as unknown as LedgerExecutor
    const j = new DbDigestJournal(exec)
    expect(await j.readByAsOf('2026-08-23')).toBeNull()
  })
})
