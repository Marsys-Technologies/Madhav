/**
 * β2 — conversation_writer unit tests.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

// ── Hoisted mocks ──────────────────────────────────────────────────────────

const { queryMock } = vi.hoisted(() => {
  const queryMock = vi.fn()
  return { queryMock }
})

vi.mock('@/lib/db/client', () => ({ query: queryMock }))
vi.mock('server-only', () => ({}))

import {
  writeConversationMessages,
  loadConversationMessagesV2,
  archiveConversation,
} from '../../../src/lib/persistence/conversation_writer'
import type { UIMessage } from 'ai'

// ── Helpers ───────────────────────────────────────────────────────────────

function makeMsg(overrides: Partial<UIMessage> = {}): UIMessage {
  return {
    id: crypto.randomUUID(),
    role: 'user',
    parts: [{ type: 'text', text: 'hello' }],
    ...overrides,
  } as UIMessage
}

// Convenience: set up mock responses for a sequence of query calls.
function setupQuerySequence(...responses: Array<{ rows: unknown[] }>) {
  for (const r of responses) {
    queryMock.mockResolvedValueOnce(r)
  }
}

// ── Tests ─────────────────────────────────────────────────────────────────

describe('writeConversationMessages', () => {
  beforeEach(() => {
    queryMock.mockReset()
  })

  it('returns empty result for empty messages array', async () => {
    const result = await writeConversationMessages({
      conversationId: 'conv-1',
      messages: [],
    })
    expect(result.messageIds).toHaveLength(0)
    expect(result.verified).toBe(true)
    expect(queryMock).not.toHaveBeenCalled()
  })

  it('inserts each message and returns their IDs', async () => {
    // msg-1 insert, msg-2 insert, then the ID-SCOPED read-back (F-24): the read-back is
    // no longer an unfiltered `COUNT(*)` returning `{ n }` — it selects the written ids
    // back and returns `{ id }` rows. See conversation_writer.ts's F-24 note.
    setupQuerySequence(
      { rows: [{ id: 'msg-1' }] },
      { rows: [{ id: 'msg-2' }] },
      { rows: [{ id: 'msg-1' }, { id: 'msg-2' }] },
    )

    const msgs = [
      makeMsg({ id: 'msg-1', role: 'user' }),
      makeMsg({ id: 'msg-2', role: 'assistant' }),
    ]
    const result = await writeConversationMessages({
      conversationId: 'conv-2',
      messages: msgs,
    })

    expect(result.messageIds).toEqual(['msg-1', 'msg-2'])
    expect(result.verified).toBe(true)
  })

  it('marks verified=false, naming the id, when a written row does not read back (F-24)', async () => {
    setupQuerySequence(
      { rows: [{ id: 'msg-a' }] },
      { rows: [] }, // id-scoped read-back finds nothing
    )
    const msgs = [makeMsg({ id: 'msg-a', role: 'user' })]
    const result = await writeConversationMessages({
      conversationId: 'conv-empty',
      messages: msgs,
    })
    expect(result.messageIds).toEqual(['msg-a'])
    expect(result.verified).toBe(false)
    expect(result.missingMessageIds).toEqual(['msg-a'])
  })

  it('stores parts_json correctly', async () => {
    setupQuerySequence({ rows: [{ id: 'msg-p' }] }, { rows: [{ id: 'msg-p' }] })

    const parts = [{ type: 'text' as const, text: 'test content' }]
    const msg = makeMsg({ id: 'msg-p', role: 'user', parts })

    await writeConversationMessages({
      conversationId: 'conv-parts',
      messages: [msg],
    })

    const insertCall = queryMock.mock.calls.find((c) =>
      String(c[0]).includes('INSERT INTO conversation_messages'),
    )
    expect(insertCall).toBeTruthy()
    const args = insertCall![1] as unknown[]
    expect(JSON.parse(args[3] as string)).toEqual(parts)
  })

  it('attaches lastAssistantMetadata to the last assistant message only', async () => {
    setupQuerySequence(
      { rows: [{ id: 'msg-u' }] },
      { rows: [{ id: 'msg-a' }] },
      { rows: [{ id: 'msg-u' }, { id: 'msg-a' }] },
    )

    const msgs = [
      makeMsg({ id: 'msg-u', role: 'user' }),
      makeMsg({ id: 'msg-a', role: 'assistant' }),
    ]
    const meta = { model: 'claude-sonnet-4-6', input_tokens: 1000 }

    await writeConversationMessages({
      conversationId: 'conv-meta',
      messages: msgs,
      lastAssistantMetadata: meta,
    })

    const insertCalls = queryMock.mock.calls.filter((c) =>
      String(c[0]).includes('INSERT INTO conversation_messages'),
    )
    // User message has empty metadata.
    expect(JSON.parse((insertCalls[0]![1] as unknown[])[4] as string)).toEqual({})
    // Assistant message has the provided metadata.
    expect(JSON.parse((insertCalls[1]![1] as unknown[])[4] as string)).toEqual(meta)
  })

  it('uses ON CONFLICT clause for idempotency', async () => {
    setupQuerySequence({ rows: [{ id: 'msg-x' }] }, { rows: [{ id: 'msg-x' }] })

    const msg = makeMsg({ id: 'msg-x' })
    await writeConversationMessages({ conversationId: 'conv-idem', messages: [msg] })

    const insertSql = queryMock.mock.calls.find((c) =>
      String(c[0]).includes('INSERT INTO conversation_messages'),
    )?.[0] as string | undefined
    expect(insertSql).toContain('ON CONFLICT')
  })
})

describe('loadConversationMessagesV2', () => {
  beforeEach(() => queryMock.mockReset())

  it('returns empty array when no rows', async () => {
    queryMock.mockResolvedValueOnce({ rows: [] })
    const msgs = await loadConversationMessagesV2('conv-none')
    expect(msgs).toEqual([])
  })

  it('maps db rows to UIMessage shape', async () => {
    const dbRow = {
      id: 'row-1',
      role: 'assistant',
      parts_json: [{ type: 'text', text: 'Hello' }],
      metadata_json: { model: 'claude' },
      created_at: '2026-05-16T00:00:00Z',
    }
    queryMock.mockResolvedValueOnce({ rows: [dbRow] })

    const msgs = await loadConversationMessagesV2('conv-restore')
    expect(msgs).toHaveLength(1)
    expect(msgs[0]).toMatchObject({
      id: 'row-1',
      role: 'assistant',
      parts: [{ type: 'text', text: 'Hello' }],
    })
  })

  it('handles null parts_json gracefully', async () => {
    const dbRow = {
      id: 'row-bad',
      role: 'user',
      parts_json: null,
      metadata_json: {},
      created_at: '2026-05-16T00:00:00Z',
    }
    queryMock.mockResolvedValueOnce({ rows: [dbRow] })

    const msgs = await loadConversationMessagesV2('conv-bad')
    expect(msgs[0]!.parts).toEqual([])
  })
})

describe('archiveConversation', () => {
  beforeEach(() => queryMock.mockReset())

  it('issues UPDATE with archived_at', async () => {
    queryMock.mockResolvedValueOnce({ rows: [] })
    await archiveConversation('conv-arch')

    expect(queryMock).toHaveBeenCalledOnce()
    const [sql, params] = queryMock.mock.calls[0]!
    expect(String(sql)).toContain('UPDATE conversations SET archived_at')
    expect(params).toContain('conv-arch')
  })
})
