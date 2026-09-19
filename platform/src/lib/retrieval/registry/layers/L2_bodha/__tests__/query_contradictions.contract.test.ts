import { beforeEach, describe, expect, it, vi } from 'vitest'

const { queryMock } = vi.hoisted(() => ({ queryMock: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: queryMock }))

import { queryContradictionsCapability } from '../query_contradictions'

const CHART_ID = 'aaaaaaaa-aaaa-4aaa-aaaa-aaaaaaaaaaaa'
const ACTIVE_BUILD_ID = 'bbbbbbbb-bbbb-4bbb-bbbb-bbbbbbbbbbbb'

function contentOf(result: Awaited<ReturnType<typeof queryContradictionsCapability.handler>>) {
  return result.content as Record<string, unknown>
}

describe('query_contradictions — reviewed contradiction collection contract', () => {
  beforeEach(() => queryMock.mockReset())

  it('uses the contradiction ID as the deterministic tie-break and keeps that collection separate from supplemental discoveries', async () => {
    queryMock.mockImplementation(async (sql: unknown) => {
      if (typeof sql !== 'string') return { rows: [] }
      if (sql.includes('FROM build_runs')) return { rows: [{ build_id: ACTIVE_BUILD_ID }] }
      if (sql.includes('FROM bodha_contradictions')) return { rows: [{ contradiction_id: 'c-2', signal_a_id: 'a', signal_b_id: 'b', build_id: ACTIVE_BUILD_ID }] }
      if (sql.includes('FROM bodha_discoveries')) return { rows: [{ discovery_id: 'd-1', build_id: ACTIVE_BUILD_ID }] }
      return { rows: [] }
    })

    const result = await queryContradictionsCapability.handler({ chart_id: CHART_ID }, undefined)
    const content = contentOf(result)

    expect(result.is_error).toBe(false)
    expect(String(queryMock.mock.calls[0]?.[0])).toContain("FROM build_runs")
    expect(String(queryMock.mock.calls[1]?.[0])).toContain('ORDER BY combined_salience DESC NULLS LAST, contradiction_id ASC')
    for (const [sql, params] of queryMock.mock.calls.filter(([sql]) => String(sql).includes('FROM bodha_'))) {
      expect(String(sql)).toContain('build_id = $3')
      expect(params).toEqual(expect.arrayContaining([ACTIVE_BUILD_ID]))
    }
    expect(content['contradictions']).toEqual([{ contradiction_id: 'c-2', signal_a_id: 'a', signal_b_id: 'b', build_id: ACTIVE_BUILD_ID }])
    expect(content['discoveries']).toEqual([{ discovery_id: 'd-1', build_id: ACTIVE_BUILD_ID }])
    expect(content['contradiction_count']).toBe(1)
    expect(content['build_id']).toBe(ACTIVE_BUILD_ID)
    expect(content['generation_provenance']).toEqual({ build_id: ACTIVE_BUILD_ID, relation_scope: 'selected_active_completed_build' })
  })

  it('indexes optional discoveries and anomalies from the selected query legs only', async () => {
    queryMock.mockImplementation(async (sql: unknown) => {
      if (typeof sql !== 'string') return { rows: [] }
      if (sql.includes('FROM build_runs')) return { rows: [{ build_id: ACTIVE_BUILD_ID }] }
      if (sql.includes('FROM bodha_contradictions')) return { rows: [{ contradiction_id: 'c-1', build_id: ACTIVE_BUILD_ID }] }
      if (sql.includes('FROM bodha_anomalies')) return { rows: [{ anomaly_id: 'a-1', build_id: ACTIVE_BUILD_ID }] }
      return { rows: [] }
    })

    const result = await queryContradictionsCapability.handler({
      chart_id: CHART_ID,
      include_discoveries: false,
      include_anomalies: true,
    }, undefined)
    const content = contentOf(result)

    expect(result.is_error).toBe(false)
    expect(queryMock).toHaveBeenCalledTimes(3)
    expect(content['discoveries']).toBeUndefined()
    expect(content['anomalies']).toEqual([{ anomaly_id: 'a-1', build_id: ACTIVE_BUILD_ID }])
  })

  it('fails closed when a selected optional relation cannot be read', async () => {
    queryMock.mockImplementation(async (sql: unknown) => {
      if (typeof sql !== 'string') return { rows: [] }
      if (sql.includes('FROM build_runs')) return { rows: [{ build_id: ACTIVE_BUILD_ID }] }
      if (sql.includes('FROM bodha_contradictions')) return { rows: [] }
      if (sql.includes('FROM bodha_discoveries')) throw new Error('bodha_discoveries unavailable')
      return { rows: [] }
    })

    const result = await queryContradictionsCapability.handler({ chart_id: CHART_ID }, undefined)

    expect(result.is_error).toBe(true)
    expect(contentOf(result)['error']).toContain('bodha_discoveries unavailable')
  })

  it.each([
    { top_k_discoveries: Number.NaN, min_novelty: Number.NaN, expectedTopK: 20, expectedNovelty: 0 },
    { top_k_discoveries: Number.POSITIVE_INFINITY, min_novelty: Number.NEGATIVE_INFINITY, expectedTopK: 20, expectedNovelty: 0 },
    { top_k_discoveries: 0, min_novelty: 0, expectedTopK: 20, expectedNovelty: 0 },
    { top_k_discoveries: -5, min_novelty: -0.5, expectedTopK: 20, expectedNovelty: 0 },
    { top_k_discoveries: 999, min_novelty: 99, expectedTopK: 200, expectedNovelty: 1 },
    { top_k_discoveries: 4.8, min_novelty: 0.25, expectedTopK: 4, expectedNovelty: 0.25 },
  ])('clamps invalid discovery inputs deterministically: %#', async ({ top_k_discoveries, min_novelty, expectedTopK, expectedNovelty }) => {
    queryMock.mockImplementation(async (sql: unknown) => typeof sql === 'string' && sql.includes('FROM build_runs')
      ? { rows: [{ build_id: ACTIVE_BUILD_ID }] }
      : { rows: [] })

    const result = await queryContradictionsCapability.handler({ chart_id: CHART_ID, top_k_discoveries, min_novelty }, undefined)
    const content = contentOf(result)

    expect(result.is_error).toBe(false)
    expect((content['filters'] as Record<string, unknown>)['top_k_discoveries']).toBe(expectedTopK)
    expect((content['filters'] as Record<string, unknown>)['min_novelty']).toBe(expectedNovelty)
    const discoveryCall = queryMock.mock.calls.find(([sql]) => String(sql).includes('FROM bodha_discoveries'))
    const params = discoveryCall?.[1] as unknown[]
    expect(params).not.toContain(Number.NaN)
    expect(params).not.toContain(Number.POSITIVE_INFINITY)
    expect(params).not.toContain(Number.NEGATIVE_INFINITY)
  })

  it('fails closed before querying a relation when no active completed build exists', async () => {
    queryMock.mockResolvedValue({ rows: [] })

    const result = await queryContradictionsCapability.handler({ chart_id: CHART_ID }, undefined)

    expect(result.is_error).toBe(true)
    expect(contentOf(result)).toMatchObject({ code: 'active_completed_build_unavailable', chart_id: CHART_ID })
    expect(queryMock).toHaveBeenCalledTimes(1)
  })

  it('fails closed if a source row violates the selected active-build fence', async () => {
    queryMock.mockImplementation(async (sql: unknown) => {
      if (typeof sql !== 'string') return { rows: [] }
      if (sql.includes('FROM build_runs')) return { rows: [{ build_id: ACTIVE_BUILD_ID }] }
      if (sql.includes('FROM bodha_contradictions')) return { rows: [{ contradiction_id: 'c-old', build_id: 'cccccccc-cccc-4ccc-cccc-cccccccccccc' }] }
      return { rows: [] }
    })

    const result = await queryContradictionsCapability.handler({ chart_id: CHART_ID, include_discoveries: false }, undefined)

    expect(result.is_error).toBe(true)
    expect(contentOf(result)).toMatchObject({ code: 'active_build_provenance_mismatch', build_id: ACTIVE_BUILD_ID })
  })
})
