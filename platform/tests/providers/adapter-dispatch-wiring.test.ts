/**
 * adapter-dispatch-wiring.test.ts
 *
 * Tests for the three bugs found during R11.D rollout investigation (2026-05-23):
 *   Bug A — current user turn missing from adapterMessages (empty messages on first query)
 *   Bug B — non-text content parts map to '' empty string (Anthropic HTTP 400)
 *   Bug C — system/synthesis prompt not passed to adapterChatReq
 *
 * These tests use the pure helper extracted from route.ts so they are fast and
 * isolated from Next.js route machinery.
 */

import { describe, it, expect } from 'vitest'
import {
  buildAdapterMessages,
  buildAdapterChatRequest,
} from '../../src/lib/providers/adapter-dispatch-helpers'
import type { ChatMessage } from '../../src/lib/providers/types'

// ---------------------------------------------------------------------------
// Bug A — current user turn must be appended
// ---------------------------------------------------------------------------

describe('buildAdapterMessages — Bug A: current user turn', () => {
  it('first message (empty history): includes the current user turn', () => {
    const history: import('ai').ModelMessage[] = []
    const messages = buildAdapterMessages(history, 'What is my current dasha?')

    expect(messages.length).toBe(1)
    expect(messages[0].role).toBe('user')
    expect(messages[0].content).toBe('What is my current dasha?')
  })

  it('multi-turn history: appends user turn AFTER history', () => {
    const history = [
      { role: 'user' as const, content: 'Prior question' },
      { role: 'assistant' as const, content: 'Prior answer' },
    ] as import('ai').ModelMessage[]

    const messages = buildAdapterMessages(history, 'Follow-up question')

    expect(messages.length).toBe(3)
    expect(messages[2].role).toBe('user')
    expect(messages[2].content).toBe('Follow-up question')
  })

  it('never returns an empty messages array even with empty history', () => {
    const messages = buildAdapterMessages([], 'Any query')
    expect(messages.length).toBeGreaterThan(0)
  })
})

// ---------------------------------------------------------------------------
// Bug B — non-text content parts must not produce empty string content
// ---------------------------------------------------------------------------

describe('buildAdapterMessages — Bug B: non-text content parts', () => {
  it('message with only text parts: content is the joined text', () => {
    const history = [
      {
        role: 'user' as const,
        content: [{ type: 'text', text: 'Hello' }, { type: 'text', text: ' world' }],
      },
    ] as import('ai').ModelMessage[]

    const messages = buildAdapterMessages(history, 'next')
    const historyMsg = messages[0]
    expect(historyMsg.content).toBe('Hello world')
  })

  it('message with ONLY non-text parts: content is NOT empty string', () => {
    const history = [
      {
        role: 'user' as const,
        content: [{ type: 'tool_result', toolCallId: 'abc', content: [] }],
      },
    ] as unknown as import('ai').ModelMessage[]

    const messages = buildAdapterMessages(history, 'next')
    const historyMsg = messages[0]
    expect(historyMsg.content).not.toBe('')
    expect(historyMsg.content.length).toBeGreaterThan(0)
  })

  it('message with mixed text and non-text parts: only text is extracted', () => {
    const history = [
      {
        role: 'assistant' as const,
        content: [
          { type: 'text', text: 'Extracted text' },
          { type: 'tool_use', toolCallId: 'xyz', toolName: 'query_signals', args: {} },
        ],
      },
    ] as unknown as import('ai').ModelMessage[]

    const messages = buildAdapterMessages(history, 'next')
    const historyMsg = messages[0]
    expect(historyMsg.content).toBe('Extracted text')
  })
})

// ---------------------------------------------------------------------------
// Bug C — system prompt must be passed through to the chat request
// ---------------------------------------------------------------------------

describe('buildAdapterChatRequest — Bug C: system prompt', () => {
  const sampleMessages: ChatMessage[] = [
    { role: 'user', content: 'What is my dasha?' },
  ]

  it('includes system prompt when provided', () => {
    const req = buildAdapterChatRequest(sampleMessages, 'claude-opus-4-7', 'System context here')
    expect(req.system).toBe('System context here')
  })

  it('system is undefined when no system content provided', () => {
    const req = buildAdapterChatRequest(sampleMessages, 'claude-opus-4-7', undefined)
    expect(req.system).toBeUndefined()
  })

  it('messages are passed through unchanged', () => {
    const req = buildAdapterChatRequest(sampleMessages, 'claude-opus-4-7', 'ctx')
    expect(req.messages).toEqual(sampleMessages)
  })

  it('model is passed through', () => {
    const req = buildAdapterChatRequest(sampleMessages, 'claude-opus-4-7', 'ctx')
    expect(req.model).toBe('claude-opus-4-7')
  })
})

// ---------------------------------------------------------------------------
// Integration — full round trip: history + queryText + system → valid ChatRequest
// ---------------------------------------------------------------------------

describe('buildAdapterMessages + buildAdapterChatRequest — round trip', () => {
  it('first query produces a valid non-empty ChatRequest with user turn + system', () => {
    const messages = buildAdapterMessages([], 'Tell me about my Jupiter dasha')
    const req = buildAdapterChatRequest(messages, 'claude-opus-4-7', 'You are Madhav...')

    expect(req.messages.length).toBeGreaterThan(0)
    expect(req.messages.some(m => m.role === 'user')).toBe(true)
    expect(req.system).toBe('You are Madhav...')
    expect(req.model).toBe('claude-opus-4-7')
  })
})
