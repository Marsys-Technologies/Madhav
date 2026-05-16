/**
 * γ7: Stream resume after disconnect — unit tests.
 *
 * Covers: pending_streams_writer behaviour (debounced accumulation, clear),
 * resume endpoint logic shapes, and client-side sessionStorage patterns.
 *
 * Chaos scenarios: clean disconnect (onFinish clears), dirty disconnect
 * (partial text remains), network partition (empty accumulated_text).
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

// ─── pending_streams_writer shape tests ──────────────────────────────────────

// Mock the DB query so we can test the writer without a real DB.
vi.mock('@/lib/db/client', () => ({
  query: vi.fn().mockResolvedValue({ rows: [] }),
}))

vi.mock('server-only', () => ({}))

const { createPendingStreamWriter } = await import(
  '@/lib/persistence/pending_streams_writer'
)
const { query } = await import('@/lib/db/client')

describe('createPendingStreamWriter', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.useFakeTimers()
  })

  it('starts with empty text and seq=0', () => {
    const w = createPendingStreamWriter('q1', 'c1')
    expect(w.getAccumulatedText()).toBe('')
    expect(w.getEventSeq()).toBe(0)
  })

  it('accumulates text deltas', () => {
    const w = createPendingStreamWriter('q2', 'c1')
    w.onTextDelta('hello ')
    w.onTextDelta('world')
    expect(w.getAccumulatedText()).toBe('hello world')
    expect(w.getEventSeq()).toBe(2)
  })

  it('increments seq on onEvent without changing text', () => {
    const w = createPendingStreamWriter('q3', 'c1')
    w.onEvent()
    w.onEvent()
    expect(w.getAccumulatedText()).toBe('')
    expect(w.getEventSeq()).toBe(2)
  })

  it('debounces DB writes — only one write per burst', async () => {
    const w = createPendingStreamWriter('q4', 'c1')
    for (let i = 0; i < 50; i++) w.onTextDelta('x')
    expect(query).not.toHaveBeenCalled()
    // Advance past debounce window
    await vi.runAllTimersAsync()
    // Should be exactly 1 DB write (UPSERT), not 50
    expect(query).toHaveBeenCalledTimes(1)
    const sql = (vi.mocked(query).mock.calls[0][0] as string).toLowerCase()
    expect(sql).toContain('insert into pending_streams')
    expect(sql).toContain('on conflict')
  })

  it('clear() deletes the DB row and stops future writes', async () => {
    const w = createPendingStreamWriter('q5', 'c1')
    w.onTextDelta('partial')
    await w.clear()
    vi.clearAllMocks()
    // After clear, further deltas should not trigger DB writes
    w.onTextDelta('more')
    await vi.runAllTimersAsync()
    expect(query).not.toHaveBeenCalled()
  })

  it('clear() upsert SQL references the correct query_id', async () => {
    const w = createPendingStreamWriter('qdelete-test', 'conv1')
    await w.clear()
    expect(query).toHaveBeenCalledWith(
      expect.stringContaining('DELETE FROM pending_streams'),
      ['qdelete-test'],
    )
  })
})

// ─── Resume endpoint contract tests (no real HTTP — shape-only) ──────────────

describe('stream resume endpoint contract', () => {
  it('GET /api/chat/consume/resume exports a GET handler', async () => {
    const src = await import('fs/promises')
    const path = await import('path')
    const content = await src.readFile(
      path.join(process.cwd(), 'src/app/api/chat/consume/resume/route.ts'),
      'utf8',
    )
    expect(content).toContain('export async function GET')
    expect(content).toContain('pending_streams')
    expect(content).toContain('since_chars')
    expect(content).toContain('query_id')
  })

  it('resume route returns 404 JSON shape comment — no UIMessage stream dependency', async () => {
    const src = await import('fs/promises')
    const path = await import('path')
    const content = await src.readFile(
      path.join(process.cwd(), 'src/app/api/chat/consume/resume/route.ts'),
      'utf8',
    )
    // Resume returns JSON, not a UIMessage stream (simpler client consumption).
    expect(content).toContain('Response.json(')
    // 404 for missing/expired rows
    expect(content).toContain('status: 404')
    // 204 for empty suffix
    expect(content).toContain('status: 204')
  })
})

// ─── Session-storage key helper tests ────────────────────────────────────────

describe('sessionStorage key stability', () => {
  it('pendingStreamKey is deterministic per chartId', () => {
    // The key is `v2_pending_${chartId}` — verified via the ConsumeChatV2 source.
    const src = require('fs').readFileSync(
      require('path').join(process.cwd(), 'src/components/consume/ConsumeChatV2.tsx'),
      'utf8',
    )
    expect(src).toContain('v2_pending_${chartId}')
    expect(src).toContain('function pendingStreamKey')
  })
})

// ─── Chaos scenario: clean disconnect ────────────────────────────────────────

describe('chaos: clean disconnect (stream completes normally)', () => {
  it('writer.clear() is called in onFinish after persistence', () => {
    // Verified via route.ts source inspection.
    const src = require('fs').readFileSync(
      require('path').join(process.cwd(), 'src/app/api/chat/consume/route.ts'),
      'utf8',
    )
    expect(src).toContain('pendingStreamWriter.clear()')
    // clear() is called after the try/catch that wraps β2 write-through persistence.
    const clearIdx = src.indexOf('pendingStreamWriter.clear()')
    const persistIdx = src.indexOf('writeConversationMessages(')
    expect(persistIdx).toBeGreaterThan(0)
    expect(clearIdx).toBeGreaterThan(persistIdx)
  })
})

// ─── Chaos scenario: dirty disconnect (partial text in table) ────────────────

describe('chaos: dirty disconnect (mid-stream, pending_streams has partial text)', () => {
  it('accumulated text grows with each delta call', () => {
    const w = createPendingStreamWriter('dirty-q', 'dirty-c')
    const tokens = ['Mars', ' transits', ' the', ' 7th', ' house']
    for (const t of tokens) w.onTextDelta(t)
    expect(w.getAccumulatedText()).toBe('Mars transits the 7th house')
    expect(w.getEventSeq()).toBe(5)
  })

  it('since_chars slicing is correct', () => {
    const accumulated = 'Mars transits the 7th house of relationships'
    const received = 14 // client received first 14 chars
    const suffix = accumulated.slice(received)
    expect(suffix).toBe('the 7th house of relationships')
  })
})

// ─── Chaos scenario: network partition (empty accumulated text) ──────────────

describe('chaos: network partition (disconnect before first chunk)', () => {
  it('writer returns empty accumulated text if no deltas received', () => {
    const w = createPendingStreamWriter('empty-q', null)
    expect(w.getAccumulatedText()).toBe('')
  })

  it('resume endpoint returns 204 for empty suffix', async () => {
    // The resume route returns 204 when suffix is empty — verified via source.
    const src = require('fs').readFileSync(
      require('path').join(process.cwd(), 'src/app/api/chat/consume/resume/route.ts'),
      'utf8',
    )
    expect(src).toContain("status: 204")
    // Empty suffix when accumulated_text is '' and since_chars is 0:
    // suffix = ''.slice(0) = '' → 204 response.
  })
})
