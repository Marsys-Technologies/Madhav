import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

import { queryYogaCatalogCapability } from '../query_yoga_catalog'

// Type-narrow the handler for assertions on post-fix fields (total_matching, more_available).
// ToolResult.content is string | object; cast to the concrete success shape so TypeScript
// can verify the F-37 assertions without requiring inline `as` casts inside the it() blocks.
type YogaContent = { rows: unknown[]; total_matching: number; more_available: boolean }
type YogaResult = { is_error: boolean; content: YogaContent }
const handler = queryYogaCatalogCapability.handler as (
  args: Record<string, unknown>,
  ctx?: Record<string, unknown>
) => Promise<YogaResult>

describe('query_yoga_catalog: total_matching reflects COUNT(*), not rows.length (F-37)', () => {
  beforeEach(() => { mockQuery.mockReset() })

  it('total_matching > page size and more_available=true when catalog has more rows', async () => {
    const pageRows = Array.from({ length: 10 }, (_, i) => ({ id: i + 51, name_en: `Yoga ${i + 51}` }))
    // After fix: Promise.all fires two queries — page query first, count query second
    mockQuery.mockResolvedValueOnce({ rows: pageRows })
    mockQuery.mockResolvedValueOnce({ rows: [{ total: '175' }] })

    const result = await handler({ limit: 10, offset: 50 }, {})

    expect(result.is_error).toBe(false)
    expect(result.content.rows.length).toBe(10)
    expect(typeof result.content.total_matching).toBe('number')
    expect(result.content.total_matching).toBeGreaterThan(10)
    expect(result.content.more_available).toBe(true)
  })

  describe('recurrence guard', () => {
    beforeEach(() => {
      mockQuery.mockReset()
      // Each handler call fires two queries via Promise.all (page query + count query)
      // r1: limit=1, offset=0
      mockQuery.mockResolvedValueOnce({ rows: [{ id: 1, name_en: 'Yoga 1' }] })
      mockQuery.mockResolvedValueOnce({ rows: [{ total: '175' }] })
      // r2: limit=1, offset=100
      mockQuery.mockResolvedValueOnce({ rows: [{ id: 101, name_en: 'Yoga 101' }] })
      mockQuery.mockResolvedValueOnce({ rows: [{ total: '175' }] })
    })

    it('total_matching is independent of limit/offset (no regression to rows.length)', async () => {
      const r1 = await handler({ limit: 1, offset: 0 }, {})
      const r2 = await handler({ limit: 1, offset: 100 }, {})
      // Both pages: 1 row served, but total_matching must be the same large number
      expect(r1.content.rows.length).toBe(1)
      expect(r2.content.rows.length).toBe(1)
      expect(r1.content.total_matching).toEqual(r2.content.total_matching)
      expect(r1.content.total_matching).toBeGreaterThan(1)
      expect(r1.content.more_available).toBe(true)
    })
  })
})
