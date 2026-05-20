/**
 * X-S8 — Selective Share
 * Amendment 2: parent-context integration tests for ShareButton checkboxes.
 *
 * Click-path: Chat V2 conversation → click Share → modal opens → two checkboxes
 *   "Show reasoning" + "Show methodology" (both checked by default) → uncheck
 *   "Show reasoning" → click "Create Link" → fetch called with hide_reasoning: true.
 *
 * Amendment 1 confirmation: MARSYS_FLAG_R10_SELECTIVE_SHARE is server-side only
 *   (read in API route + server page) — NOT in any 'use client' file.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, act, fireEvent } from '@testing-library/react'
import React from 'react'
import { ShareButton } from '@/components/chat/ShareButton'
import { filterMessages } from './selective_share_helpers'

// ── A2: parent-context shell ──────────────────────────────────────────────────

function ShareButtonShell({ conversationId }: { conversationId: string }) {
  return (
    <div data-testid="v2-chat-shell">
      <ShareButton conversationId={conversationId} />
    </div>
  )
}

// ── ShareButton checkbox tests ────────────────────────────────────────────────

describe('ShareButton selective share — parent-context (Amendment 2)', () => {
  let fetchSpy: ReturnType<typeof vi.fn>

  beforeEach(() => {
    fetchSpy = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ share: null }),
    })
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    global.fetch = fetchSpy as any
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('renders Share trigger button when conversationId is provided', () => {
    const { container } = render(<ShareButtonShell conversationId="conv-1" />)
    const trigger = container.querySelector('[aria-label="Share conversation"]')
    expect(trigger).not.toBeNull()
  })

  it('shows reasoning and methodology checkboxes in the create-share state', async () => {
    render(<ShareButtonShell conversationId="conv-1" />)
    const trigger = document.querySelector('[aria-label="Share conversation"]') as HTMLElement

    await act(async () => { trigger.click() })
    await act(async () => {})

    // Radix portals content to document.body — search there
    const reasoningCb = document.querySelector('[data-testid="v2-share-show-reasoning"]')
    const methodologyCb = document.querySelector('[data-testid="v2-share-show-methodology"]')
    expect(reasoningCb).not.toBeNull()
    expect(methodologyCb).not.toBeNull()
  })

  it('checkboxes are checked by default', async () => {
    render(<ShareButtonShell conversationId="conv-1" />)
    await act(async () => {
      ;(document.querySelector('[aria-label="Share conversation"]') as HTMLElement).click()
    })
    await act(async () => {})

    const reasoningCb = document.querySelector('[data-testid="v2-share-show-reasoning"]') as HTMLInputElement
    const methodologyCb = document.querySelector('[data-testid="v2-share-show-methodology"]') as HTMLInputElement
    expect(reasoningCb?.checked).toBe(true)
    expect(methodologyCb?.checked).toBe(true)
  })

  it('unchecking reasoning sends hide_reasoning: true in POST body', async () => {
    fetchSpy
      .mockResolvedValueOnce({ ok: true, json: async () => ({ share: null }) }) // GET
      .mockResolvedValueOnce({ ok: true, json: async () => ({ slug: 'abc123' }) }) // POST

    render(<ShareButtonShell conversationId="conv-2" />)
    await act(async () => {
      ;(document.querySelector('[aria-label="Share conversation"]') as HTMLElement).click()
    })
    await act(async () => {})

    const reasoningCb = document.querySelector('[data-testid="v2-share-show-reasoning"]') as HTMLInputElement
    await act(async () => { fireEvent.click(reasoningCb) })

    const createBtn = document.querySelector('[data-testid="v2-share-create-btn"]') as HTMLButtonElement
    await act(async () => { createBtn.click() })
    await act(async () => {})

    const postCall = fetchSpy.mock.calls.find((c: unknown[]) => (c[1] as RequestInit)?.method === 'POST')
    expect(postCall).toBeTruthy()
    const body = JSON.parse((postCall![1] as RequestInit).body as string) as Record<string, unknown>
    expect(body.hide_reasoning).toBe(true)
    expect(body.hide_methodology).toBe(false)
  })
})

// ── filterMessages helper tests ───────────────────────────────────────────────

describe('filterMessages — reasoning + methodology filtering', () => {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  type AnyMsg = any

  it('returns messages unchanged when both flags are false', () => {
    const msgs: AnyMsg[] = [{ id: '1', role: 'assistant', content: '## Methodology\nfoo', parts: [] }]
    expect(filterMessages(msgs, false, false)).toEqual(msgs)
  })

  it('removes reasoning parts when hideReasoning=true', () => {
    const msgs: AnyMsg[] = [
      {
        id: '1',
        role: 'assistant',
        content: 'response',
        parts: [
          { type: 'reasoning', content: 'thinking...' },
          { type: 'text', text: 'answer' },
        ],
      },
    ]
    const result = filterMessages(msgs, true, false)
    expect(result[0].parts).toHaveLength(1)
    expect(result[0].parts![0].type).toBe('text')
  })

  it('does not filter non-reasoning parts', () => {
    const msgs: AnyMsg[] = [
      {
        id: '1',
        role: 'assistant',
        content: 'response',
        parts: [{ type: 'text', text: 'answer' }],
      },
    ]
    const result = filterMessages(msgs, true, false)
    expect(result[0].parts).toHaveLength(1)
  })

  it('does not filter user messages', () => {
    const msgs: AnyMsg[] = [
      { id: '1', role: 'user', content: 'question', parts: [{ type: 'reasoning', content: 'x' }] },
    ]
    const result = filterMessages(msgs, true, false)
    expect(result[0].parts).toHaveLength(1)
  })
})
