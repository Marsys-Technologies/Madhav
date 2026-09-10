/**
 * f_kala_1_query_temporal_activation_order_by.test.ts — F-KALA-1
 * (L3_W1_ANALYSIS_BATCH_E.md, ka_kalasutra finding 1), second call site.
 *
 * THE DEFECT: query_temporal_activation's fetch SQL ordered candidate rows
 * `ORDER BY orb_strength DESC NULLS LAST, activation_start, id` before applying
 * `LIMIT top_k`. `orb_strength` is 99.6% NULL (measured) — `ka_sangam` only produces
 * windows for <=260 of ~50,104 activation predicates — so which rows survive the LIMIT
 * was decided by `activation_start`/`id` for nearly every chart, not by any real
 * strength signal, even though the SQL itself was already fully deterministic (unlike the
 * Python F-VIGHNA-3 case — this is "meaningless ranking", not "build-to-build
 * nondeterminism").
 *
 * THE FIX: `dasha_activation_proximity_score` (0% NULL, [0,1], higher = stronger) added
 * as the PRIMARY sort key ahead of `orb_strength`, which stays as a secondary tiebreak
 * for the rows `ka_sangam` genuinely covers; `activation_start, id` remain the final
 * deterministic tiebreak.
 *
 * DB is mocked (vi.mock('@/lib/db/client')) — assertions are against the SQL actually
 * built, matching the sibling wp13e_temporal_date_honoring.test.ts convention.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

const queryMock = vi.fn()
vi.mock('@/lib/db/client', () => ({
  query: (...args: unknown[]) => queryMock(...args),
}))

import { queryTemporalActivationCapability } from '../layers/L3_kala/query_temporal_activation'

const CHART_ID = '11111111-aaaa-4aaa-aaaa-aaaaaaaaaaaa'

const DATED_ROW = {
  id: 'act-1',
  signal_id: 'sig-1',
  ayanamsha_id: 'lahiri_chitrapaksha',
  signature_class: 'x',
  activation_start: '2020-01-01',
  activation_end: '2021-01-01',
  activation_peak_date: '2020-06-01',
  orb_strength: 0.9,
  dasha_activation_proximity_score: 0.7,
}

beforeEach(() => {
  queryMock.mockReset()
})

describe('F-KALA-1 — query_temporal_activation ORDER BY ranks on dasha_activation_proximity_score first', () => {
  it('the activation-fetch SQL leads its ORDER BY with dasha_activation_proximity_score DESC NULLS LAST', async () => {
    queryMock
      .mockResolvedValueOnce({ rows: [DATED_ROW] }) // activation query
      .mockResolvedValueOnce({ rows: [] })          // predicates query
    await queryTemporalActivationCapability.handler({ chart_id: CHART_ID }, undefined)
    const [sql] = queryMock.mock.calls[0] as [string, unknown[]]
    expect(sql).toMatch(
      /ORDER BY\s+dasha_activation_proximity_score DESC NULLS LAST,\s*\n\s*orb_strength DESC NULLS LAST, activation_start, id/,
    )
  })

  it('orb_strength survives as a secondary tiebreak (real signal is not discarded)', async () => {
    queryMock
      .mockResolvedValueOnce({ rows: [DATED_ROW] })
      .mockResolvedValueOnce({ rows: [] })
    await queryTemporalActivationCapability.handler({ chart_id: CHART_ID }, undefined)
    const [sql] = queryMock.mock.calls[0] as [string, unknown[]]
    const orderByIdx = sql.indexOf('ORDER BY')
    const proximityIdx = sql.indexOf('dasha_activation_proximity_score DESC')
    const orbIdx = sql.indexOf('orb_strength DESC')
    expect(orderByIdx).toBeGreaterThan(-1)
    expect(proximityIdx).toBeGreaterThan(orderByIdx)
    expect(orbIdx).toBeGreaterThan(proximityIdx)
  })

  it('activation_start and id remain the final deterministic tiebreak', async () => {
    queryMock
      .mockResolvedValueOnce({ rows: [DATED_ROW] })
      .mockResolvedValueOnce({ rows: [] })
    await queryTemporalActivationCapability.handler({ chart_id: CHART_ID }, undefined)
    const [sql] = queryMock.mock.calls[0] as [string, unknown[]]
    expect(sql).toMatch(/orb_strength DESC NULLS LAST, activation_start, id\s*\n\s*LIMIT/)
  })

  it('unrelated WHERE/date-param behavior is unaffected by the ORDER BY change (sanity)', async () => {
    queryMock
      .mockResolvedValueOnce({ rows: [DATED_ROW] })
      .mockResolvedValueOnce({ rows: [] })
    const res = await queryTemporalActivationCapability.handler(
      { chart_id: CHART_ID, as_of: '2020-06-15' }, undefined,
    )
    const [sql, params] = queryMock.mock.calls[0] as [string, unknown[]]
    expect(sql).toMatch(/activation_start <= \$\d+::date/)
    expect(params).toContain('2020-06-15')
    const content = (res as { content: Record<string, unknown> }).content
    expect((content['date_filter'] as Record<string, unknown>)['mode']).toBe('point_in_time')
  })
})
