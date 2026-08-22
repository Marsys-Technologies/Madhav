/**
 * DB-integration proof for `GET`/`POST /api/conversations/[id]/feedback` — P4-H
 * (Paripraśna P4 overnight, FILLER lane "Dispute capture + feedback endpoint restored").
 *
 * The route at `../[id]/feedback/route.ts` was, until this lane, an unconditional stub:
 * `message_feedback` (the dedicated table) was dropped in WS-0 and the route was left
 * accepting a submission, echoing `{ ok: true }`, and never touching a database. A
 * reader's dispute of a claim the instrument made went nowhere, silently — see the
 * module's own former header comment (git blob at `07ed2433f`, quoted verbatim below as
 * `OLD_STUB_POST`, the §N.8 can-fail baseline this suite demonstrates before proving the
 * fix).
 *
 * Nothing in the fix's assertions is mocked except the one true external I/O boundary
 * (Firebase auth, via `getServerUser`) — the route, `getConversation`'s ownership check,
 * and every SQL statement run against a REAL throwaway Postgres.
 *
 * Gated on CONV_FEEDBACK_DB_TEST=1 + CONV_FEEDBACK_DATABASE_URL (no DB in CI yet for this
 * suite; skipped, not failed, when absent — the standard `.db.test.ts` convention, see
 * `tests/pariprashna/samiksha/capture_turn_commit.db.test.ts`).
 *
 * Run locally against the scratch Postgres used to produce this lane's DD-21 evidence:
 *   CONV_FEEDBACK_DB_TEST=1 CONV_FEEDBACK_DATABASE_URL=postgres://postgres:postgres@127.0.0.1:15599/p4h_scratch \
 *     npx vitest run src/app/api/conversations/__tests__/feedback.db.test.ts
 */

// Point the shared DB client at the throwaway DB BEFORE any query runs (the pool is
// created lazily on first query; this top-level assignment precedes all tests).
const DB_URL = process.env.CONV_FEEDBACK_DATABASE_URL
const ENABLED = process.env.CONV_FEEDBACK_DB_TEST === '1' && !!DB_URL
if (DB_URL) process.env.DATABASE_URL = DB_URL

import { afterAll, beforeAll, describe, expect, it, vi } from 'vitest'
import { randomUUID } from 'node:crypto'
import { query } from '@/lib/db/client'
import { res } from '@/lib/errors'

// The only mocked boundary: identity. Firebase auth is not the thing under test; the
// dispute-capture path (ownership check → DB write → DB read-back) is.
let currentUser: { uid: string } | null = null
vi.mock('@/lib/firebase/server', () => ({
  getServerUser: async () => currentUser,
}))

const run = ENABLED ? describe : describe.skip

// Synthetic chart per the overnight run's hard-never (X-1): probes use the SYNTHETIC
// chart ONLY, never the native's real chart 482012f1-....
const SYNTHETIC_CHART = '1c826d5a-41cb-4450-b4dc-59d440e5f75a'

const OWNER_UID = 'p4h-probe-owner'
const OTHER_UID = 'p4h-probe-other-user'
const CONVERSATION_ID = randomUUID()
const ASSISTANT_MESSAGE_ID = randomUUID()
const FOREIGN_MESSAGE_ID = randomUUID() // exists, but in a DIFFERENT conversation

function makeCtx(id: string) {
  return { params: Promise.resolve({ id }) }
}
function makePostRequest(body: unknown) {
  return new Request('http://localhost/api/conversations/x/feedback', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(body),
  })
}
function makeGetRequest() {
  return new Request('http://localhost/api/conversations/x/feedback')
}

/**
 * Verbatim reproduction of the PRE-FIX route (git blob `07ed2433f`,
 * `platform/src/app/api/conversations/[id]/feedback/route.ts`) — the exact discard this
 * lane closes. §N.8: run this FIRST, against the real DB, to observe the can-fail
 * baseline before the fixed route's first counted pass.
 */
async function OLD_STUB_POST(req: Request): Promise<Response> {
  const user = await (await import('@/lib/firebase/server')).getServerUser()
  if (!user) return res.unauthenticated()
  try {
    const body = (await req.json()) as { rating?: unknown }
    return Response.json({ ok: true, rating: body?.rating ?? null })
  } catch {
    return res.badRequest('invalid body')
  }
}

async function ensureSchema() {
  await query(`CREATE TABLE IF NOT EXISTS profiles (
    id text PRIMARY KEY, role text NOT NULL DEFAULT 'guest')`)
  await query(`CREATE TABLE IF NOT EXISTS conversations (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    chart_id uuid NOT NULL, user_id text NOT NULL, module text NOT NULL DEFAULT 'consume',
    title text, created_at timestamptz DEFAULT now(), updated_at timestamptz,
    archived_at timestamptz)`)
  await query(`CREATE TABLE IF NOT EXISTS conversation_messages (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id uuid NOT NULL, parent_message_id uuid, role text NOT NULL,
    parts_json jsonb DEFAULT '[]'::jsonb NOT NULL,
    metadata_json jsonb DEFAULT '{}'::jsonb NOT NULL,
    created_at timestamptz DEFAULT now() NOT NULL)`)
}

async function cleanup() {
  await query('DELETE FROM conversation_messages WHERE conversation_id = $1 OR id = $2', [
    CONVERSATION_ID,
    FOREIGN_MESSAGE_ID,
  ])
  await query('DELETE FROM conversations WHERE id = $1', [CONVERSATION_ID])
  await query('DELETE FROM profiles WHERE id = ANY($1)', [[OWNER_UID, OTHER_UID]])
}

run('P4-H — conversations/[id]/feedback dispute capture (real Postgres)', () => {
  beforeAll(async () => {
    await ensureSchema()
    await cleanup()
    await query('INSERT INTO profiles (id, role) VALUES ($1,$2),($3,$4)', [
      OWNER_UID,
      'guest',
      OTHER_UID,
      'guest',
    ])
    await query(
      `INSERT INTO conversations (id, chart_id, user_id, module, title)
       VALUES ($1,$2,$3,'consume','Synthetic chart reading')`,
      [CONVERSATION_ID, SYNTHETIC_CHART, OWNER_UID],
    )
    await query(
      `INSERT INTO conversation_messages (id, conversation_id, role, parts_json)
       VALUES ($1,$2,'assistant', $3::jsonb)`,
      [
        ASSISTANT_MESSAGE_ID,
        CONVERSATION_ID,
        JSON.stringify([
          { type: 'text', text: 'Saturn dasha correlates with the 2019 job change you described as a promotion.' },
        ]),
      ],
    )
    // A message that exists in the DB, but NOT in this conversation — used to prove the
    // POST cannot silently "succeed" against a cross-conversation id.
    const foreignConvId = randomUUID()
    await query(
      `INSERT INTO conversations (id, chart_id, user_id, module, title) VALUES ($1,$2,$3,'consume','other')`,
      [foreignConvId, SYNTHETIC_CHART, OWNER_UID],
    )
    await query(
      `INSERT INTO conversation_messages (id, conversation_id, role, parts_json) VALUES ($1,$2,'assistant','[]'::jsonb)`,
      [FOREIGN_MESSAGE_ID, foreignConvId],
    )
  })

  afterAll(async () => {
    await cleanup()
  })

  it('§N.8 can-fail baseline: the OLD stub accepts a dispute and discards it (DB unchanged)', async () => {
    currentUser = { uid: OWNER_UID }
    const before = await query<{ metadata_json: Record<string, unknown> }>(
      'SELECT metadata_json FROM conversation_messages WHERE id=$1',
      [ASSISTANT_MESSAGE_ID],
    )
    expect(before.rows[0].metadata_json).toEqual({})

    const response = await OLD_STUB_POST(
      makePostRequest({
        messageId: ASSISTANT_MESSAGE_ID,
        rating: -1,
        comment: 'This was a layoff, not a promotion — the reading has the valence backwards.',
      }),
    )
    const responseBody = await response.json()
    // The old stub reports success ...
    expect(response.status).toBe(200)
    expect(responseBody).toEqual({ ok: true, rating: -1 })

    // ... but the dispute went nowhere: zero DB writes occurred.
    const after = await query<{ metadata_json: Record<string, unknown> }>(
      'SELECT metadata_json FROM conversation_messages WHERE id=$1',
      [ASSISTANT_MESSAGE_ID],
    )
    expect(after.rows[0].metadata_json).toEqual({})
  })

  it('restored POST persists a dispute durably, and GET reads it back', async () => {
    const { POST, GET } = await import('../[id]/feedback/route')
    currentUser = { uid: OWNER_UID }

    const postResponse = await POST(
      makePostRequest({
        messageId: ASSISTANT_MESSAGE_ID,
        rating: -1,
        comment: 'This was a layoff, not a promotion — the reading has the valence backwards.',
      }),
      makeCtx(CONVERSATION_ID),
    )
    expect(postResponse.status).toBe(200)
    const postBody = await postResponse.json()
    expect(postBody).toEqual({
      ok: true,
      rating: -1,
      comment: 'This was a layoff, not a promotion — the reading has the valence backwards.',
    })

    // Read back from the DB directly (not through the route) — the DD-21 DB-read leg.
    const row = await query<{ metadata_json: { feedback?: { rating: number; comment: string } } }>(
      'SELECT metadata_json FROM conversation_messages WHERE id=$1',
      [ASSISTANT_MESSAGE_ID],
    )
    expect(row.rows[0].metadata_json.feedback).toMatchObject({
      rating: -1,
      comment: 'This was a layoff, not a promotion — the reading has the valence backwards.',
      user_id: OWNER_UID,
    })

    // Read back through the route's own GET.
    const getResponse = await GET(makeGetRequest(), makeCtx(CONVERSATION_ID))
    const getBody = await getResponse.json()
    expect(getBody.feedback).toEqual([
      {
        message_id: ASSISTANT_MESSAGE_ID,
        rating: -1,
        comment: 'This was a layoff, not a promotion — the reading has the valence backwards.',
      },
    ])
  })

  it('residual-silent-failure guard: POST against a message outside this conversation 404s, never a hollow 200', async () => {
    const { POST } = await import('../[id]/feedback/route')
    currentUser = { uid: OWNER_UID }

    const response = await POST(
      makePostRequest({ messageId: FOREIGN_MESSAGE_ID, rating: 1 }),
      makeCtx(CONVERSATION_ID),
    )
    expect(response.status).toBe(404)

    const row = await query<{ metadata_json: Record<string, unknown> }>(
      'SELECT metadata_json FROM conversation_messages WHERE id=$1',
      [FOREIGN_MESSAGE_ID],
    )
    expect(row.rows[0].metadata_json).toEqual({})
  })

  it('ownership guard: a non-owner, non-admin user cannot read or write this conversation\'s feedback', async () => {
    const { POST, GET } = await import('../[id]/feedback/route')
    currentUser = { uid: OTHER_UID }

    const postResponse = await POST(
      makePostRequest({ messageId: ASSISTANT_MESSAGE_ID, rating: 1 }),
      makeCtx(CONVERSATION_ID),
    )
    expect(postResponse.status).toBe(404)

    const getResponse = await GET(makeGetRequest(), makeCtx(CONVERSATION_ID))
    expect(getResponse.status).toBe(404)
  })

  it('validation: rejects a malformed rating instead of silently coercing it', async () => {
    const { POST } = await import('../[id]/feedback/route')
    currentUser = { uid: OWNER_UID }

    const response = await POST(
      makePostRequest({ messageId: ASSISTANT_MESSAGE_ID, rating: 'up' }),
      makeCtx(CONVERSATION_ID),
    )
    expect(response.status).toBe(400)
  })
})
