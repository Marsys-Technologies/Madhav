/**
 * DB round-trip integration test for the M-1 canonical store.
 *
 * SKIPPED unless PARIPRASHNA_STORE_DB_TEST=1 AND DATABASE_URL is set — it needs
 * a live Postgres. It is designed to run against a THROWAWAY / local Postgres
 * (see the lane report), NEVER against the shared production/dev DB: it writes a
 * uniquely-id'd test message + parts and deletes them in afterAll. It is
 * self-contained — beforeAll applies the migration DDL idempotently (ADD COLUMN
 * IF NOT EXISTS / CREATE TABLE IF NOT EXISTS), so a bare Postgres with only the
 * base conversation_messages table is enough.
 *
 * Run locally:
 *   PARIPRASHNA_STORE_DB_TEST=1 DATABASE_URL=postgres://... \
 *     pnpm vitest run src/lib/pariprashna/store/__tests__/store.db.test.ts
 */
import { describe, it, expect, beforeAll, afterAll } from 'vitest'
import { randomUUID } from 'node:crypto'

const ENABLED = process.env.PARIPRASHNA_STORE_DB_TEST === '1' && !!process.env.DATABASE_URL

const CONVERSATION_ID = randomUUID()
const MESSAGE_ID = randomUUID()

// A part of EVERY kind, seq 0..6.
const ALL_KIND_PARTS = [
  { seq: 0, kind: 'text' as const, body: { text: 'Moon in Purva Bhadrapada.' }, model_visible: true },
  { seq: 1, kind: 'reasoning' as const, body: { text: 'weigh dignity', signature: 'sig', provider_opaque: 'op' }, model_visible: false },
  { seq: 2, kind: 'tool_call' as const, body: { call_id: 'c1', tool_name: 'ganita_nakshatra_get', args: { planet: 'Moon' } }, model_visible: false },
  { seq: 3, kind: 'tool_result' as const, body: { call_id: 'c1', status: 'done' as const, count: 1, ms: 42 }, model_visible: false },
  { seq: 4, kind: 'citation' as const, body: { index: 1, signal_id: 'SIG.MSR.042', layer: 'L2', snippet: 's', grade: 'primary' }, model_visible: true },
  { seq: 5, kind: 'prediction_candidate' as const, body: { claim: 'career shift', window: '2027-Q1', confidence: 0.6, falsifier: 'none by 2027-06' }, model_visible: true },
  { seq: 6, kind: 'attachment' as const, body: { media_type: 'image/png', filename: 'chart.png', bytes: 100 }, model_visible: true },
]

describe.skipIf(!ENABLED)('message_parts store — DB round-trip', () => {
  let writeTurn: typeof import('../writer').writeTurn
  let readTurnParts: typeof import('../reader').readTurnParts
  let readCanonicalMessage: typeof import('../reader').readCanonicalMessage
  let query: typeof import('@/lib/db/client').query
  let serializeCanonical: typeof import('../serialize').serializeCanonical

  const MESSAGE = {
    id: MESSAGE_ID,
    conversation_id: CONVERSATION_ID,
    role: 'assistant' as const,
    schema_version: 1,
    model_id: 'claude-opus-4-8[1m]',
    provider: 'anthropic',
  }

  beforeAll(async () => {
    ;({ query } = await import('@/lib/db/client'))
    ;({ writeTurn } = await import('../writer'))
    ;({ readTurnParts, readCanonicalMessage } = await import('../reader'))
    ;({ serializeCanonical } = await import('../serialize'))

    // Idempotent base + migration DDL (mirrors migration 467).
    await query(`CREATE TABLE IF NOT EXISTS conversation_messages (
      id uuid DEFAULT gen_random_uuid() NOT NULL PRIMARY KEY,
      conversation_id uuid NOT NULL,
      parent_message_id uuid,
      role text NOT NULL,
      parts_json jsonb DEFAULT '[]'::jsonb NOT NULL,
      metadata_json jsonb DEFAULT '{}'::jsonb NOT NULL,
      created_at timestamptz DEFAULT now() NOT NULL)`)
    await query(`ALTER TABLE conversation_messages
      ADD COLUMN IF NOT EXISTS schema_version int,
      ADD COLUMN IF NOT EXISTS model_id text,
      ADD COLUMN IF NOT EXISTS provider text`)
    await query(`CREATE TABLE IF NOT EXISTS message_parts (
      id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
      message_id uuid NOT NULL REFERENCES conversation_messages(id),
      seq int NOT NULL,
      kind text NOT NULL CHECK (kind IN ('text','reasoning','tool_call','tool_result','citation','prediction_candidate','attachment')),
      body jsonb NOT NULL,
      model_visible boolean NOT NULL,
      created_at timestamptz NOT NULL DEFAULT now())`)
    await query(`CREATE UNIQUE INDEX IF NOT EXISTS idx_message_parts_message_seq ON message_parts(message_id, seq)`)
  })

  afterAll(async () => {
    if (!ENABLED) return
    await query('DELETE FROM message_parts WHERE message_id = $1', [MESSAGE_ID])
    await query('DELETE FROM conversation_messages WHERE id = $1', [MESSAGE_ID])
  })

  it('writes a turn with every kind and reads all 7 parts back in seq order', async () => {
    const res = await writeTurn(MESSAGE, ALL_KIND_PARTS)
    expect(res.message_id).toBe(MESSAGE_ID)
    expect(res.parts_written).toBe(7)

    const parts = await readTurnParts(MESSAGE_ID)
    expect(parts.map((p) => p.seq)).toEqual([0, 1, 2, 3, 4, 5, 6])
    expect(parts.map((p) => p.kind)).toEqual([
      'text', 'reasoning', 'tool_call', 'tool_result', 'citation', 'prediction_candidate', 'attachment',
    ])
    // model_visible round-trips exactly.
    expect(parts.map((p) => p.model_visible)).toEqual([true, false, false, false, true, true, true])
    // A body round-trips intact.
    expect(parts[2].body).toEqual({ call_id: 'c1', tool_name: 'ganita_nakshatra_get', args: { planet: 'Moon' } })
  })

  it('reads the canonical message row (additive columns populated)', async () => {
    const msg = await readCanonicalMessage(MESSAGE_ID)
    expect(msg).not.toBeNull()
    expect(msg!.model_id).toBe('claude-opus-4-8[1m]')
    expect(msg!.provider).toBe('anthropic')
    expect(msg!.schema_version).toBe(1)
  })

  it('END-TO-END determinism: serialize(input) === serialize(DB readback)', async () => {
    const parts = await readTurnParts(MESSAGE_ID)
    const fromInput = serializeCanonical(MESSAGE, ALL_KIND_PARTS)
    const fromDb = serializeCanonical(MESSAGE, parts)
    expect(fromDb).toBe(fromInput)
  })

  it('is idempotent: re-writing the same turn keeps 7 parts (delete-then-insert)', async () => {
    await writeTurn(MESSAGE, ALL_KIND_PARTS)
    const parts = await readTurnParts(MESSAGE_ID)
    expect(parts.length).toBe(7)
  })

  it('DB CHECK constraint rejects an invalid kind (raw insert)', async () => {
    await expect(
      query(
        `INSERT INTO message_parts (message_id, seq, kind, body, model_visible)
         VALUES ($1, 99, 'bogus_kind', '{}'::jsonb, true)`,
        [MESSAGE_ID],
      ),
    ).rejects.toThrow(/check constraint|message_parts_kind_check/i)
  })

  it('writer rejects an invalid part body BEFORE writing (no partial turn)', async () => {
    const badMessageId = randomUUID()
    await expect(
      writeTurn(
        { ...MESSAGE, id: badMessageId },
        [{ seq: 0, kind: 'tool_call', body: { tool_name: 'x' } as unknown as Record<string, unknown>, model_visible: false }],
      ),
    ).rejects.toThrow()
    // Nothing was written for the bad message id.
    const parts = await readTurnParts(badMessageId)
    expect(parts.length).toBe(0)
  })
})
