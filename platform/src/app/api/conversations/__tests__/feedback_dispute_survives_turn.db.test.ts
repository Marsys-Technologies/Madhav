/**
 * QUARANTINED §N.8 REGRESSION — P4-H (Paripraśna P4 overnight, FILLER lane "Dispute
 * capture + feedback endpoint restored"), filed at PARK per the NATIVE-SURROGATE ruling
 * on PR #1496.
 *
 * PR #1496 restored `POST /api/conversations/[id]/feedback` to actually write a
 * reader's dispute into `conversation_messages.metadata_json.feedback` (see
 * `../[id]/feedback/route.ts` and the sibling `feedback.db.test.ts`, which proves that
 * leg genuinely lands and reads back). An independent refuter then found, against a
 * real throwaway Postgres, that the write does NOT survive: the very next ordinary turn
 * silently erases it. Root cause (filed as a DD-register finding, not a P4-H defect —
 * this lane discovered it, it does not own it):
 *
 *   `writeConversationMessages` (`src/lib/persistence/conversation_writer.ts`, lines
 *   63-74) re-upserts EVERY message in the conversation on EVERY turn via
 *   `ON CONFLICT (id) DO UPDATE SET ... metadata_json = EXCLUDED.metadata_json`, with
 *   `const metadata = isLastAssistant ? lastAssistantMetadata : {}` — i.e. every row
 *   that is not THIS turn's last assistant message gets its `metadata_json` REPLACED
 *   with `{}`. This is not hypothetical: `src/lib/pariprashna/pipeline/
 *   persistence_stage.ts` line 362 calls exactly this function, with exactly this
 *   shape, on every ordinary Paripraśna turn —
 *
 *       const historyResult = await writeConversationMessages({
 *         conversationId,
 *         messages: historyMsgs,
 *       })
 *
 *   — no `lastAssistantMetadata` argument at all, so EVERY row in `historyMsgs` (the
 *   full prior history, dispute-bearing rows included) is wiped to `{}` on this call,
 *   every turn. `src/app/api/chat/consult/route.ts` calls the same function directly
 *   for the Consult module's turn loop.
 *
 * This test reproduces that exact call shape — dispute via the restored route, then
 * ONE ordinary follow-up turn through the REAL, unmodified `writeConversationMessages`
 * — and asserts the dispute is still there. It correctly FAILS today: the fix
 * (preserving out-of-band `metadata_json` sub-keys, e.g.
 * `metadata_json = conversation_messages.metadata_json || EXCLUDED.metadata_json`)
 * touches `conversation_writer.ts` / `pariprashna/store/writer.ts`, both explicitly
 * off-limits to this lane (core turn-write path of the live product, unattended,
 * 04:00 — see the PARK ruling on PR #1496). §N.8: this is the detector filed BEFORE
 * the fix, not after — it already demonstrates it can call the claim false.
 *
 * QUARANTINE: the one test below is `it.skip(...)`, independent of and in addition to
 * this file's own DB-gating (`CONV_FEEDBACK_DB_TEST=1` + `CONV_FEEDBACK_DATABASE_URL`,
 * absent in CI today per the sibling suite's own note — so this file does not run in CI
 * either way). The explicit `it.skip` is the durable quarantine: it survives even a
 * future session wiring this whole file into a live-DB CI job, so this ONE test stays
 * inert until the reason named in its title is actually resolved — DO NOT REMOVE THE
 * `.skip` WITHOUT FIXING THE TWO TURN WRITERS FIRST. Un-skip locally against a scratch
 * Postgres to re-observe red; the PR/DD record for this lane carries a verbatim capture
 * of that run.
 *
 * Run locally against the scratch Postgres used to produce this lane's evidence:
 *   CONV_FEEDBACK_DB_TEST=1 CONV_FEEDBACK_DATABASE_URL=postgres://postgres@127.0.0.1:15599/p4h_scratch \
 *     npx vitest run src/app/api/conversations/__tests__/feedback_dispute_survives_turn.db.test.ts
 * (temporarily change `it.skip` to `it` to actually execute the body).
 */

const DB_URL = process.env.CONV_FEEDBACK_DATABASE_URL
const ENABLED = process.env.CONV_FEEDBACK_DB_TEST === '1' && !!DB_URL
if (DB_URL) process.env.DATABASE_URL = DB_URL

import { afterAll, beforeAll, describe, expect, it, vi } from 'vitest'
import { randomUUID } from 'node:crypto'
import { query } from '@/lib/db/client'

// Only mocked boundaries: identity (not under test) and the non-blocking embedding
// side-effect (irrelevant to the metadata-erasure claim, and this scratch schema does
// not carry `conversation_message_embeddings`).
let currentUser: { uid: string } | null = null
vi.mock('@/lib/firebase/server', () => ({
  getServerUser: async () => currentUser,
}))
vi.mock('@/lib/embeddings/embedConversationMessage', () => ({
  embedConversationMessage: vi.fn(async () => undefined),
}))

const run = ENABLED ? describe : describe.skip

// Synthetic chart per the overnight run's hard-never (X-1): probes use the SYNTHETIC
// chart ONLY, never the native's real chart 482012f1-....
const SYNTHETIC_CHART = '1c826d5a-41cb-4450-b4dc-59d440e5f75a'

const OWNER_UID = 'p4h-regress-owner'
const CONVERSATION_ID = randomUUID()
const DISPUTED_MESSAGE_ID = randomUUID()

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
  await query('DELETE FROM conversation_messages WHERE conversation_id = $1', [CONVERSATION_ID])
  await query('DELETE FROM conversations WHERE id = $1', [CONVERSATION_ID])
  await query('DELETE FROM profiles WHERE id = $1', [OWNER_UID])
}

run('P4-H QUARANTINED — dispute survival across an ordinary follow-up turn (real Postgres)', () => {
  beforeAll(async () => {
    await ensureSchema()
    await cleanup()
    await query('INSERT INTO profiles (id, role) VALUES ($1,$2)', [OWNER_UID, 'guest'])
    await query(
      `INSERT INTO conversations (id, chart_id, user_id, module, title)
       VALUES ($1,$2,$3,'pariprashna','Synthetic chart reading')`,
      [CONVERSATION_ID, SYNTHETIC_CHART, OWNER_UID],
    )
    await query(
      `INSERT INTO conversation_messages (id, conversation_id, role, parts_json)
       VALUES ($1,$2,'assistant', $3::jsonb)`,
      [
        DISPUTED_MESSAGE_ID,
        CONVERSATION_ID,
        JSON.stringify([
          { type: 'text', text: 'Saturn dasha correlates with the 2019 job change you described as a promotion.' },
        ]),
      ],
    )
  })

  afterAll(async () => {
    await cleanup()
  })

  // §N.8 quarantine: this is a REAL, executable detector — not disabled by the file's
  // own DB gating alone, but by this explicit `.skip`, so it stays inert regardless of
  // how this suite is wired into CI in the future, until the named fix lands.
  //
  // WAITING ON: `conversation_writer.ts` (line ~74) and `pariprashna/store/writer.ts`
  // (line ~77) preserving out-of-band `metadata_json` sub-keys on upsert instead of
  // replacing the column wholesale — e.g.
  // `metadata_json = conversation_messages.metadata_json || EXCLUDED.metadata_json`.
  // Both files are off-limits to P4-H (PARK ruling, PR #1496) — a future lane owns this
  // fix. Un-skip locally against a throwaway Postgres to re-observe red before
  // attempting the fix; re-skip is NOT optional until the fix is verified in place.
  it.skip(
    'a dispute recorded via the restored feedback endpoint is ERASED by the very next ' +
      'ordinary turn through the real writeConversationMessages() — WAITING ON: out-of-band ' +
      'metadata_json preservation in conversation_writer.ts / pariprashna/store/writer.ts ' +
      '(off-limits to P4-H per the PARK ruling on PR #1496; a future lane owns the fix)',
    async () => {
      const { writeConversationMessages } = await import('@/lib/persistence/conversation_writer')
      const { POST: postFeedback } = await import('../[id]/feedback/route')

      currentUser = { uid: OWNER_UID }

      // 1. The reader disputes the reading via the restored endpoint.
      const disputeResponse = await postFeedback(
        makePostRequest({
          messageId: DISPUTED_MESSAGE_ID,
          rating: -1,
          comment: 'This was a layoff, not a promotion — the reading has the valence backwards.',
        }),
        makeCtx(CONVERSATION_ID),
      )
      expect(disputeResponse.status).toBe(200)

      // Sanity leg (this much genuinely works — see feedback.db.test.ts for the full
      // proof): the dispute is really in the DB right after the POST.
      const afterDispute = await query<{ metadata_json: { feedback?: { rating: number } } }>(
        'SELECT metadata_json FROM conversation_messages WHERE id=$1',
        [DISPUTED_MESSAGE_ID],
      )
      expect(afterDispute.rows[0].metadata_json.feedback).toMatchObject({ rating: -1 })

      // 2. ONE ordinary follow-up turn — reproducing `persistence_stage.ts` line 362's
      // exact call shape: the full prior history (the disputed row included) is
      // re-persisted via the REAL, unmodified `writeConversationMessages`, with no
      // `lastAssistantMetadata` argument (exactly as that production call site does for
      // its "history rows" pass).
      const newUserMessageId = randomUUID()
      await writeConversationMessages({
        conversationId: CONVERSATION_ID,
        messages: [
          {
            id: DISPUTED_MESSAGE_ID,
            role: 'assistant',
            parts: [
              { type: 'text', text: 'Saturn dasha correlates with the 2019 job change you described as a promotion.' },
            ],
          },
          {
            id: newUserMessageId,
            role: 'user',
            parts: [{ type: 'text', text: 'What about my career outlook for next year?' }],
          },
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
        ] as any,
      })

      // 3. THE CLAIM: the dispute survives an ordinary turn. It does not — the row's
      // `metadata_json` is now `{}`. This assertion is expected to FAIL today.
      const afterNextTurn = await query<{ metadata_json: { feedback?: { rating: number } } }>(
        'SELECT metadata_json FROM conversation_messages WHERE id=$1',
        [DISPUTED_MESSAGE_ID],
      )
      expect(afterNextTurn.rows[0].metadata_json.feedback).toMatchObject({ rating: -1 })
    },
  )
})
