/**
 * Legacy consult persistence boundary (Jātaka Phase-A hardening, item 5).
 * runAdapterDispatch hands the shared write-through a guard bound to the
 * dispatch's own conversation and chart, so the same final recheck that the
 * Paripraśna race test proves also guards the legacy door.
 */
import { describe, expect, it, vi } from 'vitest'

vi.mock('server-only', () => ({}))
const { mockCheck } = vi.hoisted(() => ({ mockCheck: vi.fn() }))
vi.mock('@/lib/conversations/writeGuard', () => ({ checkConversationWritable: mockCheck }))

import { legacyConsultWriteGuard } from '../run_adapter_dispatch'

describe('legacyConsultWriteGuard', () => {
  it('re-checks the dispatch’s own conversation and chart at persistence time', async () => {
    mockCheck.mockResolvedValue({ ok: false, code: 'CONVERSATION_ARCHIVED_READ_ONLY', message: 'm' })
    const guard = legacyConsultWriteGuard({ finalConversationId: 'conv-9', chartId: 'chart-9' })
    expect(mockCheck).not.toHaveBeenCalled() // evaluated lazily, at the boundary
    expect(await guard()).toMatchObject({ ok: false, code: 'CONVERSATION_ARCHIVED_READ_ONLY' })
    expect(mockCheck).toHaveBeenCalledWith({ conversationId: 'conv-9', chartId: 'chart-9' })
  })
})
