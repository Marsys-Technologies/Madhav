import { beforeEach, describe, expect, it, vi } from 'vitest'

const queryMock = vi.fn()
vi.mock('@/lib/db/client', () => ({ query: (...args: unknown[]) => queryMock(...args) }))

import {
  gradeGraha,
  judgmentQueryCapability,
  type GrahaCondition,
} from '../register_d9_judgment'
import type { ResolvedGraha } from '@/lib/retrieval/address_resolver'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const BUILD_ID = '11111111-1111-4111-8111-111111111111'
const STALE_BUILD_ID = '22222222-2222-4222-8222-222222222222'
const AYANAMSHA = 'lahiri_chitrapaksha'

beforeEach(() => {
  queryMock.mockReset()
})

describe('judgment mandatory completed-build fence', () => {
  it('fails closed before fact reads when no completed build exists', async () => {
    queryMock.mockResolvedValueOnce({ rows: [] })

    const result = await judgmentQueryCapability.handler(
      { chart_id: CHART_ID, domain: 'wealth' },
      undefined,
    )

    expect(result.is_error).toBe(true)
    expect(result.content).toMatchObject({
      code: 'no_active_completed_build',
      chart_id: CHART_ID,
    })
    expect(queryMock).toHaveBeenCalledTimes(1)
    const [sql, params] = queryMock.mock.calls[0]!
    expect(String(sql)).toContain("state = 'completed'")
    expect(String(sql)).toContain('ORDER BY ended_at DESC NULLS LAST, id DESC')
    expect(params).toEqual([CHART_ID])
  })

  it('fails closed when completed-build selection itself errors', async () => {
    queryMock.mockRejectedValueOnce(new Error('build_runs unavailable'))

    const result = await judgmentQueryCapability.handler(
      { chart_id: CHART_ID, domain: 'wealth' },
      undefined,
    )

    expect(result.is_error).toBe(true)
    expect(result.content).toMatchObject({
      code: 'active_build_selection_failed',
      chart_id: CHART_ID,
    })
    expect(queryMock).toHaveBeenCalledTimes(1)
  })

  it('uses only the selected build for score-bearing dignity and shadbala inputs', async () => {
    queryMock.mockImplementation(async (sql: string, params: unknown[] = []) => {
      const selectedBuild = params.at(-1)
      if (sql.includes("fact_category = 'graha_dignity_per_varga'")) {
        return selectedBuild === BUILD_ID
          ? { rows: [{ fact_id: 'active-dignity', fact_value_text: 'exalted' }] }
          : { rows: [{ fact_id: 'stale-dignity', fact_value_text: 'debilitated' }] }
      }
      if (sql.includes("fact_category = 'graha_shadbala_total'")) {
        return selectedBuild === BUILD_ID
          ? { rows: [{ fact_id: 'active-shadbala', fact_value_num: 5 }] }
          : { rows: [{ fact_id: 'stale-shadbala', fact_value_num: 1 }] }
      }
      return { rows: [] }
    })
    const graha: ResolvedGraha = {
      kind: 'graha', graha: 'Jupiter', graha_code: 'JUP', sign: 'Sagittarius',
      house: 9, varga: 'D1', fact_ids: ['active-placement'],
    }

    const active: GrahaCondition = await gradeGraha(CHART_ID, AYANAMSHA, graha, BUILD_ID)
    const stale: GrahaCondition = await gradeGraha(CHART_ID, AYANAMSHA, graha, STALE_BUILD_ID)

    expect(active).toMatchObject({ dignity_state: 'exalted', dignity_weight: 2, shadbala_rupa: 5 })
    expect(active.fact_ids).toEqual(['active-placement', 'active-dignity', 'active-shadbala'])
    expect(active.fact_ids).not.toContain('stale-dignity')
    expect(stale).toMatchObject({ dignity_state: 'debilitated', dignity_weight: -2, shadbala_rupa: 1 })

    for (const [sql, params] of queryMock.mock.calls) {
      expect(String(sql)).toContain('build_id = $4::uuid')
      expect(String(sql)).not.toContain('build_id = $4::text')
      expect([BUILD_ID, STALE_BUILD_ID]).toContain((params as unknown[]).at(-1))
    }
  })
})
