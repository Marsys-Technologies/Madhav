/**
 * Reader-safe historical transcript loader (Jātaka chart workspace, Task 8).
 *
 * Only user/assistant text reaches a historical view: canonical message_parts
 * text is preferred, legacy parts_json text is the fallback, and reasoning,
 * tool calls/results, provider payloads and audit metadata never leak.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('server-only', () => ({}))
const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

import { loadHistoricalConversationMessages } from '../historicalReading'

const MESSAGES = [
  {
    id: 'm1', role: 'user', created_at: '2026-09-01T10:00:00Z',
    parts_json: [{ type: 'text', text: 'What about my career?' }],
    metadata_json: { audit: 'secret' },
  },
  {
    id: 'm2', role: 'assistant', created_at: '2026-09-01T10:00:05Z',
    parts_json: [
      { type: 'reasoning', text: 'internal chain of thought' },
      { type: 'tool-call', toolName: 'ganita_positions_get', input: { chart: 'x' } },
      { type: 'text', text: 'LEGACY SHOULD NOT WIN' },
    ],
    metadata_json: {},
  },
  {
    id: 'm3', role: 'assistant', created_at: '2026-09-01T10:01:00Z',
    parts_json: [
      { type: 'text', text: 'Legacy ' },
      { type: 'tool-result', output: { raw: 'provider payload' } },
      { type: 'text', text: 'answer.' },
      { type: 'text', text: 42 },
    ],
    metadata_json: {},
  },
  {
    id: 'm4', role: 'assistant', created_at: '2026-09-01T10:02:00Z',
    parts_json: [{ type: 'reasoning', text: 'only reasoning' }],
    metadata_json: {},
  },
]

const CANONICAL = [
  { message_id: 'm2', seq: 2, text: 'second.' },
  { message_id: 'm2', seq: 1, text: 'Canonical first, ' },
]

beforeEach(() => {
  mockQuery.mockReset()
  mockQuery.mockImplementation(async (sql: string) => {
    if (/FROM conversation_messages/.test(sql)) return { rows: MESSAGES }
    if (/FROM message_parts/.test(sql)) return { rows: CANONICAL }
    return { rows: [] }
  })
})

describe('loadHistoricalConversationMessages', () => {
  it('returns only reader-visible user and assistant text, in order', async () => {
    const out = await loadHistoricalConversationMessages('conv-1')
    expect(out).toEqual([
      { id: 'm1', role: 'user', text: 'What about my career?', createdAt: '2026-09-01T10:00:00Z' },
      { id: 'm2', role: 'assistant', text: 'Canonical first, second.', createdAt: '2026-09-01T10:00:05Z' },
      { id: 'm3', role: 'assistant', text: 'Legacy answer.', createdAt: '2026-09-01T10:01:00Z' },
    ])
  })

  it('prefers canonical text parts over legacy parts_json', async () => {
    const out = await loadHistoricalConversationMessages('conv-1')
    expect(out.find((m) => m.id === 'm2')?.text).not.toMatch(/LEGACY/)
  })

  it('never returns reasoning, tool payloads or audit metadata', async () => {
    const serialized = JSON.stringify(await loadHistoricalConversationMessages('conv-1'))
    expect(serialized).not.toMatch(/chain of thought|ganita_positions_get|provider payload|secret|only reasoning/)
  })

  it('reads only text-kind canonical parts, in seq order, and only user/assistant rows', async () => {
    await loadHistoricalConversationMessages('conv-1')
    const [msgSql, msgParams] = mockQuery.mock.calls.find(([s]) => /FROM conversation_messages/.test(s))!
    expect(msgSql).toMatch(/role IN \('user', 'assistant'\)/)
    expect(msgSql).toMatch(/ORDER BY created_at, CASE role WHEN 'user' THEN 0 ELSE 1 END, id/)
    expect(msgSql).not.toMatch(/metadata_json/)
    expect(msgParams).toEqual(['conv-1'])
    const [partSql] = mockQuery.mock.calls.find(([s]) => /FROM message_parts/.test(s))!
    expect(partSql).toMatch(/kind = 'text'/)
    expect(partSql).toMatch(/ORDER BY message_id, seq/)
  })

  it('skips the parts query when there are no messages', async () => {
    mockQuery.mockImplementation(async () => ({ rows: [] }))
    expect(await loadHistoricalConversationMessages('conv-1')).toEqual([])
    expect(mockQuery.mock.calls.some(([s]) => /FROM message_parts/.test(s))).toBe(false)
  })
})
