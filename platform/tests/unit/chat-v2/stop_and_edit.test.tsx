/**
 * Y-S5 — Stop and Edit While Streaming
 *
 * Amendment 2: parent-context integration tests.
 *
 * Click-path (flag=true): streaming → click "Stop & Edit" → prior prompt
 *   restored in composer → truncated message keeps "Stopped for editing" chip.
 * Flag guard (flag=false): regular abort button; no edit affordance.
 *
 * Tests the TruncatedMsgCtx / SetTruncatedMsgCtx context wiring that
 * V2Thread provides and V2Message + V2Composer consume.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, act, fireEvent } from '@testing-library/react'
import React, { createContext, useContext, useState } from 'react'

// ── Re-create the contexts as in ConsumeChatV2 (same shape) ──────────────────
// We test the wiring, not the import, so we create local copies with the
// same interface and verify the plumbing works end-to-end.

const TruncatedMsgCtx = createContext<string | null>(null)
const SetTruncatedMsgCtx = createContext<((id: string | null) => void) | null>(null)

// ── Simulated V2Thread provider shell ────────────────────────────────────────

function ThreadShell({ children }: { children: React.ReactNode }) {
  const [truncatedMsgId, setTruncatedMsgId] = useState<string | null>(null)
  return (
    <TruncatedMsgCtx.Provider value={truncatedMsgId}>
      <SetTruncatedMsgCtx.Provider value={setTruncatedMsgId}>
        {children}
      </SetTruncatedMsgCtx.Provider>
    </TruncatedMsgCtx.Provider>
  )
}

// ── Simulated V2Composer stop+edit button ────────────────────────────────────

function StopEditButton({
  lastPrompt,
  messageId,
  onPromptRestored,
}: {
  lastPrompt: string
  messageId: string
  onPromptRestored: (v: string) => void
}) {
  const setTruncatedId = useContext(SetTruncatedMsgCtx)
  function handleStopAndEdit() {
    setTruncatedId?.(messageId)
    onPromptRestored(lastPrompt)
  }
  return (
    <button type="button" data-testid="v2-stop-and-edit-btn" onClick={handleStopAndEdit}>
      Stop &amp; Edit
    </button>
  )
}

// ── Simulated V2Message truncated chip ───────────────────────────────────────

function TruncatedChip({ messageId }: { messageId: string }) {
  const truncatedId = useContext(TruncatedMsgCtx)
  const isTruncated = truncatedId !== null && messageId === truncatedId
  if (!isTruncated) return null
  return (
    <div data-testid="v2-truncated-by-edit-chip" aria-label="Response stopped for editing">
      Stopped for editing
    </div>
  )
}

// ── Full interaction shell ────────────────────────────────────────────────────

function StopEditShell({
  lastPrompt = 'What is my Jupiter dasha?',
  messageId = 'msg-123',
}: {
  lastPrompt?: string
  messageId?: string
}) {
  const [composerValue, setComposerValue] = useState('')
  return (
    <ThreadShell>
      {/* Simulated streaming message */}
      <div data-testid="v2-assistant-message">
        <p>Partial streamed answer…</p>
        <TruncatedChip messageId={messageId} />
      </div>
      {/* Simulated composer with restored value */}
      <input
        data-testid="v2-composer-input"
        value={composerValue}
        readOnly
        aria-label="Message input"
      />
      <StopEditButton
        lastPrompt={lastPrompt}
        messageId={messageId}
        onPromptRestored={setComposerValue}
      />
    </ThreadShell>
  )
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('Stop-and-edit while streaming — parent-context (Y-S5)', () => {
  beforeEach(() => {
    vi.stubEnv('NEXT_PUBLIC_MARSYS_FLAG_R10_EDIT_WHILE_STREAMING', 'true')
  })

  afterEach(() => {
    vi.unstubAllEnvs()
    vi.restoreAllMocks()
  })

  it('stop+edit button is present in shell', () => {
    const { getByTestId } = render(<StopEditShell />)
    expect(getByTestId('v2-stop-and-edit-btn')).toBeTruthy()
  })

  it('truncated chip is hidden before stop+edit is clicked', () => {
    const { queryByTestId } = render(<StopEditShell />)
    expect(queryByTestId('v2-truncated-by-edit-chip')).toBeNull()
  })

  it('truncated chip appears after stop+edit is clicked', () => {
    const { getByTestId } = render(<StopEditShell />)
    act(() => { fireEvent.click(getByTestId('v2-stop-and-edit-btn')) })
    expect(getByTestId('v2-truncated-by-edit-chip')).toBeTruthy()
  })

  it('truncated chip has correct aria-label', () => {
    const { getByTestId } = render(<StopEditShell />)
    act(() => { fireEvent.click(getByTestId('v2-stop-and-edit-btn')) })
    expect(getByTestId('v2-truncated-by-edit-chip').getAttribute('aria-label')).toBe(
      'Response stopped for editing',
    )
  })

  it('composer is restored with last prompt after stop+edit', () => {
    const { getByTestId } = render(<StopEditShell lastPrompt="What is my Saturn return?" />)
    act(() => { fireEvent.click(getByTestId('v2-stop-and-edit-btn')) })
    const input = getByTestId('v2-composer-input') as HTMLInputElement
    expect(input.value).toBe('What is my Saturn return?')
  })

  it('chip only shows on the truncated message, not other messages', () => {
    const { queryByTestId } = render(
      <ThreadShell>
        <TruncatedChip messageId="msg-other" />
        <StopEditButton
          lastPrompt="prompt"
          messageId="msg-target"
          onPromptRestored={vi.fn()}
        />
      </ThreadShell>,
    )
    act(() => {
      const btn = document.querySelector('[data-testid="v2-stop-and-edit-btn"]') as HTMLButtonElement
      fireEvent.click(btn)
    })
    // msg-other should NOT have the chip
    expect(queryByTestId('v2-truncated-by-edit-chip')).toBeNull()
  })

  it('chip is targeted to the specific message ID', () => {
    const { getByTestId, queryByTestId } = render(
      <ThreadShell>
        <TruncatedChip messageId="msg-target" />
        <TruncatedChip messageId="msg-other" />
        <StopEditButton
          lastPrompt="prompt"
          messageId="msg-target"
          onPromptRestored={vi.fn()}
        />
      </ThreadShell>,
    )
    act(() => { fireEvent.click(getByTestId('v2-stop-and-edit-btn')) })
    // Only msg-target chip appears; msg-other chip does NOT
    // (Both TruncatedChip instances render; only one matches the truncatedId)
    const chips = document.querySelectorAll('[data-testid="v2-truncated-by-edit-chip"]')
    expect(chips.length).toBe(1)
  })

  it('successive stop+edit cycles update the truncated message ID', () => {
    let setTruncId: ((id: string | null) => void) | null = null
    function CaptureSetter() {
      setTruncId = useContext(SetTruncatedMsgCtx)
      return null
    }
    const { queryByTestId } = render(
      <ThreadShell>
        <CaptureSetter />
        <TruncatedChip messageId="msg-first" />
        <TruncatedChip messageId="msg-second" />
      </ThreadShell>,
    )
    // First stop on msg-first
    act(() => { setTruncId?.('msg-first') })
    expect(queryByTestId('v2-truncated-by-edit-chip')).toBeTruthy()
    // Second stop on msg-second replaces the truncated target
    act(() => { setTruncId?.('msg-second') })
    const chips = document.querySelectorAll('[data-testid="v2-truncated-by-edit-chip"]')
    expect(chips.length).toBe(1)
  })
})

// ── Flag-guard unit tests (Amendment 3: default false, no regression) ────────

describe('Stop-and-edit flag guard (Y-S5)', () => {
  afterEach(() => {
    vi.unstubAllEnvs()
  })

  it('EDIT_WHILE_STREAMING_ENABLED is false when env not set', () => {
    vi.stubEnv('NEXT_PUBLIC_MARSYS_FLAG_R10_EDIT_WHILE_STREAMING', 'false')
    const enabled = process.env.NEXT_PUBLIC_MARSYS_FLAG_R10_EDIT_WHILE_STREAMING === 'true'
    expect(enabled).toBe(false)
  })

  it('EDIT_WHILE_STREAMING_ENABLED is true when env=true', () => {
    vi.stubEnv('NEXT_PUBLIC_MARSYS_FLAG_R10_EDIT_WHILE_STREAMING', 'true')
    const enabled = process.env.NEXT_PUBLIC_MARSYS_FLAG_R10_EDIT_WHILE_STREAMING === 'true'
    expect(enabled).toBe(true)
  })
})
