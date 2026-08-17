import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('@/lib/db/client', () => ({ query: vi.fn() }))

import { query } from '@/lib/db/client'
import { clearRegistry } from '../../index'
import { registerD7ChannelCapabilities } from '../register_d7_channel'
import { getToolByName } from '../../tool_name_bridge'

const mockQuery = vi.mocked(query)

describe('list_remedies_by_category pagination', () => {
  beforeEach(() => {
    clearRegistry()
    registerD7ChannelCapabilities()
    mockQuery.mockReset()
  })

  it('uses the requested page and declares the stable total without serializing an unbounded category', async () => {
    const pageRow = { remedy_id: 'mars-mantra', planet: 'mars', category: 'mantras' }
    mockQuery
      .mockResolvedValueOnce({ rows: [pageRow] } as never)
      .mockResolvedValueOnce({ rows: [{ total: 3 }] } as never)

    const tool = getToolByName('list_remedies_by_category')!
    const bundle = await tool.retrieve({}, { category: 'mantras', limit: 1, offset: 1 })

    expect(mockQuery).toHaveBeenCalledTimes(2)
    expect(mockQuery).toHaveBeenNthCalledWith(
      1,
      expect.stringContaining('LIMIT $3 OFFSET $4'),
      ['mantra', 'mantras', 1, 1],
    )
    expect(mockQuery).toHaveBeenNthCalledWith(
      2,
      expect.stringContaining('COUNT(*)::int AS total'),
      ['mantra', 'mantras'],
    )
    const content = JSON.parse(bundle.results[0]!.content) as Record<string, unknown>
    expect(content).toEqual({
      category: 'mantras',
      remedies: [pageRow],
      returned_count: 1,
      pagination: {
        limit: 1,
        offset: 1,
        total: 3,
        more_available: true,
        next_offset: 2,
      },
    })
    expect(bundle.results[0]!.content).not.toContain('[truncated for budget]')
  })
})
