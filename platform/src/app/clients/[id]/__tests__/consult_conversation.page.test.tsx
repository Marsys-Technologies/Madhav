/**
 * /clients/[id]/consult/[conversationId] — a correction-archived conversation
 * renders the read-only historical transcript and never mounts the chat
 * composer (Jātaka chart workspace, Task 8). Active conversations are unchanged.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import type { ConversationSummary } from '@/lib/conversations'

vi.mock('server-only', () => ({}))

const { mockQuery, mockLoadV2, mockLoadHistorical } = vi.hoisted(() => ({
  mockQuery: vi.fn(),
  mockLoadV2: vi.fn(),
  mockLoadHistorical: vi.fn(),
}))

vi.mock('@/lib/firebase/server', () => ({ getServerUser: vi.fn(async () => ({ uid: 'owner-uid' })) }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))
vi.mock('next/navigation', () => ({
  redirect: vi.fn((path: string) => { throw new Error(`NEXT_REDIRECT:${path}`) }),
  notFound: vi.fn(() => { throw new Error('NEXT_NOT_FOUND') }),
}))
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

const CHART_ID = '10000000-0000-4000-8000-000000000001'
const CONVERSATION_ID = '10000000-0000-4000-8000-000000000002'
const BASE_CHART = { name: 'N', birth_date: '1984-02-05', birth_place: 'P', client_id: 'owner-uid', owner_id: 'owner-uid' }
const ARCHIVE: ConversationSummary = {
  id: CONVERSATION_ID, chart_id: CHART_ID, user_id: 'owner-uid', module: 'consume', title: 'T',
  created_at: '', updated_at: '', archived_at: '2026-09-27', archive_reason: 'chart_details_changed',
  archived_chart_snapshot: null, archived_by_run_id: null,
}
const ACTIVE: ConversationSummary = { ...ARCHIVE, archived_at: null, archive_reason: null }

function seed({ chart = BASE_CHART, conversation = ARCHIVE, role = 'guest', viewGrant = false } = {}) {
  mockQuery.mockImplementation(async (sql: string, params: unknown[]) => {
    if (/FROM profiles/.test(sql)) return { rows: [{ role }] }
    if (/FROM charts/.test(sql) && params[0] === CHART_ID) return { rows: [chart] }
    if (/FROM chart_grants/.test(sql) && params[0] === CHART_ID && params[1] === 'owner-uid') {
      return { rows: viewGrant ? [{ permission: 'view' }] : [] }
    }
    if (/FROM conversations WHERE id/.test(sql) && params[0] === CONVERSATION_ID) return { rows: [conversation] }
    if (/FROM conversations c/.test(sql)) return { rows: [] }
    throw new Error(`Unexpected query: ${sql}`)
  })
}

async function renderPage() {
  render(await Page({ params: Promise.resolve({ id: CHART_ID, conversationId: CONVERSATION_ID }) }))
}

beforeEach(() => {
  vi.clearAllMocks()
  seed()
  mockLoadV2.mockResolvedValue([])
  mockLoadHistorical.mockResolvedValue([{ id: 'm1', role: 'user', text: 'old question', createdAt: '' }])
})

describe('consult conversation page', () => {
  it('renders the read-only historical view for a correction archive, with no composer', async () => {
    await renderPage()
    expect(screen.getByTestId('historical-view')).toHaveTextContent('old question')
    expect(screen.queryByTestId('consume-chat')).not.toBeInTheDocument()
    expect(mockLoadHistorical).toHaveBeenCalledWith(CONVERSATION_ID)
    expect(mockLoadV2).not.toHaveBeenCalled()
  })

  it('keeps the existing chat for an active conversation', async () => {
    seed({ conversation: ACTIVE })
    await renderPage()
    expect(screen.getByTestId('consume-chat')).toBeInTheDocument()
    expect(mockLoadHistorical).not.toHaveBeenCalled()
  })

  it.each([
    { access: 'chart ownership', owner_id: 'owner-uid', viewGrant: false },
    { access: 'a chart view grant', owner_id: 'another-uid', viewGrant: true },
  ])('opens the guest’s own correction archive through $access when they are not the chart client', async ({ owner_id, viewGrant }) => {
    seed({ chart: { ...BASE_CHART, client_id: 'another-uid', owner_id }, viewGrant })
    await renderPage()
    expect(screen.getByTestId('historical-view')).toHaveTextContent('old question')
    expect(screen.queryByTestId('consume-chat')).not.toBeInTheDocument()
  })

  it('refuses correction history after chart access is revoked even when the guest is still the chart client', async () => {
    seed({ chart: { ...BASE_CHART, owner_id: 'another-uid' } })
    await expect(renderPage()).rejects.toThrow('NEXT_REDIRECT:/dashboard')
    expect(mockLoadHistorical).not.toHaveBeenCalled()
  })

  it('refuses another user’s correction archive even when the guest owns the chart', async () => {
    seed({ conversation: { ...ARCHIVE, user_id: 'another-uid' } })
    await expect(renderPage()).rejects.toThrow('NEXT_NOT_FOUND')
    expect(mockLoadHistorical).not.toHaveBeenCalled()
  })

  it('preserves super-admin access to another user’s correction archive', async () => {
    seed({
      chart: { ...BASE_CHART, client_id: 'another-uid', owner_id: 'another-uid' },
      conversation: { ...ARCHIVE, user_id: 'another-uid' },
      role: 'super_admin',
    })
    await renderPage()
    expect(screen.getByTestId('historical-view')).toHaveTextContent('old question')
  })

  it('does not open the legacy active chat using a view grant alone', async () => {
    seed({
      chart: { ...BASE_CHART, client_id: 'another-uid', owner_id: 'another-uid' },
      conversation: ACTIVE,
      viewGrant: true,
    })
    await expect(renderPage()).rejects.toThrow('NEXT_REDIRECT:/dashboard')
    expect(mockLoadV2).not.toHaveBeenCalled()
  })
})
