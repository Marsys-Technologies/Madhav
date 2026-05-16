/**
 * history_compression — β8 unit + integration tests.
 *
 * Unit tests cover pure functions: estimateTokens, splitHistory, makeCacheKey.
 * Integration tests cover compressHistory end-to-end with an injected summarizer.
 */
import { describe, it, expect, vi } from 'vitest'
import {
  estimateTokens,
  splitHistory,
  makeCacheKey,
  compressHistory,
} from '../history_compression'
import type { ModelMessage } from 'ai'

function msg(role: 'user' | 'assistant', content: string): ModelMessage {
  return { role, content }
}

function longMsg(role: 'user' | 'assistant', chars: number): ModelMessage {
  return { role, content: 'x'.repeat(chars) }
}

// ─── Unit: estimateTokens ─────────────────────────────────────────────────────

describe('estimateTokens', () => {
  it('returns 0 for empty messages', () => {
    expect(estimateTokens([])).toBe(0)
  })

  it('estimates string content at ~4 chars per token', () => {
    const messages: ModelMessage[] = [msg('user', 'a'.repeat(400))]
    expect(estimateTokens(messages)).toBe(100)
  })

  it('sums across multiple messages', () => {
    const messages: ModelMessage[] = [
      msg('user', 'a'.repeat(400)),
      msg('assistant', 'b'.repeat(400)),
    ]
    expect(estimateTokens(messages)).toBe(200)
  })

  it('handles messages with content below 4 chars (rounds up)', () => {
    const messages: ModelMessage[] = [msg('user', 'abc')]
    expect(estimateTokens(messages)).toBe(1)
  })

  it('handles large conversations near the 32k budget', () => {
    const messages: ModelMessage[] = Array.from({ length: 20 }, (_, i) =>
      longMsg(i % 2 === 0 ? 'user' : 'assistant', 6_400),
    )
    const estimate = estimateTokens(messages)
    expect(estimate).toBe(32_000)
  })
})

// ─── Unit: splitHistory ───────────────────────────────────────────────────────

describe('splitHistory', () => {
  it('returns no head when messages fit within tailSize*2', () => {
    const messages = [msg('user', 'q1'), msg('assistant', 'a1')]
    const { head, tail } = splitHistory(messages, 4)
    expect(head).toHaveLength(0)
    expect(tail).toHaveLength(2)
  })

  it('splits correctly when there are more messages than tail size', () => {
    const messages = Array.from({ length: 10 }, (_, i) =>
      msg(i % 2 === 0 ? 'user' : 'assistant', `m${i}`),
    )
    const { head, tail } = splitHistory(messages, 2)
    expect(tail).toHaveLength(4)
    expect(head).toHaveLength(6)
  })

  it('head + tail reconstruction equals original order', () => {
    const messages = Array.from({ length: 8 }, (_, i) =>
      msg(i % 2 === 0 ? 'user' : 'assistant', `m${i}`),
    )
    const { head, tail } = splitHistory(messages, 2)
    expect([...head, ...tail]).toEqual(messages)
  })

  it('exact boundary: messages.length === tailSize * 2', () => {
    const messages = Array.from({ length: 8 }, (_, i) =>
      msg(i % 2 === 0 ? 'user' : 'assistant', `m${i}`),
    )
    const { head, tail } = splitHistory(messages, 4)
    expect(head).toHaveLength(0)
    expect(tail).toHaveLength(8)
  })
})

// ─── Unit: makeCacheKey ───────────────────────────────────────────────────────

describe('makeCacheKey', () => {
  it('formats as conversationId:tailStart', () => {
    expect(makeCacheKey('conv-123', 10)).toBe('conv-123:10')
  })

  it('different tail positions produce different keys', () => {
    const k1 = makeCacheKey('conv-abc', 8)
    const k2 = makeCacheKey('conv-abc', 10)
    expect(k1).not.toBe(k2)
  })

  it('different conversation IDs produce different keys', () => {
    const k1 = makeCacheKey('conv-A', 4)
    const k2 = makeCacheKey('conv-B', 4)
    expect(k1).not.toBe(k2)
  })
})

// ─── Integration: compressHistory ────────────────────────────────────────────

const fakeSummarizer = vi.fn(async (_msgs: ModelMessage[]) => 'FAKE SUMMARY')

describe('compressHistory — flag-gated behavior', () => {
  it('returns messages unchanged when under token budget', async () => {
    const messages = [msg('user', 'Hello'), msg('assistant', 'Hi')]
    const result = await compressHistory(messages, 'conv-1', {
      tokenBudget: 10_000,
      summarizer: fakeSummarizer,
    })
    expect(result).toEqual(messages)
    expect(fakeSummarizer).not.toHaveBeenCalled()
  })

  it('compresses when over token budget', async () => {
    fakeSummarizer.mockClear()
    const messages = Array.from({ length: 20 }, (_, i) =>
      longMsg(i % 2 === 0 ? 'user' : 'assistant', 6_400),
    )
    const result = await compressHistory(messages, 'conv-compress', {
      tokenBudget: 1_000,
      tailSize: 4,
      summarizer: fakeSummarizer,
    })

    expect(fakeSummarizer).toHaveBeenCalledOnce()
    expect(result.length).toBeLessThan(messages.length)
    expect(result[0].role).toBe('user')
    expect(result[0].content as string).toContain('CONVERSATION SUMMARY')
    expect(result[1].role).toBe('assistant')
    // verbatim tail = 4 pairs = 8 messages; +2 summary pair = 10
    expect(result).toHaveLength(10)
  })

  it('caches compression result for same conversation + tail position', async () => {
    fakeSummarizer.mockClear()
    const messages = Array.from({ length: 20 }, (_, i) =>
      longMsg(i % 2 === 0 ? 'user' : 'assistant', 6_400),
    )
    const opts = { tokenBudget: 1_000, tailSize: 4, summarizer: fakeSummarizer }

    await compressHistory(messages, 'conv-cache-test', opts)
    await compressHistory(messages, 'conv-cache-test', opts)

    expect(fakeSummarizer).toHaveBeenCalledOnce()
  })

  it('does not cache across different conversation IDs', async () => {
    fakeSummarizer.mockClear()
    const messages = Array.from({ length: 20 }, (_, i) =>
      longMsg(i % 2 === 0 ? 'user' : 'assistant', 6_400),
    )
    const opts = { tokenBudget: 1_000, tailSize: 4, summarizer: fakeSummarizer }

    await compressHistory(messages, 'conv-id-A', opts)
    await compressHistory(messages, 'conv-id-B', opts)

    expect(fakeSummarizer).toHaveBeenCalledTimes(2)
  })
})
