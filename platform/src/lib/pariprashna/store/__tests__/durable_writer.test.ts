/**
 * `writeTurnDurable` — P2-D (PPR-10, FD-9). All three modes (direct / outbox
 * / degraded-to-direct), driven with injected `writeTurnFn` + `outboxDb`
 * stubs so nothing here touches a real database — matching the brief's
 * "build against an interface/stub for the persistence layer" instruction.
 */

import { describe, it, expect, vi } from 'vitest'
import { writeTurnDurable } from '../durable_writer'
import type { OutboxDb } from '../durable_outbox'
import type { CanonicalMessage, MessagePartInput } from '../schema'
import type { WriteTurnResult } from '../writer'

const MESSAGE: CanonicalMessage = {
  id: '11111111-1111-1111-1111-111111111111',
  conversation_id: '22222222-2222-2222-2222-222222222222',
  role: 'assistant',
  schema_version: 1,
  model_id: 'm',
  provider: 'p',
}
const PARTS: MessagePartInput[] = [{ seq: 0, kind: 'text', body: { text: 'hello' }, model_visible: true }]
const OK_RESULT: WriteTurnResult = { message_id: MESSAGE.id, parts_written: 1 }

/** Minimal working outbox fake — one row's worth is all these tests need. */
function workingOutboxDb(): OutboxDb {
  let row: { id: string; status: string } | null = null
  const query = vi.fn(async (sql: string) => {
    if (sql.includes('INSERT INTO')) {
      row = { id: 'ob-1', status: 'pending' }
      return { rows: [{ id: 'ob-1' }] }
    }
    if (sql.includes("SET status = 'applied'")) {
      if (row) row.status = 'applied'
      return { rows: [] }
    }
    if (sql.includes('SET status = $2')) {
      if (row) row.status = 'pending'
      return { rows: [] }
    }
    throw new Error(`unexpected SQL: ${sql}`)
  })
  // Cast: OutboxDb.query is generic (per-call T); the mock above is a single
  // concrete implementation, which is the correct shape for a test double —
  // the cast just tells TS what every real caller here already knows.
  return { query: query as unknown as OutboxDb['query'] }
}

/** Simulates the pre-migration state: the outbox table does not exist. */
function missingTableOutboxDb(): OutboxDb {
  const query = vi.fn(async () => {
    throw new Error('relation "pariprashna_persistence_outbox" does not exist')
  })
  return { query: query as unknown as OutboxDb['query'] }
}

describe('writeTurnDurable — direct mode (flag off, today\'s exact behavior)', () => {
  it('reports durable/direct on a successful write', async () => {
    const writeTurnFn = vi.fn(async () => OK_RESULT)
    const out = await writeTurnDurable({ message: MESSAGE, parts: PARTS, enabled: false, writeTurnFn })
    expect(out.durable).toEqual({ status: 'durable', mode: 'direct' })
    expect(out.result).toEqual(OK_RESULT)
    expect(writeTurnFn).toHaveBeenCalledWith(MESSAGE, PARTS)
  })

  it('reports failed/direct — never durable — when the canonical write throws', async () => {
    const writeTurnFn = vi.fn(async () => {
      throw new Error('db down')
    })
    const out = await writeTurnDurable({ message: MESSAGE, parts: PARTS, enabled: false, writeTurnFn })
    expect(out.durable.status).toBe('failed')
    expect(out.result).toBeNull()
    expect(out.error).toBeInstanceOf(Error)
  })
})

describe('writeTurnDurable — outbox mode (flag on)', () => {
  it('records a write-ahead entry, applies it, and reports durable/outbox with the outbox id', async () => {
    const writeTurnFn = vi.fn(async () => OK_RESULT)
    const outboxDb = workingOutboxDb()
    const out = await writeTurnDurable({
      message: MESSAGE,
      parts: PARTS,
      enabled: true,
      writeTurnFn,
      outboxDb,
      chartId: '33333333-3333-3333-3333-333333333333',
      turnId: 'turn-1',
    })
    expect(out.durable.status).toBe('durable')
    expect(out.durable.mode).toBe('outbox')
    expect(out.durable.outbox_id).toBe('ob-1')
    expect(out.result).toEqual(OK_RESULT)
  })

  it('reports pending/outbox — never failed — when the canonical write fails after write-ahead succeeded', async () => {
    const writeTurnFn = vi.fn(async () => {
      throw new Error('transient db error')
    })
    const outboxDb = workingOutboxDb()
    const out = await writeTurnDurable({
      message: MESSAGE,
      parts: PARTS,
      enabled: true,
      writeTurnFn,
      outboxDb,
      chartId: '33333333-3333-3333-3333-333333333333',
      turnId: 'turn-1',
    })
    // Honest intermediate state (§N.7 item 6): the write-ahead record still
    // exists and is retryable, so this is NOT reported as a terminal failure.
    expect(out.durable.status).toBe('pending')
    expect(out.durable.mode).toBe('outbox')
    expect(out.result).toBeNull()
    expect(out.error).toBeInstanceOf(Error)
  })

  it('degrades to direct (never throws) when the outbox table does not exist yet (pre-migration)', async () => {
    const writeTurnFn = vi.fn(async () => OK_RESULT)
    const outboxDb = missingTableOutboxDb()
    const out = await writeTurnDurable({
      message: MESSAGE,
      parts: PARTS,
      enabled: true,
      writeTurnFn,
      outboxDb,
      chartId: '33333333-3333-3333-3333-333333333333',
      turnId: 'turn-1',
    })
    expect(out.durable.status).toBe('durable')
    expect(out.durable.mode).toBe('direct')
    expect(out.durable.detail).toBe('outbox_unavailable')
    expect(out.result).toEqual(OK_RESULT)
    // The canonical write still happened — degradation never means data loss.
    expect(writeTurnFn).toHaveBeenCalledTimes(1)
  })

  it('degrades to direct when the flag is on but no outbox port was supplied', async () => {
    const writeTurnFn = vi.fn(async () => OK_RESULT)
    const out = await writeTurnDurable({ message: MESSAGE, parts: PARTS, enabled: true, writeTurnFn })
    expect(out.durable.status).toBe('durable')
    expect(out.durable.mode).toBe('direct')
    expect(out.durable.detail).toBe('outbox_port_not_supplied')
  })
})
