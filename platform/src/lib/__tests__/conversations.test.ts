/**
 * V3-E-012a (Paripraśna v3 assurance, stream S1): `listConversations`'s
 * `readingsOnly` option must default OFF (byte-identical query to before it
 * existed, for the legacy consume `ArchivedView.tsx` caller) and, when ON,
 * add an EXISTS filter keyed on the receipt discriminator
 * (`conversation_messages.metadata_json ? 'acharya_reading_receipt'`) rather
 * than any heuristic on `module` (which both Paripraśna and legacy
 * consume/consult share) — Native Surrogate ruling B1, decision event
 * `f3b88219-432f-4096-999c-07f6700f6406`.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))
vi.mock('server-only', () => ({}))

import { listConversations } from '@/lib/conversations'

beforeEach(() => {
  mockQuery.mockReset()
  mockQuery.mockResolvedValue({ rows: [] })
})

describe('listConversations — readingsOnly (V3-E-012a)', () => {
  it('defaults readingsOnly to false and issues no EXISTS/receipt clause', async () => {
    await listConversations({ chartId: 'c-1', userId: 'u-1', module: 'consume' })
    const [sql] = mockQuery.mock.calls[0]
    expect(sql).not.toMatch(/acharya_reading_receipt/)
    expect(sql).not.toMatch(/EXISTS/i)
  })

  it('adds the receipt-existence filter only when readingsOnly is true', async () => {
    await listConversations({ chartId: 'c-1', userId: 'u-1', module: 'consume', readingsOnly: true })
    const [sql] = mockQuery.mock.calls[0]
    expect(sql).toMatch(/EXISTS/i)
    expect(sql).toMatch(/acharya_reading_receipt/)
    expect(sql).toMatch(/role = 'assistant'/)
  })

  it('does not filter on module beyond the existing $3 param — the discriminator is the receipt, not module', async () => {
    await listConversations({ chartId: 'c-1', userId: 'u-1', module: 'consume', readingsOnly: true })
    const [sql, params] = mockQuery.mock.calls[0]
    // module is still bound as the existing positional param (unchanged
    // contract) — the NEW filter is the EXISTS clause, not a second module check.
    expect(params).toEqual(['c-1', 'u-1', 'consume'])
    expect((sql.match(/module\s*=\s*\$3/g) ?? []).length).toBe(1)
  })

  it('returns first_message_snippet as an additive field, never mutating title', async () => {
    mockQuery.mockResolvedValueOnce({
      rows: [
        {
          id: 't-1',
          chart_id: 'c-1',
          user_id: 'u-1',
          module: 'consume',
          title: null,
          created_at: '2026-08-28T00:00:00Z',
          updated_at: null,
          archived_at: null,
          first_message_snippet: 'What does this period ask of my career?',
        },
      ],
    })
    const result = await listConversations({ chartId: 'c-1', userId: 'u-1', module: 'consume', readingsOnly: true })
    expect(result[0].title).toBeNull()
    expect(result[0].first_message_snippet).toBe('What does this period ask of my career?')
  })

  it('reports first_message_snippet as null (never undefined/omitted) when absent', async () => {
    mockQuery.mockResolvedValueOnce({
      rows: [
        {
          id: 't-1', chart_id: 'c-1', user_id: 'u-1', module: 'consume', title: 'Renamed',
          created_at: '2026-08-28T00:00:00Z', updated_at: null, archived_at: null, first_message_snippet: null,
        },
      ],
    })
    const result = await listConversations({ chartId: 'c-1', userId: 'u-1', module: 'consume' })
    expect(result[0].first_message_snippet).toBeNull()
  })
})
