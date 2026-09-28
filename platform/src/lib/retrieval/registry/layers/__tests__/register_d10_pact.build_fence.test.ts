/**
 * pact_query mandatory served-generation fence (Pūrṇa R3 / RC-1, RC-2; review §4).
 *
 * CONFIRMATION's own direct chart_facts read must be restricted to the chart's served
 * generation, and a chart with no resolvable generation must fail closed before PROMISE
 * (judgment_query) ever runs.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'

const queryMock = vi.fn()
vi.mock('@/lib/db/client', () => ({ query: (...args: unknown[]) => queryMock(...args) }))

const judgmentQueryMock = vi.fn()
vi.mock('../register_d9_judgment', () => ({
  DIGNITY_WEIGHT: { exalted: 1, own: 0.75, friend: 0.5, neutral: 0.25, enemy: -0.5, debilitated: -1 },
  judgmentQueryCapability: { handler: (...args: unknown[]) => judgmentQueryMock(...args) },
}))

import { pactQueryCapability } from '../register_d10_pact'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const SERVED = '11111111-1111-4111-8111-111111111111'

function receiptRow(asset_id: string, overrides: Record<string, unknown> = {}) {
  return {
    asset_id, chart_id: CHART_ID, partition_key: '__whole_asset__', receipt_version: 'v1',
    receipt_build_id: SERVED, rows_build_id: SERVED, receipt_state: 'proven', freshness_state: 'fresh',
    output_digest_spec_sha256: 'a'.repeat(64), spec_active: true, receipt_run_state: 'completed',
    receipt_asset_present: true, receipt_disposition: 'build', observed_at: '2026-09-07T00:00:00Z',
    ...overrides,
  }
}

beforeEach(() => {
  queryMock.mockReset()
  judgmentQueryMock.mockReset()
  judgmentQueryMock.mockResolvedValue({
    is_error: false,
    content: {
      fact_id_refs: [], about: { operative_varga: 'D9', karakas: ['Venus'] },
      verdict: { verdict_grade: 'strong' }, receipt: {}, checklist: { bhavesha_condition: { from_lagna: { graha: 'Venus', graha_code: 'VEN' } } },
    },
  })
})

async function run(chartId = CHART_ID) {
  return pactQueryCapability.handler({ chart_id: chartId, domain: 'marriage' }, undefined)
}

describe('pact_query served-generation fence', () => {
  it('fails closed before any stage runs when no chart receipt resolves to a served generation', async () => {
    queryMock.mockResolvedValueOnce({ rows: [receiptRow('ga_structural', { freshness_state: 'stale' })] })
    const result = await run()
    expect(result.is_error).toBe(true)
    expect(result.content).toMatchObject({ code: 'no_served_generation', chart_id: CHART_ID })
    expect(judgmentQueryMock).not.toHaveBeenCalled()
  })

  it('fails closed when served-generation resolution itself errors', async () => {
    queryMock.mockRejectedValueOnce(new Error('receipts unavailable'))
    const result = await run()
    expect(result.is_error).toBe(true)
    expect(result.content).toMatchObject({ code: 'served_generation_resolution_failed' })
    expect(JSON.stringify(result.content)).not.toContain('receipts unavailable')
    expect(judgmentQueryMock).not.toHaveBeenCalled()
  })

  it('fences the CONFIRMATION dignity read to the served build set', async () => {
    queryMock.mockImplementation(async (sql: string) => {
      if (sql.includes('FROM asset_provenance_receipts receipt')) return { rows: [receiptRow('ga_structural')] }
      if (sql.includes("fact_category = 'graha_dignity_per_varga'")) return { rows: [] }
      return { rows: [] }
    })
    await run()
    // This test proves the fence, not the full PACT chain's downstream assembly (covered
    // elsewhere) — judgment_query having run at all confirms the generation gate passed.
    expect(judgmentQueryMock).toHaveBeenCalledTimes(1)
    const dignityCall = queryMock.mock.calls.find(([sql]) => String(sql).includes("fact_category = 'graha_dignity_per_varga'"))!
    expect(dignityCall[0]).toContain('build_id = ANY($4::uuid[])')
    expect(dignityCall[1]).toEqual([CHART_ID, 'lahiri_chitrapaksha', 'D9_VEN', [SERVED]])
  })
})
