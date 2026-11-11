// @vitest-environment jsdom
import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { useThreadRuntime } from '@assistant-ui/react'
import { createUIMessageStream, createUIMessageStreamResponse, type UIMessage } from 'ai'

const harness = vi.hoisted(() => ({
  thread: null as ReturnType<typeof useThreadRuntime> | null,
  fetch: vi.fn(),
}))

vi.mock('@/components/consume/PartialDataBanner', async () => {
  const { useThreadRuntime } = await import('@assistant-ui/react')
  return { PartialDataBanner: function ObserveConsultRuntime() {
    harness.thread = useThreadRuntime()
    return null
  } }
})
vi.mock('@/hooks/useChatPreferences', () => ({
  useChatPreferences: () => ({ stack: 'fixture', style: 'acharya', lelEnabled: false,
    setStack: vi.fn(), setStyle: vi.fn(), setLelEnabled: vi.fn() }),
  useLastPrompt: () => ['', vi.fn()], useTextScale: () => [1, vi.fn()], TEXT_SCALES: [1],
}))
vi.mock('@/hooks/useTokenCount', () => ({ useTokenCount: () => ({ tokenCount: null, pctUsed: null }) }))
vi.mock('@/lib/chat-v2/useMultiProviderParity', () => ({ useMultiProviderParity: () => false }))
vi.mock('@/components/consume/ConversationSidebarV2', () => ({ ConversationSidebarV2: () => null }))
vi.mock('@/components/consume/ConsumeReportLibraryV2', () => ({ ConsumeReportLibraryV2: () => null }))
vi.mock('@/components/consume/TraceDrawer', () => ({ TraceDrawer: () => null }))
vi.mock('@/components/consume/SettingsDropdown', () => ({ SettingsDropdown: () => null }))
vi.mock('@/components/chat/ModelStylePicker', () => ({ ModelStylePicker: () => null }))
vi.mock('@/components/chat/CommandPalette', () => ({ CommandPalette: () => null }))
vi.mock('@/components/chat/ShortcutsDialog', () => ({ ShortcutsDialog: () => null }))
vi.mock('@/components/chat/ShareButton', () => ({ ShareButton: () => null }))

import { ConsumeChatV2 } from '@/components/consume/ConsumeChatV2'

const scrollToDescriptor = Object.getOwnPropertyDescriptor(HTMLElement.prototype, 'scrollTo')

function unavailable() {
  return Response.json({ error: { code: 'ATTACHMENT_UNAVAILABLE', retry: false } }, { status: 503 })
}

function textReply() {
  const stream = createUIMessageStream({
    execute({ writer }) {
      writer.write({ type: 'start', messageId: 'fixture-answer' })
      writer.write({ type: 'text-start', id: 'answer-text' })
      writer.write({ type: 'text-delta', id: 'answer-text', delta: 'Synthetic text reply' })
      writer.write({ type: 'text-end', id: 'answer-text' })
      writer.write({ type: 'finish', finishReason: 'stop' })
    },
  })
  return createUIMessageStreamResponse({ stream })
}

beforeEach(() => {
  harness.thread = null
  harness.fetch.mockReset().mockImplementation(async () => unavailable())
  vi.stubGlobal('fetch', harness.fetch)
  Object.defineProperty(HTMLElement.prototype, 'scrollTo', { value: vi.fn(), configurable: true })
})
afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
  if (scrollToDescriptor) Object.defineProperty(HTMLElement.prototype, 'scrollTo', scrollToDescriptor)
  else Reflect.deleteProperty(HTMLElement.prototype, 'scrollTo')
})

function mount(initialMessages?: UIMessage[]) {
  render(<ConsumeChatV2 chartId="fixture-chart" chartName="Fixture" reports={[]} conversations={[]} initialMessages={initialMessages} />)
  return screen.getByTestId('v2-composer-input')
}

function sendButton() {
  return screen.getByTestId('v2-send-btn')
}

function sentBody(index: number) {
  const [url, options] = harness.fetch.mock.calls.filter(([url]) => url === '/api/chat/consume')[index]
  expect(url).toBe('/api/chat/consume')
  return JSON.parse(options.body)
}

describe('Consult attachment availability', () => {
  it('explains unavailable attachments before submission while preserving text controls', () => {
    const input = mount()
    expect(screen.getByText(/attachments are currently unavailable in consult/i)).toBeDefined()
    expect(screen.getByTestId('v2-attach-btn')).toHaveProperty('disabled', true)
    expect(screen.getByTestId('v2-camera-btn')).toHaveProperty('disabled', true)
    expect(document.querySelector('input[type=file]')).toBeNull()
    expect(input).toHaveProperty('disabled', false)
    expect(sendButton()).toHaveProperty('disabled', true)
    fireEvent.change(input, { target: { value: 'Fixture question' } })
    expect(sendButton()).toHaveProperty('disabled', false)
  })

  it('blocks file paste and drop, shows a stale refusal and completes a new text turn', async () => {
    harness.fetch.mockImplementationOnce(async () => unavailable()).mockImplementationOnce(async () => textReply())
    const input = mount()
    fireEvent.change(input, { target: { value: 'Fixture question' } })
    await waitFor(() => expect(harness.thread?.getState().capabilities.attachments).toBe(true))
    const file = new File(['fixture'], 'fixture.png', { type: 'image/png' })
    expect(fireEvent.drop(screen.getByTestId('v2-composer'), { dataTransfer: { files: [file] } })).toBe(false)
    await act(async () => {
      expect(fireEvent.paste(input, { clipboardData: { files: [file], items: [] } })).toBe(true)
    })
    expect(harness.thread?.composer.getState().attachments).toHaveLength(0)
    expect(harness.fetch).not.toHaveBeenCalled()

    await act(async () => {
      harness.thread!.append({
        role: 'user',
        content: [],
        attachments: [{
          id: 'fixture-file', type: 'file', name: 'fixture.png', contentType: 'image/png',
          status: { type: 'complete' },
          content: [{ type: 'file', mimeType: 'image/png', data: 'data:image/png;base64,eA==' }],
        }],
      })
    })
    expect((await screen.findByRole('alert')).textContent).toMatch(/attachment unavailable/i)
    expect(harness.fetch).toHaveBeenCalledOnce()
    expect(sentBody(0).messages.at(-1).parts).toEqual([
      { type: 'file', mediaType: 'image/png', filename: 'fixture.png', url: 'data:image/png;base64,eA==' },
    ])

    fireEvent.change(input, { target: { value: 'Text retry' } })
    fireEvent.click(sendButton())
    await waitFor(() => expect(harness.fetch).toHaveBeenCalledTimes(2))
    expect(sentBody(1)).not.toHaveProperty('attachments')
    expect(sentBody(1).messages[0].parts[0].type).toBe('file')
    expect(sentBody(1).messages.at(-1).parts).toEqual([{ type: 'text', text: 'Text retry' }])
    expect(await screen.findByText('Synthetic text reply')).toBeDefined()
    expect(screen.queryByRole('alert')).toBeNull()
  })

  it('stops regenerate before truncation or reload when it would replay a stored file turn', async () => {
    mount([
      { id: 'old-user', role: 'user', parts: [
        { type: 'text', text: 'Earlier question' },
        { type: 'file', mediaType: 'image/png', url: 'data:image/png;base64,eA==' },
      ] },
      { id: 'old-answer', role: 'assistant', parts: [{ type: 'text', text: 'Earlier answer' }] },
    ])
    expect(await screen.findByText('Attachment unavailable')).toBeDefined()
    expect(document.querySelector('img[src^="data:image/png"]')).toBeNull()
    fireEvent.click(await screen.findByTestId('v2-regenerate-btn'))
    expect(await screen.findByText(/this turn contains an attachment/i)).toBeDefined()
    expect(harness.fetch).not.toHaveBeenCalled()
    expect(screen.getByText('Earlier question')).toBeDefined()
    expect(screen.getByText('Earlier answer')).toBeDefined()
  })
})
