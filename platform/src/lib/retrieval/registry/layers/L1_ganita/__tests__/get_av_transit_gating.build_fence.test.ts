/**
 * get_av_transit_gating optional build fence — sav_bav_gating mode only (Pūrṇa R3 / RC-7
 * proof typing, per-mode facets). The kakshya_windows mode makes a live sidecar transit
 * fetch and is outside this fence's scope (see the source_query contract's own review note).
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'

const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

import { getAvTransitGatingCapability } from '../get_av_transit_gating'

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

describe('get_av_transit_gating sav_bav_gating build fence', () => {
  it('binds the served build set at its own placeholder in both reads', async () => {
    const result = await getAvTransitGatingCapability.handler({ chart_id: CHART_ID, build_id: [SERVED] }, undefined)
    expect(result.is_error).toBe(false)
    const calls = chartFactsCalls()
    expect(calls.length).toBeGreaterThanOrEqual(2)
    for (const { sql, params } of calls) {
      const match = sql.match(/build_id = ANY\(\$(\d+)::uuid\[\]\)/)
      expect(match, sql).not.toBeNull()
      expect(params[Number(match![1]) - 1], sql).toEqual([SERVED])
    }
  })

  it('leaves standalone reads unfenced when no build set is supplied', async () => {
    const result = await getAvTransitGatingCapability.handler({ chart_id: CHART_ID }, undefined)
    expect(result.is_error).toBe(false)
    for (const { sql } of chartFactsCalls()) expect(sql).not.toContain('build_id')
  })
})
