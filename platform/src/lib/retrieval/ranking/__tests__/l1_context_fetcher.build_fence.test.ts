/**
 * fetchL1Context's explicit-empty build-fence handling (R3 boundary, "explicit-empty
 * build-fence semantics"). This is the DISPLAY-only counterpart to the evidentiary leaf-tool
 * refusal tests: composite_ranker's numeric ranking signal, never evidence a user sees
 * directly, with generic fallbacks already in place for any read failure — the requirement
 * here is not "refuse", it's "never silently bind an explicit-empty fence to zero rows and
 * call that the same as an absent fence" — the omission must be disclosed via
 * `generation_fence`, not indistinguishable from an ordinary unfenced call.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'

const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

import { fetchL1Context } from '../l1_context_fetcher'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const AYANAMSHA = 'lahiri_chitrapaksha'
const AS_OF = '2026-09-28'
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

describe('fetchL1Context served-generation fence disclosure', () => {
  it('binds a resolved fence and discloses fenced: true', async () => {
    const ctx = await fetchL1Context(CHART_ID, AYANAMSHA, AS_OF, [SERVED])
    expect(ctx.generation_fence).toEqual({ fenced: true, explicit_empty: false })
    for (const { sql, params } of chartFactsCalls()) {
      const match = sql.match(/build_id = ANY\(\$(\d+)::uuid\[\]\)/)
      expect(match, sql).not.toBeNull()
      expect(params[Number(match![1]) - 1], sql).toEqual([SERVED])
    }
  })

  it('reads unfenced and discloses fenced: false, explicit_empty: false when no fence is supplied', async () => {
    const ctx = await fetchL1Context(CHART_ID, AYANAMSHA, AS_OF)
    expect(ctx.generation_fence).toEqual({ fenced: false, explicit_empty: false })
    for (const { sql } of chartFactsCalls()) expect(sql).not.toContain('build_id')
  })

  it('falls back to an unfenced read but discloses explicit_empty: true — never silently matches zero rows as if it were absent', async () => {
    const ctx = await fetchL1Context(CHART_ID, AYANAMSHA, AS_OF, [])
    expect(ctx.generation_fence).toEqual({ fenced: false, explicit_empty: true })
    for (const { sql } of chartFactsCalls()) expect(sql).not.toContain('build_id')
  })

  it('gives an explicit-empty fence its own cache key, distinct from absent', async () => {
    const distinctChartId = '5e2f9a10-1111-4222-8333-999999999999'
    await fetchL1Context(distinctChartId, AYANAMSHA, AS_OF)
    const afterAbsent = mockQuery.mock.calls.length
    const ctx = await fetchL1Context(distinctChartId, AYANAMSHA, AS_OF, [])
    // A shared cache key would return the absent-call's cached (fenced: false, explicit_empty:
    // false) result instead of running fresh queries and disclosing explicit_empty: true.
    expect(mockQuery.mock.calls.length).toBeGreaterThan(afterAbsent)
    expect(ctx.generation_fence).toEqual({ fenced: false, explicit_empty: true })
  })
})
