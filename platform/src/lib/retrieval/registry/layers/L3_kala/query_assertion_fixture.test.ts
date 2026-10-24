import { existsSync } from 'node:fs'
import { beforeEach, expect, it, vi } from 'vitest'

const queryMock = vi.hoisted(() => vi.fn())
vi.mock('@/lib/db/client', () => ({ query: queryMock }))

beforeEach(() => {
  vi.unstubAllEnvs()
  queryMock.mockReset()
})

async function capability() {
  expect(existsSync(new URL('./query_assertion_fixture.ts', import.meta.url))).toBe(true)
  return (await import('./query_assertion_fixture')).queryAssertionFixtureCapability
}

it('requires the server fixture flag before accessing candidate data', async () => {
  const cap = await capability()
  vi.stubEnv('KALA_ASSERTION_FIXTURE_ENABLED', '0')
  const result = await cap.handler!({ chart_id: 'chart', generation: 'candidate-a' }, {})
  expect(result.is_error).toBe(true)
  expect(queryMock).not.toHaveBeenCalled()
})

it('requires an explicit generation and never invents current', async () => {
  const cap = await capability()
  vi.stubEnv('KALA_ASSERTION_FIXTURE_ENABLED', '1')
  expect((await cap.handler!({ chart_id: 'chart' }, {})).is_error).toBe(true)
  expect(queryMock).not.toHaveBeenCalled()
})

it('returns the SQL-projected typed state and source references unchanged', async () => {
  const cap = await capability()
  vi.stubEnv('KALA_ASSERTION_FIXTURE_ENABLED', '1')
  queryMock.mockResolvedValue({ rows: [{ assertion_id: 'negative:window:11',
    candidate_effective_state: 'obstruction_cancelled', source_assertion_ids: ['negative:window:11'],
    record_ids: ['11'], assertion: { payload: { release: { kind: 'unknown' } } } }] })
  const result = await cap.handler!({ chart_id: 'chart', generation: 'candidate-a' }, {})
  expect(result.content).toMatchObject({ generation: 'candidate-a', assertions: [
    { candidate_effective_state: 'obstruction_cancelled', record_ids: ['11'] },
  ] })
  expect(queryMock.mock.calls[0][1]).toEqual(['chart', 'candidate-a'])
})

it('is registered as the gated L3 rehearsal capability', async () => {
  const cap = await capability()
  vi.stubEnv('KALA_ASSERTION_FIXTURE_ENABLED', '1')
  await import('./index')
  const { getCapability } = await import('../../index')
  expect(getCapability(cap.uri)?.handler).toBe(cap.handler)
})

it('legacy capabilities exclude all candidate rows from both data and counts', async () => {
  queryMock.mockResolvedValue({ rows: [] })
  const { queryTemporalViewCapability } = await import('./query_temporal_view')
  const { queryObstructionPeriodsCapability } = await import('./query_obstruction_periods')
  await queryTemporalViewCapability.handler!({ chart_id: 'chart' }, {})
  await queryObstructionPeriodsCapability.handler!({ chart_id: 'chart' }, {})
  // temporal view: the legacy NULL partition; obstruction periods (SR-K9-WRITE-SCOPE): the served partition, never a candidate.
  const sqls = queryMock.mock.calls.map(([sql]) => sql as string)
  const obstruction = sqls.filter(sql => sql.includes('FROM kala_obstruction'))
  // page + total + the SR-EMPTY-REASON layer-state probe an empty result triggers. The page and total read only the served
  // partition; the probe is one statement that also counts the chart's rows in ANY partition (by design: that count is how it
  // tells "rows only in a candidate" from "nothing built"), beside a served-partition count, which carries the predicate asserted below.
  expect(obstruction.length).toBe(3)
  for (const sql of sqls.filter(sql => !obstruction.includes(sql))) expect(sql).toContain('generation IS NULL')
  for (const sql of obstruction) expect(sql).toContain('o.generation IS NOT DISTINCT FROM (SELECT h.generation FROM kala_layer_head h')
})
