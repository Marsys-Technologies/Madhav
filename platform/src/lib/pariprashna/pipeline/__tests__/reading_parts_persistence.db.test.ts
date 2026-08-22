/**
 * Lane P3-C (SMṚTI completion) — pipeline-level DB round-trip.
 *
 * `store/__tests__/store.db.test.ts` already proves the low-level DAL
 * (`writer.ts`/`reader.ts`) can persist and read back every `message_parts`
 * kind. What THIS lane added is the wiring one layer up: does the real
 * pipeline function (`reading_parts.buildCanonicalParts`, the same function
 * `persistence_stage.ts` calls) actually PRODUCE `tool_call`/`tool_result`/
 * `reasoning` parts from a turn's real in-memory shape (committed thinking
 * block + a successful evidence-stage dispatch), and does the additive
 * user-turn mirror `persistence_stage.ts` now writes (canonical
 * `USER_TURN_MODEL_ID`/`USER_TURN_PROVIDER` sentinels) round-trip too?
 *
 * SKIPPED unless PARIPRASHNA_STORE_DB_TEST=1 AND DATABASE_URL is set — needs a
 * live Postgres. Run against a THROWAWAY / local Postgres only (RF-5) —
 * never the shared dev DB. Synthetic chart only (never 482012f1-...).
 *
 * Run locally:
 *   PARIPRASHNA_STORE_DB_TEST=1 DATABASE_URL=postgres://... \
 *     pnpm vitest run src/lib/pariprashna/pipeline/__tests__/reading_parts_persistence.db.test.ts
 */
import { describe, it, expect, beforeAll, afterAll } from 'vitest'
import { randomUUID } from 'node:crypto'
import type { ToolBundle } from '@/lib/retrieval/shared_types'

const ENABLED = process.env.PARIPRASHNA_STORE_DB_TEST === '1' && !!process.env.DATABASE_URL

const SYNTHETIC_CHART_ID = '1c826d5a-41cb-4450-b4dc-59d440e5f75a'
const CONVERSATION_ID = randomUUID()
const PROFILE_ID = `p3c-db-test-${randomUUID()}`

const THINKING_BLOCK = { id: 'blk-think-1', role: 'thinking' as const, text: 'weigh Moon dignity before answering' }
const PROSE_BLOCK = { id: 'blk-prose-1', role: 'prose' as const, text: 'Your Moon sits in Purva Bhadrapada.' }
const TOOL_BUNDLE = {
  tool_bundle_id: 'tb-p3c-1',
  tool_name: 'ganita_nakshatra_get',
  tool_version: '1.0',
  invocation_params: { chart_id: SYNTHETIC_CHART_ID, planet: 'Moon' },
  results: [{ content: 'Purva Bhadrapada' }],
  served_from_cache: false,
  latency_ms: 12,
  result_hash: 'sha256:p3c-db-test',
  schema_version: '1.0',
} as unknown as ToolBundle

describe.skipIf(!ENABLED)('P3-C pipeline persistence — DB round-trip', () => {
  let writeTurn: typeof import('../../store/writer').writeTurn
  let readTurnParts: typeof import('../../store/reader').readTurnParts
  let readCanonicalMessage: typeof import('../../store/reader').readCanonicalMessage
  let query: typeof import('@/lib/db/client').query
  let buildCanonicalParts: typeof import('../reading_parts').buildCanonicalParts
  let checkPartKindCoverage: typeof import('../reading_parts').checkPartKindCoverage
  let USER_TURN_MODEL_ID: string
  let USER_TURN_PROVIDER: string
  let CANONICAL_SCHEMA_VERSION: number

  const fullMessageId = randomUUID()
  const userMessageId = randomUUID()
  const brokenMessageId = randomUUID()

  beforeAll(async () => {
    ;({ query } = await import('@/lib/db/client'))
    ;({ writeTurn } = await import('../../store/writer'))
    ;({ readTurnParts, readCanonicalMessage } = await import('../../store/reader'))
    ;({ buildCanonicalParts, checkPartKindCoverage } = await import('../reading_parts'))
    ;({ USER_TURN_MODEL_ID, USER_TURN_PROVIDER, CANONICAL_SCHEMA_VERSION } = await import('../../store/schema'))

    await query(
      `INSERT INTO profiles (id, role, name, status) VALUES ($1, 'guest', 'P3-C DB test', 'active')
       ON CONFLICT (id) DO NOTHING`,
      [PROFILE_ID],
    )
    await query(
      `INSERT INTO charts (id, chart_id, name, birth_date, birth_time, birth_place, role)
       VALUES ($1, $1, 'P3-C DB test fixture', '1990-01-01', '00:00:00', 'Synthetic', 'fixture')
       ON CONFLICT (id) DO NOTHING`,
      [SYNTHETIC_CHART_ID],
    )
    await query(
      `INSERT INTO conversations (id, chart_id, user_id, module) VALUES ($1, $2, $3, 'consume')
       ON CONFLICT (id) DO NOTHING`,
      [CONVERSATION_ID, SYNTHETIC_CHART_ID, PROFILE_ID],
    )
  })

  afterAll(async () => {
    if (!ENABLED) return
    for (const id of [fullMessageId, userMessageId, brokenMessageId]) {
      await query('DELETE FROM message_parts WHERE message_id = $1', [id])
      await query('DELETE FROM conversation_messages WHERE id = $1', [id])
    }
    await query('DELETE FROM conversations WHERE id = $1', [CONVERSATION_ID])
  })

  it('a real turn (thinking + prose + tool dispatch) persists tool_call/tool_result/reasoning/text and reads back', async () => {
    const built = buildCanonicalParts({
      committedBlocks: [THINKING_BLOCK, PROSE_BLOCK],
      accumulatedText: PROSE_BLOCK.text,
      snippets: new Map(),
      validToolResults: [TOOL_BUNDLE],
    })
    expect(built.parts.map((p) => p.kind)).toEqual(['tool_call', 'tool_result', 'reasoning', 'text'])

    await writeTurn(
      {
        id: fullMessageId,
        conversation_id: CONVERSATION_ID,
        role: 'assistant',
        schema_version: CANONICAL_SCHEMA_VERSION,
        model_id: 'p3c-db-test-model',
        provider: 'anthropic',
      },
      built.parts,
    )

    const parts = await readTurnParts(fullMessageId)
    expect(parts.map((p) => p.kind)).toEqual(['tool_call', 'tool_result', 'reasoning', 'text'])
    expect(parts.find((p) => p.kind === 'tool_call')?.body).toMatchObject({ call_id: 'tb-p3c-1' })
    expect(parts.find((p) => p.kind === 'reasoning')?.body).toMatchObject({
      text: 'weigh Moon dignity before answering',
    })

    const coverage = checkPartKindCoverage(parts, ['tool_call', 'tool_result', 'text', 'reasoning'])
    expect(coverage.ok).toBe(true)
  })

  it('the additive user-turn mirror (USER_TURN_MODEL_ID/PROVIDER sentinels) persists and reads back', async () => {
    await writeTurn(
      {
        id: userMessageId,
        conversation_id: CONVERSATION_ID,
        role: 'user',
        schema_version: CANONICAL_SCHEMA_VERSION,
        model_id: USER_TURN_MODEL_ID,
        provider: USER_TURN_PROVIDER,
      },
      [{ seq: 0, kind: 'text', body: { text: 'Where does my Moon sit?' }, model_visible: true }],
    )

    const msg = await readCanonicalMessage(userMessageId)
    expect(msg?.role).toBe('user')
    expect(msg?.model_id).toBe(USER_TURN_MODEL_ID)
    expect(msg?.provider).toBe(USER_TURN_PROVIDER)

    const parts = await readTurnParts(userMessageId)
    expect(parts.map((p) => p.kind)).toEqual(['text'])
    expect(parts[0].body).toEqual({ text: 'Where does my Moon sit?' })
  })

  it('§N.8 can-fail: withholding the thinking block leaves reasoning missing in the DB read-back while tool_call/tool_result/text still persist', async () => {
    const broken = buildCanonicalParts({
      committedBlocks: [PROSE_BLOCK], // thinking block withheld — simulates a reasoning-persistence regression
      accumulatedText: PROSE_BLOCK.text,
      snippets: new Map(),
      validToolResults: [TOOL_BUNDLE],
    })
    await writeTurn(
      {
        id: brokenMessageId,
        conversation_id: CONVERSATION_ID,
        role: 'assistant',
        schema_version: CANONICAL_SCHEMA_VERSION,
        model_id: 'p3c-db-test-model',
        provider: 'anthropic',
      },
      broken.parts,
    )

    const parts = await readTurnParts(brokenMessageId)
    const coverage = checkPartKindCoverage(parts, ['tool_call', 'tool_result', 'text', 'reasoning'])
    expect(coverage.ok).toBe(false)
    expect(coverage.missing).toEqual(['reasoning'])
    expect(parts.some((p) => p.kind === 'tool_call')).toBe(true)
    expect(parts.some((p) => p.kind === 'tool_result')).toBe(true)
    expect(parts.some((p) => p.kind === 'text')).toBe(true)
    expect(parts.some((p) => p.kind === 'reasoning')).toBe(false)
  })
})
