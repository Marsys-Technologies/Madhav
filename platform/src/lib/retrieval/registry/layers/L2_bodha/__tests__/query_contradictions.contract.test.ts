import { beforeEach, describe, expect, it, vi } from 'vitest'

const { queryMock } = vi.hoisted(() => ({ queryMock: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: queryMock }))

import { queryContradictionsCapability } from '../query_contradictions'

const CHART_ID = 'aaaaaaaa-aaaa-4aaa-aaaa-aaaaaaaaaaaa'

function contentOf(result: Awaited<ReturnType<typeof queryContradictionsCapability.handler>>) {
  return result.content as Record<string, unknown>
}

describe('query_contradictions — reviewed contradiction collection contract', () => {
  beforeEach(() => queryMock.mockReset())

  it('uses the contradiction ID as the deterministic tie-break and keeps that collection separate from supplemental discoveries', async () => {
    queryMock
      .mockResolvedValueOnce({ rows: [{ contradiction_id: 'c-2', signal_a_id: 'a', signal_b_id: 'b' }] })
      .mockResolvedValueOnce({ rows: [{ discovery_id: 'd-1' }] })

    const result = await queryContradictionsCapability.handler({ chart_id: CHART_ID }, undefined)
    const content = contentOf(result)

    expect(result.is_error).toBe(false)
    expect(String(queryMock.mock.calls[0]?.[0])).toContain('ORDER BY combined_salience DESC NULLS LAST, contradiction_id ASC')
    expect(content['contradictions']).toEqual([{ contradiction_id: 'c-2', signal_a_id: 'a', signal_b_id: 'b' }])
    expect(content['discoveries']).toEqual([{ discovery_id: 'd-1' }])
    expect(content['contradiction_count']).toBe(1)
  })

  it('indexes optional discoveries and anomalies from the selected query legs only', async () => {
    queryMock
      .mockResolvedValueOnce({ rows: [{ contradiction_id: 'c-1' }] })
      .mockResolvedValueOnce({ rows: [{ anomaly_id: 'a-1' }] })

    const result = await queryContradictionsCapability.handler({
      chart_id: CHART_ID,
      include_discoveries: false,
      include_anomalies: true,
    }, undefined)
    const content = contentOf(result)

    expect(result.is_error).toBe(false)
    expect(queryMock).toHaveBeenCalledTimes(2)
    expect(content['discoveries']).toBeUndefined()
    expect(content['anomalies']).toEqual([{ anomaly_id: 'a-1' }])
  })

  it('fails closed when a selected optional relation cannot be read', async () => {
    queryMock
      .mockResolvedValueOnce({ rows: [] })
      .mockRejectedValueOnce(new Error('bodha_discoveries unavailable'))

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
    queryMock.mockResolvedValue({ rows: [] })

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
})
