/**
 * DB round-trip integration test for the M-3 `conversation_summaries` store.
 *
 * SKIPPED unless PARIPRASHNA_STORE_DB_TEST=1 AND DATABASE_URL is set — mirrors
 * M-1's `src/lib/pariprashna/store/__tests__/store.db.test.ts` pattern exactly
 * (same env gate, same "throwaway/local Postgres only, never shared prod/dev"
 * discipline, same idempotent beforeAll DDL so a bare Postgres is enough).
 *
 * Proves `PgSummaryStore.findLatest` genuinely persists across independent
 * store INSTANCES (a stronger form of the "process restart" claim than the
 * in-memory-fake unit test in service.test.ts: here a brand-new
 * `PgSummaryStore()` object — standing in for a fresh process with no shared
 * JS state at all — still reads the row a previous instance wrote).
 *
 * Run locally:
 *   PARIPRASHNA_STORE_DB_TEST=1 DATABASE_URL=postgres://... \
 *     pnpm vitest run src/lib/pariprashna/summaries/__tests__/store.db.test.ts
 */
import { describe, it, expect, beforeAll, afterAll } from 'vitest'
import { randomUUID } from 'node:crypto'

const ENABLED = process.env.PARIPRASHNA_STORE_DB_TEST === '1' && !!process.env.DATABASE_URL

const CONVERSATION_ID = randomUUID()
const COVERS_THROUGH_MESSAGE_ID = randomUUID()

describe.skipIf(!ENABLED)('conversation_summaries store — DB round-trip', () => {
  let query: typeof import('@/lib/db/client').query
  let PgSummaryStore: typeof import('../store').PgSummaryStore

  beforeAll(async () => {
    ;({ query } = await import('@/lib/db/client'))
    ;({ PgSummaryStore } = await import('../store'))

    // Idempotent base tables + migration 468 DDL (mirrors the migration file).
    // `conversations` is added here (beyond M-1's own DB test fixture) because
    // migration 468 adds a real FK from conversation_summaries.conversation_id
    // -> conversations(id) — a bare Postgres needs the referenced row to exist.
    await query(`CREATE TABLE IF NOT EXISTS conversations (
      id uuid DEFAULT gen_random_uuid() NOT NULL PRIMARY KEY,
      chart_id uuid NOT NULL,
      user_id text NOT NULL,
      module text NOT NULL,
      created_at timestamptz DEFAULT now())`)
    await query(`CREATE TABLE IF NOT EXISTS conversation_messages (
      id uuid DEFAULT gen_random_uuid() NOT NULL PRIMARY KEY,
      conversation_id uuid NOT NULL,
      parent_message_id uuid,
      role text NOT NULL,
      parts_json jsonb DEFAULT '[]'::jsonb NOT NULL,
      metadata_json jsonb DEFAULT '{}'::jsonb NOT NULL,
      created_at timestamptz DEFAULT now() NOT NULL)`)
    await query(`CREATE TABLE IF NOT EXISTS conversation_summaries (
      id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
      conversation_id uuid NOT NULL REFERENCES conversations(id),
      covers_through_message_id uuid NOT NULL REFERENCES conversation_messages(id),
      summary_text text NOT NULL,
      model_id text,
      created_at timestamptz NOT NULL DEFAULT now())`)
    await query(
      `CREATE INDEX IF NOT EXISTS idx_conversation_summaries_conversation_created
         ON conversation_summaries(conversation_id, created_at DESC)`,
    )

    // Seed the referenced rows the new FKs require.
    await query(
      `INSERT INTO conversations (id, chart_id, user_id, module) VALUES ($1, $2, 'test-user', 'consume')
       ON CONFLICT (id) DO NOTHING`,
      [CONVERSATION_ID, randomUUID()],
    )
    await query(
      `INSERT INTO conversation_messages (id, conversation_id, role) VALUES ($1, $2, 'assistant')
       ON CONFLICT (id) DO NOTHING`,
      [COVERS_THROUGH_MESSAGE_ID, CONVERSATION_ID],
    )
  })

  afterAll(async () => {
    if (!ENABLED) return
    await query('DELETE FROM conversation_summaries WHERE conversation_id = $1', [CONVERSATION_ID])
    await query('DELETE FROM conversation_messages WHERE conversation_id = $1', [CONVERSATION_ID])
    await query('DELETE FROM conversations WHERE id = $1', [CONVERSATION_ID])
  })

  it('insert() persists a row; a BRAND-NEW store instance finds it via findLatest() (restart-equivalent)', async () => {
    const writerInstance = new PgSummaryStore()
    const inserted = await writerInstance.insert({
      conversation_id: CONVERSATION_ID,
      covers_through_message_id: COVERS_THROUGH_MESSAGE_ID,
      summary_text: 'Earlier turns covered career timing and Moon dignity. [1] SIG.MSR.042 (L2): note.',
      model_id: 'test-model',
    })
    expect(inserted.conversation_id).toBe(CONVERSATION_ID)

    // A FRESH instance — no shared JS state with writerInstance whatsoever —
    // standing in for a fresh process after a restart.
    const freshInstance = new PgSummaryStore()
    const found = await freshInstance.findLatest(CONVERSATION_ID)

    expect(found).not.toBeNull()
    expect(found!.id).toBe(inserted.id)
    expect(found!.covers_through_message_id).toBe(COVERS_THROUGH_MESSAGE_ID)
    expect(found!.summary_text).toContain('SIG.MSR.042')
  })

  it('is append-only: a second insert() adds a new row; findLatest() returns the most recent', async () => {
    const store = new PgSummaryStore()
    const second = await store.insert({
      conversation_id: CONVERSATION_ID,
      covers_through_message_id: randomUUID(),
      summary_text: 'A later summary, folded on top of the first.',
      model_id: 'test-model',
    })

    const latest = await store.findLatest(CONVERSATION_ID)
    expect(latest!.id).toBe(second.id)

    const { rows } = await query<{ count: string }>(
      'SELECT count(*)::text AS count FROM conversation_summaries WHERE conversation_id = $1',
      [CONVERSATION_ID],
    )
    expect(Number(rows[0].count)).toBe(2)
  })
})
