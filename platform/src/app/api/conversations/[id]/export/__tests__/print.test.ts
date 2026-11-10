import { beforeEach, describe, expect, it, vi } from 'vitest'
import { GET } from '../route'

const mocks = vi.hoisted(() => ({
  getServerUser: vi.fn(),
  getConversation: vi.fn(),
  loadConversationMessagesV2: vi.fn(),
}))

vi.mock('@/lib/firebase/server', () => ({ getServerUser: mocks.getServerUser }))
vi.mock('@/lib/conversations', () => ({ getConversation: mocks.getConversation }))
vi.mock('@/lib/persistence/conversation_writer', () => ({
  loadConversationMessagesV2: mocks.loadConversationMessagesV2,
}))
vi.mock('@/lib/db/client', () => ({ query: vi.fn().mockResolvedValue({ rows: [{ role: 'guest' }] }) }))

const id = 'aaaaaaaa-0000-4000-8000-000000000001'

function printConversation() {
  return GET(new Request(`http://localhost/api/conversations/${id}/export?format=print`), {
    params: Promise.resolve({ id }),
  })
}

describe('print conversation', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mocks.getServerUser.mockResolvedValue({ uid: 'test-reader' })
    mocks.getConversation.mockResolvedValue({ id, title: 'Reading <example>' })
    mocks.loadConversationMessagesV2.mockResolvedValue([
      { role: 'user', parts: [{ type: 'text', text: 'My question' }] },
      { role: 'assistant', parts: [{ type: 'text', text: 'Answer <example> & result' }] },
    ])
  })

  it('renders the authorized transcript with text escaped and caching disabled', async () => {
    const response = await printConversation()
    expect(response.status).toBe(200)
    expect(response.headers.get('content-type')).toMatch(/^text\/html/)
    expect(response.headers.get('cache-control')).toContain('no-store')
    expect(mocks.loadConversationMessagesV2).toHaveBeenCalledWith(id, { includeCanonicalText: true })
    const html = await response.text()
    expect(html).toContain('Reading &lt;example&gt;')
    expect(html).toContain('My question')
    expect(html).toContain('Answer &lt;example&gt; &amp; result')
  })

  it('keeps the transcript private when the requester is not its owner', async () => {
    mocks.getConversation.mockResolvedValue(null)
    expect((await printConversation()).status).toBe(404)
    expect(mocks.loadConversationMessagesV2).not.toHaveBeenCalled()
  })
})
