import { beforeEach, describe, expect, it, vi } from 'vitest'

const queryMock = vi.fn()
vi.mock('@/lib/db/client', () => ({ query: (...args: unknown[]) => queryMock(...args) }))

import {
  gradeGraha,
  judgmentQueryCapability,
  type GrahaCondition,
} from '../register_d9_judgment'
import { ExplicitEmptyBuildFenceError } from '@/lib/retrieval/registry/generation/served_generation'
import type { ResolvedGraha } from '@/lib/retrieval/address_resolver'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const BUILD_ID = '11111111-1111-4111-8111-111111111111'
const STALE_BUILD_ID = '22222222-2222-4222-8222-222222222222'
const AYANAMSHA = 'lahiri_chitrapaksha'

beforeEach(() => {
  queryMock.mockReset()
})

function receiptRow(asset_id: string, overrides: Record<string, unknown> = {}) {
  return {
    asset_id, chart_id: CHART_ID, partition_key: '__whole_asset__', receipt_version: 'v1',
    receipt_build_id: BUILD_ID, rows_build_id: BUILD_ID, receipt_state: 'proven', freshness_state: 'fresh',
    output_digest_spec_sha256: 'a'.repeat(64), spec_active: true, receipt_run_state: 'completed',
    receipt_asset_present: true, receipt_disposition: 'build', observed_at: '2026-09-07T00:00:00Z',
    ...overrides,
  }
}

describe('judgment mandatory served-generation fence', () => {
  it('fails closed before fact reads when no chart receipt resolves to a served generation', async () => {
    queryMock.mockResolvedValueOnce({ rows: [receiptRow('ga_structural', { freshness_state: 'stale' })] })

    const result = await judgmentQueryCapability.handler(
      { chart_id: CHART_ID, domain: 'wealth' },
      undefined,
    )

    expect(result.is_error).toBe(true)
    expect(result.content).toMatchObject({
      code: 'no_served_generation',
      chart_id: CHART_ID,
      unresolved_assets: [{ asset_id: 'ga_structural', reason: 'receipt_not_fresh' }],
    })
    expect(queryMock).toHaveBeenCalledTimes(1)
    const [sql, params] = queryMock.mock.calls[0]!
    // RC-1: the fence never consults which run finished last for the chart.
    expect(String(sql)).not.toMatch(/FROM build_runs\s+WHERE chart_id = \$1::uuid AND state = 'completed'/)
    expect(String(sql)).not.toContain('ORDER BY ended_at DESC')
    expect(String(sql)).toContain('FROM asset_provenance_receipts receipt')
    expect(params).toEqual([CHART_ID, null])
  })

  it('fails closed when served-generation resolution itself errors', async () => {
    queryMock.mockRejectedValueOnce(new Error('receipts unavailable'))

    const result = await judgmentQueryCapability.handler(
      { chart_id: CHART_ID, domain: 'wealth' },
      undefined,
    )

    expect(result.is_error).toBe(true)
    expect(result.content).toMatchObject({
      code: 'served_generation_resolution_failed',
      chart_id: CHART_ID,
    })
    expect(JSON.stringify(result.content)).not.toContain('receipts unavailable')
    expect(queryMock).toHaveBeenCalledTimes(1)
  })

  it('uses only the served build set for score-bearing dignity and shadbala inputs', async () => {
    queryMock.mockImplementation(async (sql: string, params: unknown[] = []) => {
      const fence = params.at(-1) as unknown[]
      const served = Array.isArray(fence) && fence.includes(BUILD_ID)
      if (sql.includes("fact_category = 'graha_dignity_per_varga'")) {
        return served
          ? { rows: [{ fact_id: 'active-dignity', fact_value_text: 'exalted' }] }
          : { rows: [{ fact_id: 'stale-dignity', fact_value_text: 'debilitated' }] }
      }
      if (sql.includes("fact_category = 'graha_shadbala_total'")) {
        return served
          ? { rows: [{ fact_id: 'active-shadbala', fact_value_num: 5 }] }
          : { rows: [{ fact_id: 'stale-shadbala', fact_value_num: 1 }] }
      }
      return { rows: [] }
    })
    const graha: ResolvedGraha = {
      kind: 'graha', graha: 'Jupiter', graha_code: 'JUP', sign: 'Sagittarius',
      house: 9, varga: 'D1', fact_ids: ['active-placement'],
    }

    const active: GrahaCondition = await gradeGraha(CHART_ID, AYANAMSHA, graha, [BUILD_ID, '33333333-3333-4333-8333-333333333333'])
    const stale: GrahaCondition = await gradeGraha(CHART_ID, AYANAMSHA, graha, STALE_BUILD_ID)

    expect(active).toMatchObject({ dignity_state: 'exalted', dignity_weight: 2, shadbala_rupa: 5 })
    expect(active.fact_ids).toEqual(['active-placement', 'active-dignity', 'active-shadbala'])
    expect(active.fact_ids).not.toContain('stale-dignity')
    expect(stale).toMatchObject({ dignity_state: 'debilitated', dignity_weight: -2, shadbala_rupa: 1 })

    for (const [sql, params] of queryMock.mock.calls) {
      expect(String(sql)).toContain('build_id = ANY($4::uuid[])')
      expect(String(sql)).not.toContain('build_id = $4::text')
      expect(Array.isArray((params as unknown[]).at(-1))).toBe(true)
    }
  })

  it('throws (never degrades to a false null-dignity finding) on an explicit-empty build fence', async () => {
    // judgment_query's own served-generation gate guarantees this never happens through its
    // own request surface (it always passes a non-empty resolved build set) — this is a
    // defense-in-depth invariant check on gradeGraha itself, called directly per the R3
    // boundary ruling's "at least one judgment/checklist caller" test requirement.
    queryMock.mockResolvedValue({ rows: [] })
    const graha: ResolvedGraha = {
      kind: 'graha', graha: 'Jupiter', graha_code: 'JUP', sign: 'Sagittarius',
      house: 9, varga: 'D1', fact_ids: ['active-placement'],
    }

    await expect(gradeGraha(CHART_ID, AYANAMSHA, graha, [])).rejects.toThrow(ExplicitEmptyBuildFenceError)
  })
})
