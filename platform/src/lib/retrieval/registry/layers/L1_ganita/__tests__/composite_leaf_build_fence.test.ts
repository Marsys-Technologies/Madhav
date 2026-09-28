/**
 * Optional served-generation build fence on the six chart_facts leaves that query_planet and
 * graha_portrait compose (Packet A of the fence-and-successor-envelope follow-up).
 *
 * Only get_strength and get_yoga_firings could be fenced before, so the composites read every other
 * leg from the chart's current rows even with a resolved generation. Each leaf now accepts the same
 * `build_id` fence get_strength does: a supplied build set binds every generation-scoped query, an
 * explicit-empty fence is refused (never read unfenced, never matched against zero rows), and a
 * standalone call that omits it is unchanged.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'

const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

import { getPositionsCapability } from '../get_positions'
import { getDignityCapability } from '../get_dignity'
import { getAvasthsCapability } from '../get_avasthas'
import { getAspectsCapability } from '../get_aspects'
import { getYogaDoshaCapability } from '../get_yoga_dosha'
import { getDispositorsCapability } from '../get_dispositors'
import type { CapabilityDescriptor } from '../../../types'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const SERVED = '11111111-1111-4111-8111-111111111111'
const OTHER = '22222222-2222-4222-8222-222222222222'

interface Leaf { name: string; capability: CapabilityDescriptor; args: Record<string, unknown> }
const LEAVES: readonly Leaf[] = [
  { name: 'get_positions', capability: getPositionsCapability, args: {} },
  { name: 'get_dignity', capability: getDignityCapability, args: {} },
  { name: 'get_avasthas', capability: getAvasthsCapability, args: {} },
  { name: 'get_aspects', capability: getAspectsCapability, args: {} },
  // facet=dosha_fires exercises the kala_sarpa side query as well as count, page, gated-count and firings.
  { name: 'get_yoga_dosha', capability: getYogaDoshaCapability, args: { facet: 'dosha_fires' } },
  { name: 'get_dispositors', capability: getDispositorsCapability, args: {} },
]

beforeEach(() => {
  mockQuery.mockReset()
  mockQuery.mockResolvedValue({ rows: [] })
})

/** Every read of a generation-scoped table this call issued. */
function generationScopedReads(): Array<{ sql: string; params: unknown[] }> {
  return mockQuery.mock.calls
    .map(([sql, params]) => ({ sql: String(sql), params: (params ?? []) as unknown[] }))
    .filter(({ sql }) => /FROM chart_facts|FROM ga_yoga_firings/.test(sql))
}

describe.each(LEAVES)('$name build fence', ({ capability, args, name }) => {
  it('declares the build_id input so planned dispatch can carry the fence', () => {
    expect(capability.input_schema).toHaveProperty('build_id')
  })

  it('binds the supplied served build set on EVERY generation-scoped read', async () => {
    const result = await capability.handler({ chart_id: CHART_ID, ...args, build_id: [SERVED] }, undefined)
    expect(result.is_error).toBe(false)
    const reads = generationScopedReads()
    expect(reads.length).toBeGreaterThan(0)
    for (const { sql, params } of reads) {
      const match = sql.match(/build_id = ANY\(\$(\d+)::uuid\[\]\)/)
      expect(match, `${name}: unfenced read -> ${sql}`).not.toBeNull()
      expect(params[Number(match![1]) - 1], sql).toEqual([SERVED])
    }
  })

  it('normalizes a scalar and a duplicated fence to the same canonical build set', async () => {
    const fenceOf = ({ sql, params }: { sql: string; params: unknown[] }) => {
      const match = sql.match(/build_id = ANY\(\$(\d+)::uuid\[\]\)/)
      return match ? params[Number(match[1]) - 1] : undefined
    }
    await capability.handler({ chart_id: CHART_ID, ...args, build_id: SERVED }, undefined)
    const scalar = generationScopedReads().map(fenceOf)
    mockQuery.mockClear()
    await capability.handler({ chart_id: CHART_ID, ...args, build_id: [OTHER, SERVED, SERVED] }, undefined)
    const many = generationScopedReads().map(fenceOf)
    expect(scalar.length).toBeGreaterThan(0)
    for (const set of scalar) expect(set).toEqual([SERVED])
    for (const set of many) expect(set).toEqual([SERVED, OTHER].sort())
  })

  it('refuses an explicit-empty fence without querying (never unfenced, never zero-row)', async () => {
    const result = await capability.handler({ chart_id: CHART_ID, ...args, build_id: [] }, undefined)
    expect(result.is_error).toBe(true)
    expect((result.content as Record<string, unknown>)['code']).toBe('explicit_empty_build_fence')
    expect(mockQuery).not.toHaveBeenCalled()
  })

  it('leaves a standalone call that omits build_id unfenced, exactly as before', async () => {
    const result = await capability.handler({ chart_id: CHART_ID, ...args }, undefined)
    expect(result.is_error).toBe(false)
    for (const { sql } of generationScopedReads()) expect(sql).not.toContain('build_id')
  })
})
