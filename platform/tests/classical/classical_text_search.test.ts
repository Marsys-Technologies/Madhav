// classical_text_search — unit test; DB calls are mocked so CI has no real connection.
import { describe, it, expect, vi } from 'vitest'

vi.mock('server-only', () => ({}))
vi.mock('@/lib/db/client', () => ({
  query: vi.fn().mockResolvedValue({ rows: [] }),
}))

import { classical_text_search } from '@/lib/tools/classical_text_search'

describe('classical_text_search (stub)', () => {
  it('returns empty results', async () => {
    const result = await classical_text_search({ query: 'Rahu in 7th house' })
    expect(result.results).toHaveLength(0)
    expect(result.total).toBe(0)
  })
})
