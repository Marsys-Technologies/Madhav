import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('server-only', () => ({}))
const mocks = vi.hoisted(() => ({
  prepare: vi.fn(), release: vi.fn(), stream: vi.fn(), cancelled: vi.fn(),
}))
vi.mock('ai', () => ({
  createUIMessageStream: ({ execute }: { execute: unknown }) => ({ execute }),
  createUIMessageStreamResponse: ({ stream }: { stream: unknown }) => ({ stream }),
  streamText: vi.fn(),
}))
vi.mock('@/lib/firebase/server', () => ({ getServerUser: vi.fn(async () => ({ uid: 'alice' })) }))
vi.mock('@/lib/db/client', () => ({ query: vi.fn(async () => ({ rows: [{ role: 'guest', status: 'active' }] })) }))
vi.mock('@/lib/conversations', () => ({ getConversation: vi.fn(async () => ({ chart_id: crypto.randomUUID() })) }))
vi.mock('@/lib/persistence/conversation_writer', () => ({ loadConversationMessagesV2: vi.fn(async () => [
  { role: 'user', parts: [{ type: 'text', text: 'Continue this reading' }] },
]) }))
vi.mock('@/lib/errors', () => ({ res: {
  unauthenticated: vi.fn(), badRequest: vi.fn(), dbError: vi.fn(), notFound: vi.fn(),
} }))
vi.mock('@/lib/config', () => ({ configService: { getFlag: () => true } }))
vi.mock('@/lib/ai-console/repository', () => ({ getConversationSelection: vi.fn(async () => ({ kind: 'default' })) }))
vi.mock('@/lib/pariprashna/pipeline/byok_preflight', () => ({ prepareByokTurn: mocks.prepare }))
vi.mock('@/lib/models/runtime_config', () => ({ getEffectiveModel: vi.fn() }))
vi.mock('@/lib/models/resolver', () => ({ resolveModel: vi.fn() }))

import { POST } from '../route'

describe('consult continuation BYOK lifecycle', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mocks.stream.mockImplementation((request: unknown) => {
      expect(request).toMatchObject({ maxOutputTokens: 16_384 })
      return new ReadableStream({
        start(controller) { controller.enqueue({ type: 'text_delta', text: 'continued' }) },
        cancel: mocks.cancelled,
      })
    })
    mocks.prepare.mockResolvedValue({
      kind: 'byok', releaseAdmission: mocks.release,
      executors: { synthesizer: { stream: mocks.stream } },
    })
  })

  it('cancels an unfinished reader and releases once when the writer fails mid-stream', async () => {
    const response = await POST(new Request('http://local/api/chat/consult/continue', {
      method: 'POST', body: JSON.stringify({ conversation_id: crypto.randomUUID(), last_message_id: crypto.randomUUID() }),
    })) as unknown as { stream: { execute(args: { writer: { write(event: unknown): void } }): Promise<void> } }
    let writes = 0
    await response.stream.execute({ writer: { write: () => {
      writes++
      if (writes === 3) throw new Error('writer failed')
    } } })
    expect(mocks.cancelled).toHaveBeenCalledOnce()
    expect(mocks.release).toHaveBeenCalledOnce()
  })
})
