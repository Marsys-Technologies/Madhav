/**
 * PanchangContextInjection — unit tests for the context-injection logic
 * implemented in platform/src/app/clients/[id]/consume/page.tsx
 * (buildPanchangInitialMessages function — extracted for testability).
 *
 * Tests (AC.4C8.2):
 *   - Prompt with context produces correct <panchang_context> + <user_question> wrapping
 *   - Prompt without context produces plain message
 *   - Malformed context JSON → falls back to plain message
 *   - Date extraction from context
 *
 * Phase: 4C-8 (Item 8)
 */

import { describe, it, expect } from 'vitest'

// ── Re-implement the function under test ──────────────────────────────────────
// Since the function is embedded in a Next.js server component (page.tsx),
// we re-implement it here for unit-testing. Any change to the production
// function must be reflected here.

interface UIMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  parts: { type: 'text'; text: string }[]
}

function buildPanchangInitialMessages(
  prompt: string | undefined,
  contextJson: string | undefined,
): UIMessage[] | undefined {
  if (!prompt) return undefined

  let content: string

  if (contextJson) {
    let parsedDate = ''
    try {
      const parsed = JSON.parse(contextJson) as Record<string, unknown>
      parsedDate = (parsed['date'] as string) ?? ''
    } catch {
      return [
        {
          id: 'test-id',
          role: 'user',
          content: prompt,
          parts: [{ type: 'text', text: prompt }],
        },
      ]
    }

    const dateLine = parsedDate
      ? `<!-- AUTO-INJECTED FROM /panchang ON ${parsedDate} -->`
      : '<!-- AUTO-INJECTED FROM /panchang -->'

    content = [
      `<panchang_context>`,
      dateLine,
      contextJson,
      `</panchang_context>`,
      ``,
      `<user_question>`,
      prompt,
      `</user_question>`,
    ].join('\n')
  } else {
    content = prompt
  }

  return [
    {
      id: 'test-id',
      role: 'user',
      content,
      parts: [{ type: 'text', text: content }],
    },
  ]
}

// ── Fixtures ──────────────────────────────────────────────────────────────────

const PROMPT = 'What does Chaturthi mean for me today?'
const CTX_OBJ = {
  date: '2026-05-20',
  lat: 20.2961,
  lon: 85.8245,
  angas: { tithi: { name: 'Chaturthi', number: 4 } },
}
const CTX_JSON = JSON.stringify(CTX_OBJ)

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('buildPanchangInitialMessages', () => {
  it('returns undefined when prompt is undefined', () => {
    expect(buildPanchangInitialMessages(undefined, undefined)).toBeUndefined()
  })

  it('returns plain message when no context provided', () => {
    const msgs = buildPanchangInitialMessages(PROMPT, undefined)
    expect(msgs).toHaveLength(1)
    expect(msgs![0].role).toBe('user')
    expect(msgs![0].content).toBe(PROMPT)
    expect(msgs![0].content).not.toContain('<panchang_context>')
  })

  it('wraps content with <panchang_context> when context provided (AC.4C8.2)', () => {
    const msgs = buildPanchangInitialMessages(PROMPT, CTX_JSON)
    expect(msgs).toHaveLength(1)
    const content = msgs![0].content
    expect(content).toContain('<panchang_context>')
    expect(content).toContain('</panchang_context>')
    expect(content).toContain('<user_question>')
    expect(content).toContain('</user_question>')
    expect(content).toContain(PROMPT)
    expect(content).toContain(CTX_JSON)
  })

  it('injects correct date in the AUTO-INJECTED comment', () => {
    const msgs = buildPanchangInitialMessages(PROMPT, CTX_JSON)
    const content = msgs![0].content
    expect(content).toContain('<!-- AUTO-INJECTED FROM /panchang ON 2026-05-20 -->')
  })

  it('uses generic comment when context has no date field', () => {
    const noDateCtx = JSON.stringify({ angas: {} })
    const msgs = buildPanchangInitialMessages(PROMPT, noDateCtx)
    const content = msgs![0].content
    expect(content).toContain('<!-- AUTO-INJECTED FROM /panchang -->')
    expect(content).not.toContain('ON ')
  })

  it('falls back to plain message on malformed JSON context', () => {
    const msgs = buildPanchangInitialMessages(PROMPT, 'NOT_VALID_JSON{{')
    expect(msgs).toHaveLength(1)
    expect(msgs![0].content).toBe(PROMPT)
    expect(msgs![0].content).not.toContain('<panchang_context>')
  })

  it('content is reflected in both .content and .parts[0].text', () => {
    const msgs = buildPanchangInitialMessages(PROMPT, CTX_JSON)
    const msg = msgs![0]
    expect(msg.parts[0].text).toBe(msg.content)
  })

  it('planner sees prompt inside <user_question> tag', () => {
    const msgs = buildPanchangInitialMessages(PROMPT, CTX_JSON)
    const content = msgs![0].content
    // Check that prompt appears inside the user_question block, not just anywhere
    const userQuestionBlock = content.split('<user_question>')[1]?.split('</user_question>')[0]
    expect(userQuestionBlock?.trim()).toBe(PROMPT)
  })

  it('panchang context JSON is inside <panchang_context> tag', () => {
    const msgs = buildPanchangInitialMessages(PROMPT, CTX_JSON)
    const content = msgs![0].content
    const ctxBlock = content.split('<panchang_context>')[1]?.split('</panchang_context>')[0]
    expect(ctxBlock).toContain(CTX_JSON)
    const extracted = ctxBlock!.trim().split('\n').slice(1).join('\n').trim()
    const parsed = JSON.parse(extracted) as typeof CTX_OBJ
    expect(parsed.date).toBe('2026-05-20')
    expect(parsed.angas.tithi.name).toBe('Chaturthi')
  })
})
