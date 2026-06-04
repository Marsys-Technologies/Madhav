// classical_text_search stubbed in WS-0C-2 (classical_chunks/classical_texts dropped WS-0).
import { describe, it, expect } from 'vitest'

import { classical_text_search } from '@/lib/tools/classical_text_search'

describe('classical_text_search (stub)', () => {
  it('returns empty results', async () => {
    const result = await classical_text_search({ query: 'Rahu in 7th house' })
    expect(result.results).toHaveLength(0)
    expect(result.total).toBe(0)
  })
})
