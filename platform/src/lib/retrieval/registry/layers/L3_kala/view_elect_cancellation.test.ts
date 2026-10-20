/** KA-4b: the ELECT view reads scoped cancellation beside the unchanged stored-stage response. */
import { beforeEach, expect, it, vi } from 'vitest'
const db = vi.hoisted(() => vi.fn())
vi.mock('@/lib/db/client', () => ({ query: db }))
import { makeElectView, electViewCapability } from './view_elect'

const stageArgs = { chart_id: 'chart', event_class: 'marriage', date_from: '2026-11-20T00:00:00Z', date_to: '2026-11-21T00:00:00Z' }
const cancelled = {
  evaluator_version: '1', sky_coverage: { basis: 'start_mid_end_samples', complete: true },
  rules: [{ rule_id: 101, dosha_canonical_id: 'venus_sixth', scope: 'marriage', source_citation: 'Muhūrta Cintāmaṇi, Vivāha v.88 (PG116:C1)',
    source_chunk_id: 'muhurta_chintamani_pg0116_c01', source_verse: 88, extraction_context: 'tika_commentary', result: 'applies', reason: null }],
  dosas: [{ dosha_canonical_id: 'venus_sixth', state: 'cancelled', reason: null, by_rules: [101] }],
}
const scoped = (undertaking: string) => ({ undertaking, candidate: { start_utc: '2026-11-20T04:00:00Z', end_utc: '2026-11-20T06:00:00Z' },
  location: { lat: 20.27, lon: 85.84, tz_offset_minutes: 330 }, dosas_present: ['venus_sixth'] })
beforeEach(() => db.mockReset().mockResolvedValue({ rows: [{ manifest: { manifest_id: 'build', generation: '4.1' }, coverage: [], sources: [] }] }))

it('without scoped_cancellation the response is the unchanged stored-stage envelope', async () => {
  const result = await electViewCapability.handler!(stageArgs, {})
  expect(result.is_error).toBe(false)
  expect(result.content).not.toHaveProperty('scoped_cancellation')
  expect(result.content).toMatchObject({ view: 'elect', manifest_id: 'build' })
  expect(electViewCapability.name).toBe('elect_read')
  expect(electViewCapability.uri).toBe('marsys://tool/L3/elect_read')
})
it('an in-scope request reads cancelled with its locator beside the stage rows', async () => {
  const evaluate = vi.fn().mockResolvedValue(cancelled)
  const result = await makeElectView(evaluate).handler!({ ...stageArgs, scoped_cancellation: scoped('marriage') }, {})
  expect(evaluate).toHaveBeenCalledTimes(1)
  expect(result.content).toMatchObject({ view: 'elect', manifest_id: 'build', scoped_cancellation: { in_scope: true,
    dosas: [{ dosha_canonical_id: 'venus_sixth', state: 'cancelled', citations: [{ source_chunk_id: 'muhurta_chintamani_pg0116_c01', source_verse: 88 }] }] } })
})
it('an out-of-scope undertaking reads cancellation_unassessed and does not call the producer', async () => {
  const evaluate = vi.fn().mockResolvedValue(cancelled)
  const result = await makeElectView(evaluate).handler!({ ...stageArgs, scoped_cancellation: scoped('business') }, {})
  expect(evaluate).not.toHaveBeenCalled()
  expect(result.content).toMatchObject({ scoped_cancellation: { in_scope: false,
    dosas: [{ state: 'cancellation_unassessed', reason: 'undertaking_out_of_scope' }] } })
})
it('an invalid scoped request is refused before any stored read', async () => {
  const result = await makeElectView(vi.fn()).handler!({ ...stageArgs, scoped_cancellation: { ...scoped('marriage'), dosas_present: ['*'] } }, {})
  expect(result.is_error).toBe(true)
  expect(result.content).toMatchObject({ empty_reason: 'invalid_request' })
  expect(db).not.toHaveBeenCalled()
})
