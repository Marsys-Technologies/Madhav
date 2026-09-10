import { beforeEach, describe, expect, it, vi } from 'vitest'
import { Pool } from 'pg'

import {
  listRemediesByCategory,
  queryMantras,
  queryRemedies,
  queryRemediesByPlanet,
  queryRemediesForChart,
  queryTantricRemedies,
  readRemedy,
} from '../remedy_tools'
import type { QueryPlan, RetrievalTool } from '../types'

const queryMock = vi.spyOn(Pool.prototype, 'query')
const endMock = vi.spyOn(Pool.prototype, 'end')

const plan: QueryPlan = {
  query_plan_id: 'remedy-serving-test',
  query_text: 'test',
  query_class: 'remedial',
  domains: [],
  forward_looking: false,
  audience_tier: 'client',
  tools_authorized: [],
  history_mode: 'research',
  panel_mode: false,
  expected_output_shape: 'structured_data',
  manifest_fingerprint: 'test',
  schema_version: '1.0',
}

async function invoke(tool: RetrievalTool, params?: Record<string, unknown>) {
  await tool.retrieve(plan, params)
  const call = queryMock.mock.calls.at(-1)
  if (!call) throw new Error('expected a database query')
  const sql = call[0] as string
  const values = call[1] as unknown[]
  return { sql, values }
}

describe('legacy remedy serving guards', () => {
  beforeEach(() => {
    queryMock.mockReset()
    queryMock.mockResolvedValue({ rows: [] } as never)
    endMock.mockReset()
    endMock.mockResolvedValue(undefined)
    vi.stubEnv('DATABASE_URL', 'postgres://remedy-test.invalid/test')
  })

  it('never queries a review or rejected corpus row through any remedy serving tool', async () => {
    const requests: Array<[RetrievalTool, Record<string, unknown>]> = [
      [queryRemedies, { planet: 'SATURN' }],
      [queryRemediesForChart, { affliction: 'SATURN' }],
      [listRemediesByCategory, { category: 'mantras' }],
      [readRemedy, { remedy_id: 'review-row' }],
      [queryTantricRemedies, { planet: 'SATURN' }],
      [queryRemediesByPlanet, { planet: 'SATURN' }],
      [queryMantras, { planet: 'SATURN' }],
    ]
    const queries = []
    for (const [tool, params] of requests) {
      queries.push(await invoke(tool, params))
    }

    for (const { sql } of queries) {
      expect(sql).toContain("scaffold_status = 'live'")
    }
  })

  it.each([
    [queryRemedies, { planet: 'SATURN' }],
    [queryTantricRemedies, { planet: 'SATURN' }],
    [queryRemediesByPlanet, { planet: 'SATURN' }],
    [queryMantras, { planet: 'SATURN' }],
  ])('normalizes the planet predicate for %s', async (tool, params) => {
    const { sql, values } = await invoke(tool, params)

    expect(sql).toMatch(/LOWER\(planet\) = \$\d+/)
    expect(values).toContain('saturn')
  })
})
