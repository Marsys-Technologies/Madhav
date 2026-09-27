/**
 * get_strength optional build fence (Pūrṇa R3 / RC-7 proof typing, strength group).
 *
 * Composing callers (query_planet, graha_portrait) pass the chart's served build set so every
 * strength read resolves to one generation; a standalone call omits it and reads unfenced, as
 * before this fix.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'

const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

import { getStrengthCapability } from '../get_strength'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const SERVED = '11111111-1111-4111-8111-111111111111'

beforeEach(() => {
  mockQuery.mockReset()
  mockQuery.mockResolvedValue({ rows: [] })
})

function chartFactsCalls(): Array<{ sql: string; params: unknown[] }> {
  return mockQuery.mock.calls
    .map(([sql, params]) => ({ sql: String(sql), params: (params ?? []) as unknown[] }))
    .filter(({ sql }) => sql.includes('FROM chart_facts'))
}

describe('get_strength build fence', () => {
  it('binds the served build set at its own placeholder in the count, page, and frame-position reads', async () => {
    const result = await getStrengthCapability.handler(
      { chart_id: CHART_ID, build_id: [SERVED], frame: 'chandra' }, undefined,
    )
    expect(result.is_error).toBe(false)
    const calls = chartFactsCalls()
    expect(calls.length).toBeGreaterThanOrEqual(3)
    for (const { sql, params } of calls) {
      const match = sql.match(/build_id = ANY\(\$(\d+)::uuid\[\]\)/)
      expect(match, sql).not.toBeNull()
      expect(params[Number(match![1]) - 1], sql).toEqual([SERVED])
    }
  })

  it('leaves standalone reads unfenced when no build set is supplied', async () => {
    const result = await getStrengthCapability.handler({ chart_id: CHART_ID, frame: 'chandra' }, undefined)
    expect(result.is_error).toBe(false)
    for (const { sql } of chartFactsCalls()) expect(sql).not.toContain('build_id')
  })
})
