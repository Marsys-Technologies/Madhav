/**
 * Durable-persistence write-ahead outbox — P2-D (PPR-10, FD-9).
 *
 * Exercises the REAL module functions (`writeAheadTurn`, `markPersistence
 * Applied/Failed`, `claimPendingPersistenceEntries`, `replayPendingPersistence`)
 * against an in-memory `OutboxDb` fake that interprets the same SQL shapes the
 * real Postgres pool would see — this is the "well-isolated unit test of the
 * replay logic against a mocked store" the P2-D brief asks for in place of a
 * live-DB crash test (no table exists yet — see the module's own "NEEDS A
 * MIGRATION" header). Nothing here mocks the functions under test themselves.
 */

import { describe, it, expect } from 'vitest'
import {
  writeAheadTurn,
  markPersistenceApplied,
  markPersistenceFailed,
  claimPendingPersistenceEntries,
  persistenceOutboxDepth,
  replayPendingPersistence,
  type OutboxDb,
  type WriteAheadEntryInput,
} from '../durable_outbox'
import type { CanonicalMessage, MessagePartInput } from '../schema'

// ---------------------------------------------------------------------------
// In-memory fake — interprets the exact SQL shapes durable_outbox.ts issues.
// ---------------------------------------------------------------------------

interface FakeRow {
  id: string
  message_id: string
  conversation_id: string
  chart_id: string
  turn_id: string
  payload: unknown
  status: 'pending' | 'applied' | 'failed'
  attempts: number
  enqueued_seq: number
  claimed: boolean
  applied_at: string | null
  last_error: string | null
}

class FakeOutboxDb implements OutboxDb {
  rows: FakeRow[] = []
  private nextId = 1
  private seq = 0

  async query<T = Record<string, unknown>>(sql: string, params: unknown[] = []): Promise<{ rows: T[]; rowCount?: number | null }> {
    if (sql.includes('INSERT INTO') && sql.includes('ON CONFLICT (message_id)')) {
      const [message_id, conversation_id, chart_id, turn_id, payloadJson] = params as string[]
      const existing = this.rows.find((r) => r.message_id === message_id)
      if (existing) {
        existing.payload = JSON.parse(payloadJson)
        existing.status = 'pending'
        existing.last_error = null
        return { rows: [{ id: existing.id } as T] }
      }
      const row: FakeRow = {
        id: String(this.nextId++),
        message_id,
        conversation_id,
        chart_id,
        turn_id,
        payload: JSON.parse(payloadJson),
        status: 'pending',
        attempts: 0,
        enqueued_seq: this.seq++,
        claimed: false,
        applied_at: null,
        last_error: null,
      }
      this.rows.push(row)
      return { rows: [{ id: row.id } as T] }
    }

    if (sql.includes("SET status = 'applied'")) {
      const [id] = params as string[]
      const row = this.rows.find((r) => r.id === id)
      if (row) {
        row.status = 'applied'
        row.applied_at = new Date().toISOString()
        row.last_error = null
      }
      return { rows: [] }
    }

    if (sql.includes('SET status = $2')) {
      const [id, status, message] = params as [string, 'pending' | 'failed', string]
      const row = this.rows.find((r) => r.id === id)
      if (row) {
        row.status = status
        row.last_error = message
        row.attempts += 1
        row.claimed = false
      }
      return { rows: [] }
    }

    if (sql.includes('FOR UPDATE SKIP LOCKED')) {
      const [limit] = params as [number]
      const claimable = this.rows
        .filter((r) => (r.status === 'pending' || r.status === 'failed') && !r.claimed)
        .sort((a, b) => a.enqueued_seq - b.enqueued_seq)
        .slice(0, limit)
      for (const r of claimable) r.claimed = true
      return {
        rows: claimable.map(
          (r) =>
            ({
              id: r.id,
              message_id: r.message_id,
              chart_id: r.chart_id,
              turn_id: r.turn_id,
              payload: r.payload,
              status: r.status,
              attempts: r.attempts,
            }) as T,
        ),
      }
    }

    if (sql.includes('count(*) FILTER')) {
      const pending = this.rows.filter((r) => r.status === 'pending').length
      const failed = this.rows.filter((r) => r.status === 'failed').length
      return { rows: [{ pending: String(pending), failed: String(failed) } as T] }
    }

    throw new Error(`FakeOutboxDb: unrecognized SQL: ${sql.slice(0, 80)}`)
  }
}

function message(id: string): CanonicalMessage {
  return {
    id,
    conversation_id: '22222222-2222-2222-2222-222222222222',
    role: 'assistant',
    schema_version: 1,
    model_id: 'm',
    provider: 'p',
  }
}
function parts(text: string): MessagePartInput[] {
  return [{ seq: 0, kind: 'text', body: { text }, model_visible: true }]
}
function entry(id: string, text: string): WriteAheadEntryInput {
  return {
    message_id: id,
    conversation_id: '22222222-2222-2222-2222-222222222222',
    chart_id: '33333333-3333-3333-3333-333333333333',
    turn_id: `turn-${id}`,
    message: message(id),
    parts: parts(text),
  }
}

describe('writeAheadTurn + markPersistenceApplied/Failed', () => {
  it('enqueues a pending row and returns its id', async () => {
    const db = new FakeOutboxDb()
    const id = await writeAheadTurn(entry('11111111-1111-1111-1111-111111111111', 'hello'), db)
    expect(db.rows).toHaveLength(1)
    expect(db.rows[0].id).toBe(id)
    expect(db.rows[0].status).toBe('pending')
  })

  it('is idempotent: re-enqueuing the same message_id replaces the payload, not a new row', async () => {
    const db = new FakeOutboxDb()
    const id1 = await writeAheadTurn(entry('11111111-1111-1111-1111-111111111111', 'first draft'), db)
    const id2 = await writeAheadTurn(entry('11111111-1111-1111-1111-111111111111', 'second draft'), db)
    expect(id1).toBe(id2)
    expect(db.rows).toHaveLength(1)
    expect((db.rows[0].payload as { message: { id: string } }).message.id).toBe('11111111-1111-1111-1111-111111111111')
  })

  it('markPersistenceApplied transitions pending -> applied', async () => {
    const db = new FakeOutboxDb()
    const id = await writeAheadTurn(entry('11111111-1111-1111-1111-111111111111', 'hello'), db)
    await markPersistenceApplied(id, db)
    expect(db.rows[0].status).toBe('applied')
    expect(db.rows[0].applied_at).not.toBeNull()
  })

  it('markPersistenceFailed defaults to retryable (stays pending) and increments attempts', async () => {
    const db = new FakeOutboxDb()
    const id = await writeAheadTurn(entry('11111111-1111-1111-1111-111111111111', 'hello'), db)
    await markPersistenceFailed(id, new Error('db exploded'), db)
    expect(db.rows[0].status).toBe('pending')
    expect(db.rows[0].attempts).toBe(1)
    expect(db.rows[0].last_error).toContain('db exploded')
  })

  it('markPersistenceFailed({terminal:true}) moves the row to failed', async () => {
    const db = new FakeOutboxDb()
    const id = await writeAheadTurn(entry('11111111-1111-1111-1111-111111111111', 'hello'), db)
    await markPersistenceFailed(id, new Error('poisoned'), db, { terminal: true })
    expect(db.rows[0].status).toBe('failed')
  })
})

describe('claimPendingPersistenceEntries + persistenceOutboxDepth', () => {
  it('claims pending/failed rows in enqueue order, up to the limit', async () => {
    const db = new FakeOutboxDb()
    await writeAheadTurn(entry('11111111-1111-1111-1111-111111111111', 'a'), db)
    await writeAheadTurn(entry('22222222-2222-2222-2222-222222222222', 'b'), db)
    await writeAheadTurn(entry('33333333-3333-3333-3333-333333333333', 'c'), db)
    const claimed = await claimPendingPersistenceEntries(2, db)
    expect(claimed).toHaveLength(2)
    expect(claimed.map((r) => r.message_id)).toEqual([
      '11111111-1111-1111-1111-111111111111',
      '22222222-2222-2222-2222-222222222222',
    ])
  })

  it('does not re-claim an already-claimed row (SKIP LOCKED semantics)', async () => {
    const db = new FakeOutboxDb()
    await writeAheadTurn(entry('11111111-1111-1111-1111-111111111111', 'a'), db)
    const first = await claimPendingPersistenceEntries(10, db)
    const second = await claimPendingPersistenceEntries(10, db)
    expect(first).toHaveLength(1)
    expect(second).toHaveLength(0)
  })

  it('reports honest pending/failed counts', async () => {
    const db = new FakeOutboxDb()
    const id1 = await writeAheadTurn(entry('11111111-1111-1111-1111-111111111111', 'a'), db)
    await writeAheadTurn(entry('22222222-2222-2222-2222-222222222222', 'b'), db)
    await markPersistenceFailed(id1, new Error('x'), db, { terminal: true })
    const depth = await persistenceOutboxDepth(db)
    expect(depth).toEqual({ pending: 1, failed: 1 })
  })
})

describe('replayPendingPersistence — crash recovery', () => {
  it('recovers a turn whose canonical write never happened (crash between write-ahead and writeTurn)', async () => {
    const db = new FakeOutboxDb()
    // Simulates the exact crash window durable_writer.ts's outbox mode
    // creates: the write-ahead entry was recorded, but the process died
    // before the real `writeTurn` (and therefore before markPersistenceApplied)
    // ever ran — the row is left `pending` with the full payload intact.
    await writeAheadTurn(entry('11111111-1111-1111-1111-111111111111', 'the reading that almost got lost'), db)

    const applied: Array<{ id: string; text: string }> = []
    const applyFn = async (message: CanonicalMessage, parts: readonly MessagePartInput[]) => {
      applied.push({ id: message.id, text: (parts[0].body as { text: string }).text })
      return { message_id: message.id, parts_written: parts.length }
    }

    const result = await replayPendingPersistence(db, applyFn)

    expect(result).toEqual({ claimed: 1, applied: 1, failed: 0, errors: [] })
    expect(applied).toEqual([
      { id: '11111111-1111-1111-1111-111111111111', text: 'the reading that almost got lost' },
    ])
    expect(db.rows[0].status).toBe('applied')
  })

  it('one poisoned entry does not stall the recovery of the rest of the sweep', async () => {
    const db = new FakeOutboxDb()
    await writeAheadTurn(entry('11111111-1111-1111-1111-111111111111', 'good turn A'), db)
    await writeAheadTurn(entry('22222222-2222-2222-2222-222222222222', 'poisoned turn'), db)
    await writeAheadTurn(entry('33333333-3333-3333-3333-333333333333', 'good turn B'), db)

    const applyFn = async (message: CanonicalMessage, parts: readonly MessagePartInput[]) => {
      if (message.id === '22222222-2222-2222-2222-222222222222') {
        throw new Error('malformed payload, cannot apply')
      }
      return { message_id: message.id, parts_written: parts.length }
    }

    const result = await replayPendingPersistence(db, applyFn)

    expect(result.claimed).toBe(3)
    expect(result.applied).toBe(2)
    expect(result.failed).toBe(1)
    expect(result.errors).toEqual([
      { outbox_id: '2', message_id: '22222222-2222-2222-2222-222222222222', message: 'malformed payload, cannot apply' },
    ])
    // The two good turns ARE marked applied; the poisoned one stays pending
    // (retryable) with its attempt count bumped, not silently discarded.
    const statuses = Object.fromEntries(db.rows.map((r) => [r.message_id, r.status]))
    expect(statuses['11111111-1111-1111-1111-111111111111']).toBe('applied')
    expect(statuses['33333333-3333-3333-3333-333333333333']).toBe('applied')
    expect(statuses['22222222-2222-2222-2222-222222222222']).toBe('pending')
    expect(db.rows.find((r) => r.message_id === '22222222-2222-2222-2222-222222222222')?.attempts).toBe(1)
  })

  it('a re-run of the sweep converges — idempotent replay, never a duplicate apply', async () => {
    const db = new FakeOutboxDb()
    await writeAheadTurn(entry('11111111-1111-1111-1111-111111111111', 'once only'), db)
    let applyCount = 0
    const applyFn = async () => {
      applyCount += 1
      return { message_id: 'x', parts_written: 1 }
    }
    const first = await replayPendingPersistence(db, applyFn)
    const second = await replayPendingPersistence(db, applyFn)
    expect(first.applied).toBe(1)
    expect(second.claimed).toBe(0) // already applied — nothing left to claim
    expect(applyCount).toBe(1)
  })
})
