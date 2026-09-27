/**
 * /clients/[id]/consult/[conversationId] — a correction-archived conversation
 * renders the read-only historical transcript and never mounts the chat
 * composer (Jātaka chart workspace, Task 8). Active conversations are unchanged.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'

vi.mock('server-only', () => ({}))

const { mockGetConversation, mockLoadV2, mockLoadHistorical } = vi.hoisted(() => ({
  mockGetConversation: vi.fn(),
  mockLoadV2: vi.fn(),
  mockLoadHistorical: vi.fn(),
}))

vi.mock('@/lib/firebase/server', () => ({ getServerUser: vi.fn(async () => ({ uid: 'owner-uid' })) }))
vi.mock('@/lib/db/client', () => ({
  query: vi.fn(async (sql: string) =>
    /FROM profiles/.test(sql)
      ? { rows: [{ role: 'guest' }] }
      : { rows: [{ name: 'N', birth_date: '1984-02-05', birth_place: 'P', client_id: 'owner-uid' }] },
  ),
}))
vi.mock('next/navigation', () => ({
  redirect: vi.fn(() => { throw new Error('NEXT_REDIRECT') }),
  notFound: vi.fn(() => { throw new Error('NEXT_NOT_FOUND') }),
}))
vi.mock('@/lib/conversations', () => ({ getConversation: mockGetConversation, listConversations: vi.fn(async () => []) }))
vi.mock('@/lib/persistence/conversation_writer', () => ({ loadConversationMessagesV2: mockLoadV2 }))
vi.mock('@/lib/conversations/historicalReading', () => ({ loadHistoricalConversationMessages: mockLoadHistorical }))
vi.mock('@/lib/config/index', () => ({ configService: { getFlag: vi.fn(() => false) } }))
vi.mock('@/components/consume/ConsumeChat', () => ({ ConsumeChat: () => <div data-testid="consume-chat" /> }))
vi.mock('@/components/consume/HistoricalConversationView', () => ({
  HistoricalConversationView: ({ messages }: { messages: Array<{ text: string }> }) => (
    <div data-testid="historical-view">{messages.map((m) => m.text).join('|')}</div>
  ),
}))

import Page from '../consult/[conversationId]/page'

const BASE = { id: 'conv-1', chart_id: 'c1', user_id: 'owner-uid', module: 'consume', title: 'T', created_at: '', updated_at: '' }

async function renderPage() {
  render(await Page({ params: Promise.resolve({ id: 'c1', conversationId: 'conv-1' }) }))
}

beforeEach(() => {
  vi.clearAllMocks()
  mockLoadV2.mockResolvedValue([])
  mockLoadHistorical.mockResolvedValue([{ id: 'm1', role: 'user', text: 'old question', createdAt: '' }])
})

describe('consult conversation page', () => {
  it('renders the read-only historical view for a correction archive, with no composer', async () => {
    mockGetConversation.mockResolvedValue({ ...BASE, archived_at: '2026-09-27', archive_reason: 'chart_details_changed', archived_chart_snapshot: null })
    await renderPage()
    expect(screen.getByTestId('historical-view')).toHaveTextContent('old question')
    expect(screen.queryByTestId('consume-chat')).not.toBeInTheDocument()
    expect(mockLoadHistorical).toHaveBeenCalledWith('conv-1')
    expect(mockLoadV2).not.toHaveBeenCalled()
  })

  it('keeps the existing chat for an active conversation', async () => {
    mockGetConversation.mockResolvedValue({ ...BASE, archived_at: null, archive_reason: null })
    await renderPage()
    expect(screen.getByTestId('consume-chat')).toBeInTheDocument()
    expect(mockLoadHistorical).not.toHaveBeenCalled()
  })
})
