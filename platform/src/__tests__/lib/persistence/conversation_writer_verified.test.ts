/**
 * conversation_writer_verified.test.ts — SAMĀPTI · lane B-N8-TS-SERVE · finding F-24.
 *
 * F-24 (A7-N8-AUDIT register §2.3): `writeConversationMessages`'s read-after-write
 * `verified` flag was
 *
 *     const verified = dbCount >= messageIds.length
 *
 * where `dbCount` came from an UNFILTERED `SELECT COUNT(*) FROM conversation_messages
 * WHERE conversation_id = $1`. That count includes every message from every prior turn of
 * the conversation, so from turn 2 onward the inequality held regardless of what happened
 * to this turn's rows. The check was a tautology: it could not detect a failed write, which
 * is the only thing it existed to detect. (The `>=` loosening was itself introduced to stop
 * the polluted count from tripping the comparison — the code comment conceded as much.)
 *
 * The tests below pin the repaired behaviour and, crucially, DEMONSTRATE THE OLD MISS: the
 * "prior-turn pollution" case constructs exactly the state in which the old predicate
 * returned `true` while a row this call claimed to write was absent.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

const queryMock = vi.fn()
vi.mock('@/lib/db/client', () => ({ query: (...args: unknown[]) => queryMock(...args) }))
vi.mock('@/lib/embeddings/embedConversationMessage', () => ({
  embedConversationMessage: vi.fn(async () => undefined),
}))

import { writeConversationMessages } from '@/lib/persistence/conversation_writer'
import type { UIMessage } from 'ai'

const CONV = '11111111-1111-4111-8111-111111111111'
const ID_A = 'aaaaaaaa-0000-4000-8000-000000000001'
const ID_B = 'bbbbbbbb-0000-4000-8000-000000000002'

function msg(id: string, role: 'user' | 'assistant', text: string): UIMessage {
  return { id, role, parts: [{ type: 'text', text }] } as unknown as UIMessage
}

/**
 * Drives the mocked `query`: every INSERT ... RETURNING id echoes its own id back (the
 * write "succeeded" from the writer's point of view), and the read-back SELECT returns
 * only the ids listed in `readableIds` — the durable ones.
 *
 * `priorTurnRowCount` models rows already in the conversation from earlier turns. It is
 * what the OLD unfiltered `COUNT(*)` would have counted, and is tracked here so each test
 * can state, in code, what the old predicate would have concluded.
 */
function install({ readableIds }: { readableIds: string[] }) {
  queryMock.mockReset()
  queryMock.mockImplementation(async (sql: string, params: unknown[]) => {
    if (/INSERT INTO conversation_messages/i.test(sql)) {
      return { rows: [{ id: params[0] as string }] }
    }
    if (/SELECT id FROM conversation_messages/i.test(sql)) {
      const asked = params[1] as string[]
      return { rows: asked.filter(id => readableIds.includes(id)).map(id => ({ id })) }
    }
    throw new Error(`unexpected SQL in test: ${sql}`)
  })
}

describe('F-24 · writeConversationMessages read-after-write is id-scoped, not a tautology', () => {
  beforeEach(() => {
    queryMock.mockReset()
    vi.spyOn(console, 'error').mockImplementation(() => undefined)
  })

  it('verified:true with no missing ids when every written row reads back', async () => {
    install({ readableIds: [ID_A, ID_B] })
    const r = await writeConversationMessages({
      conversationId: CONV,
      messages: [msg(ID_A, 'user', 'q'), msg(ID_B, 'assistant', 'a')],
    })
    expect(r.messageIds).toEqual([ID_A, ID_B])
    expect(r.verified).toBe(true)
    expect(r.missingMessageIds).toEqual([])
  })

  it('verified:false and NAMES the missing id when a written row is not durable', async () => {
    // The assistant row did not persist.
    install({ readableIds: [ID_A] })
    const r = await writeConversationMessages({
      conversationId: CONV,
      messages: [msg(ID_A, 'user', 'q'), msg(ID_B, 'assistant', 'a')],
    })
    expect(r.verified).toBe(false)
    expect(r.missingMessageIds).toEqual([ID_B])
  })

  it('THE OLD MISS: prior-turn rows can no longer mask a lost write (F-24)', async () => {
    // State: this call writes 2 messages; NEITHER reads back. The conversation already
    // holds 40 rows from earlier turns.
    install({ readableIds: [] })
    const priorTurnRowCount = 40
    const r = await writeConversationMessages({
      conversationId: CONV,
      messages: [msg(ID_A, 'user', 'q'), msg(ID_B, 'assistant', 'a')],
    })

    // What the OLD predicate computed on exactly this state: an unfiltered COUNT(*) over
    // the conversation returns the 40 prior rows, and `40 >= 2` is true — so it reported
    // verified:true while BOTH of this turn's messages were lost.
    const oldUnfilteredDbCount = priorTurnRowCount
    const oldVerdict = oldUnfilteredDbCount >= r.messageIds.length
    expect(oldVerdict).toBe(true)

    // The repaired predicate reports the truth.
    expect(r.verified).toBe(false)
    expect(r.missingMessageIds).toEqual([ID_A, ID_B])
  })

  it('scopes the read-back SELECT by BOTH conversation_id and the written ids', async () => {
    install({ readableIds: [ID_A] })
    await writeConversationMessages({ conversationId: CONV, messages: [msg(ID_A, 'user', 'q')] })
    const selectCall = queryMock.mock.calls.find(c => /SELECT id FROM conversation_messages/i.test(c[0] as string))
    expect(selectCall).toBeDefined()
    const sql = selectCall![0] as string
    expect(sql).toMatch(/conversation_id = \$1/)
    expect(sql).toMatch(/id = ANY\(\$2::uuid\[\]\)/)
    // and it must NOT be the old unfiltered COUNT(*)
    expect(sql).not.toMatch(/COUNT\(\*\)/i)
    expect(selectCall![1]).toEqual([CONV, [ID_A]])
  })

  it('empty message list is honestly verified with no ids', async () => {
    install({ readableIds: [] })
    const r = await writeConversationMessages({ conversationId: CONV, messages: [] })
    expect(r).toEqual({ messageIds: [], verified: true, missingMessageIds: [] })
    expect(queryMock).not.toHaveBeenCalled()
  })
})
